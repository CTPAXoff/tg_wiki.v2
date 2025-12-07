from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
from datetime import datetime
from typing import Dict, Any

from .database import enable_wal_mode, Base, engine, Message, get_db
from .telegram_manager import telegram_manager
from .schemas import (
    RequestCodeRequest, ConfirmCodeRequest, FetchMessagesRequest,
    AuthStatusResponse, ErrorResponse, SuccessResponse, 
    ChatInfo, ProgressResponse
)
from .logger import logger
from sqlalchemy import select, func

# Global parsing progress
parsing_progress: Dict[str, Any] = {
    "status": "idle",
    "progress": 0.0,
    "messages_processed": 0,
    "total_messages": None,
    "current_chat": None
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await enable_wal_mode()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown
    pass

app = FastAPI(
    title="Telegram Parser API",
    description="Minimal Telegram message parser with Telethon",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def create_error_response(error_type: str, message: str) -> ErrorResponse:
    """Create standardized error response"""
    return ErrorResponse(error=True, type=error_type, message=message)

@app.post("/auth/request-code")
async def request_code(request: RequestCodeRequest):
    """Request verification code"""
    try:
        await telegram_manager.request_code(request.phone)
        return {"status": "ok"}
    except ValueError as e:
        logger.warning(f"Invalid phone: {e}")
        raise HTTPException(status_code=400, detail=create_error_response("InvalidPhone", str(e)))
    except Exception as e:
        logger.error(f"Request code failed: {e}")
        raise HTTPException(status_code=500, detail=create_error_response("UnknownError", "Failed to request code"))

@app.post("/auth/confirm-code")
async def confirm_code(request: ConfirmCodeRequest):
    """Confirm verification code"""
    try:
        await telegram_manager.confirm_code(request.phone, request.code)
        return {"status": "ok"}
    except ValueError as e:
        logger.warning(f"Invalid code: {e}")
        raise HTTPException(status_code=400, detail=create_error_response("CodeExpired", str(e)))
    except Exception as e:
        logger.error(f"Confirm code failed: {e}")
        raise HTTPException(status_code=500, detail=create_error_response("UnknownError", "Failed to confirm code"))

@app.get("/auth/status", response_model=AuthStatusResponse)
async def get_auth_status():
    """Get authentication status"""
    try:
        status = await telegram_manager.get_auth_status()
        return status
    except Exception as e:
        logger.error(f"Get auth status failed: {e}")
        return {"status": "invalid"}

@app.post("/auth/reset")
async def reset_session():
    """Reset session"""
    try:
        await telegram_manager.reset_session()
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Reset session failed: {e}")
        raise HTTPException(status_code=500, detail=create_error_response("UnknownError", "Failed to reset session"))

@app.get("/telegram/chats", response_model=list[ChatInfo])
async def get_chats():
    """Get list of chats"""
    try:
        chats = await telegram_manager.get_chats()
        return chats
    except ValueError as e:
        logger.warning(f"No valid session: {e}")
        raise HTTPException(status_code=401, detail=create_error_response("SessionInvalid", str(e)))
    except Exception as e:
        logger.error(f"Get chats failed: {e}")
        raise HTTPException(status_code=500, detail=create_error_response("UnknownError", "Failed to get chats"))

@app.post("/telegram/fetch-messages")
async def fetch_messages(request: FetchMessagesRequest, background_tasks: BackgroundTasks):
    """Start message fetching in background"""
    try:
        # Check if parsing is already running
        if parsing_progress["status"] == "parsing":
            raise HTTPException(status_code=409, detail=create_error_response("AlreadyParsing", "Parsing already in progress"))
        
        # Start background task
        background_tasks.add_task(fetch_messages_background, request)
        
        return {"status": "started"}
    except Exception as e:
        logger.error(f"Start message fetching failed: {e}")
        raise HTTPException(status_code=500, detail=create_error_response("UnknownError", "Failed to start message fetching"))

async def fetch_messages_background(request: FetchMessagesRequest):
    """Background task for fetching messages"""
    global parsing_progress
    
    try:
        parsing_progress.update({
            "status": "parsing",
            "progress": 0.0,
            "messages_processed": 0,
            "total_messages": None,
            "current_chat": f"Chat {request.chat_id}"
        })
        
        # Get existing message count for progress calculation
        async for db in get_db():
            result = await db.execute(
                select(func.count(Message.id)).where(Message.chat_id == request.chat_id)
            )
            existing_count = result.scalar() or 0
        
        messages_processed = 0
        
        # Fetch and save messages
        async for message_data in telegram_manager.fetch_messages(
            request.chat_id, 
            request.from_date, 
            request.to_date
        ):
            # Save to database with retry logic
            for attempt in range(3):
                try:
                    async for db in get_db():
                        # Check if message already exists
                        existing = await db.execute(
                            select(Message).where(
                                Message.chat_id == message_data['chat_id'],
                                Message.msg_id == message_data['msg_id']
                            )
                        )
                        if existing.scalar_one_or_none():
                            break  # Skip if already exists
                        
                        # Create new message
                        message = Message(**message_data)
                        db.add(message)
                        await db.commit()
                        
                        messages_processed += 1
                        parsing_progress["messages_processed"] = existing_count + messages_processed
                        
                        # Update progress (simplified - in real app you'd get total count first)
                        parsing_progress["progress"] = min(0.95, messages_processed / 1000.0)
                    
                    break  # Success, exit retry loop
                    
                except Exception as e:
                    logger.warning(f"Failed to save message (attempt {attempt + 1}): {e}")
                    if attempt == 2:
                        logger.error(f"Failed to save message after 3 attempts: {e}")
                    else:
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        parsing_progress["status"] = "completed"
        parsing_progress["progress"] = 1.0
        
    except Exception as e:
        logger.error(f"Background message fetching failed: {e}")
        parsing_progress["status"] = "failed"
        parsing_progress["current_chat"] = f"Error: {str(e)}"

@app.get("/telegram/progress", response_model=ProgressResponse)
async def get_parsing_progress():
    """Get current parsing progress"""
    return parsing_progress

@app.get("/telegram/messages")
async def get_messages(chat_id: int, limit: int = 50, offset: int = 0):
    """Get parsed messages from database"""
    try:
        async for db in get_db():
            result = await db.execute(
                select(Message)
                .where(Message.chat_id == chat_id)
                .order_by(Message.date.desc())
                .limit(limit)
                .offset(offset)
            )
            messages = result.scalars().all()
            
            # Convert to dict for JSON response
            return [
                {
                    "id": msg.id,
                    "msg_id": msg.msg_id,
                    "sender_name": msg.sender_name,
                    "text": msg.text,
                    "date": msg.date.isoformat(),
                    "is_reply": msg.is_reply,
                    "reply_to_msg_id": msg.reply_to_msg_id
                }
                for msg in messages
            ]
    except Exception as e:
        logger.error(f"Failed to get messages: {e}")
        raise HTTPException(status_code=500, detail=create_error_response("UnknownError", "Failed to get messages"))

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Telegram Parser API is running"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}
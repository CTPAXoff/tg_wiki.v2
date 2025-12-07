from telethon import TelegramClient
from telethon.errors import (
    AuthKeyError,
    SessionPasswordNeededError,
    UserDeactivatedError,
    AuthKeyUnregisteredError,
    FloodWaitError
)
from telethon.tl.types import InputPeerEmpty
from typing import Optional, List, Dict, Any, AsyncGenerator
from telethon.tl.functions.messages import GetHistoryRequest
from typing import Optional, List, Dict, Any, AsyncGenerator
import asyncio
import json
from datetime import datetime
from .database import Session, Message, get_db
from .encryption import encryption
from .config import config
from .logger import logger
from .schemas import ChatInfo

class TelegramManager:
    def __init__(self):
        self._client: Optional[TelegramClient] = None
        self._phone_code_hash: Optional[str] = None
        self._parsing_lock = asyncio.Lock()
        self._is_connected = False
    
    async def _get_client(self, string_session: Optional[str] = None) -> TelegramClient:
        """Get or create Telethon client"""
        if self._client is None:
            # Use placeholder values - user will provide their own
            api_id = config.TELETHON_API_ID or 0  # User should set this
            api_hash = config.TELETHON_API_HASH or ""  # User should set this
            
            if not api_id or not api_hash:
                raise ValueError("TELETHON_API_ID and TELETHON_API_HASH must be set in .env file")
            
            self._client = TelegramClient(
                'session_name',  # placeholder, we use string sessions
                api_id,
                api_hash
            )
            
            if string_session:
                self._client.session.set_dc(2, '149.154.167.51', 80)
        
        # Connect only if not already connected
        if not self._is_connected:
            await self._client.connect()
            self._is_connected = True
        
        return self._client
    
    async def request_code(self, phone: str) -> bool:
        """Request verification code"""
        try:
            client = await self._get_client()
            
            result = await client.send_code_request(phone)
            self._phone_code_hash = result.phone_code_hash
            
            # Store phone_code_hash in database
            async for db in get_db():
                session = await db.get(Session, 1)
                if not session:
                    session = Session(id=1, phone=phone, phone_code_hash=self._phone_code_hash)
                    db.add(session)
                else:
                    session.phone = phone
                    session.phone_code_hash = self._phone_code_hash
                    session.status = "pending"
                    session.updated_at = datetime.utcnow()
                await db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to request code: {e}")
            raise
    
    async def confirm_code(self, phone: str, code: str) -> str:
        """Confirm verification code and return string session"""
        try:
            # Get phone_code_hash from database
            async for db in get_db():
                session = await db.get(Session, 1)
                if not session or not session.phone_code_hash:
                    raise ValueError("No pending code request found")
                phone_code_hash = session.phone_code_hash
            
            client = await self._get_client()
            
            # Sign in
            await client.sign_in(phone, code, phone_code_hash=phone_code_hash)
            
            # Get string session
            string_session = client.session.save()
            
            if not string_session:
                raise ValueError("Failed to get session string after sign in")

            # Encrypt and save to database
            encrypted_session = encryption.encrypt(string_session)
            
            async for db in get_db():
                session = await db.get(Session, 1)
                if session:
                    session.string_session = encrypted_session
                    session.status = "valid"
                    session.updated_at = datetime.utcnow()
                    await db.commit()
            
            return string_session
            
        except Exception as e:
            logger.error(f"Failed to confirm code: {e}")
            # Update session status to invalid
            async for db in get_db():
                session = await db.get(Session, 1)
                if session:
                    session.status = "invalid"
                    session.updated_at = datetime.utcnow()
                    await db.commit()
            raise
    
    async def get_auth_status(self) -> Dict[str, Any]:
        """Check authentication status"""
        try:
            async for db in get_db():
                session = await db.get(Session, 1)
                if not session:
                    return {"status": "empty"}
                
                if not session.string_session:
                    return {"status": "empty", "phone": session.phone}
                
                # Try to validate the session
                try:
                    string_session = encryption.decrypt(session.string_session)
                    client = await self._get_client(string_session)
                    me = await client.get_me()
                    
                    return {
                        "status": "valid",
                        "phone": session.phone
                    }
                    
                except (AuthKeyError, UserDeactivatedError, AuthKeyUnregisteredError) as e:
                    logger.warning(f"Session invalid: {e}")
                    session.status = "invalid"
                    session.updated_at = datetime.utcnow()
                    await db.commit()
                    return {"status": "invalid", "phone": session.phone}
                    
                except Exception as e:
                    logger.error(f"Session check failed: {e}")
                    session.status = "invalid"
                    session.updated_at = datetime.utcnow()
                    await db.commit()
                    return {"status": "invalid", "phone": session.phone}
                    
        except Exception as e:
            logger.error(f"Failed to get auth status: {e}")
            return {"status": "invalid"}
    
    async def reset_session(self) -> bool:
        """Reset session"""
        try:
            async for db in get_db():
                session = await db.get(Session, 1)
                if session:
                    session.string_session = None
                    session.phone_code_hash = None
                    session.status = "empty"
                    session.updated_at = datetime.utcnow()
                    await db.commit()
            
            if self._client:
                await self._client.disconnect()
                self._client = None
                self._is_connected = False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to reset session: {e}")
            raise
    
    async def get_chats(self) -> List[ChatInfo]:
        """Get list of chats"""
        try:
            # Get encrypted session from database
            async for db in get_db():
                session = await db.get(Session, 1)
                if not session or not session.string_session:
                    raise ValueError("No valid session found")
                
                string_session = encryption.decrypt(session.string_session)
            
            client = await self._get_client(string_session)
            
            # Get dialogs using get_dialogs method
            dialogs = await client.get_dialogs(limit=100)
            
            chats = []
            for dialog in dialogs:
                entity = dialog.entity
                if hasattr(entity, 'title') or hasattr(entity, 'first_name') or hasattr(entity, 'username'):
                    chat_info = ChatInfo(
                        id=entity.id,
                        title=getattr(entity, 'title', getattr(entity, 'first_name', 'Unknown')),
                        username=getattr(entity, 'username', None),
                        type=type(entity).__name__
                    )
                    chats.append(chat_info)
            
            return chats
            
        except Exception as e:
            logger.error(f"Failed to get chats: {e}")
            # Mark session as invalid if needed
            await self._handle_session_error(e)
            raise
    
    async def fetch_messages(self, chat_id: int, from_date: Optional[datetime] = None, to_date: Optional[datetime] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """Fetch messages from chat with date filtering"""
        try:
            # Get encrypted session from database
            async for db in get_db():
                session = await db.get(Session, 1)
                if not session or not session.string_session:
                    raise ValueError("No valid session found")
                
                string_session = encryption.decrypt(session.string_session)
            
            client = await self._get_client(string_session)
            
            # Get chat entity
            chat = await client.get_entity(chat_id)
            
            # Get message history
            messages = []
            offset_id = 0
            batch_size = 100
            
            while True:
                try:
                    result = await client(GetHistoryRequest(
                        peer=chat,
                        offset_id=offset_id,
                        offset_date=None,
                        add_offset=0,
                        limit=batch_size,
                        max_id=0,
                        min_id=0,
                        hash=0
                    ))
                    
                    if not result.messages:
                        break
                    
                    for message in result.messages:
                        # Filter only text messages
                        if not hasattr(message, 'message') or not message.message:
                            continue
                        
                        # Date filtering
                        msg_date = message.date.replace(tzinfo=None)
                        if from_date and msg_date < from_date:
                            continue
                        if to_date and msg_date > to_date:
                            continue
                        
                        # Get sender info
                        sender_name = "Unknown"
                        if hasattr(message, 'sender_id') and message.sender_id:
                            try:
                                sender = await client.get_entity(message.sender_id)
                                sender_name = getattr(sender, 'first_name', '') + ' ' + getattr(sender, 'last_name', '')
                                sender_name = sender_name.strip() or getattr(sender, 'username', 'Unknown')
                            except:
                                pass
                        
                        # Process entities
                        entities = None
                        if hasattr(message, 'entities') and message.entities:
                            entities = [entity.__dict__ for entity in message.entities]
                        
                        # Create message data
                        message_data = {
                            'chat_id': chat_id,
                            'msg_id': message.id,
                            'sender_id': getattr(message, 'sender_id', None),
                            'sender_name': sender_name,
                            'text': message.message,
                            'date': msg_date,
                            'is_reply': hasattr(message, 'reply_to') and message.reply_to is not None,
                            'reply_to_msg_id': getattr(message.reply_to, 'reply_to_msg_id', None) if hasattr(message, 'reply_to') and message.reply_to else None,
                            'entities': entities,
                            'raw_json': message.to_dict()
                        }
                        
                        yield message_data
                    
                    if len(result.messages) < batch_size:
                        break
                    
                    offset_id = result.messages[-1].id
                    
                    # Add delay to avoid flood wait
                    await asyncio.sleep(1)
                    
                except FloodWaitError as e:
                    logger.warning(f"Flood wait: {e.seconds} seconds")
                    await asyncio.sleep(e.seconds)
                    continue
                except Exception as e:
                    logger.error(f"Error fetching batch: {e}")
                    break
            
        except Exception as e:
            logger.error(f"Failed to fetch messages: {e}")
            await self._handle_session_error(e)
            raise
    
    async def _handle_session_error(self, error: Exception):
        """Handle session-related errors"""
        if isinstance(error, (AuthKeyError, UserDeactivatedError, AuthKeyUnregisteredError)):
            async for db in get_db():
                session = await db.get(Session, 1)
                if session:
                    session.status = "invalid"
                    session.updated_at = datetime.utcnow()
                    await db.commit()

    async def close(self):
        """Close the client connection when shutting down the application"""
        if self._client and self._is_connected:
            await self._client.disconnect()
            self._is_connected = False

telegram_manager = TelegramManager()
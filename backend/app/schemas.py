from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class RequestCodeRequest(BaseModel):
    phone: str = Field(..., min_length=10, max_length=20)

class ConfirmCodeRequest(BaseModel):
    phone: str = Field(..., min_length=10, max_length=20)
    code: str = Field(..., min_length=5, max_length=10)

class FetchMessagesRequest(BaseModel):
    chat_id: int
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None

class ChatInfo(BaseModel):
    id: int
    title: str
    username: Optional[str] = None
    type: str

class AuthStatusResponse(BaseModel):
    status: str
    phone: Optional[str] = None

class ErrorResponse(BaseModel):
    error: bool = True
    type: str
    message: str

class SuccessResponse(BaseModel):
    status: str = "ok"

class ProgressResponse(BaseModel):
    status: str = "parsing"
    progress: float = 0.0
    messages_processed: int = 0
    total_messages: Optional[int] = None
    current_chat: Optional[str] = None
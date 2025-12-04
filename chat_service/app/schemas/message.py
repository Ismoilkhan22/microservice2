from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID


class MessageCreate(BaseModel):
    """Xabar yaratish request"""
    message: str = Field(..., min_length=1, max_length=5000)
    message_type: str = Field(default="text", max_length=20)
    file_url: Optional[str] = Field(None, max_length=500)
    file_type: Optional[str] = Field(None, max_length=50)
    metadata: Optional[Dict[str, Any]] = None

    @validator("message")
    def validate_message(cls, v):
        if not v or v.isspace():
            raise ValueError("Message cannot be empty")
        return v.strip()


class MessageUpdate(BaseModel):
    """Xabarni yangilash"""
    message: Optional[str] = Field(None, max_length=5000)
    is_read: Optional[bool] = None

    @validator("message")
    def validate_message(cls, v):
        if v is not None and (not v or v.isspace()):
            raise ValueError("Message cannot be empty")
        return v.strip() if v else None


class MessageResponse(BaseModel):
    """Xabar qaytarish"""
    id: UUID
    room_id: str
    user_id: str
    message: str
    message_type: str
    is_read: bool
    is_edited: bool
    file_url: Optional[str] = None
    file_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    edited_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MessageListResponse(BaseModel):
    """Xabarlar ro'yxati"""
    total: int
    page: int
    page_size: int
    items: List[MessageResponse]


class ChatRoomCreate(BaseModel):
    """Chat room yaratish"""
    room_id: str = Field(..., min_length=1, max_length=50)
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    room_type: str = Field(default="group", max_length=20)


class ChatRoomResponse(BaseModel):
    """Chat room qaytarish"""
    id: UUID
    room_id: str
    name: Optional[str]
    description: Optional[str]
    room_type: str
    created_by: str
    members_count: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WebSocketMessage(BaseModel):
    """WebSocket xabar modeli"""
    type: str  # connect, disconnect, message
    room_id: str
    user_id: str
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
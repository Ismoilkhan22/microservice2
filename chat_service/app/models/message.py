from sqlalchemy import Column, String, Text, DateTime, Index, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, JSON
from datetime import datetime
import uuid
from chat_service.app.database.base import Base


class ChatMessage(Base):
    """
    Chat xabarining database modeli
    """
    __tablename__ = "chat_messages"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    room_id = Column(String(50), nullable=False, index=True)
    user_id = Column(String(50), nullable=False, index=True)

    # Message Content
    message = Column(Text, nullable=False)
    message_type = Column(String(20), default="text")  # text, image, file, etc

    # Status
    is_read = Column(String, default=False)  # Boolean qisqacha o'z ichiga olish uchun
    is_edited = Column(String, default=False)

    # Media
    file_url = Column(String(500), nullable=True)
    file_type = Column(String(50), nullable=True)

    # Metadata
    metadata = Column(JSON, nullable=True)  # Additional data

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    edited_at = Column(DateTime, nullable=True)

    # Indexes - Query performance
    __table_args__ = (
        Index("ix_chat_messages_room_created", "room_id", "created_at"),
        Index("ix_chat_messages_user_id", "user_id"),
        Index("ix_chat_messages_room_user", "room_id", "user_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<ChatMessage("
            f"id={self.id}, "
            f"room_id={self.room_id}, "
            f"user_id={self.user_id}, "
            f"created_at={self.created_at}"
            f")>"
        )


class ChatRoom(Base):
    """
    Chat room modeli
    """
    __tablename__ = "chat_rooms"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_id = Column(String(50), nullable=False, unique=True, index=True)

    # Room Info
    name = Column(String(200), nullable=True)
    description = Column(Text, nullable=True)
    room_type = Column(String(20), default="group")  # group, private, direct

    # Members
    created_by = Column(String(50), nullable=False)
    members_count = Column(Integer, default=0)

    # Status
    is_active = Column(String, default=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return (
            f"<ChatRoom("
            f"room_id={self.room_id}, "
            f"name={self.name}, "
            f"type={self.room_type}"
            f")>"
        )







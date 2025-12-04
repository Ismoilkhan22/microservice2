from sqlalchemy import Column, String, Float, DateTime, Enum, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
import enum
from payment_service.app.database.base import Base


class PaymentStatus(str, enum.Enum):
    """To'lov holatlari"""
    PENDING = "pending"  # Kutilmoqda
    PROCESSING = "processing"  # Qayta ishlanimoqda
    COMPLETED = "completed"  # Bajarildi
    FAILED = "failed"  # Amalga oshmadi
    CANCELLED = "cancelled"  # Bekor qilindi
    REFUNDED = "refunded"  # Qaytarildi


class Payment(Base):
    """
    To'lov modeli
    """
    __tablename__ = "payments"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign Keys
    user_id = Column(String(50), nullable=False, index=True)
    order_id = Column(String(50), nullable=False, index=True)

    # Payment Info
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)

    # Provider Info
    payment_method = Column(String(50), nullable=True)  # credit_card, paypal, etc
    provider_transaction_id = Column(String(100), nullable=True, unique=True)

    # Metadata
    description = Column(String(500), nullable=True)
    metadata_info = Column(String(1000), nullable=True)  # JSON string

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Error tracking
    error_message = Column(String(500), nullable=True)
    retry_count = Column(String, default=0)

    # Indexes - Query performance
    __table_args__ = (
        Index("ix_payments_user_id_created_at", "user_id", "created_at"),
        Index("ix_payments_order_id_status", "order_id", "status"),
        Index("ix_payments_provider_transaction_id", "provider_transaction_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<Payment("
            f"id={self.id}, "
            f"user_id={self.user_id}, "
            f"amount={self.amount}, "
            f"status={self.status}"
            f")>"
        )


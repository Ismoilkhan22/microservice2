# payment-service/app/schemas/payment.py
# ============================================
# PAYMENT PYDANTIC SCHEMAS (Request/Response)
# ============================================

from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum


class PaymentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentCreate(BaseModel):
    """To'lov yaratish request"""
    order_id: str = Field(..., min_length=1, max_length=50)
    amount: float = Field(..., gt=0, le=999999.99)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    payment_method: str = Field(..., min_length=3, max_length=50)
    description: Optional[str] = Field(None, max_length=500)
    metadata: Optional[Dict[str, Any]] = None

    @validator("amount")
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError("Amount must be greater than 0")
        if v > 999999.99:
            raise ValueError("Amount exceeds maximum allowed")
        return round(v, 2)

    @validator("currency")
    def validate_currency(cls, v):
        valid_currencies = ["USD", "EUR", "GBP", "JPY", "UZS"]
        if v not in valid_currencies:
            raise ValueError(f"Currency must be one of {valid_currencies}")
        return v


class PaymentUpdate(BaseModel):
    """To'lovni yangilash"""
    status: Optional[PaymentStatus] = None
    payment_method: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class PaymentResponse(BaseModel):
    """To'lovni qaytarish"""
    id: UUID
    user_id: str
    order_id: str
    amount: float
    currency: str
    status: PaymentStatus
    payment_method: str
    provider_transaction_id: Optional[str] = None
    description: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PaymentConfirmRequest(BaseModel):
    """To'lovni tasdiqlash"""
    provider_transaction_id: str
    status: PaymentStatus


class PaymentRefundRequest(BaseModel):
    """To'lovni qaytarish"""
    reason: str = Field(..., max_length=500)
    amount: Optional[float] = None


class PaymentListResponse(BaseModel):
    """To'lovlar ro'yxati"""
    total: int
    page: int
    page_size: int
    items: list[PaymentResponse]
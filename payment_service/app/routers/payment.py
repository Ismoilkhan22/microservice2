# payment-service/app/routers/payment.py
# ============================================
# PAYMENT ENDPOINTS
# ============================================

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from shared.dependencies import get_user_id
from shared.logger import setup_logger
from shared.exceptions import NotFoundException, ValidationException
from payment_service.app.database.session import get_db
from payment_service.app.services.payment import PaymentService
from payment_service.app.schemas.payment import (
    PaymentCreate, PaymentResponse, PaymentConfirmRequest, PaymentListResponse
)

logger = setup_logger(__name__)
router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("", response_model=PaymentResponse, status_code=201)
async def create_payment(
        payment_data: PaymentCreate,
        user_id: str = Depends(get_user_id),
        db: AsyncSession = Depends(get_db)
):
    """
    ✅ Yangi to'lov yaratish

    - **order_id**: Buyurtma ID
    - **amount**: To'lov miqdori (> 0)
    - **currency**: Valyuta kodi (USD, EUR, GBP, JPY, UZS)
    - **payment_method**: To'lov usuli
    """
    try:
        service = PaymentService(db)
        return await service.create_payment(user_id, payment_data)
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e.message))
    except Exception as e:
        logger.error(f"Error creating payment: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
        payment_id: UUID,
        user_id: str = Depends(get_user_id),
        db: AsyncSession = Depends(get_db)
):
    """
    ✅ To'lov ma'lumotlarini olish
    """
    try:
        service = PaymentService(db)
        return await service.get_payment(payment_id, user_id)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e.message))
    except Exception as e:
        logger.error(f"Error fetching payment: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{payment_id}/confirm", response_model=PaymentResponse)
async def confirm_payment(
        payment_id: UUID,
        confirm_data: PaymentConfirmRequest,
        user_id: str = Depends(get_user_id),
        db: AsyncSession = Depends(get_db)
):
    """
    ✅ To'lovni tasdiqlash

    - **provider_transaction_id**: Provider transaksiya ID
    - **status**: To'lov holati
    """
    try:
        service = PaymentService(db)
        return await service.confirm_payment(payment_id, user_id, confirm_data)
    except (NotFoundException, ValidationException) as e:
        raise HTTPException(status_code=400, detail=str(e.message))
    except Exception as e:
        logger.error(f"Error confirming payment: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("", response_model=PaymentListResponse)
async def list_payments(
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        user_id: str = Depends(get_user_id),
        db: AsyncSession = Depends(get_db)
):
    """
    ✅ To'lovlar ro'yxati (Pagination)
    """
    try:
        service = PaymentService(db)
        result = await service.list_payments(user_id, page, page_size)
        return result
    except Exception as e:
        logger.error(f"Error listing payments: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
# payment-service/app/services/payment.py
# ============================================
# PAYMENT BUSINESS LOGIC
# ============================================

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_
from datetime import datetime
from uuid import UUID
import json
import aio_pika
from shared.logger import setup_logger
from shared.exceptions import NotFoundException, ValidationException
from payment_service.app.models.payment import Payment, PaymentStatus
from payment_service.app.schemas.payment import (
    PaymentCreate, PaymentResponse, PaymentConfirmRequest
)

logger = setup_logger(__name__)


class PaymentService:
    """To'lov servisining business logikasi"""

    def __init__(self, db: AsyncSession, rabbitmq_channel: aio_pika.abc.AbstractChannel = None):
        self.db = db
        self.rabbitmq_channel = rabbitmq_channel

    async def create_payment(self, user_id: str, payment_data: PaymentCreate) -> PaymentResponse:
        """
        Yangi to'lov yaratish
        """
        logger.info(f"Creating payment for user: {user_id}, amount: {payment_data.amount}")

        # Xuddi shunga o'xshash to'lov mavjudligini tekshirish
        existing = await self.db.execute(
            select(Payment).where(
                and_(
                    Payment.user_id == user_id,
                    Payment.order_id == payment_data.order_id,
                    Payment.status.in_([PaymentStatus.PENDING, PaymentStatus.PROCESSING])
                )
            )
        )

        if existing.scalars().first():
            raise ValidationException(
                "Payment for this order already exists",
                "order_id"
            )

        # Yangi to'lov yaratish
        payment = Payment(
            user_id=user_id,
            order_id=payment_data.order_id,
            amount=payment_data.amount,
            currency=payment_data.currency,
            payment_method=payment_data.payment_method,
            description=payment_data.description,
            metadata=json.dumps(payment_data.metadata) if payment_data.metadata else None,
            status=PaymentStatus.PENDING
        )

        self.db.add(payment)
        await self.db.commit()
        await self.db.refresh(payment)

        # Event yuborish
        await self._publish_event(
            "payment.created",
            {
                "payment_id": str(payment.id),
                "user_id": user_id,
                "amount": payment.amount,
                "order_id": payment.order_id
            }
        )

        logger.info(f"Payment created: {payment.id}")
        return PaymentResponse.from_orm(payment)

    async def get_payment(self, payment_id: UUID, user_id: str) -> PaymentResponse:
        """
        To'lovni ID bilan olish
        """
        result = await self.db.execute(
            select(Payment).where(
                and_(
                    Payment.id == payment_id,
                    Payment.user_id == user_id
                )
            )
        )

        payment = result.scalars().first()
        if not payment:
            raise NotFoundException(
                f"Payment {payment_id} not found",
                "payment"
            )

        return PaymentResponse.from_orm(payment)

    async def confirm_payment(
            self,
            payment_id: UUID,
            user_id: str,
            confirm_data: PaymentConfirmRequest
    ) -> PaymentResponse:
        """
        To'lovni tasdiqlash
        """
        logger.info(f"Confirming payment: {payment_id}")

        result = await self.db.execute(
            select(Payment).where(
                and_(
                    Payment.id == payment_id,
                    Payment.user_id == user_id
                )
            )
        )

        payment = result.scalars().first()
        if not payment:
            raise NotFoundException(
                f"Payment {payment_id} not found",
                "payment"
            )

        if payment.status != PaymentStatus.PENDING:
            raise ValidationException(
                f"Payment cannot be confirmed. Current status: {payment.status}"
            )

        # Statusni yangilash
        payment.status = confirm_data.status
        payment.provider_transaction_id = confirm_data.provider_transaction_id
        payment.updated_at = datetime.utcnow()

        if confirm_data.status == PaymentStatus.COMPLETED:
            payment.completed_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(payment)

        # Event yuborish
        await self._publish_event(
            f"payment.{payment.status}",
            {
                "payment_id": str(payment.id),
                "user_id": user_id,
                "status": payment.status
            }
        )

        logger.info(f"Payment confirmed: {payment.id}, status: {payment.status}")
        return PaymentResponse.from_orm(payment)

    async def list_payments(
            self,
            user_id: str,
            page: int = 1,
            page_size: int = 20
    ) -> dict:
        """
        Foydalanuvchining barcha to'lovlarini ro'yxati
        """
        offset = (page - 1) * page_size

        # Total count
        count_result = await self.db.execute(
            select(Payment).where(Payment.user_id == user_id)
        )
        total = len(count_result.scalars().all())

        # Paginated results
        result = await self.db.execute(
            select(Payment)
            .where(Payment.user_id == user_id)
            .order_by(desc(Payment.created_at))
            .offset(offset)
            .limit(page_size)
        )

        payments = result.scalars().all()

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [PaymentResponse.from_orm(p) for p in payments]
        }

    async def _publish_event(self, event_type: str, data: dict) -> None:
        """
        RabbitMQ orqali event yuborish
        """
        if not self.rabbitmq_channel:
            logger.warning("RabbitMQ channel not available")
            return

        try:
            exchange = await self.rabbitmq_channel.declare_exchange(
                'payment_events',
                aio_pika.ExchangeType.TOPIC,
                durable=True
            )

            message = aio_pika.Message(
                body=json.dumps({
                    "event": event_type,
                    "timestamp": datetime.utcnow().isoformat(),
                    "data": data
                }).encode()
            )

            await exchange.publish(message, routing_key=f"payment.{event_type}")
            logger.info(f"Event published: {event_type}")
        except Exception as e:
            logger.error(f"Failed to publish event: {str(e)}")

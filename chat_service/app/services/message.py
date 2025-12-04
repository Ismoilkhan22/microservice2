from doctest import master

from pyexpat.errors import messages
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_
from datetime import datetime
from uuid import UUID
import redis.asyncio as redis
from sqlalchemy.testing.suite.test_reflection import metadata

from shared import NotFoundException, ValidationException
from shared.logger import setup_logger
from chat_service.app.models.message import ChatMessage, ChatRoom
from chat_service.app.schemas.message import  MessageResponse, MessageCreate, MessageUpdate


logger = setup_logger(__name__)


class MessageService:
    """
    chat habarlarning besnes logikasi
    """

    def __init__(self, db:AsyncSession, redis_client:redis.Redis = None):
        self.db = db
        self.redis_client = redis_client

    async def create_message(
            self,
            room_id:str,
            user_id:str,
            message_data: MessageCreate
    )->MessageResponse:
        """
        yangi habar yaratish
        """
        logger.info(f"creating message in room{room_id} from user {user_id}")

        # Room mavjudligini tekshirish
        room_result = await self.db.execute(
            select(ChatRoom).where(ChatRoom.room_id == room_id)
        )
        room = room_result.scalars().first()

        if not room:
            raise NotFoundException(f"Room {room_id} not found", "room")

        # xabar yaratish

        message = ChatMessage(
            room_id=room_id,
            user_id=user_id,
            message=message_data.message,
            message_type=message_data.message_type,
            file_url=message_data.file_url,
            file_type=message_data.file_type,
            metadata=message_data.metadata
        )
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        # redis cache ga saqlash qo'shimch tezlik uchun
        if self.redis_client:
            cache_key = f"messages:{room_id}:latest"
            await self.redis_client.setex(
                cache_key,
                3600,
                str(message.id)
            )

        logger.info(f"message created: {message.id}")
        return MessageResponse.from_orm(message)

    async def get_message(self, message_id: UUID)-> MessageResponse:
        """
       Xabarni id bilan olish
        """
        result = await self.db.execute(
            select(ChatMessage).where(ChatMessage.id == message_id)
        )

        message = result.scalars().first()
        if not message:
            raise NotFoundException(f"Message {message_id} not found ", "message")
        return MessageResponse.from_orm(message)


    async def update_message(
            self,
            message_id:UUID,
            user_id:str,
            update_data:MessageUpdate
    )-> MessageResponse:
        """
        xabarni yangilash

        """
        logger.info(f"updating message ", {message_id})
        result = await self.db.execute(
            select(ChatMessage).where(ChatMessage.id == message_id)
        )

        message = result.scalars().first()
        if not message:
            raise NotFoundException(f"Message {message_id} not found ", "message")

        # faqat habar egasiga o'zgartirishga ruxsat

        if message.user_id != user_id:
            raise ValidationException("You can only your own messages")

        if update_data.message:
            message.message = update_data.message
            message.is_edited = True
            message.edited_at = datetime.utcnow()

        if update_data.is_read is not None:
            message.is_read = str(update_data.is_read)


        await self.db.commit()
        await self.db.refresh(message)

        logger.info(f"message updated:{message.id}")
        return MessageResponse.from_orm(message)



    async def delete_message(self, message_id:UUID, user_id:str)-> None:
        """
        Xabarni o'chirish
        :param message_id:
        :param user_id:
        :return:
        """
        result = await self.db.execute(
            select(ChatMessage).where(ChatMessage.id == message_id)
        )

        message= result.scalars().first()

        if not message:
            raise NotFoundException(f"Message {message_id} not found ", "message")

        if message.user_id != user_id:
            raise ValidationException("you can only your own messagess")

        await self.db.delete(message)
        await self.db.commit()

        logger.info(f"Message deleted: {message_id}")


    async def get_room_message(
            self,
            room_id:str,
            page:int=1,
            page_size:int=50
    )-> dict:
        """
        Room dagi xabarlar (pagination)
        """
        offset = (page-1)*page_size

        # total_count

        count_result = await self.db.excute(
            select(ChatMessage).where(ChatMessage.room_id == room_id)
        )
        total = len(count_result.scalars().all())

        # pagination result
        result = await self.db.execute(
            select(ChatMessage)
            .where(ChatMessage.room_id == room_id)
            .order_by(desc(ChatMessage.created_at))
            .offset(offset)
            .limit(page_size)
        )
        messages = result.scalars().all()

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": [MessageResponse.from_orm(m) for m in messages]
        }






































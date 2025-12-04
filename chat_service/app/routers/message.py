# chat-service/app/routers/message.py
# ============================================
# CHAT MESSAGE ENDPOINTS
# ============================================

from fastapi import APIRouter, Depends, HTTPException, Query
from six import reraise
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from watchfiles import awatch

from shared.dependencies import get_user_id
from shared.logger import setup_logger
from shared.exceptions import NotFoundException, ValidationException
from chat_service.app.database.session import get_db
from chat_service.app.services.message import MessageService
from chat_service.app.schemas.message import (
    MessageCreate, MessageResponse, MessageUpdate, MessageListResponse
)

logger = setup_logger(__name__)
router = APIRouter(prefix="/messages", tags=["messages"])


@router.post("", response_model=MessageResponse, status_code=201)
async def create_message(
        room_id:str = Query(..., min_length=1),
        message_data:MessageCreate = None,
        user_id: str = Depends(get_user_id),
        db:AsyncSession = Depends(get_db)
):
    """
    Yangi habar yaratish

    """
    try:
        service = MessageService(db)
        return await service.create_message(room_id, user_id, message_data)
    except (NotFoundException, ValidationException) as e:
        raise HTTPException(status_code=400, datail=str(e.message))
    except Exception as e:
        logger.error(f"error creating message: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/message_id", response_model=MessageResponse)
async def get_message(
        message_id:UUID,
        user_id:str = Depends(get_user_id),
        db:AsyncSession = Depends(get_db)
):
    """
    Xabarni olish

    """
    try:
        service = MessageService(db)
        return await service.get_message(message_id)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e.message))
    except Exception as e:
        logger.error(f"error fetching message: {str(e.message)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{message_id}", response_model=MessageResponse)
async def update_message(
        message_id: UUID,
        update_data: MessageUpdate,
        user_id:str = Depends(get_user_id),
        db:AsyncSession = Depends(get_db)
):
    """
    Xabarni yangilash
    """

    try:
        service = MessageService(db)
        return await service.update_message(message_id, user_id, update_data)
    except (NotFoundException, ValidationException) as e:
        raise HTTPException(status_code=400, detail=str(e.message))

    except Exception as e:
        logger.error(f" Error updating message: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/room/{room_id}", response_model=MessageResponse)
async def get_room_message(
        room_id:str = Query(..., min_length=1),
        page:int = Query(1,ge=1),
        page_size = Depends(get_user_id),
        db:AsyncSession = Depends(get_db)
):
    """
        room dagi habarlar
    """
    try:
        service = MessageService(db)
        result = await service.get_room_message(room_id, page, page_size)
        return result

    except Exception as e:
        logger.error(f" Error fetching message: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

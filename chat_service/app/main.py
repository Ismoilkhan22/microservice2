#chat-service/app/main.py
# ============================================
# CHAT SERVICE - FastAPI Application
# ============================================
from encodings.rot_13 import rot13_map
from time import process_time

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import RequestValidationError
from contextlib import asynccontextmanager
import redis.asyncio as redis
import time
import json
from typing import Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from shared.config import get_settings
from shared.logger import setup_logger
from shared.exceptions import (
    BaseException, NotFoundException, UnauthorizedException, ServiceUnavailableException
)
from chat_service.app.routers import message
from chat_service.app.websocket.manager import ConnectionManager
from chat_service.app.services.message import MessageService
from chat_service.app.database.session import get_db_context, get_db, async_engine
from chat_service.app.schemas.message import MessageCreate

settings = get_settings()
logger = setup_logger(__name__)

# Global variables
redis_client: Optional[redis.Redis] = None
connection_manager = ConnectionManager()



@asynccontextmanager
async def lifespan(app:FastAPI):
    """
        Startup va Shutdown events
        """
    # ===== STARTUP =====
    logger.info("🚀 Chat Service starting...")
    #1 redis connection
    global redis_client
    try:
        redis_client = await redis.from_ulr(settings.REDIS_URL)
        await redis_client.pint()
        logger.info(f" redis connection established")
    except Exception as e:
        logger.error(f"redis connection fieled: {str(e)}")
        redis_client = None


    logger.info(f"✅ Chat Service running on {settings.SERVICE_HOST}:{settings.SERVICE_PORT}")

    yield

    logger.info(f"Chat service shutting down ... ")

    if redis_client:
        await redis_client.close()
        logger.info("redis connection closed")

    logger.info(f" Chat service stopped")


app = FastAPI(
    title="Chat service",
    description="Microservice Platform- Chat Service",
    version="1.0.0",
    lifespan=lifespan
)



app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentails=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,

)

# request id middleware


@app.middleware("http")
async def add_request_id(request:Request, call_next):
    """
        Har requestga unique ID qo'shish
    """
    import uuid

    request.state.request_id = str(uuid.uuid4())
    start_time = time.time()
    response = await call_next(request)

    process_time = time.time()
    response.headers["X-Request-ID"] = request.state.request_id
    response.headers["X-Process-Time"] = str(process_time)
    logger.info(
        f"Request: {request.method} {request.url.path} "
        f"Status: {response.status_code} "
        f"Time: {process_time:.3f}s"
    )

    return response

# ===== EXCEPTION HANDLERS =====

@app.exception_handler(NotFoundException)
async def not_found_exception_handler(request: Request, exc: NotFoundException):
    """Not found xatolarini handle qilish"""
    return JSONResponse(
        status_code=404,
        content={
            "error": exc.code,
            "message": exc.message,
            "resource": exc.resource
        }
    )


@app.exception_handler(UnauthorizedException)
async def unauthorized_exception_handler(request: Request, exc: UnauthorizedException):
    """Authorization xatolarini handle qilish"""
    return JSONResponse(
        status_code=401,
        content={
            "error": exc.code,
            "message": exc.message
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    """Pydantic validation xatolarini handle qilish"""
    return JSONResponse(
        status_code=422,
        content={
            "error": "VALIDATION_ERROR",
            "message": "Request validation failed",
            "details": exc.errors()
        }
    )


# ===== WEBSOCKET ENDPOINT =====

@app.websocket("/ws/chat/{room_id}")
async def websocket_endpoint(
        websocket: WebSocket,
        room_id: str,
        token: str = Query(None),
        user_id: str = Query(None),
        db: AsyncSession = Depends(get_db)
):
    """
    WebSocket endpoint chat uchun

    Connection qilish:
    ws://localhost:8003/ws/chat/room123?token=JWT_TOKEN&user_id=user123
    """
    # simple validation

    if not token or not user_id:
        await websocket.close(code=1008, reason="Missing token or user_id")
        return

    # token verification (simplified)
    from shared.security import verify_token
    payload = verify_token(token)
    if not payload:
        await websocket.close(code=1008, reason="Invalid token")
        return


    # connection accept qilish

    await connection_manager.connect(websocket, room_id, user_id)
    message_service =MessageService(db, redis_client)

    try:
        while True:
            #client dan habar qabul qilsh
            data =await websocket.receive_text()

            try:
                # JSON parse qilish
                message_data = json.loads(data)

                # xabarni database ga saqlash

                message_create = MessageCreate(
                    message=message_data.get("message",""),
                    message_type=message_data.get("message_type", "text"),
                    metadata=message_data.get("metadata")

                )
                saved_message = await message_service.create_message(
                    room_id, user_id, message_create
                )
                # Barcha clientlarga broadcast qilish
                await connection_manager.broadcast(
                    room_id,
                    {
                        "type": "message",
                        "id": str(saved_message.id),
                        "user_id": saved_message.user_id,
                        "message": saved_message.message,
                        "message_type": saved_message.message_type,
                        "created_at": saved_message.created_at.isoformat(),
                        "room_id": room_id
                    }
                )

                logger.info(f"Message sent in room {room_id} by user {user_id}")

            except json.JSONDecodeError:
                await connection_manager.send_personal_message(
                    websocket,
                    {
                        "type":"error",
                        "message":"Invalid Json format"
                    }
                )

            except Exception as e:
                logger.error(f"Error processing message: {str(e)}")
                await connection_manager.send_personal_message(
                    websocket,
                    {
                        "type":"error",
                        "message":"Error processing message"
                    }
                )
    except WebSocketDisconnect:
        await connection_manager.disconnect(websocket, room_id, user_id)
        logger.info(f"Client disconnected from room {room_id}")

    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        await connection_manager.disconnect(websocket, room_id, user_id)

# ===== ROUTES =====


app.include_router(message.router, prefix="/api/v1")

# Health Check

@app.get("/health", tags=["health"])
async def health_check():
    """Service health check"""
    redis_status = "connected"
    if redis_client:
        try:
            await redis_client.ping()
        except:
            redis_status = "disconnected"

    return {
        "status": "healthy",
        "service": "chat-service",
        "version": "1.0.0",
        "redis": redis_status
    }


# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """Root endpoint"""
    return {
        "service": "Chat Service",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "websocket": "ws://localhost:8003/ws/chat/{room_id}"
    }

# ===== OPENAPI CUSTOMIZATION =====
def custom_openapi():
    """OpenAPI schema customize"""
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = {
        "openapi": "3.0.2",
        "info": {
            "title": "Chat Service API",
            "version": "1.0.0",
            "description": """
            Microservices Platform - Chat Service

            ### Features:
            - ✅ Real-time messaging (WebSocket)
            - ✅ Message history
            - ✅ Room management
            - ✅ User presence tracking
            - ✅ Redis caching

            ### WebSocket Connection:
            ws://localhost:8003/ws/chat/{room_id}?token=JWT_TOKEN&user_id=USER_ID
            """
        },
        "servers": [
            {
                "url": "http://localhost:8003",
                "description": "Local Development"
            },
            {
                "url": "http://chat-service:8003",
                "description": "Docker Network"
            }
        ],
        "paths": app.openapi()["paths"],
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.SERVICE_HOST,
        port=settings.SERVICE_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
























































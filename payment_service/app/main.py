# payment-service/app/main.py
# ============================================
# PAYMENT SERVICE - FastAPI Application
# ============================================


from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import RequestValidationError
from contextlib import asynccontextmanager
import aio_pika
import time

from sqlalchemy.event import listens_for

from shared.config import get_settings
from shared.logger import setup_logger
from shared.exceptions import (
    BaseException, ValidationException, NotFoundException,
    UnauthorizedException, ServiceUnavailableException
)
from payment_service.app.routers import payment
from payment_service.app.database.session import get_db_context
from payment_service.app.database.base import Base, get_engine

settings = get_settings()
logger = setup_logger(__name__)

rabbitmq_connection = None
rabbitmq_channel = None


@asynccontextmanager
async def lifespan(app:FastAPI):
    """
    Startup va SHUtdown events

    """
    # 1. Database connection test
    logger.info("Payment Service starting ..")
    try:
        engine = get_engine()
        logger.info("Database connection established")

    except Exception as e:
        logger.error(f" Database connection failed: {str(e)}")
        raise
    # 2. RabbitMQ connection
    global  rabbitmq_connection, rabbitmq_channel
    try:
        rabbitmq_connection = await aio_pika.connect_robust(
            settings.RABBITMQ_URL
        )
        rabbitmq_channel = await rabbitmq_connection.channel()
    # Exchange declare

        exchange = await rabbitmq_channel.declare_exchange(
            'payment_events',
            aio_pika.ExchangeType.TOPIC,
            durable=True
        )
        logger.info("✅ RabbitMQ connection established")
    except Exception as e:
        logger.error(f"⚠️  RabbitMQ connection failed: {str(e)}")
        logger.warning("Service will work without RabbitMQ")
    logger.info(f"✅ Payment Service running on {settings.SERVICE_HOST}:{settings.SERVICE_PORT}")

    yield


    logger.info("payment service shutting down")
    if rabbitmq_connection:
        await rabbitmq_connection.close()
        logger.info("RabmitMQ connection closed")

    logger.info("payment service stopped")



# Fast api aplication

app = FastAPI(
    title="Payment service",
    description="Microservice Platform - Payment Service",
    version="1.0.0",
    lifespan=lifespan,

)

# ===== MIDDLEWARE =====

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)


# Request ID Middleware

@app.middleware("http")
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """
    Har requestga unique ID qo'shish
    """
    import uuid
    request.state.request_id = str(uuid.uuid4())

    start_time = time.time()
    response = await call_next(request)

    process_time = time.time() - start_time
    response.headers["X-Request-ID"] = request.state.request_id
    response.headers["X-Process-Time"] = str(process_time)

    logger.info(
        f"Request: {request.method} {request.url.path} "
        f"Status: {response.status_code} "
        f"Time: {process_time:.3f}s "
        f"ID: {request.state.request_id}"
    )

    return response

# ===== EXCEPTION HANDLERS =====

@app.exception_handler(ValidationException)
async def validation_exception_handler(request: Request, exc: ValidationException):
    """Validation xatolarini handle qilish"""
    return JSONResponse(
        status_code=400,
        content={
            "error": exc.code,
            "message": exc.message,
            "field": exc.field,
            "request_id": getattr(request.state, "request_id", None)
        }
    )


@app.exception_handler(NotFoundException)
async def not_found_exception_handler(request: Request, exc: NotFoundException):
    """Not found xatolarini handle qilish"""
    return JSONResponse(
        status_code=404,
        content={
            "error": exc.code,
            "message": exc.message,
            "resource": exc.resource,
            "request_id": getattr(request.state, "request_id", None)
        }
    )


@app.exception_handler(UnauthorizedException)
async def unauthorized_exception_handler(request: Request, exc: UnauthorizedException):
    """Authorization xatolarini handle qilish"""
    return JSONResponse(
        status_code=401,
        content={
            "error": exc.code,
            "message": exc.message,
            "request_id": getattr(request.state, "request_id", None)
        }
    )
@app.exception_handler(ServiceUnavailableException)
async def service_unavailable_handler(request: Request, exc: ServiceUnavailableException):
    """Service unavailable"""
    return JSONResponse(
        status_code=503,
        content={
            "error": exc.code,
            "message": exc.message,
            "service": exc.service,
            "request_id": getattr(request.state, "request_id", None)
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
            "details": exc.errors(),
            "request_id": getattr(request.state, "request_id", None)
        }
    )



# ===== ROUTES =====

# Routers
app.include_router(payment.router, prefix="/api/v1")

# Health Check
@app.get("/health", tags=["health"])
async def health_check():
    """Service health check"""
    return {
        "status": "healthy",
        "service": "payment-service",
        "version": "1.0.0"
    }

# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """Root endpoint"""
    return {
        "service": "Payment Service",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


# ===== OPENAPI CUSTOMIZATION =====

def custom_openapi():
    """OpenAPI schema customize"""
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = {
        "openapi": "3.0.2",
        "info": {
            "title": "Payment Service API",
            "version": "1.0.0",
            "description": """
            Microservices Platform - Payment Service

            ### Features:
            - ✅ Payment creation and management
            - ✅ Real-time payment status updates
            - ✅ Event-driven architecture
            - ✅ Comprehensive error handling
            - ✅ Request tracking

            ### Security:
            - JWT Authentication
            - Rate Limiting
            - CORS Protection
            """
        },
        "servers": [
            {
                "url": "http://localhost:8002",
                "description": "Local Development"
            },
            {
                "url": "http://payment-service:8002",
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
        log_level=settings.LOG_LEVEL.lower(),
        access_log=settings.ENVIRONMENT != "production"
    )




















































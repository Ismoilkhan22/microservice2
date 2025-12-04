# payment-service/app/database/session.py
# ============================================
# DATABASE SESSION MANAGEMENT
# ============================================

from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from shared.config import get_settings
from payment_service.app.database.base import Base
from contextlib import asynccontextmanager

settings = get_settings()

# PostgreSQL async connection
async_engine = create_async_engine(
    settings.DATABASE_URL.replace("postgresql", "postgresql+asyncpg"),
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=10,
    pool_recycle=settings.DB_POOL_RECYCLE,
    pool_pre_ping=settings.DB_POOL_PRE_PING,
    echo=settings.DB_ECHO,
)

AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

async def get_db() -> AsyncSession:
    """
    Dependency - har requestda DB session
    """
    async with AsyncSessionLocal() as session:
        yield session

@asynccontextmanager
async def get_db_context():
    """Context manager - standalone code uchun"""
    async with AsyncSessionLocal() as session:
        yield session
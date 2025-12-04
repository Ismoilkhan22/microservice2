# payment-service/app/database/base.py
# ============================================
# DATABASE BASE CONFIGURATION
# ============================================

from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.pool import NullPool, QueuePool
from shared.config import get_settings

settings = get_settings()

Base = declarative_base()


def get_engine():
    """
    SQLAlchemy engine yaratish optimal pool settings bilan
    """
    if settings.ENVIRONMENT == "production":
        pool_class = QueuePool
    else:
        pool_class = QueuePool  # Local testing uchun ham QueuePool

    engine = create_engine(
        settings.DATABASE_URL,
        poolclass=pool_class,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=10,
        pool_recycle=settings.DB_POOL_RECYCLE,
        pool_pre_ping=settings.DB_POOL_PRE_PING,
        echo=settings.DB_ECHO,
        connect_args={
            "connect_timeout": 10,
            "options": "-c statement_timeout=30000"
        }
    )
    return engine





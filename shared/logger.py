# shared/logger.py
# ============================================
# LOGGING SETUP
# ============================================
import logging
import logging.handlers
import json
from datetime import datetime
from shared.config import get_settings

settings = get_settings()


class JSONFormatter(logging.Formatter):
    """JSON formatida log yozish"""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": settings.SERVICE_NAME,
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        if hasattr(record, 'user_id'):
            log_data["user_id"] = record.user_id

        if hasattr(record, 'request_id'):
            log_data["request_id"] = record.request_id

        return json.dumps(log_data)


def setup_logger(name: str) -> logging.Logger:
    """
    Logger setup
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, settings.LOG_LEVEL))

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JSONFormatter())
    logger.addHandler(console_handler)

    # File handler (production)
    if settings.ENVIRONMENT == "production":
        file_handler = logging.handlers.RotatingFileHandler(
            f"logs/{name}.log",
            maxBytes=10485760,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(JSONFormatter())
        logger.addHandler(file_handler)

    return logger



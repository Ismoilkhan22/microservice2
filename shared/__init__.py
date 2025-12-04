# shared/__init__.py
# ============================================
# SHARED PACKAGE EXPORTS
# ============================================

from .config import Settings, get_settings
from .exceptions import (
    BaseException,
    ValidationException,
    NotFoundException,
    UnauthorizedException,
    ForbiddenException,
    ConflictException,
    ServiceUnavailableException,
    DatabaseException
)
from .logger import setup_logger, JSONFormatter
from .security import (
    hash_password,
    verify_password,
    create_access_token,
    verify_token
)
from .dependencies import get_current_user, get_user_id

__all__ = [
    "Settings",
    "get_settings",
    "BaseException",
    "ValidationException",
    "NotFoundException",
    "UnauthorizedException",
    "ForbiddenException",
    "ConflictException",
    "ServiceUnavailableException",
    "DatabaseException",
    "setup_logger",
    "JSONFormatter",
    "hash_password",
    "verify_password",
    "create_access_token",
    "verify_token",
    "get_current_user",
    "get_user_id"
]
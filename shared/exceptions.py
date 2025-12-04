# shared/exceptions.py
# ============================================
# CUSTOM EXCEPTIONS
# ============================================

class BaseException(Exception):
    """Base custom exception"""
    def __init__(self, message: str, code: str = None):
        self.message = message
        self.code = code or self.__class__.__name__
        super().__init__(self.message)


class ValidationException(BaseException):
    """Data validation xatosi"""
    def __init__(self, message: str, field: str = None):
        self.field = field
        super().__init__(message, "VALIDATION_ERROR")



class NotFoundException(BaseException):
    """Resurs topilmadi"""
    def __init__(self, message: str, resource: str = None):
        self.resource = resource
        super().__init__(message, "NOT_FOUND")


class UnauthorizedException(BaseException):
    """Autentifikatsiya xatosi"""
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, "UNAUTHORIZED")


class ForbiddenException(BaseException):
    """Ruxsat yo'q"""
    def __init__(self, message: str = "Forbidden"):
        super().__init__(message, "FORBIDDEN")



class ConflictException(BaseException):
    """Conflict - duplicate entry"""
    def __init__(self, message: str, resource: str = None):
        self.resource = resource
        super().__init__(message, "CONFLICT")


class ServiceUnavailableException(BaseException):
    """Service unavailable"""
    def __init__(self, message: str, service: str = None):
        self.service = service
        super().__init__(message, "SERVICE_UNAVAILABLE")

class DatabaseException(BaseException):
    """Database xatosi"""
    def __init__(self, message: str):
        super().__init__(message, "DATABASE_ERROR")


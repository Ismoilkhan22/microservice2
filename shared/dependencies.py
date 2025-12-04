# shared/dependencies.py
# ============================================
# COMMON DEPENDENCIES
# ============================================

from fastapi import Depends, Header, HTTPException
from shared.security import verify_token
from shared.exceptions import UnauthorizedException
from typing import Optional, Dict, Any


async def get_current_user(authorization:Optional[str]=Header(None)) ->Dict[str, Any]:
    """
        Current user ni olish JWT tokendan
        """
    if not authorization:
        raise UnauthorizedException("Missing authorization header")

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise UnauthorizedException("Invalid authentication scheme")
    except ValueError:
        raise UnauthorizedException("Invalid authorization header")

    payload = verify_token(token)
    if not payload:
        raise UnauthorizedException("Invalid or expired token")

    return payload



async def get_user_id(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> str:
    """User ID olish"""
    user_id = current_user.get("sub")
    if not user_id:
        raise UnauthorizedException("Invalid token payload")
    return user_id























































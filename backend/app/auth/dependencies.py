"""
FastAPI dependencies for authenticated routes.

Usage
-----
    from app.auth.dependencies import get_current_user, require_admin

    @router.get("/protected")
    async def protected(user = Depends(get_current_user)):
        ...

    @router.get("/admin-only")
    async def admin_only(user = Depends(require_admin)):
        ...
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError

from app.auth.security import decode_access_token
from app.models.user import User

_bearer = HTTPBearer(auto_error=True)
_bearer_optional = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> User:
    token = credentials.credentials
    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        user_id: str = payload.get("sub", "")
        if not user_id:
            raise exc
    except JWTError:
        raise exc

    user = await User.filter(id=user_id, is_active=True).first()
    if not user:
        raise exc
    return user

async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_optional),
) -> User | None:
    if credentials is None:
        return None

    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


async def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return user

from __future__ import annotations

from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.config import settings


async def get_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    async with request.app.state.sessionmaker() as session:
        yield session


async def get_redis(request: Request):
    return request.app.state.redis


async def get_minio(request: Request):
    return request.app.state.minio


async def get_minio_public(request: Request):
    return request.app.state.minio_public


# Import after get_db to avoid circular imports
from app.auth import get_current_user as _get_current_user  # noqa: E402


async def require_registered_user(
    user: User = Depends(_get_current_user),
) -> User:
    if not user.is_registered:
        raise HTTPException(status_code=403, detail="Registration required")
    return user


async def require_admin(
    user: User = Depends(_get_current_user),
) -> User:
    if user.telegram_id not in settings.admin_telegram_ids:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

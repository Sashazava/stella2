from __future__ import annotations

import time
from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException, Header, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from aiogram.utils.web_app import safe_parse_webapp_init_data

from app.config import settings
from app.models.user import User
from app.deps import get_db


async def get_or_create_user(db: AsyncSession, tg_user) -> User:
    result = await db.execute(select(User).where(User.telegram_id == tg_user.id))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(
            telegram_id=tg_user.id,
            first_name=tg_user.first_name,
            last_name=tg_user.last_name,
            username=tg_user.username,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    return user


async def get_current_user(
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not authorization.startswith("tma "):
        raise HTTPException(status_code=401, detail="Invalid auth scheme")
    raw_init_data = authorization[4:]
    try:
        data = safe_parse_webapp_init_data(token=settings.bot_token, init_data=raw_init_data)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid initData")
    if time.time() - data.auth_date.timestamp() > 3600:
        raise HTTPException(status_code=401, detail="initData expired")
    user = await get_or_create_user(db, data.user)
    return user

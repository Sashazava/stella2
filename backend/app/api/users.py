from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.deps import get_db, get_minio_public, require_registered_user
from app.models.user import User
from app.schemas.user import (
    AvatarUploadResponse,
    UserProfile,
    UserPublic,
    UserRegistration,
    UserUpdate,
)
from app.services.storage import BUCKET_AVATARS, get_upload_url

router = APIRouter(prefix="/api/users", tags=["users"])


@router.post("/register", response_model=UserProfile)
async def register_user(
    data: UserRegistration,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> UserProfile:
    """Complete user registration after Telegram auth."""
    user.first_name = data.first_name
    user.last_name = data.last_name
    user.phone = data.phone
    user.city = data.city
    user.latitude = data.latitude
    user.longitude = data.longitude
    user.is_registered = True
    await db.commit()
    await db.refresh(user)
    return UserProfile.model_validate(user)


@router.get("/profile", response_model=UserProfile)
async def get_profile(
    user: User = Depends(get_current_user),
) -> UserProfile:
    """Return current user's full profile."""
    return UserProfile.model_validate(user)


@router.patch("/profile", response_model=UserProfile)
async def update_profile(
    data: UserUpdate,
    user: User = Depends(require_registered_user),
    db: AsyncSession = Depends(get_db),
) -> UserProfile:
    """Update current user's profile fields."""
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    await db.commit()
    await db.refresh(user)
    return UserProfile.model_validate(user)


@router.post("/avatar", response_model=AvatarUploadResponse)
async def get_avatar_upload_url(
    user: User = Depends(get_current_user),
    minio_public=Depends(get_minio_public),
) -> AvatarUploadResponse:
    """Return presigned PUT URL for avatar upload.

    Client uploads directly to MinIO, then calls PATCH /profile with avatar_url.
    """
    object_key = f"avatars/{user.id}/{uuid4()}.jpg"
    upload_url = get_upload_url(minio_public, BUCKET_AVATARS, object_key)
    return AvatarUploadResponse(upload_url=upload_url, object_key=object_key)


@router.get("/{telegram_id}/public", response_model=UserPublic)
async def get_public_profile(
    telegram_id: int,
    db: AsyncSession = Depends(get_db),
) -> UserPublic:
    """Return public seller profile (no phone number). No auth required."""
    result = await db.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return UserPublic.model_validate(user)

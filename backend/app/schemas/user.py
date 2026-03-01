from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UserRegistration(BaseModel):
    first_name: str
    last_name: str | None = None
    phone: str
    city: str
    latitude: float | None = None
    longitude: float | None = None


class UserUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    city: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    avatar_url: str | None = None


class UserProfile(BaseModel):
    id: UUID
    telegram_id: int
    first_name: str
    last_name: str | None
    username: str | None
    phone: str | None
    city: str | None
    avatar_url: str | None
    is_registered: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class UserPublic(BaseModel):
    telegram_id: int
    first_name: str
    last_name: str | None
    username: str | None
    city: str | None
    avatar_url: str | None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
    # NOTE: NO phone field


class AvatarUploadResponse(BaseModel):
    upload_url: str
    object_key: str

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.listing import ListingStatus


class ListingCreate(BaseModel):
    title: str
    description: str
    price: Decimal
    currency: str = "RUB"
    category_id: UUID


class ListingUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    price: Decimal | None = None
    currency: str | None = None
    category_id: UUID | None = None


class ListingPhotoResponse(BaseModel):
    id: UUID
    url: str  # presigned GET URL
    position: int
    model_config = ConfigDict(from_attributes=True)


class SellerInfo(BaseModel):
    telegram_id: int
    first_name: str
    last_name: str | None
    username: str | None
    avatar_url: str | None
    model_config = ConfigDict(from_attributes=True)


class CategoryInfo(BaseModel):
    id: UUID
    name: str
    slug: str
    model_config = ConfigDict(from_attributes=True)


class ListingResponse(BaseModel):
    id: UUID
    title: str
    description: str
    price: Decimal
    currency: str
    status: ListingStatus
    city: str | None
    category: CategoryInfo
    seller: SellerInfo
    photos: list[ListingPhotoResponse]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class PhotoUploadResponse(BaseModel):
    upload_url: str
    object_key: str
    position: int


class PhotoConfirm(BaseModel):
    object_key: str
    position: int

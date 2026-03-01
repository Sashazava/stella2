from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    per_page: int
    total_pages: int


class CategoryInfo(BaseModel):
    id: UUID
    name: str
    slug: str
    icon: str | None
    model_config = ConfigDict(from_attributes=True)


class SellerInfo(BaseModel):
    id: UUID
    first_name: str
    last_name: str | None
    username: str | None
    avatar_url: str | None
    model_config = ConfigDict(from_attributes=True)


class ListingCard(BaseModel):
    id: UUID
    title: str
    price: Decimal
    currency: str
    city: str | None
    first_photo_url: str | None
    category: CategoryInfo | None
    seller: SellerInfo
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

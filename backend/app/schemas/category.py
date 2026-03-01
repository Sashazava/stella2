from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CategoryResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    icon: str | None
    model_config = ConfigDict(from_attributes=True)


class CategoryPropose(BaseModel):
    name: str

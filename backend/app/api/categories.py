from __future__ import annotations

import re
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db, get_redis, require_admin, require_registered_user
from app.models.category import Category
from app.models.user import User
from app.schemas.category import CategoryPropose, CategoryResponse
from app.services.redis import get_cached, invalidate, set_cached

router = APIRouter(prefix="/api/categories", tags=["categories"])

CACHE_KEY = "categories:approved"
CACHE_TTL = 300  # 5 minutes


def slugify(name: str) -> str:
    """Transliterate Russian text to URL-safe slug."""
    translit_map = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch',
        'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
    }
    result = name.lower()
    for ru, en in translit_map.items():
        result = result.replace(ru, en)
    result = re.sub(r'[^a-z0-9]+', '-', result)
    return result.strip('-')


@router.get("", response_model=list[CategoryResponse])
async def list_categories(
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> list[CategoryResponse]:
    """Return list of approved categories, cached in Redis for 5 minutes."""
    cached = await get_cached(redis, CACHE_KEY)
    if cached is not None:
        return [CategoryResponse(**item) for item in cached]

    result = await db.execute(
        select(Category).where(Category.is_approved == True).order_by(Category.name)  # noqa: E712
    )
    categories = result.scalars().all()

    await set_cached(
        redis,
        CACHE_KEY,
        [CategoryResponse.model_validate(c).model_dump(mode="json") for c in categories],
        CACHE_TTL,
    )
    return categories


@router.post("/propose", response_model=CategoryResponse, status_code=201)
async def propose_category(
    body: CategoryPropose,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_registered_user),
) -> CategoryResponse:
    """Propose a new category (pending approval)."""
    slug = slugify(body.name)
    category = Category(
        name=body.name,
        slug=slug,
        is_approved=False,
        created_by_id=current_user.id,
    )
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category


@router.patch("/{id}/approve", response_model=CategoryResponse)
async def approve_category(
    id: UUID,
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
    current_user: User = Depends(require_admin),
) -> CategoryResponse:
    """Approve a proposed category and invalidate cache."""
    result = await db.execute(select(Category).where(Category.id == id))
    category = result.scalar_one_or_none()
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")

    category.is_approved = True
    await db.commit()
    await db.refresh(category)
    await invalidate(redis, CACHE_KEY)
    return category

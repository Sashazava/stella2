from __future__ import annotations

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from minio import Minio
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.deps import get_db, get_minio_public, get_redis
from app.models.listing import Listing, ListingStatus
from app.schemas.common import CategoryInfo, ListingCard, PaginatedResponse, SellerInfo
from app.services.redis import get_cached, set_cached
from app.services.storage import BUCKET_LISTINGS, get_download_url

router = APIRouter(prefix="/api/catalog", tags=["catalog"])


@router.get("", response_model=PaginatedResponse)
async def get_catalog(
    city: str | None = Query(None),
    category_id: UUID | None = Query(None),
    sort: Literal["recent", "price_asc", "price_desc"] = Query("recent"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
    minio_public: Minio = Depends(get_minio_public),
) -> PaginatedResponse:
    cache_key = (
        f"catalog:{city or 'all'}:{category_id or 'all'}:{sort}:{page}:{per_page}"
    )
    cached = await get_cached(redis, cache_key)
    if cached is not None:
        return PaginatedResponse(**cached)

    # Build filter conditions
    conditions = [Listing.status == ListingStatus.approved]
    if city:
        conditions.append(func.lower(Listing.city) == func.lower(city))
    if category_id:
        conditions.append(Listing.category_id == category_id)

    # Count total matching records
    count_stmt = select(func.count(Listing.id)).where(*conditions)
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    # Build fetch query with sort
    stmt = select(Listing).where(*conditions)
    if sort == "price_asc":
        stmt = stmt.order_by(Listing.price.asc())
    elif sort == "price_desc":
        stmt = stmt.order_by(Listing.price.desc())
    else:
        stmt = stmt.order_by(Listing.created_at.desc())

    # Pagination + eager loading
    stmt = (
        stmt.offset((page - 1) * per_page)
        .limit(per_page)
        .options(
            selectinload(Listing.photos),
            joinedload(Listing.category),
            joinedload(Listing.seller),
        )
    )

    result = await db.execute(stmt)
    listings = result.scalars().unique().all()

    # Build response items
    items: list[ListingCard] = []
    for listing in listings:
        first_photo_url: str | None = None
        if listing.photos:
            # photos are ordered by position via relationship definition
            first_photo = listing.photos[0]
            try:
                first_photo_url = get_download_url(
                    minio_public, BUCKET_LISTINGS, first_photo.object_key
                )
            except Exception:
                first_photo_url = None

        category_info: CategoryInfo | None = None
        if listing.category:
            category_info = CategoryInfo.model_validate(listing.category)

        seller_info = SellerInfo.model_validate(listing.seller)

        items.append(
            ListingCard(
                id=listing.id,
                title=listing.title,
                price=listing.price,
                currency=listing.currency,
                city=listing.city,
                first_photo_url=first_photo_url,
                category=category_info,
                seller=seller_info,
                created_at=listing.created_at,
            )
        )

    total_pages = (total + per_page - 1) // per_page
    response = PaginatedResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
    )

    # Cache for 2 minutes (120 seconds)
    await set_cached(
        redis,
        cache_key,
        response.model_dump(mode="json"),
        ttl=120,
    )

    return response

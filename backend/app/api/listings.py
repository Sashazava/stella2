from __future__ import annotations

import time
import uuid

from aiogram.utils.web_app import safe_parse_webapp_init_data
from fastapi import APIRouter, Depends, Header, HTTPException, status
from minio import Minio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import get_or_create_user
from app.config import settings
from app.deps import get_db, get_minio, get_minio_public, require_registered_user
from app.models.listing import Listing, ListingStatus
from app.models.listing_photo import ListingPhoto
from app.models.user import User
from app.schemas.listing import (
    CategoryInfo,
    ListingCreate,
    ListingPhotoResponse,
    ListingResponse,
    ListingUpdate,
    PhotoConfirm,
    PhotoUploadResponse,
    SellerInfo,
)
from app.services.storage import (
    BUCKET_LISTINGS,
    delete_object,
    generate_object_key,
    get_download_url,
    get_upload_url,
)

MAX_PHOTOS = 5

router = APIRouter(prefix="/listings", tags=["listings"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _load_options() -> list:
    return [
        selectinload(Listing.photos),
        selectinload(Listing.category),
        selectinload(Listing.seller),
    ]


def _photo_to_response(photo: ListingPhoto, minio_public: Minio) -> ListingPhotoResponse:
    url = get_download_url(minio_public, BUCKET_LISTINGS, photo.object_key)
    return ListingPhotoResponse(id=photo.id, url=url, position=photo.position)


def _listing_to_response(listing: Listing, minio_public: Minio) -> ListingResponse:
    photos = [_photo_to_response(p, minio_public) for p in listing.photos]
    return ListingResponse(
        id=listing.id,
        title=listing.title,
        description=listing.description,
        price=listing.price,
        currency=listing.currency,
        status=listing.status,
        city=listing.city,
        category=CategoryInfo.model_validate(listing.category),
        seller=SellerInfo.model_validate(listing.seller),
        photos=photos,
        created_at=listing.created_at,
    )


async def _get_listing_or_404(
    listing_id: uuid.UUID,
    db: AsyncSession,
    *,
    require_owner: User | None = None,
) -> Listing:
    result = await db.execute(
        select(Listing)
        .where(Listing.id == listing_id)
        .options(*_load_options())
    )
    listing = result.scalar_one_or_none()
    if listing is None:
        raise HTTPException(status_code=404, detail="Listing not found")
    if require_owner is not None and listing.seller_id != require_owner.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return listing


async def get_optional_user(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """Optional authentication — returns None if no valid credentials present."""
    if authorization is None:
        return None
    if not authorization.startswith("tma "):
        return None
    raw_init_data = authorization[4:]
    try:
        data = safe_parse_webapp_init_data(
            token=settings.bot_token, init_data=raw_init_data
        )
    except (ValueError, Exception):
        return None
    if time.time() - data.auth_date.timestamp() > 3600:
        return None
    return await get_or_create_user(db, data.user)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("", response_model=ListingResponse, status_code=status.HTTP_201_CREATED)
async def create_listing(
    data: ListingCreate,
    current_user: User = Depends(require_registered_user),
    db: AsyncSession = Depends(get_db),
    minio_public: Minio = Depends(get_minio_public),
) -> ListingResponse:
    """Create a new listing. Status starts as pending. City copied from seller profile."""
    listing = Listing(
        title=data.title,
        description=data.description,
        price=data.price,
        currency=data.currency,
        category_id=data.category_id,
        seller_id=current_user.id,
        status=ListingStatus.pending,
        city=current_user.city,
    )
    db.add(listing)
    await db.commit()

    # Reload with relationships eagerly
    result = await db.execute(
        select(Listing).where(Listing.id == listing.id).options(*_load_options())
    )
    listing = result.scalar_one()
    return _listing_to_response(listing, minio_public)


@router.get("/my", response_model=list[ListingResponse])
async def get_my_listings(
    current_user: User = Depends(require_registered_user),
    db: AsyncSession = Depends(get_db),
    minio_public: Minio = Depends(get_minio_public),
) -> list[ListingResponse]:
    """Return all listings (all statuses) belonging to the current user."""
    result = await db.execute(
        select(Listing)
        .where(Listing.seller_id == current_user.id)
        .options(*_load_options())
        .order_by(Listing.created_at.desc())
    )
    listings = result.scalars().all()
    return [_listing_to_response(lst, minio_public) for lst in listings]


@router.get("/{listing_id}", response_model=ListingResponse)
async def get_listing(
    listing_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    minio_public: Minio = Depends(get_minio_public),
    current_user: User | None = Depends(get_optional_user),
) -> ListingResponse:
    """Get a single listing. Non-approved listings visible only to their owner."""
    listing = await _get_listing_or_404(listing_id, db)
    if listing.status != ListingStatus.approved:
        if current_user is None or listing.seller_id != current_user.id:
            raise HTTPException(status_code=404, detail="Listing not found")
    return _listing_to_response(listing, minio_public)


@router.patch("/{listing_id}", response_model=ListingResponse)
async def update_listing(
    listing_id: uuid.UUID,
    data: ListingUpdate,
    current_user: User = Depends(require_registered_user),
    db: AsyncSession = Depends(get_db),
    minio_public: Minio = Depends(get_minio_public),
) -> ListingResponse:
    """Update a listing. Content changes (title/description/price) reset status to pending."""
    listing = await _get_listing_or_404(listing_id, db, require_owner=current_user)

    content_changed = False
    if data.title is not None and data.title != listing.title:
        listing.title = data.title
        content_changed = True
    if data.description is not None and data.description != listing.description:
        listing.description = data.description
        content_changed = True
    if data.price is not None and data.price != listing.price:
        listing.price = data.price
        content_changed = True
    if data.currency is not None:
        listing.currency = data.currency
    if data.category_id is not None:
        listing.category_id = data.category_id

    if content_changed:
        listing.status = ListingStatus.pending

    await db.commit()

    result = await db.execute(
        select(Listing).where(Listing.id == listing.id).options(*_load_options())
    )
    listing = result.scalar_one()
    return _listing_to_response(listing, minio_public)


@router.delete("/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_listing(
    listing_id: uuid.UUID,
    current_user: User = Depends(require_registered_user),
    db: AsyncSession = Depends(get_db),
    minio: Minio = Depends(get_minio),
) -> None:
    """Delete a listing and all its photos from MinIO. Owner only."""
    listing = await _get_listing_or_404(listing_id, db, require_owner=current_user)

    for photo in listing.photos:
        try:
            delete_object(minio, BUCKET_LISTINGS, photo.object_key)
        except Exception:
            pass  # Best-effort deletion

    await db.delete(listing)
    await db.commit()


@router.post("/{listing_id}/photos/upload-url", response_model=PhotoUploadResponse)
async def get_photo_upload_url(
    listing_id: uuid.UUID,
    current_user: User = Depends(require_registered_user),
    db: AsyncSession = Depends(get_db),
    minio_public: Minio = Depends(get_minio_public),
) -> PhotoUploadResponse:
    """Generate a presigned PUT URL for direct browser-to-MinIO upload. Max 5 photos."""
    listing = await _get_listing_or_404(listing_id, db, require_owner=current_user)

    if len(listing.photos) >= MAX_PHOTOS:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {MAX_PHOTOS} photos per listing allowed",
        )

    position = len(listing.photos)
    object_key = generate_object_key(str(current_user.id), "photo.jpg")
    upload_url = get_upload_url(minio_public, BUCKET_LISTINGS, object_key)

    return PhotoUploadResponse(
        upload_url=upload_url,
        object_key=object_key,
        position=position,
    )


@router.post("/{listing_id}/photos", response_model=ListingPhotoResponse)
async def confirm_photo_upload(
    listing_id: uuid.UUID,
    data: PhotoConfirm,
    current_user: User = Depends(require_registered_user),
    db: AsyncSession = Depends(get_db),
    minio_public: Minio = Depends(get_minio_public),
) -> ListingPhotoResponse:
    """Confirm a completed photo upload by saving object_key + position to DB."""
    listing = await _get_listing_or_404(listing_id, db, require_owner=current_user)

    if len(listing.photos) >= MAX_PHOTOS:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {MAX_PHOTOS} photos per listing allowed",
        )

    photo = ListingPhoto(
        listing_id=listing_id,
        object_key=data.object_key,
        position=data.position,
    )
    db.add(photo)
    await db.commit()
    await db.refresh(photo)
    return _photo_to_response(photo, minio_public)


@router.delete(
    "/{listing_id}/photos/{photo_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_photo(
    listing_id: uuid.UUID,
    photo_id: uuid.UUID,
    current_user: User = Depends(require_registered_user),
    db: AsyncSession = Depends(get_db),
    minio: Minio = Depends(get_minio),
) -> None:
    """Delete a single photo from DB and MinIO. Owner only."""
    await _get_listing_or_404(listing_id, db, require_owner=current_user)

    result = await db.execute(
        select(ListingPhoto).where(
            ListingPhoto.id == photo_id,
            ListingPhoto.listing_id == listing_id,
        )
    )
    photo = result.scalar_one_or_none()
    if photo is None:
        raise HTTPException(status_code=404, detail="Photo not found")

    try:
        delete_object(minio, BUCKET_LISTINGS, photo.object_key)
    except Exception:
        pass  # Best-effort deletion

    await db.delete(photo)
    await db.commit()

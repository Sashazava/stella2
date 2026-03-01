"""Factory helpers for creating test database objects."""
from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.models.listing import Listing, ListingStatus
from app.models.listing_photo import ListingPhoto
from app.models.user import User


async def create_user(
    db: AsyncSession,
    telegram_id: int = 12345,
    first_name: str = "Test",
    city: str = "Москва",
    is_registered: bool = True,
) -> User:
    user = User(
        telegram_id=telegram_id,
        first_name=first_name,
        last_name="User",
        username="testuser",
        city=city,
        phone="+79001234567",
        is_registered=is_registered,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def create_category(
    db: AsyncSession,
    name: str = "Электроника",
    is_approved: bool = True,
) -> Category:
    slug = name.lower().replace(" ", "-")
    category = Category(
        name=name,
        slug=slug,
        is_approved=is_approved,
    )
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category


async def create_listing(
    db: AsyncSession,
    seller: User,
    category: Category | None = None,
    status: ListingStatus = ListingStatus.approved,
    city: str = "Москва",
    title: str = "Test Listing",
    price: Decimal = Decimal("1000.00"),
) -> Listing:
    listing = Listing(
        title=title,
        description="Test description for listing",
        price=price,
        currency="RUB",
        status=status,
        city=city,
        seller_id=seller.id,
        category_id=category.id if category else None,
    )
    db.add(listing)
    await db.commit()
    await db.refresh(listing)
    return listing


async def create_photo(
    db: AsyncSession,
    listing: Listing,
    position: int = 0,
) -> ListingPhoto:
    photo = ListingPhoto(
        listing_id=listing.id,
        object_key=f"listings/{uuid.uuid4()}.jpg",
        position=position,
    )
    db.add(photo)
    await db.commit()
    await db.refresh(photo)
    return photo

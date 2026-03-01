"""Tests for /listings endpoints."""
from __future__ import annotations

import uuid

from tests.conftest import AUTH_HEADER
from tests.factories import create_category, create_listing, create_photo, create_user
from app.models.listing import ListingStatus


class TestCreateListing:
    """POST /listings"""

    async def test_create_listing_returns_pending_status(self, client, mock_auth, db_session):
        """
        Creating a listing via the API always sets status=pending.
        category_id is a required field in ListingCreate schema.
        """
        await create_user(db_session, telegram_id=12345, is_registered=True)
        category = await create_category(db_session)
        resp = await client.post(
            "/listings",
            headers=AUTH_HEADER,
            json={
                "title": "Продам велосипед",
                "description": "Отличный велосипед",
                "price": "5000",
                "currency": "RUB",
                "category_id": str(category.id),
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Продам велосипед"
        assert data["status"] == "pending"

    async def test_create_listing_without_auth_returns_4xx(self, client):
        resp = await client.post(
            "/listings",
            json={"title": "Test", "description": "Test", "price": 100, "category_id": str(uuid.uuid4())},
        )
        assert resp.status_code in (401, 422)

    async def test_create_listing_unregistered_returns_403(self, client, mock_auth, db_session):
        """Unregistered users cannot create listings (require_registered_user)."""
        await create_user(db_session, telegram_id=12345, is_registered=False)
        category = await create_category(db_session)
        resp = await client.post(
            "/listings",
            headers=AUTH_HEADER,
            json={
                "title": "Test",
                "description": "Test",
                "price": "100",
                "category_id": str(category.id),
            },
        )
        assert resp.status_code == 403


class TestGetListing:
    """GET /listings/{id}"""

    async def test_get_approved_listing(self, client, mock_auth, db_session):
        """Approved listing is visible to anyone (optional auth)."""
        user = await create_user(db_session, telegram_id=12345)
        category = await create_category(db_session)
        listing = await create_listing(
            db_session, seller=user, category=category, status=ListingStatus.approved
        )
        resp = await client.get(f"/listings/{listing.id}", headers=AUTH_HEADER)
        assert resp.status_code == 200
        assert resp.json()["id"] == str(listing.id)

    async def test_pending_listing_hidden_from_non_owner(self, client, mock_auth, db_session):
        """Non-owner receives 404 for a pending listing."""
        owner = await create_user(db_session, telegram_id=77777)
        # mock_auth patches telegram_id=12345; owner is 77777 → different user
        listing = await create_listing(db_session, seller=owner, status=ListingStatus.pending)
        resp = await client.get(f"/listings/{listing.id}", headers=AUTH_HEADER)
        assert resp.status_code == 404

    async def test_owner_can_see_own_pending_listing(self, client, mock_auth, db_session):
        """The owner (telegram_id=12345) can see their own pending listing."""
        owner = await create_user(db_session, telegram_id=12345)
        category = await create_category(db_session)
        listing = await create_listing(
            db_session, seller=owner, category=category, status=ListingStatus.pending
        )
        resp = await client.get(f"/listings/{listing.id}", headers=AUTH_HEADER)
        assert resp.status_code == 200

    async def test_get_nonexistent_listing_returns_404(self, client):
        resp = await client.get(f"/listings/{uuid.uuid4()}")
        assert resp.status_code == 404


class TestUpdateListing:
    """PATCH /listings/{id}"""

    async def test_owner_can_update_listing(self, client, mock_auth, db_session):
        owner = await create_user(db_session, telegram_id=12345, is_registered=True)
        category = await create_category(db_session)
        listing = await create_listing(db_session, seller=owner, category=category)
        resp = await client.patch(
            f"/listings/{listing.id}",
            headers=AUTH_HEADER,
            json={"title": "Обновлённое название"},
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "Обновлённое название"

    async def test_non_owner_cannot_update_listing(self, client, mock_auth, db_session):
        """mock_auth is telegram_id=12345; listing belongs to telegram_id=88888."""
        other_user = await create_user(db_session, telegram_id=88888)
        listing = await create_listing(db_session, seller=other_user)
        # Auto-create the mock_auth user so get_or_create_user succeeds
        await create_user(db_session, telegram_id=12345, is_registered=True)
        resp = await client.patch(
            f"/listings/{listing.id}",
            headers=AUTH_HEADER,
            json={"title": "Попытка изменить"},
        )
        assert resp.status_code == 403

    async def test_content_change_resets_status_to_pending(self, client, mock_auth, db_session):
        """Changing title/description/price of an approved listing resets status to pending."""
        owner = await create_user(db_session, telegram_id=12345, is_registered=True)
        category = await create_category(db_session)
        listing = await create_listing(
            db_session, seller=owner, category=category, status=ListingStatus.approved
        )
        resp = await client.patch(
            f"/listings/{listing.id}",
            headers=AUTH_HEADER,
            json={"title": "Изменённый заголовок"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "pending"


class TestDeleteListing:
    """DELETE /listings/{id}"""

    async def test_owner_can_delete_listing(self, client, mock_auth, db_session):
        owner = await create_user(db_session, telegram_id=12345, is_registered=True)
        listing = await create_listing(db_session, seller=owner)
        resp = await client.delete(f"/listings/{listing.id}", headers=AUTH_HEADER)
        assert resp.status_code == 204

    async def test_non_owner_cannot_delete_listing(self, client, mock_auth, db_session):
        other = await create_user(db_session, telegram_id=66666)
        listing = await create_listing(db_session, seller=other)
        await create_user(db_session, telegram_id=12345, is_registered=True)
        resp = await client.delete(f"/listings/{listing.id}", headers=AUTH_HEADER)
        assert resp.status_code == 403


class TestPhotoUpload:
    """POST /listings/{id}/photos/upload-url"""

    async def test_get_upload_url_returns_presigned_url(self, client, mock_auth, db_session):
        """Returns PhotoUploadResponse with upload_url and object_key."""
        owner = await create_user(db_session, telegram_id=12345, is_registered=True)
        listing = await create_listing(db_session, seller=owner)
        resp = await client.post(
            f"/listings/{listing.id}/photos/upload-url",
            headers=AUTH_HEADER,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "upload_url" in data
        assert "object_key" in data
        assert "position" in data

    async def test_max_5_photos_enforced(self, client, mock_auth, db_session):
        """Attempting to get a 6th upload URL returns 400."""
        owner = await create_user(db_session, telegram_id=12345, is_registered=True)
        listing = await create_listing(db_session, seller=owner)
        # Add MAX_PHOTOS (5) photos directly via factory
        for i in range(5):
            await create_photo(db_session, listing=listing, position=i)

        resp = await client.post(
            f"/listings/{listing.id}/photos/upload-url",
            headers=AUTH_HEADER,
        )
        assert resp.status_code == 400
        assert "5" in resp.json()["detail"]

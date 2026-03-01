"""Tests for /api/listings endpoints."""
from __future__ import annotations

import uuid

import pytest

from tests.conftest import AUTH_HEADER
from tests.factories import create_category, create_listing, create_photo, create_user
from app.models.listing import ListingStatus


class TestCreateListing:
    """POST /api/listings"""

    async def test_create_listing_returns_pending_status(self, client, mock_auth, db_session):
        await create_user(db_session, telegram_id=12345, is_registered=True)
        resp = await client.post(
            "/api/listings",
            headers=AUTH_HEADER,
            json={
                "title": "Продам велосипед",
                "description": "Отличный велосипед, почти новый",
                "price": 5000,
                "currency": "RUB",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Продам велосипед"
        assert data["status"] == "pending"

    async def test_create_listing_without_auth_returns_401(self, client):
        resp = await client.post(
            "/api/listings",
            json={"title": "Test", "description": "Test", "price": 100},
        )
        assert resp.status_code == 401

    async def test_create_listing_unregistered_returns_403(self, client, mock_auth, db_session):
        await create_user(db_session, telegram_id=12345, is_registered=False)
        resp = await client.post(
            "/api/listings",
            headers=AUTH_HEADER,
            json={"title": "Test", "description": "Test", "price": 100},
        )
        assert resp.status_code == 403


class TestGetListing:
    """GET /api/listings/{id}"""

    async def test_get_approved_listing(self, client, mock_auth, db_session):
        user = await create_user(db_session, telegram_id=12345)
        listing = await create_listing(db_session, seller=user, status=ListingStatus.approved)
        resp = await client.get(f"/api/listings/{listing.id}", headers=AUTH_HEADER)
        assert resp.status_code == 200
        assert resp.json()["id"] == str(listing.id)

    async def test_pending_listing_hidden_from_non_owner(self, client, mock_auth, db_session):
        """Non-owner cannot see pending listing."""
        owner = await create_user(db_session, telegram_id=77777)
        listing = await create_listing(db_session, seller=owner, status=ListingStatus.pending)
        # mock_auth is telegram_id=12345, not the owner
        resp = await client.get(f"/api/listings/{listing.id}", headers=AUTH_HEADER)
        assert resp.status_code == 404

    async def test_owner_can_see_own_pending_listing(self, client, mock_auth, db_session):
        """Owner can see their own pending listing."""
        owner = await create_user(db_session, telegram_id=12345)
        listing = await create_listing(db_session, seller=owner, status=ListingStatus.pending)
        resp = await client.get(f"/api/listings/{listing.id}", headers=AUTH_HEADER)
        assert resp.status_code == 200

    async def test_get_nonexistent_listing_returns_404(self, client):
        resp = await client.get(f"/api/listings/{uuid.uuid4()}")
        assert resp.status_code == 404


class TestUpdateListing:
    """PATCH /api/listings/{id}"""

    async def test_owner_can_update_listing(self, client, mock_auth, db_session):
        owner = await create_user(db_session, telegram_id=12345, is_registered=True)
        listing = await create_listing(db_session, seller=owner)
        resp = await client.patch(
            f"/api/listings/{listing.id}",
            headers=AUTH_HEADER,
            json={"title": "Обновлённое название"},
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "Обновлённое название"

    async def test_non_owner_cannot_update_listing(self, client, mock_auth, db_session):
        other_user = await create_user(db_session, telegram_id=88888)
        listing = await create_listing(db_session, seller=other_user)
        # mock_auth is telegram_id=12345
        await create_user(db_session, telegram_id=12345, is_registered=True)
        resp = await client.patch(
            f"/api/listings/{listing.id}",
            headers=AUTH_HEADER,
            json={"title": "Попытка изменить"},
        )
        assert resp.status_code == 403

    async def test_content_change_resets_status_to_pending(self, client, mock_auth, db_session):
        owner = await create_user(db_session, telegram_id=12345, is_registered=True)
        listing = await create_listing(db_session, seller=owner, status=ListingStatus.approved)
        resp = await client.patch(
            f"/api/listings/{listing.id}",
            headers=AUTH_HEADER,
            json={"title": "Изменённый заголовок"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "pending"


class TestDeleteListing:
    """DELETE /api/listings/{id}"""

    async def test_owner_can_delete_listing(self, client, mock_auth, db_session):
        owner = await create_user(db_session, telegram_id=12345, is_registered=True)
        listing = await create_listing(db_session, seller=owner)
        resp = await client.delete(f"/api/listings/{listing.id}", headers=AUTH_HEADER)
        assert resp.status_code == 204

    async def test_non_owner_cannot_delete_listing(self, client, mock_auth, db_session):
        other = await create_user(db_session, telegram_id=66666)
        listing = await create_listing(db_session, seller=other)
        await create_user(db_session, telegram_id=12345, is_registered=True)
        resp = await client.delete(f"/api/listings/{listing.id}", headers=AUTH_HEADER)
        assert resp.status_code == 403


class TestPhotoUpload:
    """POST /api/listings/{id}/photos/upload-url"""

    async def test_get_upload_url_returns_presigned_url(self, client, mock_auth, db_session):
        owner = await create_user(db_session, telegram_id=12345, is_registered=True)
        listing = await create_listing(db_session, seller=owner)
        resp = await client.post(
            f"/api/listings/{listing.id}/photos/upload-url",
            headers=AUTH_HEADER,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "upload_url" in data
        assert "object_key" in data

    async def test_max_5_photos_enforced(self, client, mock_auth, db_session):
        """6th photo upload attempt returns 400."""
        owner = await create_user(db_session, telegram_id=12345, is_registered=True)
        listing = await create_listing(db_session, seller=owner)
        # Add 5 photos directly
        for i in range(5):
            await create_photo(db_session, listing=listing, position=i)

        resp = await client.post(
            f"/api/listings/{listing.id}/photos/upload-url",
            headers=AUTH_HEADER,
        )
        assert resp.status_code == 400
        assert "5" in resp.json()["detail"]

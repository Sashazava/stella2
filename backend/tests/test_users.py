"""Tests for /api/users endpoints."""
from __future__ import annotations

import pytest

from tests.conftest import AUTH_HEADER
from tests.factories import create_user


class TestUserProfile:
    """GET /api/users/profile"""

    async def test_get_profile_returns_current_user(self, client, mock_auth, db_session):
        await create_user(db_session, telegram_id=12345)
        resp = await client.get("/api/users/profile", headers=AUTH_HEADER)
        assert resp.status_code == 200
        data = resp.json()
        assert data["telegram_id"] == 12345
        assert data["first_name"] == "Test"

    async def test_get_profile_without_auth_returns_401(self, client):
        resp = await client.get("/api/users/profile")
        assert resp.status_code == 401


class TestUserRegistration:
    """POST /api/users/register"""

    async def test_register_user_sets_profile(self, client, mock_auth, db_session):
        """Registration updates user fields and sets is_registered=True."""
        # User auto-created by auth
        resp = await client.post(
            "/api/users/register",
            headers=AUTH_HEADER,
            json={
                "first_name": "Иван",
                "last_name": "Иванов",
                "phone": "+79001234567",
                "city": "Москва",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["first_name"] == "Иван"
        assert data["city"] == "Москва"
        assert data["is_registered"] is True

    async def test_register_without_auth_returns_401(self, client):
        resp = await client.post(
            "/api/users/register",
            json={"first_name": "Test", "phone": "+79001234567", "city": "Москва"},
        )
        assert resp.status_code == 401


class TestUpdateProfile:
    """PATCH /api/users/profile"""

    async def test_update_profile_changes_city(self, client, mock_auth, db_session):
        user = await create_user(db_session, telegram_id=12345, is_registered=True)
        resp = await client.patch(
            "/api/users/profile",
            headers=AUTH_HEADER,
            json={"city": "Санкт-Петербург"},
        )
        assert resp.status_code == 200
        assert resp.json()["city"] == "Санкт-Петербург"

    async def test_update_profile_unregistered_returns_403(self, client, mock_auth, db_session):
        """Unregistered users cannot update profile."""
        await create_user(db_session, telegram_id=12345, is_registered=False)
        resp = await client.patch(
            "/api/users/profile",
            headers=AUTH_HEADER,
            json={"city": "Казань"},
        )
        assert resp.status_code == 403


class TestPublicProfile:
    """GET /api/users/{telegram_id}/public"""

    async def test_get_public_profile_returns_user(self, client, db_session):
        user = await create_user(db_session, telegram_id=55555)
        resp = await client.get(f"/api/users/{user.telegram_id}/public")
        assert resp.status_code == 200
        data = resp.json()
        assert data["telegram_id"] == 55555
        # Phone should NOT be in public profile
        assert "phone" not in data

    async def test_get_public_profile_unknown_user_returns_404(self, client):
        resp = await client.get("/api/users/999999999/public")
        assert resp.status_code == 404

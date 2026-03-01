"""Tests for authentication middleware."""
from __future__ import annotations

import time
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from tests.conftest import AUTH_HEADER
from tests.factories import create_user


class TestAuthValidation:
    """Test Authorization header parsing and validation."""

    async def test_missing_auth_header_returns_401(self, client):
        """Requests without Authorization header are rejected."""
        resp = await client.get("/api/users/profile")
        assert resp.status_code == 401

    async def test_wrong_scheme_returns_401(self, client):
        """Bearer scheme instead of tma is rejected."""
        resp = await client.get(
            "/api/users/profile",
            headers={"Authorization": "Bearer some_token"},
        )
        assert resp.status_code == 401

    async def test_valid_auth_returns_user(self, client, mock_auth, db_session):
        """Valid tma initData returns the user profile."""
        await create_user(db_session, telegram_id=12345)
        resp = await client.get("/api/users/profile", headers=AUTH_HEADER)
        assert resp.status_code == 200
        data = resp.json()
        assert data["telegram_id"] == 12345

    async def test_expired_auth_returns_401(self, client):
        """initData older than 1 hour is rejected."""
        mock_data = MagicMock()
        # auth_date is 2 hours ago
        mock_data.auth_date = datetime.fromtimestamp(
            time.time() - 7201, tz=timezone.utc
        )
        mock_data.user = MagicMock()
        mock_data.user.id = 12345
        mock_data.user.first_name = "Test"
        mock_data.user.last_name = None
        mock_data.user.username = "testuser"

        with patch("app.auth.safe_parse_webapp_init_data", return_value=mock_data):
            resp = await client.get("/api/users/profile", headers=AUTH_HEADER)
        assert resp.status_code == 401

    async def test_tampered_init_data_returns_401(self, client):
        """ValueError from safe_parse_webapp_init_data returns 401."""
        with patch(
            "app.auth.safe_parse_webapp_init_data",
            side_effect=ValueError("invalid signature"),
        ):
            resp = await client.get("/api/users/profile", headers=AUTH_HEADER)
        assert resp.status_code == 401

    async def test_auto_creates_user_on_first_auth(self, client, mock_auth, db_session):
        """First-time auth auto-creates a User record in the DB."""
        from sqlalchemy import select
        from app.models.user import User

        # Use a unique telegram_id not in DB yet
        mock_auth.user.id = 99001
        mock_auth.user.first_name = "NewUser"

        resp = await client.get("/api/users/profile", headers=AUTH_HEADER)
        assert resp.status_code == 200

        result = await db_session.execute(
            select(User).where(User.telegram_id == 99001)
        )
        user = result.scalar_one_or_none()
        assert user is not None
        assert user.first_name == "NewUser"

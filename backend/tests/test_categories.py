"""Tests for /api/categories endpoints."""
from __future__ import annotations

import pytest

from tests.conftest import AUTH_HEADER
from tests.factories import create_category, create_user


class TestListCategories:
    """GET /api/categories"""

    async def test_returns_only_approved_categories(self, client, db_session):
        await create_category(db_session, name="Одобренная", is_approved=True)
        await create_category(db_session, name="Неодобренная", is_approved=False)

        resp = await client.get("/api/categories")
        assert resp.status_code == 200
        names = [c["name"] for c in resp.json()]
        assert "Одобренная" in names
        assert "Неодобренная" not in names

    async def test_returns_empty_list_when_no_categories(self, client):
        resp = await client.get("/api/categories")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestProposeCategory:
    """POST /api/categories/propose"""

    async def test_propose_creates_unapproved_category(self, client, mock_auth, db_session):
        await create_user(db_session, telegram_id=12345, is_registered=True)
        resp = await client.post(
            "/api/categories/propose",
            headers=AUTH_HEADER,
            json={"name": "Новая категория"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Новая категория"
        assert data["is_approved"] is False

    async def test_propose_without_auth_returns_401(self, client):
        resp = await client.post(
            "/api/categories/propose",
            json={"name": "Тест"},
        )
        assert resp.status_code == 401

    async def test_propose_unregistered_returns_403(self, client, mock_auth, db_session):
        await create_user(db_session, telegram_id=12345, is_registered=False)
        resp = await client.post(
            "/api/categories/propose",
            headers=AUTH_HEADER,
            json={"name": "Тест"},
        )
        assert resp.status_code == 403


class TestApproveCategory:
    """PATCH /api/categories/{id}/approve"""

    async def test_approve_requires_admin(self, client, mock_auth, db_session):
        """Non-admin user gets 403."""
        await create_user(db_session, telegram_id=12345, is_registered=True)
        category = await create_category(db_session, name="Ожидает", is_approved=False)
        resp = await client.patch(
            f"/api/categories/{category.id}/approve",
            headers=AUTH_HEADER,
        )
        assert resp.status_code == 403

    async def test_approve_works_for_admin(self, admin_client, mock_auth_admin, db_session):
        """Admin can approve a pending category."""
        from app.config import settings
        admin_id = settings.admin_telegram_ids[0]
        await create_user(db_session, telegram_id=admin_id, is_registered=True)
        category = await create_category(db_session, name="ПендингКат", is_approved=False)

        resp = await admin_client.patch(
            f"/api/categories/{category.id}/approve",
            headers={"Authorization": "tma mock_admin_data"},
        )
        assert resp.status_code == 200
        assert resp.json()["is_approved"] is True

    async def test_approve_nonexistent_returns_404(self, admin_client, mock_auth_admin, db_session):
        from app.config import settings
        admin_id = settings.admin_telegram_ids[0]
        await create_user(db_session, telegram_id=admin_id, is_registered=True)

        import uuid
        resp = await admin_client.patch(
            f"/api/categories/{uuid.uuid4()}/approve",
            headers={"Authorization": "tma mock_admin_data"},
        )
        assert resp.status_code == 404

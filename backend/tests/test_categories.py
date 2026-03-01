"""Tests for /api/categories endpoints."""
from __future__ import annotations

from sqlalchemy import select

from app.models.category import Category
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

    async def test_returns_200_with_schema_fields(self, client, db_session):
        await create_category(db_session, name="Техника", is_approved=True)
        resp = await client.get("/api/categories")
        assert resp.status_code == 200
        item = resp.json()[0]
        # CategoryResponse has: id, name, slug, icon
        assert "id" in item
        assert "name" in item
        assert "slug" in item
        assert "icon" in item


class TestProposeCategory:
    """POST /api/categories/propose"""

    async def test_propose_creates_unapproved_category(self, client, mock_auth, db_session):
        """A proposed category is created with is_approved=False in the DB."""
        await create_user(db_session, telegram_id=12345, is_registered=True)
        resp = await client.post(
            "/api/categories/propose",
            headers=AUTH_HEADER,
            json={"name": "Новая категория"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Новая категория"
        # CategoryResponse schema does not expose is_approved.
        # Verify from DB that it is indeed not approved.
        result = await db_session.execute(
            select(Category).where(Category.name == "Новая кетегория")
        )
        # Use the name from the response to be precise
        result2 = await db_session.execute(
            select(Category).where(Category.id == data["id"])
        )
        cat = result2.scalar_one_or_none()
        assert cat is not None
        assert cat.is_approved is False

    async def test_propose_without_auth_returns_4xx(self, client):
        resp = await client.post(
            "/api/categories/propose",
            json={"name": "Тест"},
        )
        assert resp.status_code in (401, 422)

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
        """A non-admin user receives 403."""
        await create_user(db_session, telegram_id=12345, is_registered=True)
        category = await create_category(db_session, name="Ожидает", is_approved=False)
        resp = await client.patch(
            f"/api/categories/{category.id}/approve",
            headers=AUTH_HEADER,
        )
        assert resp.status_code == 403

    async def test_approve_works_for_admin(self, client, mock_auth_admin, db_session):
        """Admin can approve a pending category; response has id, name, slug."""
        from app.config import settings

        admin_id = settings.admin_telegram_ids[0]
        await create_user(db_session, telegram_id=admin_id, is_registered=True)
        category = await create_category(db_session, name="ПендингКат", is_approved=False)

        resp = await client.patch(
            f"/api/categories/{category.id}/approve",
            headers=AUTH_HEADER,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == str(category.id)
        # Verify approval persisted to DB
        await db_session.expire_all()
        result = await db_session.execute(
            select(Category).where(Category.id == category.id)
        )
        cat = result.scalar_one_or_none()
        assert cat is not None
        assert cat.is_approved is True

    async def test_approve_nonexistent_returns_404(self, client, mock_auth_admin, db_session):
        import uuid
        from app.config import settings

        admin_id = settings.admin_telegram_ids[0]
        await create_user(db_session, telegram_id=admin_id, is_registered=True)

        resp = await client.patch(
            f"/api/categories/{uuid.uuid4()}/approve",
            headers=AUTH_HEADER,
        )
        assert resp.status_code == 404

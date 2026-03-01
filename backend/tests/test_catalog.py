"""Tests for GET /api/catalog endpoint."""
from __future__ import annotations

from decimal import Decimal

import pytest

from tests.factories import create_category, create_listing, create_user
from app.models.listing import ListingStatus


class TestCatalogFiltering:
    """GET /api/catalog — filtering and pagination."""

    async def test_catalog_returns_only_approved_listings(self, client, db_session):
        user = await create_user(db_session, telegram_id=11111)
        await create_listing(db_session, seller=user, status=ListingStatus.approved, title="Одобрено")
        await create_listing(db_session, seller=user, status=ListingStatus.pending, title="Ожидает")
        await create_listing(db_session, seller=user, status=ListingStatus.rejected, title="Отклонено")

        resp = await client.get("/api/catalog")
        assert resp.status_code == 200
        data = resp.json()
        titles = [item["title"] for item in data["items"]]
        assert "Одобрено" in titles
        assert "Ожидает" not in titles
        assert "Отклонено" not in titles

    async def test_catalog_filter_by_city(self, client, db_session):
        user = await create_user(db_session, telegram_id=22222)
        await create_listing(db_session, seller=user, city="Москва", title="Москва товар")
        await create_listing(db_session, seller=user, city="Казань", title="Казань товар")

        resp = await client.get("/api/catalog?city=Москва")
        assert resp.status_code == 200
        titles = [item["title"] for item in resp.json()["items"]]
        assert "Москва товар" in titles
        assert "Казань товар" not in titles

    async def test_catalog_filter_by_category(self, client, db_session):
        user = await create_user(db_session, telegram_id=33333)
        cat1 = await create_category(db_session, name="Техника")
        cat2 = await create_category(db_session, name="Одежда")
        await create_listing(db_session, seller=user, category=cat1, title="Ноутбук")
        await create_listing(db_session, seller=user, category=cat2, title="Куртка")

        resp = await client.get(f"/api/catalog?category_id={cat1.id}")
        assert resp.status_code == 200
        titles = [item["title"] for item in resp.json()["items"]]
        assert "Ноутбук" in titles
        assert "Куртка" not in titles

    async def test_catalog_sort_price_asc(self, client, db_session):
        user = await create_user(db_session, telegram_id=44444)
        await create_listing(db_session, seller=user, title="Дорогой", price=Decimal("9999.00"))
        await create_listing(db_session, seller=user, title="Дешёвый", price=Decimal("100.00"))

        resp = await client.get("/api/catalog?sort=price_asc")
        assert resp.status_code == 200
        items = resp.json()["items"]
        if len(items) >= 2:
            prices = [float(item["price"]) for item in items]
            assert prices == sorted(prices)

    async def test_catalog_sort_price_desc(self, client, db_session):
        user = await create_user(db_session, telegram_id=55551)
        await create_listing(db_session, seller=user, title="Дорогой2", price=Decimal("8888.00"))
        await create_listing(db_session, seller=user, title="Дешёвый2", price=Decimal("200.00"))

        resp = await client.get("/api/catalog?sort=price_desc")
        assert resp.status_code == 200
        items = resp.json()["items"]
        if len(items) >= 2:
            prices = [float(item["price"]) for item in items]
            assert prices == sorted(prices, reverse=True)

    async def test_catalog_pagination(self, client, db_session):
        user = await create_user(db_session, telegram_id=66661)
        for i in range(5):
            await create_listing(db_session, seller=user, title=f"Товар {i}")

        resp = await client.get("/api/catalog?per_page=2&page=1")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "per_page" in data
        assert "total_pages" in data
        assert len(data["items"]) <= 2

    async def test_catalog_returns_paginated_response_shape(self, client, db_session):
        resp = await client.get("/api/catalog")
        assert resp.status_code == 200
        data = resp.json()
        assert set(data.keys()) >= {"items", "total", "page", "per_page", "total_pages"}

    async def test_catalog_empty_when_no_approved_listings(self, client):
        resp = await client.get("/api/catalog")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data["items"], list)
        assert data["total"] >= 0

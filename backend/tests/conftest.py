"""
Test infrastructure for Stella backend.

Uses SQLite in-memory DB (no Docker required).
All external services (Redis, MinIO, bot) are mocked.
"""
from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# ---------------------------------------------------------------------------
# Patch the lifespan BEFORE importing app so bot/redis/minio are never called
# ---------------------------------------------------------------------------

@asynccontextmanager
async def _mock_lifespan(app):
    """No-op lifespan: skip bot webhook, DB engine, Redis, MinIO setup."""
    app.state.redis = AsyncMock()
    app.state.minio = MagicMock()
    app.state.minio_public = MagicMock()
    yield


# Patch lifespan at import time so FastAPI never tries to connect to Telegram
with patch("app.main.lifespan", _mock_lifespan):
    from app.main import app  # noqa: E402

from app.deps import get_db, get_minio, get_minio_public, get_redis  # noqa: E402
from app.models.base import Base  # noqa: E402

# ---------------------------------------------------------------------------
# Database fixtures
# ---------------------------------------------------------------------------

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="session")
async def engine():
    _engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield _engine
    await _engine.dispose()


@pytest_asyncio.fixture
async def db_session(engine):
    _session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with _session_factory() as session:
        yield session
        await session.rollback()


# ---------------------------------------------------------------------------
# Mock fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_redis():
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock(return_value=True)
    redis.setex = AsyncMock(return_value=True)
    redis.delete = AsyncMock(return_value=1)
    return redis


@pytest.fixture
def mock_minio():
    minio = MagicMock()
    minio.presigned_put_object = MagicMock(return_value="http://minio/upload-url")
    minio.presigned_get_object = MagicMock(return_value="http://minio/download-url")
    return minio


# ---------------------------------------------------------------------------
# Auth mock helpers
# ---------------------------------------------------------------------------


def _make_mock_init_data(telegram_id: int = 12345, first_name: str = "Test") -> MagicMock:
    mock_data = MagicMock()
    mock_data.auth_date = datetime.now(timezone.utc)
    mock_data.user = MagicMock()
    mock_data.user.id = telegram_id
    mock_data.user.first_name = first_name
    mock_data.user.last_name = None
    mock_data.user.username = "testuser"
    return mock_data


AUTH_HEADER = {"Authorization": "tma mock_init_data_string"}


@pytest.fixture
def mock_auth():
    """Patch safe_parse_webapp_init_data to return a valid user (telegram_id=12345)."""
    mock_data = _make_mock_init_data(telegram_id=12345)
    with patch("app.auth.safe_parse_webapp_init_data", return_value=mock_data):
        with patch("app.api.listings.safe_parse_webapp_init_data", return_value=mock_data):
            yield mock_data


@pytest.fixture
def mock_auth_admin():
    """Patch auth to return admin user (telegram_id in settings.admin_telegram_ids)."""
    from app.config import settings
    admin_id = 99999
    original_admins = settings.admin_telegram_ids
    settings.admin_telegram_ids = [admin_id]

    mock_data = _make_mock_init_data(telegram_id=admin_id)
    with patch("app.auth.safe_parse_webapp_init_data", return_value=mock_data):
        with patch("app.api.listings.safe_parse_webapp_init_data", return_value=mock_data):
            yield mock_data

    settings.admin_telegram_ids = original_admins


# ---------------------------------------------------------------------------
# HTTP client fixture
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def client(db_session, mock_redis, mock_minio):
    """AsyncClient with all external deps overridden."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = lambda: mock_redis
    app.dependency_overrides[get_minio] = lambda: mock_minio
    app.dependency_overrides[get_minio_public] = lambda: mock_minio

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def admin_client(db_session, mock_redis, mock_minio, mock_auth_admin):
    """AsyncClient authenticated as admin user."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = lambda: mock_redis
    app.dependency_overrides[get_minio] = lambda: mock_minio
    app.dependency_overrides[get_minio_public] = lambda: mock_minio

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()

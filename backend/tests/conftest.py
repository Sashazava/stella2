"""
Test infrastructure for Stella Marketplace backend.

External services (PostgreSQL, Redis, MinIO, Telegram bot) are all mocked.
Uses SQLite in-memory via aiosqlite — no Docker required.
"""
from __future__ import annotations

# ──────────────────────────────────────────────────────────────────────────────
# Set fake bot token BEFORE any app import.
# aiogram 3.x validates token format at Bot() construction time.
# An empty token would raise TokenValidationError.
# ──────────────────────────────────────────────────────────────────────────────
import os

os.environ.setdefault("BOT_TOKEN", "123456789:ABCdefGHIjklMNOpqrsTUVwxyz")

# ──────────────────────────────────────────────────────────────────────────────
# Standard library + third-party imports
# ──────────────────────────────────────────────────────────────────────────────
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.pool import StaticPool
from sqlalchemy.schema import ColumnDefault
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

# ──────────────────────────────────────────────────────────────────────────────
# App imports (after env is set so Settings() reads the fake token)
# ──────────────────────────────────────────────────────────────────────────────

# Import every model so Base.metadata is fully populated before patching.
import app.models.user  # noqa: F401
import app.models.category  # noqa: F401
import app.models.listing  # noqa: F401
import app.models.listing_photo  # noqa: F401

from app.config import settings
from app.deps import get_db, get_minio, get_minio_public, get_redis
from app.main import app
from app.models.base import Base

# ──────────────────────────────────────────────────────────────────────────────
# SQLite compatibility: replace PostgreSQL-specific func.now() defaults.
# `server_default=func.now()` compiles to `now()` which SQLite does not support.
# `onupdate=func.now()` compiles to `SET col = now()` on UPDATE — same issue.
# We patch metadata at import time so every test shares the fixed schema.
# ──────────────────────────────────────────────────────────────────────────────


def _py_now() -> datetime:
    """Python callable used as the replacement for onupdate=func.now()."""
    return datetime.now(timezone.utc)


for _tbl in Base.metadata.tables.values():
    for _col in _tbl.columns:
        if _col.server_default is not None:
            # Replace SQL expression with SQLite-native CURRENT_TIMESTAMP
            _col.server_default = text("CURRENT_TIMESTAMP")
        if _col.onupdate is not None:
            # Replace SQL expression update hook with Python callable
            _col.onupdate = ColumnDefault(_py_now, for_update=True)


# ──────────────────────────────────────────────────────────────────────────────
# Database fixtures
# ──────────────────────────────────────────────────────────────────────────────

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def engine():
    """
    Fresh in-memory SQLite DB for every test (complete isolation).

    StaticPool ensures all async checkouts use the SAME underlying sqlite3
    connection, so the single in-memory database is visible to every session.
    check_same_thread=False lets aiosqlite's background thread use it.
    """
    _engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield _engine
    await _engine.dispose()


@pytest_asyncio.fixture
async def db_session(engine):
    """AsyncSession for the test.  Rolled back automatically after each test."""
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session


# ──────────────────────────────────────────────────────────────────────────────
# External service mocks
# ──────────────────────────────────────────────────────────────────────────────


@pytest.fixture
def mock_redis():
    """AsyncMock that always reports a cache miss (get returns None)."""
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock(return_value=True)
    redis.setex = AsyncMock(return_value=True)
    redis.delete = AsyncMock(return_value=1)
    return redis


@pytest.fixture
def mock_minio():
    """MagicMock MinIO client that returns fake presigned URLs."""
    minio = MagicMock()
    minio.presigned_put_object = MagicMock(
        return_value="http://minio-test/bucket/object?X-Amz-Signature=upload"
    )
    minio.presigned_get_object = MagicMock(
        return_value="http://minio-test/bucket/object?X-Amz-Signature=download"
    )
    return minio


# ──────────────────────────────────────────────────────────────────────────────
# HTTP test client
# ──────────────────────────────────────────────────────────────────────────────


@pytest_asyncio.fixture
async def client(db_session, mock_redis, mock_minio):
    """
    AsyncClient wired to the FastAPI app.

    * Overrides get_db / get_redis / get_minio / get_minio_public.
    * Patches every external call made by the lifespan so no real services
      (Telegram bot, Redis, MinIO, PostgreSQL) are contacted.
    """

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = lambda: mock_redis
    app.dependency_overrides[get_minio] = lambda: mock_minio
    app.dependency_overrides[get_minio_public] = lambda: mock_minio

    # Lifespan calls engine.dispose() on shutdown; make that awaitable.
    mock_pg_engine = MagicMock()
    mock_pg_engine.dispose = AsyncMock()

    with (
        patch("app.main.bot") as mock_bot,
        patch("app.main.init_redis", new=AsyncMock(return_value=AsyncMock())),
        patch("app.main.close_redis", new=AsyncMock()),
        patch("app.main.init_minio", return_value=MagicMock()),
        patch("app.main.init_minio_public", return_value=MagicMock()),
        patch("app.main.ensure_buckets"),
        patch("app.main.create_async_engine", return_value=mock_pg_engine),
        patch("app.main.async_sessionmaker", return_value=MagicMock()),
    ):
        mock_bot.set_webhook = AsyncMock()
        mock_bot.set_chat_menu_button = AsyncMock()
        mock_bot.delete_webhook = AsyncMock()
        mock_bot.session = MagicMock()
        mock_bot.session.close = AsyncMock()

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            yield ac

    app.dependency_overrides.clear()


# ──────────────────────────────────────────────────────────────────────────────
# Auth helpers
# ──────────────────────────────────────────────────────────────────────────────

# Convenience constant used in every test that needs auth.
AUTH_HEADER = {"Authorization": "tma mock_init_data_string"}


def _make_mock_init_data(
    telegram_id: int = 12345,
    first_name: str = "Test",
    expired: bool = False,
) -> MagicMock:
    """Build the object returned by safe_parse_webapp_init_data."""
    from datetime import timedelta

    mock_data = MagicMock()
    if expired:
        mock_data.auth_date = datetime.now(timezone.utc) - timedelta(hours=2)
    else:
        mock_data.auth_date = datetime.now(timezone.utc)
    mock_data.user = MagicMock()
    mock_data.user.id = telegram_id
    mock_data.user.first_name = first_name
    mock_data.user.last_name = None
    mock_data.user.username = f"user{telegram_id}"
    return mock_data


@pytest.fixture
def mock_auth():
    """Patch safe_parse_webapp_init_data → valid user with telegram_id=12345."""
    mock_data = _make_mock_init_data(telegram_id=12345)
    with (
        patch("app.auth.safe_parse_webapp_init_data", return_value=mock_data),
        patch(
            "app.api.listings.safe_parse_webapp_init_data", return_value=mock_data
        ),
    ):
        yield mock_data


@pytest.fixture
def mock_auth_admin():
    """
    Patch auth → admin user (telegram_id=99999).
    Also sets settings.admin_telegram_ids = [99999] for the duration of the test.
    """
    admin_id = 99999
    original_admins = settings.admin_telegram_ids
    settings.admin_telegram_ids = [admin_id]

    mock_data = _make_mock_init_data(telegram_id=admin_id, first_name="Admin")
    with (
        patch("app.auth.safe_parse_webapp_init_data", return_value=mock_data),
        patch(
            "app.api.listings.safe_parse_webapp_init_data", return_value=mock_data
        ),
    ):
        yield mock_data

    settings.admin_telegram_ids = original_admins

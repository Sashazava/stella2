from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from aiogram.types import MenuButtonWebApp, WebAppInfo

from app.config import settings
from app.bot.bot import bot, dp
import app.bot.handlers  # noqa: F401 — registers handlers with dp
from app.services.redis import init_redis, close_redis
from app.services.storage import init_minio_public, ensure_buckets

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup
    try:
        await bot.set_webhook(
            url=f"{settings.app_base_url}/bot/webhook",
            secret_token=settings.webhook_secret,
            allowed_updates=dp.resolve_used_update_types(),
            drop_pending_updates=True,
        )
    except Exception as exc:
        print(f"WARNING: Webhook setup failed, will retry on next restart ({exc})")
    try:
        await bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(
                text="Открыть Stella",
                web_app=WebAppInfo(url=settings.app_base_url),
            )
        )
    except Exception as exc:
        print(f"WARNING: Menu button setup skipped ({exc})")
    app.state.redis = await init_redis(settings.redis_url)
    # Database — normalize URL to use psycopg async driver
    # Coolify may provide postgres://, postgresql://, or postgresql+asyncpg://
    db_url = settings.database_url
    if db_url.startswith("postgres://"):
        db_url = "postgresql+psycopg://" + db_url[len("postgres://"):]
    elif db_url.startswith("postgresql://"):
        db_url = "postgresql+psycopg://" + db_url[len("postgresql://"):]
    elif db_url.startswith("postgresql+asyncpg://"):
        db_url = "postgresql+psycopg://" + db_url[len("postgresql+asyncpg://"):]
    print(f"DB URL scheme: {db_url.split('@')[0].split('://')[0]}")
    engine = create_async_engine(db_url)
    app.state.sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
    dp["sessionmaker"] = app.state.sessionmaker  # inject into bot dispatcher for handlers
    # MinIO
    try:
        minio_client = init_minio_public(
            settings.minio_server_url,
            access_key=settings.minio_root_user,
            secret_key=settings.minio_root_password,
        )
        ensure_buckets(minio_client)
        app.state.minio = minio_client
        app.state.minio_public = minio_client
    except Exception as exc:
        print(f"WARNING: MinIO unavailable, file uploads disabled ({exc})")
        app.state.minio = None
        app.state.minio_public = None
    yield
    # Shutdown
    await bot.delete_webhook()
    await bot.session.close()
    await close_redis(app.state.redis)
    await engine.dispose()
    # MinIO clients are stateless; no explicit cleanup needed


app = FastAPI(
    title="Stella API",
    description="Stella Marketplace — Telegram Mini App",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.bot.webhook import router as bot_webhook_router  # noqa: E402
app.include_router(bot_webhook_router)

from app.api.router import router as api_router  # noqa: E402
app.include_router(api_router)  # includes /api/users, /api/categories, /api/listings, /api/catalog


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}

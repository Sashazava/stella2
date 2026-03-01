# Decisions — stella-marketplace

## [2026-02-26] Wave 1

- Auth: `Authorization: tma <initData.raw()>` header, validated via aiogram built-in
- Contact seller: `tg://user?id={telegram_id}` deep link
- Categories: hybrid (admin-defined + seller-proposed with moderation)
- Listings: max 5 photos, status: pending → approved/rejected
- Moderation: bot commands /approve, /reject (admin Telegram IDs in config)
- Granian: --workers 1 (aiogram in-process requires single event loop)
- MinIO: presigned URLs, MINIO_SERVER_URL env var for Docker networking
- Redis: redis.asyncio (not deprecated aioredis)
- ORM: SQLAlchemy 2 async + psycopg3

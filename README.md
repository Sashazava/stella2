# Stella — Telegram Mini App Marketplace

> Найдёшь всё, что нужно!

A full-stack Telegram Mini App marketplace (Avito-like) where sellers create moderated listings with photos, and buyers browse by city/category and contact sellers via Telegram.

## Tech Stack

**Backend**: Python 3.12, FastAPI, SQLAlchemy 2 async, aiogram 3.x, PostgreSQL (pgvector), Redis, MinIO, Granian

**Frontend**: Vue 3, TypeScript, Vite 6, TailwindCSS v4, Pinia, @telegram-apps/sdk-vue, Nginx

**Infra**: Docker Compose, Coolify deployment

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) + Docker Compose
- [uv](https://docs.astral.sh/uv/) (Python package manager)
- [pnpm](https://pnpm.io/) (Node package manager)
- [just](https://github.com/casey/just) (task runner)
- A Telegram Bot token from [@BotFather](https://t.me/BotFather)

## Quick Start

### 1. Clone and configure environment

```bash
git clone <repo-url>
cd site
cp .env.example .env
# Edit .env with your BOT_TOKEN and other settings
```

### 2. Start infrastructure services

```bash
just up          # Start PostgreSQL, Redis, MinIO
just db-migrate  # Run database migrations
```

### 3. Start backend (development)

```bash
just py-dev      # Start FastAPI with hot reload on :8000
```

### 4. Start frontend (development)

```bash
just node-install  # Install Node dependencies
just node-dev      # Start Vite dev server on :5173
```

## Project Structure

```
site/
├── backend/          # FastAPI backend
│   ├── app/
│   │   ├── api/      # REST endpoints (users, categories, listings, catalog)
│   │   ├── bot/      # aiogram bot (handlers, webhook, moderation)
│   │   ├── models/   # SQLAlchemy models
│   │   ├── schemas/  # Pydantic schemas
│   │   └── services/ # Redis, MinIO services
│   └── tests/        # pytest test suite
├── frontend/         # Vue 3 SPA
│   ├── src/
│   │   ├── features/ # Page components (catalog, listing, profile, etc.)
│   │   ├── stores/   # Pinia stores
│   │   └── api/      # Axios API client
│   └── tests/        # vitest test suite
├── infra/
│   ├── nginx/        # Nginx configuration
│   └── postgres/     # DB init scripts
├── docker-compose.yml       # Development services
├── docker-compose.prod.yml  # Production stack
└── justfile                 # Task runner recipes
```

## Available Just Recipes

```bash
just up           # Start dev infrastructure (postgres, redis, minio)
just down         # Stop dev infrastructure
just py-dev       # Run FastAPI dev server
just py-test      # Run backend tests
just py-lint      # Run ruff + mypy
just db-migrate   # Run alembic migrations
just node-dev     # Run Vite dev server
just node-build   # Build frontend for production
just node-test    # Run vitest
```

## Deployment (Coolify)

1. Push code to GitHub
2. In Coolify: create new service → Docker Compose → point to `docker-compose.prod.yml`
3. Set environment variables in Coolify dashboard
4. Deploy — Coolify handles HTTPS/TLS termination

## Bot Moderation Commands

Admins (configured via `ADMIN_TELEGRAM_IDS`) can use:
- `/pending` — list listings awaiting moderation
- `/approve <id>` — approve a listing
- `/reject <id>` — reject a listing
- `/stats` — show marketplace statistics

## Environment Variables

See `.env.example` for all required variables. Key ones:
- `BOT_TOKEN` — Telegram bot token from @BotFather
- `ADMIN_TELEGRAM_IDS` — comma-separated Telegram user IDs for admins
- `APP_BASE_URL` — public URL of the app (for webhook and Mini App)
- `WEBHOOK_SECRET` — secret token for bot webhook validation

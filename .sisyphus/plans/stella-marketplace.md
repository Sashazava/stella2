# Stella — Telegram Mini App Marketplace

## TL;DR

> **Quick Summary**: Build "Stella" — an Avito-like classifieds marketplace as a Telegram Mini App. Sellers create listings with photos, buyers browse by city/category and contact sellers via Telegram.
> 
> **Deliverables**:
> - Full-stack Telegram Mini App (Vue 3 frontend + FastAPI backend)
> - Telegram bot with webhook integration (aiogram 3.x)
> - User registration with profile management
> - Listing CRUD with photo uploads (MinIO S3)
> - Catalog with city-based filtering and category browsing
> - Listing moderation via bot commands
> - Splash screen with branded animation
> - Docker Compose dev + production setup
> - Dockerfiles for Coolify deployment (GitHub webhook auto-deploy)
> 
> **Estimated Effort**: Large
> **Parallel Execution**: YES — 6 waves
> **Critical Path**: Task 1→4→9→14→17→21→29→F1-F4

---

## Context

### Original Request
Build a Telegram Mini App marketplace called "Stella" (слоган: "Найдёшь всё, что нужно!") — an Avito-like platform for buying and selling goods. Users register with full profile, sellers create listings with photos, buyers browse catalog by city and category, contact sellers via Telegram deep link.

### Interview Summary
**Key Discussions**:
- **Registration**: Full profile for all users — name/surname from Telegram (editable), phone (share via TG or type), avatar (from TG, can upload custom), city (GPS suggestion + manual)
- **Seller contact**: "Write in Telegram" button — deep link to seller's TG chat
- **Geolocation**: GPS detection + manual city selection at registration
- **MVP scope**: Minimum — catalog + listings. NO: favorites, notifications, chat, search, admin panel
- **Categories**: Hybrid — admin-defined + seller can propose new ones
- **Listings**: Max 5 photos, moderation before publishing (pending → approved/rejected)
- **Tests**: After code (pytest + vitest), not TDD
- **Design**: Modern, minimalistic, volumetric/3D forms, intuitive navigation
- **Deployment**: Dockerfiles → GitHub → Coolify (webhook auto-deploy, already configured)

**Research Findings**:
- `@telegram-apps/sdk-vue` v2.x is the official SDK; `init()` must be called before `createApp()` and throws outside Telegram context — dev mock required
- aiogram has built-in `safe_parse_webapp_init_data()` for initData validation — no need for custom HMAC implementation
- Vue Router MUST use `createWebHistory()` — hash mode destroys Telegram launch parameters
- Granian ASGI server must run with `--workers 1` when aiogram bot runs in-process (single event loop)
- MinIO presigned URLs use `MINIO_SERVER_URL` env var for Docker networking (internal vs external URL gotcha)
- TailwindCSS v4 uses `@tailwindcss/vite` plugin — no `tailwind.config.js` needed, config via CSS `@theme {}`
- `redis.asyncio` (not deprecated aioredis) is the current async Redis client
- SQLAlchemy 2 async + psycopg3 is the best ORM choice for pgvector future-proofing

### Metis Review
**Identified Gaps** (addressed):
- **Moderation without Directus**: Resolved → bot commands (`/approve`, `/reject`) for admin users (Telegram IDs in config)
- **Seller without @username**: Resolved → `tg://user?id={telegram_id}` deep link + phone number fallback
- **SDK init() crash in dev**: Resolved → mock Telegram environment in dev mode with `mockTelegramEnv()`
- **Granian worker count**: Resolved → `--workers 1` (aiogram requires single event loop)
- **MinIO presigned URL networking**: Resolved → `MINIO_SERVER_URL` env var for public-facing URL
- **initData expiry**: Resolved → 1-hour max age on initData validation

---

## Work Objectives

### Core Objective
Build a production-ready Telegram Mini App marketplace where sellers create moderated listings and buyers discover goods by city and category.

### Concrete Deliverables
- `backend/` — FastAPI application with aiogram bot, PostgreSQL, Redis, MinIO integration
- `frontend/` — Vue 3 SPA served by Nginx, integrated with Telegram Mini App SDK
- `docker-compose.yml` — Development environment (PG, Redis, MinIO)
- `docker-compose.prod.yml` — Production stack
- `backend/Dockerfile` + `frontend/Dockerfile` — For Coolify deployment
- `justfile` — Task runner for common operations

### Definition of Done
- [ ] `docker compose up` starts all services, app accessible at `http://localhost:5173`
- [ ] Bot responds to `/start` command and opens Mini App via menu button
- [ ] User can register with full profile (name, phone, city, avatar)
- [ ] Seller can create listing with up to 5 photos
- [ ] Listing appears in catalog after admin approval via bot command
- [ ] Buyer can browse catalog filtered by city and category
- [ ] Buyer can click "Write in Telegram" to contact seller
- [ ] Splash screen shows for 3 seconds on app launch
- [ ] All backend tests pass: `pytest`
- [ ] All frontend tests pass: `vitest run`
- [ ] Ruff lint passes: `ruff check .`
- [ ] mypy passes: `mypy app/`
- [ ] Docker build succeeds for both services
- [ ] `docker compose -f docker-compose.prod.yml up` runs the full production stack

### Must Have
- Telegram initData HMAC validation on EVERY API request (no exceptions)
- `createWebHistory()` for Vue Router (hash mode breaks Telegram)
- `init()` called before `createApp()` in Vue entry point
- Dev mode mock for Telegram environment (app must work outside Telegram for development)
- Presigned URLs for MinIO uploads (never proxy file uploads through FastAPI)
- `auth_date` expiry check (max 1 hour) in initData validation
- `hmac.compare_digest()` for hash comparison (timing-attack safe)
- Granian `--workers 1` (aiogram in-process requires single event loop)
- Nginx `try_files $uri $uri/ /index.html` for SPA routing
- `MINIO_SERVER_URL` env var for presigned URL generation
- Listing status field: `pending` → `approved` / `rejected`
- Admin Telegram IDs in environment config for moderation

### Must NOT Have (Guardrails)
- NO favorites/bookmarks system
- NO notification system (push or bot messages to users)
- NO in-app messaging/chat
- NO search functionality (only category filter)
- NO Directus integration
- NO pgvector usage
- NO payment integration
- NO reviews/ratings
- NO `as any` or `@ts-ignore` in TypeScript
- NO `# type: ignore` in Python (fix types properly)
- NO console.log/print in production code (use proper logging)
- NO hardcoded secrets (all in environment variables)
- NO file uploads proxied through FastAPI (use MinIO presigned URLs)
- NO hash mode in Vue Router (`createWebHashHistory` is FORBIDDEN)
- NO aiohttp imports (use FastAPI patterns for webhook, not aiogram's aiohttp helpers)

---

## Verification Strategy

> **ZERO HUMAN INTERVENTION** — ALL verification is agent-executed. No exceptions.

### Test Decision
- **Infrastructure exists**: NO (greenfield)
- **Automated tests**: YES (Tests-after)
- **Backend framework**: pytest + pytest-asyncio + httpx (TestClient)
- **Frontend framework**: vitest + @vue/test-utils
- **Setup**: Test infrastructure created as part of scaffolding tasks

### QA Policy
Every task MUST include agent-executed QA scenarios.
Evidence saved to `.sisyphus/evidence/task-{N}-{scenario-slug}.{ext}`.

- **Frontend/UI**: Use Playwright (playwright skill) — Navigate, interact, assert DOM, screenshot
- **TUI/CLI**: Use interactive_bash (tmux) — Run command, send keystrokes, validate output
- **API/Backend**: Use Bash (curl/httpx) — Send requests, assert status + response fields
- **Bot commands**: Use Bash (curl to webhook endpoint) — Simulate Telegram updates

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Foundation — all independent, start immediately):
├── Task 1: Monorepo structure + root configs [quick]
├── Task 2: Backend project scaffolding [quick]
├── Task 3: Frontend project scaffolding [quick]
├── Task 4: Database models + Alembic setup [unspecified-high]
├── Task 5: TypeScript types + API client [quick]
└── Task 6: Docker Compose dev environment [quick]

Wave 2 (Integration Layer — after Wave 1):
├── Task 7: Telegram SDK init + dev mock (depends: 3) [unspecified-high]
├── Task 8: Telegram bot + webhook endpoint (depends: 2) [unspecified-high]
├── Task 9: Auth middleware — initData validation (depends: 2, 8) [deep]
├── Task 10: Redis service layer (depends: 2, 6) [quick]
├── Task 11: MinIO service layer (depends: 2, 6) [unspecified-high]
├── Task 12: Vue Router + route guards (depends: 3, 7) [quick]
└── Task 13: Pinia stores setup (depends: 3, 5, 7) [quick]

Wave 3 (Backend APIs — after Wave 2):
├── Task 14: User registration + profile API (depends: 4, 9, 11) [deep]
├── Task 15: Category API (depends: 4, 9) [unspecified-high]
├── Task 16: Listing CRUD + photo upload API (depends: 4, 9, 11) [deep]
├── Task 17: Catalog API + pagination (depends: 4, 9, 10) [unspecified-high]
└── Task 18: Bot moderation commands (depends: 8, 16) [unspecified-high]

Wave 4 (Frontend UI — after Wave 3):
├── Task 19: Splash screen (depends: 7, 12) [visual-engineering]
├── Task 20: Registration flow UI (depends: 12, 13, 14) [visual-engineering]
├── Task 21: Catalog page UI (depends: 12, 13, 17) [visual-engineering]
├── Task 22: Listing detail + seller contact (depends: 12, 13, 17) [visual-engineering]
├── Task 23: Create listing UI (depends: 12, 13, 16) [visual-engineering]
├── Task 24: User profile page UI (depends: 12, 13, 14) [visual-engineering]
└── Task 25: My listings page UI (depends: 12, 13, 16) [visual-engineering]

Wave 5 (Deployment + Testing — after Wave 4):
├── Task 26: Dockerfiles (backend + frontend) [quick]
├── Task 27: Nginx configuration [quick]
├── Task 28: Docker Compose production [quick]
├── Task 29: Backend tests — pytest (depends: 14-18) [unspecified-high]
├── Task 30: Frontend tests — vitest (depends: 19-25) [unspecified-high]
└── Task 31: Git repo init + README + .gitignore (depends: all) [quick]

Wave FINAL (Verification — after ALL tasks, 4 parallel):
├── Task F1: Plan compliance audit (oracle)
├── Task F2: Code quality review (unspecified-high)
├── Task F3: Real manual QA (unspecified-high + playwright)
└── Task F4: Scope fidelity check (deep)

Critical Path: T1 → T4 → T9 → T14 → T17 → T21 → T29 → F1-F4
Parallel Speedup: ~65% faster than sequential
Max Concurrent: 7 (Waves 2, 4)
```

### Dependency Matrix

| Task | Depends On | Blocks | Wave |
|------|-----------|--------|------|
| 1 | — | 2,3,4,5,6 | 1 |
| 2 | 1 | 7,8,9,10,11 | 1 |
| 3 | 1 | 7,12,13 | 1 |
| 4 | 1 | 14,15,16,17 | 1 |
| 5 | 1 | 13 | 1 |
| 6 | 1 | 10,11 | 1 |
| 7 | 3 | 12,13,19 | 2 |
| 8 | 2 | 9,18 | 2 |
| 9 | 2,8 | 14,15,16,17 | 2 |
| 10 | 2,6 | 17 | 2 |
| 11 | 2,6 | 14,16 | 2 |
| 12 | 3,7 | 19-25 | 2 |
| 13 | 3,5,7 | 20-25 | 2 |
| 14 | 4,9,11 | 20,24 | 3 |
| 15 | 4,9 | 21,23 | 3 |
| 16 | 4,9,11 | 18,23,25 | 3 |
| 17 | 4,9,10 | 21,22 | 3 |
| 18 | 8,16 | — | 3 |
| 19 | 7,12 | — | 4 |
| 20 | 12,13,14 | — | 4 |
| 21 | 12,13,17 | — | 4 |
| 22 | 12,13,17 | — | 4 |
| 23 | 12,13,16 | — | 4 |
| 24 | 12,13,14 | — | 4 |
| 25 | 12,13,16 | — | 4 |
| 26 | 2,3 | 28 | 5 |
| 27 | 3 | 28 | 5 |
| 28 | 26,27 | — | 5 |
| 29 | 14-18 | — | 5 |
| 30 | 19-25 | — | 5 |
| 31 | all | — | 5 |

### Agent Dispatch Summary

- **Wave 1**: **6 tasks** — T1→`quick`, T2→`quick`, T3→`quick`, T4→`unspecified-high`, T5→`quick`, T6→`quick`
- **Wave 2**: **7 tasks** — T7→`unspecified-high`, T8→`unspecified-high`, T9→`deep`, T10→`quick`, T11→`unspecified-high`, T12→`quick`, T13→`quick`
- **Wave 3**: **5 tasks** — T14→`deep`, T15→`unspecified-high`, T16→`deep`, T17→`unspecified-high`, T18→`unspecified-high`
- **Wave 4**: **7 tasks** — T19-T25→`visual-engineering`
- **Wave 5**: **6 tasks** — T26-T28,T31→`quick`, T29-T30→`unspecified-high`
- **Wave FINAL**: **4 tasks** — F1→`oracle`, F2→`unspecified-high`, F3→`unspecified-high`+`playwright`, F4→`deep`

---

## TODOs


- [ ] 1. Monorepo Structure + Root Configs

  **What to do**:
  - Create monorepo directory structure: `backend/`, `frontend/`, `infra/`
  - Create root `justfile` with recipes: `up`, `down`, `logs`, `db-migrate`, `db-revision`, `py-dev`, `py-test`, `py-lint`, `py-types`, `node-dev`, `node-build`, `node-test`, `check`, `env-init`, `secret`
  - Create `.env.example` with all required env vars (BOT_TOKEN, POSTGRES_*, REDIS_URL, MINIO_*, GRANIAN settings)
  - Create root `.gitignore` (Python, Node.js, Docker, .env, __pycache__, node_modules, dist, .vite)
  - Create `.editorconfig` for consistent formatting
  - Use `uv` as Python package manager prefix, `pnpm` as Node package manager

  **Must NOT do**:
  - Do NOT create any source code files (only configs)
  - Do NOT install dependencies (just create config files)
  - Do NOT create Dockerfiles (Task 26)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Config files only, no complex logic
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 2, 3, 4, 5, 6)
  - **Blocks**: Tasks 2, 3, 4, 5, 6
  - **Blocked By**: None (can start immediately)

  **References**:

  **Pattern References**:
  - Standard monorepo layout: `backend/` (Python), `frontend/` (Node.js), `infra/` (Docker, Nginx configs)

  **External References**:
  - `just` task runner: https://github.com/casey/just — use `{{variable}}` interpolation, `[private]`, `*args` for variadic
  - `uv` package manager: https://docs.astral.sh/uv/ — replaces pip/poetry

  **justfile recipe structure** (MUST follow this exact pattern):
  ```
  python := "uv run"
  node := "pnpm"
  
  [private]
  default:
      @just --list --unsorted
  
  up:
      docker compose up -d
  
  down:
      docker compose down
  
  logs service="api":
      docker compose logs -f {{ service }}
  
  db-migrate:
      {{ python }} alembic upgrade head
  
  db-revision msg:
      {{ python }} alembic revision --autogenerate -m "{{ msg }}"
  
  py-dev:
      {{ python }} granian --interface asgi app.main:app --reload --host 0.0.0.0 --port 8000
  
  py-test *args:
      {{ python }} pytest {{ args }} -x --tb=short
  
  py-lint:
      {{ python }} ruff check . --fix && {{ python }} ruff format .
  
  py-types:
      {{ python }} mypy app/
  
  node-dev:
      {{ node }} run dev
  
  node-build:
      {{ node }} run build
  
  node-test:
      {{ node }} run test
  
  check: py-lint py-types py-test node-test
  
  env-init:
      cp .env.example .env
  
  secret:
      python3 -c "import secrets; print(secrets.token_urlsafe(32))"
  ```

  **Acceptance Criteria**:
  - [ ] Directory structure exists: `backend/`, `frontend/`, `infra/`
  - [ ] `justfile` at project root with all recipes listed above
  - [ ] `.env.example` contains: BOT_TOKEN, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, REDIS_URL, MINIO_ROOT_USER, MINIO_ROOT_PASSWORD, MINIO_SERVER_URL, MINIO_ENDPOINT, ADMIN_TELEGRAM_IDS, APP_BASE_URL, WEBHOOK_SECRET
  - [ ] `.gitignore` covers Python, Node.js, Docker, IDE files
  - [ ] `just --list` shows all recipes without errors

  **QA Scenarios:**
  ```
  Scenario: Justfile lists all recipes
    Tool: Bash
    Preconditions: just is installed
    Steps:
      1. Run `just --list` from project root
      2. Verify output contains recipes: up, down, logs, db-migrate, py-dev, py-test, py-lint, py-types, node-dev, node-build, node-test, check, env-init, secret
    Expected Result: All 14+ recipes listed without syntax errors
    Failure Indicators: just returns error, missing recipes
    Evidence: .sisyphus/evidence/task-1-justfile-list.txt

  Scenario: .env.example has all required variables
    Tool: Bash
    Preconditions: .env.example file exists
    Steps:
      1. Run `cat .env.example`
      2. Verify contains BOT_TOKEN, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, REDIS_URL, MINIO_ROOT_USER, MINIO_ROOT_PASSWORD, ADMIN_TELEGRAM_IDS, APP_BASE_URL
    Expected Result: All required env vars present with placeholder values
    Failure Indicators: Missing required variables
    Evidence: .sisyphus/evidence/task-1-env-example.txt
  ```

  **Commit**: YES (groups with 2, 3)
  - Message: `feat(scaffold): init monorepo with backend + frontend skeletons`
  - Files: `justfile, .env.example, .gitignore, .editorconfig, backend/, frontend/, infra/`
  - Pre-commit: `just --list`

---

- [ ] 2. Backend Project Scaffolding

  **What to do**:
  - Create `backend/pyproject.toml` with all dependencies:
    - Core: fastapi, pydantic, sqlalchemy[asyncio], psycopg[binary,pool], alembic, aiogram, python-jose[cryptography], httpx, redis[hiredis], minio, granian[uvloop]
    - Dev: pytest, pytest-asyncio, pytest-cov, httpx (for TestClient), ruff, mypy, types-redis
  - Create `backend/app/` package structure:
    ```
    app/
    ├── __init__.py
    ├── main.py            # FastAPI app with lifespan
    ├── config.py           # Pydantic Settings class
    ├── deps.py             # FastAPI dependencies (get_db, get_redis, get_tg_user)
    ├── api/
    │   ├── __init__.py
    │   └── router.py       # Empty APIRouter placeholder
    ├── bot/
    │   ├── __init__.py
    │   └── handlers.py     # Empty placeholder
    ├── models/
    │   ├── __init__.py
    │   └── base.py         # SQLAlchemy DeclarativeBase
    ├── schemas/
    │   └── __init__.py
    ├── services/
    │   └── __init__.py
    └── utils/
        └── __init__.py
    ```
  - `app/main.py`: FastAPI app with lifespan (startup: DB, Redis, MinIO, Bot webhook; shutdown: cleanup). Include `/api/health` endpoint returning `{"status": "ok"}`
  - `app/config.py`: Pydantic `BaseSettings` class with all env vars (DATABASE_URL, REDIS_URL, BOT_TOKEN, MINIO_*, ADMIN_TELEGRAM_IDS as list[int], APP_BASE_URL, WEBHOOK_SECRET)
  - `backend/ruff.toml`: line-length=120, target Python 3.12, select=["E", "F", "I", "UP", "B", "SIM", "TCH"]
  - `backend/mypy.ini`: strict mode, plugins=[pydantic.mypy, sqlalchemy.ext.mypy.plugin]
  - `backend/alembic.ini` + `backend/alembic/` directory (empty migration env, configured for async)

  **Must NOT do**:
  - Do NOT implement any business logic
  - Do NOT create database models (Task 4)
  - Do NOT set up bot handlers (Task 8)
  - Do NOT implement auth middleware (Task 9)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Boilerplate scaffolding, no business logic
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 3, 4, 5, 6)
  - **Blocks**: Tasks 7, 8, 9, 10, 11
  - **Blocked By**: Task 1 (needs monorepo structure)

  **References**:

  **External References**:
  - FastAPI lifespan: https://fastapi.tiangolo.com/advanced/events/ — use `@asynccontextmanager` pattern
  - Pydantic Settings: https://docs.pydantic.dev/latest/concepts/pydantic_settings/ — `model_config = SettingsConfigDict(env_file=".env")`
  - Granian CLI: `granian --interface asgi --host 0.0.0.0 --port 8000 --workers 1 --loop uvloop app.main:app`
  - Alembic async: https://alembic.sqlalchemy.org/en/latest/cookbook.html#using-asyncio-with-alembic

  **WHY Each Reference Matters**:
  - FastAPI lifespan manages startup/shutdown of DB pool, Redis, MinIO client, and bot webhook registration — this is the foundation everything plugs into
  - Pydantic Settings reads .env file and provides typed config — used by every service
  - Granian must use `--workers 1` because aiogram bot runs in-process (single event loop required)

  **Acceptance Criteria**:
  - [ ] `cd backend && uv sync` installs all dependencies without errors
  - [ ] `cd backend && uv run python -c "from app.main import app; print(app.title)"` prints app title
  - [ ] `cd backend && uv run ruff check .` passes
  - [ ] `cd backend && uv run mypy app/` passes
  - [ ] Directory structure matches spec above
  - [ ] `app/config.py` loads all env vars via Pydantic Settings

  **QA Scenarios:**
  ```
  Scenario: Backend dependencies install cleanly
    Tool: Bash
    Preconditions: uv is installed, pyproject.toml exists
    Steps:
      1. Run `cd backend && uv sync`
      2. Run `uv run python -c "import fastapi, aiogram, sqlalchemy, redis, minio; print('OK')"` 
    Expected Result: All imports succeed, prints 'OK'
    Failure Indicators: ImportError, uv sync failure
    Evidence: .sisyphus/evidence/task-2-deps-install.txt

  Scenario: Health endpoint responds
    Tool: Bash
    Preconditions: App can be imported
    Steps:
      1. Run `cd backend && uv run python -c "from app.main import app; from fastapi.testclient import TestClient; c=TestClient(app); r=c.get('/api/health'); print(r.status_code, r.json())"` 
    Expected Result: `200 {'status': 'ok'}`
    Failure Indicators: Import error, non-200 status, missing endpoint
    Evidence: .sisyphus/evidence/task-2-health-endpoint.txt
  ```

  **Commit**: YES (groups with 1, 3)
  - Message: `feat(scaffold): init monorepo with backend + frontend skeletons`
  - Files: `backend/**`
  - Pre-commit: `cd backend && uv run ruff check .`

---

- [ ] 3. Frontend Project Scaffolding

  **What to do**:
  - Initialize Vue 3 + TypeScript + Vite project in `frontend/` using `pnpm create vue@latest` or manual setup
  - Install dependencies:
    - Core: vue, vue-router, pinia, axios, @telegram-apps/sdk-vue, lucide-vue-next
    - Styles: tailwindcss, @tailwindcss/vite
    - Dev: typescript, vite, @vitejs/plugin-vue, vitest, @vue/test-utils, jsdom
  - Create project structure:
    ```
    frontend/src/
    ├── api/                  # Axios instance + API modules
    │   └── client.ts         # Axios instance (placeholder)
    ├── assets/
    │   └── main.css          # TailwindCSS v4 import + @theme
    ├── components/
    │   ├── ui/               # Shared UI primitives (empty)
    │   └── layout/           # AppLayout.vue placeholder
    ├── composables/          # Shared composables (empty)
    ├── features/             # Feature modules (empty dirs)
    ├── router/
    │   ├── index.ts          # createRouter with createWebHistory()
    │   └── routes.ts         # Empty routes array
    ├── stores/               # Global Pinia stores (empty)
    ├── types/                # Global TypeScript types (empty)
    ├── App.vue               # Root component with <RouterView>
    └── main.ts               # Entry: init TG SDK → createApp → mount
    ```
  - `vite.config.ts`: Vue plugin, TailwindCSS v4 vite plugin, path alias `@` → `./src`, proxy `/api` to `http://localhost:8000`
  - `frontend/src/assets/main.css`: TailwindCSS v4 with `@import "tailwindcss"` and `@theme {}` for Stella brand colors
  - `frontend/src/main.ts`: Import CSS, call `init()` from SDK (with dev mode guard), create Pinia, create Router, create App, mount
  - `tsconfig.json` + `tsconfig.app.json` with strict mode, path aliases
  - `frontend/.env.example`: VITE_API_URL=http://localhost:8000

  **Must NOT do**:
  - Do NOT implement any pages or features
  - Do NOT create Pinia stores (Task 13)
  - Do NOT set up route guards (Task 12)
  - Do NOT configure Axios interceptors (Task 5)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Boilerplate scaffolding, no business logic
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 2, 4, 5, 6)
  - **Blocks**: Tasks 7, 12, 13
  - **Blocked By**: Task 1 (needs monorepo structure)

  **References**:

  **External References**:
  - Vue 3 + Vite: https://vitejs.dev/guide/ — use `defineConfig` with `loadEnv`
  - TailwindCSS v4 Vite plugin: https://tailwindcss.com/docs/installation/vite — `@tailwindcss/vite` replaces PostCSS setup
  - `@telegram-apps/sdk-vue` v2.x: https://www.npmjs.com/package/@telegram-apps/sdk-vue — `init()` before `createApp()`
  - Lucide Vue Next: https://lucide.dev/guide/packages/lucide-vue-next — named imports, auto tree-shaken

  **WHY Each Reference Matters**:
  - TailwindCSS v4 has NO config file — all configuration is in CSS `@theme {}`. Agent must NOT create `tailwind.config.js`
  - SDK `init()` MUST be called before `createApp()` and THROWS outside Telegram. Dev guard is critical
  - Vue Router MUST use `createWebHistory()` — `createWebHashHistory()` destroys Telegram launch params

  **vite.config.ts MUST follow this pattern:**
  ```typescript
  import { defineConfig, loadEnv } from 'vite'
  import vue from '@vitejs/plugin-vue'
  import tailwindcss from '@tailwindcss/vite'
  import { fileURLToPath, URL } from 'node:url'

  export default defineConfig(({ mode }) => {
    const env = loadEnv(mode, process.cwd(), '')
    return {
      plugins: [vue(), tailwindcss()],
      resolve: {
        alias: { '@': fileURLToPath(new URL('./src', import.meta.url)) },
      },
      server: {
        port: 5173,
        proxy: {
          '/api': {
            target: env.VITE_API_URL || 'http://localhost:8000',
            changeOrigin: true,
          },
        },
      },
      build: {
        outDir: 'dist',
        target: 'es2020',
        rollupOptions: {
          output: {
            manualChunks: {
              'vue-vendor': ['vue', 'vue-router', 'pinia'],
              'ui-vendor': ['lucide-vue-next'],
            },
          },
        },
      },
    }
  })
  ```

  **main.ts MUST follow this pattern:**
  ```typescript
  import { createApp } from 'vue'
  import { createPinia } from 'pinia'
  import { init, isTMA, mockTelegramEnv } from '@telegram-apps/sdk-vue'
  import App from './App.vue'
  import { router } from './router'
  import './assets/main.css'

  async function bootstrap() {
    // Dev mode: mock Telegram environment
    if (import.meta.env.DEV) {
      const isTma = await isTMA('complete')
      if (!isTma) {
        mockTelegramEnv({
          themeParams: {
            accentTextColor: '#6ab2f2',
            bgColor: '#17212b',
            buttonColor: '#5288c1',
            buttonTextColor: '#ffffff',
            destructiveTextColor: '#ec3942',
            headerBgColor: '#17212b',
            hintColor: '#708499',
            linkColor: '#6ab3f3',
            secondaryBgColor: '#232e3c',
            sectionBgColor: '#17212b',
            sectionHeaderTextColor: '#6ab3f3',
            subtitleTextColor: '#708499',
            textColor: '#f5f5f5',
          },
          initData: {
            user: {
              id: 99281932,
              firstName: 'Test',
              lastName: 'User',
              username: 'testuser',
              languageCode: 'en',
              allowsWriteToPm: true,
              photoUrl: 'https://t.me/i/userpic/320/testuser.svg',
            },
            hash: 'mock-hash',
            authDate: new Date(),
            startParam: 'debug',
            chatType: 'sender',
            chatInstance: '-1',
          },
          version: '8',
          platform: 'tdesktop',
        })
      }
    }

    init()

    const app = createApp(App)
    app.use(createPinia())
    app.use(router)
    app.mount('#app')
  }

  bootstrap()
  ```

  **Acceptance Criteria**:
  - [ ] `cd frontend && pnpm install` succeeds
  - [ ] `cd frontend && pnpm run dev` starts dev server at localhost:5173
  - [ ] `cd frontend && pnpm run build` produces `dist/` directory
  - [ ] `cd frontend && npx vue-tsc --noEmit` passes
  - [ ] No `tailwind.config.js` file exists (v4 uses CSS @theme)
  - [ ] `vite.config.ts` uses `@tailwindcss/vite` plugin
  - [ ] `main.ts` calls `init()` with dev mock guard

  **QA Scenarios:**
  ```
  Scenario: Frontend dev server starts
    Tool: Bash
    Preconditions: pnpm install completed
    Steps:
      1. Run `cd frontend && pnpm run dev &` (background)
      2. Wait 5 seconds
      3. Run `curl -s http://localhost:5173 | head -20`
      4. Kill dev server
    Expected Result: HTML response contains `<div id="app">` and script tags
    Failure Indicators: Connection refused, build errors
    Evidence: .sisyphus/evidence/task-3-dev-server.txt

  Scenario: Production build succeeds
    Tool: Bash
    Preconditions: Dependencies installed
    Steps:
      1. Run `cd frontend && pnpm run build`
      2. Verify `dist/index.html` exists
      3. Verify `dist/assets/` contains .js and .css files
    Expected Result: Build succeeds, dist/ has index.html + assets with hash in filename
    Failure Indicators: Build error, empty dist/
    Evidence: .sisyphus/evidence/task-3-build.txt
  ```

  **Commit**: YES (groups with 1, 2)
  - Message: `feat(scaffold): init monorepo with backend + frontend skeletons`
  - Files: `frontend/**`
  - Pre-commit: `cd frontend && npx vue-tsc --noEmit`

---

- [ ] 4. Database Models + Alembic Setup

  **What to do**:
  - Create SQLAlchemy 2 async models in `backend/app/models/`:
    - `user.py`: User model — `id` (UUID, PK), `telegram_id` (BigInt, unique, indexed), `first_name` (str), `last_name` (str, nullable), `username` (str, nullable), `phone` (str, nullable), `city` (str, nullable), `latitude` (Float, nullable), `longitude` (Float, nullable), `avatar_url` (str, nullable — MinIO object key), `is_registered` (bool, default False), `created_at`, `updated_at`
    - `category.py`: Category model — `id` (UUID, PK), `name` (str, unique), `slug` (str, unique, indexed), `icon` (str, nullable — Lucide icon name), `is_approved` (bool, default True for admin-created, False for user-proposed), `created_by` (FK → User, nullable — null for admin-created), `created_at`
    - `listing.py`: Listing model — `id` (UUID, PK), `title` (str), `description` (text), `price` (Numeric(12,2)), `currency` (str, default 'RUB'), `status` (Enum: pending/approved/rejected, default pending), `city` (str, indexed), `category_id` (FK → Category), `seller_id` (FK → User), `created_at`, `updated_at`
    - `listing_photo.py`: ListingPhoto model — `id` (UUID, PK), `listing_id` (FK → Listing, cascade delete), `object_key` (str — MinIO key), `position` (int — order 0-4), `created_at`
  - Configure `backend/app/models/base.py` with DeclarativeBase + mapped_column defaults
  - Create `backend/app/models/__init__.py` that re-exports all models (for Alembic autogenerate)
  - Configure Alembic `env.py` for async engine (use `run_async` pattern), import all models for autogenerate
  - Generate initial migration: `alembic revision --autogenerate -m "initial schema"`
  - Create seed data script or initial migration with default categories:
    Electronics, Clothing, Home & Garden, Auto, Sports, Books, Kids, Services, Pets, Other

  **Must NOT do**:
  - Do NOT create API endpoints (Tasks 14-17)
  - Do NOT implement any service logic
  - Do NOT add pgvector columns (deferred from MVP)

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Database schema design requires careful FK relationships and type choices
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 2, 3, 5, 6)
  - **Blocks**: Tasks 14, 15, 16, 17
  - **Blocked By**: Task 1 (monorepo structure)

  **References**:

  **External References**:
  - SQLAlchemy 2 async: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html — `async_sessionmaker`, `create_async_engine`
  - SQLAlchemy mapped_column: https://docs.sqlalchemy.org/en/20/orm/mapped_column.html — modern declarative style
  - Alembic async cookbook: https://alembic.sqlalchemy.org/en/latest/cookbook.html#using-asyncio-with-alembic
  - psycopg3 async: https://www.psycopg.org/psycopg3/docs/advanced/async.html

  **Model relationships** (MUST implement correctly):
  - Listing → User (many-to-one): `seller = relationship('User', back_populates='listings')`
  - Listing → Category (many-to-one): `category = relationship('Category', back_populates='listings')`
  - Listing → ListingPhoto (one-to-many, cascade delete): `photos = relationship('ListingPhoto', back_populates='listing', cascade='all, delete-orphan')`
  - User → Listing (one-to-many): `listings = relationship('Listing', back_populates='seller')`
  - User → Category (one-to-many, proposed): `proposed_categories = relationship('Category', back_populates='created_by_user')`

  **Acceptance Criteria**:
  - [ ] All 4 model files exist with correct columns and relationships
  - [ ] `alembic upgrade head` succeeds against a running PostgreSQL
  - [ ] `alembic downgrade base` and `alembic upgrade head` round-trip works
  - [ ] Default categories seeded in DB after migration
  - [ ] `cd backend && uv run mypy app/models/` passes

  **QA Scenarios:**
  ```
  Scenario: Alembic migration applies cleanly
    Tool: Bash
    Preconditions: Docker Compose PG running (`docker compose up -d postgres`)
    Steps:
      1. Run `cd backend && uv run alembic upgrade head`
      2. Run `docker compose exec postgres psql -U stella -d stella -c "\dt"` to list tables
      3. Verify tables exist: users, categories, listings, listing_photos, alembic_version
    Expected Result: All 4 app tables + alembic_version table present
    Failure Indicators: Migration error, missing tables, FK constraint errors
    Evidence: .sisyphus/evidence/task-4-migration.txt

  Scenario: Default categories are seeded
    Tool: Bash
    Preconditions: Migration applied
    Steps:
      1. Run `docker compose exec postgres psql -U stella -d stella -c "SELECT name FROM categories ORDER BY name"`
      2. Count rows
    Expected Result: 10 default categories listed (Auto, Books, Clothing, Electronics, Home & Garden, Kids, Other, Pets, Services, Sports)
    Failure Indicators: Empty result, fewer than 10 categories
    Evidence: .sisyphus/evidence/task-4-seed-categories.txt
  ```

  **Commit**: YES
  - Message: `feat(db): add SQLAlchemy models and Alembic migrations`
  - Files: `backend/app/models/**, backend/alembic/**, backend/alembic.ini`
  - Pre-commit: `cd backend && uv run ruff check . && uv run mypy app/`

---

- [ ] 5. TypeScript Types + Axios API Client

  **What to do**:
  - Create `frontend/src/types/` with shared TypeScript interfaces matching backend Pydantic schemas:
    - `user.ts`: `User`, `UserRegistration`, `UserProfile`, `UserUpdate`
    - `listing.ts`: `Listing`, `ListingCreate`, `ListingUpdate`, `ListingPhoto`, `ListingStatus` (enum: pending/approved/rejected)
    - `category.ts`: `Category`, `CategoryCreate`
    - `common.ts`: `PaginatedResponse<T>` (items, total, page, per_page), `ApiError`
    - `index.ts`: barrel export
  - Create `frontend/src/api/client.ts`:
    - Axios instance with baseURL `/api`, timeout 10s
    - Request interceptor: attach `Authorization: tma <initData.raw()>` header from `@telegram-apps/sdk`
    - Response interceptor: handle 401 (redirect to error page), 500 (console.error)
  - Create API module stubs (empty functions with correct types):
    - `frontend/src/api/users.ts`: `getProfile()`, `register()`, `updateProfile()`, `uploadAvatar()`
    - `frontend/src/api/listings.ts`: `getListings()`, `getListing()`, `createListing()`, `updateListing()`, `deleteListing()`, `getMyListings()`, `getUploadUrl()`
    - `frontend/src/api/categories.ts`: `getCategories()`, `proposeCategory()`

  **Must NOT do**:
  - Do NOT implement API function bodies (just typed stubs returning `Promise<T>`)
  - Do NOT create Pinia stores (Task 13)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Type definitions and stub functions, no complex logic
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 2, 3, 4, 6)
  - **Blocks**: Task 13 (Pinia stores)
  - **Blocked By**: Task 1 (monorepo structure)

  **References**:

  **External References**:
  - Axios interceptors: https://axios-http.com/docs/interceptors — request and response interceptor pattern
  - `@telegram-apps/sdk`: `initData.raw()` returns the URL-encoded string for backend validation
  - Auth header convention: `Authorization: tma <initData>` — de-facto standard for TMA backends

  **Axios client MUST follow this pattern:**
  ```typescript
  import axios from 'axios'
  import { initData } from '@telegram-apps/sdk-vue'

  const apiClient = axios.create({
    baseURL: import.meta.env.VITE_API_URL || '/api',
    timeout: 10_000,
    headers: { 'Content-Type': 'application/json' },
  })

  apiClient.interceptors.request.use((config) => {
    const raw = initData.raw()
    if (raw) {
      config.headers['Authorization'] = `tma ${raw}`
    }
    return config
  })

  apiClient.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.response?.status === 401) {
        // initData expired or invalid
        window.location.href = '/error?reason=auth-failed'
      }
      return Promise.reject(error)
    }
  )

  export default apiClient
  ```

  **Acceptance Criteria**:
  - [ ] All type files in `frontend/src/types/` with correct interfaces
  - [ ] `frontend/src/api/client.ts` with Axios instance + interceptors
  - [ ] API module stubs with typed function signatures
  - [ ] `cd frontend && npx vue-tsc --noEmit` passes

  **QA Scenarios:**
  ```
  Scenario: TypeScript types compile cleanly
    Tool: Bash
    Preconditions: Frontend dependencies installed
    Steps:
      1. Run `cd frontend && npx vue-tsc --noEmit`
    Expected Result: Exit code 0, no type errors
    Failure Indicators: Type errors in types/ or api/ files
    Evidence: .sisyphus/evidence/task-5-tsc.txt
  ```

  **Commit**: YES (groups with 6)
  - Message: `feat(infra): add TypeScript types, API client, Docker Compose dev`
  - Files: `frontend/src/types/**, frontend/src/api/**`
  - Pre-commit: `cd frontend && npx vue-tsc --noEmit`

---

- [ ] 6. Docker Compose Dev Environment

  **What to do**:
  - Create `docker-compose.yml` with development services:
    - **postgres**: image `pgvector/pgvector:pg16`, env from .env, volume `postgres_data`, healthcheck with `pg_isready`, port 5432, init script at `infra/postgres/init.sql` that runs `CREATE EXTENSION IF NOT EXISTS vector; CREATE EXTENSION IF NOT EXISTS pg_trgm;`
    - **redis**: image `redis:7-alpine`, command with `--maxmemory 256mb --maxmemory-policy volatile-lru --save 60 1000`, volume `redis_data`, healthcheck with `redis-cli ping`, port 6379
    - **minio**: image `minio/minio:latest`, command `server /data --console-address ":9001"`, env MINIO_ROOT_USER/PASSWORD from .env, volume `minio_data`, healthcheck with `mc ready local`, ports 9000 (API) + 9001 (console)
  - Create `infra/postgres/init.sql` with extension creation
  - Create `infra/minio/` directory (placeholder for bucket init scripts)
  - Named volumes: postgres_data, redis_data, minio_data
  - All services with `restart: unless-stopped`

  **Must NOT do**:
  - Do NOT add api/frontend services to dev compose (those run locally with hot-reload)
  - Do NOT create production compose (Task 28)
  - Do NOT add Directus service (deferred from MVP)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Docker Compose config, no business logic
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 2, 3, 4, 5)
  - **Blocks**: Tasks 10, 11
  - **Blocked By**: Task 1 (monorepo structure)

  **References**:

  **External References**:
  - pgvector Docker: https://hub.docker.com/r/pgvector/pgvector — use `pgvector/pgvector:pg16`
  - MinIO Docker: https://hub.docker.com/r/minio/minio — `server /data --console-address ":9001"`
  - Redis Alpine: https://hub.docker.com/_/redis — `redis:7-alpine` minimal image

  **WHY Each Reference Matters**:
  - `pgvector/pgvector:pg16` includes pgvector extension pre-built — standard `postgres:16` does NOT
  - MinIO console on port 9001 is needed for dev to view uploaded files
  - Redis `volatile-lru` policy evicts only keys with TTL set — safe for mixed cache+session usage

  **Acceptance Criteria**:
  - [ ] `docker compose up -d` starts all 3 services
  - [ ] `docker compose ps` shows postgres, redis, minio as healthy
  - [ ] `docker compose exec postgres psql -U stella -d stella -c "SELECT 1"` succeeds
  - [ ] `docker compose exec redis redis-cli ping` returns PONG
  - [ ] MinIO console accessible at `http://localhost:9001`

  **QA Scenarios:**
  ```
  Scenario: All dev services start and are healthy
    Tool: Bash
    Preconditions: Docker is running
    Steps:
      1. Copy `.env.example` to `.env` and fill placeholder values
      2. Run `docker compose up -d`
      3. Wait 15 seconds
      4. Run `docker compose ps --format json`
      5. Verify all 3 services show "running" status
      6. Run `docker compose exec postgres psql -U stella -d stella -c "SELECT extname FROM pg_extension WHERE extname='vector'"`
    Expected Result: All services running, pgvector extension available
    Failure Indicators: Service not starting, unhealthy status, missing extension
    Evidence: .sisyphus/evidence/task-6-services-health.txt

  Scenario: MinIO console is accessible
    Tool: Bash
    Preconditions: Docker compose running
    Steps:
      1. Run `curl -s -o /dev/null -w "%{http_code}" http://localhost:9001`
    Expected Result: HTTP 200 response
    Failure Indicators: Connection refused, non-200 status
    Evidence: .sisyphus/evidence/task-6-minio-console.txt
  ```

  **Commit**: YES (groups with 5)
  - Message: `feat(infra): add TypeScript types, API client, Docker Compose dev`
  - Files: `docker-compose.yml, infra/**`
  - Pre-commit: `docker compose config --quiet`

---

- [ ] 7. Telegram SDK Initialization + Dev Mock

  **What to do**:
  - Create `frontend/src/composables/useTelegram.ts` composable:
    - Wraps `@telegram-apps/sdk-vue` for consistent access
    - Exposes reactive: `user`, `initDataRaw`, `isReady`, `colorScheme`, `themeParams`
    - Mount and bind SDK components: `viewport.mount()`, `viewport.bindCssVars()`, `themeParams.mount()`, `themeParams.bindCssVars()`, `backButton.mount()`
    - Use `useSignal()` from SDK to convert signals to Vue refs
  - Create `frontend/src/lib/telegram-mock.ts`:
    - Contains `mockTelegramEnv()` call with realistic test data (user, theme, etc.)
    - Imported in `main.ts` only in dev mode when `!isTMA('complete')`
    - Mock data should match Telegram dark theme for visual development
  - Update `main.ts` to mount SDK components after `init()` but before `createApp()`
  - Create CSS variables mapping: `--tg-viewport-height`, `--tg-theme-bg-color`, etc. available globally via `bindCssVars()`
  - Handle Telegram expanding: call `viewport.expand()` on mount for fullscreen Mini App

  **Must NOT do**:
  - Do NOT create route guards (Task 12)
  - Do NOT create Pinia stores (Task 13)
  - Do NOT implement any UI pages

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Telegram SDK integration requires careful init order and signal handling
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (after Wave 1)
  - **Parallel Group**: Wave 2 (with Tasks 8, 9, 10, 11, 12, 13)
  - **Blocks**: Tasks 12, 13, 19
  - **Blocked By**: Task 3 (frontend scaffolding)

  **References**:

  **External References**:
  - @telegram-apps/sdk-vue: https://www.npmjs.com/package/@telegram-apps/sdk-vue — Vue bindings for Telegram SDK
  - SDK init docs: https://docs.telegram-mini-apps.com/ — `init()`, `useSignal()`, component mount pattern
  - Mock environment: `mockTelegramEnv()` from `@telegram-apps/sdk-vue` — for development outside Telegram

  **WHY Each Reference Matters**:
  - `init()` MUST be called before any SDK component or composable — it configures the global SDK state
  - `useSignal()` wraps SDK signals into Vue `ref()` — required for reactivity in Vue components
  - `mockTelegramEnv()` prevents `init()` from throwing in non-Telegram browser (critical for dev experience)
  - `viewport.expand()` makes Mini App fullscreen — without it, the app shows in compact mode

  **Component mount pattern (MUST follow):**
  ```typescript
  // Every SDK component follows: check availability → mount → use
  import { viewport, themeParams, backButton } from '@telegram-apps/sdk-vue'

  if (viewport.mount.isAvailable()) {
    viewport.mount()
    viewport.bindCssVars()  // exposes --tg-viewport-height, --tg-viewport-width
    if (viewport.expand.isAvailable()) viewport.expand()
  }

  if (themeParams.mount.isAvailable()) {
    themeParams.mount()
    themeParams.bindCssVars()  // exposes --tg-theme-bg-color, --tg-theme-text-color, etc.
  }

  if (backButton.mount.isAvailable()) {
    backButton.mount()
  }
  ```

  **Acceptance Criteria**:
  - [ ] `useTelegram` composable exports reactive user, initDataRaw, isReady
  - [ ] Dev mode mock works: app loads in regular browser without errors
  - [ ] CSS variables `--tg-viewport-height`, `--tg-theme-bg-color` are available
  - [ ] `npx vue-tsc --noEmit` passes

  **QA Scenarios:**
  ```
  Scenario: Dev mock loads without errors
    Tool: Bash
    Preconditions: Frontend deps installed
    Steps:
      1. Run `cd frontend && VITE_DEV=true pnpm run dev &`
      2. Wait 5 seconds
      3. Run `curl -s http://localhost:5173 | grep -c 'app'`
    Expected Result: No console errors about Telegram SDK, page loads
    Failure Indicators: init() throws, mock not applied
    Evidence: .sisyphus/evidence/task-7-dev-mock.txt
  ```

  **Commit**: YES (groups with 8)
  - Message: `feat(telegram): integrate SDK init + bot webhook`
  - Files: `frontend/src/composables/useTelegram.ts, frontend/src/lib/telegram-mock.ts, frontend/src/main.ts`
  - Pre-commit: `cd frontend && npx vue-tsc --noEmit`

---

- [ ] 8. Telegram Bot + Webhook Endpoint

  **What to do**:
  - Create `backend/app/bot/` module:
    - `bot.py`: Create `Bot` instance with `DefaultBotProperties(parse_mode=ParseMode.HTML)`, create `Dispatcher`
    - `handlers.py`: `/start` command handler — sends welcome message with InlineKeyboardButton that has `web_app=WebAppInfo(url=APP_BASE_URL)`
    - `webhook.py`: FastAPI `POST /bot/webhook` endpoint that validates `X-Telegram-Bot-Api-Secret-Token` header, parses `Update`, and calls `dp.feed_update(bot, update)`
  - Integrate bot lifecycle into FastAPI lifespan (`app/main.py`):
    - On startup: `bot.set_webhook(url, secret_token, allowed_updates, drop_pending_updates=True)`
    - On startup: `bot.set_chat_menu_button(MenuButtonWebApp(text="Открыть Stella", web_app=WebAppInfo(url=APP_BASE_URL)))`
    - On shutdown: `bot.delete_webhook()`, `bot.session.close()`
  - Use `dp.resolve_used_update_types()` for `allowed_updates` parameter

  **Must NOT do**:
  - Do NOT use `from aiogram.webhook.aiohttp_server import ...` — that’s aiohttp-only, we use FastAPI
  - Do NOT implement moderation commands (Task 18)
  - Do NOT implement web_app_data handling (not needed for this MVP)
  - Do NOT use polling mode (webhook only)

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Bot + webhook integration requires careful lifecycle management
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (after Wave 1)
  - **Parallel Group**: Wave 2 (with Tasks 7, 9, 10, 11, 12, 13)
  - **Blocks**: Tasks 9, 18
  - **Blocked By**: Task 2 (backend scaffolding)

  **References**:

  **External References**:
  - aiogram 3.x webhook: https://github.com/aiogram/aiogram/blob/dev-3.x/examples/web_app/main.py — canonical example
  - aiogram types: `WebAppInfo`, `MenuButtonWebApp`, `InlineKeyboardButton` from `aiogram.types`
  - Telegram Bot API: https://core.telegram.org/bots/api#setwebhook — webhook configuration

  **WHY Each Reference Matters**:
  - The aiogram example uses aiohttp — we MUST adapt to FastAPI pattern (lifespan + raw POST endpoint)
  - `dp.feed_update(bot, update)` is the aiogram 3.x way to process updates programmatically (NOT `SimpleRequestHandler`)
  - `X-Telegram-Bot-Api-Secret-Token` header verification prevents unauthorized webhook calls

  **Webhook endpoint MUST follow this pattern:**
  ```python
  from fastapi import Request, Response
  from aiogram.types import Update

  @app.post("/bot/webhook")
  async def bot_webhook(request: Request) -> Response:
      if request.headers.get("X-Telegram-Bot-Api-Secret-Token") != settings.WEBHOOK_SECRET:
          return Response(status_code=403)
      body = await request.json()
      update = Update.model_validate(body, context={"bot": bot})
      await dp.feed_update(bot, update)
      return Response()
  ```

  **Acceptance Criteria**:
  - [ ] Bot module created with dispatcher and handlers
  - [ ] Webhook endpoint registered at `/bot/webhook`
  - [ ] Secret token validation on webhook
  - [ ] Lifespan registers/deregisters webhook
  - [ ] `/start` handler sends keyboard with Mini App button
  - [ ] `cd backend && uv run ruff check . && uv run mypy app/` passes

  **QA Scenarios:**
  ```
  Scenario: Webhook endpoint rejects unauthorized requests
    Tool: Bash
    Preconditions: FastAPI app running
    Steps:
      1. Run `curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/bot/webhook -H "Content-Type: application/json" -d '{}'`
    Expected Result: HTTP 403 (no secret token header)
    Failure Indicators: 200 or 500 response
    Evidence: .sisyphus/evidence/task-8-webhook-auth.txt

  Scenario: Webhook endpoint accepts valid update
    Tool: Bash
    Preconditions: FastAPI app running with BOT_TOKEN set
    Steps:
      1. Run `curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/bot/webhook -H "Content-Type: application/json" -H "X-Telegram-Bot-Api-Secret-Token: $WEBHOOK_SECRET" -d '{"update_id": 1}'`
    Expected Result: HTTP 200 (update processed or ignored gracefully)
    Failure Indicators: 500 error, unhandled exception
    Evidence: .sisyphus/evidence/task-8-webhook-valid.txt
  ```

  **Commit**: YES (groups with 7)
  - Message: `feat(telegram): integrate SDK init + bot webhook`
  - Files: `backend/app/bot/**`
  - Pre-commit: `cd backend && uv run ruff check . && uv run mypy app/`

---

- [ ] 9. Auth Middleware — initData Validation

  **What to do**:
  - Create `backend/app/auth.py`:
    - FastAPI dependency `get_current_user` that extracts and validates Telegram initData from `Authorization` header
    - Header format: `Authorization: tma <initData_raw_string>`
    - Use `aiogram.utils.web_app.safe_parse_webapp_init_data(token=BOT_TOKEN, init_data=raw_string)` for validation
    - Check `auth_date` is not older than 1 hour (3600 seconds)
    - After validation, find or create User in database by `telegram_id`
    - Return User ORM object as the dependency result
  - Create `backend/app/deps.py` with shared dependencies:
    - `get_db() -> AsyncSession`: yields session from async sessionmaker
    - `get_redis() -> redis.asyncio.Redis`: returns Redis from app state
    - `get_current_user() -> User`: auth dependency (calls auth.py logic)
    - `require_registered_user() -> User`: wraps get_current_user + checks `is_registered=True`, raises 403 if not
    - `require_admin() -> User`: checks telegram_id in ADMIN_TELEGRAM_IDS, raises 403 if not

  **Must NOT do**:
  - Do NOT use python-jose for initData validation — aiogram has built-in HMAC validation
  - Do NOT implement custom HMAC — use `safe_parse_webapp_init_data()` from aiogram
  - Do NOT skip auth_date expiry check
  - Do NOT use `==` for hash comparison (use `hmac.compare_digest` — aiogram handles this internally)

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Security-critical auth system, must be correct
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (after Tasks 2, 8)
  - **Parallel Group**: Wave 2 (with Tasks 7, 8, 10, 11, 12, 13)
  - **Blocks**: Tasks 14, 15, 16, 17
  - **Blocked By**: Tasks 2 (backend scaffolding), 8 (bot setup for BOT_TOKEN)

  **References**:

  **External References**:
  - aiogram initData validation: `aiogram.utils.web_app.safe_parse_webapp_init_data` and `check_webapp_signature`
  - Telegram validation docs: https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
  - FastAPI dependencies: https://fastapi.tiangolo.com/tutorial/dependencies/

  **WHY Each Reference Matters**:
  - `safe_parse_webapp_init_data()` handles ALL validation including HMAC, field parsing, and user extraction
  - The Telegram docs describe the exact algorithm — aiogram implements it, but understanding it helps debug issues
  - FastAPI Depends pattern is how we inject the authenticated user into every endpoint

  **Auth dependency MUST follow this pattern:**
  ```python
  from fastapi import Depends, HTTPException, Header
  from aiogram.utils.web_app import safe_parse_webapp_init_data
  import time

  async def get_current_user(
      authorization: str = Header(...),
      db: AsyncSession = Depends(get_db),
  ) -> User:
      if not authorization.startswith("tma "):
          raise HTTPException(401, "Invalid auth scheme")
      raw_init_data = authorization[4:]  # strip 'tma ' prefix
      try:
          data = safe_parse_webapp_init_data(token=settings.BOT_TOKEN, init_data=raw_init_data)
      except ValueError:
          raise HTTPException(401, "Invalid initData")
      # Check expiry
      if time.time() - data.auth_date.timestamp() > 3600:
          raise HTTPException(401, "initData expired")
      # Find or create user
      user = await get_or_create_user(db, data.user)
      return user
  ```

  **Acceptance Criteria**:
  - [ ] Auth dependency validates initData via aiogram built-in
  - [ ] Auth dependency checks auth_date expiry (1 hour max)
  - [ ] Auth dependency auto-creates User record on first visit
  - [ ] `require_registered_user` raises 403 for unregistered users
  - [ ] `require_admin` raises 403 for non-admin users
  - [ ] All dependencies properly typed for mypy

  **QA Scenarios:**
  ```
  Scenario: Auth rejects missing Authorization header
    Tool: Bash
    Preconditions: Backend running
    Steps:
      1. Run `curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/health`
      2. Run `curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/profile` (no auth header)
    Expected Result: /api/health returns 200 (public), /api/profile returns 401 (requires auth)
    Failure Indicators: /api/profile returns 200 without auth
    Evidence: .sisyphus/evidence/task-9-auth-reject.txt

  Scenario: Auth rejects expired initData
    Tool: Bash
    Preconditions: Backend running, test initData with old auth_date
    Steps:
      1. Create initData string with auth_date from 2 hours ago
      2. Send request with `Authorization: tma <expired_data>`
    Expected Result: HTTP 401 with "initData expired" message
    Failure Indicators: 200 response, missing expiry check
    Evidence: .sisyphus/evidence/task-9-auth-expiry.txt
  ```

  **Commit**: YES (groups with 10, 11)
  - Message: `feat(core): add auth middleware, Redis, MinIO services`
  - Files: `backend/app/auth.py, backend/app/deps.py`
  - Pre-commit: `cd backend && uv run pytest -x`

---

- [ ] 10. Redis Service Layer

  **What to do**:
  - Create `backend/app/services/redis.py`:
    - `init_redis(url: str) -> redis.asyncio.Redis`: creates connection pool with `decode_responses=True`, `max_connections=20`, `health_check_interval=30`
    - `close_redis(client: redis.asyncio.Redis)`: clean shutdown
    - Cache helpers: `get_cached(redis, key) -> dict | None`, `set_cached(redis, key, data, ttl)`, `invalidate(redis, *keys)`
    - Rate limiter: `RateLimiter` class using Lua script for atomic check-and-increment (sliding window: 100 requests per 60 seconds per user)
  - Integrate into FastAPI lifespan (update `app/main.py`):
    - Startup: `app.state.redis = await init_redis(settings.REDIS_URL)`
    - Shutdown: `await close_redis(app.state.redis)`
  - Add `get_redis` dependency to `deps.py`

  **Must NOT do**:
  - Do NOT use deprecated `aioredis` — use `redis.asyncio` from `redis-py`
  - Do NOT implement pub/sub (not needed in MVP)
  - Do NOT implement session storage (Telegram initData is stateless auth)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Standard Redis patterns, no complex business logic
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (after Wave 1)
  - **Parallel Group**: Wave 2 (with Tasks 7, 8, 9, 11, 12, 13)
  - **Blocks**: Task 17 (catalog caching)
  - **Blocked By**: Tasks 2 (backend scaffolding), 6 (Docker Compose for Redis)

  **References**:

  **External References**:
  - redis-py async: https://redis-py.readthedocs.io/en/stable/examples/asyncio_examples.html
  - `redis.asyncio.ConnectionPool.from_url()` for pool management
  - Lua scripts: `redis.register_script()` for atomic rate limiting

  **Rate limiter Lua script (MUST use for atomicity):**
  ```python
  RATE_LIMIT_SCRIPT = """
  local key = KEYS[1]
  local limit = tonumber(ARGV[1])
  local window = tonumber(ARGV[2])
  local current = redis.call('GET', key)
  if current and tonumber(current) >= limit then return 0 end
  current = redis.call('INCR', key)
  if current == 1 then redis.call('EXPIRE', key, window) end
  return 1
  """
  ```

  **Acceptance Criteria**:
  - [ ] Redis connects successfully at startup
  - [ ] Cache get/set/invalidate functions work
  - [ ] Rate limiter blocks after limit exceeded
  - [ ] Clean shutdown (no connection leaks)
  - [ ] `ruff check . && mypy app/` passes

  **QA Scenarios:**
  ```
  Scenario: Redis cache round-trip
    Tool: Bash
    Preconditions: Docker Compose Redis running, backend running
    Steps:
      1. Run a quick Python script via `uv run python -c` that imports the service, sets a cache key, gets it back
    Expected Result: Set value matches retrieved value
    Failure Indicators: Connection error, None returned
    Evidence: .sisyphus/evidence/task-10-redis-cache.txt
  ```

  **Commit**: YES (groups with 9, 11)
  - Message: `feat(core): add auth middleware, Redis, MinIO services`
  - Files: `backend/app/services/redis.py`
  - Pre-commit: `cd backend && uv run ruff check .`

---

- [ ] 11. MinIO Service Layer

  **What to do**:
  - Create `backend/app/services/storage.py`:
    - `init_minio(endpoint, access_key, secret_key) -> Minio`: creates MinIO client
    - `ensure_buckets(client)`: idempotent bucket creation — `stella-listings` (private), `stella-avatars` (private)
    - `get_upload_url(client, bucket, object_key, expires_hours=2) -> str`: presigned PUT URL for direct browser upload
    - `get_download_url(client, bucket, object_key, expires_hours=1) -> str`: presigned GET URL for viewing
    - `delete_object(client, bucket, object_key)`: delete single object
    - `delete_objects(client, bucket, prefix)`: delete by prefix (for listing deletion)
    - Object key generation: `{bucket}/{user_id}/{uuid}.{ext}` pattern
  - **CRITICAL**: Presigned URLs must use `MINIO_SERVER_URL` (public-facing URL), NOT internal Docker hostname
    - In `init_minio()`: use `settings.MINIO_ENDPOINT` for internal operations
    - For presigned URL generation: client must be configured with `settings.MINIO_SERVER_URL` (public URL)
    - This means two client instances OR re-sign with public URL
  - Integrate into FastAPI lifespan:
    - Startup: init client, ensure buckets
    - Store client in `app.state.minio`
  - Add `get_minio` dependency to `deps.py`

  **Must NOT do**:
  - Do NOT implement file upload endpoint (Task 16 handles the API)
  - Do NOT create public buckets (all access via presigned URLs)
  - Do NOT proxy uploads through FastAPI — presigned URLs only

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: MinIO Docker networking + presigned URLs require careful URL handling
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (after Wave 1)
  - **Parallel Group**: Wave 2 (with Tasks 7, 8, 9, 10, 12, 13)
  - **Blocks**: Tasks 14 (avatar upload), 16 (listing photo upload)
  - **Blocked By**: Tasks 2 (backend scaffolding), 6 (Docker Compose for MinIO)

  **References**:

  **External References**:
  - minio-py API: https://min.io/docs/minio/linux/developers/python/API.html — presigned_put_object, presigned_get_object
  - Docker networking gotcha: set `MINIO_SERVER_URL` env var for presigned URLs to use public-facing hostname

  **WHY Each Reference Matters**:
  - `presigned_put_object()` generates a URL the browser can PUT directly to — bypasses FastAPI completely
  - Without `MINIO_SERVER_URL`, presigned URLs contain internal Docker hostname (`minio:9000`) which is unreachable from browser

  **Acceptance Criteria**:
  - [ ] MinIO client initializes at startup
  - [ ] Buckets `stella-listings` and `stella-avatars` created idempotently
  - [ ] Presigned PUT URL allows upload from external client
  - [ ] Presigned GET URL allows download from browser
  - [ ] Object deletion works
  - [ ] `ruff check . && mypy app/` passes

  **QA Scenarios:**
  ```
  Scenario: Presigned upload URL works
    Tool: Bash
    Preconditions: Docker Compose MinIO running, backend running
    Steps:
      1. Call storage service to get presigned PUT URL for `stella-avatars/test/test.txt`
      2. Upload a test file using `curl -X PUT <presigned_url> -d "test content"`
      3. Get presigned GET URL for same object
      4. Download using `curl <presigned_get_url>`
    Expected Result: Downloaded content matches uploaded content ("test content")
    Failure Indicators: 403 on upload, wrong hostname in URL, file not found
    Evidence: .sisyphus/evidence/task-11-minio-presigned.txt
  ```

  **Commit**: YES (groups with 9, 10)
  - Message: `feat(core): add auth middleware, Redis, MinIO services`
  - Files: `backend/app/services/storage.py`
  - Pre-commit: `cd backend && uv run ruff check .`

---

- [ ] 12. Vue Router + Route Structure + Guards

  **What to do**:
  - Update `frontend/src/router/routes.ts` with full route structure:
    ```
    /                  → SplashScreen (then redirect)
    /catalog           → CatalogPage (main page after splash)
    /catalog/:id       → ListingDetailPage
    /register          → RegistrationPage
    /create-listing    → CreateListingPage (requires registered user)
    /my-listings       → MyListingsPage (requires registered user)
    /profile           → ProfilePage (requires registered user)
    /error             → ErrorPage (no guard)
    ```
  - Update `frontend/src/router/index.ts`:
    - Use `createWebHistory()` (NOT hash mode — CRITICAL for Telegram)
    - `beforeEach` guard: check `meta.requiresTelegram` → verify initData exists, redirect to `/error` if missing
    - `beforeEach` guard: check `meta.requiresRegistration` → verify user is_registered in Pinia store, redirect to `/register` if not
    - `afterEach` hook: manage Telegram BackButton — show on all routes except `/catalog`, bind `onClick` to `router.back()`
  - Add route meta types in `frontend/src/types/router.d.ts`:
    ```typescript
    declare module 'vue-router' {
      interface RouteMeta {
        requiresTelegram?: boolean
        requiresRegistration?: boolean
      }
    }
    ```

  **Must NOT do**:
  - Do NOT use `createWebHashHistory()` — it destroys Telegram launch params
  - Do NOT implement page components (Tasks 19-25)
  - Do NOT implement splash screen logic (Task 19)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Route config + guards, no complex UI logic
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (after Tasks 3, 7)
  - **Parallel Group**: Wave 2 (with Tasks 7, 8, 9, 10, 11, 13)
  - **Blocks**: Tasks 19-25 (all UI pages)
  - **Blocked By**: Tasks 3 (frontend scaffolding), 7 (Telegram SDK init)

  **References**:

  **External References**:
  - Vue Router: https://router.vuejs.org/guide/advanced/navigation-guards.html — `beforeEach`, `afterEach`
  - Vue Router meta: https://router.vuejs.org/guide/advanced/meta.html — type-safe route meta
  - Telegram BackButton: integrate via `backButton.show()`, `backButton.hide()`, `backButton.onClick()`

  **WHY Each Reference Matters**:
  - `createWebHistory()` is MANDATORY — Telegram uses URL hash for launch params (tgWebAppData)
  - BackButton sync with Vue Router provides native Telegram UX — users expect hardware-like back navigation

  **Acceptance Criteria**:
  - [ ] Router uses `createWebHistory()` (grep for `createWebHashHistory` must find 0 results)
  - [ ] All routes defined with correct paths and meta
  - [ ] beforeEach guards check requiresTelegram and requiresRegistration
  - [ ] afterEach manages Telegram BackButton visibility
  - [ ] `npx vue-tsc --noEmit` passes

  **QA Scenarios:**
  ```
  Scenario: Hash mode not used
    Tool: Bash
    Steps:
      1. Run `grep -r "createWebHashHistory" frontend/src/`
    Expected Result: No matches found (exit code 1)
    Failure Indicators: Any match found
    Evidence: .sisyphus/evidence/task-12-no-hash-mode.txt
  ```

  **Commit**: YES (groups with 13)
  - Message: `feat(frontend): add router, guards, Pinia stores`
  - Files: `frontend/src/router/**`
  - Pre-commit: `cd frontend && npx vue-tsc --noEmit`

---

- [ ] 13. Pinia Stores Setup

  **What to do**:
  - Create `frontend/src/stores/telegram.ts` (global Telegram state):
    - Composition API (Setup Store) pattern with `defineStore`
    - State: `initDataRaw` (string), `user` (TelegramUser | null), `isReady` (boolean)
    - Getters: `isAuthenticated` (computed: has initData + user)
    - Actions: `initialize()` — reads from SDK, sets state
  - Create `frontend/src/stores/user.ts` (app user profile):
    - State: `profile` (User | null), `isRegistered` (boolean), `isLoading` (boolean)
    - Actions: `fetchProfile()`, `register(data)`, `updateProfile(data)`
    - Uses API client from `@/api/users`
  - Create `frontend/src/stores/catalog.ts` (catalog state):
    - State: `listings` (Listing[]), `categories` (Category[]), `loading`, `error`, `currentPage`, `totalPages`, `selectedCity`, `selectedCategory`
    - Actions: `loadListings(filters)`, `loadCategories()`
    - Uses API client from `@/api/listings` and `@/api/categories`
  - Create `frontend/src/stores/listing.ts` (single listing + create flow):
    - State: `currentListing` (Listing | null), `myListings` (Listing[]), `loading`
    - Actions: `fetchListing(id)`, `createListing(data)`, `fetchMyListings()`

  **Must NOT do**:
  - Do NOT implement API calls in stores yet (stubs from Task 5 return empty data)
  - Do NOT use Options API stores (use Composition API / Setup Stores)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Standard Pinia store patterns, no business logic
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (after Tasks 3, 5, 7)
  - **Parallel Group**: Wave 2 (with Tasks 7, 8, 9, 10, 11, 12)
  - **Blocks**: Tasks 20-25 (all UI pages except splash)
  - **Blocked By**: Tasks 3 (frontend scaffolding), 5 (TypeScript types), 7 (Telegram SDK)

  **References**:

  **External References**:
  - Pinia Setup Stores: https://pinia.vuejs.org/core-concepts/#setup-stores — `defineStore('id', () => { ... })`
  - Pinia TypeScript: https://pinia.vuejs.org/core-concepts/#typescript

  **WHY Each Reference Matters**:
  - Setup Stores give full TypeScript inference without extra type annotations
  - Store organization: global stores in `stores/`, feature stores colocated with features

  **Acceptance Criteria**:
  - [ ] 4 stores created: telegram, user, catalog, listing
  - [ ] All stores use Composition API (Setup Store) pattern
  - [ ] All stores properly typed (no `any`)
  - [ ] `npx vue-tsc --noEmit` passes

  **QA Scenarios:**
  ```
  Scenario: Stores type-check correctly
    Tool: Bash
    Steps:
      1. Run `cd frontend && npx vue-tsc --noEmit`
    Expected Result: Exit code 0
    Failure Indicators: Type errors in store files
    Evidence: .sisyphus/evidence/task-13-stores-tsc.txt
  ```

  **Commit**: YES (groups with 12)
  - Message: `feat(frontend): add router, guards, Pinia stores`
  - Files: `frontend/src/stores/**`
  - Pre-commit: `cd frontend && npx vue-tsc --noEmit`

---

- [ ] 14. User Registration + Profile API

  **What to do**:
  - Create `backend/app/api/users.py` APIRouter with prefix `/api/users`:
    - `POST /api/users/register` — Register user: accepts `{first_name, last_name, phone, city, latitude?, longitude?}`. Sets `is_registered=True`. Requires `get_current_user` dependency (user auto-created by auth). Returns full User profile.
    - `GET /api/users/profile` — Get current user profile. Requires `get_current_user`.
    - `PATCH /api/users/profile` — Update profile fields (name, phone, city, coordinates). Requires `require_registered_user`.
    - `POST /api/users/avatar` — Returns MinIO presigned PUT URL for avatar upload. Client uploads directly. Then `PATCH /api/users/profile` with `avatar_url` to save the object key.
    - `GET /api/users/{telegram_id}/public` — Public seller profile (name, city, avatar_url, created_at). NO phone. For listing detail page.
  - Create `backend/app/schemas/user.py` Pydantic schemas:
    - `UserRegistration(first_name, last_name?, phone, city, latitude?, longitude?)`
    - `UserUpdate(first_name?, last_name?, phone?, city?, latitude?, longitude?, avatar_url?)`
    - `UserProfile` (full profile, for authenticated user)
    - `UserPublic` (public info only, for seller display)
    - `AvatarUploadResponse(upload_url: str, object_key: str)`
  - Phone validation: Russian format (+7XXXXXXXXXX) or international
  - Telegram request_contact integration: accept phone from Telegram `requestContact()` via a dedicated endpoint or as part of registration

  **Must NOT do**:
  - Do NOT expose phone number in public profile
  - Do NOT implement email field (not in scope)
  - Do NOT implement user deletion (not in MVP)

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: User registration is a core flow with validation, file upload coordination, and security concerns
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (after Wave 2)
  - **Parallel Group**: Wave 3 (with Tasks 15, 16, 17, 18)
  - **Blocks**: Tasks 20 (registration UI), 24 (profile UI)
  - **Blocked By**: Tasks 4 (models), 9 (auth), 11 (MinIO)

  **References**:

  **External References**:
  - FastAPI request body: https://fastapi.tiangolo.com/tutorial/body/
  - Pydantic validation: https://docs.pydantic.dev/latest/concepts/validators/ — phone format validation
  - MinIO presigned PUT: `minio_client.presigned_put_object(bucket, key, timedelta(hours=2))`

  **Acceptance Criteria**:
  - [ ] All 5 endpoints functional and returning correct response schemas
  - [ ] Registration validates required fields and sets `is_registered=True`
  - [ ] Avatar endpoint returns valid presigned PUT URL
  - [ ] Public profile does NOT expose phone number
  - [ ] `pytest` passes for user endpoints

  **QA Scenarios:**
  ```
  Scenario: User registration happy path
    Tool: Bash (curl)
    Preconditions: Backend running, valid initData
    Steps:
      1. GET /api/users/profile → verify is_registered=false (new user)
      2. POST /api/users/register with {first_name: "Test", phone: "+79001234567", city: "Москва"}
      3. GET /api/users/profile → verify is_registered=true, city="Москва"
    Expected Result: User registered, profile shows updated data
    Evidence: .sisyphus/evidence/task-14-register.txt

  Scenario: Public profile hides phone
    Tool: Bash (curl)
    Steps:
      1. GET /api/users/{telegram_id}/public
      2. Verify response does NOT contain "phone" field
    Expected Result: Response has name, city, avatar_url but NO phone
    Evidence: .sisyphus/evidence/task-14-public-profile.txt
  ```

  **Commit**: YES (groups with 15, 16, 17)
  - Message: `feat(api): add user, category, listing, catalog endpoints`
  - Files: `backend/app/api/users.py, backend/app/schemas/user.py`
  - Pre-commit: `cd backend && uv run pytest -x`

---

- [ ] 15. Category API

  **What to do**:
  - Create `backend/app/api/categories.py` APIRouter with prefix `/api/categories`:
    - `GET /api/categories` — List all approved categories (is_approved=True). Cached in Redis (5 min TTL). Returns list with id, name, slug, icon.
    - `POST /api/categories/propose` — Seller proposes new category. Creates with `is_approved=False`, `created_by=current_user.id`. Requires `require_registered_user`.
    - `PATCH /api/categories/{id}/approve` — Admin approves proposed category. Sets `is_approved=True`. Requires `require_admin`.
  - Create `backend/app/schemas/category.py` Pydantic schemas:
    - `CategoryResponse(id, name, slug, icon)`
    - `CategoryPropose(name: str)` — auto-generates slug from name
  - Slug generation: transliterate Russian name to URL-safe slug (e.g., "Электроника" → "elektronika")
  - Redis caching: invalidate category cache on approve/propose

  **Must NOT do**:
  - Do NOT implement category deletion
  - Do NOT implement category editing (beyond approve)
  - Do NOT implement subcategories/hierarchy (flat list only)

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Standard CRUD with caching and admin auth
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (after Wave 2)
  - **Parallel Group**: Wave 3 (with Tasks 14, 16, 17, 18)
  - **Blocks**: Tasks 21 (catalog UI), 23 (create listing UI)
  - **Blocked By**: Tasks 4 (models), 9 (auth)

  **References**:

  **External References**:
  - python-slugify or transliterate: for Russian → Latin slug generation
  - Redis caching pattern: `get_cached(redis, "categories")` → miss → query DB → `set_cached(redis, "categories", data, ttl=300)`

  **Acceptance Criteria**:
  - [ ] GET /api/categories returns only approved categories
  - [ ] POST /api/categories/propose creates unapproved category
  - [ ] PATCH /api/categories/{id}/approve requires admin
  - [ ] Categories cached in Redis with 5-min TTL
  - [ ] Slug auto-generated from name

  **QA Scenarios:**
  ```
  Scenario: Category list returns only approved
    Tool: Bash (curl)
    Steps:
      1. GET /api/categories
      2. Verify all returned categories have is_approved=true
      3. Propose a new category
      4. GET /api/categories → verify proposed category NOT in list
      5. Approve the category (as admin)
      6. GET /api/categories → verify now in list
    Expected Result: Only approved categories visible in public list
    Evidence: .sisyphus/evidence/task-15-categories.txt
  ```

  **Commit**: YES (groups with 14, 16, 17)
  - Message: `feat(api): add user, category, listing, catalog endpoints`
  - Files: `backend/app/api/categories.py, backend/app/schemas/category.py`
  - Pre-commit: `cd backend && uv run pytest -x`

---

- [ ] 16. Listing CRUD + Photo Upload API

  **What to do**:
  - Create `backend/app/api/listings.py` APIRouter with prefix `/api/listings`:
    - `POST /api/listings` — Create listing (title, description, price, currency, category_id). Status=pending. Requires `require_registered_user`. Returns listing with id.
    - `GET /api/listings/{id}` — Get single listing. Includes seller public info, photos with presigned GET URLs, category. Only show approved listings to non-owners.
    - `PATCH /api/listings/{id}` — Update listing. Only by owner. Resets status to pending if content changed.
    - `DELETE /api/listings/{id}` — Delete listing + all photos from MinIO. Only by owner.
    - `GET /api/listings/my` — Current user's listings (all statuses). Requires `require_registered_user`.
    - `POST /api/listings/{id}/photos/upload-url` — Returns presigned PUT URL for photo upload. Max 5 photos per listing. Returns `{upload_url, object_key, position}`.
    - `POST /api/listings/{id}/photos` — Confirm photo upload: save object_key + position to DB. Called after client successfully PUT to presigned URL.
    - `DELETE /api/listings/{id}/photos/{photo_id}` — Delete single photo.
  - Create `backend/app/schemas/listing.py` Pydantic schemas:
    - `ListingCreate(title, description, price, currency?, category_id)`
    - `ListingUpdate(title?, description?, price?, currency?, category_id?)`
    - `ListingResponse(id, title, description, price, currency, status, city, category, seller, photos, created_at)`
    - `ListingPhotoResponse(id, url, position)` — url is presigned GET URL
    - `PhotoUploadResponse(upload_url, object_key, position)`
  - Photo upload flow:
    1. Client calls `POST /api/listings/{id}/photos/upload-url`
    2. Backend generates MinIO presigned PUT URL + object_key
    3. Client uploads file directly to MinIO via PUT
    4. Client calls `POST /api/listings/{id}/photos` with object_key to confirm
  - Listing's city is auto-set from seller's profile city

  **Must NOT do**:
  - Do NOT proxy file uploads through FastAPI
  - Do NOT allow more than 5 photos per listing
  - Do NOT implement search/full-text-search
  - Do NOT implement favorites/bookmarks

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Complex CRUD with file upload coordination, ownership checks, status management
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (after Wave 2)
  - **Parallel Group**: Wave 3 (with Tasks 14, 15, 17, 18)
  - **Blocks**: Tasks 18 (moderation), 23 (create listing UI), 25 (my listings UI)
  - **Blocked By**: Tasks 4 (models), 9 (auth), 11 (MinIO)

  **References**:

  **External References**:
  - MinIO presigned PUT: `presigned_put_object(bucket, key, timedelta(hours=2))`
  - SQLAlchemy relationship cascade: `cascade='all, delete-orphan'` on Listing.photos

  **Acceptance Criteria**:
  - [ ] All 8 endpoints functional
  - [ ] Photo upload flow works: get URL → upload → confirm
  - [ ] Max 5 photos enforced (6th upload returns 400)
  - [ ] Only owner can update/delete listings
  - [ ] Non-owners see only approved listings
  - [ ] Listing deletion cascades to photos (DB + MinIO)

  **QA Scenarios:**
  ```
  Scenario: Create listing with photos
    Tool: Bash (curl)
    Steps:
      1. POST /api/listings → create listing, get listing_id
      2. POST /api/listings/{id}/photos/upload-url → get presigned URL
      3. PUT file to presigned URL
      4. POST /api/listings/{id}/photos with object_key
      5. GET /api/listings/{id} → verify photo URL present
    Expected Result: Listing created with photo, GET returns presigned download URL
    Evidence: .sisyphus/evidence/task-16-listing-photos.txt

  Scenario: Max 5 photos enforced
    Tool: Bash (curl)
    Steps:
      1. Upload 5 photos to a listing (repeat steps 2-4 above 5 times)
      2. Try to get 6th upload URL
    Expected Result: 6th request returns HTTP 400 with error message
    Evidence: .sisyphus/evidence/task-16-max-photos.txt
  ```

  **Commit**: YES (groups with 14, 15, 17)
  - Message: `feat(api): add user, category, listing, catalog endpoints`
  - Files: `backend/app/api/listings.py, backend/app/schemas/listing.py`
  - Pre-commit: `cd backend && uv run pytest -x`

---

- [ ] 17. Catalog API + Pagination

  **What to do**:
  - Create `backend/app/api/catalog.py` APIRouter with prefix `/api/catalog`:
    - `GET /api/catalog` — List approved listings with filters:
      - `?city=<city>` — filter by city (exact match, case-insensitive)
      - `?category_id=<uuid>` — filter by category
      - `?page=1&per_page=20` — cursor-based or offset pagination
      - `?sort=recent|price_asc|price_desc` — sorting
    - Returns `PaginatedResponse<ListingResponse>` with total count
    - Only shows `status=approved` listings
    - Eager-loads: first photo (for thumbnail), category name, seller basic info
    - Redis caching for popular queries (city + category combo, 2-min TTL)
  - Optimize queries:
    - Indexes: `(status, city)`, `(status, category_id)`, `(status, created_at DESC)`
    - Use SQLAlchemy `selectinload` for photos relationship
  - Add database indexes via Alembic migration

  **Must NOT do**:
  - Do NOT implement text search
  - Do NOT implement location-based radius search (only exact city match)
  - Do NOT implement infinite scroll backend (standard pagination)

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Query optimization, caching, pagination
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (after Wave 2)
  - **Parallel Group**: Wave 3 (with Tasks 14, 15, 16, 18)
  - **Blocks**: Tasks 21 (catalog UI), 22 (listing detail UI)
  - **Blocked By**: Tasks 4 (models), 9 (auth), 10 (Redis for caching)

  **References**:

  **External References**:
  - SQLAlchemy pagination: `select().offset().limit()` with count query
  - SQLAlchemy eager loading: `selectinload(Listing.photos)`, `joinedload(Listing.category)`
  - Composite indexes: https://docs.sqlalchemy.org/en/20/orm/mapped_sql_expr.html

  **Acceptance Criteria**:
  - [ ] GET /api/catalog returns paginated approved listings
  - [ ] City filter works (case-insensitive)
  - [ ] Category filter works
  - [ ] Sorting by recent/price works
  - [ ] Response includes first photo URL, category name, seller info
  - [ ] Popular queries cached in Redis

  **QA Scenarios:**
  ```
  Scenario: Catalog filters by city
    Tool: Bash (curl)
    Steps:
      1. Create listings in different cities (via direct DB or API)
      2. GET /api/catalog?city=Москва
      3. Verify all returned listings have city=Москва
    Expected Result: Only listings from Москва returned
    Evidence: .sisyphus/evidence/task-17-catalog-city.txt

  Scenario: Catalog shows only approved listings
    Tool: Bash (curl)
    Steps:
      1. Create a listing (status=pending)
      2. GET /api/catalog → verify listing NOT in results
      3. Approve listing (via bot command or direct DB)
      4. GET /api/catalog → verify listing IS in results
    Expected Result: Pending listings invisible in catalog
    Evidence: .sisyphus/evidence/task-17-catalog-approved.txt
  ```

  **Commit**: YES (groups with 14, 15, 16)
  - Message: `feat(api): add user, category, listing, catalog endpoints`
  - Files: `backend/app/api/catalog.py`
  - Pre-commit: `cd backend && uv run pytest -x`

---

- [ ] 18. Bot Moderation Commands

  **What to do**:
  - Add moderation handlers to `backend/app/bot/handlers.py`:
    - `/pending` — Lists pending listings (title, seller, created_at). Only for admin Telegram IDs.
    - `/approve <listing_id>` — Sets listing status to `approved`. Sends notification to seller: "✅ Ваше объявление '{title}' одобрено!"
    - `/reject <listing_id> [reason]` — Sets listing status to `rejected`. Sends notification to seller: "❌ Ваше объявление '{title}' отклонено. Причина: {reason}"
    - `/stats` — Basic stats: total users, total listings (by status), total categories. Admin only.
  - Admin check: compare `message.from_user.id` against `settings.ADMIN_TELEGRAM_IDS` list
  - When new listing is created (in listing API), send notification to all admins:
    "📦 Новое объявление: '{title}' от @{username}" with inline keyboard [Approve | Reject]
  - Inline keyboard callback handlers for approve/reject from notification

  **Must NOT do**:
  - Do NOT implement full admin panel (Directus is deferred)
  - Do NOT implement user banning
  - Do NOT implement listing editing via bot

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Bot handlers with DB access and inline keyboards
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (after Task 8 + 16)
  - **Parallel Group**: Wave 3 (with Tasks 14, 15, 16, 17)
  - **Blocks**: None
  - **Blocked By**: Tasks 8 (bot setup), 16 (listing API — needs listing model operations)

  **References**:

  **External References**:
  - aiogram command handlers: `@router.message(Command('approve'))`
  - aiogram callback queries: `@router.callback_query(F.data.startswith('approve:'))`
  - aiogram inline keyboards: `InlineKeyboardBuilder`

  **Acceptance Criteria**:
  - [ ] `/pending` shows pending listings for admin
  - [ ] `/approve <id>` changes status and notifies seller
  - [ ] `/reject <id> <reason>` changes status and notifies seller
  - [ ] Non-admin users get "Access denied" on admin commands
  - [ ] New listing creation triggers admin notification with inline keyboard

  **QA Scenarios:**
  ```
  Scenario: Admin approve flow via bot
    Tool: Bash (curl to webhook)
    Steps:
      1. Create a listing via API (status=pending)
      2. Simulate `/approve <listing_id>` command via webhook (admin user_id)
      3. Verify listing status changed to approved in DB
    Expected Result: Listing status is 'approved'
    Evidence: .sisyphus/evidence/task-18-approve.txt

  Scenario: Non-admin rejected from moderation
    Tool: Bash (curl to webhook)
    Steps:
      1. Simulate `/pending` command via webhook (non-admin user_id)
    Expected Result: Bot responds with access denied message
    Evidence: .sisyphus/evidence/task-18-admin-check.txt
  ```

  **Commit**: YES
  - Message: `feat(bot): add moderation commands (approve/reject)`
  - Files: `backend/app/bot/handlers.py`
  - Pre-commit: `cd backend && uv run pytest -x`

---

- [ ] 19. Splash Screen

  **What to do**:
  - Create `frontend/src/features/splash/SplashScreen.vue`:
    - Full-screen overlay with Stella branding
    - Animation: logo appears with fade-in + subtle scale (0.8→1.0), slogan fades in below with 0.5s delay
    - Logo: "⭐ Stella" (star emoji or Lucide Star icon + text) in large bold font
    - Slogan: "Найдёшь всё, что нужно!" in smaller text below, lighter weight
    - Background: gradient using Telegram theme colors (--tg-theme-bg-color to slightly lighter)
    - Duration: 3 seconds total, then auto-redirect
    - Use CSS animations (@keyframes), NOT JavaScript timers for animation
    - Use `setTimeout` or `onMounted` + timer for the 3s redirect
  - After 3 seconds:
    - If user is registered → redirect to `/catalog`
    - If user is NOT registered → redirect to `/catalog` (they see unregistered view with prompt)
  - Splash shows ONLY on first app open (use `sessionStorage` flag `stella_splash_shown`)
  - Design: modern, clean, centered content, subtle animation — NOT flashy or over-animated

  **Must NOT do**:
  - Do NOT use heavy animation libraries (no Lottie, no GSAP)
  - Do NOT block longer than 3 seconds
  - Do NOT show splash on subsequent navigation (only on app launch)

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
    - Reason: Animation, branding, visual design
  - **Skills**: [`frontend-ui-ux`]
    - `frontend-ui-ux`: For crafting polished splash animation and brand presentation

  **Parallelization**:
  - **Can Run In Parallel**: YES (after Wave 2)
  - **Parallel Group**: Wave 4 (with Tasks 20-25)
  - **Blocks**: None
  - **Blocked By**: Tasks 7 (Telegram SDK), 12 (router)

  **References**:

  **External References**:
  - CSS @keyframes: `opacity 0→1`, `transform: scale(0.8)→scale(1)` — 60fps GPU-accelerated
  - Telegram theme CSS vars: `--tg-theme-bg-color`, `--tg-theme-text-color`, `--tg-theme-hint-color`

  **Acceptance Criteria**:
  - [ ] Splash screen shows on first app open for ~3 seconds
  - [ ] Logo + slogan animate in smoothly
  - [ ] Redirects to /catalog after 3 seconds
  - [ ] Does NOT show on page refresh / subsequent navigation (sessionStorage flag)
  - [ ] Uses Telegram theme colors

  **QA Scenarios:**
  ```
  Scenario: Splash screen displays and redirects
    Tool: Playwright
    Steps:
      1. Navigate to http://localhost:5173/
      2. Assert `.splash-screen` element is visible
      3. Assert text "Stella" is visible
      4. Assert text "Найдёшь всё, что нужно!" is visible
      5. Wait 3.5 seconds
      6. Assert current URL contains /catalog
    Expected Result: Splash shows branding, then redirects to catalog
    Evidence: .sisyphus/evidence/task-19-splash.png

  Scenario: Splash skipped on return visit
    Tool: Playwright
    Steps:
      1. Navigate to http://localhost:5173/ (first visit → splash shown)
      2. Wait for redirect to /catalog
      3. Navigate to http://localhost:5173/ again (same session)
      4. Assert immediately on /catalog (no splash)
    Expected Result: Splash not shown on second visit within same session
    Evidence: .sisyphus/evidence/task-19-splash-skip.png
  ```

  **Commit**: YES (groups with 20-25)
  - Message: `feat(ui): add all frontend pages and components`
  - Files: `frontend/src/features/splash/**`
  - Pre-commit: `cd frontend && npx vue-tsc --noEmit`

---

- [ ] 20. Registration Flow UI

  **What to do**:
  - Create `frontend/src/features/registration/` module:
    - `RegistrationPage.vue` — multi-step registration form:
      - Step 1: Name — `first_name` (pre-filled from Telegram), `last_name` (pre-filled, optional). Editable.
      - Step 2: Phone — Option A: "Share from Telegram" button (uses Telegram requestContact). Option B: Manual input field with +7 mask.
      - Step 3: City — GPS auto-detect button ("📍 Определить автоматически") + manual text input. Reverse geocoding GPS coordinates to city name.
      - Step 4: Avatar — Shows Telegram avatar (pre-loaded), option to upload custom. Presigned URL upload to MinIO.
      - Final: Submit → `POST /api/users/register`
    - `RegistrationStep.vue` — reusable step wrapper with progress indicator (dots)
  - Design: Full-screen steps, one field per step (mobile-first), large touch targets, smooth transitions between steps
  - Progress indicator: 4 dots at top showing current step
  - Back button: Use Telegram BackButton to go to previous step
  - GPS: Use browser `navigator.geolocation.getCurrentPosition()`. If denied, show manual input.
  - Reverse geocoding: Use free API (e.g., Nominatim/OpenStreetMap) or simple coordinates → city mapping

  **Must NOT do**:
  - Do NOT use Google Maps API (paid)
  - Do NOT require GPS (always offer manual input)
  - Do NOT skip validation (name required, phone required, city required)

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
    - Reason: Multi-step form with animations, GPS integration, file upload UX
  - **Skills**: [`frontend-ui-ux`]
    - `frontend-ui-ux`: For polished step-by-step registration flow design

  **Parallelization**:
  - **Can Run In Parallel**: YES (after Wave 3)
  - **Parallel Group**: Wave 4 (with Tasks 19, 21-25)
  - **Blocks**: None
  - **Blocked By**: Tasks 12 (router), 13 (stores), 14 (user API)

  **Acceptance Criteria**:
  - [ ] 4-step registration flow functional
  - [ ] Pre-fills name/surname from Telegram data
  - [ ] Phone input accepts manual input and Telegram share
  - [ ] GPS auto-detect works with fallback to manual input
  - [ ] Avatar upload via presigned URL
  - [ ] Registration API called on submit, redirects to /catalog

  **QA Scenarios:**
  ```
  Scenario: Complete registration flow
    Tool: Playwright
    Steps:
      1. Navigate to /register
      2. Assert Step 1 visible with pre-filled name from Telegram mock
      3. Click "Next"
      4. Enter phone "+79001234567" in input
      5. Click "Next"
      6. Enter city "Москва" in input
      7. Click "Next"
      8. Skip avatar (keep Telegram default)
      9. Click "Register" / "Зарегистрироваться"
      10. Assert redirected to /catalog
    Expected Result: Full registration completes, user redirected to catalog
    Evidence: .sisyphus/evidence/task-20-registration.png
  ```

  **Commit**: YES (groups with 19, 21-25)
  - Message: `feat(ui): add all frontend pages and components`
  - Files: `frontend/src/features/registration/**`
  - Pre-commit: `cd frontend && npx vue-tsc --noEmit`

---

- [ ] 21. Catalog Page UI

  **What to do**:
  - Create `frontend/src/features/catalog/` module:
    - `CatalogPage.vue` — main page of the app:
      - Top bar: City name (clickable to change) + optional registration prompt for unregistered users
      - Category filter: Horizontal scrollable chip/pill list. First item: "Все" (selected by default). Each category shows icon (Lucide) + name.
      - Listing grid: 2-column grid on mobile. Each card shows: first photo (thumbnail), title, price, city.
      - Pull-to-refresh: reload catalog
      - Load more: button at bottom or infinite scroll
      - Empty state: Illustration + "Пока нет объявлений" message
    - `ListingCard.vue` — compact card for grid:
      - Photo thumbnail (first photo or placeholder)
      - Title (truncated to 2 lines)
      - Price in bold (formatted: "1 500 ₽")
      - City name in hint color
    - `CategoryFilter.vue` — horizontal scrollable categories:
      - Chips with icon + name
      - Active chip highlighted
      - Scroll horizontally on overflow
  - For UNREGISTERED users: show banner at top "📍 Укажите город, чтобы видеть товары рядом" with "Зарегистрироваться" button
  - For REGISTERED users: auto-filter by user's city, show city in top bar
  - Connect to catalog Pinia store and API
  - Design: Modern, clean card design with subtle shadows, rounded corners (12-16px), volumetric feel

  **Must NOT do**:
  - Do NOT implement search bar (deferred)
  - Do NOT implement favorites/bookmark button on cards
  - Do NOT implement infinite scroll (use "Load more" button — simpler for MVP)

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
    - Reason: Core UI page with grid layout, cards, horizontal scroll filter
  - **Skills**: [`frontend-ui-ux`]
    - `frontend-ui-ux`: For polished card design and responsive layout

  **Parallelization**:
  - **Can Run In Parallel**: YES (after Wave 3)
  - **Parallel Group**: Wave 4 (with Tasks 19, 20, 22-25)
  - **Blocks**: None
  - **Blocked By**: Tasks 12 (router), 13 (stores), 17 (catalog API)

  **Acceptance Criteria**:
  - [ ] Catalog shows approved listings in 2-column grid
  - [ ] Category filter chips work (tap to filter)
  - [ ] Registered users see city-filtered listings
  - [ ] Unregistered users see all listings + registration banner
  - [ ] Empty state displayed when no listings
  - [ ] Listing cards show photo, title, price, city
  - [ ] Price formatted with space separators ("1 500 ₽")

  **QA Scenarios:**
  ```
  Scenario: Catalog displays listings
    Tool: Playwright
    Steps:
      1. Navigate to /catalog (with seeded data)
      2. Assert `.listing-card` elements exist (count > 0)
      3. Assert each card has `.listing-card__photo`, `.listing-card__title`, `.listing-card__price`
      4. Assert category filter chips visible
      5. Click a category chip
      6. Assert listings filtered (count changes or stays same)
    Expected Result: Catalog shows listings with filtering
    Evidence: .sisyphus/evidence/task-21-catalog.png

  Scenario: Empty state when no listings
    Tool: Playwright
    Steps:
      1. Navigate to /catalog?city=NonexistentCity (or clear DB)
      2. Assert empty state message visible
    Expected Result: Empty state illustration and message shown
    Evidence: .sisyphus/evidence/task-21-empty-state.png
  ```

  **Commit**: YES (groups with 19, 20, 22-25)
  - Message: `feat(ui): add all frontend pages and components`
  - Files: `frontend/src/features/catalog/**`
  - Pre-commit: `cd frontend && npx vue-tsc --noEmit`

---

- [ ] 22. Listing Detail Page + Seller Contact

  **What to do**:
  - Create `frontend/src/features/listing/` module:
    - `ListingDetailPage.vue` — full listing view:
      - Photo carousel/swiper at top (swipeable, dots indicator, full-width)
      - Title (large, bold)
      - Price (large, accent color, formatted)
      - Status badge (visible only to listing owner: pending/approved/rejected)
      - Description (full text, multi-line)
      - Category chip
      - City with map pin icon
      - Seller info section: avatar, name, "Member since" date
      - **CTA button at bottom**: "Написать продавцу" — opens Telegram chat with seller
    - `PhotoCarousel.vue` — swipeable photo gallery:
      - Touch swipe between photos
      - Dot indicators below
      - Placeholder for listings without photos
    - `SellerContactButton.vue` — the "Write in Telegram" button:
      - Primary action: `tg://user?id={seller_telegram_id}` deep link (works even without @username)
      - Fallback: if seller has @username, use `https://t.me/{username}`
      - Haptic feedback on tap: `hapticFeedback.impactOccurred('medium')`
      - Fixed at bottom of screen (sticky)
  - Design: clean product page, large photos, clear price, prominent CTA button
  - Use Telegram haptic feedback for button taps

  **Must NOT do**:
  - Do NOT show seller phone number (privacy)
  - Do NOT implement in-app chat
  - Do NOT implement sharing/forwarding

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
    - Reason: Photo carousel, product page layout, CTA design
  - **Skills**: [`frontend-ui-ux`]
    - `frontend-ui-ux`: For polished product page with photo swiper and contact CTA

  **Parallelization**:
  - **Can Run In Parallel**: YES (after Wave 3)
  - **Parallel Group**: Wave 4 (with Tasks 19-21, 23-25)
  - **Blocks**: None
  - **Blocked By**: Tasks 12 (router), 13 (stores), 17 (catalog API for listing detail)

  **Acceptance Criteria**:
  - [ ] Photos display in swipeable carousel with dot indicators
  - [ ] Title, price, description, category, city all visible
  - [ ] Seller info section shows avatar + name
  - [ ] Contact button at bottom with Telegram deep link
  - [ ] Haptic feedback on button tap
  - [ ] Owner sees status badge

  **QA Scenarios:**
  ```
  Scenario: Listing detail displays correctly
    Tool: Playwright
    Steps:
      1. Navigate to /catalog/:id (with seeded listing data)
      2. Assert `.photo-carousel` visible
      3. Assert `.listing-title` contains listing title text
      4. Assert `.listing-price` contains formatted price
      5. Assert `.seller-contact-button` visible at bottom
      6. Assert contact button href starts with `tg://user?id=` or `https://t.me/`
    Expected Result: Full listing detail displayed with contact button
    Evidence: .sisyphus/evidence/task-22-listing-detail.png
  ```

  **Commit**: YES (groups with 19-21, 23-25)
  - Message: `feat(ui): add all frontend pages and components`
  - Files: `frontend/src/features/listing/**`
  - Pre-commit: `cd frontend && npx vue-tsc --noEmit`

---

- [ ] 23. Create Listing Page UI

  **What to do**:
  - Create `frontend/src/features/create-listing/` module:
    - `CreateListingPage.vue` — listing creation form:
      - Photo upload section (top): Grid of 5 slots. Tap empty slot to open file picker. Show uploaded photo preview. Drag to reorder (optional for MVP — can skip). Delete photo button (X) on each.
      - Title input (required, max 100 chars)
      - Description textarea (required, max 2000 chars, auto-grow)
      - Price input (number, with ₽ suffix)
      - Category selector: dropdown or bottom sheet with category list + icons
      - Submit button: "Опубликовать" — calls `POST /api/listings`, then uploads photos via presigned URLs, then confirms each photo
    - `PhotoUploadGrid.vue` — 5-slot grid for photos:
      - Upload flow: tap slot → file picker → compress image client-side → get presigned URL → PUT to MinIO → confirm via API
      - Progress indicator during upload
      - Preview thumbnail after upload
    - `CategorySelector.vue` — category picker:
      - List of approved categories with icons
      - "Propose new category" option at bottom
  - Client-side image compression before upload (resize to max 1200px width, JPEG 80% quality)
  - Form validation: all required fields, price > 0, at least 1 photo
  - After successful creation: show success message, redirect to /my-listings

  **Must NOT do**:
  - Do NOT implement drag-to-reorder photos (nice-to-have, not MVP)
  - Do NOT implement image cropping
  - Do NOT allow video uploads

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
    - Reason: Complex form with file upload, image compression, multi-step submit
  - **Skills**: [`frontend-ui-ux`]
    - `frontend-ui-ux`: For polished form design with photo upload UX

  **Parallelization**:
  - **Can Run In Parallel**: YES (after Wave 3)
  - **Parallel Group**: Wave 4 (with Tasks 19-22, 24, 25)
  - **Blocks**: None
  - **Blocked By**: Tasks 12 (router), 13 (stores), 16 (listing API)

  **Acceptance Criteria**:
  - [ ] Form with all fields: photos, title, description, price, category
  - [ ] Photo upload via presigned URL (max 5)
  - [ ] Client-side image compression
  - [ ] Category selector shows approved categories
  - [ ] Form validation (required fields, price > 0, at least 1 photo)
  - [ ] Submit creates listing + uploads photos
  - [ ] Success message + redirect to /my-listings

  **QA Scenarios:**
  ```
  Scenario: Create listing with photo
    Tool: Playwright
    Steps:
      1. Navigate to /create-listing (registered user)
      2. Upload a test image to first photo slot
      3. Fill title: "Test Listing"
      4. Fill description: "Test description for listing"
      5. Fill price: "1500"
      6. Select first category
      7. Click "Опубликовать"
      8. Assert redirect to /my-listings
      9. Assert new listing visible with status "pending"
    Expected Result: Listing created with photo, shown in my listings as pending
    Evidence: .sisyphus/evidence/task-23-create-listing.png
  ```

  **Commit**: YES (groups with 19-22, 24, 25)
  - Message: `feat(ui): add all frontend pages and components`
  - Files: `frontend/src/features/create-listing/**`
  - Pre-commit: `cd frontend && npx vue-tsc --noEmit`

---

- [ ] 24. User Profile Page UI

  **What to do**:
  - Create `frontend/src/features/profile/` module:
    - `ProfilePage.vue` — user profile view/edit:
      - Avatar section: large circular avatar, "Change" button
      - Info section: name, surname, phone, city — all editable
      - Edit mode: tap field to edit, save button appears
      - "My listings" link/button (→ /my-listings)
      - App info: version, "About Stella" link
  - Avatar change: same flow as registration (presigned URL upload to MinIO)
  - City change: same as registration (GPS + manual)
  - Use Telegram theme colors for consistent look

  **Must NOT do**:
  - Do NOT implement account deletion
  - Do NOT implement settings page
  - Do NOT implement language switching

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
    - Reason: Profile page with edit mode, avatar upload
  - **Skills**: [`frontend-ui-ux`]

  **Parallelization**:
  - **Can Run In Parallel**: YES (after Wave 3)
  - **Parallel Group**: Wave 4 (with Tasks 19-23, 25)
  - **Blocks**: None
  - **Blocked By**: Tasks 12 (router), 13 (stores), 14 (user API)

  **Acceptance Criteria**:
  - [ ] Profile shows current user data
  - [ ] All fields editable
  - [ ] Avatar change uploads to MinIO
  - [ ] Save updates profile via API
  - [ ] Link to My Listings

  **QA Scenarios:**
  ```
  Scenario: Edit profile name
    Tool: Playwright
    Steps:
      1. Navigate to /profile (registered user)
      2. Assert current name displayed
      3. Click name field / edit button
      4. Change name to "New Name"
      5. Click Save
      6. Refresh page
      7. Assert name shows "New Name"
    Expected Result: Name updated and persisted
    Evidence: .sisyphus/evidence/task-24-edit-profile.png
  ```

  **Commit**: YES (groups with 19-23, 25)
  - Message: `feat(ui): add all frontend pages and components`
  - Files: `frontend/src/features/profile/**`
  - Pre-commit: `cd frontend && npx vue-tsc --noEmit`

---

- [ ] 25. My Listings Page UI

  **What to do**:
  - Create `frontend/src/features/my-listings/` module:
    - `MyListingsPage.vue` — seller's listing management:
      - List of user's listings (all statuses)
      - Each listing card shows: photo thumbnail, title, price, status badge
      - Status badges: 🟡 Pending (yellow), 🟢 Approved (green), 🔴 Rejected (red)
      - Tap listing → navigate to listing detail (/catalog/:id)
      - FAB (Floating Action Button): "+" button to create new listing (→ /create-listing)
      - Empty state: "You haven't created any listings yet" + "Create first listing" button
  - Sort by: most recent first
  - Use Telegram haptic feedback on FAB tap

  **Must NOT do**:
  - Do NOT implement inline editing
  - Do NOT implement listing deletion from this page (go to detail page)
  - Do NOT implement statistics/analytics

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
    - Reason: List page with status badges, FAB
  - **Skills**: [`frontend-ui-ux`]

  **Parallelization**:
  - **Can Run In Parallel**: YES (after Wave 3)
  - **Parallel Group**: Wave 4 (with Tasks 19-24)
  - **Blocks**: None
  - **Blocked By**: Tasks 12 (router), 13 (stores), 16 (listing API)

  **Acceptance Criteria**:
  - [ ] Shows all user's listings with correct status badges
  - [ ] FAB button navigates to /create-listing
  - [ ] Empty state when no listings
  - [ ] Tap listing navigates to detail page

  **QA Scenarios:**
  ```
  Scenario: My listings shows status badges
    Tool: Playwright
    Steps:
      1. Navigate to /my-listings (user with listings in different statuses)
      2. Assert listing cards visible
      3. Assert status badges show correct colors (🟡/🟢/🔴)
      4. Click FAB button
      5. Assert navigated to /create-listing
    Expected Result: Listings shown with status, FAB works
    Evidence: .sisyphus/evidence/task-25-my-listings.png
  ```

  **Commit**: YES (groups with 19-24)
  - Message: `feat(ui): add all frontend pages and components`
  - Files: `frontend/src/features/my-listings/**`
  - Pre-commit: `cd frontend && vitest run`

---

- [ ] 26. Dockerfiles (Backend + Frontend)

  **What to do**:
  - Create `backend/Dockerfile`:
    - Multi-stage: builder (install deps with uv) + runtime (slim image)
    - Base image: `python:3.12-slim`
    - Install uv, copy pyproject.toml + uv.lock, install deps
    - Copy app code
    - CMD: `granian --interface asgi --host 0.0.0.0 --port 8000 --workers 1 --loop uvloop --workers-max-rss 512 app.main:app`
    - EXPOSE 8000
    - Non-root user
  - Create `frontend/Dockerfile`:
    - Multi-stage: builder (pnpm install + build) + runtime (nginx)
    - Stage 1: `node:20-alpine`, pnpm install, pnpm build
    - Stage 2: `nginx:alpine`, copy dist/ to /usr/share/nginx/html, copy nginx.conf
    - EXPOSE 80
  - Both Dockerfiles optimized for layer caching (deps first, code second)

  **Must NOT do**:
  - Do NOT include dev dependencies in production images
  - Do NOT use `--workers > 1` in Granian (aiogram requires single event loop)
  - Do NOT use `latest` tags for base images (pin versions)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Standard Dockerfile patterns
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (after core features)
  - **Parallel Group**: Wave 5 (with Tasks 27, 28, 29, 30, 31)
  - **Blocks**: Task 28
  - **Blocked By**: Tasks 2 (backend), 3 (frontend)

  **Acceptance Criteria**:
  - [ ] `docker build -t stella-api backend/` succeeds
  - [ ] `docker build -t stella-frontend frontend/` succeeds
  - [ ] Backend image runs Granian with --workers 1
  - [ ] Frontend image serves Vue SPA via Nginx
  - [ ] Images use non-root users

  **QA Scenarios:**
  ```
  Scenario: Docker images build successfully
    Tool: Bash
    Steps:
      1. Run `docker build -t stella-api backend/`
      2. Run `docker build -t stella-frontend frontend/`
      3. Run `docker image ls | grep stella`
    Expected Result: Both images built, sizes reasonable (<500MB each)
    Evidence: .sisyphus/evidence/task-26-docker-build.txt
  ```

  **Commit**: YES (groups with 27, 28)
  - Message: `feat(deploy): add Dockerfiles, Nginx, production compose`
  - Files: `backend/Dockerfile, frontend/Dockerfile`
  - Pre-commit: `docker build -t test-api backend/ && docker build -t test-frontend frontend/`

---

- [ ] 27. Nginx Configuration

  **What to do**:
  - Create `infra/nginx/default.conf`:
    - SPA static file serving from `/usr/share/nginx/html`
    - `try_files $uri $uri/ /index.html` — CRITICAL for Vue Router history mode
    - `/assets/` location: `expires 1y; add_header Cache-Control "public, immutable"`
    - `/` location: `add_header Cache-Control "no-cache"` (for index.html)
    - Gzip: on, text/plain text/css application/javascript application/json image/svg+xml
    - `/api/` reverse proxy to FastAPI backend (upstream `api:8000` for Docker network)
    - `/bot/` reverse proxy to FastAPI (for webhook endpoint)
    - Security headers: X-Frame-Options, X-Content-Type-Options, Referrer-Policy
  - Copy this config in frontend Dockerfile

  **Must NOT do**:
  - Do NOT configure SSL in Nginx (Coolify handles TLS termination)
  - Do NOT add rate limiting in Nginx (Redis handles it)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Standard Nginx config
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 5 (with Tasks 26, 28-31)
  - **Blocks**: Task 28
  - **Blocked By**: Task 3 (frontend)

  **Acceptance Criteria**:
  - [ ] SPA fallback configured (`try_files`)
  - [ ] Asset caching with immutable header
  - [ ] index.html served with no-cache
  - [ ] API reverse proxy configured
  - [ ] Gzip enabled

  **QA Scenarios:**
  ```
  Scenario: Nginx config is valid
    Tool: Bash
    Steps:
      1. Run `docker run --rm -v $(pwd)/infra/nginx/default.conf:/etc/nginx/conf.d/default.conf:ro nginx:alpine nginx -t`
    Expected Result: "nginx: configuration file is ok"
    Evidence: .sisyphus/evidence/task-27-nginx-config.txt
  ```

  **Commit**: YES (groups with 26, 28)
  - Message: `feat(deploy): add Dockerfiles, Nginx, production compose`
  - Files: `infra/nginx/default.conf`
  - Pre-commit: (nginx -t via Docker)

---

- [ ] 28. Docker Compose Production

  **What to do**:
  - Create `docker-compose.prod.yml`:
    - All services from dev compose (postgres, redis, minio) + api + frontend
    - **api service**: build from `backend/Dockerfile`, depends on postgres+redis, environment from .env, healthcheck (`curl http://localhost:8000/api/health`)
    - **frontend service**: build from `frontend/Dockerfile`, depends on api, ports 80:80
    - All services with `restart: unless-stopped`
    - Production-ready: no exposed DB ports (except via internal network), proper healthchecks
    - Network: internal Docker network for service communication
  - Compatible with Coolify deployment (Coolify uses docker-compose)

  **Must NOT do**:
  - Do NOT expose postgres/redis/minio ports in production
  - Do NOT include development tools

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Docker Compose config
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (after Tasks 26, 27)
  - **Parallel Group**: Wave 5 (with Tasks 26, 27, 29-31)
  - **Blocks**: None
  - **Blocked By**: Tasks 26 (Dockerfiles), 27 (Nginx config)

  **Acceptance Criteria**:
  - [ ] `docker compose -f docker-compose.prod.yml config --quiet` validates
  - [ ] `docker compose -f docker-compose.prod.yml build` succeeds
  - [ ] All services start and are healthy
  - [ ] No DB/Redis/MinIO ports exposed externally

  **QA Scenarios:**
  ```
  Scenario: Production stack starts
    Tool: Bash
    Steps:
      1. Run `docker compose -f docker-compose.prod.yml build`
      2. Run `docker compose -f docker-compose.prod.yml up -d`
      3. Wait 30 seconds
      4. Run `docker compose -f docker-compose.prod.yml ps`
      5. Run `curl http://localhost/api/health`
    Expected Result: All services running, health endpoint returns 200
    Evidence: .sisyphus/evidence/task-28-prod-stack.txt
  ```

  **Commit**: YES (groups with 26, 27)
  - Message: `feat(deploy): add Dockerfiles, Nginx, production compose`
  - Files: `docker-compose.prod.yml`

---

- [ ] 29. Backend Tests (pytest)

  **What to do**:
  - Set up test infrastructure:
    - `backend/tests/conftest.py`: test fixtures — async test client (httpx AsyncClient), test DB (SQLite in-memory or test PostgreSQL), test Redis mock, mock MinIO
    - `backend/tests/factories.py`: factory functions for creating test User, Listing, Category objects
    - `backend/pytest.ini` or pyproject.toml config: asyncio_mode=auto, test paths
  - Write tests:
    - `tests/test_auth.py`: initData validation (valid, expired, tampered, missing header), user auto-creation
    - `tests/test_users.py`: registration (happy path, duplicate, validation errors), profile CRUD, avatar URL generation
    - `tests/test_categories.py`: list categories (only approved), propose (creates unapproved), approve (admin only)
    - `tests/test_listings.py`: create listing, get listing, update (owner only), delete (cascades photos), max 5 photos
    - `tests/test_catalog.py`: filter by city, filter by category, pagination, only approved shown, sorting
  - Use httpx AsyncClient with FastAPI TestClient for endpoint testing
  - Mock external services (MinIO, bot) — don't require running Docker for unit tests

  **Must NOT do**:
  - Do NOT write integration tests that require running Docker (keep unit tests fast)
  - Do NOT test aiogram handlers directly (complex to mock, covered by QA scenarios)

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Test suite covering multiple modules with fixtures and mocks
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (after Wave 3)
  - **Parallel Group**: Wave 5 (with Tasks 26-28, 30, 31)
  - **Blocks**: None
  - **Blocked By**: Tasks 14-18 (all APIs must be implemented)

  **Acceptance Criteria**:
  - [ ] Test infrastructure set up (conftest, factories)
  - [ ] `cd backend && uv run pytest -x --tb=short` → all tests pass
  - [ ] Minimum 20 test cases covering auth, users, categories, listings, catalog
  - [ ] Tests run without Docker (mocked external services)

  **QA Scenarios:**
  ```
  Scenario: All backend tests pass
    Tool: Bash
    Steps:
      1. Run `cd backend && uv run pytest -x --tb=short -v`
    Expected Result: All tests pass, 0 failures
    Evidence: .sisyphus/evidence/task-29-pytest.txt
  ```

  **Commit**: YES
  - Message: `test: add backend and frontend test suites`
  - Files: `backend/tests/**`
  - Pre-commit: `cd backend && uv run pytest -x`

---

- [ ] 30. Frontend Tests (vitest)

  **What to do**:
  - Set up test infrastructure:
    - `frontend/vitest.config.ts`: test config with jsdom environment, path aliases
    - `frontend/tests/setup.ts`: global test setup (mock Telegram SDK, mock Axios)
  - Write tests:
    - `tests/stores/telegram.test.ts`: store initialization, isAuthenticated computed
    - `tests/stores/user.test.ts`: fetchProfile, register actions
    - `tests/stores/catalog.test.ts`: loadListings, loadCategories, filtering
    - `tests/components/ListingCard.test.ts`: renders title, price, photo
    - `tests/components/CategoryFilter.test.ts`: renders chips, emits selection
  - Mock Telegram SDK in all tests
  - Mock Axios responses with correct typed responses

  **Must NOT do**:
  - Do NOT write E2E tests (Playwright handles that in QA scenarios)
  - Do NOT test third-party components (Lucide icons, etc.)

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Test suite with mocking and component testing
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (after Wave 4)
  - **Parallel Group**: Wave 5 (with Tasks 26-29, 31)
  - **Blocks**: None
  - **Blocked By**: Tasks 19-25 (all UI pages must be implemented)

  **Acceptance Criteria**:
  - [ ] `cd frontend && pnpm run test` → all tests pass
  - [ ] Minimum 10 test cases covering stores and key components
  - [ ] Telegram SDK properly mocked

  **QA Scenarios:**
  ```
  Scenario: All frontend tests pass
    Tool: Bash
    Steps:
      1. Run `cd frontend && pnpm run test -- --run`
    Expected Result: All tests pass, 0 failures
    Evidence: .sisyphus/evidence/task-30-vitest.txt
  ```

  **Commit**: YES (groups with 29)
  - Message: `test: add backend and frontend test suites`
  - Files: `frontend/tests/**`
  - Pre-commit: `cd frontend && pnpm run test -- --run`

---

- [ ] 31. Git Repository Init + README

  **What to do**:
  - Initialize git repository: `git init`
  - Create comprehensive `.gitignore` (verify covers all): Python (__pycache__, .venv, *.pyc, .mypy_cache, .ruff_cache, .pytest_cache), Node (node_modules, dist, .vite), Docker (docker-compose.override.yml), IDE (.vscode, .idea), Environment (.env, !.env.example), OS (.DS_Store, Thumbs.db)
  - Create `README.md` with:
    - Project name, description, tech stack overview
    - Prerequisites (Docker, uv, pnpm, just)
    - Quick start: `just env-init && just up && just py-dev` (backend) + `just node-dev` (frontend)
    - Project structure overview
    - Available just recipes
    - Deployment section (Coolify + GitHub webhook)
  - Initial commit with all code
  - Push to GitHub (user should have remote configured)

  **Must NOT do**:
  - Do NOT create extensive documentation (README is enough for MVP)
  - Do NOT commit .env file (only .env.example)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Git init + README
  - **Skills**: [`git-master`]
    - `git-master`: For proper git initialization and commit

  **Parallelization**:
  - **Can Run In Parallel**: NO (must be last)
  - **Parallel Group**: Wave 5 (final task)
  - **Blocks**: None
  - **Blocked By**: All previous tasks

  **Acceptance Criteria**:
  - [ ] Git repository initialized
  - [ ] .gitignore covers all necessary patterns
  - [ ] README.md with setup instructions
  - [ ] Initial commit with all code
  - [ ] No .env or secrets committed

  **QA Scenarios:**
  ```
  Scenario: Git repo is clean
    Tool: Bash
    Steps:
      1. Run `git status`
      2. Verify no untracked files or uncommitted changes
      3. Run `git log --oneline | head -5`
      4. Run `grep -r "BOT_TOKEN=" . --include="*.env" | grep -v example`
    Expected Result: Clean git status, commits present, no secrets committed
    Evidence: .sisyphus/evidence/task-31-git-clean.txt
  ```

  **Commit**: YES
  - Message: `chore: add README, .gitignore, final cleanup`
  - Files: `README.md, .gitignore`
  - Pre-commit: `ruff check backend/ && cd frontend && npx vue-tsc --noEmit`

---

## Final Verification Wave

> 4 review agents run in PARALLEL. ALL must APPROVE. Rejection → fix → re-run.

- [ ] F1. **Plan Compliance Audit** — `oracle`
  Read the plan end-to-end. For each "Must Have": verify implementation exists (read file, curl endpoint, run command). For each "Must NOT Have": search codebase for forbidden patterns — reject with file:line if found. Check evidence files exist in .sisyphus/evidence/. Compare deliverables against plan.
  Output: `Must Have [N/N] | Must NOT Have [N/N] | Tasks [N/N] | VERDICT: APPROVE/REJECT`

- [ ] F2. **Code Quality Review** — `unspecified-high`
  Run `ruff check .` + `mypy app/` (backend) and `vue-tsc --noEmit` (frontend). Review all changed files for: `as any`/`@ts-ignore`, empty catches, console.log/print in prod, commented-out code, unused imports. Check AI slop: excessive comments, over-abstraction, generic names (data/result/item/temp). Verify `hmac.compare_digest` used (not `==`), no hardcoded secrets.
  Output: `Ruff [PASS/FAIL] | mypy [PASS/FAIL] | vue-tsc [PASS/FAIL] | Tests [N pass/N fail] | Files [N clean/N issues] | VERDICT`

- [ ] F3. **Real Manual QA** — `unspecified-high` (+ `playwright` skill)
  Start from clean state (`docker compose down -v && docker compose up -d`). Execute EVERY QA scenario from EVERY task — follow exact steps, capture evidence. Test cross-task integration: register → create listing → approve via bot → see in catalog → contact seller. Test edge cases: empty catalog, max 5 photos, long text, no GPS permission. Save to `.sisyphus/evidence/final-qa/`.
  Output: `Scenarios [N/N pass] | Integration [N/N] | Edge Cases [N tested] | VERDICT`

- [ ] F4. **Scope Fidelity Check** — `deep`
  For each task: read "What to do", read actual diff (git log/diff). Verify 1:1 — everything in spec was built (no missing), nothing beyond spec was built (no creep). Check "Must NOT do" compliance: no favorites, no search, no notifications, no Directus, no pgvector usage. Flag unaccounted changes.
  Output: `Tasks [N/N compliant] | Scope Creep [CLEAN/N issues] | Forbidden Features [CLEAN/N found] | VERDICT`

---

## Commit Strategy

| After Tasks | Commit Message | Pre-commit Check |
|-------------|----------------|------------------|
| 1-3 | `feat(scaffold): init monorepo with backend + frontend skeletons` | `ruff check .` |
| 4 | `feat(db): add SQLAlchemy models and Alembic migrations` | `ruff check . && mypy app/` |
| 5-6 | `feat(infra): add TypeScript types, API client, Docker Compose dev` | `ruff check .` |
| 7-8 | `feat(telegram): integrate SDK init + bot webhook` | `ruff check . && mypy app/` |
| 9-11 | `feat(core): add auth middleware, Redis, MinIO services` | `pytest -x` |
| 12-13 | `feat(frontend): add router, guards, Pinia stores` | `vue-tsc --noEmit` |
| 14-17 | `feat(api): add user, category, listing, catalog endpoints` | `pytest -x` |
| 18 | `feat(bot): add moderation commands (approve/reject)` | `pytest -x` |
| 19-25 | `feat(ui): add all frontend pages and components` | `vitest run` |
| 26-28 | `feat(deploy): add Dockerfiles, Nginx, production compose` | `docker compose build` |
| 29-30 | `test: add backend and frontend test suites` | `pytest && vitest run` |
| 31 | `chore: add README, .gitignore, final cleanup` | `ruff check . && mypy app/` |

---

## Success Criteria

### Verification Commands
```bash
# Backend
cd backend && ruff check .           # Expected: All checks passed
cd backend && mypy app/              # Expected: Success: no issues found
cd backend && pytest -x --tb=short   # Expected: All tests passed

# Frontend
cd frontend && npx vue-tsc --noEmit  # Expected: No errors
cd frontend && npx vitest run        # Expected: All tests passed

# Docker
docker compose build                 # Expected: Successfully built
docker compose up -d                 # Expected: All services healthy
curl http://localhost:8000/api/health # Expected: {"status": "ok"}

# Full stack
docker compose -f docker-compose.prod.yml build  # Expected: Success
```

### Final Checklist
- [ ] All "Must Have" items verified present
- [ ] All "Must NOT Have" items verified absent
- [ ] All backend tests pass (`pytest`)
- [ ] All frontend tests pass (`vitest run`)
- [ ] Ruff clean (`ruff check .`)
- [ ] mypy clean (`mypy app/`)
- [ ] TypeScript clean (`vue-tsc --noEmit`)
- [ ] Docker builds succeed
- [ ] App works in Telegram (or with mock environment)
- [ ] Full user flow works: register → create listing → moderate → browse → contact seller

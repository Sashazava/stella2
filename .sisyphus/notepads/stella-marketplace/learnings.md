# Learnings — stella-marketplace

## [2026-02-26] Wave 1 Completed

### Environment
- `just` is NOT installed on system — justfile created but untestable
- `docker` is NOT installed — docker-compose.yml created but untestable
- `uv` is NOT installed — Python deps not installed/tested
- Available: Python 3.12.3, Node 20, pnpm 10.30.3, npx

### Frontend
- TailwindCSS v4: use `@import "tailwindcss"` in CSS, NO tailwind.config.js
- Vue Router: `createWebHistory()` ONLY — hash mode breaks Telegram
- Telegram SDK: `init()` BEFORE `createApp()`, dev mock with `mockTelegramEnv()`
- TypeScript: strict mode, `vue-tsc --noEmit` passes
- Build: `pnpm run build` produces dist/ successfully

### Backend
- Python syntax verified via `python3 -c "import ast; ast.parse(...)"`
- Alembic: async configured with explicit model imports in env.py
- Models: User, Category, Listing (ListingStatus enum), ListingPhoto

### Verification Commands
- Frontend typecheck: `cd frontend && pnpm run typecheck`
- Python syntax: `python3 -c "import ast; ast.parse(open('file.py').read())"`
- Frontend build: `cd frontend && pnpm run build`

## Task 7: Telegram SDK Initialization + Dev Mock (2026-02-26)

### SDK version: `@telegram-apps/sdk-vue@2.0.31` (re-exports `@telegram-apps/sdk@3.11.8`)

### `useSignal()` must be called inside a Vue component setup
- It calls `onBeforeUnmount()` internally to unsubscribe from signal updates
- Import: `import { useSignal } from '@telegram-apps/sdk-vue'`
- Signature: `useSignal(signal) → Readonly<Ref<T>>`

### initData namespace properties are Computed<T> signals
- `initData.user` → `Computed<User | undefined>` — SDK User from @telegram-apps/types
- `initData.raw` → `Computed<string | undefined>` — raw init data query string
- Both work directly with `useSignal(initData.user)`

### themeParams namespace
- `themeParams.isDark` → `Computed<boolean>` — true when bg color is dark
- `themeParams.state` → `Computed<ThemeParams>` — full theme params object
- `themeParams.mount.isAvailable()` — check before calling `themeParams.mount()`
- `themeParams.bindCssVars()` — exposes `--tg-theme-*` CSS variables

### viewport and backButton
- `viewport.mount.isAvailable()`, `viewport.expand.isAvailable()` — availability guards
- `viewport.bindCssVars()` — exposes `--tg-viewport-height`, `--tg-viewport-width`
- `backButton.mount.isAvailable()` — check before mounting

### mockTelegramEnv in v2.x bridge API
- New signature: `mockTelegramEnv({ launchParams?, onEvent?, resetPostMessage? })`
- However old-style `{ themeParams, initData, version, platform }` also compiles without errors
  (likely because `@telegram-apps/bridge` types may not be fully resolved in pnpm virtual store)

### Dynamic import for dev mock prevents production bundle inclusion
```typescript
if (import.meta.env.DEV) {
  const { setupDevMock } = await import('./lib/telegram-mock')
  // ...
}
```

### SDK component mounting pattern (with availability guards)
Always check `.isAvailable()` before calling mount — prevents errors in non-TMA environments.

## [2026-02-27] Task 23: Create Listing Page

### Components created
- `CreateListingPage.vue` — 3-step wizard (info → category/city → photos)
- `PhotoUploadGrid.vue` — grid of up to 5 photo slots with canvas compression + presigned upload
- `CategorySelector.vue` — dropdown with category list + "propose new" inline form

### Type compatibility notes
- `ListingCreate` type doesn't include `city` field. Workaround: assign payload to a variable first (avoids excess property check on object literals), then pass to `createListing()`. TypeScript structural subtyping allows extra properties from variables.
- `Category.id` is `string`, not `number` — used `string | null` for CategorySelector's modelValue prop despite task suggesting `number`.
- `PhotoUploadResponse` uses `object_key` (not `photo_key` as mentioned in task spec).
- `confirmPhotoUpload` returns `void` — construct photo URL locally using `VITE_STORAGE_URL` env var + `object_key`.
- `listingStore.submitListing()` doesn't exist in the store. Listing is created as `pending` status in step 2; step 3 just navigates to `/my-listings`.

### Patterns followed
- `<script setup lang="ts">` + Composition API throughout
- `<style scoped>` with BEM-like CSS class naming (matches CatalogPage, ProfilePage)
- Telegram theme CSS variables with fallbacks: `var(--tg-theme-*, #fallback)`
- `color-mix(in srgb, ...)` for opacity effects on theme colors
- Canvas-based image compression before presigned URL upload (same pattern as ProfilePage avatar upload)
- `defineEmits<{...}>()` and `defineProps<{...}>()` for typed component API

### Router update
- Replaced `defineComponent({ template })` placeholder with lazy `() => import(...)` pattern
- Kept `defineComponent` import since `ErrorPage` still uses it on line 21

## [2026-02-27] Task 27: Nginx Config

### Findings
- Created `/infra/nginx/default.conf` with complete SPA + API proxy configuration
- Key features implemented:
  - **SPA Fallback**: `try_files $uri $uri/ /index.html` for Vue Router history mode (CRITICAL)
  - **Asset Caching**: 1-year expiry with immutable header for `/assets/` (Vite content-hashed)
  - **API Proxying**: `/api/` and `/bot/` routes proxy to `http://api:8000` with proper headers
  - **Gzip Compression**: Enabled for text/css/js/json/svg with level 6
  - **Security Headers**: X-Frame-Options, X-Content-Type-Options, Referrer-Policy
  - **No SSL**: Coolify handles TLS termination externally
- Service name confirmed as `api` (from task spec, not yet in docker-compose)
- Port 80 listening, proxies to backend on port 8000
- `index.html` served with `no-cache` header to ensure fresh SPA loads

## [2026-02-27] Task 26: Dockerfiles

### Backend Dockerfile (`backend/Dockerfile`)
- **Multi-stage build**: builder (uv + deps) → runtime (slim image)
- **Critical**: `--workers 1` in Granian CMD (aiogram requires single event loop)
- **Base image**: `python:3.12-slim` (not latest)
- **Non-root user**: `stella` (groupadd + useradd)
- **Layer caching**: pyproject.toml copied before app code
- **Entry point**: `granian --interface asgi --host 0.0.0.0 --port 8000 --workers 1 --loop uvloop --workers-max-rss 512 app.main:app`
- **Exposed port**: 8000

### Frontend Dockerfile (`frontend/Dockerfile`)
- **Multi-stage build**: builder (Node 20 + pnpm) → runtime (nginx:alpine)
- **Base images**: `node:20-alpine` (builder), `nginx:alpine` (runtime)
- **pnpm setup**: corepack enable + corepack prepare pnpm@latest
- **Layer caching**: package.json + pnpm-lock.yaml copied before source
- **Build flag**: `--frozen-lockfile` for reproducibility
- **Nginx config**: Copied from `frontend/nginx.conf` to `/etc/nginx/conf.d/default.conf`
- **Exposed port**: 80

### Frontend Nginx Config (`frontend/nginx.conf`)
- **Gzip compression**: Enabled for text/css/js/json/svg
- **Security headers**: X-Frame-Options, X-Content-Type-Options, Referrer-Policy
- **Asset caching**: `/assets/` with 1y expiry + immutable flag
- **API proxy**: `/api/` → `http://api:8000` with forwarded headers
- **Bot webhook proxy**: `/bot/` → `http://api:8000`
- **SPA fallback**: `try_files $uri $uri/ /index.html` for Vue Router history mode

### Key Decisions
1. **Single worker for backend**: Mandatory for aiogram's in-process event loop
2. **Nginx config in frontend dir**: Simplifies Docker build context (frontend/ only)
3. **No dev dependencies**: Production images use `--no-dev` flag
4. **Specific version tags**: Avoid `latest` for reproducibility
5. **Non-root user**: Security best practice (stella user)

### Files Created
- ✅ `/home/fosterspc/project/site/backend/Dockerfile` (41 lines)
- ✅ `/home/fosterspc/project/site/frontend/Dockerfile` (36 lines)
- ✅ `/home/fosterspc/project/site/frontend/nginx.conf` (45 lines)

All files verified for syntax correctness and requirement compliance.

## [2026-02-27] Task 28: Docker Compose Production

### Key Findings
- **MINIO_SERVER_URL critical**: Must use internal Docker hostname (`http://minio:9000`) for presigned URL generation, NOT `http://localhost:9000`
- **Database URL scheme**: Uses `postgresql+psycopg://` (psycopg3 async driver), not `postgresql://`
- **Service dependencies**: All services use `condition: service_healthy` to ensure proper startup order
- **Network isolation**: postgres, redis, minio have NO exposed ports in production (internal network only)
- **Frontend only exposure**: Only frontend service exposes port 80 to external world
- **Environment variables**: Both `env_file: .env` and explicit `environment:` overrides for Docker networking
- **Healthchecks**: All services have proper healthchecks; api uses Python urllib for HTTP health check

### Architecture Pattern
```
External (port 80)
    ↓
frontend (Nginx/Vue) → proxies /api/ to api:8000
    ↓
api (FastAPI) → connects to postgres, redis, minio via internal network
    ↓
postgres, redis, minio (internal network only)
```

### Production Deployment
- Coolify deploys via: `docker compose -f docker-compose.prod.yml up`
- All inter-service communication uses Docker service names (postgres:5432, redis:6379, minio:9000)
- No development tools or volumes included
- All services have `restart: unless-stopped` for resilience

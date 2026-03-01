# ============================================================
# Stage 1: Build Vue 3 frontend
# ============================================================
FROM node:20-alpine AS frontend-builder

RUN corepack enable && corepack prepare pnpm@latest --activate
WORKDIR /build
COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY frontend/ ./
RUN pnpm run build

# ============================================================
# Stage 2: Install Python backend dependencies
# ============================================================
FROM python:3.12-slim AS backend-builder

RUN pip install uv
WORKDIR /build
COPY backend/pyproject.toml .
COPY backend/app/ ./app/
RUN uv venv && uv pip install .

# ============================================================
# Stage 3: Production image — Nginx + Granian via supervisord
# ============================================================
FROM python:3.12-slim

# Install Nginx + Supervisor
RUN apt-get update \
    && apt-get install -y --no-install-recommends nginx supervisor \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python venv from builder
COPY --from=backend-builder /build/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Backend source code
COPY backend/app/ /app/app/

# Built Vue SPA → Nginx root
COPY --from=frontend-builder /build/dist/ /usr/share/nginx/html/

# Nginx config (proxy /api/ → localhost:8000)
COPY nginx.conf /etc/nginx/sites-available/default

# Supervisor config (manages nginx + granian)
COPY supervisord.conf /etc/supervisor/conf.d/stella.conf

EXPOSE 80

CMD ["/usr/bin/supervisord", "-n", "-c", "/etc/supervisor/conf.d/stella.conf"]

# Multi-stage build for FastAPI backend with Granian
# Stage 1: builder — install uv and Python dependencies
FROM python:3.12-slim AS builder

# Install uv package manager
RUN pip install uv

WORKDIR /app

# Copy dependency files first for layer caching
COPY pyproject.toml .

# Create virtual environment and install dependencies (no dev deps)
RUN uv venv && uv pip install --no-dev .

# Stage 2: runtime — slim image with non-root user
FROM python:3.12-slim AS runtime

# Create non-root user for security
RUN groupadd -r stella && useradd -r -g stella stella

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY app/ app/

# Set PATH to use virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Switch to non-root user
USER stella

# Expose port
EXPOSE 8000

# Run Granian with single worker (CRITICAL: aiogram requires single event loop)
CMD ["granian", "--interface", "asgi", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--loop", "uvloop", "--workers-max-rss", "512", "app.main:app"]

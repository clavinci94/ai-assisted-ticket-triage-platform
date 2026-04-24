# syntax=docker/dockerfile:1.7

# =========================================================
# Stage 1 — Build the React/Vite frontend
# =========================================================
FROM node:20-alpine AS frontend-builder

WORKDIR /frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./

# Default API base; override at build-time with --build-arg VITE_API_BASE_URL=...
ARG VITE_API_BASE_URL=/api
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

RUN npm run build


# =========================================================
# Stage 2 — Python runtime (FastAPI + static frontend)
# =========================================================
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# libpq is needed by psycopg (binary wheel still needs shared libs on slim images
# in some cases; this keeps things predictable across architectures).
RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY app ./app
COPY scripts ./scripts

# Ship the built frontend alongside the backend so the image is self-contained.
COPY --from=frontend-builder /frontend/dist ./frontend_dist

# Non-root user
RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

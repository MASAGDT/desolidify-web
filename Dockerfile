# Dockerfile
# Multi-stage build: bundle frontend (esbuild) then run Flask + Socket.IO + gunicorn.

# ──────────────────────────────────────────────────────────────────────────────
# Stage 1: Frontend build (ESM bundle via esbuild)
# ──────────────────────────────────────────────────────────────────────────────
FROM node:20-alpine AS webbuild
WORKDIR /web

# Copy only frontend sources
COPY frontend /web/frontend

# Initialize a minimal package context and install build deps
RUN npm init -y >/dev/null 2>&1 \
 && npm i --silent esbuild react react-dom >/dev/null 2>&1

# Build app.js bundle (ESM). We keep vendor modules as remote ESM (see vendor/*).
RUN npx esbuild frontend/src/App.jsx \
      --bundle \
      --format=esm \
      --sourcemap \
      --outfile=frontend/public/assets/app.js \
      --loader:.jsx=jsx

# Copy styles
RUN mkdir -p frontend/public/assets \
 && cp frontend/src/styles.css frontend/public/assets/styles.css

# ──────────────────────────────────────────────────────────────────────────────
# Stage 2: Python runtime
# ──────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# System deps:
# - libspatialindex: runtime for rtree
# - libgl1: optional headless GL provider (pyrender offscreen may require it)
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      libspatialindex-dev libgl1 ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Workdir
WORKDIR /app

# Copy backend
COPY backend /app/backend

# Copy frontend public + vendor
COPY frontend/public /app/frontend/public
COPY frontend/vendor /app/frontend/vendor

# Copy built frontend assets from Stage 1
COPY --from=webbuild /web/frontend/public/assets /app/frontend/public/assets

# Python dependencies
RUN pip install --no-cache-dir -r backend/requirements.txt

# Jobs directory (mounted volume recommended in production)
RUN mkdir -p /app/jobs

# Environment defaults (override with .env or docker run -e)
ENV FLASK_ENV=production \
    APP_VERSION=0.1.0 \
    JOBS_ROOT=/app/jobs \
    FRONTEND_PUBLIC=/app/frontend/public \
    FRONTEND_VENDOR=/app/frontend/vendor \
    MAX_WORKERS=1

# Expose Flask
EXPOSE 5000

# Healthcheck (simple TCP)
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import socket as s; import sys; x=s.socket(); x.settimeout(2); x.connect(('127.0.0.1',5000)); x.close(); sys.exit(0)"

# Entrypoint: gunicorn with eventlet worker for Socket.IO support
CMD ["gunicorn", "-k", "eventlet", "-w", "1", "-b", "0.0.0.0:5000", "backend.wsgi:app"]

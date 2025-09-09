# backend/config.py
from __future__ import annotations

import os
from pathlib import Path
from typing import Type

# -----------------------------------------------------------------------------
# Config Classes
# -----------------------------------------------------------------------------

class Config:
    # App
    APP_NAME = "desolidify-web"
    APP_VERSION = os.getenv("APP_VERSION", "0.1.0")
    ENV_NAME = os.getenv("FLASK_ENV", "development")
    SECRET_KEY = os.getenv("SECRET_KEY", "change-this-in-production")

    # Paths
    _BASE = Path(__file__).resolve().parents[1]
    JOBS_ROOT = os.getenv("JOBS_ROOT", str((_BASE / "jobs").resolve()))
    FRONTEND_PUBLIC = os.getenv("FRONTEND_PUBLIC", str((_BASE / "frontend" / "public").resolve()))
    FRONTEND_VENDOR = os.getenv("FRONTEND_VENDOR", str((_BASE / "frontend" / "vendor").resolve()))

    # Uploads
    MAX_CONTENT_LENGTH = int(float(os.getenv("MAX_CONTENT_LENGTH_MB", "100")) * 1024 * 1024)  # default 100 MB
    ALLOWED_EXTENSIONS = {ext.strip().lower() for ext in os.getenv("ALLOWED_EXTENSIONS", "stl").split(",")}

    # CORS
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")

    # Socket.IO
    SOCKETIO_ASYNC_MODE = os.getenv("SOCKETIO_ASYNC_MODE", "threading")  # 'eventlet'|'gevent'|'threading'
    SOCKETIO_CORS_ALLOWED_ORIGINS = os.getenv("SOCKETIO_CORS_ALLOWED_ORIGINS", "*")
    SOCKETIO_LOGGER = os.getenv("SOCKETIO_LOGGER", "0") in ("1", "true", "True")
    SOCKETIO_ENGINEIO_LOGGER = os.getenv("SOCKETIO_ENGINEIO_LOGGER", "0") in ("1", "true", "True")
    SOCKETIO_PING_INTERVAL = int(os.getenv("SOCKETIO_PING_INTERVAL", "25"))
    SOCKETIO_PING_TIMEOUT = int(os.getenv("SOCKETIO_PING_TIMEOUT", "60"))

    # Queue / Workers
    QUEUE_BACKEND = os.getenv("QUEUE_BACKEND", "thread")  # 'thread' | 'celery'
    MAX_WORKERS = int(os.getenv("MAX_WORKERS", "1"))

    # Retention
    JOB_RETENTION_HOURS = int(os.getenv("JOB_RETENTION_HOURS", "6"))

    # Engine Safety
    ENGINE_MAX_CHUNK_PTS = int(os.getenv("ENGINE_MAX_CHUNK_PTS", "2500000"))
    ENGINE_MAX_VOXEL = float(os.getenv("ENGINE_MAX_VOXEL", "1.2"))
    ENGINE_MIN_VOXEL = float(os.getenv("ENGINE_MIN_VOXEL", "0.2"))


class Development(Config):
    DEBUG = True


class Production(Config):
    DEBUG = False
    # In production, set CORS origins appropriately and a strong SECRET_KEY


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def load_config_from_env(app, default: Type[Config] = Config) -> None:
    """
    Load configuration for the Flask app using DESOLIDIFY_CONFIG or fallback.
    """
    dotted = os.getenv("DESOLIDIFY_CONFIG")
    if dotted:
        app.config.from_object(dotted)
    else:
        app.config.from_object(default)

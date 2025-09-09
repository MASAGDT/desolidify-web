# backend/app.py
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from flask import Flask, jsonify, send_from_directory, Blueprint
from flask_cors import CORS
from flask_socketio import SocketIO

# Socket.IO singleton (initialized in create_app)
socketio: Optional[SocketIO] = None

# -----------------------------------------------------------------------------
# App Factory
# -----------------------------------------------------------------------------

def create_app(config_object: str | None = None) -> Flask:
    """
    Flask application factory.
    Loads configuration, registers blueprints, static routes, and Socket.IO.
    """
    app = Flask(
        __name__,
        static_folder=None,  # We wire frontend public manually
        template_folder=None,
    )

    # Load configuration
    from .config import Config, load_config_from_env
    if config_object:
        app.config.from_object(config_object)
    else:
        # Resolves DESOLIDIFY_CONFIG or falls back to Config
        load_config_from_env(app, default=Config)

    # Enable CORS (dev-friendly defaults; override via env)
    CORS(
        app,
        resources={r"/api/*": {"origins": app.config.get("CORS_ORIGINS", "*")}},
        supports_credentials=True,
    )

    # Ensure required runtime dirs exist
    jobs_root = Path(app.config["JOBS_ROOT"]).resolve()
    jobs_root.mkdir(parents=True, exist_ok=True)

    # Initialize Socket.IO
    _init_socketio(app)

    # Register blueprints
    _register_api(app)

    # Error handlers
    _register_error_handlers(app)

    # Static frontend routes (serve SPA from frontend/public)
    _register_frontend_routes(app)

    # Simple health
    @app.get("/api/health")
    def api_health():
        return jsonify(
            {
                "name": "desolidify-web",
                "status": "ok",
                "socketio": True,
                "jobs_root": str(jobs_root),
                "env": app.config.get("ENV_NAME", "development"),
                "version": app.config.get("APP_VERSION", "0.1.0"),
            }
        )

    # CLI utilities (optional)
    _register_cli(app)

    return app


# -----------------------------------------------------------------------------
# Internal wiring
# -----------------------------------------------------------------------------

def _init_socketio(app: Flask) -> None:
    global socketio
    if isinstance(socketio, SocketIO):
        return
    cors = app.config.get("SOCKETIO_CORS_ALLOWED_ORIGINS", "*")
    async_mode = app.config.get("SOCKETIO_ASYNC_MODE", "threading")  # 'eventlet'|'gevent'|'threading'
    socketio = SocketIO(
        app,
        cors_allowed_origins=cors,
        async_mode=async_mode,
        logger=app.config.get("SOCKETIO_LOGGER", False),
        engineio_logger=app.config.get("SOCKETIO_ENGINEIO_LOGGER", False),
        ping_interval=app.config.get("SOCKETIO_PING_INTERVAL", 25),
        ping_timeout=app.config.get("SOCKETIO_PING_TIMEOUT", 60),
        max_http_buffer_size=app.config.get("MAX_CONTENT_LENGTH"),
    )


def _register_api(app: Flask) -> None:
    try:
        # Expected factory in backend/api/__init__.py
        from .api import create_api_blueprint  # type: ignore
        api_bp = create_api_blueprint()
    except Exception:
        # Temporary stub blueprint to avoid import errors during scaffold phase.
        api_bp = Blueprint("api", __name__, url_prefix="/api")
        @api_bp.get("/stub")
        def _stub():
            return jsonify({"ok": True, "note": "API not yet populated."})
    app.register_blueprint(api_bp)


def _register_error_handlers(app: Flask) -> None:
    try:
        from .api.errors import register_error_handlers  # type: ignore
        register_error_handlers(app)
    except Exception:
        # Defer until api/errors.py exists
        pass


def _register_frontend_routes(app: Flask) -> None:
    project_root = Path(__file__).resolve().parents[1]
    public_dir = (project_root / "frontend" / "public").resolve()
    vendor_dir = (project_root / "frontend" / "vendor").resolve()

    app.config.setdefault("FRONTEND_PUBLIC", str(public_dir))
    app.config.setdefault("FRONTEND_VENDOR", str(vendor_dir))

    @app.get("/")
    def index_html():
        return send_from_directory(app.config["FRONTEND_PUBLIC"], "index.html")

    @app.get("/assets/<path:path>")
    def assets(path: str):
        return send_from_directory(app.config["FRONTEND_PUBLIC"], path)

    @app.get("/vendor/<path:path>")
    def vendor(path: str):
        return send_from_directory(app.config["FRONTEND_VENDOR"], path)


def _register_cli(app: Flask) -> None:
    import click
    @app.cli.command("purge-jobs")
    @click.option("--hours", default=app.config.get("JOB_RETENTION_HOURS", 6), help="Delete jobs older than N hours")
    def purge_jobs(hours: int):
        """Delete old job folders."""
        try:
            from .services.storage import purge_old_jobs  # type: ignore
            deleted = purge_old_jobs(hours=hours)
            click.echo(f"Deleted {deleted} old job(s).")
        except Exception as e:
            click.echo(f"purge-jobs failed: {e}")


# -----------------------------------------------------------------------------
# Socket.IO helpers (used by services.progress)
# -----------------------------------------------------------------------------

def socketio_emit_progress(job_id: str, progress: float, message: str | None = None) -> None:
    """
    Emit a progress update to WebSocket room 'job:<id>'.
    """
    global socketio
    if not isinstance(socketio, SocketIO):
        return
    payload = {"job_id": job_id, "progress": float(progress)}
    if message is not None:
        payload["message"] = message
    socketio.emit("progress", payload, room=f"job:{job_id}")

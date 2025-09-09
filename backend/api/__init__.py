# backend/api/__init__.py
from __future__ import annotations

from flask import Blueprint

def create_api_blueprint() -> Blueprint:
    bp = Blueprint("api", __name__, url_prefix="/api")

    # Register subroutes
    from .meta import register_meta_routes
    from .jobs import register_job_routes

    register_meta_routes(bp)
    register_job_routes(bp)

    return bp

# backend/services/progress.py
from __future__ import annotations

from typing import Optional

try:
    from flask import current_app
except Exception:  # pragma: no cover
    current_app = None  # type: ignore

from .storage import set_status
# We call Socket.IO emitter via backend.app helper to avoid circular import
try:
    from ..app import socketio_emit_progress  # type: ignore
except Exception:  # pragma: no cover
    socketio_emit_progress = None  # type: ignore


def set_progress(job_id: str, frac: float, message: Optional[str] = None) -> None:
    """
    Persist progress to status.json and emit over WebSocket room job:<id>.
    """
    f = float(max(0.0, min(1.0, frac)))
    set_status(job_id, state="running", progress=f, message=message or "")
    try:
        if socketio_emit_progress:
            socketio_emit_progress(job_id, f, message)
    except Exception:
        # Best-effort only
        pass

# backend/services/queue.py
from __future__ import annotations

import concurrent.futures
import threading
import uuid
from typing import Any, Dict, Optional

try:
    from flask import current_app
except Exception:  # pragma: no cover
    current_app = None  # type: ignore

from .storage import set_status, write_log

_executor_lock = threading.Lock()
_executor: Optional[concurrent.futures.ThreadPoolExecutor] = None


def _get_max_workers() -> int:
    try:
        if current_app:  # type: ignore
            return int(current_app.config.get("MAX_WORKERS", 1))
    except Exception:
        pass
    return 1


def _ensure_executor() -> concurrent.futures.ThreadPoolExecutor:
    global _executor
    if _executor is None:
        with _executor_lock:
            if _executor is None:
                _executor = concurrent.futures.ThreadPoolExecutor(max_workers=_get_max_workers(), thread_name_prefix="perforate")
    return _executor


def submit_perforate(job_id: str, params: Dict[str, Any]) -> str:
    """
    Schedule the perforation task on the local thread pool.
    Returns a task_id (UUID).
    """
    task_id = str(uuid.uuid4())
    exec_ = _ensure_executor()

    def _run():
        set_status(job_id, state="running", progress=0.0, message="Started")
        write_log(job_id, f"Task {task_id} started")
        try:
            # Defer to tasks module (to be implemented): tasks.perforate.run(job_id, params)
            from ..tasks.perforate import run as task_run  # type: ignore
        except Exception as e:
            write_log(job_id, f"Task import error: {e}")
            set_status(job_id, state="error", progress=0.0, message=f"Task import error: {e}")
            return

        try:
            task_run(job_id, params)
        except Exception as e:
            write_log(job_id, f"Task failed: {e}")
            set_status(job_id, state="error", progress=0.0, message=str(e))
        else:
            write_log(job_id, f"Task {task_id} finished")
            set_status(job_id, state="finished", progress=1.0, message="Completed")

    exec_.submit(_run)
    return task_id

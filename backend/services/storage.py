# backend/services/storage.py
from __future__ import annotations

import io
import json
import os
import shutil
import time
import uuid
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Dict, Optional, List, Tuple

try:
    from flask import current_app
except Exception:  # pragma: no cover
    current_app = None  # type: ignore

# -----------------------------------------------------------------------------
# Paths & low-level I/O
# -----------------------------------------------------------------------------

def _base_dir() -> Path:
    # Prefer Flask config; fallback to env or local ./jobs
    root: Optional[str] = None
    try:
        if current_app:  # type: ignore
            root = current_app.config.get("JOBS_ROOT")
    except Exception:
        root = None
    if not root:
        root = os.getenv("JOBS_ROOT")
    if not root:
        root = str(Path(__file__).resolve().parents[2] / "jobs")
    p = Path(root).resolve()
    p.mkdir(parents=True, exist_ok=True)
    return p


def job_dir(job_id: str) -> Path:
    return (_base_dir() / job_id).resolve()


def _atomic_write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def _atomic_write_text(path: Path, text: str) -> None:
    _atomic_write_bytes(path, text.encode("utf-8"))


def _atomic_write_json(path: Path, obj: Any) -> None:
    if is_dataclass(obj):
        obj = asdict(obj)
    _atomic_write_text(path, json.dumps(obj, ensure_ascii=False, indent=2))


def _read_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

# -----------------------------------------------------------------------------
# Public API
# -----------------------------------------------------------------------------

def new_job() -> str:
    """Create a new job folder and return its ID."""
    jid = str(uuid.uuid4())
    d = job_dir(jid)
    d.mkdir(parents=True, exist_ok=True)
    # Seed status
    set_status(jid, state="created", progress=0.0, message="Job created")
    return jid


def save_upload(job_id: str, file_storage, *, filename_hint: str = "input.stl") -> Path:
    """
    Save uploaded file (Werkzeug FileStorage) to job folder as input.stl.
    """
    d = job_dir(job_id)
    d.mkdir(parents=True, exist_ok=True)
    in_path = d / "input.stl"
    # werkzeug FileStorage has .save()
    file_storage.save(str(in_path))
    # Save original filename
    meta = {"filename": filename_hint, "uploaded_at": int(time.time())}
    _atomic_write_json(d / "upload.json", meta)
    return in_path


def write_params(job_id: str, params: Dict[str, Any]) -> Path:
    p = job_dir(job_id) / "params.json"
    _atomic_write_json(p, params)
    return p


def read_params(job_id: str) -> Optional[Dict[str, Any]]:
    return _read_json(job_dir(job_id) / "params.json")


def set_status(job_id: str, *, state: str, progress: float | int = 0.0, message: Optional[str] = None) -> Path:
    st = {
        "state": state,
        "progress": float(progress),
        "message": message or "",
        "ts": int(time.time()),
    }
    p = job_dir(job_id) / "status.json"
    _atomic_write_json(p, st)
    return p


def get_status(job_id: str) -> Optional[Dict[str, Any]]:
    return _read_json(job_dir(job_id) / "status.json")


def list_statuses() -> List[Tuple[str, Dict[str, Any]]]:
    base = _base_dir()
    out: List[Tuple[str, Dict[str, Any]]] = []
    for child in base.iterdir():
        if not child.is_dir():
            continue
        st = _read_json(child / "status.json")
        if st:
            out.append((child.name, st))
    return out


def write_log(job_id: str, line: str) -> None:
    p = job_dir(job_id) / "log.txt"
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{ts}] {line}\n")


def write_result(job_id: str, source: Path | bytes | io.BytesIO) -> Path:
    """
    Save output STL to job folder as output.stl.
    Accepts a filesystem path or raw bytes/BytesIO.
    """
    out_path = job_dir(job_id) / "output.stl"
    if isinstance(source, Path):
        out_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(str(source), str(out_path))
    elif isinstance(source, io.BytesIO):
        _atomic_write_bytes(out_path, source.getvalue())
    elif isinstance(source, bytes):
        _atomic_write_bytes(out_path, source)
    else:
        raise TypeError("write_result: unsupported source type")
    return out_path


def has_result(job_id: str) -> bool:
    return (job_dir(job_id) / "output.stl").exists()


def purge_old_jobs(*, hours: int) -> int:
    """
    Delete jobs older than N hours based on status.json ts or folder mtime.
    Returns count of deleted jobs.
    """
    cutoff = time.time() - hours * 3600
    base = _base_dir()
    deleted = 0
    for child in base.iterdir():
        if not child.is_dir():
            continue
        st = _read_json(child / "status.json") or {}
        ts = st.get("ts")
        if not isinstance(ts, (int, float)):
            try:
                ts = child.stat().st_mtime
            except Exception:
                ts = time.time()
        if ts < cutoff:
            try:
                shutil.rmtree(child, ignore_errors=True)
                deleted += 1
            except Exception:
                pass
    return deleted


def purge_all_jobs() -> int:
    base = _base_dir()
    count = 0
    for child in base.iterdir():
        if child.is_dir():
            shutil.rmtree(child, ignore_errors=True)
            count += 1
    return count

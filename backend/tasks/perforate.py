# backend/tasks/perforate.py
from __future__ import annotations

import io
from pathlib import Path
from typing import Any, Dict, Optional, Callable

from ..services.storage import (
    job_dir,
    read_params,
    write_params,
    write_log,
    set_status,
    write_result,
)
from ..services.progress import set_progress as _set_progress
from ..desolidify_engine.settings import from_params, clamp_settings
from ..desolidify_engine.engine import perforate_mesh_sdf, load_mesh_any


def _progress_cb(job_id: str) -> Callable[[float], None]:
    last = -1

    def _cb(frac: float) -> None:
        nonlocal last
        pct = int(max(0, min(100, round(float(frac) * 100))))
        if pct != last:
            last = pct
            _set_progress(job_id, pct / 100.0)
    return _cb


def run(job_id: str, params: Dict[str, Any] | None = None) -> None:
    """
    Worker entrypoint: perforate uploaded STL for a given job_id.
    Side effects:
      - updates status.json with progress
      - writes output.stl
      - appends to log.txt
    """
    d = job_dir(job_id)
    in_path = d / "input.stl"
    if not in_path.exists():
        set_status(job_id, state="error", progress=0.0, message="input.stl not found")
        write_log(job_id, "ERROR: input.stl missing")
        return

    # Load/merge params
    disk_params = read_params(job_id) or {}
    merged: Dict[str, Any] = {**disk_params, **(params or {})}
    # Persist merged params back (authoritative)
    write_params(job_id, merged)

    # Build settings (clamped to server-side ranges)
    s = clamp_settings(from_params(merged))

    write_log(job_id, f"Starting perforation: spacing={s.spacing} radius={s.radius} voxel={s.voxel} orient={s.orientations} chunk={s.chunk_pts}")
    set_status(job_id, state="running", progress=0.0, message="Loading mesh")

    try:
        mesh = load_mesh_any(Path(in_path))
    except Exception as e:
        set_status(job_id, state="error", progress=0.0, message=f"Load failed: {e}")
        write_log(job_id, f"ERROR loading mesh: {e}")
        return

    # Execute core engine with progress callback
    cb = _progress_cb(job_id)
    try:
        set_status(job_id, state="running", progress=0.0, message="Perforating")
        result = perforate_mesh_sdf(mesh, s, progress=cb)
    except Exception as e:
        set_status(job_id, state="error", progress=0.0, message=f"Engine failed: {e}")
        write_log(job_id, f"ERROR engine: {e}")
        return

    # Export to STL bytes and write
    try:
        buf = io.BytesIO()
        result.export(buf, file_type="stl")
        write_result(job_id, buf)
        _set_progress(job_id, 1.0)
        set_status(job_id, state="finished", progress=1.0, message="Completed")
        write_log(job_id, "Perforation complete. output.stl written.")
    except Exception as e:
        set_status(job_id, state="error", progress=0.95, message=f"Write failed: {e}")
        write_log(job_id, f"ERROR writing result: {e}")


# TODO: optional: add CLI shim for local debugging
# if __name__ == "__main__":
#     import sys, json
#     jid = sys.argv[1]
#     params = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
#     run(jid, params)

# backend/desolidify_engine/preview.py
from __future__ import annotations

import io
from typing import Any, Callable, Dict, Optional

import trimesh

from backend.desolidify_engine.settings import Settings, from_params, clamp_settings
from backend.desolidify_engine.engine import perforate_mesh_sdf


def run_preview_mesh(mesh: trimesh.Trimesh, params: Dict[str, Any],
                     progress: Optional[Callable[[float], None]] = None) -> trimesh.Trimesh:
    """
    Coarse/fast run for interactive previews.
    Enforces fast mode regardless of input params.fast.
    """
    s = from_params({**params, "fast": max(1, int(params.get("fast", 1)))})
    # Tighten for preview: smaller chunks (safer) and no mem backoff to keep UI snappy
    s.chunk_pts = max(300_000, int(800_000 / (s._fast_factor or 1)))
    s.mem_retry = True
    s.mem_delay = max(6.0, float(s.mem_delay))
    s = clamp_settings(s)
    return perforate_mesh_sdf(mesh, s, progress=progress)


def run_preview_bytes(stl_bytes: bytes, params: Dict[str, Any]) -> bytes:
    """
    Load STL from bytes, run coarse pass, return STL bytes.
    """
    # Load mesh from memory
    f = io.BytesIO(stl_bytes)
    mesh = trimesh.load(f, file_type="stl")
    if not isinstance(mesh, trimesh.Trimesh):
        mesh = mesh.dump().sum()
    result = run_preview_mesh(mesh, params)
    out = io.BytesIO()
    result.export(out, file_type="stl")
    return out.getvalue()

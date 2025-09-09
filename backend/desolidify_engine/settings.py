# backend/desolidify_engine/settings.py
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional


@dataclass
class Settings:
    # I/O (used by CLI historically; kept for compatibility)
    in_dir: str = "stl"
    out_dir: str = "out"

    # Core lattice controls
    spacing: float = 12.0
    radius: float = 2.5
    voxel: float = 0.3
    orientations: str = "z"
    stagger: bool = True
    zmin: Optional[float] = None
    zmax: Optional[float] = None
    padding: float = 2.0
    shell_band: float = 1.2
    keep_top: float = 1.5
    keep_bottom: float = 0.5
    grid_align: str = "centroid"  # 'min' | 'centroid'
    density: Optional[float] = None
    open_bottom: float = 1.5

    # Memory & speed controls
    chunk_pts: int = 1_500_000
    mem_retry: bool = True
    mem_delay: float = 12.0
    mem_tries: int = 6

    # Internal/transient
    _fast_factor: int = 0  # 0..2

    def copy(self) -> "Settings":
        return Settings(**asdict(self))

    # TODO: integrate richer validation errors when used by API schema.


# Canonical UI/server ranges (mirrors backend/api/schemas.py)
_PARAM_RANGES = {
    "spacing":     {"min": 8.0,  "max": 30.0},
    "radius":      {"min": 1.2,  "max": 5.0},
    "voxel":       {"min": 0.2,  "max": 1.2},
    "shell_band":  {"min": 0.8,  "max": 2.0},
    "keep_top":    {"min": -1.0, "max": 4.0},
    "keep_bottom": {"min": -1.0, "max": 4.0},
    "open_bottom": {"min": 0.0,  "max": 6.0},
    "density":     {"min": 0.02, "max": 0.35},
    "fast":        {"min": 0,    "max": 2},
    "chunk":       {"min": 100_000, "max": 2_500_000},
    "mem_delay":   {"min": 5.0,  "max": 60.0},
    "mem_tries":   {"min": 1,    "max": 10},
}


def _clamp(v, lo=None, hi=None, *, min=None, max=None, **kwargs):
    """Clamp ``v`` between lower/upper bounds.

    Supports both positional ``lo``/``hi`` and keyword ``min``/``max`` styles,
    so callers can unpack dictionaries with those keys (as ``_PARAM_RANGES``
    does).
    """
    if lo is None:
        lo = min
    if hi is None:
        hi = max
    if lo is not None and v < lo:
        v = lo
    if hi is not None and v > hi:
        v = hi
    return v


def clamp_settings(s: Settings) -> Settings:
    s.spacing = float(_clamp(s.spacing, **_PARAM_RANGES["spacing"]))
    s.radius = float(_clamp(s.radius, **_PARAM_RANGES["radius"]))
    s.voxel = float(_clamp(s.voxel, **_PARAM_RANGES["voxel"]))
    s.shell_band = float(_clamp(s.shell_band, **_PARAM_RANGES["shell_band"]))
    s.keep_top = float(_clamp(s.keep_top, **_PARAM_RANGES["keep_top"]))
    s.keep_bottom = float(_clamp(s.keep_bottom, **_PARAM_RANGES["keep_bottom"]))
    s.open_bottom = float(_clamp(s.open_bottom, **_PARAM_RANGES["open_bottom"]))
    if s.density is not None:
        s.density = float(_clamp(s.density, **_PARAM_RANGES["density"]))
    s.chunk_pts = int(_clamp(int(s.chunk_pts), **_PARAM_RANGES["chunk"]))
    s.mem_delay = float(_clamp(float(s.mem_delay), **_PARAM_RANGES["mem_delay"]))
    s.mem_tries = int(_clamp(int(s.mem_tries), **_PARAM_RANGES["mem_tries"]))
    # Enforce web thickness ≥ 2*radius + shell_band
    min_spacing = max(s.spacing, 2.0 * s.radius + s.shell_band)
    s.spacing = float(_clamp(min_spacing, **_PARAM_RANGES["spacing"]))
    return s


def from_params(params: Dict[str, Any]) -> Settings:
    """Construct Settings from a loose dict (API payload), then clamp."""
    s = Settings(
        spacing=float(params.get("spacing", Settings.spacing)),
        radius=float(params.get("radius", Settings.radius)),
        voxel=float(params.get("voxel", Settings.voxel)),
        orientations=str(params.get("orientations", Settings.orientations)),
        stagger=bool(params.get("stagger", Settings.stagger)),
        zmin=params.get("zmin"),
        zmax=params.get("zmax"),
        padding=float(params.get("padding", Settings.padding)),
        shell_band=float(params.get("shell_band", Settings.shell_band)),
        keep_top=float(params.get("keep_top", Settings.keep_top)),
        keep_bottom=float(params.get("keep_bottom", Settings.keep_bottom)),
        grid_align=str(params.get("grid_align", Settings.grid_align)),
        density=(float(params["density"]) if params.get("density") is not None else None),
        open_bottom=float(params.get("open_bottom", Settings.open_bottom)),
        chunk_pts=int(params.get("chunk", Settings.chunk_pts)),
        mem_retry=not bool(params.get("mem_retry_off", False)),
        mem_delay=float(params.get("mem_delay", Settings.mem_delay)),
        mem_tries=int(params.get("mem_tries", Settings.mem_tries)),
        _fast_factor=int(params.get("fast", 0)),
    )
    if s._fast_factor > 0:
        s.voxel = max(s.voxel, 0.6 + 0.3 * int(s._fast_factor))
    return clamp_settings(s)

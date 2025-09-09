# backend/api/schemas.py
from __future__ import annotations

from typing import Any, Dict, Mapping

from backend.desolidify_engine.settings import _clamp

# UI/Server param specification (authoritative ranges + tips)
PARAM_SPECS: Dict[str, Dict[str, Any]] = {
    "spacing":     {"type": "number",  "min": 8.0,  "max": 30.0,  "step": 0.1,
                    "default": 12.0, "tip": "Center-to-center hole spacing (mm). Web must be ≥ 2·radius + shell_band."},
    "radius":      {"type": "number",  "min": 1.2,  "max": 5.0,   "step": 0.1,
                    "default": 2.5,  "tip": "Hole radius (mm). For 0.4mm nozzle keep ≥ 2 perimeters of wall."},
    "voxel":       {"type": "number",  "min": 0.2,  "max": 1.2,   "step": 0.1,
                    "default": 0.3,  "tip": "SDF sampling step (mm). Lower = smoother & slower."},
    "orientations":{"type": "select",  "choices": ["z","x","y","xy","xz","yz","xyz","radial"],
                    "default": "radial", "tip": "Which cylinder families to subtract. 'radial' hugs tapered walls."},
    "stagger":     {"type": "bool",    "default": True,
                    "tip": "Offset every other row by half a spacing."},
    "shell_band":  {"type": "number",  "min": 0.8,  "max": 2.0,   "step": 0.1,
                    "default": 1.2,  "tip": "Only perforate within this thickness from the shell."},
    "keep_top":    {"type": "number",  "min": -1.0, "max": 4.0,   "step": 0.1,
                    "default": 1.0,  "tip": "Keep-out at the rim (mm). Set −1 to allow."},
    "keep_bottom": {"type": "number",  "min": -1.0, "max": 4.0,   "step": 0.1,
                    "default": 0.5,  "tip": "Keep-out near the base (mm)."},
    "open_bottom": {"type": "number",  "min": 0.0,  "max": 6.0,   "step": 0.5,
                    "default": 1.5,  "tip": "Disable shell gating for lowest X mm to punch through."},
    "grid_align":  {"type": "select",  "choices": ["min","centroid"], "default": "centroid",
                    "tip": "Anchor lattice to bounds min or mesh centroid."},
    "density":     {"type": "number",  "min": 0.02, "max": 0.35,  "step": 0.01,
                    "default": None, "tip": "Target open area πr²/s². Adjusts spacing unless both spacing & radius are fixed."},
    "fast":        {"type": "integer", "min": 0,    "max": 2,     "default": 1,
                    "tip": "Preview accelerator (0=off, 1≈0.9mm voxel, 2≈1.2mm voxel)."},
    # memory/safety
    "chunk":       {"type": "integer", "min": 100_000, "max": 2_500_000, "step": 50_000,
                    "default": 1_500_000, "tip": "Max points per signed-distance batch."},
    "mem_delay":   {"type": "number",  "min": 5, "max": 60, "step": 1, "default": 12,
                    "tip": "Seconds to sleep before retry when memory is tight."},
    "mem_tries":   {"type": "integer", "min": 1, "max": 10, "default": 6,
                    "tip": "Total attempts per file under memory pressure."}
}

# -----------------------------------------------------------------------------
# Validation & coercion helpers (server-side clamp)
# -----------------------------------------------------------------------------

_NUMERIC_KEYS = {
    "spacing", "radius", "voxel", "shell_band", "keep_top", "keep_bottom",
    "open_bottom", "density", "mem_delay"
}
_INT_KEYS = {"fast", "chunk", "mem_tries"}
_BOOL_KEYS = {"stagger"}
_SELECT_KEYS = {"orientations", "grid_align"}


def _default_for(key: str):
    spec = PARAM_SPECS.get(key, {})
    return spec.get("default")


def validate_filename_ext(fname: str, allowed: set[str]) -> bool:
    ext = fname.rsplit(".", 1)[-1].lower() if "." in fname else ""
    return ext in {e.lower().lstrip(".") for e in allowed or {"stl"}}


def coerce_and_clamp_params(
    params: Mapping[str, Any] | None,
    *,
    preset_name: str | None = None,
    presets: Mapping[str, Mapping[str, Any]] | None = None,
    force_fast: int | None = None
) -> Dict[str, Any]:
    """
    Merge defaults + optional preset + overrides, then clamp to PARAM_SPECS.
    """
    base: Dict[str, Any] = {k: _default_for(k) for k in PARAM_SPECS.keys()}

    # Apply preset if given
    if preset_name and presets and preset_name in presets:
        for k, v in dict(presets[preset_name]).items():
            if k in base:
                base[k] = v

    # Apply explicit overrides
    if params:
        for k, v in params.items():
            if k not in PARAM_SPECS:
                continue
            base[k] = v

    # Force-fast preview if requested
    if isinstance(force_fast, int):
        base["fast"] = int(force_fast)

    # Coerce & clamp
    out: Dict[str, Any] = {}
    for k, spec in PARAM_SPECS.items():
        if k not in base:
            continue
        v = base[k]

        if k in _NUMERIC_KEYS:
            if v is None:
                out[k] = None
            else:
                try:
                    vv = float(v)
                except Exception:
                    vv = float(_default_for(k))
                out[k] = _clamp(vv, **spec)
        elif k in _INT_KEYS:
            try:
                vv = int(v)
            except Exception:
                vv = int(_default_for(k))
            out[k] = int(_clamp(vv, **spec))
        elif k in _BOOL_KEYS:
            out[k] = bool(v)
        elif k in _SELECT_KEYS:
            choices = spec.get("choices", [])
            vv = str(v) if v is not None else str(_default_for(k))
            out[k] = vv if vv in choices else spec.get("default")
        else:
            out[k] = v

    # Derived constraint: web thickness ≥ 2*radius + shell_band -> adjust spacing if needed
    try:
        radius = float(out.get("radius", _default_for("radius")) or 0.0)
        shell_band = float(out.get("shell_band", _default_for("shell_band")) or 0.0)
        spacing = float(out.get("spacing", _default_for("spacing")) or 0.0)
        min_spacing = max(spacing, 2.0 * radius + shell_band)
        if spacing < min_spacing:
            out["spacing"] = _clamp(min_spacing, **PARAM_SPECS["spacing"])
    except Exception:
        pass

    return out

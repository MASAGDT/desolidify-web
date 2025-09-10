# backend/api/meta.py
from __future__ import annotations

from flask import jsonify

from .schemas import PARAM_SPECS


def register_meta_routes(bp):
    @bp.get("/meta/presets")
    def get_presets():
        # Try loading from engine presets; fallback to inline subset
        try:
            from backend.desolidify_engine.presets import PRESETS_DEFAULT  # type: ignore
            presets = PRESETS_DEFAULT
        except Exception:
            presets = _fallback_presets()
        return jsonify(presets)

    @bp.get("/meta/params")
    def get_params():
        return jsonify(PARAM_SPECS)


def _fallback_presets():
    return {
        "Quick Uniform Z — 2.5mm (Best Run)": {
            "spacing": 12.0,
            "radius": 2.5,
            "voxel": 0.3,
            "orientations": "z",
            "stagger": True,
            "shell_band": 1.2,
            "keep_top": 1.5,
            "keep_bottom": -1.0,
            "grid_align": "centroid",
            "density": 0.10,
            "open_bottom": 3.0,
        }
    }

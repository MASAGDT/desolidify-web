# backend/desolidify_engine/presets.py
from __future__ import annotations

# Mirrors CLI 1.2.5 defaults
PRESETS_DEFAULT = {
    "Quick Uniform Z — 2.5mm (Best Run)": {
        "spacing": 12.0, "radius": 2.5, "voxel": 0.3,
        "orientations": "z", "stagger": True,
        "shell_band": 1.2, "keep_top": 1.5, "keep_bottom": -1.0,
        "grid_align": "centroid", "density": 0.10, "open_bottom": 3.0
    },
    "Quick Uniform Z — 3.0mm (Sparse)": {
        "spacing": 14.0, "radius": 3.0, "voxel": 0.3,
        "orientations": "z", "stagger": True,
        "shell_band": 1.2, "keep_top": 1.5, "keep_bottom": -1.0,
        "grid_align": "centroid", "density": 0.08, "open_bottom": 3.0
    },
    "Quick Radial — 2.5mm": {
        "spacing": 12.0, "radius": 2.5, "voxel": 0.3,
        "orientations": "radial", "stagger": True,
        "shell_band": 1.2, "keep_top": 1.5, "keep_bottom": -1.0,
        "grid_align": "centroid", "density": 0.09, "open_bottom": 1.5
    },
    "Plant Dose Insert — Controlled": {
        "spacing": 14.0, "radius": 2.2, "voxel": 0.3,
        "orientations": "radial", "stagger": True,
        "shell_band": 1.2, "keep_top": 1.0, "keep_bottom": 0.5,
        "grid_align": "centroid", "density": 0.08, "open_bottom": 1.5
    },
    "Plant Dose Insert — High Flow": {
        "spacing": 16.0, "radius": 2.0, "voxel": 0.3,
        "orientations": "radial", "stagger": True,
        "shell_band": 1.2, "keep_top": 1.0, "keep_bottom": 0.5,
        "grid_align": "centroid", "density": 0.12, "open_bottom": 1.5
    }
}

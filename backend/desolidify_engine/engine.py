# backend/desolidify_engine/engine.py
from __future__ import annotations

import gc
import math
import time
from pathlib import Path
from typing import Callable, Iterable, List, Optional, Tuple

import numpy as np
import trimesh
from skimage.measure import marching_cubes

from backend.desolidify_engine.settings import Settings

# -----------------------------------------------------------------------------
# Mesh I/O
# -----------------------------------------------------------------------------

def load_mesh_any(path: Path) -> trimesh.Trimesh:
    m = trimesh.load_mesh(str(path))
    if isinstance(m, trimesh.Trimesh):
        return m
    if hasattr(m, "dump"):
        geoms = list(m.dump().geometry.values())
        if not geoms:
            raise ValueError(f"No geometry in: {path}")
        return trimesh.util.concatenate(geoms)
    raise ValueError(f"Unsupported container for: {path}")


# -----------------------------------------------------------------------------
# Grid helpers
# -----------------------------------------------------------------------------

def _start_aligned(a_min: float, spacing: float, anchor: Optional[float], align: str) -> float:
    if align.lower().startswith("cent"):
        if anchor is None:
            return a_min + spacing * 0.5
        return a_min + (spacing * 0.5) + float(np.mod(anchor - a_min, spacing))
    return a_min


def _grid_centers_xy(xmin, xmax, ymin, ymax, spacing, stagger,
                     align: str = "min",
                     anchor_xy: Optional[Tuple[float, float]] = None) -> np.ndarray:
    sx = _start_aligned(xmin, spacing, None if anchor_xy is None else anchor_xy[0], align)
    sy = _start_aligned(ymin, spacing, None if anchor_xy is None else anchor_xy[1], align)
    cx = np.arange(sx, xmax + 1e-6, spacing, dtype=np.float32)
    cy = np.arange(sy, ymax + 1e-6, spacing, dtype=np.float32)
    if stagger and len(cy) > 1:
        offsets = np.where((np.arange(len(cy)) % 2) == 1, spacing * 0.5, 0.0).astype(np.float32)
        centers = np.column_stack([np.tile(cx, len(cy)) + np.repeat(offsets, len(cx)),
                                   np.repeat(cy, len(cx))])
    else:
        centers = np.array([(x, y) for y in cy for x in cx], dtype=np.float32)
    return centers


def _grid_min_cyl_sdf_xy(xs: np.ndarray, ys: np.ndarray,
                         centers: np.ndarray, radius: float) -> np.ndarray:
    if centers.size == 0:
        return np.full((len(ys), len(xs)), np.inf, dtype=np.float32)
    XX, YY = np.meshgrid(xs, ys, indexing='xy')
    dx = XX[..., None] - centers[:, 0]
    dy = YY[..., None] - centers[:, 1]
    d = np.sqrt(dx * dx + dy * dy) - radius
    return np.min(d, axis=2).astype(np.float32)


def sdf_cylinders_Z(xs, ys, xmin, xmax, ymin, ymax, spacing, radius, stagger,
                    align: str = "min",
                    anchor_xy: Optional[Tuple[float, float]] = None):
    centers = _grid_centers_xy(xmin, xmax, ymin, ymax, spacing, stagger, align, anchor_xy)
    return _grid_min_cyl_sdf_xy(xs, ys, centers, radius)


def sdf_cylinders_X(ys, zs, ymin, ymax, zmin, zmax, spacing, radius, stagger):
    cy = np.arange(ymin, ymax + 1e-6, spacing, dtype=np.float32)
    cz = np.arange(zmin, zmax + 1e-6, spacing, dtype=np.float32)
    if stagger and len(cy) > 1:
        offsets = np.where((np.arange(len(cy)) % 2) == 1, spacing * 0.5, 0.0).astype(np.float32)
        centers = np.column_stack([np.tile(cy, len(cz)),
                                   np.repeat(cz, len(cy)) + np.repeat(offsets, len(cz))])
    else:
        centers = np.array([(y, z) for z in cz for y in cy], dtype=np.float32)
    ZV, YV = np.meshgrid(zs, ys, indexing='xy')
    dy = YV.T[..., None] - centers[:, 0]
    dz = ZV.T[..., None] - centers[:, 1]
    d = np.sqrt(dy * dy + dz * dz) - radius
    return np.min(d, axis=2).astype(np.float32)


def sdf_cylinders_Y(xs, zs, xmin, xmax, zmin, zmax, spacing, radius, stagger):
    cx = np.arange(xmin, xmax + 1e-6, spacing, dtype=np.float32)
    cz = np.arange(zmin, zmax + 1e-6, spacing, dtype=np.float32)
    if stagger and len(cx) > 1:
        offsets = np.where((np.arange(len(cx)) % 2) == 1, spacing * 0.5, 0.0).astype(np.float32)
        centers = np.column_stack([np.tile(cx, len(cz)),
                                   np.repeat(cz, len(cx)) + np.repeat(offsets, len(cz))])
    else:
        centers = np.array([(x, z) for z in cz for x in cx], dtype=np.float32)
    ZV, XV = np.meshgrid(zs, xs, indexing='xy')
    dx = XV.T[..., None] - centers[:, 0]
    dz = ZV.T[..., None] - centers[:, 1]
    d = np.sqrt(dx * dx + dz * dz) - radius
    return np.min(d, axis=2).astype(np.float32)


def sdf_cylinders_RADIAL_prep(xs: np.ndarray, ys: np.ndarray,
                              xmin: float, xmax: float, ymin: float, ymax: float,
                              spacing: float, stagger: bool,
                              cx0: float, cy0: float,
                              align: str = "min") -> np.ndarray:
    centers = _grid_centers_xy(xmin, xmax, ymin, ymax, spacing, stagger,
                               align=align, anchor_xy=(cx0, cy0))
    if centers.size == 0:
        return np.full((len(ys), len(xs)), np.inf, dtype=np.float32)
    v = centers - np.array([cx0, cy0], dtype=np.float32)
    norms = np.linalg.norm(v, axis=1, keepdims=True)
    norms = np.where(norms == 0.0, 1.0, norms)
    v = v / norms
    vx = v[:, 0]
    vy = v[:, 1]
    XX, YY = np.meshgrid(xs, ys, indexing='xy')
    dx = XX[..., None] - centers[:, 0]
    dy = YY[..., None] - centers[:, 1]
    perp = np.abs(dx * vy - dy * vx).astype(np.float32)
    return np.min(perp * perp, axis=2).astype(np.float32)


# -----------------------------------------------------------------------------
# Core algorithm (memory-resilient wrapper + single attempt)
# -----------------------------------------------------------------------------

def _perforate_once(mesh: trimesh.Trimesh, s: Settings,
                    progress: Optional[Callable[[float], None]]) -> trimesh.Trimesh:
    # rtree required for signed_distance
    try:
        import rtree  # noqa: F401
    except Exception as e:
        raise RuntimeError(
            "rtree missing. Install with 'pip install rtree' "
            "(Ubuntu: apt-get install libspatialindex-dev, macOS: brew install spatialindex)."
        ) from e

    m = mesh.copy()
    m.remove_unreferenced_vertices()
    m.process(validate=True)

    bmin, bmax = m.bounds
    xmin, ymin, zmin = (bmin - s.padding).astype(np.float32)
    xmax, ymax, zmax = (bmax + s.padding).astype(np.float32)

    centroid = m.centroid.astype(np.float32)
    cx0, cy0, cz0 = centroid

    if s.zmin is not None:
        zmin = max(zmin, float(s.zmin) - s.padding)
    if s.zmax is not None:
        zmax = min(zmax, float(s.zmax) + s.padding)

    xs = np.arange(xmin, xmax, s.voxel, dtype=np.float32)
    ys = np.arange(ymin, ymax, s.voxel, dtype=np.float32)
    zs = np.arange(zmin, zmax, s.voxel, dtype=np.float32)

    nx, ny, nz = len(xs), len(ys), len(zs)
    if nx < 2 or ny < 2 or nz < 2:
        raise ValueError("Sampling grid too small. Decrease voxel or check model scale.")

    o = s.orientations.lower()
    want_x = ('x' in o)
    want_y = ('y' in o)
    want_z = ('z' in o)
    want_rad = ('radial' in o)

    cyl_xy = sdf_cylinders_Z(xs, ys, xmin, xmax, ymin, ymax,
                             s.spacing, s.radius, s.stagger,
                             align=s.grid_align, anchor_xy=(cx0, cy0)) if want_z else None
    cyl_zy = sdf_cylinders_X(ys, zs, ymin, ymax, zmin, zmax,
                             s.spacing, s.radius, s.stagger) if want_x else None
    cyl_zx = sdf_cylinders_Y(xs, zs, xmin, xmax, zmin, zmax,
                             s.spacing, s.radius, s.stagger) if want_y else None

    radial_min_perp_sq = None
    dz_min_sq_by_k = None
    if want_rad:
        radial_min_perp_sq = sdf_cylinders_RADIAL_prep(
            xs, ys, xmin, xmax, ymin, ymax, s.spacing, s.stagger, cx0, cy0, align=s.grid_align
        )
        z_start = _start_aligned(zmin, s.spacing, cz0, s.grid_align)
        z_rows = np.arange(z_start, zmax + 1e-6, s.spacing, dtype=np.float32)
        dz_min_sq_by_k = np.array([np.min((zk - z_rows) ** 2) for zk in zs], dtype=np.float32)

    volume = np.empty((nz, ny, nx), dtype=np.float32)
    XX, YY = np.meshgrid(xs, ys, indexing='xy')

    top_guard = (zmax - s.keep_top)
    bot_guard = (zmin + s.keep_bottom)

    for k, z in enumerate(zs):
        # Build points in CHUNKS to keep mem bounded
        N = XX.size
        sd_flat = np.empty(N, dtype=np.float32)
        start = 0
        while start < N:
            end = min(start + int(s.chunk_pts), N)
            chunk_len = end - start
            pts = np.empty((chunk_len, 3), dtype=np.float32)
            flat_x = XX.ravel(order='C')[start:end]
            flat_y = YY.ravel(order='C')[start:end]
            pts[:, 0] = flat_x
            pts[:, 1] = flat_y
            pts[:, 2] = z
            sd_chunk = trimesh.proximity.signed_distance(m, pts).astype(np.float32, copy=False)
            sd_flat[start:end] = sd_chunk
            start = end
            del pts, sd_chunk
            gc.collect()

        sdf_mesh = (-sd_flat.reshape((ny, nx))).astype(np.float32)

        parts: List[np.ndarray] = []
        if cyl_xy is not None:
            parts.append(cyl_xy)
        if cyl_zy is not None:
            parts.append(cyl_zy[k][:, None].repeat(nx, axis=1))
        if cyl_zx is not None:
            parts.append(cyl_zx[k][None, :].repeat(ny, axis=0))
        if radial_min_perp_sq is not None:
            dz_sq = float(dz_min_sq_by_k[k])
            parts.append(np.sqrt(radial_min_perp_sq + dz_sq).astype(np.float32) - s.radius)

        if parts:
            sdf_holes = parts[0]
            for p in parts[1:]:
                sdf_holes = np.minimum(sdf_holes, p)
        else:
            sdf_holes = np.full_like(sdf_mesh, np.inf, dtype=np.float32)

        # Shell-band gating (skip near base if open_bottom window active)
        if s.shell_band is not None and s.shell_band > 0:
            near_base_window = (s.open_bottom > 0 and z <= (float(bmin[2]) + s.open_bottom))
            if not near_base_window:
                mask_shell = (np.abs(sdf_mesh) <= s.shell_band)
                sdf_holes = np.where(mask_shell, sdf_holes, np.inf)

        if (z >= top_guard) or (z <= bot_guard):
            sdf_holes[:] = np.inf

        volume[k] = np.maximum(sdf_mesh, -sdf_holes)

        if progress:
            progress((k + 1) / nz)

        del sd_flat, sdf_mesh, sdf_holes
        gc.collect()

    verts, faces, _, _ = marching_cubes(volume, level=0.0,
                                        spacing=(s.voxel, s.voxel, s.voxel))
    verts_world = np.column_stack([verts[:, 2] + xmin, verts[:, 1] + ymin, verts[:, 0] + zmin])

    out = trimesh.Trimesh(vertices=verts_world, faces=faces, process=False)
    out.remove_unreferenced_vertices()
    out.process(validate=True)
    try:
        out.fix_normals()
    except Exception:
        pass
    return out


def perforate_mesh_sdf(mesh: trimesh.Trimesh, s: Settings,
                       progress: Optional[Callable[[float], None]] = None) -> trimesh.Trimesh:
    """Memory-resilient wrapper around _perforate_once with backoff & retries."""
    attempt = 0
    voxel0 = float(s.voxel)
    last_err = None
    while attempt < max(1, int(s.mem_tries)):
        try:
            return _perforate_once(mesh, s, progress)
        except (MemoryError, np.core._exceptions._ArrayMemoryError) as e:  # type: ignore[attr-defined]
            last_err = e
            attempt += 1
            if not s.mem_retry or attempt >= int(s.mem_tries):
                raise
            # Backoffs
            s.chunk_pts = max(250_000, int(s.chunk_pts * 0.65))
            s.voxel = min(max(voxel0, s.voxel * 1.10), voxel0 * 1.8)
            gc.collect()
            time.sleep(float(s.mem_delay))
        except Exception as e:
            raise
    raise last_err  # pragma: no cover

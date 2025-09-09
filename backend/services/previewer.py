# backend/services/previewer.py
from __future__ import annotations

import io
from typing import Tuple

# Optional dependencies
try:
    import numpy as np
    import trimesh
    import pyrender
    from PIL import Image
except Exception:  # pragma: no cover
    np = None  # type: ignore
    trimesh = None  # type: ignore
    pyrender = None  # type: ignore
    Image = None  # type: ignore


def stl_to_png_bytes(stl_bytes: bytes, size: Tuple[int, int] = (800, 600), background=(255, 255, 255, 0)) -> bytes:
    """
    Render an STL (bytes) to a PNG snapshot and return PNG bytes.
    If preview stack is unavailable, raises RuntimeError.
    """
    if any(x is None for x in (np, trimesh, pyrender, Image)):
        raise RuntimeError("Preview stack not available (requires numpy, trimesh, pyrender, Pillow).")

    mesh = trimesh.load(io.BytesIO(stl_bytes), file_type="stl")
    if not isinstance(mesh, trimesh.Trimesh):
        mesh = mesh.dump().sum()

    scene = pyrender.Scene(bg_color=background, ambient_light=(0.3, 0.3, 0.3, 1.0))
    tri = pyrender.Mesh.from_trimesh(mesh, smooth=True)
    scene.add(tri)

    # Lights
    light = pyrender.DirectionalLight(color=[1.0, 1.0, 1.0], intensity=3.0)
    scene.add(light)
    # Camera
    centroid = mesh.centroid
    extents = float(mesh.extents.max()) if hasattr(mesh.extents, "max") else float(mesh.extents)
    dist = max(1.5 * extents, 1.0)
    camera = pyrender.PerspectiveCamera(yfov=np.deg2rad(45.0))
    cam_node = scene.add(camera, pose=_look_at(centroid + [dist, dist, dist], centroid))
    try:
        r = pyrender.OffscreenRenderer(viewport_width=size[0], viewport_height=size[1])
        color, _ = r.render(scene)
    finally:
        try:
            r.delete()
        except Exception:
            pass
        scene.remove_node(cam_node)

    img = Image.fromarray(color, mode="RGBA")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _look_at(eye, target, up=(0, 0, 1)):
    """
    Build a 4x4 look-at pose matrix for pyrender.
    """
    eye = np.array(eye, dtype=float)
    target = np.array(target, dtype=float)
    up = np.array(up, dtype=float)

    z = eye - target
    z = z / (np.linalg.norm(z) + 1e-9)
    x = np.cross(up, z)
    x = x / (np.linalg.norm(x) + 1e-9)
    y = np.cross(z, x)

    m = np.eye(4, dtype=float)
    m[:3, 0] = x
    m[:3, 1] = y
    m[:3, 2] = z
    m[:3, 3] = eye
    return m

# backend/api/jobs.py
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from flask import current_app, request, jsonify, send_file, url_for
from werkzeug.utils import secure_filename

from .errors import api_error
from .schemas import coerce_and_clamp_params, validate_filename_ext


def register_job_routes(bp):
    # -------------------------------------------------------------------------
    # POST /api/jobs  → create job, save upload, enqueue
    # -------------------------------------------------------------------------
    @bp.post("/jobs")
    def create_job():
        if "file" not in request.files:
            return api_error(400, "Missing file field 'file'")

        f = request.files["file"]
        if not f or f.filename == "":
            return api_error(400, "Empty filename")

        filename = secure_filename(f.filename)
        if not validate_filename_ext(filename, current_app.config.get("ALLOWED_EXTENSIONS", {"stl"})):
            return api_error(400, "Unsupported file extension")

        # Parse params (JSON string in multipart 'params') and optional preset
        raw_params: Dict[str, Any] = {}
        if "params" in request.form and request.form["params"].strip():
            try:
                raw_params = json.loads(request.form["params"])
            except Exception:
                return api_error(400, "Invalid JSON in 'params'")

        preset_name = request.form.get("preset") or None

        # Create a new job folder & save artifacts via storage service
        try:
            # Lazy import to avoid hard dependency before services are scaffolded
            from ..services.storage import new_job, save_upload, write_params, set_status  # type: ignore
        except Exception:
            return api_error(503, "Storage service not ready (scaffold phase)")

        job_id = new_job()
        try:
            save_upload(job_id, f, filename_hint=filename)
        except Exception as e:
            return api_error(500, f"Failed to store upload: {e}")

        # Resolve presets (optional) and clamp parameters
        try:
            # Try to import real presets; fallback to built-ins if engine not present yet
            try:
                from ..desolidify_engine.presets import PRESETS_DEFAULT  # type: ignore
            except Exception:
                PRESETS_DEFAULT = _fallback_presets()
            params = coerce_and_clamp_params(raw_params, preset_name=preset_name, presets=PRESETS_DEFAULT)
            write_params(job_id, params)
        except Exception as e:
            return api_error(400, f"Invalid parameters: {e}")

        # Queue the work
        try:
            from ..services.queue import submit_perforate  # type: ignore
        except Exception:
            # Mark as queued but not actually submitted (scaffold phase)
            set_status(job_id, state="queued", progress=0.0, message="Queue not available yet.")
            task_id = None
        else:
            task_id = submit_perforate(job_id, params)

        set_status(job_id, state="queued", progress=0.0, message="Job enqueued.")

        return jsonify(
            {
                "job_id": job_id,
                "task_id": task_id,
                "status_url": url_for("api.get_job", job_id=job_id, _external=True),
                "result_url": url_for("api.get_job_result", job_id=job_id, _external=True),
                "ws_room": f"job:{job_id}",
            }
        ), 202

    # -------------------------------------------------------------------------
    # GET /api/jobs/<id> → status
    # -------------------------------------------------------------------------
    @bp.get("/jobs/<job_id>")
    def get_job(job_id: str):
        try:
            from ..services.storage import get_status  # type: ignore
        except Exception:
            return jsonify({"job_id": job_id, "state": "unknown", "progress": 0.0, "message": "Storage not ready"}), 503

        status = get_status(job_id)
        if not status:
            return api_error(404, "Job not found")

        return jsonify({"job_id": job_id, **status})

    # -------------------------------------------------------------------------
    # GET /api/jobs/<id>/result → output STL
    # -------------------------------------------------------------------------
    @bp.get("/jobs/<job_id>/result")
    def get_job_result(job_id: str):
        jobs_root = Path(current_app.config["JOBS_ROOT"]).resolve()
        out_path = jobs_root / job_id / "output.stl"
        if not out_path.exists():
            # Not ready yet
            try:
                from ..services.storage import get_status  # type: ignore
                st = get_status(job_id) or {}
            except Exception:
                st = {}
            return jsonify({"job_id": job_id, "ready": False, **st}), 202

        return send_file(out_path, mimetype="model/stl", as_attachment=True, download_name=f"{job_id}_desolid.stl")

    # -------------------------------------------------------------------------
    # POST /api/preview → quick coarse pass (returns STL)
    # -------------------------------------------------------------------------
    @bp.post("/preview")
    def preview_job():
        if "file" not in request.files:
            return api_error(400, "Missing file field 'file'")
        f = request.files["file"]
        if not f or f.filename == "":
            return api_error(400, "Empty filename")
        filename = secure_filename(f.filename)
        if not validate_filename_ext(filename, current_app.config.get("ALLOWED_EXTENSIONS", {"stl"})):
            return api_error(400, "Unsupported file extension")

        raw_params: Dict[str, Any] = {}
        if "params" in request.form and request.form["params"].strip():
            try:
                raw_params = json.loads(request.form["params"])
            except Exception:
                return api_error(400, "Invalid JSON in 'params'")

        preset_name = request.form.get("preset") or None

        # Clamp params
        try:
            try:
                from ..desolidify_engine.presets import PRESETS_DEFAULT  # type: ignore
            except Exception:
                PRESETS_DEFAULT = _fallback_presets()
            params = coerce_and_clamp_params(raw_params, preset_name=preset_name, presets=PRESETS_DEFAULT, force_fast=2)
        except Exception as e:
            return api_error(400, f"Invalid parameters: {e}")

        # Run preview (in-process, coarse)
        try:
            # Lazy import preview helper (to be provided in backend/desolidify_engine/preview.py)
            from ..desolidify_engine.preview import run_preview_bytes  # type: ignore
        except Exception:
            return api_error(501, "Preview engine not available yet (scaffold phase).")

        try:
            data = f.read()
            stl_bytes = run_preview_bytes(data, params)
            return current_app.response_class(stl_bytes, mimetype="model/stl")
        except Exception as e:
            return api_error(500, f"Preview failed: {e}")


# -----------------------------------------------------------------------------
# Local helpers
# -----------------------------------------------------------------------------

def _fallback_presets() -> Dict[str, Dict[str, Any]]:
    # Mirrors CLI 1.2.5 defaults (subset sufficient for UI boot)
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
        },
        "Quick Uniform Z — 3.0mm (Sparse)": {
            "spacing": 14.0,
            "radius": 3.0,
            "voxel": 0.3,
            "orientations": "z",
            "stagger": True,
            "shell_band": 1.2,
            "keep_top": 1.5,
            "keep_bottom": -1.0,
            "grid_align": "centroid",
            "density": 0.08,
            "open_bottom": 3.0,
        },
        "Quick Radial — 2.5mm": {
            "spacing": 12.0,
            "radius": 2.5,
            "voxel": 0.3,
            "orientations": "radial",
            "stagger": True,
            "shell_band": 1.2,
            "keep_top": 1.5,
            "keep_bottom": -1.0,
            "grid_align": "centroid",
            "density": 0.09,
            "open_bottom": 1.5,
        },
    }

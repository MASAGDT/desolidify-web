# desolidify-web

Flask + React web app for SDF-based lattice perforation of STL models.

> Backend provides `/api/*` for job upload/processing + progress.
> Frontend bundles to `/frontend/public/assets/app.js` and is served by Flask.

---

## Quick Start (Docker)

```bash
# 1) Build
docker build -t desolidify-web .

# 2) Run (mount a host jobs folder if desired)
docker run --rm -it   -p 5000:5000   -e SECRET_KEY=change-me   -e MAX_WORKERS=1   -v "$PWD/jobs:/app/jobs"   --name desolidify desolidify-web

# Open http://localhost:5000
```

Environment variables are documented in `.env.example`. You can pass `--env-file .env` to `docker run`.

---

## Local Dev (Python + esbuild)

```bash
# Backend (Python 3.11)
python -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt

# Frontend (build once; re-run on changes)
npm -g i esbuild
esbuild frontend/src/App.jsx --bundle --format=esm --sourcemap   --outfile=frontend/public/assets/app.js --loader:.jsx=jsx
cp frontend/src/styles.css frontend/public/assets/styles.css

# Run Flask dev server
export FLASK_APP=backend.wsgi
export FLASK_ENV=development
flask run --host 0.0.0.0 --port 5000
```

> **Note:** Vendor modules (`three` + `STLLoader`) are loaded via ESM CDN and do not require bundling.

---

## API Overview

- `GET /api/health` → service health
- `GET /api/meta/presets` → presets dictionary
- `GET /api/meta/params` → UI parameter specs
- `POST /api/jobs` (multipart):
  - `file`: `.stl` upload
  - `params`: JSON settings override
  - `preset`: optional preset name
  - → `202 Accepted { job_id, status_url, result_url, ws_room }`
- `GET /api/jobs/<id>` → `{state, progress, message}`
- `GET /api/jobs/<id>/result` → STL (or `202` if not ready)
- `POST /api/preview` (multipart) → coarse preview STL

---

## Project Layout

```
desolidify-web/
├── backend/
│   ├── app.py
│   ├── config.py
│   ├── wsgi.py
│   ├── requirements.txt
│   ├── desolidify_engine/
│   ├── api/
│   ├── services/
│   └── tasks/
├── frontend/
│   ├── public/
│   ├── src/
│   └── vendor/three/
├── jobs/
├── .env.example
├── Dockerfile
└── README.md
```

---

## Operational Notes

- **Memory safety:** Engine performs chunked signed-distance queries with backoff/retries.
- **Retention:** `flask purge-jobs --hours 6` cleans old job folders.
- **WebSockets:** Progress emits to room `job:<id>` when Socket.IO client is wired (TODO in `src/api.js`).
- **Preview rendering:** Optional PNG snapshot via `backend/services/previewer.py` (requires `pyrender`).

---

## TODO

- Socket.IO client join/leave room in the frontend.
- Auth/session hardening (production).
- Upload rate limiting & virus scanning.
- Unit tests & CI.
- Add favicon/manifest and persistent settings storage.

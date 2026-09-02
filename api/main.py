"""Point d'entrée FastAPI -- expose le moteur ligue1sim (intact) au frontend,
et sert le frontend buildé (ui/dist) sur le même port/origine.

Lancement (dev, avec rechargement à chaud du frontend séparé) :
  uv run uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
  cd ui && npm run dev
Lancement (accès stable partagé, un seul port -- voir "Lancer l'appli.bat") :
  cd ui && npm run build
  uv run uvicorn api.main:app --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from api.routers import competitions, leagues

app = FastAPI(title="Simulafoot API")

# CORS large en dev seulement (frontend Vite sur un autre port pendant le
# développement) -- sans effet une fois le frontend buildé et servi par ce
# même serveur (même origine, CORS non sollicité).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(leagues.router, prefix="/api")
app.include_router(competitions.router, prefix="/api")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


# --- Frontend buildé (ui/dist) -- absent en dev pur (npm run dev séparé sur
# le port 5173), présent après `npm run build` pour l'accès partagé stable.
_DIST_DIR = Path(__file__).resolve().parent.parent / "ui" / "dist"

if _DIST_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=_DIST_DIR / "assets"), name="assets")

    # Catch-all APRÈS les routes /api -- sert index.html pour toute route
    # côté client (react-router) qui ne correspond pas à un fichier statique
    # réel (icônes, manifest.json, sw.js...), indispensable pour qu'un accès
    # direct/rechargement sur une URL profonde (ex. /competition/xyz/simulate)
    # fonctionne au lieu de 404.
    @app.get("/{full_path:path}")
    def spa(full_path: str) -> FileResponse:
        candidate = _DIST_DIR / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(_DIST_DIR / "index.html")

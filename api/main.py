"""Point d'entrée FastAPI -- expose le moteur ligue1sim (intact) au frontend,
et sert le frontend buildé (ui/dist) sur le même port/origine.

Lancement (dev, avec rechargement à chaud du frontend séparé) :
  uv run uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
  cd ui && npm run dev
Lancement (accès stable partagé, un seul port -- voir "simulafoot.bat") :
  cd ui && npm run build
  uv run uvicorn api.main:app --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from ligue1sim.faces import FACES_DIR

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

# Ticket 4 (optimisation 1) : gzip des réponses de plus de 1 000 octets (payload
# d'animation : ~14 Mo -> ~2 Mo). Les navigateurs décompressent nativement.
app.add_middleware(GZipMiddleware, minimum_size=1000)

app.include_router(leagues.router, prefix="/api")
app.include_router(competitions.router, prefix="/api")

# Photos de joueurs (voir ligue1sim.faces) -- non versionnées, absentes tant
# que scripts/extract_faces.py n'a pas tourné localement. Chemin distinct de
# /assets (déjà pris par le build du frontend, voir plus bas).
if FACES_DIR.is_dir():
    app.mount("/media/faces", StaticFiles(directory=FACES_DIR), name="faces")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


# Lecteur d'animation embarqué dans la PWA via <iframe> (docs/
# canvas_integration_state.md §2.11) : on sert l'unique fichier
# render/canvas.html tel quel (source unique, aucune copie dans ui/), jamais
# le dossier render/ en entier (les previews générées n'ont rien à faire là).
_CANVAS_HTML = Path(__file__).resolve().parent.parent / "render" / "canvas.html"


@app.get("/render/canvas.html", include_in_schema=False)
def canvas_player() -> FileResponse:
    return FileResponse(_CANVAS_HTML, media_type="text/html; charset=utf-8", headers={"Cache-Control": "no-cache"})


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

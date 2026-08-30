"""Point d'entrée FastAPI -- expose le moteur ligue1sim (intact) au frontend.

Lancement : uv run uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import competitions, leagues

app = FastAPI(title="Simulafoot API")

# CORS large en dev seulement (frontend Vite sur un autre port, test depuis
# le téléphone via l'IP locale du PC) -- à restreindre avant tout
# déploiement public au-delà du réseau local.
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

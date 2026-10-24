"""Route API de la V2 (docs/TRD_V2.md, D-V01) : lance un match isolé et renvoie sa trace
complète (positions à chaque instant échantillonné + buts horodatés) au frontend, qui la rejoue.
Entièrement séparée des routes V1 (`leagues.py`, `competitions.py`) -- réutilise seulement, en
lecture seule, le chargement des clubs déjà exposé par `/api/clubs` côté frontend (pas besoin
d'une route de listing dédiée ici)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ligue1sim.clubs import load_all_clubs
from ligue1sim.season import CLUBS_PATH

from v2engine.match import simulate_match

router = APIRouter(prefix="/v2", tags=["v2"])

# Granularité du calcul physique et sous-échantillonnage de la trace enregistrée -- mesuré sur
# pipeline réel (24/10/2026) : ~26 s pour un match complet de 90 minutes, ~5 100 ticks
# enregistrés. ponytail : pas optimisé (collision O(n²), voir v2engine/match.py) -- à revoir si
# ça devient gênant à l'usage.
_TICK_SECONDS = 0.15
_RECORD_EVERY = 7


class SimulateV2Request(BaseModel):
    home: str
    away: str


class PlayerSnapshotOut(BaseModel):
    name: str
    team: str
    poste: str
    x: float
    y: float


class BallSnapshotOut(BaseModel):
    x: float
    y: float


class TickOut(BaseModel):
    minute: float
    players: list[PlayerSnapshotOut]
    ball: BallSnapshotOut


class GoalEventOut(BaseModel):
    minute: float
    team: str


class MatchTraceOut(BaseModel):
    home: str
    away: str
    tick_seconds: float
    home_goals: int
    away_goals: int
    goals: list[GoalEventOut]
    ticks: list[TickOut]


def _find_club(name: str):
    """`load_all_clubs` renvoie des `ClubOption` (résumé léger pour un sélecteur) -- `.as_club()`
    donne le `Club` complet (effectif) qu'attend `simulate_match`."""
    for option in load_all_clubs(CLUBS_PATH):
        if option.name == name:
            return option.as_club()
    raise HTTPException(status_code=404, detail=f"Club introuvable : {name!r}")


@router.post("/matches", response_model=MatchTraceOut)
def create_match(payload: SimulateV2Request) -> MatchTraceOut:
    home_club = _find_club(payload.home)
    away_club = _find_club(payload.away)
    trace = simulate_match(home_club, away_club, duration_minutes=90.0, tick_seconds=_TICK_SECONDS, record_every=_RECORD_EVERY)

    return MatchTraceOut(
        home=trace.home,
        away=trace.away,
        tick_seconds=trace.tick_seconds,
        home_goals=trace.home_goals,
        away_goals=trace.away_goals,
        goals=[GoalEventOut(minute=g.minute, team=g.team) for g in trace.goals],
        ticks=[
            TickOut(
                minute=tick.minute,
                players=[
                    PlayerSnapshotOut(name=p.name, team=p.team, poste=p.poste, x=p.position.x, y=p.position.y)
                    for p in tick.players
                ],
                ball=BallSnapshotOut(x=tick.ball.position.x, y=tick.ball.position.y),
            )
            for tick in trace.ticks
        ],
    )

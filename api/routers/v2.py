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
from v2engine.trace import MatchTrace

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


class IntentionSegmentOut(BaseModel):
    """Intention d'un joueur à partir de `minute`, jusqu'au segment suivant (ADR 0001). Un segment ne commence
    que quand le rôle, l'action ou le joueur visé change, pour garder la réponse légère ; la raison n'a donc pas
    de chiffre (la distance varie à chaque instant)."""
    minute: float
    role: str
    action: str
    mate: str | None
    reason: str


class PlayerIntentionsOut(BaseModel):
    player: str
    segments: list[IntentionSegmentOut]
    # délai avant de percevoir un changement de situation de son équipe (Anticipation, ticket v2-collectif/03) :
    # la situation perçue se déduit de celle de l'équipe, sans alourdir les segments
    reaction_delay_s: float | None = None


class DecisionOut(BaseModel):
    minute: float
    player: str
    team: str
    action: str
    target: str | None
    considered: int
    best: bool


class SituationOut(BaseModel):
    """Changement de situation de jeu d'une équipe, valable jusqu'au changement suivant (ticket v2-collectif/03)."""
    minute: float
    team: str
    situation: str


class MatchTraceOut(BaseModel):
    home: str
    away: str
    tick_seconds: float
    home_goals: int
    away_goals: int
    goals: list[GoalEventOut]
    ticks: list[TickOut]
    intentions: list[PlayerIntentionsOut] = []
    decisions: list[DecisionOut] = []
    situations: list[SituationOut] = []


def intention_segments(trace: MatchTrace) -> list[PlayerIntentionsOut]:
    segments: dict[str, list[IntentionSegmentOut]] = {}
    for tick in trace.ticks:
        for p in tick.players:
            if p.intention is None:
                continue
            seq = segments.setdefault(p.name, [])
            i = p.intention
            if not seq or (seq[-1].role, seq[-1].action, seq[-1].mate) != (i.role, i.action, i.mate):
                seq.append(IntentionSegmentOut(minute=tick.minute, role=i.role, action=i.action, mate=i.mate,
                                               reason=i.reason))
    return [PlayerIntentionsOut(player=name, segments=seq, reaction_delay_s=trace.reaction_delays_s.get(name))
            for name, seq in segments.items()]


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
        intentions=intention_segments(trace),
        decisions=[DecisionOut(minute=d.minute, player=d.player, team=d.team, action=d.action, target=d.target,
                               considered=d.considered, best=d.best) for d in trace.decisions],
        situations=[SituationOut(minute=s.minute, team=s.team, situation=s.situation) for s in trace.situations],
    )

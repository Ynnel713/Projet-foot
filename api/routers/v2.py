"""Route API de la V2 (docs/TRD_V2.md, D-V01) : lance un match isolé et renvoie sa trace
complète (positions à chaque instant échantillonné + buts horodatés) au frontend, qui la rejoue.
Entièrement séparée des routes V1 (`leagues.py`, `competitions.py`) -- réutilise seulement, en
lecture seule, le chargement des clubs déjà exposé par `/api/clubs` côté frontend (pas besoin
d'une route de listing dédiée ici)."""

from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ligue1sim.clubs import load_all_clubs
from ligue1sim.coaches import coach_name, preferred_formations
from ligue1sim.lineup import bench, pick_best_formation
from ligue1sim.players import ATTACKER, DEFENDER, GOALKEEPER, MIDFIELDER, position_group
from ligue1sim.season import CLUBS_PATH

from v2engine.match import TICK_SECONDS, simulate_match
from v2engine.trace import MatchTrace

router = APIRouter(prefix="/v2", tags=["v2"])

# Granularité du calcul physique et sous-échantillonnage de la trace enregistrée : le pas du produit, le même que
# celui du banc de mesure (ticket v2-collectif/25, validé le 29/10/2026), et une image par seconde.
# ponytail : pas optimisé (collision O(n²), voir v2engine/match.py) -- à revoir si ça devient gênant à l'usage.
_TICK_SECONDS = TICK_SECONDS
_RECORD_EVERY = 10


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
    holder: str | None = None  # porteur du ballon : son nom s'affiche sous son rond


class TickOut(BaseModel):
    minute: float
    players: list[PlayerSnapshotOut]
    ball: BallSnapshotOut


class GoalEventOut(BaseModel):
    minute: float
    team: str


class OffsideEventOut(BaseModel):
    """Hors-jeu sifflé (ticket v2-collectif/23) : `team` est l'équipe qui le commet."""
    minute: float
    team: str
    player: str
    x: float
    y: float


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
    best_kind: str | None = None  # meilleur choix factuel (ticket v2-collectif/33)
    gap: float = 0.0  # valeur perdue par rapport au meilleur choix factuel, en part de celui-ci


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
    offsides: list[OffsideEventOut] = []


class MatchProgressOut(BaseModel):
    """État d'un match en cours de calcul (rejeu en direct) : seulement les images à partir de `first_tick`, pour que
    chaque lecture reste légère. Intentions et décisions, lourdes, n'arrivent qu'une fois le match fini."""
    done: bool
    error: str | None = None
    home: str
    away: str
    tick_seconds: float
    home_goals: int
    away_goals: int
    goals: list[GoalEventOut]
    situations: list[SituationOut]
    offsides: list[OffsideEventOut]
    first_tick: int
    ticks: list[TickOut]
    intentions: list[PlayerIntentionsOut] = []
    decisions: list[DecisionOut] = []


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


_BENCH_SIZE = 9  # remplaçants sur la feuille de match (Ligue 1)
_GROUP_ORDER = {GOALKEEPER: 0, DEFENDER: 1, MIDFIELDER: 2, ATTACKER: 3}


class LineupPlayerOut(BaseModel):
    name: str
    poste: str
    number: int


class LineupOut(BaseModel):
    """Feuille de match d'un club, telle que `simulate_match` la choisit (`pick_best_formation`, déterministe)."""
    club: str
    formation: str
    coach: str | None
    starters: list[LineupPlayerOut]
    bench: list[LineupPlayerOut]


def numbered_lineup(club) -> LineupOut:
    """Numéros de maillot attribués à l'affichage : gardien 1, puis de la défense à l'attaque (2 à 11), remplaçants
    à partir de 12 -- les données n'ont pas de numéros réels."""
    lineup = pick_best_formation(club)
    starters = sorted(lineup.players, key=lambda p: lineup.bands.get(p.name, _GROUP_ORDER.get(position_group(p.poste), 2)))
    subs = sorted(bench(club, lineup), key=lambda p: -p.note)
    keepers = [p for p in subs if position_group(p.poste) == GOALKEEPER][:1]  # un gardien remplaçant, s'il y en a
    subs = keepers + [p for p in subs if p not in keepers][:_BENCH_SIZE - len(keepers)]
    subs.sort(key=lambda p: _GROUP_ORDER.get(position_group(p.poste), 2))
    return LineupOut(
        club=club.name, formation=lineup.formation, coach=coach_name(club.name),
        starters=[LineupPlayerOut(name=p.name, poste=p.poste, number=i) for i, p in enumerate(starters, start=1)],
        bench=[LineupPlayerOut(name=p.name, poste=p.poste, number=i) for i, p in enumerate(subs, start=12)],
    )


@router.get("/lineup", response_model=LineupOut)
def club_lineup(club: str) -> LineupOut:  # nom en paramètre de requête : certains noms de club contiennent un « / »
    return numbered_lineup(_find_club(club))


def _tick_out(tick) -> TickOut:
    return TickOut(
        minute=tick.minute,
        players=[PlayerSnapshotOut(name=p.name, team=p.team, poste=p.poste, x=p.position.x, y=p.position.y)
                 for p in tick.players],
        ball=BallSnapshotOut(x=tick.ball.position.x, y=tick.ball.position.y, holder=tick.ball.holder),
    )


def _decisions_out(trace: MatchTrace) -> list[DecisionOut]:
    return [DecisionOut(minute=d.minute, player=d.player, team=d.team, action=d.action, target=d.target,
                        considered=d.considered, best=d.best, best_kind=d.best_kind, gap=d.gap)
            for d in trace.decisions]


def _situations_out(trace: MatchTrace) -> list[SituationOut]:
    return [SituationOut(minute=s.minute, team=s.team, situation=s.situation) for s in list(trace.situations)]


def _offsides_out(trace: MatchTrace) -> list[OffsideEventOut]:
    return [OffsideEventOut(minute=o.minute, team=o.team, player=o.player, x=o.x, y=o.y) for o in list(trace.offsides)]


def _goals_out(trace: MatchTrace) -> list[GoalEventOut]:
    return [GoalEventOut(minute=g.minute, team=g.team) for g in list(trace.goals)]


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
        goals=_goals_out(trace),
        ticks=[_tick_out(tick) for tick in trace.ticks],
        intentions=intention_segments(trace),
        decisions=_decisions_out(trace),
        situations=_situations_out(trace),
        offsides=_offsides_out(trace),
    )


# --- Rejeu en direct : le match se calcule en tâche de fond et l'écran le lit par morceaux, pour commencer à le
# rejouer après quelques secondes au lieu d'attendre la fin du calcul (3 minutes environ). Le calcul va plus vite que
# le rejeu à x8 ; à x16 le rejeu peut rattraper le calcul, l'écran attend alors les images suivantes.
@dataclass
class _Job:
    home: str
    away: str
    trace: MatchTrace | None = None  # créée par `simulate_match` au démarrage, lue ici pendant qu'elle se remplit
    done: bool = False
    error: str | None = None
    cancelled: bool = False  # levé par un nouveau lancement (donc avant toute éviction) : le calcul s'arrête au tick suivant


_MAX_JOBS = 8  # ponytail : en mémoire, un seul processus ; les plus anciens sont oubliés au-delà
_jobs: dict[str, _Job] = {}
_jobs_lock = threading.Lock()


class _Cancelled(Exception):
    pass


def _run_job(job: _Job, home_club, away_club) -> None:
    def stop_if_cancelled(*_):
        if job.cancelled:
            raise _Cancelled
    try:
        simulate_match(home_club, away_club, duration_minutes=90.0, tick_seconds=_TICK_SECONDS,
                       record_every=_RECORD_EVERY, observer=stop_if_cancelled,
                       on_start=lambda trace: setattr(job, "trace", trace))
    except _Cancelled:
        job.error = "annulé"
    except Exception as exc:  # le calcul tourne hors requête : l'erreur doit remonter à l'écran, pas se perdre
        job.error = f"{type(exc).__name__}: {exc}"
    finally:
        job.done = True


class MatchStartedOut(BaseModel):
    id: str


@router.post("/matches/start", response_model=MatchStartedOut)
def start_match(payload: SimulateV2Request) -> MatchStartedOut:
    home_club = _find_club(payload.home)
    away_club = _find_club(payload.away)
    job = _Job(home=home_club.name, away=away_club.name)
    job_id = uuid.uuid4().hex
    with _jobs_lock:
        for previous in _jobs.values():  # un seul écran : le match précédent n'est plus regardé, son calcul s'arrête
            previous.cancelled = True
        _jobs[job_id] = job
        while len(_jobs) > _MAX_JOBS:
            del _jobs[next(iter(_jobs))]
    threading.Thread(target=_run_job, args=(job, home_club, away_club), daemon=True).start()
    return MatchStartedOut(id=job_id)


@router.get("/matches/{job_id}", response_model=MatchProgressOut)
def match_progress(job_id: str, from_tick: int = 0) -> MatchProgressOut:
    job = _jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Match introuvable (API redémarrée ?)")
    trace = job.trace
    done = job.done  # lu AVANT les images : si le calcul est fini, elles sont toutes là
    if trace is None:
        return MatchProgressOut(done=done, error=job.error, home=job.home, away=job.away,
                                tick_seconds=_TICK_SECONDS * _RECORD_EVERY, home_goals=0, away_goals=0,
                                goals=[], situations=[], offsides=[], first_tick=from_tick, ticks=[])
    first = max(0, from_tick)
    return MatchProgressOut(
        done=done,
        error=job.error,
        home=trace.home,
        away=trace.away,
        tick_seconds=trace.tick_seconds,
        home_goals=trace.home_goals,
        away_goals=trace.away_goals,
        goals=_goals_out(trace),
        situations=_situations_out(trace),
        offsides=_offsides_out(trace),
        first_tick=first,
        ticks=[_tick_out(tick) for tick in trace.ticks[first:]],
        intentions=intention_segments(trace) if done else [],
        decisions=_decisions_out(trace) if done else [],
    )


def prewarm() -> None:
    """Charge à froid, au démarrage de l'API, ce qui coûte au premier match (fichier des joueurs ~30 s, entraîneurs ~9 s)."""
    load_all_clubs(CLUBS_PATH)
    preferred_formations()

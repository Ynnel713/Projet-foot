"""Format de trace de match (D-V04, docs/TRD_V2.md) : position de chaque joueur et du ballon à
chaque instant échantillonné, calculée une fois côté serveur (voir `match.py`) puis destinée à
être rejouée par un rendu -- même principe calcul-puis-rejeu que la V1, mais contenu physique et
continu au lieu de narratif. Le rendu lui-même n'est pas construit en Phase 1 (voir
docs/PLAN_V2.md) : ce module ne fait que produire et porter les données."""

from __future__ import annotations

from dataclasses import dataclass, field

from v2engine.cerveau import Intention
from v2engine.geometry import Vec2


@dataclass(frozen=True)
class PlayerSnapshot:
    name: str
    team: str  # "home" / "away"
    poste: str
    position: Vec2
    intention: Intention | None = None  # ce que le joueur cherche à faire à cet instant (ADR 0001)


@dataclass(frozen=True)
class BallSnapshot:
    position: Vec2


@dataclass(frozen=True)
class Tick:
    minute: float  # minute de match simulée
    players: tuple[PlayerSnapshot, ...]
    ball: BallSnapshot


@dataclass(frozen=True)
class DecisionRecord:
    """Une décision du porteur (journal des décisions, ADR 0001)."""
    minute: float
    player: str
    team: str
    action: str  # "shot" | "pass" | "dribble"
    target: str | None  # coéquipier visé, pour une passe
    considered: int  # options envisagées
    best: bool  # meilleure option prise


@dataclass(frozen=True)
class SituationRecord:
    """Changement de situation de jeu d'une équipe (ticket v2-collectif/03)."""
    minute: float
    team: str
    situation: str


@dataclass(frozen=True)
class GoalEvent:
    minute: float
    team: str  # "home" / "away"


@dataclass
class MatchTrace:
    home: str
    away: str
    tick_seconds: float  # intervalle de temps de match entre deux ticks enregistrés
    ticks: list[Tick] = field(default_factory=list)
    # Score : émerge entièrement du moteur (Phase 4, docs/PLAN_V2.md) -- jamais décidé à
    # l'avance, contrairement à la V1. `goals` horodate chaque but (minute, équipe) pour que le
    # rendu puisse révéler le score au fil du visionnage (US-29), pas avant.
    home_goals: int = 0
    away_goals: int = 0
    goals: list[GoalEvent] = field(default_factory=list)
    decisions: list[DecisionRecord] = field(default_factory=list)
    situations: list[SituationRecord] = field(default_factory=list)
    reaction_delays_s: dict[str, float] = field(default_factory=dict)  # par joueur (Anticipation, ticket v2-collectif/03)

    def record(self, minute: float, players: list[PlayerSnapshot], ball: BallSnapshot) -> None:
        self.ticks.append(Tick(minute=minute, players=tuple(players), ball=ball))

    def record_goal(self, team: str, minute: float) -> None:
        if team == "home":
            self.home_goals += 1
        elif team == "away":
            self.away_goals += 1
        else:
            raise ValueError(f"équipe inconnue : {team!r} (attendu 'home' ou 'away')")
        self.goals.append(GoalEvent(minute=minute, team=team))

"""Format de trace de match (D-V04, docs/TRD_V2.md) : position de chaque joueur et du ballon à
chaque instant échantillonné, calculée une fois côté serveur (voir `match.py`) puis destinée à
être rejouée par un rendu -- même principe calcul-puis-rejeu que la V1, mais contenu physique et
continu au lieu de narratif. Le rendu lui-même n'est pas construit en Phase 1 (voir
docs/PLAN_V2.md) : ce module ne fait que produire et porter les données."""

from __future__ import annotations

from dataclasses import dataclass, field

from v2engine.geometry import Vec2


@dataclass(frozen=True)
class PlayerSnapshot:
    name: str
    team: str  # "home" / "away"
    poste: str
    position: Vec2


@dataclass(frozen=True)
class BallSnapshot:
    position: Vec2


@dataclass(frozen=True)
class Tick:
    minute: float  # minute de match simulée
    players: tuple[PlayerSnapshot, ...]
    ball: BallSnapshot


@dataclass
class MatchTrace:
    home: str
    away: str
    tick_seconds: float  # intervalle de temps de match entre deux ticks enregistrés
    ticks: list[Tick] = field(default_factory=list)
    # Score : émerge entièrement du moteur (Phase 4, docs/PLAN_V2.md) -- jamais décidé à
    # l'avance, contrairement à la V1. Pas encore de liste de buteurs/minutes (hors périmètre de
    # ce premier jalon, voir docs/PLAN_V2.md Phase 4).
    home_goals: int = 0
    away_goals: int = 0

    def record(self, minute: float, players: list[PlayerSnapshot], ball: BallSnapshot) -> None:
        self.ticks.append(Tick(minute=minute, players=tuple(players), ball=ball))

    def record_goal(self, team: str) -> None:
        if team == "home":
            self.home_goals += 1
        elif team == "away":
            self.away_goals += 1
        else:
            raise ValueError(f"équipe inconnue : {team!r} (attendu 'home' ou 'away')")

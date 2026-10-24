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

    def record(self, minute: float, players: list[PlayerSnapshot], ball: BallSnapshot) -> None:
        self.ticks.append(Tick(minute=minute, players=tuple(players), ball=ball))

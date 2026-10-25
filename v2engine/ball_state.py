"""État du ballon pendant une simulation (Phase 2, docs/PLAN_V2.md) : position/vitesse comme en
Phase 1, plus la possession (quel joueur le contrôle, le cas échéant). Distinct de
`trace.BallSnapshot` (instantané figé destiné au rendu, pas d'état de simulation)."""

from __future__ import annotations

from dataclasses import dataclass, field

from v2engine.geometry import Vec2


@dataclass
class BallState:
    position: Vec2
    velocity: Vec2
    holder: str | None = None  # nom du joueur en contrôle du ballon, None = ballon libre
    # Instant (s de match) avant lequel le porteur garde son choix en cours -- conduite de balle
    # entre deux réévaluations (`decision.DECISION_INTERVAL_S`).
    next_decision_s: float = 0.0
    # Adversaires qui ont lu la passe en cours et le point où ils courent la couper (Anticipation,
    # `anticipation.pass_readers`) ; vidé dès que quelqu'un contrôle le ballon.
    readers: dict[str, Vec2] = field(default_factory=dict)
    last_pass_team: str | None = None  # équipe de la dernière passe, pour repérer une interception
    receiver: str | None = None  # coéquipier visé par la passe en cours, qui vient au-devant du ballon (v2-socle/01)
    receiving: bool = False  # porteur encore dans son temps de réception, avant sa première décision (v2-socle/06)
    # Duels (v2-socle/03) : défenseurs ayant déjà tenté leur tacle dans la confrontation en cours avec
    # `engaged_holder`, et instant jusqu'auquel un défenseur au tacle raté ne peut plus tacler.
    engaged: set[str] = field(default_factory=set)
    engaged_holder: str | None = None
    tackle_ban_until_s: dict[str, float] = field(default_factory=dict)

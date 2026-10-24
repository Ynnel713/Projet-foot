"""État du ballon pendant une simulation (Phase 2, docs/PLAN_V2.md) : position/vitesse comme en
Phase 1, plus la possession (quel joueur le contrôle, le cas échéant). Distinct de
`trace.BallSnapshot` (instantané figé destiné au rendu, pas d'état de simulation)."""

from __future__ import annotations

from dataclasses import dataclass

from v2engine.geometry import Vec2


@dataclass
class BallState:
    position: Vec2
    velocity: Vec2
    holder: str | None = None  # nom du joueur en contrôle du ballon, None = ballon libre
    # Instant (s de match) avant lequel le porteur garde son choix en cours -- conduite de balle
    # entre deux réévaluations (`decision.DECISION_INTERVAL_S`).
    next_decision_s: float = 0.0

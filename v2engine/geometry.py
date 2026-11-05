"""Géométrie 2D minimale du moteur V2 -- terrain à plat (x/y, pas de hauteur, D-V03), en mètres,
mêmes dimensions que la V1 (`ligue1sim.pitch_geometry`, réutilisé en lecture seule, voir D-V02)."""

from __future__ import annotations

import math
from dataclasses import dataclass

from ligue1sim.pitch_geometry import PENALTY_AREA_DEPTH_M, PENALTY_AREA_WIDTH_M, PITCH_LENGTH_M, PITCH_WIDTH_M

__all__ = ["PITCH_LENGTH_M", "PITCH_WIDTH_M", "Vec2", "clamp_to_pitch", "in_penalty_area"]


@dataclass(frozen=True)
class Vec2:
    x: float
    y: float

    def __add__(self, other: Vec2) -> Vec2:
        return Vec2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Vec2) -> Vec2:
        return Vec2(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> Vec2:
        return Vec2(self.x * scalar, self.y * scalar)

    __rmul__ = __mul__

    def length(self) -> float:
        return math.hypot(self.x, self.y)

    def normalized(self) -> Vec2:
        length = self.length()
        return Vec2(self.x / length, self.y / length) if length > 1e-9 else Vec2(0.0, 0.0)

    def distance_to(self, other: Vec2) -> float:
        return math.hypot(self.x - other.x, self.y - other.y)


def clamp_to_pitch(position: Vec2) -> Vec2:
    """Empêche un joueur ou le ballon de sortir du rectangle du terrain -- simplification
    volontaire de la Phase 1 (pas de sortie en touche/remise en jeu modélisée)."""
    return Vec2(min(max(position.x, 0.0), PITCH_LENGTH_M), min(max(position.y, 0.0), PITCH_WIDTH_M))


def in_penalty_area(team: str, position: Vec2) -> bool:
    """`position` est-elle dans la surface de réparation que `team` attaque ? (`home` attaque vers x = 105)"""
    depth = PITCH_LENGTH_M - position.x if team == "home" else position.x
    return depth <= PENALTY_AREA_DEPTH_M and abs(position.y - PITCH_WIDTH_M / 2.0) <= PENALTY_AREA_WIDTH_M / 2.0

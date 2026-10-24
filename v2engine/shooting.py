"""Tirs et gardien (Phase 4, docs/PLAN_V2.md) : un porteur du ballon proche du but adverse tente
sa chance -- issue pilotée par Finishing/Composure (tireur) contre Reflexes/One on Ones/Handling
(gardien), modulée par la distance et l'angle de tir (physique, voir `shot_probability`). Jalon
du premier plan (US-29) : à la fin de cette phase, un score émerge entièrement du moteur, plus
aucun résultat décidé à l'avance (IA de décision placeholder, D-V08 : un porteur à portée tente
toujours sa chance, pas de lecture tactique de quand tirer)."""

from __future__ import annotations

import random

from v2engine.attributes import duel_probability, player_attribute
from v2engine.movement import PlayerState

# Distance (m) en dessous de laquelle un porteur tente sa chance plutôt que de chercher une
# passe -- IA de décision placeholder (D-V08), pas une vraie lecture tactique.
SHOOTING_RANGE_M = 20.0

_CLOSE_RANGE_M = 6.0  # profondeur approximative de la surface de but -- tir à pleine chance en dessous

_MIN_SHOT_PROBABILITY = 0.03
_MAX_SHOT_PROBABILITY = 0.9

# Repli neutre (gardien absent -- effectif synthétique sans gardien, voir docs/PLAN_V2.md
# Phase 1) : proche de la moyenne réelle de la base (voir `attributes.player_attribute`).
_NEUTRAL_KEEPER_RATING = 60.0


def _distance_factor(distance_m: float) -> float:
    """1.0 à bout portant, décroît linéairement jusqu'à un plancher à la limite de la zone de
    tir -- jamais 0 (un tir à la limite reste à faible pourcentage, pas impossible)."""
    if distance_m <= _CLOSE_RANGE_M:
        return 1.0
    ratio = (distance_m - _CLOSE_RANGE_M) / (SHOOTING_RANGE_M - _CLOSE_RANGE_M)
    return max(0.15, 1.0 - min(1.0, ratio))


def _angle_factor(shooter_y: float, goal_center_y: float, distance_m: float) -> float:
    """1.0 face au but, décroît avec l'écart latéral relatif à la distance -- jamais 0 (un angle
    fermé reste à faible pourcentage, pas impossible)."""
    lateral_offset = abs(shooter_y - goal_center_y)
    ratio = lateral_offset / (distance_m + 1.0)
    return max(0.2, 1.0 - ratio)


def _keeper_rating(keeper: PlayerState | None) -> float:
    if keeper is None:
        return _NEUTRAL_KEEPER_RATING
    return (
        0.5 * player_attribute(keeper, "Reflexes")
        + 0.3 * player_attribute(keeper, "One on Ones")
        + 0.2 * player_attribute(keeper, "Handling")
    )


def shot_probability(shooter: PlayerState, keeper: PlayerState | None, distance_m: float, goal_center_y: float) -> float:
    """Probabilité qu'un tir de `shooter` à `distance_m` du but (centré en y=`goal_center_y`)
    devienne un but face à `keeper` -- jamais garantie, jamais nulle (règle "jamais binaire" du
    guide). `keeper=None` : repli neutre (voir `_NEUTRAL_KEEPER_RATING`)."""
    shot_quality = 0.8 * player_attribute(shooter, "Finishing") + 0.2 * player_attribute(shooter, "Composure")
    base = duel_probability(shot_quality, _keeper_rating(keeper))
    modifier = _distance_factor(distance_m) * _angle_factor(shooter.position.y, goal_center_y, distance_m)
    return max(_MIN_SHOT_PROBABILITY, min(_MAX_SHOT_PROBABILITY, base * modifier))


def attempt_shot(shooter: PlayerState, keeper: PlayerState | None, distance_m: float, goal_center_y: float) -> bool:
    """`True` si le tir devient un but."""
    return random.random() < shot_probability(shooter, keeper, distance_m, goal_center_y)

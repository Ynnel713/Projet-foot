"""Tirs et gardien (Phase 4, docs/PLAN_V2.md) : un porteur du ballon proche du but adverse tente
sa chance -- issue pilotée par Finishing/Composure (tireur) contre Reflexes/One on Ones/Handling
(gardien), modulée par la distance et l'angle de tir (physique, voir `shot_probability`). Jalon
du premier plan (US-29) : à la fin de cette phase, un score émerge entièrement du moteur, plus
aucun résultat décidé à l'avance (IA de décision placeholder, D-V08 : un porteur à portée tente
toujours sa chance, pas de lecture tactique de quand tirer)."""

from __future__ import annotations

import random

from v2engine.attributes import duel_probability, player_attribute
from v2engine.geometry import Vec2
from v2engine.movement import PlayerState

# Distance de tir maximale (m) : au-delà, l'option « tirer » n'existe pas pour le porteur (voir
# `decision.py`, qui choisit QUAND tirer). Constante validée par le propriétaire (24/10/2026,
# ticket v2-cerveau-joueurs/01, 20 m auparavant).
SHOOTING_RANGE_M = 30.0
# Chance selon la distance (ticket v2-collectif/33, validé par délégation du propriétaire le 04/11/2026 ; avant :
# baisse linéaire jusqu'à 10 % de la chance à bout portant à 30 m, soit 14 % de but à 25 m) : divisée par deux tous
# les `_HALF_DISTANCE_M` au-delà de la surface de but, pour un tireur moyen environ 25 % à 11 m, 12 % à 16 m, 7 % à
# 20 m, 4 % à 25 m, 2 % à 30 m (ordres de grandeur des modèles « expected goals », de mémoire, à sourcer au ticket 28).
# Dans la monnaie du danger attendu, une chance trop forte de loin faisait du tir à 25-30 m le meilleur choix factuel.
_HALF_DISTANCE_M = 5.0

_CLOSE_RANGE_M = 6.0  # profondeur approximative de la surface de but -- tir à pleine chance en dessous

_MIN_SHOT_PROBABILITY = 0.01  # 0,03 avant le ticket v2-collectif/33
_MAX_SHOT_PROBABILITY = 0.9

# Tir contré (ticket v2-collectif/33, version minimale en attendant le ticket 28 ; validé par délégation du propriétaire
# le 04/11/2026) : un défenseur de champ placé entre le tireur et le but, à moins de `BLOCK_WIDTH_M` de la ligne de tir
# (jambe tendue plus ballon), contre le tir avec la chance `BLOCK_CHANCE` s'il est pile dans la ligne, de moins en
# moins vers le bord. Chaque défenseur tire sa chance, du plus proche du tireur au plus loin. Même règle pour décider
# (valeur du tir) et pour résoudre (match.py). Réel : 20 à 28 % des tirs contrés (ordre de grandeur, ticket 28).
BLOCK_WIDTH_M = 1.0
BLOCK_CHANCE = 0.6

# Repli neutre (gardien absent -- effectif synthétique sans gardien, voir docs/PLAN_V2.md
# Phase 1) : proche de la moyenne réelle de la base (voir `attributes.player_attribute`).
_NEUTRAL_KEEPER_RATING = 60.0


def _distance_factor(distance_m: float) -> float:
    """1.0 à bout portant (surface de but), puis divisé par deux tous les `_HALF_DISTANCE_M` -- jamais 0."""
    if distance_m <= _CLOSE_RANGE_M:
        return 1.0
    return 0.5 ** ((distance_m - _CLOSE_RANGE_M) / _HALF_DISTANCE_M)


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


def _blockers(shooter: PlayerState, goal: Vec2, opponents: list[PlayerState]) -> list[tuple[PlayerState, float]]:
    """Défenseurs de champ dans la ligne de tir et leur chance de contrer, du plus proche du tireur au plus loin."""
    # ponytail: ligne vers le centre du but, pas de cône entre les poteaux ni de visée ; le ticket 28 fait le cône
    line = goal - shooter.position
    length = line.length()
    if length == 0.0:
        return []
    axis = line * (1.0 / length)
    found = []
    for opponent in opponents:
        if opponent.poste == "GK":
            continue
        offset = opponent.position - shooter.position
        along = offset.x * axis.x + offset.y * axis.y
        if not 0.0 < along < length:
            continue
        across = abs(offset.x * axis.y - offset.y * axis.x)
        if across < BLOCK_WIDTH_M:
            found.append((along, opponent, BLOCK_CHANCE * (1.0 - across / BLOCK_WIDTH_M)))
    return [(o, c) for _, o, c in sorted(found, key=lambda t: t[0])]


def block_probability(shooter: PlayerState, goal: Vec2, opponents: list[PlayerState]) -> float:
    """Chance que le tir soit contré par au moins un défenseur de la ligne de tir."""
    through = 1.0
    for _, chance in _blockers(shooter, goal, opponents):
        through *= 1.0 - chance
    return 1.0 - through


def draw_blocker(shooter: PlayerState, goal: Vec2, opponents: list[PlayerState]) -> PlayerState | None:
    """Le défenseur qui contre ce tir-ci, ou `None` s'il passe (un tirage par défenseur de la ligne)."""
    return next((o for o, chance in _blockers(shooter, goal, opponents) if random.random() < chance), None)

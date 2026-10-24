"""Contrôle et passe (Phase 2, docs/PLAN_V2.md) : un joueur qui touche le ballon tente de le
contrôler (First Touch), puis, s'il y parvient, le transmet aussitôt à un coéquipier (Passing/
Technique) -- pas encore de conduite de balle ni de lecture tactique du jeu (IA placeholder,
D-V08 ; la vraie prise de décision vient en Phase 5+, voir docs/PLAN_V2.md)."""

from __future__ import annotations

import math
import random

from v2engine.attributes import player_attribute, success_probability
from v2engine.geometry import Vec2
from v2engine.movement import PlayerState

PASS_SPEED_MPS = 15.0  # vitesse simple d'une passe, indépendante de la distance (simplification Phase 2)
# Dispersion maximale (m) d'une passe totalement ratée -- bornée pour qu'une mauvaise passe reste
# plausible (dans le même quart de terrain) plutôt qu'aberrante.
MAX_PASS_ERROR_M = 8.0


def attempt_control(player: PlayerState) -> bool:
    """Un joueur tente de contrôler le ballon à son contact -- probabilité pilotée par First
    Touch (voir `success_probability`). Jamais garanti, même à note élevée (règle "jamais
    binaire" du guide)."""
    first_touch = player_attribute(player, "First Touch")
    return random.random() < success_probability(first_touch)


def choose_pass_target(passer: PlayerState, teammates: list[PlayerState]) -> PlayerState | None:
    """Coéquipier visé par une passe -- le plus proche, hors soi-même (IA placeholder, D-V08 :
    aucune lecture tactique du jeu pour l'instant). `None` si aucun coéquipier disponible."""
    candidates = [p for p in teammates if p.name != passer.name]
    if not candidates:
        return None
    return min(candidates, key=lambda p: passer.position.distance_to(p.position))


def pass_velocity(passer: PlayerState, target: PlayerState) -> Vec2:
    """Vitesse du ballon juste après une passe de `passer` vers `target` -- précision pilotée par
    Passing (réussite de la passe) et Technique (gamme de gestes), les deux améliorant la
    probabilité de réussite (voir `success_probability`). Une passe ratée part vers un point
    décalé aléatoirement autour du coéquipier visé plutôt que de l'atteindre -- jamais une passe
    garantie, même à notes élevées (règle "jamais binaire" du guide)."""
    passing = player_attribute(passer, "Passing")
    technique = player_attribute(passer, "Technique")
    accuracy = (success_probability(passing) + success_probability(technique)) / 2.0

    aim_point = target.position
    if random.random() > accuracy:
        error_angle = random.uniform(0.0, 2.0 * math.pi)
        error_distance = random.uniform(0.0, MAX_PASS_ERROR_M) * (1.0 - accuracy)
        aim_point = aim_point + Vec2(error_distance * math.cos(error_angle), error_distance * math.sin(error_angle))

    direction = (aim_point - passer.position).normalized()
    return direction * PASS_SPEED_MPS

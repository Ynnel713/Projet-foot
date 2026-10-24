"""Contrôle et passe (Phase 2, docs/PLAN_V2.md) : un joueur qui touche le ballon tente de le
contrôler (First Touch), puis exécute la passe choisie par `decision.py` (Passing/Technique)."""

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


def pass_accuracy(passer: PlayerState) -> float:
    """Probabilité qu'une passe de `passer` arrive où il la destine -- Passing (réussite de la
    passe) et Technique (gamme de gestes), voir `success_probability`. Partagée par l'exécution
    (`pass_velocity`) et l'évaluation de l'option « passer » (`decision.py`)."""
    passing = player_attribute(passer, "Passing")
    technique = player_attribute(passer, "Technique")
    return (success_probability(passing) + success_probability(technique)) / 2.0


def pass_velocity(passer: PlayerState, target: PlayerState) -> Vec2:
    """Vitesse du ballon juste après une passe de `passer` vers `target` -- précision pilotée par
    Passing (réussite de la passe) et Technique (gamme de gestes), les deux améliorant la
    probabilité de réussite (voir `success_probability`). Une passe ratée part vers un point
    décalé aléatoirement autour du coéquipier visé plutôt que de l'atteindre -- jamais une passe
    garantie, même à notes élevées (règle "jamais binaire" du guide)."""
    accuracy = pass_accuracy(passer)

    aim_point = target.position
    if random.random() > accuracy:
        error_angle = random.uniform(0.0, 2.0 * math.pi)
        error_distance = random.uniform(0.0, MAX_PASS_ERROR_M) * (1.0 - accuracy)
        aim_point = aim_point + Vec2(error_distance * math.cos(error_angle), error_distance * math.sin(error_angle))

    direction = (aim_point - passer.position).normalized()
    return direction * PASS_SPEED_MPS

"""Anticipation (Phase 5, ticket v2-cerveau-joueurs/04) : réagir AVANT l'action. Deux effets
(Guide_attributs_joueurs.pdf, Anticipation) : un adversaire proche de la trajectoire d'une passe peut la
« lire » et courir vers le point où il la coupe ; sur un ballon libre, un joueur vise l'endroit où le
ballon va s'arrêter plutôt que sa position actuelle. L'interception elle-même reste un contrôle du ballon
(First Touch, `possession.attempt_control`)."""

from __future__ import annotations

import math
import random

from v2engine.attributes import player_attribute, success_probability
from v2engine.geometry import Vec2
from v2engine.movement import PlayerState, max_speed_mps

# Constantes produit validées par le propriétaire (24/10/2026), courbe partagée du guide.
_READ_PASS = (0.40, 0.40, 0.10, 0.80)  # baseline, amplitude, min, max : 99 -> 80 %, 55 -> 40 %, 11 -> 10 %
READING_LANE_M = 8.0  # seuls les adversaires à moins de 8 m de la trajectoire peuvent lire la passe
_LOOSE_BALL_LEAD = (0.5, 0.5, 0.0, 1.0)  # part du chemin vers le point d'arrêt : 99 -> 100 %, 55 -> 50 %, 11 -> 0 %


def _curve(note: float, params: tuple[float, float, float, float]) -> float:
    baseline, amplitude, low, high = params
    return success_probability(note, baseline=baseline, amplitude=amplitude, min_prob=low, max_prob=high)


# Délai de réaction à un changement de situation (ticket v2-collectif/03, validé le 26/10/2026) : 99 -> 0,4 s,
# 55 -> 0,7 s, 11 -> 1,0 s. Réf. : 0,7 s, temps de réaction par défaut du modèle de pression Unravel Sports (tracking).
_REACTION_S = (0.7, 0.3, 0.4, 1.0)  # baseline, amplitude, min, max (inversé : bonne note = délai court)
MAX_REACTION_S = _REACTION_S[3]


def reaction_delay_s(player: PlayerState) -> float:
    """Temps pour qu'un joueur se rende compte d'un changement de situation de son équipe (perte, récupération)."""
    _, _, low, high = _REACTION_S
    return low + high - _curve(player_attribute(player, "Anticipation"), _REACTION_S)


def read_pass_probability(anticipation: float) -> float:
    return _curve(anticipation, _READ_PASS)


def loose_ball_lead(anticipation: float) -> float:
    return _curve(anticipation, _LOOSE_BALL_LEAD)


def pass_readers(start: Vec2, velocity: Vec2, aim: Vec2, opponents: list[PlayerState]) -> dict[str, Vec2]:
    """Adversaires qui lisent une passe partant de `start` vers `aim` à `velocity`, avec le point de la
    trajectoire où chacun court la couper. Il faut être dans le couloir (`READING_LANE_M`), pouvoir y être
    avant le ballon (vitesse de pointe, ballon supposé à vitesse constante -- critère strict), et la lire
    (tirage piloté par Anticipation)."""
    path = aim - start
    length = path.length()
    speed = velocity.length()
    if length < 1e-9 or speed < 1e-9:
        return {}
    direction = path * (1.0 / length)
    readers = {}
    for opponent in opponents:
        rel = opponent.position - start
        along = min(length, max(0.0, rel.x * direction.x + rel.y * direction.y))
        point = start + direction * along
        if opponent.position.distance_to(point) > READING_LANE_M:
            continue
        if opponent.position.distance_to(point) / max_speed_mps(opponent.pace) > along / speed:
            continue
        if random.random() < read_pass_probability(player_attribute(opponent, "Anticipation")):
            readers[opponent.name] = point
    return readers


def loose_ball_target(player: PlayerState, ball_position: Vec2, ball_velocity: Vec2, friction_per_s: float) -> Vec2:
    """Point visé sur un ballon libre : entre sa position actuelle et son point d'arrêt (ballon freiné de
    `friction_per_s` par seconde : il parcourt encore v / -ln(f)), selon Anticipation."""
    stop = ball_position + ball_velocity * (1.0 / -math.log(friction_per_s))
    return ball_position + (stop - ball_position) * loose_ball_lead(player_attribute(player, "Anticipation"))


def meeting_point(player: PlayerState, ball_position: Vec2, ball_velocity: Vec2, friction_per_s: float) -> Vec2:
    """Point de la trajectoire RÉELLE du ballon (freiné de `friction_per_s` par seconde) que `player` peut
    atteindre le plus tôt, à sa vitesse de pointe -- là où un receveur vient couper le ballon (ticket
    v2-socle/01). S'il ne peut l'atteindre nulle part en route, son point d'arrêt."""
    log_f = math.log(friction_per_s)
    speed = max_speed_mps(player.pace)
    t = 0.0
    while t < 4.0:  # au-delà, le ballon est quasiment arrêté (il a parcouru 87 % de sa course à 0,6/s)
        point = ball_position + ball_velocity * ((friction_per_s**t - 1.0) / log_f)
        if player.position.distance_to(point) <= speed * t:
            return point
        t += 0.1
    return ball_position + ball_velocity * (1.0 / -log_f)

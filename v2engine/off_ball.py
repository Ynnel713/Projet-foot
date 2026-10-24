"""Déplacement sans ballon de l'équipe en possession (Phase 5, ticket v2-cerveau-joueurs/03, Off the Ball) :
au lieu de foncer sur le ballon, chaque coéquipier du porteur cherche un espace libre autour de sa place de
formation, surtout vers l'avant (appel), parfois en décrochage. Off the Ball règle jusqu'où il cherche et la
probabilité qu'il trouve le meilleur espace (Guide_attributs_joueurs.pdf, Off the Ball)."""

from __future__ import annotations

import random

from v2engine.attributes import player_attribute, success_probability
from v2engine.geometry import Vec2, clamp_to_pitch
from v2engine.movement import PlayerState

# Constantes produit validées par le propriétaire (24/10/2026).
RUN_INTERVAL_S = 1.0  # fréquence de recherche d'espace
_SEARCH_RADIUS_M = (8.0, 7.0, 2.0, 15.0)  # baseline, amplitude, min, max : 99 -> 15 m, 55 -> 8 m, 11 -> 2 m
_FORWARD_SHARE = 2.0 / 3.0  # part du rayon cherchée vers l'avant ; le reste (1/3) en arrière
# Choisir le meilleur espace : 99 -> 95 %, 55 -> 70 %, 11 -> 45 % (même courbe que Decisions).
_BEST_SPACE_BASELINE = 0.70
_BEST_SPACE_AMPLITUDE = 0.25

# Grille de points candidats, en fractions du rayon : avant/arrière x latéral. Pas une constante produit.
_FORWARD_STEPS = (-1.0 / 3.0, 0.0, 1.0 / 3.0, _FORWARD_SHARE)
_LATERAL_STEPS = (-0.5, 0.0, 0.5)


def search_radius_m(off_the_ball: float) -> float:
    baseline, amplitude, low, high = _SEARCH_RADIUS_M
    return success_probability(off_the_ball, baseline=baseline, amplitude=amplitude, min_prob=low, max_prob=high)


def best_space_probability(off_the_ball: float) -> float:
    return success_probability(off_the_ball, baseline=_BEST_SPACE_BASELINE, amplitude=_BEST_SPACE_AMPLITUDE)


def choose_space(player: PlayerState, opponents: list[PlayerState], forward: float) -> Vec2:
    """Point libre visé par `player` (coéquipier du porteur), autour de sa place de formation. `forward` : +1 si
    son équipe attaque vers x croissant, -1 sinon. Un espace vaut sa distance à l'adversaire le plus proche ;
    à égalité, le plus avancé gagne."""
    radius = search_radius_m(player_attribute(player, "Off the Ball"))
    candidates = [
        clamp_to_pitch(player.home_target + Vec2(forward * fx * radius, ly * radius))
        for fx in _FORWARD_STEPS
        for ly in _LATERAL_STEPS
    ]

    def openness(point: Vec2) -> float:
        nearest = min((point.distance_to(o.position) for o in opponents), default=0.0)
        return nearest + 0.01 * forward * point.x

    ranked = sorted(candidates, key=openness, reverse=True)
    if random.random() < best_space_probability(player_attribute(player, "Off the Ball")):
        return ranked[0]
    return random.choice(ranked[1:])

"""Gardien (ticket v2-realisme/03a) : sous-système propre. Le gardien ne passe plus par la règle générale du cerveau (qui en
faisait un presseur à moins de 15 m d'un porteur adverse et un soutien à moins de 15 m du sien) : son rôle est `GARDIEN`
et ses états sont tracés dans la raison de son intention.

États : `placement` (il se tient sur la bissectrice de l'angle ballon-poteaux, ticket 03b), `sortie` (ballon libre à
sa portée : il va le chercher, comme avant), `intervention` (passe pour lui, ou passe qu'il a lue), `relance` (il a le
ballon). Aucun attribut de gardien ici (`v2-attributs-restants/03b`)."""

from __future__ import annotations

import math

from ligue1sim.pitch_geometry import GOAL_WIDTH_M

from v2engine.ball_state import BallState
from v2engine.geometry import PENALTY_AREA_DEPTH_M, PENALTY_AREA_WIDTH_M, PITCH_LENGTH_M, PITCH_WIDTH_M, Vec2
from v2engine.movement import PlayerState

# Placement sur la bissectrice (ticket v2-realisme/03b ; chiffres réels non trouvés, ordres de grandeur, constantes
# proposées par Claude et validées par délégation du propriétaire le 06/11/2026) : le gardien se tient sur la bissectrice
# de l'angle ballon-poteaux, à une distance de sa ligne qui croît avec la distance du ballon à son but : `DEPTH_M[0]`
# quand le ballon est à `BALL_DISTANCE_M[0]` ou moins, `DEPTH_M[1]` à `BALL_DISTANCE_M[1]` ou plus (de la distance de tir
# aux abords de la surface : près de sa ligne ; loin : avancé), toujours dans sa surface. Écart toléré à la bissectrice au
# moment des tirs, seuil de contrôle du banc : `BISECTOR_TOLERANCE_M`.
DEPTH_M = (1.5, 8.0)
BALL_DISTANCE_M = (12.0, 40.0)
BISECTOR_TOLERANCE_M = 2.0

GARDIEN = "gardien"
PLACEMENT, SORTIE, INTERVENTION, RELANCE = "placement", "sortie", "intervention", "relance"


def state(player: PlayerState, ball: BallState, is_receiver: bool, has_read: bool, loose_in_reach: bool) -> str:
    """État du gardien : `loose_in_reach` vaut vrai si le ballon est libre et à sa portée (à moins de CHASE_RADIUS_M, ou
    s'il est le plus proche de son équipe, règle du cerveau pour tout joueur)."""
    if player.name == ball.holder:
        return RELANCE
    if is_receiver or has_read:
        return INTERVENTION
    return SORTIE if loose_in_reach else PLACEMENT


def own_goal(team: str) -> Vec2:
    """Centre du but défendu par `team` (domicile : x = 0)."""
    return Vec2(0.0 if team == "home" else PITCH_LENGTH_M, PITCH_WIDTH_M / 2.0)


def bisector_direction(ball: Vec2, goal: Vec2) -> Vec2:
    """Direction unitaire, du ballon vers le but, de la bissectrice de l'angle sous lequel le ballon voit les deux poteaux
    (repli : droit vers le centre du but, si le ballon est sur la ligne de but entre les poteaux)."""
    half = GOAL_WIDTH_M / 2.0
    first = (Vec2(goal.x, goal.y - half) - ball).normalized()
    second = (Vec2(goal.x, goal.y + half) - ball).normalized()
    bisector = Vec2(first.x + second.x, first.y + second.y)
    return bisector.normalized() if bisector.length() > 1e-6 else (goal - ball).normalized()


def depth_for_ball(distance_m: float) -> float:
    """Distance à sa ligne de but (m) du gardien, selon la distance du ballon à son but : bornée à `DEPTH_M`."""
    near, far = BALL_DISTANCE_M
    share = min(1.0, max(0.0, (distance_m - near) / (far - near)))
    return DEPTH_M[0] + (DEPTH_M[1] - DEPTH_M[0]) * share


def bisector_point(player: PlayerState, ball: Vec2) -> Vec2:
    """Point de la bissectrice ballon-poteaux à la distance de sa ligne que demande la distance du ballon, dans sa
    surface de réparation. Si le ballon est plus près de la ligne que cette distance (près de la ligne de but), le point
    est pris à la distance minimale `DEPTH_M[0]` ; sur la ligne même, le gardien va au ballon."""
    goal = own_goal(player.team)
    inward = 1.0 if player.team == "home" else -1.0
    direction = bisector_direction(ball, goal)
    reach = ball.distance_to(goal)
    if abs(direction.x) > 1e-6:
        depth = depth_for_ball(reach)
        along = (goal.x + inward * depth - ball.x) / direction.x  # distance, sur la bissectrice, jusqu'à cette profondeur
        if along < 0.0:  # le ballon est plus près de la ligne que `depth`
            along = (goal.x + inward * DEPTH_M[0] - ball.x) / direction.x
        reach = min(reach, max(0.0, along))
    point = ball + direction * reach
    depth_now = min(abs(point.x - goal.x), PENALTY_AREA_DEPTH_M)
    side = min(max(point.y - goal.y, -PENALTY_AREA_WIDTH_M / 2.0), PENALTY_AREA_WIDTH_M / 2.0)
    return Vec2(goal.x + inward * depth_now, goal.y + side)


def placement(player: PlayerState, ball: Vec2) -> Vec2:
    """Place visée en état `placement` (ticket v2-realisme/03b) : le point de la bissectrice ballon-poteaux."""
    return bisector_point(player, ball)

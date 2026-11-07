"""Gardien (ticket v2-realisme/03a) : sous-système propre. Le gardien ne passe plus par la règle générale du cerveau (qui en
faisait un presseur à moins de 15 m d'un porteur adverse et un soutien à moins de 15 m du sien) : son rôle est `GARDIEN`
et ses états sont tracés dans la raison de son intention.

États : `placement` (il tient sa place devant son but ; le ticket 03b y mettra la bissectrice), `sortie` (ballon libre à
sa portée : il va le chercher, comme avant), `intervention` (passe pour lui, ou passe qu'il a lue), `relance` (il a le
ballon). Aucun attribut de gardien ici (`v2-attributs-restants/03b`)."""

from __future__ import annotations

from v2engine.ball_state import BallState
from v2engine.geometry import Vec2
from v2engine.movement import PlayerState

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


def placement(player: PlayerState) -> Vec2:
    """Place visée en état `placement` : sa place de coup d'envoi (ponytail : fixe, la bissectrice vient au 03b)."""
    return player.home_target

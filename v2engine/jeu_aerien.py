"""Qui attaque un ballon aérien (ticket v2-realisme/15a) : tant que le ballon est en l'air (de la frappe jusqu'à ce qu'il
roule), chaque équipe envoie au plus `AERIAL_ATTACKERS` joueurs de champ au point où chacun peut le toucher le plus
tôt : premier point de la trajectoire où il est à temps et où le ballon passe à sa portée (taille et détente,
`atteinte.reach_m`, ticket v2-hauteur-ballon/03a). Le receveur visé d'une passe compte toujours parmi ceux de son
équipe. Les autres gardent leur rôle (le second ballon est le ticket 15e) ; le gardien garde ses règles de sortie et
ne compte pas. Aucun tirage : la sélection est la même à chaque exécution. Qui gagne le ballon reste au contact
(`match._step_loose_ball`) ; le duel aérien est le ticket 15b.

Constantes validées par le propriétaire le 23/11/2026 (« Validées telles quelles », chiffres réels non trouvés) :
- `AERIAL_ATTACKERS` : au plus deux joueurs par équipe (fixé par le ticket) ;
- `SECOND_ATTACKER_GAP_S` : le second n'y va que s'il touche le ballon au plus 1,0 s après le premier de son équipe ;
- `ATTACKER_HOLD_S` : un joueur désigné le reste tant qu'un coéquipier n'arrive pas 0,3 s plus tôt que lui ; le même
  maintien s'ajoute à l'écart du second déjà en route (1,3 s).
Recherche du point de contact : `STEP_S` et `HORIZON_S`, les valeurs de la lecture d'occasion
(`occasion.REACH_STEP_S`, `occasion.REACH_HORIZON_S`), horizon prolongé jusqu'à la retombée du ballon, au plus
`vol.MAX_FLIGHT_S` (un long ballon vole plus de 3 s : sans cela, personne n'attendrait sous sa chute) ; contact à
`TOUCH_M` (`match.CONTROL_RADIUS_M`)."""

from __future__ import annotations

import math
from dataclasses import dataclass, replace

from v2engine.atteinte import reach_m
from v2engine.ball_state import BallState
from v2engine.condition import effective_rating
from v2engine.geometry import Vec2
from v2engine.movement import PlayerState, max_speed_mps
from v2engine.possession import BALL_FRICTION_PER_S, BALL_STOPPED_MPS
from v2engine.vol import GRAVITY_MPS2, MAX_FLIGHT_S, height_at

AERIAL_ATTACKERS = 2
SECOND_ATTACKER_GAP_S = 1.0
ATTACKER_HOLD_S = 0.3
STEP_S = 0.1
HORIZON_S = 3.0
TOUCH_M = 0.41

BALLON_AERIEN = "ballon aérien"  # rôle du joueur désigné qui n'est pas le receveur visé


@dataclass(frozen=True)
class AerialAttacker:
    """Joueur désigné sur un ballon aérien : son équipe, le point visé, l'instant (s, depuis ce pas) où il peut y toucher
    le ballon, à temps ou non (`on_time`), son rang dans son équipe (0 : le premier) et l'instant où il arrive au point."""

    team: str
    point: Vec2
    contact_s: float
    on_time: bool
    rank: int
    arrival_s: float


def is_aerial_ball(ball: BallState) -> bool:
    """Ballon libre en l'air, pas encore roulant : ni porteur, ni ballon mort, ni tir en vol, et encore en mouvement."""
    return (ball.holder is None and ball.restart is None and not ball.shot_in_flight
            and (ball.z > 0.0 or ball.vz > 0.0) and ball.velocity.length() >= BALL_STOPPED_MPS)


def _arrival_s(player: PlayerState, point: Vec2) -> float:
    """Temps pour toucher le ballon en `point`, à sa vitesse de pointe (`occasion._arrival_s`)."""
    return max(0.0, player.position.distance_to(point) - TOUCH_M) / max_speed_mps(effective_rating(player, "Pace"))


def ball_path(ball: BallState) -> list[tuple[float, Vec2, float]]:
    """Points (instant, position, hauteur) de la trajectoire freinée du ballon, rebonds compris, sur `HORIZON_S` ou
    jusqu'au pas qui suit sa retombée si elle est plus tardive (au plus `MAX_FLIGHT_S`)."""
    log_f = math.log(BALL_FRICTION_PER_S)
    landing_s = (ball.vz + math.sqrt(ball.vz * ball.vz + 2.0 * GRAVITY_MPS2 * max(0.0, ball.z))) / GRAVITY_MPS2
    horizon_s = max(HORIZON_S, min(MAX_FLIGHT_S, landing_s) + STEP_S)  # un point après la retombée
    points, k = [], 0
    while k * STEP_S <= horizon_s + 1e-9:
        t = k * STEP_S
        travelled = (BALL_FRICTION_PER_S ** t - 1.0) / log_f
        points.append((t, ball.position + ball.velocity * travelled, height_at(ball.z, ball.vz, t)))
        k += 1
    return points


def contact_point(player: PlayerState,
                  path: list[tuple[float, Vec2, float]]) -> tuple[float, Vec2, bool, float] | None:
    """(instant du contact, point, à temps, arrivée au point) : premier point de `path` où le ballon passe à sa portée
    et où il arrive à temps ; sinon, parmi les points à sa portée, celui où il arrive le moins en retard (le contact est
    alors à son arrivée). `None` si le ballon ne passe jamais à sa portée sur l'horizon."""
    reach = reach_m(player)
    late: tuple[float, float, Vec2] | None = None
    for t, point, z in path:
        if z > reach:
            continue
        arrival = _arrival_s(player, point)
        if arrival <= t:
            return t, point, True, arrival
        if late is None or arrival - t < late[0]:
            late = (arrival - t, arrival, point)
    return None if late is None else (late[1], late[2], False, late[1])


def select_attackers(ball: BallState, players: list[PlayerState],
                     previous: dict[str, AerialAttacker] | None = None) -> dict[str, AerialAttacker]:
    """Joueurs désignés de chaque équipe sur un ballon aérien (vide sinon), par nom. Classement : à temps avant en
    retard, puis instant du contact (le plus grand ou le meilleur sauteur touche plus tôt un ballon qui descend), puis
    arrivée au point, où un désigné du pas précédent (`previous`) garde l'avantage de `ATTACKER_HOLD_S`. Le
    receveur visé est toujours retenu ; le second n'y va que s'il arrive au plus `SECOND_ATTACKER_GAP_S` après le
    premier de son équipe."""
    if not is_aerial_ball(ball):
        return {}
    previous = previous or {}
    path = ball_path(ball)
    chosen: dict[str, AerialAttacker] = {}
    for team in ("home", "away"):
        options = []
        for p in players:
            if p.team != team or p.poste == "GK" or p.name == ball.released_by \
                    or (p.name in ball.offside_watch and p.name != ball.receiver):
                continue  # le passeur ne touche pas le ballon qu'il lâche (ticket 25) ; signalé hors-jeu à la passe : il
                # ne joue pas ce ballon (le receveur visé y va, comme avant)
            found = contact_point(p, path)
            if found is None and p.name != ball.receiver:
                continue
            contact_s, point, on_time, arrival_s = found if found is not None else (math.inf, p.position, False, math.inf)
            hold = ATTACKER_HOLD_S if p.name in previous else 0.0
            # instant du contact arrondi au pas : celui d'un joueur à temps ne dépend que de sa portée (stable)
            key = (p.name != ball.receiver, not on_time, round(contact_s, 6), arrival_s - hold, p.name)
            options.append((key, AerialAttacker(team, point, contact_s, on_time, 0, arrival_s), p.name))
        options.sort(key=lambda o: o[0])
        first_arrival_s = min((o[1].arrival_s for o in options), default=math.inf)
        for _, attacker, name in options[:AERIAL_ATTACKERS]:
            rank = sum(1 for a in chosen.values() if a.team == team)
            # le second déjà en route garde aussi l'avantage du maintien : sans lui, il partirait et s'arrêterait au gré
            # des petites variations des temps d'arrivée
            gap_s = SECOND_ATTACKER_GAP_S + (ATTACKER_HOLD_S if name in previous else 0.0)
            if rank > 0 and name != ball.receiver and attacker.arrival_s > first_arrival_s + gap_s:
                continue
            chosen[name] = replace(attacker, rank=rank)
    return chosen

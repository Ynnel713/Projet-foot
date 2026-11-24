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
- `ATTACKER_HOLD_S` : un joueur désigné garde sa place (et le premier sa priorité sur le second) tant qu'un coéquipier
  ne touche pas le ballon plus de 0,3 s avant lui, ni ne le touche au plus tard au même instant en arrivant plus de
  0,3 s avant lui (règle double, ticket 15a2, choisie par le propriétaire le 24/11/2026) ; le même maintien s'ajoute à l'écart du second déjà en route (1,3 s).
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


def _neutral_key(entry: tuple[str, AerialAttacker], receiver: str | None) -> tuple:
    """Clé hors maintien : receveur visé d'abord, puis à temps avant en retard, instant du contact (arrondi : celui d'un
    joueur à temps ne dépend que de sa portée), arrivée, nom."""
    name, a = entry
    return name != receiver, not a.on_time, round(a.contact_s, 6), a.arrival_s, name


def _displaces(challenger: tuple[str, AerialAttacker], holder: tuple[str, AerialAttacker],
               receiver: str | None) -> bool:
    """Règle double du maintien (ticket 15a2, choisie par le propriétaire le 24/11/2026) : `challenger` prend la place
    de `holder` s'il passe avant lui sur le receveur visé ou le fait d'être à temps ; à égalité sur ces deux points, s'il
    touche le ballon plus de `ATTACKER_HOLD_S` avant lui, ou le touche au plus tard au même instant et arrive plus de
    `ATTACKER_HOLD_S` avant lui."""
    head_c, head_h = _neutral_key(challenger, receiver)[:2], _neutral_key(holder, receiver)[:2]
    if head_c != head_h:
        return head_c < head_h
    c, h = challenger[1], holder[1]
    c_contact, h_contact = round(c.contact_s, 6), round(h.contact_s, 6)
    return (c_contact < round(h.contact_s - ATTACKER_HOLD_S, 6)
            or (c_contact <= h_contact and c.arrival_s < h.arrival_s - ATTACKER_HOLD_S))


def fill_places(candidates: list[tuple[str, AerialAttacker]], previous_rank: dict[str, int],
                receiver: str | None) -> list[tuple[str, AerialAttacker]]:
    """Joueurs d'une équipe pour les places de premier puis de second (au plus `AERIAL_ATTACKERS`), place par place
    (ticket 15a3) : le titulaire, plus ancien désigné encore candidat (premier du pas précédent, puis second, de rang
    `previous_rank`), garde la place sauf si un coéquipier le déplace (`_displaces`) ; le mieux classé hors maintien
    (`_neutral_key`) parmi ceux qui le déplacent la prend alors. Sans titulaire, le mieux classé hors maintien. Le
    résultat ne dépend pas de l'ordre de `candidates` (un classement deux à deux n'était pas transitif à trois joueurs,
    réserve A1 du 15a2)."""
    remaining = sorted(candidates, key=lambda e: _neutral_key(e, receiver))
    places: list[tuple[str, AerialAttacker]] = []
    while remaining and len(places) < AERIAL_ATTACKERS:
        seniors = sorted((e for e in remaining if e[0] in previous_rank), key=lambda e: previous_rank[e[0]])
        if seniors:
            holder = seniors[0]
            winner = next((e for e in remaining if e is not holder and _displaces(e, holder, receiver)), holder)
        else:
            winner = remaining[0]
        places.append(winner)
        remaining = [e for e in remaining if e is not winner]
    return places


def select_attackers(ball: BallState, players: list[PlayerState],
                     previous: dict[str, AerialAttacker] | None = None) -> dict[str, AerialAttacker]:
    """Joueurs désignés de chaque équipe sur un ballon aérien (vide sinon), par nom. Classement : à temps avant en
    retard, puis instant du contact (le plus grand ou le meilleur sauteur touche plus tôt un ballon qui descend), puis
    arrivée au point ; un désigné du pas précédent (`previous`) garde sa place, et le premier sa priorité sur le second,
    selon la règle double du maintien (`fill_places`, tickets 15a2 et 15a3). Le receveur visé est toujours retenu ; le second n'y va
    que s'il arrive au plus `SECOND_ATTACKER_GAP_S` après le premier de son équipe."""
    if not is_aerial_ball(ball):
        return {}
    previous = previous or {}
    path = ball_path(ball)
    chosen: dict[str, AerialAttacker] = {}
    for team in ("home", "away"):
        candidates = []
        for p in players:
            if p.team != team or p.poste == "GK" or p.name == ball.released_by \
                    or (p.name in ball.offside_watch and p.name != ball.receiver):
                continue  # le passeur ne touche pas le ballon qu'il lâche (ticket 25) ; signalé hors-jeu à la passe : il
                # ne joue pas ce ballon (le receveur visé y va, comme avant)
            found = contact_point(p, path)
            if found is None and p.name != ball.receiver:
                continue
            contact_s, point, on_time, arrival_s = found if found is not None else (math.inf, p.position, False, math.inf)
            candidates.append((p.name, AerialAttacker(team, point, contact_s, on_time, 0, arrival_s)))
        previous_rank = {name: previous[name].rank for name, _ in candidates if name in previous}
        first_arrival_s = min((a.arrival_s for _, a in candidates), default=math.inf)
        for name, attacker in fill_places(candidates, previous_rank, ball.receiver):
            rank = sum(1 for a in chosen.values() if a.team == team)
            # le second déjà en route garde aussi l'avantage du maintien : sans lui, il partirait et s'arrêterait au gré
            # des petites variations des temps d'arrivée
            gap_s = SECOND_ATTACKER_GAP_S + (ATTACKER_HOLD_S if name in previous else 0.0)
            if rank > 0 and name != ball.receiver and attacker.arrival_s > first_arrival_s + gap_s:
                continue
            chosen[name] = replace(attacker, rank=rank)
    return chosen

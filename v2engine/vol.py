"""Hauteur du ballon (ticket v2-hauteur-ballon/02a1, révision de D-V03) : le ballon a une hauteur `z` et une vitesse
verticale `vz` ; il part d'une passe en l'air avec la vitesse verticale qui le fait retomber sur son point visé, monte
et redescend en chute libre, rebondit puis roule. La vitesse horizontale garde sa loi (freinage `BALL_FRICTION_PER_S`
dans `match._step_ball`) ; ce module ne règle que la verticale.

Constantes validées par le propriétaire le 23/11/2026 :
- `GRAVITY_MPS2` : physique ;
- `GROUND_RESTITUTION` (0,70) et `BOUNCE_HORIZONTAL_KEEP` (0,85) : valeurs de la V1 (`ligue1sim/animation/ball.py`,
  Phase 6, Bloc B2), un rebond monte à 49 % du précédent ;
- `BOUNCE_STOP_M` : un rebond dont le sommet serait sous 15 cm est supprimé, le ballon roule (V1, réglage B1) ;
- `MAX_FLIGHT_S` : la durée de vol est plafonnée à 4 s (sommet de 19,6 m) ; sans plafond, le freinage horizontal du
  moteur ferait monter un ballon de 55 m à 36 m. Plafonné, le ballon retombe avant sa cible ;
- `AERIAL_HEIGHT_M` : au-dessus de 2,5 m, le ballon est « aérien » (mode tracé, affichage). Depuis le ticket
  v2-hauteur-ballon/03a, qui touche le ballon dépend de l'atteinte de chaque joueur (`atteinte.reach_m`).
Repères réels (temps de vol et sommet d'un dégagement, d'un centre, d'une passe lobée) : non trouvés."""

from __future__ import annotations

import math

from v2engine.possession import BALL_FRICTION_PER_S

GRAVITY_MPS2 = 9.81
GROUND_RESTITUTION = 0.70
BOUNCE_HORIZONTAL_KEEP = 0.85
BOUNCE_STOP_M = 0.15
MAX_FLIGHT_S = 4.0
AERIAL_HEIGHT_M = 2.5


def flight_time_s(distance_m: float, speed_mps: float, tick_s: float = 0.0) -> float:
    """Durée de vol pour que le ballon, parti à `speed_mps` et freiné (`BALL_FRICTION_PER_S`), retombe après
    `distance_m` : `T = −ln(1 − d·λ / v0) / λ`, plafonnée à `MAX_FLIGHT_S` (y compris quand `d·λ ≥ v0` : le ballon
    n'arriverait jamais, il retombe avant). `tick_s` > 0 : même calcul sur l'avance pas à pas du moteur (le ballon
    avance de `v·dt` puis freine, environ 2,6 % plus loin que la loi continue à 0,1 s), pour retomber sur le point."""
    if distance_m <= 0.0 or speed_mps <= 0.0:
        return 0.0
    if tick_s > 0.0:
        q = BALL_FRICTION_PER_S ** tick_s
        share = distance_m * (1.0 - q) / (speed_mps * tick_s)
        if share >= 1.0:
            return MAX_FLIGHT_S
        return min(MAX_FLIGHT_S, math.log(1.0 - share) / math.log(q) * tick_s)
    lam = -math.log(BALL_FRICTION_PER_S)
    share = distance_m * lam / speed_mps
    if share >= 1.0:
        return MAX_FLIGHT_S
    return min(MAX_FLIGHT_S, -math.log(1.0 - share) / lam)


def launch_vz(distance_m: float, speed_mps: float, tick_s: float = 0.0) -> float:
    """Vitesse verticale de départ (m/s) d'un ballon en l'air qui doit retomber après `distance_m` : `g·T / 2`
    (`tick_s` : pas du moteur, voir `flight_time_s`)."""
    return GRAVITY_MPS2 * flight_time_s(distance_m, speed_mps, tick_s) / 2.0


def line_crossing_s(distance_m: float, speed_mps: float, tick_s: float) -> float | None:
    """Instant (s) où le ballon, parti à `speed_mps` et avancé pas à pas comme dans le moteur (`v·dt`, puis freinage
    `BALL_FRICTION_PER_S`), a parcouru `distance_m`, interpolé dans le pas comme le point de sortie
    (`restart.exit_point`) ; `None` s'il s'arrête avant (ticket v2-hauteur-ballon/02a2)."""
    if distance_m <= 0.0:
        return 0.0
    q = BALL_FRICTION_PER_S ** tick_s
    travelled, step, k = 0.0, speed_mps * tick_s, 0
    while step > 1e-9 and k * tick_s <= MAX_FLIGHT_S:
        if travelled + step >= distance_m:
            return (k + (distance_m - travelled) / step) * tick_s
        travelled, step, k = travelled + step, step * q, k + 1
    return None


def shot_launch_vz(distance_m: float, speed_mps: float, line_height_m: float, tick_s: float) -> float:
    """Vitesse verticale de départ d'un tir (ticket v2-hauteur-ballon/02a2) : le ballon, frappé du sol, passe la ligne
    (à `distance_m` sur sa trajectoire) à `line_height_m`, la hauteur qui fixe déjà son issue (visée + pente,
    `shooting.SHOT_AIM_HEIGHT_M`) : `vz0 = (h + g·t²/2) / t`. Le ballon reste au-dessus du sol jusqu'à la ligne, sans
    rebond (sa vitesse horizontale, donc l'issue du tir, est inchangée). Hauteur nulle ou négative à la ligne, ou ligne
    jamais atteinte : tir rasant (`0`), le ballon roule."""
    t = line_crossing_s(distance_m, speed_mps, tick_s)
    if t is None or t <= 0.0 or line_height_m <= 0.0:
        return 0.0
    return (line_height_m + GRAVITY_MPS2 * t * t / 2.0) / t


def step_height(z: float, vz: float, dt: float) -> tuple[float, float, int]:
    """Avance la hauteur de `dt` secondes : chute libre exacte, impact au sol coupé à l'instant exact, rebond
    (`GROUND_RESTITUTION`), puis le ballon roule quand le rebond serait sous `BOUNCE_STOP_M`. Retourne `(z, vz, n)`,
    `n` le nombre d'impacts pendant le pas (la vitesse horizontale perd `1 − BOUNCE_HORIZONTAL_KEEP` à chacun)."""
    impacts = 0
    left = dt
    while left > 0.0 and (z > 0.0 or vz > 0.0):
        hit = (vz + math.sqrt(vz * vz + 2.0 * GRAVITY_MPS2 * z)) / GRAVITY_MPS2  # instant d'impact
        if hit >= left:
            return max(0.0, z + vz * left - GRAVITY_MPS2 * left * left / 2.0), vz - GRAVITY_MPS2 * left, impacts
        impacts += 1
        left -= hit
        vz = -GROUND_RESTITUTION * (vz - GRAVITY_MPS2 * hit)
        z = 0.0
        if vz * vz / (2.0 * GRAVITY_MPS2) < BOUNCE_STOP_M:
            vz = 0.0
    if left <= 0.0 and (z > 0.0 or vz > 0.0):
        return z, vz, impacts  # durée nulle : le ballon reste où il est (ticket v2-hauteur-ballon/03a)
    return 0.0, 0.0, impacts


def height_at(z: float, vz: float, t: float) -> float:
    """Hauteur du ballon dans `t` secondes (rebonds compris), sans rien modifier."""
    return step_height(z, vz, t)[0]


def is_aerial_height(z: float) -> bool:
    """Ballon « aérien » : au-dessus de `AERIAL_HEIGHT_M` (mode tracé ; le contact suit `atteinte.reach_m`)."""
    return z > AERIAL_HEIGHT_M

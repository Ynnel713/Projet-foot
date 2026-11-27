"""Loi de freinage horizontal du ballon : seul module qui la connaît (interface du ticket v2-realisme/14a1). Passes,
interceptions, gardien, tirs, vol (`hauteur`) et pas du ballon (`match._step_ball`) passent par les fonctions ci-dessous.

Loi (ticket v2-realisme/14a2a, constantes validées par le propriétaire le 26/11/2026) : roulement constant plus traînée
quadratique, `dv/dt = −(a + k·v²)`, `k = ½·ρ·Cd·A / m`, avec une **crise de traînée en palier** : `Cd` = 0,45 sous
15 m/s, 0,25 dès 15 m/s. Au sol, le ballon s'arrête en un temps fini. **En vol** (ticket v2-realisme/14a2b, paramètre
`airborne`) : traînée seule, `dv/dt = −k·v²`, sans roulement ; le ballon ne s'arrête jamais en l'air (toute distance est
atteinte en un temps fini). Seule la vitesse horizontale est freinée (la vitesse verticale suit la chute libre de
`hauteur`). Sources (détail dans `.scratch/v2-realisme/issues/14a2-roulement-et-trainee.md`) :
- roulement 1,2 m/s² : FIFA, classement des pelouses naturelles, roulé de 4 à 10 m depuis la rampe (0,6 à 1,5 m/s²) ;
- crise entre Re 2,2 et 3,0·10⁵, soit 15 à 20 m/s (Asai et al. 2007), `Cd` ≈ 0,45 au-dessous ; 0,25 au-dessus sur de
  vraies frappes (Goff & Carré 2009) ;
- masse 0,43 kg, rayon 0,11 m (Lois du jeu), air 1,225 kg/m³.

Sur un morceau à `a` et `k` fixes, solutions exactes : `w = √(a/k)`, `c = √(a·k)`, `θ = atan(v/w)` ;
`v(t) = w·tan(θ0 − c·t)` (arrêt à `θ0 / c`), `x(t) = ln(cos(θ0 − c·t) / cos θ0) / k`, distance entre deux vitesses
`ln((a + k·v0²) / (a + k·v1²)) / 2k`. Un ballon au-dessus de 15 m/s parcourt un morceau « sur-critique » jusqu'à 15 m/s,
puis le morceau « sous-critique ». En vol (`a = 0`) : `v(t) = v0 / (1 + k·v0·t)`, `x(t) = ln(1 + k·v0·t) / k`, distance
entre deux vitesses `ln(v0 / v1) / k`, temps `(1/v1 − 1/v0) / k`.

Deux lectures du temps :
- **continue** (`dt = 0`, prévisions des joueurs) : solutions exactes ci-dessus ;
- **au pas du moteur** (`dt > 0`) : le moteur avance le ballon de `v·dt` puis prend la vitesse exacte en fin de pas
  (`step_velocity`) ; distance et temps de trajet suivent cette boucle exactement (cumul des pas, interpolation linéaire
  dans le pas, comme `restart.exit_point` coupe la trajectoire).

Le ballon va en ligne droite (pas d'effet avant `v2-realisme/14b`) : une position prévue est la position actuelle plus la
distance parcourue dans la direction de la vitesse."""

from __future__ import annotations

import bisect
import math
from functools import lru_cache

from v2engine.geometry import Vec2

ROLLING_DECEL_M_S2 = 1.2  # roulement sur gazon (validé le 26/11/2026)
AIR_DENSITY_KG_M3 = 1.225
BALL_MASS_KG = 0.43
BALL_RADIUS_M = 0.11  # le même que `match.BALL_RADIUS_M` (test)
DRAG_CRISIS_MPS = 15.0  # palier de la crise de traînée (Re ≈ 2,2·10⁵)
CD_SUBCRITICAL = 0.45  # sous 15 m/s
CD_SUPERCRITICAL = 0.25  # dès 15 m/s


def _drag_k(cd: float) -> float:
    """`k = ½·ρ·Cd·A / m` (1/m) : décélération de traînée = `k·v²`."""
    return 0.5 * AIR_DENSITY_KG_M3 * cd * math.pi * BALL_RADIUS_M**2 / BALL_MASS_KG


K_LOW = _drag_k(CD_SUBCRITICAL)  # ≈ 0,0244
K_HIGH = _drag_k(CD_SUPERCRITICAL)  # ≈ 0,0135
_A = ROLLING_DECEL_M_S2
_V_STAR = DRAG_CRISIS_MPS
# Fin de la table d'un ballon en vol (constante de calcul, pas de jeu) : sous cette vitesse horizontale, il n'arrive plus
# nulle part (plus de 250 m parcourus depuis 30 m/s, plus de 400 s de vol).
_AIR_FLOOR_MPS = 0.1


def _k(speed_mps: float) -> float:
    return K_HIGH if speed_mps >= _V_STAR else K_LOW


def deceleration(speed_mps: float, airborne: bool = False) -> float:
    """Décélération (m/s²) d'un ballon à `speed_mps` ; nulle à l'arrêt. En vol (`airborne`) : traînée seule."""
    if speed_mps <= 0.0:
        return 0.0
    return (0.0 if airborne else _A) + _k(speed_mps) * speed_mps * speed_mps


# --- un morceau à `k` fixe ------------------------------------------------------------------------------------------

def _w_c(k: float) -> tuple[float, float]:
    return math.sqrt(_A / k), math.sqrt(_A * k)


def _seg_time(k: float, v0: float, v1: float) -> float:
    """Temps pour passer de `v0` à `v1` (≤ `v0`) sur un morceau."""
    w, c = _w_c(k)
    return (math.atan(v0 / w) - math.atan(v1 / w)) / c


def _seg_distance(k: float, v0: float, v1: float) -> float:
    """Distance pour passer de `v0` à `v1` (≤ `v0`) sur un morceau."""
    return math.log((_A + k * v0 * v0) / (_A + k * v1 * v1)) / (2.0 * k)


def _seg_speed(k: float, v0: float, t: float) -> float:
    """Vitesse après `t` sur un morceau (0 une fois arrêté)."""
    w, c = _w_c(k)
    theta = math.atan(v0 / w) - c * t
    return w * math.tan(theta) if theta > 0.0 else 0.0


def _seg_travel(k: float, v0: float, t: float) -> float:
    """Distance après `t` sur un morceau (bornée à l'arrêt)."""
    w, c = _w_c(k)
    theta0 = math.atan(v0 / w)
    theta = max(0.0, theta0 - c * t)
    return math.log(math.cos(theta) / math.cos(theta0)) / k


def _seg_launch(k: float, distance_m: float, v1: float) -> float:
    """Vitesse de départ pour arriver à `v1` après `distance_m` sur un morceau."""
    return math.sqrt(max(0.0, ((_A + k * v1 * v1) * math.exp(2.0 * k * distance_m) - _A) / k))


def _seg_arrival(k: float, v0: float, distance_m: float) -> float:
    """Vitesse après `distance_m` sur un morceau (0 s'il s'arrête avant)."""
    rest = (_A + k * v0 * v0) * math.exp(-2.0 * k * distance_m) - _A
    return math.sqrt(rest / k) if rest > 0.0 else 0.0


# --- en vol : traînée seule (ticket v2-realisme/14a2b) -------------------------------------------------------------

def _air_time(v0: float, v1: float) -> float:
    """Temps en vol pour passer de `v0` à `v1` (0 < `v1` ≤ `v0`)."""
    if v0 > _V_STAR > v1:
        return (1.0 / _V_STAR - 1.0 / v0) / K_HIGH + (1.0 / v1 - 1.0 / _V_STAR) / K_LOW
    return (1.0 / v1 - 1.0 / v0) / _k(v1)


def _air_speed_after(speed_mps: float, t: float) -> float:
    if speed_mps > _V_STAR:
        t_high = _air_time(speed_mps, _V_STAR)
        if t < t_high:
            return speed_mps / (1.0 + K_HIGH * speed_mps * t)
        return _V_STAR / (1.0 + K_LOW * _V_STAR * (t - t_high))
    return speed_mps / (1.0 + K_LOW * speed_mps * t)


def _air_distance(speed_mps: float, t: float) -> float:
    if speed_mps > _V_STAR:
        t_high = _air_time(speed_mps, _V_STAR)
        if t < t_high:
            return math.log1p(K_HIGH * speed_mps * t) / K_HIGH
        return math.log(speed_mps / _V_STAR) / K_HIGH + math.log1p(K_LOW * _V_STAR * (t - t_high)) / K_LOW
    return math.log1p(K_LOW * speed_mps * t) / K_LOW


def _air_arrival(speed_mps: float, distance_m: float) -> float:
    """Vitesse en vol après `distance_m` (jamais nulle)."""
    if speed_mps > _V_STAR:
        high = math.log(speed_mps / _V_STAR) / K_HIGH
        if distance_m < high:
            return speed_mps * math.exp(-K_HIGH * distance_m)
        return _V_STAR * math.exp(-K_LOW * (distance_m - high))
    return speed_mps * math.exp(-K_LOW * distance_m)


# --- loi complète (continue) ----------------------------------------------------------------------------------------

def speed_after(speed_mps: float, t: float, airborne: bool = False) -> float:
    """Vitesse d'un ballon parti à `speed_mps`, `t` secondes plus tard (0 une fois arrêté). En vol (`airborne`) :
    traînée seule, tout le temps `t` en l'air."""
    if speed_mps <= 0.0 or t <= 0.0:
        return max(0.0, speed_mps)
    if airborne:
        return _air_speed_after(speed_mps, t)
    if speed_mps > _V_STAR:
        t_high = _seg_time(K_HIGH, speed_mps, _V_STAR)
        if t < t_high:
            return _seg_speed(K_HIGH, speed_mps, t)
        return _seg_speed(K_LOW, _V_STAR, t - t_high)
    return _seg_speed(K_LOW, speed_mps, t)


def _continuous_distance(speed_mps: float, t: float) -> float:
    if speed_mps <= 0.0 or t <= 0.0:
        return 0.0
    if speed_mps > _V_STAR:
        t_high = _seg_time(K_HIGH, speed_mps, _V_STAR)
        if t < t_high:
            return _seg_travel(K_HIGH, speed_mps, t)
        return _seg_distance(K_HIGH, speed_mps, _V_STAR) + _seg_travel(K_LOW, _V_STAR, t - t_high)
    return _seg_travel(K_LOW, speed_mps, t)


def distance_to_slow(speed_mps: float, slower_mps: float) -> float:
    """Distance pour passer de `speed_mps` à `slower_mps` (`slower_mps` = 0 : distance d'arrêt)."""
    v0, v1 = max(0.0, speed_mps), max(0.0, slower_mps)
    if v1 >= v0:
        return 0.0
    if v0 > _V_STAR > v1:
        return _seg_distance(K_HIGH, v0, _V_STAR) + _seg_distance(K_LOW, _V_STAR, v1)
    return _seg_distance(K_HIGH if v1 >= _V_STAR else K_LOW, v0, v1)


def time_to_slow(speed_mps: float, slower_mps: float) -> float:
    """Temps pour passer de `speed_mps` à `slower_mps` (`slower_mps` = 0 : temps d'arrêt, fini)."""
    v0, v1 = max(0.0, speed_mps), max(0.0, slower_mps)
    if v1 >= v0:
        return 0.0
    if v0 > _V_STAR > v1:
        return _seg_time(K_HIGH, v0, _V_STAR) + _seg_time(K_LOW, _V_STAR, v1)
    return _seg_time(K_HIGH if v1 >= _V_STAR else K_LOW, v0, v1)


def launch_speed(distance_m: float, arrival_mps: float) -> float:
    """Vitesse de départ pour arriver à `arrival_mps` après `distance_m` (sans plafond : à l'appelant)."""
    if distance_m <= 0.0:
        return arrival_mps
    if arrival_mps >= _V_STAR:
        return _seg_launch(K_HIGH, distance_m, arrival_mps)
    low = _seg_distance(K_LOW, _V_STAR, arrival_mps)  # distance sous-critique pour ralentir de 15 m/s à l'arrivée
    if distance_m <= low:
        return _seg_launch(K_LOW, distance_m, arrival_mps)
    return _seg_launch(K_HIGH, distance_m - low, _V_STAR)


def arrival_speed(speed_mps: float, distance_m: float) -> float:
    """Vitesse après `distance_m` d'un ballon parti à `speed_mps` ; 0 s'il s'arrête avant."""
    if distance_m <= 0.0:
        return max(0.0, speed_mps)
    if speed_mps > _V_STAR:
        high = _seg_distance(K_HIGH, speed_mps, _V_STAR)
        if distance_m < high:
            return _seg_arrival(K_HIGH, speed_mps, distance_m)
        return _seg_arrival(K_LOW, _V_STAR, distance_m - high)
    return _seg_arrival(K_LOW, max(0.0, speed_mps), distance_m)


def position_after(position: Vec2, velocity: Vec2, t: float) -> Vec2:
    """Position prévue (lecture continue) d'un ballon en `position` à `velocity`, `t` secondes plus tard."""
    return position + velocity.normalized() * _continuous_distance(velocity.length(), t)


def stop_position(position: Vec2, velocity: Vec2) -> Vec2:
    """Point où le ballon s'arrête (lecture continue)."""
    return position + velocity.normalized() * distance_to_slow(velocity.length(), 0.0)


# --- pas du moteur --------------------------------------------------------------------------------------------------

def step_velocity(velocity: Vec2, dt: float, airborne: bool = False) -> Vec2:
    """Vitesse après un pas `dt` du moteur (le ballon a déjà avancé de `velocity·dt`) : solution exacte sur le pas. En vol
    (`airborne`, état au début du pas) : traînée seule."""
    speed = velocity.length()
    if speed <= 0.0:
        return velocity
    return velocity * (speed_after(speed, dt, airborne) / speed)


@lru_cache(maxsize=512)
def _stepped_path(speed_mps: float, dt: float) -> tuple[tuple[float, ...], tuple[float, ...]]:
    """Boucle du moteur depuis `speed_mps` : distance cumulée au début de chaque pas et vitesse pendant ce pas, jusqu'à
    l'arrêt. Mise en cache : les tirs partent tous à la même vitesse."""
    done, speeds, total, speed = [], [], 0.0, speed_mps
    while speed > 0.0:
        done.append(total)
        speeds.append(speed)
        total += speed * dt
        speed = speed_after(speed, dt)
    return tuple(done), tuple(speeds)


def _air_steps(speed_mps: float, dt: float):
    """Boucle du moteur en vol (traînée seule) : (distance cumulée au début du pas, vitesse pendant le pas), jusqu'à la fin
    de table `_AIR_FLOOR_MPS`. Paresseuse et sans cache : les vitesses des passes aériennes varient d'une passe à l'autre
    et la table complète compte des milliers de pas."""
    total, speed = 0.0, speed_mps
    while speed >= _AIR_FLOOR_MPS:
        yield total, speed
        total += speed * dt
        speed = _air_speed_after(speed, dt)


def distance_after(speed_mps: float, t: float, dt: float = 0.0, airborne: bool = False) -> float:
    """Distance parcourue en `t` secondes par un ballon parti à `speed_mps` ; `dt` > 0 : au pas du moteur (cumul des
    pas, linéaire dans le pas). En vol (`airborne`) : traînée seule pendant tout `t`."""
    if speed_mps <= 0.0 or t <= 0.0:
        return 0.0
    if airborne:
        if dt <= 0.0:
            return _air_distance(speed_mps, t)
        step, last = int(t / dt + 1e-9), 0.0
        for index, (done, speed) in enumerate(_air_steps(speed_mps, dt)):
            if index == step:
                return done + speed * (t - step * dt)
            last = done + speed * dt
        return last  # au-delà de la fin de table : ballon considéré arrêté
    if dt <= 0.0:
        return _continuous_distance(speed_mps, t)
    done, speeds = _stepped_path(speed_mps, dt)
    step = int(t / dt + 1e-9)
    if step >= len(done):
        return done[-1] + speeds[-1] * dt
    return done[step] + speeds[step] * (t - step * dt)


def stepped_travel_time_s(distance_m: float, speed_mps: float, dt: float, airborne: bool = False) -> float | None:
    """Temps exact que met le moteur à amener le ballon à `distance_m` (ticket v2-hauteur-ballon/02a2) : il avance par pas
    de `dt` et franchit le point en ligne droite à l'intérieur d'un pas. `None` s'il s'arrête avant ; distance nulle : 0.
    En vol (`airborne`, ticket 14a2b) : traînée seule pendant tout le trajet, `None` seulement au-delà de la fin de table."""
    if distance_m <= 0.0:
        return 0.0
    if speed_mps <= 0.0 or dt <= 0.0:
        return None
    if airborne:
        for index, (done, speed) in enumerate(_air_steps(speed_mps, dt)):
            if done + speed * dt >= distance_m:
                return (index + (distance_m - done) / (speed * dt)) * dt
        return None
    done, speeds = _stepped_path(speed_mps, dt)
    step = bisect.bisect_right(done, distance_m) - 1
    if done[step] + speeds[step] * dt < distance_m:
        return None  # arrêté avant
    return (step + (distance_m - done[step]) / (speeds[step] * dt)) * dt


def travel_time_s(distance_m: float, speed_mps: float, dt: float = 0.0, airborne: bool = False) -> float | None:
    """Temps pour parcourir `distance_m` en partant à `speed_mps` (inverse de `distance_after`, même `dt` et même
    `airborne`). `None` si le ballon s'arrête avant ou si la vitesse est nulle. Distance nulle : 0. En vol, lecture
    continue : toujours fini."""
    if distance_m <= 0.0:
        return 0.0
    if speed_mps <= 0.0:
        return None
    if dt > 0.0:
        return stepped_travel_time_s(distance_m, speed_mps, dt, airborne)
    if airborne:
        return _air_time(speed_mps, _air_arrival(speed_mps, distance_m))
    if distance_m >= distance_to_slow(speed_mps, 0.0):
        return None
    return time_to_slow(speed_mps, arrival_speed(speed_mps, distance_m))

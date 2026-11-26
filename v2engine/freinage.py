"""Loi de freinage horizontal du ballon (ticket v2-realisme/14a1) : seul module qui la connaît. Passes, interceptions,
gardien, tirs, vol (`hauteur`) et pas du ballon (`match._step_ball`) passent par les fonctions ci-dessous, jamais par la
constante : changer la loi (ticket v2-realisme/14a2 : roulement + traînée quadratique) ne touche que ce fichier.

Loi actuelle, inchangée depuis la Phase 2 : freinage exponentiel, la vitesse est multipliée par `BALL_FRICTION_PER_S`
chaque seconde (`v(t) = v0·f^t`, λ = −ln f). Deux lectures du temps :
- **continue** (`dt = 0`, prévisions des joueurs) : `x(t) = v0·(f^t − 1) / ln f` ;
- **au pas du moteur** (`dt > 0`) : le moteur avance le ballon de `v·dt` puis freine (`v ← v·f^dt`, Euler explicite),
  `x(t) = v0·dt·(1 − q^(t/dt)) / (1 − q)`, q = f^dt (réserve A1 de l'expert, 02a1).

Le ballon va en ligne droite (pas d'effet avant `v2-realisme/14b`) : une position prévue est la position actuelle plus
la distance parcourue dans la direction de la vitesse."""

from __future__ import annotations

import math

from v2engine.geometry import Vec2

BALL_FRICTION_PER_S = 0.6  # la vitesse est multipliée par 0,6 chaque seconde (pas un coefficient calibré : 14a2)
_LOG_F = math.log(BALL_FRICTION_PER_S)


def speed_after(speed_mps: float, t: float) -> float:
    """Vitesse d'un ballon parti à `speed_mps`, `t` secondes plus tard."""
    return speed_mps * BALL_FRICTION_PER_S**t


def step_velocity(velocity: Vec2, dt: float) -> Vec2:
    """Vitesse après un pas `dt` du moteur (le ballon a déjà avancé de `velocity·dt`)."""
    return velocity * (BALL_FRICTION_PER_S**dt)


def distance_after(speed_mps: float, t: float, dt: float = 0.0) -> float:
    """Distance parcourue en `t` secondes par un ballon parti à `speed_mps` ; `dt` > 0 : au pas du moteur (`t` multiple
    de `dt` ou non, la formule géométrique est prolongée entre les pas)."""
    if dt > 0.0:
        q = BALL_FRICTION_PER_S**dt
        return speed_mps * dt * (1.0 - q ** (t / dt)) / (1.0 - q)
    return speed_mps * ((BALL_FRICTION_PER_S**t - 1.0) / _LOG_F)


def position_after(position: Vec2, velocity: Vec2, t: float) -> Vec2:
    """Position prévue (lecture continue) d'un ballon en `position` à `velocity`, `t` secondes plus tard."""
    return position + velocity * ((BALL_FRICTION_PER_S**t - 1.0) / _LOG_F)


def stop_position(position: Vec2, velocity: Vec2) -> Vec2:
    """Point où le ballon s'arrête (lecture continue)."""
    return position + velocity * (1.0 / -_LOG_F)


def distance_to_slow(speed_mps: float, slower_mps: float) -> float:
    """Distance pour passer de `speed_mps` à `slower_mps` (`slower_mps` = 0 : distance d'arrêt)."""
    return (speed_mps - slower_mps) / -_LOG_F


def launch_speed(distance_m: float, arrival_mps: float) -> float:
    """Vitesse de départ pour arriver à `arrival_mps` après `distance_m` (sans plafond : à l'appelant)."""
    return arrival_mps - distance_m * _LOG_F


def arrival_speed(speed_mps: float, distance_m: float) -> float:
    """Vitesse après `distance_m` d'un ballon parti à `speed_mps` ; négative ou nulle s'il s'arrête avant (l'appelant
    borne)."""
    return speed_mps + distance_m * _LOG_F


def time_to_slow(speed_mps: float, slower_mps: float) -> float:
    """Temps pour passer de `speed_mps` à `slower_mps` (> 0)."""
    return math.log(slower_mps / speed_mps) / _LOG_F


def travel_time_s(distance_m: float, speed_mps: float, dt: float = 0.0) -> float | None:
    """Temps pour parcourir `distance_m` en partant à `speed_mps` (inverse de `distance_after`, même `dt`) :
    `T = −ln(1 − d·λ / v0) / λ` en continu ; au pas du moteur, `d·λ / v0` devient `d·(1 − f^dt) / (v0·dt)`. `None` si
    le ballon s'arrête avant ou si la vitesse est nulle. Distance nulle : 0."""
    if distance_m <= 0.0:
        return 0.0
    if speed_mps <= 0.0:
        return None
    lam = -_LOG_F
    reach = (distance_m * (1.0 - BALL_FRICTION_PER_S**dt) / (speed_mps * dt) if dt > 0.0
             else distance_m * lam / speed_mps)
    if reach >= 1.0:
        return None
    return -math.log1p(-reach) / lam


def shot_travel_time_s(distance_m: float, speed_mps: float, dt: float) -> float:
    """Même temps que `travel_time_s(distance_m, speed_mps, dt)` (inverse de `distance_after` au pas du moteur), écrit
    `dt·ln(1 − d·(1 − q) / (v0·dt)) / ln q` comme l'écrivait `shooting._flight_time_s` : l'arrondi diffère au dernier bit
    de la forme en `log1p`, et la garder laisse le jeu identique au 14a1 (fusion au 14a2, où la loi change). L'infini si
    le ballon s'arrête avant."""
    q = BALL_FRICTION_PER_S**dt
    rest = 1.0 - distance_m * (1.0 - q) / (speed_mps * dt)
    return math.inf if rest <= 0.0 else dt * math.log(rest) / math.log(q)


def stepped_travel_time_s(distance_m: float, speed_mps: float, dt: float) -> float | None:
    """Temps exact que met le moteur à amener le ballon à `distance_m` (ticket v2-hauteur-ballon/02a2) : il avance par pas
    de `dt` (`x += v·dt`, puis freine) et franchit le point en ligne droite à l'intérieur d'un pas, comme
    `restart.exit_point` le coupe. `None` si le ballon s'arrête avant ; distance nulle : 0."""
    if distance_m <= 0.0:
        return 0.0
    if speed_mps <= 0.0 or dt <= 0.0:
        return None
    keep = BALL_FRICTION_PER_S**dt
    done, speed, steps = 0.0, speed_mps, 0
    while done + speed * dt < distance_m:
        done += speed * dt
        speed *= keep
        steps += 1
        if speed * dt < 1e-9:
            return None  # arrêté avant
    return (steps + (distance_m - done) / (speed * dt)) * dt

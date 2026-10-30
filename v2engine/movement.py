"""Modèle de vitesse, accélération et fatigue d'un joueur, dérivé des repères de
`Guide_attributs_joueurs.pdf` (Pace/Acceleration/Stamina). Modèle volontairement simple
(interpolation linéaire par repères) -- pas visé parfait d'entrée (décision du porteur du projet,
session /grill-me du 24/10/2026) : à recalibrer si le rendu le justifie."""

from __future__ import annotations

import math
from dataclasses import dataclass

from v2engine.geometry import Vec2, clamp_to_pitch

KMH_TO_MS = 1.0 / 3.6

# Repères (note, km/h) du guide pour Pace : 99 -> 36-37, 50 -> 30, 10 -> 25.
_PACE_POINTS: tuple[tuple[float, float], ...] = ((10.0, 25.0), (50.0, 30.0), (99.0, 36.5))

# Montée en vitesse (ticket v2-collectif/25, validé le 29/10/2026) : modèle exponentiel du sprint
# v(t) = v_max·(1 − e^(−t/τ)) (Furusawa 1927 ; Samozino et Morin, profil force-vitesse), τ selon Acceleration.
# Accélération au départ v_max/τ : ~7,3 m/s² pour un joueur moyen, 10,1 m/s² au mieux. Réel : footballeurs pros
# F0 = 5,18 N/kg, V0 = 10,29 m/s, soit τ ≈ 2 s (PMC9819841, premier sprint).
_TAU_POINTS: tuple[tuple[float, float], ...] = ((11.0, 1.5), (55.0, 1.2), (99.0, 1.0))
# Freinage borné, le même pour tous en attendant Agility (phase 7) : à l'approche d'une cible et à toute baisse
# d'intensité. Réel : les freinages au-dessus de 3,5 m/s² sont fréquents en match, plus que les accélérations
# (Harper, Carling et Kiely 2019, Sports Medicine) ; valeur maximale non trouvée.
DECEL_MAX_MPS2 = 7.0
ARRIVAL_DEADZONE_M = 0.1  # en deçà, le joueur est arrivé : il ne vise plus aucune vitesse

# Fatigue (Stamina) : plancher de vitesse en fin de match et minute à partir de laquelle la baisse
# démarre, aux deux extrêmes de note (guide : bonne Stamina stable jusqu'à la 85e, mauvaise
# Stamina "s'éteint dès la 60e-65e").
_STAMINA_FLOOR_POINTS: tuple[tuple[float, float], ...] = ((5.0, 0.60), (99.0, 0.97))
_STAMINA_DECAY_START_POINTS: tuple[tuple[float, float], ...] = ((5.0, 45.0), (99.0, 75.0))

MATCH_END_MINUTE = 90.0


def _lerp(note: float, points: tuple[tuple[float, float], ...]) -> float:
    """Interpolation linéaire par repères, bornée aux extrémités (jamais d'extrapolation hors de
    la plage connue)."""
    clamped = min(max(note, points[0][0]), points[-1][0])
    for (n0, v0), (n1, v1) in zip(points, points[1:]):
        if n0 <= clamped <= n1:
            ratio = (clamped - n0) / (n1 - n0) if n1 > n0 else 0.0
            return v0 + ratio * (v1 - v0)
    return points[-1][1]


def max_speed_mps(pace: float) -> float:
    return _lerp(pace, _PACE_POINTS) * KMH_TO_MS


def accel_tau_s(acceleration: float) -> float:
    """Constante de temps τ (s) de la montée en vitesse : 63 % de la vitesse visée après τ."""
    return _lerp(acceleration, _TAU_POINTS)


def stamina_factor(stamina: float, minute: float) -> float:
    """Multiplicateur de vitesse (0-1) dû à la fatigue à `minute` de match -- 1.0 avant le début
    de la baisse, décroît linéairement jusqu'au plancher à la 90e."""
    floor = _lerp(stamina, _STAMINA_FLOOR_POINTS)
    decay_start = _lerp(stamina, _STAMINA_DECAY_START_POINTS)
    if minute <= decay_start:
        return 1.0
    ratio = min(1.0, (minute - decay_start) / (MATCH_END_MINUTE - decay_start))
    return 1.0 - ratio * (1.0 - floor)


@dataclass
class PlayerState:
    name: str
    team: str
    poste: str
    position: Vec2
    velocity: Vec2
    pace: float
    acceleration: float
    stamina: float
    home_target: Vec2  # position de formation à rejoindre hors pressing du ballon (voir match.py)
    radius_m: float = 0.3
    # Attributs bruts du joueur (voir `ligue1sim.players.Player.attributes`), pour les phases
    # suivantes (First Touch, Passing...) via `attributes.player_attribute` -- `pace`/
    # `acceleration`/`stamina` ci-dessus restent des champs dédiés (chemin chaud, lu à chaque
    # tick par `step`), ce champ sert aux attributs plus occasionnels (voir `possession.py`).
    attributes: dict[str, int] | None = None


def step(state: PlayerState, dt: float, target: Vec2, minute: float, speed_factor: float = 1.0,
         target_velocity: Vec2 = Vec2(0.0, 0.0)) -> PlayerState:
    """Avance `state` de `dt` secondes, en dirigeant le joueur vers `target` (sa position de
    formation ou le ballon, voir `match.py`) -- vitesse plafonnée par Pace et la fatigue
    (Stamina), montée en vitesse exponentielle pilotée par Acceleration, freinage borné et loi
    d'arrivée (ticket v2-collectif/25). IA de déplacement volontairement
    simpliste (D-V08) : `target` est choisi par l'appelant, pas par ce module. `speed_factor` :
    part de la vitesse max (ex. conduite de balle, `decision.DRIBBLE_SPEED_FACTOR`). `target_velocity` : vitesse
    de la cible quand elle bouge (le porteur qu'il presse) -- la loi d'arrivée porte alors sur la vitesse de
    rapprochement, sans quoi il resterait à sa distance de freinage derrière un porteur en conduite."""
    effective_max_speed = max_speed_mps(state.pace) * stamina_factor(state.stamina, minute) * speed_factor
    to_target = target - state.position
    distance = to_target.length()
    if distance > ARRIVAL_DEADZONE_M:
        # loi d'arrivée : jamais plus vite que la vitesse dont il peut freiner avant la cible, soit √(2·a·d). Forme
        # en pas discret : la vitesse v' de fin de pas telle qu'il puisse encore s'arrêter après avoir parcouru ce pas
        # ((v + v')/2·dt), pour ne pas dépasser quel que soit `dt`.
        relative = state.velocity - target_velocity
        closing = max(0.0, (relative.x * to_target.x + relative.y * to_target.y) / distance)
        half_step = 0.5 * DECEL_MAX_MPS2 * dt
        room = max(0.0, distance - 0.5 * closing * dt)
        stopping_speed = math.sqrt(half_step * half_step + 2.0 * DECEL_MAX_MPS2 * room) - half_step
        desired_velocity = target_velocity + to_target * (stopping_speed / distance)
        if desired_velocity.length() > effective_max_speed:
            desired_velocity = desired_velocity.normalized() * effective_max_speed
    else:
        desired_velocity = Vec2(0.0, 0.0)

    # Montée en vitesse : forme exacte en pas discret (indépendante de `dt`). Si elle ferait ralentir (baisse
    # d'intensité, arrivée, changement de direction), le joueur freine à `DECEL_MAX_MPS2` vers la vitesse visée.
    velocity = state.velocity
    candidate = desired_velocity + (velocity - desired_velocity) * math.exp(-dt / accel_tau_s(state.acceleration))
    if candidate.length() >= velocity.length():
        new_velocity = candidate
    else:
        delta = desired_velocity - velocity
        brake = DECEL_MAX_MPS2 * dt
        new_velocity = desired_velocity if delta.length() <= brake else velocity + delta * (brake / delta.length())

    # vitesse moyenne du pas (trapèzes) : exacte pour un freinage constant, très proche pour l'exponentielle
    new_position = clamp_to_pitch(state.position + (velocity + new_velocity) * (0.5 * dt))
    return PlayerState(
        name=state.name,
        team=state.team,
        poste=state.poste,
        position=new_position,
        velocity=new_velocity,
        pace=state.pace,
        acceleration=state.acceleration,
        stamina=state.stamina,
        home_target=state.home_target,
        radius_m=state.radius_m,
        attributes=state.attributes,
    )

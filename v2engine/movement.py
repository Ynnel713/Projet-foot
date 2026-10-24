"""Modèle de vitesse, accélération et fatigue d'un joueur, dérivé des repères de
`Guide_attributs_joueurs.pdf` (Pace/Acceleration/Stamina). Modèle volontairement simple
(interpolation linéaire par repères) -- pas visé parfait d'entrée (décision du porteur du projet,
session /grill-me du 24/10/2026) : à recalibrer si le rendu le justifie."""

from __future__ import annotations

from dataclasses import dataclass

from v2engine.geometry import Vec2, clamp_to_pitch

KMH_TO_MS = 1.0 / 3.6

# Repères (note, km/h) du guide pour Pace : 99 -> 36-37, 50 -> 30, 10 -> 25.
_PACE_POINTS: tuple[tuple[float, float], ...] = ((10.0, 25.0), (50.0, 30.0), (99.0, 36.5))

# Le guide ne donne pas de repère chiffré pour Acceleration (description qualitative seulement) :
# temps (s) pour atteindre sa vitesse de pointe, estimé sur la même fourchette de notes.
# ponytail : repères choisis à dire d'expert, pas mesurés -- à recalibrer si le rendu le justifie.
_ACCEL_POINTS: tuple[tuple[float, float], ...] = ((5.0, 2.5), (50.0, 1.5), (99.0, 0.5))

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


def accel_time_s(acceleration: float) -> float:
    return _lerp(acceleration, _ACCEL_POINTS)


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


def step(state: PlayerState, dt: float, target: Vec2, minute: float) -> PlayerState:
    """Avance `state` de `dt` secondes, en dirigeant le joueur vers `target` (sa position de
    formation ou le ballon, voir `match.py`) -- vitesse plafonnée par Pace et la fatigue
    (Stamina), montée en vitesse pilotée par Acceleration. IA de déplacement volontairement
    simpliste (D-V08) : `target` est choisi par l'appelant, pas par ce module."""
    effective_max_speed = max_speed_mps(state.pace) * stamina_factor(state.stamina, minute)
    to_target = target - state.position
    desired_velocity = to_target.normalized() * effective_max_speed if to_target.length() > 0.1 else Vec2(0.0, 0.0)

    accel_time = accel_time_s(state.acceleration)
    accel_mag = effective_max_speed / accel_time if accel_time > 0 else effective_max_speed

    delta = desired_velocity - state.velocity
    delta_length = delta.length()
    max_delta = accel_mag * dt
    if delta_length > 1e-9:
        new_velocity = state.velocity + delta * (min(max_delta, delta_length) / delta_length)
    else:
        new_velocity = state.velocity

    speed = new_velocity.length()
    if speed > effective_max_speed > 0.0:
        new_velocity = new_velocity.normalized() * effective_max_speed

    new_position = clamp_to_pitch(state.position + new_velocity * dt)
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
    )

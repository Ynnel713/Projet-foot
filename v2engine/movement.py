"""Modèle de vitesse, accélération et fatigue d'un joueur, dérivé des repères de
`Guide_attributs_joueurs.pdf` (Pace/Acceleration/Stamina). Modèle volontairement simple
(interpolation linéaire par repères) -- pas visé parfait d'entrée (décision du porteur du projet,
session /grill-me du 24/10/2026) : à recalibrer si le rendu le justifie."""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache

from v2engine.condition import PlayerCondition, effective_rating
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

# Réserve d'énergie (ticket v2-realisme/12e, constantes recommandées et retenues par délégation du propriétaire,
# 11/11/2026), modèle à deux paramètres de la famille vitesse critique / D' (W' balance, Skiba 2012) : la course
# au-dessus de `AEROBIC_SPEED_MPS` (14,4 km/h, haut du trot de Bradley 2009) vide la réserve de l'excès de vitesse
# (m), la course en dessous la recharge à un débit fixe ; Stamina règle la taille et le débit. Valeurs de modèle
# (taille, débit, genou, plancher) : non trouvées telles quelles, calées sur l'effort mesuré du banc après 12d
# (médiane 1 035 m d'excès par match et par joueur de champ, 5 080 s sous 14,4 km/h), puis recharge choisie sur 6 matchs
# entre trois candidates : course au-dessus de 19,8 km/h, dernier quart d'heure réglementaire contre le premier, − 21 %
# pour tous (repère 10 à 30 %), − 27 % sous Stamina 75, − 7 % à 75 et plus et qu'un Stamina haut ne baisse presque pas (guide : bonne Stamina stable
# jusqu'à la 85e, mauvaise Stamina "s'éteint dès la 60e-65e").
AEROBIC_SPEED_MPS = 4.0
_RESERVE_POINTS: tuple[tuple[float, float], ...] = ((5.0, 500.0), (55.0, 1000.0), (99.0, 1500.0))  # m d'excès
_RECOVERY_POINTS: tuple[tuple[float, float], ...] = ((5.0, 0.06), (55.0, 0.15), (99.0, 0.30))  # m/s au repos ;
# rapportée à la réserve, la recharge croît aussi avec Stamina (5 : 0,012 % par seconde ; 99 : 0,020 %)
FATIGUE_KNEE = 0.8  # au-dessus de 80 % de sa réserve, aucune perte de vitesse ; en dessous, perte progressive
FATIGUE_FLOOR = 0.6  # réserve vide : 60 % de sa vitesse max

# Orientation du corps (ticket v2-realisme/07a, valeurs recommandées et validées par délégation du propriétaire,
# 12/11/2026) : le cap (`PlayerState.facing`, direction du corps, distincte de la vitesse) tourne vers la direction
# voulue d'au plus `turn_rate_rad_s(Agility)` par seconde. Direction voulue : le
# sens de course au-dessus de `FACING_RUN_SPEED_MPS` (19,8 km/h, seuil de course rapide du banc), le ballon sinon.
# Demi-tour en 0,5 s : ordre de grandeur, vitesse angulaire réelle du corps d'un footballeur non trouvée. Sans effet sur
# le jeu avant 07b, 07c et 07e : tracé et affiché seulement.
TURN_RATE_RAD_S = math.radians(360.0)  # Agility 55 (note moyenne de la base)
# Vitesse angulaire selon Agility (ticket v2-realisme/07f, valeurs recommandées et validées par délégation du
# propriétaire, 13/11/2026), mêmes repères linéaires que Pace et Acceleration : demi-tour en 0,67 s à 11, 0,5 s à 55,
# 0,4 s à 99 (écart 99/11 de 1,67, proche de celui d'Acceleration, 1,5). Vitesse angulaire réelle : non trouvée.
_TURN_POINTS: tuple[tuple[float, float], ...] = ((11.0, 270.0), (55.0, 360.0), (99.0, 450.0))  # degrés par seconde
FACING_RUN_SPEED_MPS = 19.8 * KMH_TO_MS


@lru_cache(maxsize=None)
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


def turn_rate_rad_s(agility: float) -> float:
    """Vitesse angulaire maximale du corps (rad/s) selon Agility (ticket 07f)."""
    return math.radians(_lerp(agility, _TURN_POINTS))


def energy_factor(energy: float) -> float:
    """Multiplicateur de vitesse max (0-1) selon la part de réserve restante `energy` (ticket 12e)."""
    return FATIGUE_FLOOR + (1.0 - FATIGUE_FLOOR) * min(1.0, energy / FATIGUE_KNEE)


def spend_energy(energy: float, stamina: float, speed_mps: float, dt: float) -> float:
    """Part de réserve après `dt` secondes à `speed_mps` (ticket 12e) : l'excès au-dessus de 14,4 km/h la vide,
    la course plus lente la recharge, bornée à [0, 1]."""
    reserve = _lerp(stamina, _RESERVE_POINTS)
    excess = speed_mps - AEROBIC_SPEED_MPS
    delta = -excess * dt if excess > 0.0 else _lerp(stamina, _RECOVERY_POINTS) * dt
    return min(1.0, max(0.0, energy + delta / reserve))


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
    # Attributs bruts du joueur (voir `ligue1sim.players.Player.attributes`), lus par la façade
    # `condition.effective_rating` (ticket v2-realisme/19a) -- `pace`/`acceleration`/`stamina` ci-dessus restent
    # des champs dédiés (chemin chaud, lu à chaque tick par `step`) ; ailleurs, ils passent aussi par la façade.
    attributes: dict[str, int] | None = None
    role: str = ""  # rôle du joueur (voir `roles.py`), ticket v2-realisme/02c ; sans effet sur le jeu avant 02d/02e/09
    condition: PlayerCondition = PlayerCondition()  # état qui module l'expression des notes (19a ; réserve, 12e)
    facing: Vec2 = Vec2(1.0, 0.0)  # cap du corps, vecteur unitaire (ticket v2-realisme/07a) ; sans effet sur le jeu


def turn_toward(facing: Vec2, desired: Vec2, max_angle_rad: float) -> Vec2:
    """Cap `facing` tourné vers la direction `desired` d'au plus `max_angle_rad`, par le plus court côté (ticket
    v2-realisme/07a). Direction nulle : le cap ne bouge pas."""
    if desired.length() < 1e-9:
        return facing
    current, wanted = math.atan2(facing.y, facing.x), math.atan2(desired.y, desired.x)
    delta = (wanted - current + math.pi) % (2.0 * math.pi) - math.pi
    angle = current + max(-max_angle_rad, min(max_angle_rad, delta))
    return Vec2(math.cos(angle), math.sin(angle))


def desired_facing(position: Vec2, velocity: Vec2, look_at: Vec2 | None) -> Vec2:
    """Direction où le joueur veut tourner le corps (ticket 07a) : sens de course en course rapide, le ballon sinon ;
    sans ballon à regarder (`look_at` absent ou sur lui), le sens de course, ou aucune."""
    if velocity.length() >= FACING_RUN_SPEED_MPS or look_at is None:
        return velocity
    to_ball = look_at - position
    return to_ball if to_ball.length() >= 1e-9 else velocity


def step(state: PlayerState, dt: float, target: Vec2, minute: float, speed_factor: float = 1.0,
         target_velocity: Vec2 = Vec2(0.0, 0.0), look_at: Vec2 | None = None) -> PlayerState:
    """Avance `state` de `dt` secondes, en dirigeant le joueur vers `target` (sa position de
    formation ou le ballon, voir `match.py`) -- vitesse plafonnée par Pace et la fatigue
    (Stamina), montée en vitesse exponentielle pilotée par Acceleration, freinage borné et loi
    d'arrivée (ticket v2-collectif/25). IA de déplacement volontairement
    simpliste (D-V08) : `target` est choisi par l'appelant, pas par ce module. `speed_factor` :
    part de la vitesse max (ex. conduite de balle, `decision.dribble_speed_factor`). `target_velocity` : vitesse
    de la cible quand elle bouge (le porteur qu'il presse) -- la loi d'arrivée porte alors sur la vitesse de
    rapprochement, sans quoi il resterait à sa distance de freinage derrière un porteur en conduite. `look_at` : le
    ballon, que son corps regarde hors course rapide (cap, ticket v2-realisme/07a ; sans effet sur le déplacement)."""
    # fatigue : réserve d'énergie (ticket 12e) ; `minute` n'est plus lue ici (gardée pour les appelants)
    effective_max_speed = max_speed_mps(state.pace) * energy_factor(state.condition.energy) * speed_factor
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
        role=state.role,
        condition=PlayerCondition(energy=spend_energy(state.condition.energy, state.stamina,
                                                      0.5 * (velocity.length() + new_velocity.length()), dt)),
        facing=turn_toward(state.facing, desired_facing(new_position, new_velocity, look_at),
                            turn_rate_rad_s(effective_rating(state, "Agility")) * dt),
    )

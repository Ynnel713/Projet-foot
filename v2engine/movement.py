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
# Freinage borné : à l'approche d'une cible et à toute baisse d'intensité. Réel : les freinages au-dessus de 3,5 m/s²
# sont fréquents en match, plus que les accélérations (Harper, Carling et Kiely 2019, Sports Medicine) ; valeur
# maximale non trouvée. `DECEL_MAX_MPS2` : la valeur commune d'avant le ticket v2-realisme/12a, gardée pour Agility 55.
DECEL_MAX_MPS2 = 7.0
# Freinage selon Agility (ticket v2-realisme/12a, valeurs recommandées et validées par délégation du propriétaire,
# 14/11/2026) : 6 m/s² à 11, 7 à 55 (la valeur commune d'avant : rythme de la base inchangé), 8 à 99 (linéaire ; écart
# 99/11 de 1,33, sous ceux d'Acceleration, 1,5, et de la rotation, 1,67 : le freinage dépend aussi de la force des
# jambes, hors Agility). Depuis 7 m/s : arrêt en 4,1 m à 11, 3,5 m à 55, 3,1 m à 99. Chiffres réels par niveau : non
# trouvés.
_DECEL_POINTS: tuple[tuple[float, float], ...] = ((11.0, 6.0), (55.0, DECEL_MAX_MPS2), (99.0, 8.0))  # m/s²
# Virage selon Agility (ticket v2-realisme/12b, valeurs recommandées et validées par délégation du propriétaire,
# 14/11/2026) : la part de la variation de vitesse perpendiculaire à la course (accélération latérale, v²/R) est bornée,
# 4,5 m/s² à 11, 5,5 à 55, 6,5 à 99 (linéaire) ; la part le long de la course (accélérer, freiner) reste celle de la
# montée en vitesse et du freinage (12a). Un virage serré dure donc plus longtemps, et le freinage qui l'accompagne fait
# perdre plus de vitesse. Ordre de grandeur réel : course en courbe sur le rond central (rayon 9,15 m) vers 7 m/s, soit
# environ 5,4 m/s² (tests de « curve sprint » ; valeur par niveau non trouvée). Sous `LATERAL_FREE_MPS` (2 m/s), pas de
# borne : le joueur pivote sur un appui. Pas de double comptage avec le 07b : celui-ci plafonne la vitesse selon le cap
# (corps pas encore tourné) ; ce ticket borne la courbure de la trajectoire, quel que soit le cap.
_LATERAL_POINTS: tuple[tuple[float, float], ...] = ((11.0, 4.5), (55.0, 5.5), (99.0, 6.5))  # m/s²
LATERAL_FREE_MPS = 2.0
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
# Déplacement selon l'orientation (ticket v2-realisme/07b, valeurs proposées et validées par le propriétaire,
# 13/11/2026) : la vitesse max dépend de l'angle entre la direction voulue et le cap. Pleine vitesse jusqu'à 45°,
# 80 % à 90° (pas chassés, chiffre réel non trouvé), 65 % à 180° (à reculons ; réel : 29 % plus lent que vers l'avant
# sur les 20 premiers mètres, 21 footballeurs universitaires, J Sports Sci 2021 ; vitesse de pointe non trouvée).
_DIRECTION_SPEED_POINTS: tuple[tuple[float, float], ...] = ((45.0, 1.0), (90.0, 0.80), (180.0, 0.65))  # degrés, part
# Se retourner ou reculer (07b) : il tourne le corps vers sa course quand sa cible est à `TURN_TO_RUN_DISTANCE_M` ou
# plus et que le ballon est à plus de `BALL_FREE_ANGLE_DEG` de sa course (en deçà, regarder le ballon ne coûte rien) ;
# il revient face au ballon sous `BACK_TO_BALL_DISTANCE_M`. Seuil de rentabilité : un demi-tour (0,5 s) contre 35 % de
# vitesse perdue à reculons, environ 7,7 m à 30 km/h. Bande de `FACING_RUN_BAND_MPS` autour du seuil de course rapide
# (réserve A1 de l'expert au 07a : pas de flottement du cap autour de 19,8 km/h).
TURN_TO_RUN_DISTANCE_M = 8.0
BACK_TO_BALL_DISTANCE_M = 6.0
BALL_FREE_ANGLE_DEG = 45.0
# Bande sur le cône du ballon (réserve A2 de l'expert au 07b, validée par le propriétaire le 13/11/2026) : retourné vers
# sa course, il ne revient face au ballon que quand celui-ci rentre à 40° de sa course (pas de cap qui tremble à 45°).
BALL_CONE_BAND_DEG = 5.0
FACING_RUN_BAND_MPS = 0.3


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


def decel_max_mps2(agility: float) -> float:
    """Freinage maximal (m/s²) selon Agility (ticket v2-realisme/12a)."""
    return _lerp(agility, _DECEL_POINTS)


def lateral_max_mps2(agility: float) -> float:
    """Accélération latérale maximale (m/s²) selon Agility (ticket v2-realisme/12b)."""
    return _lerp(agility, _LATERAL_POINTS)


def limit_turn(velocity: Vec2, new_velocity: Vec2, lateral_max: float, dt: float) -> Vec2:
    """`new_velocity` dont la part perpendiculaire à `velocity` est bornée à `lateral_max · dt` (ticket 12b) ; la part le
    long de la course est gardée. Sous `LATERAL_FREE_MPS`, inchangée."""
    speed = velocity.length()
    if speed < LATERAL_FREE_MPS:
        return new_velocity
    ux, uy = velocity.x / speed, velocity.y / speed
    change = new_velocity - velocity
    along = change.x * ux + change.y * uy
    lateral = Vec2(change.x - along * ux, change.y - along * uy)
    cap = lateral_max * dt
    if lateral.length() <= cap:
        return new_velocity
    return velocity + Vec2(along * ux, along * uy) + lateral * (cap / lateral.length())


def turn_rate_rad_s(agility: float) -> float:
    """Vitesse angulaire maximale du corps (rad/s) selon Agility (ticket 07f)."""
    return math.radians(_lerp(agility, _TURN_POINTS))


def direction_speed_factor(facing: Vec2, direction: Vec2) -> float:
    """Part de la vitesse max (0,65-1) selon l'angle entre le cap `facing` et la direction de course `direction`
    (ticket 07b) : de face, de côté (pas chassés) ou à reculons. Direction nulle : 1."""
    length = direction.length()
    if length < 1e-9:
        return 1.0
    cos = max(-1.0, min(1.0, (facing.x * direction.x + facing.y * direction.y) / (facing.length() * length)))
    return _lerp(math.degrees(math.acos(cos)), _DIRECTION_SPEED_POINTS)


def faces_run(was_facing_run: bool, speed: float, to_target: Vec2, look_at: Vec2 | None, position: Vec2,
              target_velocity: Vec2 = Vec2(0.0, 0.0), backpedal_speed: float = math.inf) -> bool:
    """Le joueur tourne-t-il le corps vers sa course plutôt que vers le ballon (tickets 07a et 07b) ? En course rapide
    (au-dessus de 19,8 km/h) ; sinon, ballon hors de sa course, et cible lointaine ou qui s'éloigne dans le sens de sa
    course plus vite que `backpedal_speed` (sa vitesse à reculons : à reculons, il la perdrait ; réserve A1 de l'expert
    au 07b, l'appel dans le dos du défenseur au marquage). Bandes d'hystérésis sur la vitesse, la distance et le cône du
    ballon, selon son choix du pas précédent `was_facing_run`."""
    band = FACING_RUN_BAND_MPS if was_facing_run else -FACING_RUN_BAND_MPS
    if speed >= FACING_RUN_SPEED_MPS - band:
        return True
    distance = to_target.length()
    if look_at is None or distance < 1e-9:
        return False
    to_ball = look_at - position
    if to_ball.length() < 1e-9:
        return False
    cos = (to_ball.x * to_target.x + to_ball.y * to_target.y) / (to_ball.length() * distance)
    free_cone = BALL_FREE_ANGLE_DEG - (BALL_CONE_BAND_DEG if was_facing_run else 0.0)
    if cos >= math.cos(math.radians(free_cone)):
        return False
    fleeing = (target_velocity.x * to_target.x + target_velocity.y * to_target.y) / distance
    if fleeing > backpedal_speed:
        return True
    return distance >= (BACK_TO_BALL_DISTANCE_M if was_facing_run else TURN_TO_RUN_DISTANCE_M)


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
    facing: Vec2 = Vec2(1.0, 0.0)  # cap du corps, vecteur unitaire (ticket v2-realisme/07a) ; borne la vitesse (07b)
    facing_run: bool = False  # corps tourné vers sa course plutôt que vers le ballon (07b, hystérésis du choix)


def turn_toward(facing: Vec2, desired: Vec2, max_angle_rad: float) -> Vec2:
    """Cap `facing` tourné vers la direction `desired` d'au plus `max_angle_rad`, par le plus court côté (ticket
    v2-realisme/07a). Direction nulle : le cap ne bouge pas."""
    if desired.length() < 1e-9:
        return facing
    current, wanted = math.atan2(facing.y, facing.x), math.atan2(desired.y, desired.x)
    delta = (wanted - current + math.pi) % (2.0 * math.pi) - math.pi
    angle = current + max(-max_angle_rad, min(max_angle_rad, delta))
    return Vec2(math.cos(angle), math.sin(angle))


def desired_facing(position: Vec2, velocity: Vec2, look_at: Vec2 | None, turning: bool = False,
                   facing_run: bool | None = None) -> Vec2:
    """Direction où le joueur veut tourner le corps (ticket 07a) : sens de course en course rapide, le ballon sinon ;
    sans ballon à regarder (`look_at` absent ou sur lui), le sens de course, ou aucune. `turning` : il se retourne vers
    son geste (ticket v2-realisme/07e, réserve A2 de l'expert), `look_at` prime même en course rapide. `facing_run` :
    choix déjà fait par `faces_run` (ticket 07b) ; absent, le seuil de course rapide seul."""
    run = velocity.length() >= FACING_RUN_SPEED_MPS if facing_run is None else facing_run
    if look_at is None or (run and not turning):
        return velocity
    to_ball = look_at - position
    return to_ball if to_ball.length() >= 1e-9 else velocity


def step(state: PlayerState, dt: float, target: Vec2, minute: float, speed_factor: float = 1.0,
         target_velocity: Vec2 = Vec2(0.0, 0.0), look_at: Vec2 | None = None, turning: bool = False) -> PlayerState:
    """Avance `state` de `dt` secondes, en dirigeant le joueur vers `target` (sa position de
    formation ou le ballon, voir `match.py`) -- vitesse plafonnée par Pace et la fatigue
    (Stamina), montée en vitesse exponentielle pilotée par Acceleration, freinage borné et loi
    d'arrivée (ticket v2-collectif/25). IA de déplacement volontairement
    simpliste (D-V08) : `target` est choisi par l'appelant, pas par ce module. `speed_factor` :
    part de la vitesse max (ex. conduite de balle, `decision.dribble_speed_factor`). `target_velocity` : vitesse
    de la cible quand elle bouge (le porteur qu'il presse) -- la loi d'arrivée porte alors sur la vitesse de
    rapprochement, sans quoi il resterait à sa distance de freinage derrière un porteur en conduite. `look_at` : le
    ballon, que son corps regarde hors course rapide (cap, ticket v2-realisme/07a). Vitesse max réduite de côté et à
    reculons selon l'angle entre le cap et la direction voulue (ticket v2-realisme/07b) ; il se retourne pour courir
    vers une cible lointaine (`faces_run`)."""
    # fatigue : réserve d'énergie (ticket 12e) ; `minute` n'est plus lue ici (gardée pour les appelants)
    effective_max_speed = max_speed_mps(state.pace) * energy_factor(state.condition.energy) * speed_factor
    agility = effective_rating(state, "Agility")  # freinage (12a), virage (12b) et rotation du corps (07f)
    decel = decel_max_mps2(agility)
    to_target = target - state.position
    distance = to_target.length()
    if distance > ARRIVAL_DEADZONE_M:
        # loi d'arrivée : jamais plus vite que la vitesse dont il peut freiner avant la cible, soit √(2·a·d). Forme
        # en pas discret : la vitesse v' de fin de pas telle qu'il puisse encore s'arrêter après avoir parcouru ce pas
        # ((v + v')/2·dt), pour ne pas dépasser quel que soit `dt`.
        relative = state.velocity - target_velocity
        closing = max(0.0, (relative.x * to_target.x + relative.y * to_target.y) / distance)
        half_step = 0.5 * decel * dt
        room = max(0.0, distance - 0.5 * closing * dt)
        stopping_speed = math.sqrt(half_step * half_step + 2.0 * decel * room) - half_step
        desired_velocity = target_velocity + to_target * (stopping_speed / distance)
        # de face, de côté ou à reculons (ticket 07b) : selon le cap du début du pas
        capped_speed = effective_max_speed * direction_speed_factor(state.facing, desired_velocity)
        if desired_velocity.length() > capped_speed:
            desired_velocity = desired_velocity.normalized() * capped_speed
    else:
        desired_velocity = Vec2(0.0, 0.0)

    # Montée en vitesse : forme exacte en pas discret (indépendante de `dt`). Si elle ferait ralentir (baisse
    # d'intensité, arrivée, changement de direction), le joueur freine à `decel` (Agility, 12a) vers la vitesse visée.
    velocity = state.velocity
    candidate = desired_velocity + (velocity - desired_velocity) * math.exp(-dt / accel_tau_s(state.acceleration))
    if candidate.length() >= velocity.length():
        new_velocity = candidate
    else:
        delta = desired_velocity - velocity
        brake = decel * dt
        new_velocity = desired_velocity if delta.length() <= brake else velocity + delta * (brake / delta.length())
    new_velocity = limit_turn(velocity, new_velocity, lateral_max_mps2(agility), dt)  # virage (12b)

    # vitesse moyenne du pas (trapèzes) : exacte pour un freinage constant, très proche pour l'exponentielle
    new_position = clamp_to_pitch(state.position + (velocity + new_velocity) * (0.5 * dt))
    facing_run = faces_run(state.facing_run, new_velocity.length(), target - new_position, look_at, new_position,
                           target_velocity, effective_max_speed * _DIRECTION_SPEED_POINTS[-1][1])
    run_direction = new_velocity if new_velocity.length() >= 0.5 or not facing_run else target - new_position
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
        facing=turn_toward(state.facing, desired_facing(new_position, run_direction, look_at, turning, facing_run),
                            turn_rate_rad_s(agility) * dt),
        facing_run=facing_run,
    )

"""Événements visuels du ballon (Phase 6, Bloc B4, 08/10/2026) : but, parade, poteau, barre, corner, sortie de but,
touche, dégagement -- produits par le MOTEUR (et non plus devinés par le navigateur) et ajoutés au payload d'un clip
sous `metadata.events_ball` (champ optionnel : `render/canvas.html` l'ignore, il garde sa propre détection du but).

**Principe : le score est décidé en amont, jamais ici.** Le moteur de Poisson décide but ou non-but ; la narration
(`narrative.py`) tire l'issue VISUELLE d'un non-but dans un menu (`arret`, `hors_cadre`, `tacle`, `degagement`,
`poteau`, `barre`), de façon déterministe, et le commentaire texte (NLG) s'appuie sur cette même issue. Ce module ne
choisit donc RIEN : il met en images l'issue reçue. Une parade est la représentation d'un `arret` ; un but n'est
jamais annulé par une parade ; une parade n'est jamais calculée à partir de la portée du gardien.

Issue -> événements :
    but         -> `but` (franchissement de la ligne entre les poteaux, sous la barre)
    arret       -> `parade` (le gardien repousse), puis `corner` / `touche` si le ballon sort ensuite
    poteau      -> `poteau`, puis `touche` / `sortie_but` si le ballon sort ensuite (rebond de B2)
    barre       -> `barre`, idem
    hors_cadre  -> `sortie_but` (le tireur est le dernier à avoir touché le ballon)
    tacle / degagement -> `degagement` (ballon renvoyé par un défenseur)
                        (coup franc direct, B7-c : le ballon part vers le mur, le heurte et repart vers le terrain ; l'événement
                        `degagement` est alors placé au point d'impact sur le mur, voir `_wall_block_trajectory`)

Règle corner / sortie de but (ligne de but franchie HORS des poteaux ou au-dessus de la barre) :
    dernier toucheur = défenseur (ou gardien) -> `corner` ; dernier toucheur = attaquant -> `sortie_but`.
Ligne de touche franchie -> `touche`. Entre les poteaux et sous la barre -> `but`.

Parade (constantes validées par l'architecte le 08/10/2026) : le gardien repousse le ballon en le réfléchissant sur
un plan vertical dont la normale est inclinée de `a = a_max · u` (`a_max` = 60°, `u` ∈ [-1, 1] = décalage latéral du
tir ramené à la demi-largeur de la cible `arret`) ; la vitesse de sortie vaut la vitesse d'arrivée × une restitution
tirée par hachage de `event_ref` dans [0,5 ; 0,7] (un tir à 30 m/s repart à 15-21 m/s) ; un aléa de ±10° sur
l'azimut, déterministe. Garde-fou : si la trajectoire de sortie franchit la ligne entre les poteaux (ce serait un
but), l'angle est ramené à 40° au plus, puis, en dernier recours, le ballon repart vers le terrain.
Coupe : un clip qui se prolonge (parade, rebond de montant) s'arrête 1,0 s après le franchissement d'une ligne.

Tout est déterministe : hachage sha256 de `event_ref`, jamais `random`/`np.random`."""

from __future__ import annotations

import math
from dataclasses import dataclass, replace

from ligue1sim.animation.ball import (
    BALL_FLIGHT,
    GRAVITY_M_S2,
    REBOUND_AZIMUTH_JITTER_DEG,
    ReboundTrajectory,
    _Arc,
    _arc_drag,
    _deterministic_unit,
    _enforce_backward,
    _simulate_rebound,
    ball_state_at,
    rebound_after_flight,
)
from ligue1sim.animation.sequence_generator import _WALL_DISTANCE_M, _WALL_SIZE_BY_MAX_DISTANCE_M, _WALL_SIZE_DEFAULT
from ligue1sim.animation.templates import strike_speed_for, strike_type_for
from ligue1sim.animation.types import BallState, Sequence
from ligue1sim.pitch_geometry import GOAL_HEIGHT_M, GOAL_WIDTH_M, PITCH_LENGTH_M, PITCH_WIDTH_M

# --- types d'événements -----------------------------------------------------
BUT = "but"
CORNER = "corner"
SORTIE_BUT = "sortie_but"
TOUCHE = "touche"
PARADE = "parade"
POTEAU = "poteau"
BARRE = "barre"
DEGAGEMENT = "degagement"
BALL_EVENT_TYPES = (BUT, CORNER, SORTIE_BUT, TOUCHE, PARADE, POTEAU, BARRE, DEGAGEMENT)

ATTAQUANT = "attaquant"
DEFENSEUR = "defenseur"

# --- constantes validées (architecte, 08/10/2026) ---------------------------
PARRY_MAX_ANGLE_DEG = 60.0  # a_max
PARRY_SAFE_ANGLE_DEG = 40.0  # garde-fou : jamais un but sur une parade
PARRY_RESTITUTION_RANGE = (0.5, 0.7)
PARRY_AZIMUTH_JITTER_DEG = REBOUND_AZIMUTH_JITTER_DEG  # +-10° (D8)
LINE_CUT_S = 1.0  # le clip s'arrête 1,0 s après le franchissement d'une ligne

# Mur d'un coup franc direct (Phase 6, B7-c, 14/10/2026) -- constantes validées par le propriétaire. Un coup franc d'issue `tacle` /
# `degagement` (seules issues que le mur peut contrarier : toutes les autres sont décidées en amont et franchissent le mur, voir
# `ball._free_kick_hump_m`) : le ballon part vers le mur, le heurte et repart vers le terrain.
_WALL_THICKNESS_M = 0.5  # épaisseur de détection : la face côté tireur est à `_WALL_DISTANCE_M` - 0,25 m
_WALL_HALF_WIDTH_PER_PLAYER_M = 0.75  # largeur de collision par joueur (1,5 m, l'écartement du mur) : le mur est fermé
_WALL_BLOCK_Z_MAX_M = 1.8 + 0.2  # mur 1,80 m + marge : un ballon plus bas est bloqué
_WALL_AIM_Z_MARGIN_M = 0.3  # le point d'impact est tiré dans [0,3 ; `_WALL_BLOCK_Z_MAX_M` - 0,3] m
_WALL_DRIFT_MARGIN_M = 0.5  # dérive latérale partagée du mur (<= 0,5 m, B7-b) : le point visé reste dans l'emprise réelle
_WALL_RESTITUTION_RANGE = (0.30, 0.50)
_WALL_MAX_DEFLECTION_DEG = 45.0

# Décalage latéral de référence de la parade : demi-largeur de la cible `arret` (`templates._flight_target` : y dans
# [0,47 ; 0,53]) ; un tir au bord de cette zone donne l'angle maximal.
_PARRY_OFFSET_REF = 0.03
_HALF_GOAL_NORM = (GOAL_WIDTH_M / 2.0) / PITCH_WIDTH_M
# Les points de contact des cibles (poteau, barre) peuvent dépasser la ligne de but de 0,5 % : tolérance avant de
# considérer que le ballon est sorti.
_LINE_TOLERANCE = 0.006
_CROSSING_STEP_S = 1.0 / 60.0


@dataclass(frozen=True)
class BallEvent:
    """Événement visuel du ballon. `t` : instant dans le clip (s) ; `t_minute` : minute du match ; `x`, `y` : position
    normalisée ; `direction_deg` : cap de sortie du ballon (0° = vers le but attaqué, +x ; 90° = vers +y), `None` si
    sans objet ; `joueur` : nom du joueur concerné (gardien pour une parade, tireur pour un poteau), `None` si inconnu."""

    type: str
    t_minute: int
    t: float
    x: float
    y: float
    joueur: str | None
    direction_deg: float | None
    last_toucher: str
    event_ref: str

    def to_dict(self) -> dict:
        return {
            "type": self.type, "t_minute": self.t_minute, "t": round(self.t, 3), "x": round(self.x, 4),
            "y": round(self.y, 4), "joueur": self.joueur,
            "direction_deg": None if self.direction_deg is None else round(self.direction_deg, 1),
            "last_toucher": self.last_toucher, "event_ref": self.event_ref,
        }


@dataclass(frozen=True)
class BallPlan:
    """Ce qu'un clip doit ajouter : les événements et, pour un ballon qui repart (parade, rebond de montant), sa
    trajectoire et la durée retenue (`end_tau` s après le contact, coupe à 1,0 s après un franchissement de ligne)."""

    events: tuple[BallEvent, ...]
    trajectory: ReboundTrajectory | None = None
    end_tau: float = 0.0


@dataclass(frozen=True)
class LineCrossing:
    tau: float
    kind: str  # "goal_line" | "touch_line"
    x: float
    y: float
    z: float


def classify_line_exit(kind: str, y: float, z: float, last_toucher: str) -> str:
    """Événement produit par un ballon qui franchit une ligne. `kind` : "goal_line" ou "touch_line" ; `y`, `z` :
    position du franchissement (y normalisé, z en mètres)."""
    if kind == "touch_line":
        return TOUCHE
    if abs(y - 0.5) <= _HALF_GOAL_NORM and z <= GOAL_HEIGHT_M:
        return BUT
    return CORNER if last_toucher == DEFENSEUR else SORTIE_BUT


def _outside(state: BallState) -> bool:
    return state.x > 1.0 + _LINE_TOLERANCE or state.x < 0.0 or state.y < 0.0 or state.y > 1.0


def first_line_crossing(trajectory: ReboundTrajectory, step: float = _CROSSING_STEP_S) -> LineCrossing | None:
    """Premier franchissement d'une ligne par la trajectoire (le ballon est en jeu au contact)."""
    previous = trajectory.state_at(0.0)
    tau = 0.0
    while tau < trajectory.duration - 1e-12:
        tau = min(tau + step, trajectory.duration)
        current = trajectory.state_at(tau)
        if _outside(current):
            # Interpolation linéaire entre les deux échantillons, sur l'axe franchi.
            kind = "goal_line" if (current.x > 1.0 + _LINE_TOLERANCE or current.x < 0.0) else "touch_line"
            if kind == "goal_line":
                line_x = 1.0 if current.x > 1.0 else 0.0
                span = current.x - previous.x
                f = 0.0 if span == 0.0 else min(max((line_x - previous.x) / span, 0.0), 1.0)
            else:
                line_y = 1.0 if current.y > 1.0 else 0.0
                span = current.y - previous.y
                f = 0.0 if span == 0.0 else min(max((line_y - previous.y) / span, 0.0), 1.0)
            return LineCrossing(
                tau=tau - step * (1.0 - f), kind=kind,
                x=previous.x + (current.x - previous.x) * f, y=previous.y + (current.y - previous.y) * f,
                z=previous.z + (current.z - previous.z) * f,
            )
        previous = current
    return None


def _azimuth_deg(vx_m: float, vy_m: float) -> float:
    return math.degrees(math.atan2(vy_m, vx_m))


def _rotate(vx: float, vy: float, angle_rad: float) -> tuple[float, float]:
    c, s = math.cos(angle_rad), math.sin(angle_rad)
    return vx * c - vy * s, vx * s + vy * c


def _parry_exit_velocity(
    contact: BallState, seed_key: str, max_angle_deg: float, *, jitter: bool = True
) -> tuple[float, float, float]:
    vx, vy, vz = contact.vx * PITCH_LENGTH_M, contact.vy * PITCH_WIDTH_M, contact.vz
    offset = max(-1.0, min(1.0, (contact.y - 0.5) / _PARRY_OFFSET_REF))
    phi = math.radians(max_angle_deg) * offset
    nx, ny = -math.cos(phi), math.sin(phi)  # normale horizontale : vers le terrain, du côté du tir
    vn = vx * nx + vy * ny
    mirror_x, mirror_y = vx - 2.0 * vn * nx, vy - 2.0 * vn * ny  # réflexion sur le plan vertical de la parade
    low, high = PARRY_RESTITUTION_RANGE
    restitution = low + (high - low) * _deterministic_unit(seed_key, "parade_restitution")
    out_x, out_y, out_z = mirror_x * restitution, mirror_y * restitution, vz * restitution
    if jitter:
        unit = _deterministic_unit(seed_key, "parade_azimuth")
        out_x, out_y = _rotate(out_x, out_y, math.radians(PARRY_AZIMUTH_JITTER_DEG) * (2.0 * unit - 1.0))
    return out_x, out_y, out_z


def _trajectory_from(
    surface: str, contact: BallState, exit_velocity: tuple[float, float, float]
) -> ReboundTrajectory:
    p0 = (contact.x * PITCH_LENGTH_M, contact.y * PITCH_WIDTH_M, contact.z)
    arcs, ground_contacts, apexes = _simulate_rebound(p0, exit_velocity)
    duration = arcs[-1].t0 + arcs[-1].duration
    trajectory = ReboundTrajectory(
        surface=surface, contact=(contact.x, contact.y, contact.z), exit_velocity=exit_velocity, arcs=arcs,
        duration=duration, ground_bounces=ground_contacts, apexes_m=apexes,
        first_bounce_apex_m=apexes[0] if apexes else 0.0, rest=(0.0, 0.0, 0.0),
    )
    end = trajectory.state_at(duration)
    return replace(trajectory, rest=(end.x, end.y, end.z))


def _scores_a_goal(trajectory: ReboundTrajectory) -> bool:
    crossing = first_line_crossing(trajectory)
    return (
        crossing is not None and crossing.kind == "goal_line"
        and classify_line_exit("goal_line", crossing.y, crossing.z, DEFENSEUR) == BUT
    )


def parry_trajectory(contact: BallState, seed_key: str, *, jitter: bool = True) -> ReboundTrajectory:
    """Trajectoire du ballon repoussé par le gardien (voir la docstring de module). Garde-fou : jamais un but."""
    for max_angle in (PARRY_MAX_ANGLE_DEG, PARRY_SAFE_ANGLE_DEG):
        trajectory = _trajectory_from("keeper", contact, _parry_exit_velocity(contact, seed_key, max_angle, jitter=jitter))
        if not _scores_a_goal(trajectory):
            return trajectory
    # Dernier recours : le ballon repart vers le terrain, à la vitesse de la parade.
    vx, vy, vz = _parry_exit_velocity(contact, seed_key, PARRY_SAFE_ANGLE_DEG, jitter=False)
    return _trajectory_from("keeper", contact, (-abs(vx) - 1.0, vy, vz))


def _goal_crossing_time(sequence: Sequence) -> tuple[float, float, float]:
    """(t, y, z) du franchissement de la ligne de but par le vol d'un tir ; repli sur la fin du vol."""
    start = sequence.keyframes[-2].t
    end = sequence.duration
    steps = max(1, int((end - start) / (1.0 / 120.0)))
    for k in range(steps + 1):
        t = start + (end - start) * k / steps
        state = ball_state_at(sequence, t)
        if state.x >= 1.0:
            return t, state.y, state.z
    final = ball_state_at(sequence, end)
    return end, final.y, final.z


def _wall_block_trajectory(sequence: Sequence) -> ReboundTrajectory:
    """Trajectoire d'un coup franc bloqué par le mur (B7-c) : vol balistique (gravité, friction de l'air) du ballon posé jusqu'à
    la face du mur, à un point tiré dans l'emprise du mur (n x 1,5 m, moins la dérive) et à moins de `_WALL_BLOCK_Z_MAX_M`, puis
    réflexion sur le plan vertical du mur (normale tournée de +-45 degrés au plus, restitution 0,30 à 0,50, tirés par hachage de
    `event_ref`), puis rebonds au sol. Le ballon repart toujours vers le terrain (`_enforce_backward`, 1 m/s au moins). Le temps
    `tau` de la trajectoire part de la frappe (fin de `sequence`) : `contact` est le point d'impact sur le mur."""
    seed_key = sequence.event_ref
    spot = ball_state_at(sequence, sequence.duration)
    ball_x, ball_y = spot.x * PITCH_LENGTH_M, spot.y * PITCH_WIDTH_M
    goal_x, goal_y = PITCH_LENGTH_M - ball_x, PITCH_WIDTH_M / 2.0 - ball_y
    goal_m = math.hypot(goal_x, goal_y)
    ux, uy = goal_x / goal_m, goal_y / goal_m
    size = next((n for limit_m, n in _WALL_SIZE_BY_MAX_DISTANCE_M if goal_m <= limit_m), _WALL_SIZE_DEFAULT)

    # Point d'impact : sur la face du mur, décalé latéralement dans l'emprise, à une hauteur sous le haut du mur.
    face_m = _WALL_DISTANCE_M - _WALL_THICKNESS_M / 2.0
    reach_m = size * _WALL_HALF_WIDTH_PER_PLAYER_M - _WALL_DRIFT_MARGIN_M
    lateral_m = (2.0 * _deterministic_unit(seed_key, "wall_aim_y") - 1.0) * reach_m
    z_low, z_high = _WALL_AIM_Z_MARGIN_M, _WALL_BLOCK_Z_MAX_M - _WALL_AIM_Z_MARGIN_M
    aim_z = z_low + (z_high - z_low) * _deterministic_unit(seed_key, "wall_aim_z")
    aim_x = ball_x + face_m * ux - lateral_m * uy
    aim_y = ball_y + face_m * uy + lateral_m * ux
    reach_distance_m = math.hypot(aim_x - ball_x, aim_y - ball_y)

    # Vol jusqu'au mur : vitesse de la frappe de ce coup franc, composante verticale résolue pour arriver à `aim_z`.
    speed = strike_speed_for(strike_type_for("coup_franc", seed_key), seed_key)
    drag = _arc_drag(speed)
    reach_t = math.expm1(drag * reach_distance_m) / (drag * speed) if drag > 0.0 else reach_distance_m / speed
    launch_vz = (aim_z + 0.5 * GRAVITY_M_S2 * reach_t * reach_t) / reach_t
    leg_to_wall = _Arc(
        0.0, reach_t, (ball_x, ball_y, 0.0),
        (speed * (aim_x - ball_x) / reach_distance_m, speed * (aim_y - ball_y) / reach_distance_m, launch_vz), "flight", drag,
    )
    (hit_x, hit_y, hit_z), (vx, vy, vz) = leg_to_wall.at(reach_t)

    # Réflexion sur le plan vertical du mur.
    phi = math.radians(_WALL_MAX_DEFLECTION_DEG) * (2.0 * _deterministic_unit(seed_key, "wall_angle") - 1.0)
    nx, ny = _rotate(-ux, -uy, phi)  # normale horizontale : vers le terrain, tournée de phi
    vn = vx * nx + vy * ny
    low, high = _WALL_RESTITUTION_RANGE
    restitution = low + (high - low) * _deterministic_unit(seed_key, "wall_restitution")
    out_x, out_y = _enforce_backward(*((vx - 2.0 * vn * nx) * restitution, (vy - 2.0 * vn * ny) * restitution))
    exit_velocity = (out_x, out_y, vz * restitution)

    rebound_arcs, ground_contacts, apexes = _simulate_rebound((hit_x, hit_y, hit_z), exit_velocity)
    arcs = (leg_to_wall,) + tuple(replace(arc, t0=arc.t0 + reach_t) for arc in rebound_arcs)
    trajectory = ReboundTrajectory(
        surface="wall", contact=(hit_x / PITCH_LENGTH_M, hit_y / PITCH_WIDTH_M, hit_z), exit_velocity=exit_velocity, arcs=arcs,
        duration=arcs[-1].t0 + arcs[-1].duration, ground_bounces=ground_contacts, apexes_m=apexes,
        first_bounce_apex_m=apexes[0] if apexes else 0.0, rest=(0.0, 0.0, 0.0),
    )
    end = trajectory.state_at(trajectory.duration)
    return replace(trajectory, rest=(end.x, end.y, end.z))


def plan_ball_events(
    sequence: Sequence,
    outcome: str | None,
    minute: int,
    shooter: str | None,
    keeper: str | None,
) -> BallPlan:
    """Événements visuels et trajectoire de ballon d'un clip, pour l'issue DÉJÀ décidée `outcome`. Ne choisit pas
    l'issue et ne lit aucun score."""
    event_ref = sequence.event_ref
    end_t = sequence.duration
    has_flight = len(sequence.keyframes) >= 2 and sequence.keyframes[-2].physics_tag == BALL_FLIGHT

    def event(kind, t, x, y, joueur, direction, toucher):
        return BallEvent(kind, minute, t, x, y, joueur, direction, toucher, event_ref)

    if outcome == "but" and has_flight:
        t, y, z = _goal_crossing_time(sequence)
        return BallPlan((event(BUT, t, 1.0, y, shooter, 0.0, ATTAQUANT),))

    if outcome == "hors_cadre" and has_flight:
        contact = ball_state_at(sequence, end_t)
        return BallPlan((event(SORTIE_BUT, end_t, min(contact.x, 1.0), contact.y, shooter, 0.0, ATTAQUANT),))

    wall_block = outcome in ("tacle", "degagement") and sequence.meta.get("template") == "coup_franc"  # B7-c : le mur bloque
    if outcome in ("tacle", "degagement") and not wall_block:
        contact = ball_state_at(sequence, end_t)
        return BallPlan((event(DEGAGEMENT, end_t, contact.x, contact.y, None, None, DEFENSEUR),))

    if wall_block:
        trajectory = _wall_block_trajectory(sequence)
        vx, vy, _ = trajectory.exit_velocity
        hit_x, hit_y, _ = trajectory.contact
        first = event(DEGAGEMENT, end_t + trajectory.arcs[0].duration, hit_x, hit_y, None, _azimuth_deg(vx, vy), DEFENSEUR)
        toucher = DEFENSEUR
    elif outcome == "arret" and has_flight:
        contact = ball_state_at(sequence, end_t)
        trajectory = parry_trajectory(contact, f"{event_ref}|parade")
        vx, vy, _ = trajectory.exit_velocity
        first = event(PARADE, end_t, contact.x, contact.y, keeper, _azimuth_deg(vx, vy), DEFENSEUR)
        toucher = DEFENSEUR
    elif outcome in ("poteau", "barre") and has_flight:
        trajectory = rebound_after_flight(sequence, outcome)
        vx, vy, _ = trajectory.exit_velocity
        contact = ball_state_at(sequence, end_t)
        first = event(POTEAU if outcome == "poteau" else BARRE, end_t, contact.x, contact.y, shooter,
                      _azimuth_deg(vx, vy), ATTAQUANT)
        toucher = ATTAQUANT
    else:
        return BallPlan(())

    events = [first]
    crossing = first_line_crossing(trajectory)
    end_tau = trajectory.duration
    if crossing is not None:
        kind = classify_line_exit(crossing.kind, crossing.y, crossing.z, toucher)
        events.append(event(kind, end_t + crossing.tau, min(max(crossing.x, 0.0), 1.0), min(max(crossing.y, 0.0), 1.0),
                            None, None, toucher))
        end_tau = min(trajectory.duration, crossing.tau + LINE_CUT_S)
    return BallPlan(tuple(events), trajectory, end_tau)

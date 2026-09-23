"""Phase 3.2 : trajectoire continue du ballon entre les keyframes discrets
d'une `Sequence` (voir `animation.types`) -- `ball_state_at(sequence, t) ->
BallState` donne la position/vitesse/spin du ballon à un instant `t`
QUELCONQUE, sur le même principe que `motion.interpolate` pour les joueurs.

Consommateur PUR de `Sequence` : ne modifie ni `templates.py`, ni
`sequence_generator.py`, ni `types.py`. Point d'intégration UNIQUE :
`motion.interpolate` appelle `ball_state_at` pour peupler `FrameState.ball`
(auparavant toujours `None`, voir motion.py).

**Tag-driven, avec repli par inférence** (brief du 23/09/2026, "tag-driven
trajectory with fallback inference") : le comportement d'un segment (entre
`Keyframe[i]` et `Keyframe[i+1]`) est déterminé par `Keyframe[i].physics_tag`
s'il est renseigné, sinon INFÉRÉ (voir `_resolve_physics_tag`) :
    - porteur (`ball.owner_id`) absent au départ du segment -> `"deflect"`
      (ballon disputé/en l'air, pas de porteur clair).
    - dernier segment de la séquence (celui qui arrive au tir/à la
      conclusion) -> `"shot"`.
    - sinon -> `"pass_ground"`.
Cinq comportements disponibles : `pass_ground`, `pass_lob`, `shot`, `cross`,
`deflect` -- voir chaque fonction `_behavior_*` pour le détail. `pass_ground`,
`shot` (sur tous les gabarits), `deflect` (sur `recuperation_haute` et
`corner`) et `cross` (sur `corner`) sont aujourd'hui déclenchés par les 12
gabarits réels (voir leurs `physics_tags` dans `templates.py`) -- l'ambiguïté
cross/deflect du segment 0.3->0.6 de `corner` a été tranchée avec Olivier
(brief "corner tags decision", 23/09/2026) : `cross` pour le centre en vol
(0.3->0.6), `deflect` pour le ballon disputé au contact (0.6->1.0). Seul
`pass_lob` existe et est testé unitairement sans être pour l'instant
déclenché par aucun gabarit.

**`ball_height`/`Keyframe.ball.z` (l'ancien champ, rempli par
`templates.py`) est IGNORÉ ici** (arbitrage du 23/09/2026) : ses valeurs
(0.3, 0.6, 0.8...) n'ont jamais été calibrées en mètres nulle part dans le
code. `ball_state_at` calcule sa propre hauteur, en mètres, directement
depuis les formules ci-dessous -- jamais depuis `ball_height`.

Toute amplitude "aléatoire" (courbure d'un tir, contrôle latéral d'un
centre, perturbation d'une déviation) est déterministe -- hash sha256 du
`(event_ref, t de la keyframe de départ)`, même principe que
`motion._start_offset`/`sequence_generator._deterministic_unit` -- jamais
`random`/`np.random`, pour un déterminisme bit à bit garanti.

**Continuité** : garantie DANS un segment (même comportement du début à la
fin, échantillonné à dt=1/60 -- voir tests/test_ball.py). PAS garantie
D'UN SEGMENT À L'AUTRE quand le comportement change (ex. `pass_ground` qui
enchaîne sur `shot`) : chaque comportement est un modèle physique
différent avec son propre profil de vitesse local, les recoller en une
seule spline globalement C1 serait un chantier séparé, hors scope de ce
brief -- documenté ici plutôt que silencieusement supposé résolu.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import replace

from ligue1sim.animation.types import BallState, Keyframe, Sequence
from ligue1sim.pitch_geometry import PITCH_LENGTH_M, PITCH_WIDTH_M

PASS_GROUND = "pass_ground"
PASS_LOB = "pass_lob"
SHOT = "shot"
CROSS = "cross"
DEFLECT = "deflect"
_KNOWN_TAGS = frozenset({PASS_GROUND, PASS_LOB, SHOT, CROSS, DEFLECT})

_VELOCITY_EPSILON_S = 1e-4  # même principe que motion._VELOCITY_EPSILON_S -- différence finie pour (vx, vy, vz)
_STATIONARY_EPSILON_M = 0.01  # ballon "immobile" (cas limite) : moins d'1 cm entre kf_a et kf_b


def _deterministic_unit(key: str, salt: str) -> float:
    """Fraction déterministe dans [0, 1) -- même principe que
    `motion._start_offset`/`sequence_generator._deterministic_unit` (hash
    sha256, jamais `hash()` ni `random`)."""
    digest = hashlib.sha256(f"{salt}|{key}".encode()).digest()
    return int.from_bytes(digest[:8], "big") / 2**64


def _real_distance_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    dx_m = (b[0] - a[0]) * PITCH_LENGTH_M
    dy_m = (b[1] - a[1]) * PITCH_WIDTH_M
    return math.hypot(dx_m, dy_m)


def _perp_unit(a: tuple[float, float], b: tuple[float, float]) -> tuple[float, float]:
    """Vecteur unitaire perpendiculaire à `a -> b`, dans le référentiel
    NORMALISÉ (x, y) -- utilisé pour décaler latéralement une trajectoire
    (courbure d'un tir, perturbation d'une déviation). `(0.0, 0.0)` si
    `a == b` (aucune direction définie, jamais utilisé dans ce cas -- voir
    le cas limite "ballon immobile")."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    norm = math.hypot(dx, dy)
    if norm < 1e-12:
        return (0.0, 0.0)
    return (-dy / norm, dx / norm)


def _hat(s: float) -> float:
    """Parabole "chapeau" : 0 en s=0, pic (1.0) en s=0.5, 0 en s=1 -- forme
    partagée par la hauteur d'un lob/centre et la courbure latérale d'un
    tir/d'une déviation (voir chaque comportement). `s` clampé à [0, 1]."""
    s = min(1.0, max(0.0, s))
    return 4.0 * s * (1.0 - s)


def _hat_derivative(s: float) -> float:
    """Dérivée de `_hat` par rapport à `s` (pas au temps) -- utile pour des
    vitesses analytiques exactes plutôt qu'une différence finie."""
    return 4.0 - 8.0 * s


# --- pass_ground -----------------------------------------------------------
# Quasi linéaire, freinage léger : la vitesse finale est `_BRAKE_RATIO` fois
# la vitesse initiale (5% de moins, valeur donnée par Olivier). Modèle
# fermé : progress(s) = (1+k)s - k*s^2 avec k choisi pour que
# progress'(1)/progress'(0) = _BRAKE_RATIO -- garantit progress(0)=0,
# progress(1)=1 (arrivée exacte) quel que soit k.
_BRAKE_RATIO = 0.95  # vitesse finale / vitesse initiale (freinage de 5%)
_BRAKE_K = (1.0 - _BRAKE_RATIO) / (1.0 + _BRAKE_RATIO)


def _pass_ground_progress(s: float) -> float:
    return (1.0 + _BRAKE_K) * s - _BRAKE_K * s * s


def _pass_ground_progress_derivative(s: float) -> float:
    return (1.0 + _BRAKE_K) - 2.0 * _BRAKE_K * s


def _behavior_pass_ground(start: tuple[float, float], end: tuple[float, float], s: float, duration: float) -> BallState:
    progress = _pass_ground_progress(s)
    x = start[0] + (end[0] - start[0]) * progress
    y = start[1] + (end[1] - start[1]) * progress
    dprogress_ds = _pass_ground_progress_derivative(s)
    vx = (end[0] - start[0]) * dprogress_ds / duration
    vy = (end[1] - start[1]) * dprogress_ds / duration
    return BallState(x=x, y=y, z=0.0, spin=0.0, owner_id=None, vx=vx, vy=vy, vz=0.0)


# --- pass_lob ----------------------------------------------------------------
# Trajectoire au sol EN LIGNE DROITE (pas de courbure latérale -- rien dans
# le brief n'en demande pour un lob, contrairement à shot/cross), hauteur en
# parabole (_hat), pic à mi-parcours, retombée exacte à s=1. Hauteur max
# interpolée linéairement entre les deux points donnés par Olivier (25 cm à
# 10 m, 1,2 m à 30 m), distance clampée à [10, 30] m au-delà de cette
# fourchette (pas d'extrapolation absurde sur un lob très court/long).
_LOB_HEIGHT_NEAR_M = 0.25
_LOB_HEIGHT_NEAR_DIST_M = 10.0
_LOB_HEIGHT_FAR_M = 1.2
_LOB_HEIGHT_FAR_DIST_M = 30.0


def _lob_height_max_m(distance_m: float) -> float:
    clamped = min(_LOB_HEIGHT_FAR_DIST_M, max(_LOB_HEIGHT_NEAR_DIST_M, distance_m))
    span = _LOB_HEIGHT_FAR_DIST_M - _LOB_HEIGHT_NEAR_DIST_M
    frac = (clamped - _LOB_HEIGHT_NEAR_DIST_M) / span
    return _LOB_HEIGHT_NEAR_M + (_LOB_HEIGHT_FAR_M - _LOB_HEIGHT_NEAR_M) * frac


def _behavior_pass_lob(start: tuple[float, float], end: tuple[float, float], s: float, duration: float) -> BallState:
    distance_m = _real_distance_m(start, end)
    height_max = _lob_height_max_m(distance_m)
    x = start[0] + (end[0] - start[0]) * s
    y = start[1] + (end[1] - start[1]) * s
    z = height_max * _hat(s)
    vx = (end[0] - start[0]) / duration
    vy = (end[1] - start[1]) / duration
    vz = height_max * _hat_derivative(s) / duration
    return BallState(x=x, y=y, z=z, spin=0.0, owner_id=None, vx=vx, vy=vy, vz=vz)


# --- shot ----------------------------------------------------------------
# Ligne droite + courbure latérale (offset perpendiculaire en _hat, pic à
# ~15% de la distance totale, retombe à 0 à l'arrivée -- garantit l'arrivée
# exacte quelle que soit la courbure). z=0 si distance <= 16 m (tir du sol),
# sinon une trajectoire modeste (0 m à 16 m -> 0.8 m à 40 m+, clampé) --
# valeurs non fournies par le brief, extrapolation raisonnable documentée
# comme telle. < 11 m : tir tendu, AUCUNE courbure (offset forcé à 0).
_SHOT_CURVE_RATIO = 0.15  # pic de courbure = 15% de la distance totale
_SHOT_STRAIGHT_MAX_DIST_M = 11.0  # en dessous : tir tendu, pas de courbure
_SHOT_AIRBORNE_MIN_DIST_M = 16.0  # en dessous : au ras du sol
_SHOT_HEIGHT_FAR_M = 0.8
_SHOT_HEIGHT_FAR_DIST_M = 40.0


def _shot_height_max_m(distance_m: float) -> float:
    if distance_m <= _SHOT_AIRBORNE_MIN_DIST_M:
        return 0.0
    span = _SHOT_HEIGHT_FAR_DIST_M - _SHOT_AIRBORNE_MIN_DIST_M
    frac = min(1.0, (distance_m - _SHOT_AIRBORNE_MIN_DIST_M) / span)
    return _SHOT_HEIGHT_FAR_M * frac


def _behavior_shot(
    start: tuple[float, float], end: tuple[float, float], s: float, duration: float, seed_key: str
) -> BallState:
    distance_m = _real_distance_m(start, end)
    px, py = _perp_unit(start, end)
    curve_sign = 1.0 if _deterministic_unit(seed_key, "shot_curve_side") < 0.5 else -1.0
    curve_peak_m = 0.0 if distance_m < _SHOT_STRAIGHT_MAX_DIST_M else _SHOT_CURVE_RATIO * distance_m
    offset_m = curve_sign * curve_peak_m * _hat(s)
    offset_x = (offset_m / PITCH_LENGTH_M) * px
    offset_y = (offset_m / PITCH_WIDTH_M) * py

    base_x = start[0] + (end[0] - start[0]) * s
    base_y = start[1] + (end[1] - start[1]) * s
    x = base_x + offset_x
    y = base_y + offset_y

    height_max = _shot_height_max_m(distance_m)
    z = height_max * _hat(s)

    vx = (end[0] - start[0]) / duration + (curve_sign * curve_peak_m / PITCH_LENGTH_M) * px * _hat_derivative(s) / duration
    vy = (end[1] - start[1]) / duration + (curve_sign * curve_peak_m / PITCH_WIDTH_M) * py * _hat_derivative(s) / duration
    vz = height_max * _hat_derivative(s) / duration
    return BallState(x=x, y=y, z=z, spin=0.0, owner_id=None, vx=vx, vy=vy, vz=vz)


# --- cross -------------------------------------------------------------------
# Parabole haute (2-2.5 m, valeur seedée dans la fourchette -- pas de
# distance fournie pour ce comportement contrairement au lob), trajectoire
# latérale en VRAIE courbe de Bézier quadratique (pas juste un offset comme
# shot) : point de contrôle décalé perpendiculairement au milieu de la
# corde. Une Bézier quadratique arrive TOUJOURS exactement à son point
# final (P(1)=P2=end par construction), donc "point de chute précis" est
# garanti par la géométrie, pas ajusté a posteriori.
_CROSS_HEIGHT_MIN_M = 2.0
_CROSS_HEIGHT_MAX_M = 2.5
_CROSS_LATERAL_RATIO = 0.12  # décalage du point de contrôle, fraction de la distance totale


def _behavior_cross(
    start: tuple[float, float], end: tuple[float, float], s: float, duration: float, seed_key: str
) -> BallState:
    distance_m = _real_distance_m(start, end)
    px, py = _perp_unit(start, end)
    lateral_sign = 1.0 if _deterministic_unit(seed_key, "cross_side") < 0.5 else -1.0
    lateral_m = lateral_sign * _CROSS_LATERAL_RATIO * distance_m
    control_x = (start[0] + end[0]) / 2.0 + (lateral_m / PITCH_LENGTH_M) * px
    control_y = (start[1] + end[1]) / 2.0 + (lateral_m / PITCH_WIDTH_M) * py

    one_minus_s = 1.0 - s
    x = one_minus_s * one_minus_s * start[0] + 2 * one_minus_s * s * control_x + s * s * end[0]
    y = one_minus_s * one_minus_s * start[1] + 2 * one_minus_s * s * control_y + s * s * end[1]
    dx_ds = 2 * one_minus_s * (control_x - start[0]) + 2 * s * (end[0] - control_x)
    dy_ds = 2 * one_minus_s * (control_y - start[1]) + 2 * s * (end[1] - control_y)
    vx = dx_ds / duration
    vy = dy_ds / duration

    height_max = _CROSS_HEIGHT_MIN_M + (_CROSS_HEIGHT_MAX_M - _CROSS_HEIGHT_MIN_M) * _deterministic_unit(seed_key, "cross_height")
    z = height_max * _hat(s)
    vz = height_max * _hat_derivative(s) / duration
    return BallState(x=x, y=y, z=z, spin=0.0, owner_id=None, vx=vx, vy=vy, vz=vz)


# --- deflect -----------------------------------------------------------------
# Trajectoire de base quasi rectiligne (comme pass_ground, SANS freinage --
# un ballon disputé n'a pas de "porteur" qui décélère volontairement),
# perturbée UNIQUEMENT sur les 15% finaux du segment : une perturbation
# blanche (indépendante d'une frame à l'autre) donnerait un tremblement
# visuel incohérent -- ici une seule bosse LISSE, amplitude bornée à 8% de
# la distance totale, qui revient à 0 exactement à s=1 (arrivée garantie).
# Fenêtre en cosinus surélevé (0.5*(1-cos(2*pi*w))), PAS un simple sinus :
# un sinus a une dérivée non nulle à l'entrée de la fenêtre (s=0.85), donc
# un saut de VITESSE instantané à cet instant précis -- bug trouvé par
# tests/test_ball.py::TestContinuityAndArrivalPerBehavior (le saut de
# vitesse dépassait largement la tolérance de 5%). Le cosinus surélevé a une
# dérivée nulle aux DEUX bords de la fenêtre (s=0.85 ET s=1.0), donc une
# trajectoire C1-continue même à l'entrée de la perturbation.
#
# Frontière ENTRE deux segments (ex. le "cross" 0.3->0.6 qui enchaîne sur le
# "deflect" 0.6->1.0 de corner) : POSITION continue, VITESSE discontinue --
# ricochet visuel attendu, pas un bug. Vérifié numériquement (brief
# "ball_owner=None debt", Tâche 3, 23/09/2026,
# tests/test_ball.py::TestBallPositionContinuousAcrossDeflectBoundary) : à la
# jonction, x/y/z convergent vers LA MÊME valeur des deux côtés (à <1e-6
# près, la position du Keyframe partagé), mais vx/vy/vz sautent nettement
# (ex. vz : -4.6 m/s juste avant -> 0.0 m/s juste après sur corner) --
# cohérent avec la docstring de module ("PAS garantie D'UN SEGMENT À
# L'AUTRE quand le comportement change") : un ballon qui change de
# comportement physique (ici, un centre qui devient une déviation disputée)
# change légitimement de vitesse sans sauter dans l'espace. Le ratio de
# vitesse mesuré à 7.75 dans un retour précédent était un artefact de script
# (échantillonnage pile à la frontière, résolu vers le segment PRÉCÉDENT par
# `_find_ball_segment`, jamais une vraie mesure de `deflect`) -- pas cette
# discontinuité-ci.
_DEFLECT_WINDOW_START = 0.85
_DEFLECT_AMPLITUDE_RATIO = 0.08


def _deflect_bump(s: float) -> float:
    if s <= _DEFLECT_WINDOW_START:
        return 0.0
    window = min(1.0, (s - _DEFLECT_WINDOW_START) / (1.0 - _DEFLECT_WINDOW_START))
    return 0.5 * (1.0 - math.cos(2.0 * math.pi * window))


def _deflect_bump_derivative(s: float) -> float:
    if s <= _DEFLECT_WINDOW_START:
        return 0.0
    window_span = 1.0 - _DEFLECT_WINDOW_START
    window = (s - _DEFLECT_WINDOW_START) / window_span
    if window >= 1.0:
        return 0.0
    return (math.pi / window_span) * math.sin(2.0 * math.pi * window)


def _behavior_deflect(
    start: tuple[float, float], end: tuple[float, float], s: float, duration: float, seed_key: str
) -> BallState:
    distance_m = _real_distance_m(start, end)
    px, py = _perp_unit(start, end)
    perturb_sign = 1.0 if _deterministic_unit(seed_key, "deflect_side") < 0.5 else -1.0
    amplitude_m = perturb_sign * _DEFLECT_AMPLITUDE_RATIO * distance_m
    bump = _deflect_bump(s)
    bump_d = _deflect_bump_derivative(s)

    base_x = start[0] + (end[0] - start[0]) * s
    base_y = start[1] + (end[1] - start[1]) * s
    x = base_x + (amplitude_m / PITCH_LENGTH_M) * px * bump
    y = base_y + (amplitude_m / PITCH_WIDTH_M) * py * bump

    vx = (end[0] - start[0]) / duration + (amplitude_m / PITCH_LENGTH_M) * px * bump_d / duration
    vy = (end[1] - start[1]) / duration + (amplitude_m / PITCH_WIDTH_M) * py * bump_d / duration
    return BallState(x=x, y=y, z=0.0, spin=0.0, owner_id=None, vx=vx, vy=vy, vz=0.0)


# --- résolution du tag / dispatch -------------------------------------------


def _resolve_physics_tag(sequence: Sequence, kf_a: Keyframe, is_last_segment: bool) -> str:
    """Modification C du brief (23/09/2026) : `physics_tag` explicite s'il
    est renseigné sur `kf_a`, sinon inféré -- porteur absent -> `deflect`,
    dernier segment -> `shot`, sinon `pass_ground`."""
    if kf_a.physics_tag is not None:
        if kf_a.physics_tag not in _KNOWN_TAGS:
            raise ValueError(f"physics_tag inconnu : {kf_a.physics_tag!r} (t={kf_a.t}, {sequence.event_ref})")
        return kf_a.physics_tag
    if kf_a.ball.owner_id is None:
        return DEFLECT
    if is_last_segment:
        return SHOT
    return PASS_GROUND


def _find_ball_segment(sequence: Sequence, t: float) -> tuple[Keyframe, Keyframe, float, bool]:
    """Keyframes encadrant `t` (clampé aux bornes de la séquence, comportement
    2) et la progression `s` ∈ [0, 1] dans ce segment -- même principe que
    `motion._find_segment`, réimplémenté ici pour que `ball.py` reste
    indépendant de `motion.py` (aucun import croisé, seul `motion.interpolate`
    appelle `ball_state_at`, jamais l'inverse). `is_last_segment` : `True` si
    `kf_b` est le dernier keyframe de la séquence (comportement 4, `shot` par
    défaut)."""
    keyframes = sequence.keyframes
    last_idx = len(keyframes) - 1
    clamped_t = min(max(t, keyframes[0].t), keyframes[-1].t)

    if clamped_t <= keyframes[0].t:
        idx_a, idx_b = 0, min(1, last_idx)
    elif clamped_t >= keyframes[-1].t:
        idx_a, idx_b = max(0, last_idx - 1), last_idx
    else:
        idx_a, idx_b = 0, last_idx
        for i in range(last_idx):
            if keyframes[i].t <= clamped_t <= keyframes[i + 1].t:
                idx_a, idx_b = i, i + 1
                break

    kf_a, kf_b = keyframes[idx_a], keyframes[idx_b]
    duration = kf_b.t - kf_a.t
    s = 0.0 if duration <= 0 else min(1.0, max(0.0, (clamped_t - kf_a.t) / duration))
    return kf_a, kf_b, s, idx_b == last_idx


def ball_state_at(sequence: Sequence, t: float) -> BallState:
    """Position/vitesse/spin du ballon de `sequence` à l'instant `t`
    (clampé aux bornes de la séquence, JAMAIS d'extrapolation) -- voir la
    docstring de module pour le principe tag-driven + repli par inférence.

    Cas limite "ballon immobile" (`kf_a`/`kf_b` à moins d'1 cm l'un de
    l'autre, comportement 1) : renvoie une position figée, vitesse nulle,
    sans même consulter le `physics_tag` -- rien à faire "bouger"."""
    kf_a, kf_b, s, is_last_segment = _find_ball_segment(sequence, t)
    start = (kf_a.ball.x, kf_a.ball.y)
    end = (kf_b.ball.x, kf_b.ball.y)

    if _real_distance_m(start, end) < _STATIONARY_EPSILON_M:
        return BallState(x=start[0], y=start[1], z=0.0, spin=0.0, owner_id=kf_a.ball.owner_id, vx=0.0, vy=0.0, vz=0.0)

    duration = kf_b.t - kf_a.t
    if duration <= 0:
        return BallState(x=end[0], y=end[1], z=0.0, spin=0.0, owner_id=kf_b.ball.owner_id, vx=0.0, vy=0.0, vz=0.0)

    tag = _resolve_physics_tag(sequence, kf_a, is_last_segment)
    seed_key = f"{sequence.event_ref}|{kf_a.t}"

    if tag == PASS_GROUND:
        state = _behavior_pass_ground(start, end, s, duration)
    elif tag == PASS_LOB:
        state = _behavior_pass_lob(start, end, s, duration)
    elif tag == SHOT:
        state = _behavior_shot(start, end, s, duration, seed_key)
    elif tag == CROSS:
        state = _behavior_cross(start, end, s, duration, seed_key)
    else:
        state = _behavior_deflect(start, end, s, duration, seed_key)

    owner_id = kf_a.ball.owner_id if s < 1.0 else kf_b.ball.owner_id
    return replace(state, owner_id=owner_id)

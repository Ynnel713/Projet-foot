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

Toute amplitude "aléatoire" encore basée sur un hash (contrôle latéral d'un
centre, perturbation d'une déviation) est déterministe -- hash sha256 du
`(event_ref, t de la keyframe de départ)`, même principe que
`motion._start_offset`/`sequence_generator._deterministic_unit` -- jamais
`random`/`np.random`, pour un déterminisme bit à bit garanti. **Exception
depuis le 23/09/2026 (brief "real Magnus effect", Tâche 2)** : la courbure
d'un `shot` n'est plus un hash -- elle vient de `Keyframe.ball.spin`
(rad/s), via une vraie accélération de Magnus (`a = k · spin · v`, voir
`_behavior_shot`) -- déterministe aussi, mais pilotée par une donnée
physique du gabarit plutôt que par un id de séquence.

**Continuité** : garantie DANS un segment (même comportement du début à la
fin, échantillonné à dt=1/60 -- voir tests/test_ball.py). PAS garantie
D'UN SEGMENT À L'AUTRE quand le comportement change (ex. `pass_ground` qui
enchaîne sur `shot`) : chaque comportement est un modèle physique
différent avec son propre profil de vitesse local, les recoller en une
seule spline globalement C1 serait un chantier séparé, hors scope de ce
brief -- documenté ici plutôt que silencieusement supposé résolu.
"""

# CHANGEMENT -- 2026-09-23 -- hash sha256(event_ref) -> effet Magnus piloté
# par spin, dans `_behavior_shot` uniquement -- raison : audit de la Tâche 3
# du brief "canvas vertical slice" (2026-09-23) qui a établi que la
# "courbure" d'un tir était un pur artefact géométrique (offset perpendiculaire
# seedé par hash), sans aucun rapport avec `BallState.spin` (toujours 0.0,
# jamais lu) -- `decalage_enroulee` ne courbait donc jamais réellement selon
# son spin. Remplacé par une vraie accélération de Magnus (voir `_MAGNUS_K`
# et `_behavior_shot`) : spin=0 -> trajectoire droite, spin non nul -> courbe
# dans le sens du signe de `spin`. `cross` et `deflect` gardent leur hash
# (courbure/perturbation latérale sans notion de spin physique dans leur
# brief d'origine) -- non touchés ici (scope de la Tâche 2, pas un refacto
# global de ball.py).
#
# AUTRE DETTE REPÉRÉE (signalée, PAS corrigée -- hors scope de ce brief) :
# `cross`/`deflect` utilisent encore un hash sur `seed_key` pour leur
# amplitude/côté latéral, sans lien avec une donnée physique du gabarit
# (contrairement à `shot` désormais) -- même incohérence structurelle que
# celle trouvée pour `shot`, potentiellement à auditer plus tard.
#
# DETTE -- 2026-09-24 -- résidu Magnus sur les bords du segment `ball_flight`
# (brief "ball_flight duration uses 3D distance") : `decalage_enroulee` (seul
# gabarit avec `spin != 0`) peut dépasser 35 m/s en vitesse 3D INSTANTANÉE
# près des bords du segment (`s` proche de 0 ou 1), même quand la vitesse
# MOYENNE du vol est correcte (couverte par
# tests/test_ball.py::TestBallSpeedRealisticOnFlight, qui reste vert) --
# `_hat_derivative(s)` (courbure Magnus, voir `_behavior_shot`) culmine aux
# bords du segment (`_hat_derivative(0)=4`, `_hat_derivative(1)=-4`, nul au
# milieu), sa contribution de vitesse s'ADDITIONNE à la vitesse de base
# `_behavior_ball_flight` (jamais à `_behavior_shot` lui-même, non modifié).
# Mesuré sur 100 matchs simulés (1251 vols) : 35/1251 (2,8%), tous
# `decalage_enroulee`, max observé 35,51 m/s (35,0 visé) -- écart 1,5%,
# invisible à l'œil. Piste : amortir l'ajout de la composante Magnus en
# entrée/sortie du segment `ball_flight` plutôt qu'un `_hat_derivative` brut.
# Non corrigé ici (hors périmètre de la Tâche 1 du brief, "formule 2D->3D,
# rien d'autre") -- à traiter dans le chantier des déclinaisons multiples de
# `decalage_enroulee` prévu séparément (voir aussi
# docs/ball_flight_design.md, section "Dette connue").
#
# Précision (brief "structural test for 2D->3D flight duration", 24/09/2026) :
# la formule 2D->3D elle-même (`_flight_distance_m`, templates.py) est
# couverte par un test structurel dédié
# (tests/test_templates.py::TestBallFlightDurationUses3DDistance) --
# vérifiée rouge si la distance repasse en 2D, vérifiée verte avec la
# distance 3D en place. Ce test NE COUVRE PAS le résidu Magnus décrit
# ci-dessus (les deux causes sont distinctes : formule de durée vs
# contribution de vitesse de la courbure) -- le résidu Magnus reste sans
# test de non-régression, à traiter avec le chantier séparé.

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, replace

from ligue1sim.animation.types import BallState, Keyframe, Sequence
from ligue1sim.pitch_geometry import GOAL_WIDTH_M, PITCH_LENGTH_M, PITCH_WIDTH_M

PASS_GROUND = "pass_ground"
PASS_LOB = "pass_lob"
SHOT = "shot"
CROSS = "cross"
DEFLECT = "deflect"
# Brief "ball flight after shot" (24/09/2026), voir docs/ball_flight_design.md
# -- segment qui suit un `shot`/`deflect` de gabarit (templates.py) et
# atteint une cible (x, y, z) explicite dérivée de l'issue réelle de
# l'action, jamais dérivée d'un `Template.ball_position` statique. Distinct
# de `SHOT` (pas juste réutilisé avec le même tag) car son modèle de hauteur
# DIFFÈRE : `_behavior_shot` retombe toujours à z=0 en fin de segment
# (`_hat(1)=0`, voir plus bas) -- correct pour un tir qui arrive au pied du
# tireur (comportement historique, inchangé), mais faux pour un vol qui doit
# atteindre une hauteur cible arbitraire (ex. la barre, ~2,44m). Un tag
# dédié évite tout changement de comportement des segments `shot` EXISTANTS
# des 12 gabarits (voir `_behavior_ball_flight`, qui réutilise la
# composante x/y/Magnus de `_behavior_shot` SANS toucher à cette fonction).
BALL_FLIGHT = "ball_flight"
# Phase 6, Bloc B2 (08/10/2026) -- rebond après impact sur un montant (voir plus bas, "Rebonds") : segment qui
# démarre au point de contact (fin d'un `ball_flight`) et suit `ReboundTrajectory`.
BOUNCE = "bounce"
_KNOWN_TAGS = frozenset({PASS_GROUND, PASS_LOB, SHOT, CROSS, DEFLECT, BALL_FLIGHT, BOUNCE})

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


# --- Friction de l'air (Phase 6, Bloc B1, 08/10/2026) ------------------------------------------------
# Un ballon libre ralentit : `dv/dt = -c·v²` (friction proportionnelle au carré de la vitesse), donc `v(d) = v0·exp(-c·d)`
# à la distance `d` parcourue. Les trajectoires de ce module sont CINÉMATIQUES (position imposée aux keyframes, durée
# fixée par le gabarit) : la friction est donc un reparamétrage du temps le long de la trajectoire,
#     p(s) = ln(1 + (e^{cD} - 1)·s) / (cD),    p(0) = 0, p(1) = 1 (arrivée exacte), p'(s) = ((e^{cD}-1)/(cD)) / (1 + (e^{cD}-1)·s)
# qui donne un ballon plus rapide au départ qu'à l'arrivée (rapport v_fin / v_début = e^{-cD}) sans changer les positions
# imposées. La vitesse INITIALE d'un segment est celle de la frappe (v0 = v_moyenne · cD / (1 - e^{-cD})) : elle n'est pas
# réduite, seule la suite du vol ralentit.
# Coefficient : 5 % de perte de vitesse par seconde à 15 m/s (c·v = 0,05 -> c = 0,05 / 15 = 0,0033 /m, valeur de
# l'architecte) ; la perte relative est proportionnelle à la vitesse (~1 %/s à 3 m/s, ~11 %/s à 34 m/s), jamais nulle.
# Bornes : la décélération relative initiale ne dépasse pas `AIR_DRAG_MAX_RATE_PER_S`, et un segment cinématique ne
# perd jamais plus de la moitié de sa vitesse (`AIR_DRAG_MIN_SPEED_RATIO`).
# Les déplacements MESURÉS dans ce module (conduite `shot`, `pass_ground`, `cross`, `deflect`, `pass_lob`,
# `ball_flight`, rebonds) utilisent tous cette loi ; la hauteur `z` reste fonction du temps (la gravité n'est pas freinée).
AIR_DRAG_PER_M = 0.05 / 15.0
AIR_DRAG_MAX_RATE_PER_S = 0.30
AIR_DRAG_MIN_SPEED_RATIO = 0.50


def _segment_drag(distance_m: float) -> float:
    """Coefficient effectif (1/m) d'un segment cinématique de `distance_m` mètres : `AIR_DRAG_PER_M`, borné pour que
    v_fin / v_début >= `AIR_DRAG_MIN_SPEED_RATIO`."""
    if distance_m <= 1e-9:
        return 0.0
    return min(AIR_DRAG_PER_M, math.log(1.0 / AIR_DRAG_MIN_SPEED_RATIO) / distance_m)


def _drag_progress(s: float, distance_m: float) -> tuple[float, float]:
    """(p(s), p'(s)) : progression le long du segment avec friction de l'air (voir ci-dessus). `p'(s)` multiplie la
    vitesse moyenne `distance / durée` pour obtenir la vitesse instantanée."""
    cd = _segment_drag(distance_m) * distance_m
    if cd < 1e-12:
        return s, 1.0
    a = math.expm1(cd)
    return math.log1p(a * s) / cd, (a / cd) / (1.0 + a * s)


# --- pass_ground -----------------------------------------------------------
# Trajectoire droite au sol qui ralentit avec la friction de l'air (`_drag_progress`) : ancien freinage fixe de 5 %
# (valeur donnée par Olivier) remplacé le 08/10/2026 par une perte qui dépend de la distance parcourue.


def _behavior_pass_ground(start: tuple[float, float], end: tuple[float, float], s: float, duration: float) -> BallState:
    progress, dprogress_ds = _drag_progress(s, _real_distance_m(start, end))
    x = start[0] + (end[0] - start[0]) * progress
    y = start[1] + (end[1] - start[1]) * progress
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
    progress, dprogress_ds = _drag_progress(s, distance_m)
    x = start[0] + (end[0] - start[0]) * progress
    y = start[1] + (end[1] - start[1]) * progress
    z = height_max * _hat(s)
    vx = (end[0] - start[0]) * dprogress_ds / duration
    vy = (end[1] - start[1]) * dprogress_ds / duration
    vz = height_max * _hat_derivative(s) / duration
    return BallState(x=x, y=y, z=z, spin=0.0, owner_id=None, vx=vx, vy=vy, vz=vz)


# --- shot ----------------------------------------------------------------
# Ligne droite + courbure latérale de Magnus (offset perpendiculaire en
# _hat, pic à mi-vol, retombe à 0 à l'arrivée -- garantit l'arrivée exacte
# quelle que soit la courbure). z=0 si distance <= 16 m (tir du sol), sinon
# une trajectoire modeste (0 m à 16 m -> 0.8 m à 40 m+, clampé) -- valeurs
# non fournies par le brief, extrapolation raisonnable documentée comme
# telle. < 11 m : tir tendu, AUCUNE courbure même à spin élevé (pas le temps
# de dévier sensiblement sur une distance aussi courte).
#
# Magnus (brief "real Magnus effect", 23/09/2026, Tâche 2) : accélération
# latérale a = _MAGNUS_K * spin * v_base (spin en rad/s, v_base = distance/
# durée en m/s, a en m/s²) -- _MAGNUS_K est donc SANS UNITE (rad est sans
# dimension en SI, l'équation reste homogène). Valeur choisie par ordre de
# grandeur physique réel (pas mesurée sur CE moteur) : a = C_L·ρ·A·r/m ·
# spin · v, avec C_L≈0.25 (coefficient de portance d'un ballon en rotation),
# ρ=1.2 kg/m³ (densité de l'air), A=π·r²≈0.038 m² (section du ballon),
# r=0.11 m (rayon réglementaire), m=0.43 kg (masse réglementaire) ->
# C_L·ρ·A·r/m ≈ 0.003. Ordre de grandeur attendu : à spin=60 rad/s (~10
# tours/s, une frappe enroulée marquée) et v_base=20 m/s, a ≈ 3.6 m/s² ;
# intégrée sur la moitié du temps de vol (cinématique à accélération
# constante, offset_pic = 0.5·a·(duration/2)²), ça donne une déviation de
# l'ordre du mètre sur un tir de 1 à 2 s -- cohérent avec un vrai coup-franc
# enroulé. Le signe de la courbure suit directement le signe de `spin`
# (Tâche 2.6) ; spin=0 -> aucune courbure, trajectoire parfaitement droite
# (Tâche 2.4, remplace l'ancien hash sur `event_ref`, voir CHANGEMENT en
# tête de fichier).
_SHOT_STRAIGHT_MAX_DIST_M = 11.0  # en dessous : tir tendu, pas de courbure
_SHOT_AIRBORNE_MIN_DIST_M = 16.0  # en dessous : au ras du sol
_SHOT_HEIGHT_FAR_M = 0.8
_SHOT_HEIGHT_FAR_DIST_M = 40.0
_MAGNUS_K = 0.003  # sans unité, voir justification ci-dessus


def _shot_height_max_m(distance_m: float) -> float:
    if distance_m <= _SHOT_AIRBORNE_MIN_DIST_M:
        return 0.0
    span = _SHOT_HEIGHT_FAR_DIST_M - _SHOT_AIRBORNE_MIN_DIST_M
    frac = min(1.0, (distance_m - _SHOT_AIRBORNE_MIN_DIST_M) / span)
    return _SHOT_HEIGHT_FAR_M * frac


def _behavior_shot(
    start: tuple[float, float], end: tuple[float, float], s: float, duration: float, spin: float
) -> BallState:
    distance_m = _real_distance_m(start, end)
    px, py = _perp_unit(start, end)
    v_base_m_s = distance_m / duration if duration > 0 else 0.0
    lateral_accel_m_s2 = _MAGNUS_K * spin * v_base_m_s
    curve_peak_m = 0.0 if distance_m < _SHOT_STRAIGHT_MAX_DIST_M else 0.5 * lateral_accel_m_s2 * (duration / 2.0) ** 2
    offset_m = curve_peak_m * _hat(s)
    offset_x = (offset_m / PITCH_LENGTH_M) * px
    offset_y = (offset_m / PITCH_WIDTH_M) * py

    progress, dprogress_ds = _drag_progress(s, distance_m)
    base_x = start[0] + (end[0] - start[0]) * progress
    base_y = start[1] + (end[1] - start[1]) * progress
    x = base_x + offset_x
    y = base_y + offset_y

    height_max = _shot_height_max_m(distance_m)
    z = height_max * _hat(s)

    vx = (end[0] - start[0]) * dprogress_ds / duration + (curve_peak_m / PITCH_LENGTH_M) * px * _hat_derivative(s) / duration
    vy = (end[1] - start[1]) * dprogress_ds / duration + (curve_peak_m / PITCH_WIDTH_M) * py * _hat_derivative(s) / duration
    vz = height_max * _hat_derivative(s) / duration
    return BallState(x=x, y=y, z=z, spin=spin, owner_id=None, vx=vx, vy=vy, vz=vz)


# --- ball_flight -------------------------------------------------------------
# Brief "ball flight after shot" (24/09/2026) -- réutilise EXACTEMENT la
# composante x/y (ligne droite + courbure de Magnus si spin != 0) de
# `_behavior_shot` (appel direct, aucune duplication de cette partie), et
# remplace SEULEMENT sa composante z : `_behavior_shot` ramène toujours z à 0
# en fin de segment (`_hat(1)=0`), correct pour un tir qui s'arrête au pied
# du tireur, mais un `ball_flight` doit atteindre une hauteur cible
# arbitraire (ex. ~2,44m pour "barre") -- rampe linéaire simple de 0 (début
# du vol, ballon au sol au pied du tireur) vers `end_z` (hauteur de la cible,
# voir templates._flight_target), pas de nouveau modèle physique de hauteur.
def _behavior_ball_flight(
    start: tuple[float, float], end: tuple[float, float], s: float, duration: float, spin: float, end_z: float
) -> BallState:
    base = _behavior_shot(start, end, s, duration, spin)
    z = end_z * s
    vz = end_z / duration if duration > 0 else 0.0
    return replace(base, z=z, vz=vz)


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

    progress, dprogress_ds = _drag_progress(s, distance_m)  # le paramètre de la courbe suit la friction de l'air
    one_minus_s = 1.0 - progress
    x = one_minus_s * one_minus_s * start[0] + 2 * one_minus_s * progress * control_x + progress * progress * end[0]
    y = one_minus_s * one_minus_s * start[1] + 2 * one_minus_s * progress * control_y + progress * progress * end[1]
    dx_du = 2 * one_minus_s * (control_x - start[0]) + 2 * progress * (end[0] - control_x)
    dy_du = 2 * one_minus_s * (control_y - start[1]) + 2 * progress * (end[1] - control_y)
    vx = dx_du * dprogress_ds / duration
    vy = dy_du * dprogress_ds / duration

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

    progress, dprogress_ds = _drag_progress(s, distance_m)
    base_x = start[0] + (end[0] - start[0]) * progress
    base_y = start[1] + (end[1] - start[1]) * progress
    x = base_x + (amplitude_m / PITCH_LENGTH_M) * px * bump
    y = base_y + (amplitude_m / PITCH_WIDTH_M) * py * bump

    vx = (end[0] - start[0]) * dprogress_ds / duration + (amplitude_m / PITCH_LENGTH_M) * px * bump_d / duration
    vy = (end[1] - start[1]) * dprogress_ds / duration + (amplitude_m / PITCH_WIDTH_M) * py * bump_d / duration
    return BallState(x=x, y=y, z=0.0, spin=0.0, owner_id=None, vx=vx, vy=vy, vz=0.0)


# --- Rebonds (Phase 6, Bloc B2, 08/10/2026) --------------------------------------
# Le ballon rebondit au lieu de s'arrêter net : sur le sol (restitution 0,70, -15 % de vitesse horizontale par
# rebond), sur un poteau et sur la barre (restitution 0,70). Fonctions PURES : aucune lecture de l'état global,
# aucun `random` ; l'aléa de direction est un hachage déterministe (même principe que `_deterministic_unit`).
#
# Choix des paramètres (valeurs validées par l'architecte) :
# - Restitution 0,70 : la hauteur d'un rebond vaut e² de la précédente (0,49), soit une perte de 51 %, dans la
#   cible « rebond mou » de Football Manager (40 à 50 % de hauteur perdue). Plus bas, le rebond meurt trop vite ;
#   plus haut (0,8 -> 36 % de perte), le ballon « rebondit comme une balle de tennis ».
# - Friction horizontale 15 % par rebond : le contact avec l'herbe freine la composante horizontale (frottement
#   tangentiel) ; 10 à 20 % est la fourchette donnée, 15 % en est le milieu.
# - Arrêt (réglé en B1, 08/10/2026) : un rebond dont le sommet est sous 15 cm est supprimé (5 cm en B2) ; le ballon roule
#   ensuite avec une décélération constante de 4 m/s² (2,5 en B2). Durée totale bornée à 5 s (3 s en B2).
#   Mesuré (12 gabarits x 40 événements, friction de l'air de B1 comprise) : l'arrêt vient APRÈS LE PREMIER REBOND en
#   3,6 s (poteau) et 4,3 s (barre) en moyenne, contre 5,4 et 5,6 s sans friction. La friction de l'air seule ne suffit
#   pas (-8 %) : la durée est portée par la série de rebonds verticaux (restitution 0,70), qu'elle ne freine pas.
#   Le seuil de 15 cm ramène la barre de 6 à 4-5 rebonds ; un rebond de moins de 15 cm lève le ballon de moins d'1 px.
# - Poteau : réflexion horizontale (cylindre vertical, `vz` conservé) ; barre : normale inclinée de 5 à 15° sous
#   l'horizontale côté terrain, donc le ballon repart vers le bas ET vers le terrain, jamais derrière la ligne
#   (une réflexion purement verticale lui laisserait sa vitesse vers l'avant).
# - Aléa D8 : l'angle de sortie vient de la géométrie (écart du point d'impact au centre du montant, angle
#   d'incidence) ; un aléa borné de +-10° sur l'azimut de sortie, déterministe par `event_ref`, s'y ajoute.
# - Planches de publicité : le ballon est arrêté à 3 m des lignes (coordonnées bornées, vitesse annulée).
# - Friction de l'air (B1) : vols balistiques freinés horizontalement par `dv/dt = -c·v²` (voir `AIR_DRAG_PER_M`).
GRAVITY_M_S2 = 9.81
GROUND_RESTITUTION = 0.70
GROUND_HORIZONTAL_KEEP = 0.85  # -15 % de vitesse horizontale par rebond au sol
POST_RESTITUTION = 0.70
BAR_RESTITUTION = 0.70
REBOUND_MIN_APEX_M = 0.15
ROLL_DECEL_M_S2 = 4.0
REBOUND_MAX_DURATION_S = 5.0
REBOUND_AZIMUTH_JITTER_DEG = 10.0
SURFACE_POST = "post"
SURFACE_BAR = "bar"
_POST_MAX_CONTACT_ANGLE_DEG = 35.0  # au-delà, le ballon ne repartirait plus dans le demi-plan opposé
_POST_OFFSET_REF_M = 0.005 * PITCH_WIDTH_M  # résolution de la cible `poteau` (templates : +-0,005 normalisé)
# Inclinaison de la normale de la barre sous l'horizontale (consigne : < 30°). 5 à 15° : le ballon repart vers le
# terrain et vers le bas ; mesuré avec 10 à 30°, le premier rebond au sol montait à 3,2 m en moyenne (10,5 m au
# maximum), trop haut pour un rebond de barre.
_BAR_TILT_MIN_DEG = 5.0
_BAR_TILT_MAX_DEG = 15.0
_BAR_Z_MIN_M = 2.35  # intervalle de la cible `barre` (templates)
_BAR_Z_MAX_M = 2.44
_MIN_BACKWARD_SPEED_M_S = 1.0  # le ballon repart toujours vers le terrain d'au moins 1 m/s
_MIN_DOWNWARD_SPEED_M_S = 1.0  # et vers le bas (barre)
_BOARDS_MARGIN_M = 3.0
_ROLL_STOP_SPEED_M_S = 0.05
_GOAL_Y_MIN_NORM = 0.5 - (GOAL_WIDTH_M / 2.0) / PITCH_WIDTH_M
_GOAL_Y_MAX_NORM = 0.5 + (GOAL_WIDTH_M / 2.0) / PITCH_WIDTH_M


@dataclass(frozen=True)
class _Arc:
    """Un morceau de trajectoire (mètres, temps local `t0`) : vol balistique (gravité) ou roulement (décélération
    constante, `z = 0`)."""

    t0: float
    duration: float
    p0: tuple[float, float, float]
    v0: tuple[float, float, float]
    kind: str  # "flight" | "roll"
    drag: float = 0.0  # coefficient de friction de l'air (1/m) de ce vol, voir `_arc_drag`

    def at(self, tau: float) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
        tau = min(max(tau, 0.0), self.duration)
        x0, y0, z0 = self.p0
        vx, vy, vz = self.v0
        if self.kind == "flight":
            # Vitesse horizontale freinée par l'air (dv/dt = -c·v²) : h(τ) = h0 / (1 + c·h0·τ), distance
            # ln(1 + c·h0·τ) / c ; la composante verticale ne subit que la gravité.
            h0 = math.hypot(vx, vy)
            if self.drag > 0.0 and h0 > 1e-12:
                distance = math.log1p(self.drag * h0 * tau) / self.drag
                speed = h0 / (1.0 + self.drag * h0 * tau)
                ux, uy = vx / h0, vy / h0
                return (
                    (x0 + ux * distance, y0 + uy * distance, z0 + vz * tau - 0.5 * GRAVITY_M_S2 * tau * tau),
                    (ux * speed, uy * speed, vz - GRAVITY_M_S2 * tau),
                )
            return (
                (x0 + vx * tau, y0 + vy * tau, z0 + vz * tau - 0.5 * GRAVITY_M_S2 * tau * tau),
                (vx, vy, vz - GRAVITY_M_S2 * tau),
            )
        speed = math.hypot(vx, vy)
        if speed < 1e-12:
            return (x0, y0, 0.0), (0.0, 0.0, 0.0)
        tau = min(tau, speed / ROLL_DECEL_M_S2)
        distance = speed * tau - 0.5 * ROLL_DECEL_M_S2 * tau * tau
        now = max(0.0, speed - ROLL_DECEL_M_S2 * tau)
        ux, uy = vx / speed, vy / speed
        return (x0 + ux * distance, y0 + uy * distance, 0.0), (ux * now, uy * now, 0.0)


@dataclass(frozen=True)
class ReboundTrajectory:
    """Trajectoire du ballon après un impact (poteau, barre) : rebonds successifs puis arrêt. `state_at(tau)`
    donne l'état `tau` secondes après le contact (borné à `[0, duration]`, jamais d'extrapolation)."""

    surface: str
    contact: tuple[float, float, float]  # x, y normalisés, z en mètres
    exit_velocity: tuple[float, float, float]  # m/s juste après le contact
    arcs: tuple[_Arc, ...]
    duration: float
    ground_bounces: int
    apexes_m: tuple[float, ...]  # sommet de chaque arc qui suit un contact avec le sol
    first_bounce_apex_m: float
    rest: tuple[float, float, float]  # position finale (x, y normalisés, z m)

    def state_at(self, tau: float) -> BallState:
        tau = min(max(tau, 0.0), self.duration)
        arc = self.arcs[-1]
        for candidate in self.arcs:
            if tau <= candidate.t0 + candidate.duration + 1e-12:
                arc = candidate
                break
        (px, py, pz), (vx, vy, vz) = arc.at(tau - arc.t0)
        lo_x, hi_x = -_BOARDS_MARGIN_M, PITCH_LENGTH_M + _BOARDS_MARGIN_M
        lo_y, hi_y = -_BOARDS_MARGIN_M, PITCH_WIDTH_M + _BOARDS_MARGIN_M
        if px < lo_x or px > hi_x:
            px, vx = min(max(px, lo_x), hi_x), 0.0
        if py < lo_y or py > hi_y:
            py, vy = min(max(py, lo_y), hi_y), 0.0
        return BallState(
            x=px / PITCH_LENGTH_M, y=py / PITCH_WIDTH_M, z=0.0 if pz < 1e-9 else pz, spin=0.0, owner_id=None,
            vx=vx / PITCH_LENGTH_M, vy=vy / PITCH_WIDTH_M, vz=vz,
        )


def _rotate(vx: float, vy: float, angle_rad: float) -> tuple[float, float]:
    c, s = math.cos(angle_rad), math.sin(angle_rad)
    return vx * c - vy * s, vx * s + vy * c


def _enforce_backward(vx: float, vy: float) -> tuple[float, float]:
    """Le ballon repart toujours vers le terrain (vx <= -1 m/s), à vitesse horizontale conservée."""
    if vx <= -_MIN_BACKWARD_SPEED_M_S:
        return vx, vy
    horizontal = math.hypot(vx, vy)
    lateral = math.sqrt(max(horizontal * horizontal - _MIN_BACKWARD_SPEED_M_S ** 2, 0.0))
    return -_MIN_BACKWARD_SPEED_M_S, math.copysign(lateral, vy if vy != 0.0 else 1.0)


def rebound_exit_velocity(
    surface: str,
    contact: tuple[float, float, float],
    velocity_m_s: tuple[float, float, float],
    seed_key: str,
    *,
    jitter: bool = True,
) -> tuple[float, float, float]:
    """Vitesse (m/s) juste après l'impact sur un montant. `contact` = (x, y normalisés, z m), `velocity_m_s` =
    vitesse d'arrivée. L'angle de sortie est calculé GÉOMÉTRIQUEMENT (point d'impact, angle d'incidence) puis
    perturbé d'un aléa borné de +-`REBOUND_AZIMUTH_JITTER_DEG` degrés, déterministe pour un `seed_key` donné
    (`jitter=False` pour obtenir la valeur sans aléa)."""
    vx, vy, vz = velocity_m_s
    _, cy, cz = contact
    if surface == SURFACE_POST:
        # Écart latéral du contact au centre du poteau, ramené à un angle de contact de 0 (plein centre : le ballon
        # revient sur lui-même) à 35° (bord : il part de côté). Le poteau est un cylindre vertical : `vz` est conservé.
        post_y = min((_GOAL_Y_MIN_NORM, _GOAL_Y_MAX_NORM), key=lambda y: abs(y - cy))
        offset = max(-1.0, min(1.0, (cy - post_y) * PITCH_WIDTH_M / _POST_OFFSET_REF_M))
        phi = math.radians(_POST_MAX_CONTACT_ANGLE_DEG) * offset
        nx, ny = -math.cos(phi), math.sin(phi)  # normale horizontale : vers le terrain et vers le côté du contact
        vn = vx * nx + vy * ny
        out_x = vx - (1.0 + POST_RESTITUTION) * vn * nx
        out_y = vy - (1.0 + POST_RESTITUTION) * vn * ny
        out_z = vz
    elif surface == SURFACE_BAR:
        # Contact sous la face avant de la barre : normale inclinée de 5 à 15° sous l'horizontale, côté terrain
        # (plus le contact est bas, plus elle est inclinée) -> le ballon repart vers le bas et vers le terrain.
        depth = max(0.0, min(1.0, (_BAR_Z_MAX_M - cz) / (_BAR_Z_MAX_M - _BAR_Z_MIN_M)))
        theta = math.radians(_BAR_TILT_MIN_DEG + (_BAR_TILT_MAX_DEG - _BAR_TILT_MIN_DEG) * depth)
        nx, nz = -math.cos(theta), -math.sin(theta)
        vn = vx * nx + vz * nz
        out_x = vx - (1.0 + BAR_RESTITUTION) * vn * nx
        out_y = vy
        out_z = vz - (1.0 + BAR_RESTITUTION) * vn * nz
    else:
        raise ValueError(f"surface de rebond inconnue : {surface!r}")

    if jitter:
        unit = _deterministic_unit(seed_key, "rebound_azimuth")
        out_x, out_y = _rotate(out_x, out_y, math.radians(REBOUND_AZIMUTH_JITTER_DEG) * (2.0 * unit - 1.0))
    out_x, out_y = _enforce_backward(out_x, out_y)
    if surface == SURFACE_BAR:
        out_z = min(out_z, -_MIN_DOWNWARD_SPEED_M_S)
    return out_x, out_y, out_z


def _arc_drag(horizontal_speed: float) -> float:
    """Coefficient de friction d'un vol : `AIR_DRAG_PER_M`, borné pour que la perte relative de vitesse initiale ne
    dépasse pas `AIR_DRAG_MAX_RATE_PER_S`."""
    if horizontal_speed <= 1e-9:
        return 0.0
    return min(AIR_DRAG_PER_M, AIR_DRAG_MAX_RATE_PER_S / horizontal_speed)


def _simulate_rebound(
    p0: tuple[float, float, float], v0: tuple[float, float, float]
) -> tuple[tuple[_Arc, ...], int, tuple[float, ...]]:
    """Vols balistiques successifs avec rebonds au sol, puis roulement jusqu'à l'arrêt (ou jusqu'à
    `REBOUND_MAX_DURATION_S`). Retourne (arcs, nombre de contacts avec le sol, sommets des arcs de rebond)."""
    arcs: list[_Arc] = []
    apexes: list[float] = []
    ground_contacts = 0
    t = 0.0
    x, y, z = p0
    vx, vy, vz = v0
    while True:
        remaining = REBOUND_MAX_DURATION_S - t
        fall_time = (vz + math.sqrt(vz * vz + 2.0 * GRAVITY_M_S2 * z)) / GRAVITY_M_S2
        drag = _arc_drag(math.hypot(vx, vy))
        if fall_time >= remaining:
            # Le prochain arc ne tient pas dans la durée maximale : le rebond s'arrête au dernier contact avec le
            # sol (ballon au sol, encore en mouvement), jamais coupé en plein vol.
            if not arcs:
                arcs.append(_Arc(t, remaining, (x, y, z), (vx, vy, vz), "flight", drag))
            return tuple(arcs), ground_contacts, tuple(apexes)
        arc = _Arc(t, fall_time, (x, y, z), (vx, vy, vz), "flight", drag)
        arcs.append(arc)
        (x, y, _), (vx, vy, _) = arc.at(fall_time)
        t += fall_time
        impact_vz = vz - GRAVITY_M_S2 * fall_time
        ground_contacts += 1
        z, vz = 0.0, -GROUND_RESTITUTION * impact_vz
        vx, vy = vx * GROUND_HORIZONTAL_KEEP, vy * GROUND_HORIZONTAL_KEEP
        apex = vz * vz / (2.0 * GRAVITY_M_S2)
        if apex < REBOUND_MIN_APEX_M:
            break
        apexes.append(apex)
    speed = math.hypot(vx, vy)
    remaining = REBOUND_MAX_DURATION_S - t
    if speed > _ROLL_STOP_SPEED_M_S and remaining > 0.0:
        arcs.append(_Arc(t, min(speed / ROLL_DECEL_M_S2, remaining), (x, y, 0.0), (vx, vy, 0.0), "roll"))
    else:
        arcs.append(_Arc(t, 0.0, (x, y, 0.0), (0.0, 0.0, 0.0), "roll"))
    return tuple(arcs), ground_contacts, tuple(apexes)


def rebound_trajectory(
    surface: str, contact_state: BallState, seed_key: str, *, jitter: bool = True
) -> ReboundTrajectory:
    """Rebond après l'impact de `contact_state` (état d'arrivée du ballon : position normalisée, `z` en mètres,
    vitesse) sur un montant (`SURFACE_POST` ou `SURFACE_BAR`) : le ballon repart du point de contact, rebondit sur le
    sol (restitution 0,70, -15 % de vitesse horizontale par rebond) et s'arrête."""
    contact = (contact_state.x, contact_state.y, contact_state.z)
    velocity = (contact_state.vx * PITCH_LENGTH_M, contact_state.vy * PITCH_WIDTH_M, contact_state.vz)
    exit_velocity = rebound_exit_velocity(surface, contact, velocity, seed_key, jitter=jitter)
    p0 = (contact_state.x * PITCH_LENGTH_M, contact_state.y * PITCH_WIDTH_M, contact_state.z)
    arcs, ground_contacts, apexes = _simulate_rebound(p0, exit_velocity)
    duration = arcs[-1].t0 + arcs[-1].duration
    trajectory = ReboundTrajectory(
        surface=surface, contact=contact, exit_velocity=exit_velocity, arcs=arcs, duration=duration,
        ground_bounces=ground_contacts, apexes_m=apexes, first_bounce_apex_m=apexes[0] if apexes else 0.0,
        rest=(0.0, 0.0, 0.0),
    )
    end = trajectory.state_at(duration)
    return replace(trajectory, rest=(end.x, end.y, end.z))


_REBOUND_SURFACE_BY_OUTCOME = {"poteau": SURFACE_POST, "barre": SURFACE_BAR}


def rebound_after_flight(sequence: Sequence, outcome: str | None) -> ReboundTrajectory | None:
    """Rebond qui prolonge un clip dont le vol (`ball_flight`) s'arrête sur un montant (`outcome` `poteau` ou
    `barre`). `None` pour toute autre issue (but, arrêt, hors cadre, tacle, dégagement : inchangées) ou pour une
    séquence sans vol. L'état de contact est l'état d'arrivée du vol, donc la trajectoire existante ne change pas :
    le rebond commence là où elle s'arrête (à `sequence.duration`)."""
    surface = _REBOUND_SURFACE_BY_OUTCOME.get(outcome or "")
    if surface is None or len(sequence.keyframes) < 2 or sequence.keyframes[-2].physics_tag != BALL_FLIGHT:
        return None
    contact_state = ball_state_at(sequence, sequence.duration)
    return rebound_trajectory(surface, contact_state, f"{sequence.event_ref}|rebound")


def _surface_from_contact(contact_state: BallState) -> str:
    return SURFACE_BAR if contact_state.z >= _BAR_Z_MIN_M - 0.05 else SURFACE_POST


# Rebond d'un ballon qui retombe sur le sol (centre de corner : `cross` puis `deflect`) : seule la HAUTEUR rebondit
# (restitution 0,70, arrêt sous `REBOUND_MIN_APEX_M` de sommet), la trajectoire x/y du `deflect` est inchangée.
def _landing_speed_m_s(sequence: Sequence, kf_a: Keyframe) -> float | None:
    idx = next((i for i, kf in enumerate(sequence.keyframes) if kf is kf_a), 0)
    if idx == 0:
        return None
    previous = sequence.keyframes[idx - 1]
    if previous.physics_tag not in (CROSS, PASS_LOB):
        return None
    arrival = ball_state_at(sequence, kf_a.t)  # `_find_ball_segment` résout t = kf_a.t vers le segment PRÉCÉDENT
    return -arrival.vz if arrival.vz < 0.0 else None


def _vertical_bounce(landing_speed_m_s: float, tau: float, horizon: float) -> tuple[float, float]:
    """(z, vz) `tau` s après l'atterrissage à `landing_speed_m_s` : rebonds successifs jusqu'à un sommet < `REBOUND_MIN_APEX_M`, ou
    jusqu'à ce que le dernier arc ne tienne plus dans `horizon` (le ballon est alors au sol à la fin du segment)."""
    t0 = 0.0
    vz_up = GROUND_RESTITUTION * landing_speed_m_s
    while vz_up * vz_up / (2.0 * GRAVITY_M_S2) >= REBOUND_MIN_APEX_M:
        arc = 2.0 * vz_up / GRAVITY_M_S2
        if t0 + arc > horizon:
            break
        if tau <= t0 + arc:
            local = tau - t0
            return vz_up * local - 0.5 * GRAVITY_M_S2 * local * local, vz_up - GRAVITY_M_S2 * local
        t0 += arc
        vz_up *= GROUND_RESTITUTION
    return 0.0, 0.0


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
        state = _behavior_shot(start, end, s, duration, kf_a.ball.spin)
    elif tag == BALL_FLIGHT:
        state = _behavior_ball_flight(start, end, s, duration, kf_a.ball.spin, kf_b.ball.z)
    elif tag == CROSS:
        state = _behavior_cross(start, end, s, duration, seed_key)
    elif tag == BOUNCE:
        contact_state = ball_state_at(sequence, kf_a.t)  # fin du segment précédent (le vol)
        trajectory = rebound_trajectory(
            _surface_from_contact(contact_state), contact_state, f"{sequence.event_ref}|rebound"
        )
        state = trajectory.state_at(s * duration)
    else:
        state = _behavior_deflect(start, end, s, duration, seed_key)
        landing = _landing_speed_m_s(sequence, kf_a)
        if landing is not None:
            z, vz = _vertical_bounce(landing, s * duration, duration)
            state = replace(state, z=z, vz=vz)

    owner_id = kf_a.ball.owner_id if s < 1.0 else kf_b.ball.owner_id
    return replace(state, owner_id=owner_id)

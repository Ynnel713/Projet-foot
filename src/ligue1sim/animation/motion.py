"""Phase 3.1 : interpolation continue des joueurs entre les keyframes
discrets d'une `Sequence` (voir animation.types) -- `interpolate(sequence, t)
-> FrameState` donne la position/vitesse de chaque joueur suivi à un instant
`t` QUELCONQUE (pas seulement aux instants des keyframes), pour un rendu
fluide côté client.

Consommateur PUR de `Sequence` : ce module ne modifie ni `templates.py`, ni
`sequence_generator.py`, ni `types.py`, et ne recalcule jamais où un
`Keyframe` place un joueur -- il ne fait qu'interpoler ENTRE ces points déjà
décidés. Aucun tirage aléatoire : `interpolate` est une fonction pure de
`(sequence, t)`, voir tests/test_motion.py (continuité, déterminisme,
non-collision).

**Poste (comportement 2, vitesse max) et rôle (comportements 3-4, décalage
temporel/"runner") sont lus directement sur `sequence.roster`** (voir
`animation.types.Sequence.roster`/`RosterEntry`) -- une `Sequence` est
auto-descriptive, ce module n'a donc jamais besoin de recevoir la `Lineup`
d'origine en plus de la `Sequence`. `Sequence.__post_init__` garantit déjà
que `roster` couvre tous les joueurs des keyframes (voir `animation.types`)
: un joueur référencé sans entrée de roster ne peut pas exister dans une
`Sequence` valide, donc pas non plus atteindre `interpolate`.

**Joueurs "décor" (`sequence.background`, voir `sequence_generator.
enrich_with_background`, Point 1 du bilan du 23/09/2026)** : pas de
keyframes ni de Bézier pour eux, juste un `BackgroundTrack` (position de
départ + drift) parcouru avec la même courbe `_ease_progress` que les
joueurs actifs, mais sans vitesse plafonnée (l'amplitude est déjà bornée à
la construction). `interpolate` couvre les deux populations dans un seul
`FrameState`, et les fait passer ensemble par `_apply_avoidance` (22
joueurs, pas seulement les 2-4 actifs).

**Limite connue et non corrigée : un segment "impossible" (distance qu'un
joueur ne peut PHYSIQUEMENT pas couvrir à v_max dans le temps du segment)
produit un saut de position À LA TRANSITION vers le keyframe suivant, pas
une vitesse excessive en continu.** Le repli linéaire (`_interpolate_segment`,
comportement 2) clampe `progress` à 1.0 -- donc la vitesse INSTANTANÉE ne
dépasse jamais `v_max` PENDANT le segment -- mais si `v_max * duration <
distance`, `progress` reste < 1.0 même à `elapsed = duration` : le joueur
n'atteint jamais `pos_b` en interpolant DANS ce segment. Au tick suivant
(t = kf_b.t exactement), `_find_segment` bascule sur le segment SUIVANT, où
`pos_a` vaut alors `kf_b.players[player_id]` = la position cible -- la
position "saute" donc instantanément au keyframe visé à cet instant précis,
avec une vitesse calculée par différence finie qui explose (des milliers
d'unités/s, vérifié dans tests/test_motion.py::TestImpossibleSegment). Ce
n'est un problème que si un gabarit demande RÉELLEMENT plus que `v_max` en
moyenne sur un segment (voir la table de marge par gabarit dans
docs/simulation_physique_archi.md, section "Point B") -- aucun des 12
gabarits actuels n'atteint ce seuil (`une_deux` est le plus proche, à 76%
de `v_max`), donc ce cas n'est PAS corrigé ici (pas de raison de complexifier
sans besoin réel) : seulement documenté et testé pour qu'il ne surprenne pas
une future session (`ball.py` aura probablement la même contrainte)."""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass

from ligue1sim.animation.types import BackgroundTrack, BallState, PlayerId, Sequence
from ligue1sim.pitch_geometry import PITCH_LENGTH_M, PITCH_WIDTH_M

# --- Vitesse maximale par poste (comportement 2) -------------------------
# m/s, vitesse de pointe soutenable -- valeurs données par Olivier pour
# GK/DC/MDC/MC/MOC+ailiers/BU ; LB/RB/SA/ATT non spécifiés, complétés par
# extrapolation raisonnable (latéraux entre DC et MC, SA/ATT alignés sur BU
# -- profil offensif proche), documentée comme telle plutôt que présentée
# comme une donnée fournie.
MAX_SPEED_MPS: dict[str, float] = {
    "GK": 6.0,
    "DC": 7.0,
    "LB": 8.0,
    "RB": 8.0,
    "MDC": 8.0,
    "MC": 8.0,
    "MOC": 9.0,
    "AG": 9.0,
    "AD": 9.0,
    "BU": 9.0,
    "SA": 9.0,
    "ATT": 9.0,
}
_DEFAULT_MAX_SPEED_MPS = 8.0  # repli pour un poste absent de MAX_SPEED_MPS (poste inconnu, ex. joueur de test synthétique)


def max_speed_normalized(poste: str | None) -> float:
    """Vitesse maximale d'un poste, convertie en unités normalisées par
    seconde (voir ligue1sim.pitch_geometry -- terrain 105 m de long).
    Simplification assumée : la conversion utilise UNIQUEMENT la longueur
    (105 m), pas la largeur (68 m), donc un déplacement purement latéral est
    en réalité plafonné un peu plus bas que la vraie vitesse du poste (68/105
    ≈ 65% de la valeur nominale) -- acceptable pour un plafond de sécurité,
    pas une simulation physique exacte."""
    speed = MAX_SPEED_MPS.get(poste, _DEFAULT_MAX_SPEED_MPS) if poste else _DEFAULT_MAX_SPEED_MPS
    return speed / PITCH_LENGTH_M


# --- Décalage temporel déterministe (comportement 3) ----------------------
_MAX_START_OFFSET_RATIO = 0.3  # fraction de la durée totale


def _start_offset(player_id: PlayerId, duration: float) -> float:
    """Décalage temporel déterministe (secondes) avant qu'un joueur "non
    impliqué" (voir `player_roles`) commence à réagir -- même principe que
    `events._deterministic_rng` (hash sha256, pas `hash()` qui varie d'un
    process Python à l'autre) : la même combinaison retombe toujours sur le
    même décalage, dans [0, 0.3 * duration]."""
    digest = hashlib.sha256(f"start_offset|{player_id}".encode()).digest()
    fraction = int.from_bytes(digest[:8], "big") / 2**64  # ∈ [0, 1)
    return fraction * _MAX_START_OFFSET_RATIO * duration


def _is_primary_role(role: str | None) -> bool:
    """"Impliqué" au sens fort (comportement 3) : réagit sans délai. Les
    rôles "scorer"/"assist" pilotent directement l'action -- les rôles
    "support*" (comportement 4, "runner") réagissent avec un léger temps de
    retard comme n'importe quel joueur non directement sollicité."""
    return role in ("scorer", "assist")


# --- Interpolation par courbe de Bézier cubique (comportement 1) ---------
# Points de contrôle de la courbe d'accélération/décélération -- mêmes
# valeurs que CSS cubic-bezier(0.42, 0, 0.58, 1) ("ease-in-out"), un choix
# standard et reconnu plutôt qu'un réglage inventé. Résolue par
# Newton-Raphson (même technique que les moteurs de rendu web pour
# cubic-bezier()) : x(u) donne le temps, y(u) donne la progression, on
# cherche u tel que x(u) = fraction de temps écoulée.
_EASE_P1 = (0.42, 0.0)
_EASE_P2 = (0.58, 1.0)
# Ratio pic/moyenne mesuré empiriquement pour cette courbe précise (voir
# scripts/preview_motion.py ou la mesure faite lors de l'implémentation) :
# ≈1.72. Un segment qui exigerait déjà plus de 55% de la vitesse max EN
# MOYENNE dépasserait donc la vitesse max à son pic si on le laissait
# accélérer/décélérer -- il retombe alors sur un mouvement linéaire à
# vitesse constante (voir _interpolate_segment), seule façon de garantir
# qu'aucun instant ne dépasse jamais la vitesse max.
_EASE_SAFE_AVG_SPEED_RATIO = 0.55


def _bezier_component(p1: float, p2: float, u: float) -> float:
    one_minus_u = 1.0 - u
    return 3 * one_minus_u * one_minus_u * u * p1 + 3 * one_minus_u * u * u * p2 + u**3


def _bezier_derivative(p1: float, p2: float, u: float) -> float:
    one_minus_u = 1.0 - u
    return 3 * one_minus_u * one_minus_u * p1 + 6 * one_minus_u * u * (p2 - p1) + 3 * u * u * (1.0 - p2)


def _ease_progress(s: float) -> float:
    """Reparamétrise une fraction de temps linéaire `s` ∈ [0, 1] en une
    progression accélérée-puis-décélérée (voir _EASE_P1/_EASE_P2)."""
    if s <= 0.0:
        return 0.0
    if s >= 1.0:
        return 1.0
    u = s
    for _ in range(8):
        error = _bezier_component(_EASE_P1[0], _EASE_P2[0], u) - s
        derivative = _bezier_derivative(_EASE_P1[0], _EASE_P2[0], u)
        if abs(derivative) < 1e-9:
            break
        u -= error / derivative
        u = min(1.0, max(0.0, u))
    return _bezier_component(_EASE_P1[1], _EASE_P2[1], u)


def _real_distance_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    dx_m = (b[0] - a[0]) * PITCH_LENGTH_M
    dy_m = (b[1] - a[1]) * PITCH_WIDTH_M
    return math.hypot(dx_m, dy_m)


def _interpolate_segment(
    pos_a: tuple[float, float], pos_b: tuple[float, float], elapsed: float, duration: float, v_max: float
) -> tuple[float, float]:
    """Position entre `pos_a` (t=0 du segment) et `pos_b` (t=duration),
    `elapsed` secondes après le début du segment -- Bézier ease-in-out
    (comportement 1) si le trajet est atteignable à vitesse max sans
    dépasser le pic mesuré (voir _EASE_SAFE_AVG_SPEED_RATIO), sinon repli
    linéaire à vitesse constante (v_max ou moins) : seule façon de GARANTIR
    qu'aucun instant ne dépasse jamais v_max (comportement 2), même quand le
    gabarit demande un trajet trop long pour le temps imparti."""
    if duration <= 0:
        return pos_b
    distance_m = _real_distance_m(pos_a, pos_b)
    required_avg_speed = (distance_m / PITCH_LENGTH_M) / duration  # unités normalisées/s, cohérent avec v_max

    if required_avg_speed <= v_max * _EASE_SAFE_AVG_SPEED_RATIO:
        progress = _ease_progress(min(1.0, max(0.0, elapsed / duration)))
    else:
        # Mouvement linéaire à v_max : progress = distance parcourable / distance totale.
        normalized_distance = distance_m / PITCH_LENGTH_M
        progress = min(1.0, (v_max * elapsed) / normalized_distance) if normalized_distance > 0 else 1.0

    return (pos_a[0] + (pos_b[0] - pos_a[0]) * progress, pos_a[1] + (pos_b[1] - pos_a[1]) * progress)


def _find_segment(sequence: Sequence, t: float) -> tuple[int, int, float]:
    """Indices des deux keyframes encadrant `t` (clampé aux bornes de la
    séquence) et le temps écoulé depuis le début du segment."""
    keyframes = sequence.keyframes
    if t <= keyframes[0].t:
        return 0, 0, 0.0
    if t >= keyframes[-1].t:
        last = len(keyframes) - 1
        return last, last, 0.0
    for i in range(len(keyframes) - 1):
        if keyframes[i].t <= t <= keyframes[i + 1].t:
            return i, i + 1, t - keyframes[i].t
    last = len(keyframes) - 1
    return last, last, 0.0


def _player_position_at(sequence: Sequence, player_id: PlayerId, t: float, v_max: float) -> tuple[float, float]:
    idx_a, idx_b, elapsed = _find_segment(sequence, t)
    if idx_a == idx_b:
        return sequence.keyframes[idx_a].players[player_id]
    kf_a, kf_b = sequence.keyframes[idx_a], sequence.keyframes[idx_b]
    return _interpolate_segment(
        kf_a.players[player_id], kf_b.players[player_id], elapsed, kf_b.t - kf_a.t, v_max
    )


# --- Évitement minimal (comportement 5) -----------------------------------
_AVOIDANCE_TRIGGER_M = 1.5  # déclenche une répulsion
_AVOIDANCE_PASSES = 4  # relaxation simple, pas un vrai solveur physique


def _stable_repulsion_angle(a: PlayerId, b: PlayerId) -> float:
    """Direction déterministe (radians) utilisée quand deux joueurs sont
    exactement à la même position -- jamais aléatoire (voir même principe
    que _start_offset)."""
    digest = hashlib.sha256(f"{a}|{b}".encode()).digest()
    return (int.from_bytes(digest[:4], "big") % 360) * math.pi / 180.0


def _apply_avoidance(positions: dict[PlayerId, tuple[float, float]]) -> dict[PlayerId, tuple[float, float]]:
    """Répulsion latérale minimale : pas un vrai pathfinding, juste éviter
    que deux ronds se superposent à l'écran (comportement 5). Quelques
    passes de relaxation (pas un solveur physique) -- l'écart entre le seuil
    de déclenchement (1,5 m) et l'exigence de test (jamais < 0,5 m) laisse
    une marge confortable pour converger."""
    ids = sorted(positions, key=str)  # ordre stable, indépendant du hash Python (déterminisme)
    adjusted = dict(positions)
    for _pass in range(_AVOIDANCE_PASSES):
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                a, b = ids[i], ids[j]
                ax, ay = adjusted[a]
                bx, by = adjusted[b]
                dist_m = _real_distance_m((ax, ay), (bx, by))
                if dist_m >= _AVOIDANCE_TRIGGER_M:
                    continue
                if dist_m < 1e-9:
                    angle = _stable_repulsion_angle(a, b)
                    dir_x, dir_y = math.cos(angle), math.sin(angle)
                else:
                    dx_m = (bx - ax) * PITCH_LENGTH_M
                    dy_m = (by - ay) * PITCH_WIDTH_M
                    dir_x, dir_y = dx_m / dist_m, dy_m / dist_m
                missing_m = _AVOIDANCE_TRIGGER_M - dist_m
                push_x = (dir_x * missing_m / 2) / PITCH_LENGTH_M
                push_y = (dir_y * missing_m / 2) / PITCH_WIDTH_M
                adjusted[a] = (ax - push_x, ay - push_y)
                adjusted[b] = (bx + push_x, by + push_y)
    return adjusted


def _ball_carrier_at(sequence: Sequence, t: float) -> PlayerId | None:
    """Porteur du ballon à `t` : celui du keyframe qui DÉBUTE le segment
    courant (la passe/le changement de porteur a lieu à la transition vers
    le keyframe suivant, pas progressivement)."""
    idx_a, _idx_b, _elapsed = _find_segment(sequence, t)
    return sequence.keyframes[idx_a].ball.owner_id


# --- Résultat --------------------------------------------------------------


@dataclass(frozen=True)
class PlayerMotionState:
    x: float
    y: float
    vx: float  # unités normalisées par seconde
    vy: float
    is_ball_carrier: bool


@dataclass(frozen=True)
class FrameState:
    t: float
    players: dict[PlayerId, PlayerMotionState]
    ball: BallState | None = None  # géré par animation.ball (phase 3.2) -- toujours None ICI (interpolate ne le peuple jamais), mais le TYPE accepte déjà un BallState réel pour ne rien casser côté appelant quand ball.py sera branché


_VELOCITY_EPSILON_S = 1e-4  # pas de différence finie pour (vx, vy) -- petit, déterministe, pas de dépendance à dt du test


def _background_position_at(track: BackgroundTrack, t: float, duration: float) -> tuple[float, float]:
    """Position d'un joueur "décor" (`sequence.background`, voir docstring
    de module) à l'instant `t` -- pas de keyframes, juste `start + drift *
    progress`, `progress` suivant la même courbe ease-in-out que les joueurs
    actifs (`_ease_progress`) pour un mouvement visuellement cohérent avec
    le reste de la scène. Aucun plafond de vitesse (comportement 2) : l'
    amplitude de `drift` est déjà bornée à la construction
    (`sequence_generator.enrich_with_background`)."""
    progress = _ease_progress(t / duration) if duration > 0 else 0.0
    return (track.start[0] + track.drift[0] * progress, track.start[1] + track.drift[1] * progress)


def _raw_position_at(sequence: Sequence, player_id: PlayerId, t: float) -> tuple[float, float]:
    """Dispatch vers la trajectoire d'un joueur actif (keyframes + Bézier,
    comportements 1-4) ou "décor" (`BackgroundTrack`, drift) -- voir
    docstring de module. Un `player_id` ne peut appartenir qu'à l'un des
    deux (invariant 3 de `Sequence`), jamais les deux."""
    if player_id in sequence.background:
        return _background_position_at(sequence.background[player_id], t, sequence.duration)

    entry = sequence.roster[player_id]
    v_max = max_speed_normalized(entry.poste)
    offset = 0.0 if _is_primary_role(entry.role) else _start_offset(player_id, sequence.duration)
    return _player_position_at(sequence, player_id, t - offset, v_max)


def interpolate(sequence: Sequence, t: float) -> FrameState:
    """Position/vitesse continue de chaque joueur de `sequence` à l'instant
    `t` (clampé aux bornes de la séquence) -- voir les comportements 1-5 en
    tête de module, plus le drift des joueurs "décor" (`sequence.background`).
    Poste et rôle de chaque joueur sont lus sur `sequence.roster` (voir
    docstring de module) : `Sequence` est auto-descriptive, `interpolate`
    n'a besoin de rien d'autre."""
    clamped_t = min(max(t, sequence.keyframes[0].t), sequence.keyframes[-1].t)
    all_ids = set(sequence.keyframes[0].players) | set(sequence.background)

    raw_positions: dict[PlayerId, tuple[float, float]] = {}
    velocities: dict[PlayerId, tuple[float, float]] = {}
    for player_id in all_ids:
        raw_positions[player_id] = _raw_position_at(sequence, player_id, clamped_t)

        pos_before = _raw_position_at(sequence, player_id, clamped_t - _VELOCITY_EPSILON_S)
        pos_after = _raw_position_at(sequence, player_id, clamped_t + _VELOCITY_EPSILON_S)
        vx = (pos_after[0] - pos_before[0]) / (2 * _VELOCITY_EPSILON_S)
        vy = (pos_after[1] - pos_before[1]) / (2 * _VELOCITY_EPSILON_S)
        velocities[player_id] = (vx, vy)

    adjusted_positions = _apply_avoidance(raw_positions)
    carrier_id = _ball_carrier_at(sequence, clamped_t)

    players = {
        player_id: PlayerMotionState(
            x=xy[0], y=xy[1], vx=velocities[player_id][0], vy=velocities[player_id][1],
            is_ball_carrier=(player_id == carrier_id),
        )
        for player_id, xy in adjusted_positions.items()
    }
    return FrameState(t=clamped_t, players=players, ball=None)

"""État dynamique d'un joueur ou du ballon à un instant donné. Les positions
restent calculées par interpolation des keyframes de gabarit -- c'est une
migration pure, jamais un nouveau calcul physique.

Pont ADDITIF au-dessus de `animation.motion.interpolate` (brief "introduce
PlayerState and BallState", 24/09/2026, préparation étape 2 du PDF) --
`interpolate` n'est PAS modifié : `player_states_and_ball_at` l'appelle tel
quel puis reformate son résultat déjà calculé (`FrameState`) en
`(list[PlayerState], DynamicBallState)`, sans jamais recalculer une
position. C'est le choix retenu pour garantir mécaniquement "aucune
modification visuelle" (voir retour de brief) -- le contrat existant
d'`interpolate`, déjà couvert par tests/test_motion.py, reste physiquement
intact.

`DynamicBallState` (ce fichier) est DISTINCT de `ligue1sim.animation.types.
BallState` (moteur ballon actuel, champs x/y/z/spin/owner_id) -- collision
de nom repérée et tranchée le 24/09/2026 (brief "add velocity/acceleration
to PlayerState") : renommé `DynamicBallState` ici précisément pour ne plus
les confondre à l'import. Ne pas confondre les deux : `types.BallState` est
le contrat interne au moteur d'animation (ball.py/motion.py/serialize.py),
`state.DynamicBallState` est la vue "état dynamique" destinée à un futur
moteur physique (étape 2+ du PDF).

DETTE (24/09/2026) : `PlayerState.team` porte `"scorer"` / `"opponent"`
faute de mieux -- `Sequence` ne connaît pas le camp domicile/extérieur
(voir `RosterEntry`, `animation.types`), seulement quelle équipe a marqué.
À faire remonter à `home`/`away` quand `Sequence` portera cette information
(brief futur, préalable étape 4 physique) -- nécessiterait de faire
remonter cette info depuis `Timeline`/`Lineup` jusqu'à `Sequence`, un
changement de contrat hors périmètre d'une migration pure.

Autre substitution documentée : `PlayerState.current_action` ne distingue
que `"idle"`/`"sprint"` (seuil de vitesse, voir `_SPRINT_THRESHOLD_M_S`) --
`"pass"`/`"shoot"` (cités en exemple par le brief d'origine) exigeraient de
lire les tags narratifs du gabarit (`Keyframe.tag`/`physics_tag`), une vraie
classification d'action hors périmètre de cette migration structurelle.

DETTE (24/09/2026) — accélération : `acceleration` calculée par dérivée
numérique peut dépasser 400 m/s² à deux types d'instants hérités de
`motion.interpolate` :

- frontières de keyframe avec segment impossible (déjà documenté dans
  `motion.py`) ;
- points où le joueur atteint sa cible avant la fin du segment (repli
  linéaire -> position constante -> v=0 brutal).

Ces pics ne sont pas des artefacts de calcul -- ils reflètent des
discontinuités RÉELLES de la fonction position (vérifié : à ces instants
précis, la position elle-même devient exactement constante d'un échantillon
à l'autre, la vitesse y tombe donc brutalement à 0 quel que soit le pas de
dérivation choisi). Ils seront supprimés à l'étape 4 du PDF (physique
joueurs), qui remplacera `motion.interpolate` par un système à base de
vitesse/accélération. Ne pas lisser dans ce brief -- ce serait masquer la
cause plutôt que la corriger."""

from __future__ import annotations

import math
from dataclasses import dataclass

from ligue1sim.animation.motion import interpolate
from ligue1sim.animation.types import PlayerId, Sequence
from ligue1sim.pitch_geometry import PITCH_LENGTH_M, PITCH_WIDTH_M

_SPRINT_THRESHOLD_M_S = 3.0  # au-dessus : "sprint", en-deca : "idle" -- voir docstring de module
_DERIVATIVE_DT_S = 0.01  # pas de la derivee numerique de velocity/acceleration -- voir _velocities_and_accelerations_m_s


@dataclass(frozen=True)
class PlayerState:
    player_id: str
    team: str  # "scorer" / "opponent" -- DETTE, voir docstring de module
    position: tuple[float, float]  # x, y en metres
    direction_body: float  # radians, 0 = vers la droite (atan2(vy_m, vx_m))
    current_action: str  # "idle" | "sprint" -- voir docstring de module
    target: tuple[float, float] | None  # x, y en metres, destination finale de ce joueur sur ce clip
    velocity: tuple[float, float]  # vx, vy en m/s -- derivee numerique de `position`, voir _velocities_and_accelerations_m_s
    acceleration: tuple[float, float]  # ax, ay en m/s^2 -- derivee numerique de `velocity`, meme fonction


@dataclass(frozen=True)
class DynamicBallState:
    position: tuple[float, float, float]  # x, y, z en metres
    velocity: tuple[float, float, float]  # vx, vy, vz en m/s
    possession: str | None  # player_id du porteur, ou None


def _final_target_m(sequence: Sequence, player_id: PlayerId) -> tuple[float, float]:
    """Destination finale d'un joueur sur ce clip, en mètres -- le dernier
    keyframe scripté pour un joueur actif, ou `start + drift` (déjà la
    position finale par construction, voir `BackgroundTrack`) pour un
    figurant. Ne recalcule rien : lit une position déjà décidée par le
    gabarit ou `enrich_with_background`."""
    if player_id in sequence.background:
        track = sequence.background[player_id]
        x = track.start[0] + track.drift[0]
        y = track.start[1] + track.drift[1]
    else:
        x, y = sequence.keyframes[-1].players[player_id]
    return (x * PITCH_LENGTH_M, y * PITCH_WIDTH_M)


def _positions_m_at(sequence: Sequence, t: float) -> dict[PlayerId, tuple[float, float]]:
    """Positions (mètres) de tous les joueurs à `t`, via `interpolate`
    INCHANGÉ -- un seul appel "pleine frame" par instant demandé, jamais un
    appel par joueur (`interpolate` calcule déjà tout le monde d'un coup)."""
    frame = interpolate(sequence, t)
    return {pid: (s.x * PITCH_LENGTH_M, s.y * PITCH_WIDTH_M) for pid, s in frame.players.items()}


def _velocities_m_s_at(
    sequence: Sequence, t: float, dt: float, duration: float
) -> dict[PlayerId, tuple[float, float]]:
    """`velocity(t) ≈ (position(t+dt) - position(t-dt)) / (2·dt)` (Tâche
    3.2 du brief "add velocity/acceleration to PlayerState", 24/09/2026) --
    différence CENTRÉE par défaut. Aux bords (`t - dt < 0` ou `t + dt >
    durée`), bascule sur une différence AVANT/ARRIÈRE (une seule évaluation
    supplémentaire, jamais hors des bornes de la séquence -- `interpolate`
    clampe de toute façon, mais une différence centrée y perdrait la moitié
    de son amplitude sans le détecter, d'où ce branchement explicite plutôt
    que de laisser le clamp interne masquer le bord)."""
    if t - dt < 0.0:
        a, b, denom = _positions_m_at(sequence, t), _positions_m_at(sequence, t + dt), dt
    elif t + dt > duration:
        a, b, denom = _positions_m_at(sequence, t - dt), _positions_m_at(sequence, t), dt
    else:
        a, b, denom = _positions_m_at(sequence, t - dt), _positions_m_at(sequence, t + dt), 2 * dt
    return {pid: ((b[pid][0] - a[pid][0]) / denom, (b[pid][1] - a[pid][1]) / denom) for pid in a}


def _velocities_and_accelerations_m_s(
    sequence: Sequence, t: float, dt: float = _DERIVATIVE_DT_S
) -> tuple[dict[PlayerId, tuple[float, float]], dict[PlayerId, tuple[float, float]]]:
    """`acceleration(t) ≈ (velocity(t+dt) - velocity(t-dt)) / (2·dt)`
    (Tâche 3.2) -- même règle de bord que `_velocities_m_s_at`, appliquée
    ICI (autour de `t`, pour choisir entre `velocity(t±dt)`) ET
    récursivement DANS `_velocities_m_s_at` (autour de `t+dt`/`t-dt`, pour
    choisir entre `position(t±dt±dt)`) : un joueur peut être dans
    l'intérieur du clip pour l'accélération mais toucher un bord pour l'une
    de ses deux vitesses voisines (ex. `t` proche de `dt` du bord), les deux
    niveaux doivent donc décider indépendamment."""
    velocity = _velocities_m_s_at(sequence, t, dt, sequence.duration)
    if t - dt < 0.0:
        v_a, v_b, denom = velocity, _velocities_m_s_at(sequence, t + dt, dt, sequence.duration), dt
    elif t + dt > sequence.duration:
        v_a, v_b, denom = _velocities_m_s_at(sequence, t - dt, dt, sequence.duration), velocity, dt
    else:
        v_a = _velocities_m_s_at(sequence, t - dt, dt, sequence.duration)
        v_b = _velocities_m_s_at(sequence, t + dt, dt, sequence.duration)
        denom = 2 * dt
    acceleration = {pid: ((v_b[pid][0] - v_a[pid][0]) / denom, (v_b[pid][1] - v_a[pid][1]) / denom) for pid in v_a}
    return velocity, acceleration


def player_states_and_ball_at(sequence: Sequence, t: float) -> tuple[list[PlayerState], DynamicBallState]:
    """Reformate `interpolate(sequence, t)` (INCHANGÉ, voir docstring de
    module) en `(list[PlayerState], DynamicBallState)` -- les positions x/y
    restent exactement celles d'`interpolate`, converties de normalisé
    (0-1) en mètres par une simple mise à l'échelle (`* PITCH_LENGTH_M`/
    `* PITCH_WIDTH_M`, réversible, sans arrondi au-delà de la précision
    flottante habituelle) -- jamais une nouvelle interpolation.

    `velocity`/`acceleration` (Tâche 3, 24/09/2026) sont des dérivées
    numériques de CES positions (voir `_velocities_and_accelerations_m_s`),
    distinctes de la vitesse `PlayerMotionState.vx/vy` déjà calculée en
    interne par `interpolate` (autre pas `dt`, autre usage -- direction du
    corps/`current_action` ci-dessous, INCHANGÉS depuis le brief précédent,
    continuent d'utiliser `PlayerMotionState.vx/vy` telle quelle)."""
    frame = interpolate(sequence, t)
    velocities, accelerations = _velocities_and_accelerations_m_s(sequence, t)

    player_states = []
    for player_id, motion_state in frame.players.items():
        entry = sequence.roster[player_id]
        vx_m_s = motion_state.vx * PITCH_LENGTH_M
        vy_m_s = motion_state.vy * PITCH_WIDTH_M
        speed_m_s = math.hypot(vx_m_s, vy_m_s)
        player_states.append(PlayerState(
            player_id=str(player_id),
            team=entry.team_side,
            position=(motion_state.x * PITCH_LENGTH_M, motion_state.y * PITCH_WIDTH_M),
            direction_body=math.atan2(vy_m_s, vx_m_s),
            current_action="sprint" if speed_m_s > _SPRINT_THRESHOLD_M_S else "idle",
            target=_final_target_m(sequence, player_id),
            velocity=velocities[player_id],
            acceleration=accelerations[player_id],
        ))

    ball = frame.ball
    ball_state = DynamicBallState(
        position=(ball.x * PITCH_LENGTH_M, ball.y * PITCH_WIDTH_M, ball.z),
        velocity=(ball.vx * PITCH_LENGTH_M, ball.vy * PITCH_WIDTH_M, ball.vz),
        possession=None if ball.owner_id is None else str(ball.owner_id),
    )
    return player_states, ball_state

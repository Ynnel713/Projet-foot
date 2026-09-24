"""État dynamique d'un joueur ou du ballon à un instant donné. Les champs de
vitesse et d'accélération pour les joueurs seront ajoutés dans un brief
ultérieur (étape 4 du PDF). Les positions restent calculées par
interpolation des keyframes de gabarit dans ce brief -- c'est une migration
pure.

Pont ADDITIF au-dessus de `animation.motion.interpolate` (brief "introduce
PlayerState and BallState", 24/09/2026, préparation étape 2 du PDF) --
`interpolate` n'est PAS modifié : `player_states_and_ball_at` l'appelle tel
quel puis reformate son résultat déjà calculé (`FrameState`) en
`(list[PlayerState], BallState)`, sans jamais recalculer une position. C'est
le choix retenu pour garantir mécaniquement "aucune modification visuelle"
(voir retour de brief) -- le contrat existant d'`interpolate`, déjà couvert
par tests/test_motion.py, reste physiquement intact.

Deux substitutions documentées, faute de donnée plus précise dans le modèle
actuel (`Sequence`/`RosterEntry` ne portent ni home/away, ni classification
d'action) :

- `PlayerState.team` porte `RosterEntry.team_side` ("scorer"/"opponent",
  déjà existant) plutôt que "home"/"away" à la lettre du brief -- `Sequence`
  ne connaît jamais le nom des clubs ni qui est domicile/extérieur (voir
  `RosterEntry`, `animation.types`), seulement quelle équipe a marqué. Une
  vraie conversion "home"/"away" nécessiterait de faire remonter cette
  information depuis `Timeline`/`Lineup` jusqu'à `Sequence`, un changement
  de contrat hors périmètre d'une migration pure.
- `PlayerState.current_action` ne distingue que `"idle"`/`"sprint"` (seuil
  de vitesse, voir `_SPRINT_THRESHOLD_M_S`) -- `"pass"`/`"shoot"` (cités en
  exemple par le brief) exigeraient de lire les tags narratifs du gabarit
  (`Keyframe.tag`/`physics_tag`), une vraie classification d'action hors
  périmètre de cette migration structurelle."""

from __future__ import annotations

import math
from dataclasses import dataclass

from ligue1sim.animation.motion import interpolate
from ligue1sim.animation.types import PlayerId, Sequence
from ligue1sim.pitch_geometry import PITCH_LENGTH_M, PITCH_WIDTH_M

_SPRINT_THRESHOLD_M_S = 3.0  # au-dessus : "sprint", en-deca : "idle" -- voir docstring de module


@dataclass(frozen=True)
class PlayerState:
    player_id: str
    team: str  # "scorer" / "opponent" -- voir docstring de module
    position: tuple[float, float]  # x, y en metres
    direction_body: float  # radians, 0 = vers la droite (atan2(vy_m, vx_m))
    current_action: str  # "idle" | "sprint" -- voir docstring de module
    target: tuple[float, float] | None  # x, y en metres, destination finale de ce joueur sur ce clip


@dataclass(frozen=True)
class BallState:
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


def player_states_and_ball_at(sequence: Sequence, t: float) -> tuple[list[PlayerState], BallState]:
    """Reformate `interpolate(sequence, t)` (INCHANGÉ, voir docstring de
    module) en `(list[PlayerState], BallState)` -- les positions x/y restent
    exactement celles d'`interpolate`, converties de normalisé (0-1) en
    mètres par une simple mise à l'échelle (`* PITCH_LENGTH_M`/
    `* PITCH_WIDTH_M`, réversible, sans arrondi au-delà de la précision
    flottante habituelle) -- jamais une nouvelle interpolation."""
    frame = interpolate(sequence, t)

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
        ))

    ball = frame.ball
    ball_state = BallState(
        position=(ball.x * PITCH_LENGTH_M, ball.y * PITCH_WIDTH_M, ball.z),
        velocity=(ball.vx * PITCH_LENGTH_M, ball.vy * PITCH_WIDTH_M, ball.vz),
        possession=None if ball.owner_id is None else str(ball.owner_id),
    )
    return player_states, ball_state

"""Type de réception (ticket v2-realisme/07c) : de face, de profil ou dos au jeu, selon le cap du receveur (07a) et la
direction du but adverse ; cap « ouvert » que vise le receveur d'une passe en vol. Tracé, sans effet sur le jeu avant
le temps de contrôle selon l'orientation (07d).

Constantes recommandées et validées par délégation du propriétaire (12/11/2026) ; données réelles non trouvées
(découpage géométrique en trois secteurs égaux) :
- `FACE_MAX_DEG` : de face si le corps est tourné à 60° au plus du but adverse ;
- `BACK_MIN_DEG` : dos au jeu au-delà de 120° ; de profil entre les deux ;
- `OPEN_CONE_DEG` : le receveur garde le ballon dans son demi-plan avant (90° de part et d'autre de son cap) ; il se
  tourne vers la direction la plus proche du but adverse qui le permet.
"""

from __future__ import annotations

import math

from v2engine.geometry import PITCH_LENGTH_M, PITCH_WIDTH_M, Vec2

DE_FACE, DE_PROFIL, DOS_AU_JEU = "de face", "de profil", "dos au jeu"
FACE_MAX_DEG = 60.0
BACK_MIN_DEG = 120.0
OPEN_CONE_DEG = 90.0


def attacking_goal(team: str) -> Vec2:
    """Centre du but que `team` attaque (`home` attaque vers x = longueur du terrain, comme `geometry.in_penalty_area`)."""
    return Vec2(PITCH_LENGTH_M if team == "home" else 0.0, PITCH_WIDTH_M / 2.0)


def _angle_deg(a: Vec2, b: Vec2) -> float:
    """Angle non orienté entre deux directions, en degrés (0 à 180)."""
    la, lb = a.length(), b.length()
    if la < 1e-9 or lb < 1e-9:
        return 0.0
    cosine = (a.x * b.x + a.y * b.y) / (la * lb)
    return math.degrees(math.acos(max(-1.0, min(1.0, cosine))))


def facing_to_goal_deg(facing: Vec2, position: Vec2, team: str) -> float:
    """Angle entre le cap du joueur et la direction du but adverse."""
    return _angle_deg(facing, attacking_goal(team) - position)


def reception_type(facing: Vec2, position: Vec2, team: str) -> str:
    """De face, de profil ou dos au jeu, selon l'angle entre le cap et le but adverse."""
    angle = facing_to_goal_deg(facing, position, team)
    return DE_FACE if angle <= FACE_MAX_DEG else DOS_AU_JEU if angle > BACK_MIN_DEG else DE_PROFIL


def open_facing(position: Vec2, ball_position: Vec2, team: str, current: Vec2) -> Vec2:
    """Cap visé par le receveur d'une passe en vol : la direction la plus proche du but adverse qui garde le ballon à
    `OPEN_CONE_DEG` au plus de son cap. Ballon pile à l'opposé du but : il s'ouvre du côté où son cap est déjà tourné."""
    to_goal = attacking_goal(team) - position
    to_ball = ball_position - position
    if to_ball.length() < 1e-9 or to_goal.length() < 1e-9:
        return current
    ball_a, goal_a = math.atan2(to_ball.y, to_ball.x), math.atan2(to_goal.y, to_goal.x)
    delta = (goal_a - ball_a + math.pi) % (2.0 * math.pi) - math.pi  # du ballon vers le but, par le plus court
    cone = math.radians(OPEN_CONE_DEG)
    if abs(delta) <= cone:
        return to_goal.normalized()
    side = math.copysign(1.0, delta)
    if abs(abs(delta) - math.pi) < 1e-6:  # but pile derrière le ballon : côté de son cap actuel
        cross = to_ball.x * current.y - to_ball.y * current.x
        side = 1.0 if cross >= 0.0 else -1.0
    angle = ball_a + side * cone
    return Vec2(math.cos(angle), math.sin(angle))

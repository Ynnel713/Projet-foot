"""Orientation du corps d'un joueur (ticket v2-realisme/07a) : un cap, direction vers laquelle il fait face, distinct
de sa vitesse. Le cap tourne vers une direction voulue à une vitesse angulaire maximale qui dépend d'Agility (ticket
07f) ; il ne pèse encore sur rien (déplacement selon l'orientation : 07b ; contrôle orienté : 07c ; perception : 08a).

Angles en radians, dans le repère du terrain : 0 = vers x croissant (le but que `home` attaque), π/2 = vers y
croissant."""

from __future__ import annotations

import math

from v2engine.attributes import success_probability
from v2engine.condition import effective_rating
from v2engine.geometry import Vec2

# Vitesse de rotation maximale du corps d'un joueur moyen : 360°/s, soit un demi-tour en 0,5 s (environ deux appuis).
# Valeur réelle non trouvée (vitesse de rotation du bassin ou du tronc sur un demi-tour) ; ordre de grandeur proposé et
# validé par le propriétaire le 12/11/2026 (ticket 07a).
TURN_RATE_RAD_S = math.radians(360.0)
# Selon Agility (ticket 07f, validé le 12/11/2026), courbe partagée de `attributes` : 99 -> 450°/s (demi-tour en 0,40 s),
# 55 -> 360°/s, 11 -> 270°/s (0,67 s) ; ± 25 % comme les autres capacités physiques (Acceleration, vitesse balle au pied).
# Valeur réelle non trouvée.
_TURN_RATE_DEG_S = (360.0, 90.0, 270.0, 450.0)  # baseline, amplitude, min, max
# Au-dessus de 19,8 km/h (seuil de course à haute intensité du banc), le joueur regarde où il court ; en dessous, il
# regarde le ballon (validé par le propriétaire le 12/11/2026).
FAST_RUN_MPS = 19.8 / 3.6
# En deçà de cette distance, la direction du ballon n'a pas de sens (ballon dans ses pieds) : il garde son cap.
BALL_DEADZONE_M = 0.1
# Type de réception (ticket 07c, validé le 12/11/2026) selon l'angle entre le cap du receveur et la direction du but
# adverse : de face sous 60°, de profil (ouvert) de 60 à 120°, dos au jeu au-delà. Trois secteurs égaux ; valeur réelle
# non trouvée.
FACE, PROFIL, DOS = "de face", "de profil", "dos au jeu"
FACE_MAX_DEG = 60.0
BACK_MIN_DEG = 120.0


def turn_rate_rad_s(player) -> float:
    """Vitesse de rotation maximale du corps de `player` (rad/s), selon Agility (façade `condition.effective_rating`)."""
    baseline, amplitude, low, high = _TURN_RATE_DEG_S
    return math.radians(success_probability(effective_rating(player, "Agility"), baseline=baseline, amplitude=amplitude,
                                            min_prob=low, max_prob=high))


def kickoff_facing(team: str) -> float:
    """Cap au coup d'envoi et à la reprise : face au but adverse (`home` attaque vers x croissant)."""
    return 0.0 if team == "home" else math.pi


def wrap(angle: float) -> float:
    """Ramène un angle dans ]−π, π]."""
    wrapped = math.remainder(angle, math.tau)
    return math.pi if wrapped == -math.pi else wrapped


def desired_facing(position: Vec2, velocity: Vec2, ball: Vec2, current: float, holding: bool = False,
                   goal: Vec2 | None = None) -> float:
    """Direction voulue : celle de la course au-dessus de `FAST_RUN_MPS`, sinon celle du ballon ; `current` si le
    ballon est sur lui. Le porteur (`holding`) a le ballon dans ses pieds : il regarde où il va, et garde son cap
    à l'arrêt (le ballon du moteur est recopié sur sa position du pas précédent, sa direction serait l'inverse de sa
    course ; réserve A1 de l'expert, 12/11/2026). Le receveur visé d'une passe en vol (`goal` : le but qu'il attaque)
    s'ouvre : il vise la direction à mi-chemin entre le ballon et ce but, pour voir les deux (ticket 07c) ; il n'y
    arrive avant le ballon que s'il en a le temps (rotation bornée, Agility)."""
    if holding:
        return math.atan2(velocity.y, velocity.x) if velocity.length() > 0.0 else current
    if velocity.length() >= FAST_RUN_MPS:
        return math.atan2(velocity.y, velocity.x)
    to_ball = ball - position
    if to_ball.length() <= BALL_DEADZONE_M:
        return current
    if goal is not None:
        return _open_body(to_ball, goal - position, current)
    return math.atan2(to_ball.y, to_ball.x)


def _open_body(to_ball: Vec2, to_goal: Vec2, current: float) -> float:
    """Direction à mi-chemin entre le ballon et le but (bissectrice). Ballon exactement à l'opposé du but : la
    perpendiculaire au but la plus proche de son cap actuel (choix sans tirage)."""
    if to_goal.length() < 1e-9:
        return math.atan2(to_ball.y, to_ball.x)
    middle = to_ball.normalized() + to_goal.normalized()
    if middle.length() > 1e-6:
        return math.atan2(middle.y, middle.x)
    goal_angle = math.atan2(to_goal.y, to_goal.x)
    return min((goal_angle + math.pi / 2, goal_angle - math.pi / 2), key=lambda a: abs(wrap(a - current)))


def reception_type(facing: float, position: Vec2, goal: Vec2) -> str:
    """Type de réception (ticket 07c) : de face, de profil ou dos au jeu, selon l'angle entre le cap et le but adverse."""
    to_goal = goal - position
    angle = abs(math.degrees(wrap(facing - math.atan2(to_goal.y, to_goal.x))))
    return FACE if angle < FACE_MAX_DEG else DOS if angle > BACK_MIN_DEG else PROFIL


def turn_towards(current: float, desired: float, dt: float, rate: float = TURN_RATE_RAD_S) -> float:
    """Cap après `dt` secondes : tourne vers `desired` par le plus court chemin, au plus de `rate`·`dt`."""
    delta = wrap(desired - current)
    limit = rate * dt
    return wrap(current + max(-limit, min(limit, delta)))

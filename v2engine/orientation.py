"""Orientation du corps d'un joueur (ticket v2-realisme/07a) : un cap, direction vers laquelle il fait face, distinct
de sa vitesse. Le cap tourne vers une direction voulue à une vitesse angulaire maximale commune à tous ; il ne pèse
encore sur rien (déplacement selon l'orientation : 07b ; Agility : 07f ; contrôle orienté : 07c ; perception : 08a).

Angles en radians, dans le repère du terrain : 0 = vers x croissant (le but que `home` attaque), π/2 = vers y
croissant."""

from __future__ import annotations

import math

from v2engine.geometry import Vec2

# Vitesse de rotation maximale du corps, la même pour tous en attendant Agility (07f) : 360°/s, soit un demi-tour en
# 0,5 s (environ deux appuis). Valeur réelle non trouvée (vitesse de rotation du bassin ou du tronc sur un demi-tour) ;
# ordre de grandeur proposé et validé par le propriétaire le 12/11/2026.
TURN_RATE_RAD_S = math.radians(360.0)
# Au-dessus de 19,8 km/h (seuil de course à haute intensité du banc), le joueur regarde où il court ; en dessous, il
# regarde le ballon (validé par le propriétaire le 12/11/2026).
FAST_RUN_MPS = 19.8 / 3.6
# En deçà de cette distance, la direction du ballon n'a pas de sens (ballon dans ses pieds) : il garde son cap.
BALL_DEADZONE_M = 0.1


def kickoff_facing(team: str) -> float:
    """Cap au coup d'envoi et à la reprise : face au but adverse (`home` attaque vers x croissant)."""
    return 0.0 if team == "home" else math.pi


def wrap(angle: float) -> float:
    """Ramène un angle dans ]−π, π]."""
    wrapped = math.remainder(angle, math.tau)
    return math.pi if wrapped == -math.pi else wrapped


def desired_facing(position: Vec2, velocity: Vec2, ball: Vec2, current: float, holding: bool = False) -> float:
    """Direction voulue : celle de la course au-dessus de `FAST_RUN_MPS`, sinon celle du ballon ; `current` si le
    ballon est sur lui. Le porteur (`holding`) a le ballon dans ses pieds : il regarde où il va, et garde son cap
    à l'arrêt (le ballon du moteur est recopié sur sa position du pas précédent, sa direction serait l'inverse de sa
    course ; réserve A1 de l'expert, 12/11/2026)."""
    if holding:
        return math.atan2(velocity.y, velocity.x) if velocity.length() > 0.0 else current
    if velocity.length() >= FAST_RUN_MPS:
        return math.atan2(velocity.y, velocity.x)
    to_ball = ball - position
    if to_ball.length() <= BALL_DEADZONE_M:
        return current
    return math.atan2(to_ball.y, to_ball.x)


def turn_towards(current: float, desired: float, dt: float, rate: float = TURN_RATE_RAD_S) -> float:
    """Cap après `dt` secondes : tourne vers `desired` par le plus court chemin, au plus de `rate`·`dt`."""
    delta = wrap(desired - current)
    limit = rate * dt
    return wrap(current + max(-limit, min(limit, delta)))

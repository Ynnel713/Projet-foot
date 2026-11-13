"""Champ de vision (ticket v2-realisme/08a) : chaque joueur voit les joueurs situés dans un cône autour de son cap
(`PlayerState.facing`, 07a) ; les autres ne sont pas vus à cet instant. Calculé et tracé, sans effet sur le jeu dans ce
ticket (mémoire : 08b ; décisions sur le monde perçu : 08d ; rotations de tête : scan, 08c).

Constante validée par le propriétaire (13/11/2026, « Ok 100° ») : `FIELD_OF_VIEW_HALF_DEG`, 100° de part et d'autre du
cap, soit 200° au total. Réel : champ visuel horizontal humain d'environ 200° (sources courantes) à 214° (± 107°,
Strasburger et al. 2011, Journal of Vision, corrigé en 2024) ; l'extrême périphérie détecte mal un joueur, d'où 100°.
Le cap est celui du corps : la tête qui tourne (scan) élargira ce champ au 08c.
"""

from __future__ import annotations

import math

from v2engine.geometry import Vec2
from v2engine.movement import PlayerState

FIELD_OF_VIEW_HALF_DEG = 100.0
_COS_HALF = math.cos(math.radians(FIELD_OF_VIEW_HALF_DEG))


def sees(observer: PlayerState, point: Vec2) -> bool:
    """Vrai si `point` est dans le champ de vision de `observer` (cône de ± `FIELD_OF_VIEW_HALF_DEG` autour de son cap).
    Un point confondu avec lui est vu."""
    dx, dy = point.x - observer.position.x, point.y - observer.position.y
    distance = math.hypot(dx, dy)
    if distance < 1e-9:
        return True
    return (observer.facing.x * dx + observer.facing.y * dy) / distance >= _COS_HALF


def unseen(observer: PlayerState, players: list[PlayerState], within_m: float | None = None) -> list[PlayerState]:
    """Joueurs de `players` (lui exclu) hors de son champ de vision ; seulement ceux à `within_m` au plus si donné."""
    return [p for p in players if p.name != observer.name and not sees(observer, p.position)
            and (within_m is None or observer.position.distance_to(p.position) <= within_m)]

"""Évitement entre coéquipiers (ticket v2-realisme/11f) : conscience spatiale de base. Avant de se déplacer, le joueur
regarde devant lui, le long de sa course voulue, sur un court horizon ; si un coéquipier occupe ce couloir, il infléchit
sa course (35° au plus) ou, à défaut, ralentit. Les adversaires ne sont pas évités (le contact avec eux est un duel :
tickets 11b, 11c, tacle). Le porteur du ballon n'évite personne : les autres l'évitent (priorité au porteur) ; de même
le joueur prioritaire sur le ballon (receveur visé, gardien qui sort, coéquipier désigné sur un ballon libre : réserve A1
de l'expert, correction décidée par le propriétaire le 15/11/2026), désigné par l'appelant (`priority`). Le côté
choisi est tenu au moins `AVOID_SIDE_HOLD_S` (hystérésis contre l'effet miroir et les saccades).

Constantes validées par le propriétaire le 15/11/2026 (« Je valide entièrement les valeurs pour 11f ») : horizon 0,8 s,
couloir à la somme des rayons + 0,3 m, inflexion 35° au plus, freinage limité à 50 % de l'intensité voulue, tous les
coéquipiers évités sans attribut, priorité au porteur, côté tenu 0,2 s. Chiffre réel : non trouvé."""

from __future__ import annotations

import math
from dataclasses import dataclass

from v2engine.geometry import Vec2
from v2engine.movement import PlayerState

AVOID_HORIZON_S = 0.8  # regard porté devant soi, en temps de course
AVOID_MARGIN_M = 0.3  # couloir : somme des rayons + cette marge
AVOID_MAX_DEFLECTION_DEG = 35.0  # inflexion maximale par rapport à la course voulue
AVOID_MAX_BRAKE = 0.5  # l'intensité ne descend pas sous 50 % de l'intensité voulue
AVOID_SIDE_HOLD_S = 0.2  # côté d'évitement tenu au moins 0,2 s
_DEFLECTION_STEP_DEG = 5.0  # résolution de la recherche du cap libre (5°, 10°, ..., 35°) ; détail de calcul
LEFT, RIGHT = 1, -1  # côté d'inflexion : à gauche (sens trigonométrique) ou à droite de la course voulue


@dataclass(frozen=True)
class Avoidance:
    target: Vec2  # cible à donner à `movement.step`
    target_velocity: Vec2  # vitesse de la cible (pressing), infléchie du même angle que la course
    intensity: float  # part de la vitesse max à donner à `movement.step`
    side: int  # côté retenu (LEFT, RIGHT), 0 sans inflexion
    side_until_s: float  # jusqu'à quand ce côté est tenu


def _rotate(v: Vec2, angle_rad: float) -> Vec2:
    c, s = math.cos(angle_rad), math.sin(angle_rad)
    return Vec2(v.x * c - v.y * s, v.x * s + v.y * c)


def _blocks(player: PlayerState, dx: float, dy: float, speed: float, mate: PlayerState) -> bool:
    """`mate` passe-t-il dans le couloir de `player` courant selon (`dx`, `dy`) (unitaire) à `speed`, dans l'horizon ?
    Plus courte distance entre les deux, mouvement relatif rectiligne sur `AVOID_HORIZON_S` (calcul en flottants : chemin
    chaud, 22 joueurs par pas)."""
    corridor = player.radius_m + mate.radius_m + AVOID_MARGIN_M
    rx, ry = mate.position.x - player.position.x, mate.position.y - player.position.y
    wx, wy = dx * speed - mate.velocity.x, dy * speed - mate.velocity.y  # vitesse de `player` relative à `mate`
    ww = wx * wx + wy * wy
    if ww < 1e-12:
        return False
    t = (rx * wx + ry * wy) / ww
    if t <= 0.0:
        return False
    t = min(AVOID_HORIZON_S, t)
    gx, gy = rx - wx * t, ry - wy * t
    return gx * gx + gy * gy < corridor * corridor


def _near(player: PlayerState, speed: float, mates: list[PlayerState]) -> list[PlayerState]:
    """Coéquipiers assez proches pour entrer dans le couloir dans l'horizon, quelle que soit la direction."""
    px, py = player.position.x, player.position.y
    out = []
    for m in mates:
        reach = (speed + math.hypot(m.velocity.x, m.velocity.y)) * AVOID_HORIZON_S + player.radius_m + m.radius_m \
            + AVOID_MARGIN_M
        ex, ey = m.position.x - px, m.position.y - py
        if ex * ex + ey * ey <= reach * reach:
            out.append(m)
    return out


def conflicts(player: PlayerState, direction: Vec2, speed: float, mates: list[PlayerState]) -> list[PlayerState]:
    """Coéquipiers qui bloquent la course de `player` selon `direction` (unitaire) à `speed`."""
    return [m for m in _near(player, speed, mates) if _blocks(player, direction.x, direction.y, speed, m)]


def avoid_teammates(player: PlayerState, target: Vec2, intensity: float, players: list[PlayerState],
                    holder: str | None, now_s: float, side: int = 0, side_until_s: float = 0.0,
                    target_velocity: Vec2 = Vec2(0.0, 0.0), priority: bool = False) -> Avoidance:
    """Cible, vitesse de cible et intensité de `player` après évitement de ses coéquipiers. `side`, `side_until_s` : côté
    retenu au pas précédent et sa fin. `target_velocity` : vitesse de la cible quand elle bouge (pressing) ; `step`
    l'ajoute à la course, elle est donc infléchie du même angle. Sans coéquipier dans le couloir, tout est rendu tel
    quel. `priority` : joueur prioritaire sur le ballon (receveur, gardien qui sort, désigné sur ballon libre), qui
    n'évite personne, comme le porteur ; les autres l'évitent."""
    keep = Avoidance(target, target_velocity, intensity, side if now_s < side_until_s else 0, side_until_s)
    if priority or player.name == holder:
        return keep  # priorité au porteur et au joueur qui va au ballon : il n'évite pas, les autres l'évitent
    to_target = target - player.position
    distance = to_target.length()
    speed = player.velocity.length()
    if distance < 1e-6 or speed < 1e-6:
        return keep
    direction = to_target * (1.0 / distance)
    mates = _near(player, speed, [p for p in players if p.team == player.team and p.name != player.name])
    if not mates:
        return keep
    blocking = [m for m in mates if _blocks(player, direction.x, direction.y, speed, m)]
    if not blocking:
        return keep
    held = side if now_s < side_until_s and side in (LEFT, RIGHT) else 0
    if held:
        sides = (held,)
    else:  # s'écarter du côté opposé au coéquipier le plus proche ; pile en face : à droite (pas d'effet miroir)
        nearest = min(blocking, key=lambda m: m.position.distance_to(player.position))
        r = nearest.position - player.position
        cross = direction.x * r.y - direction.y * r.x  # > 0 : coéquipier à gauche de la course
        first = RIGHT if cross >= -1e-9 * max(1.0, r.length()) else LEFT
        sides = (first, -first)
    steps = int(round(AVOID_MAX_DEFLECTION_DEG / _DEFLECTION_STEP_DEG))
    for chosen in sides:
        for k in range(1, steps + 1):
            candidate = _rotate(direction, chosen * math.radians(k * _DEFLECTION_STEP_DEG))
            if not any(_blocks(player, candidate.x, candidate.y, speed, m) for m in mates):
                turn = chosen * math.radians(k * _DEFLECTION_STEP_DEG)
                return Avoidance(player.position + candidate * distance, _rotate(target_velocity, turn), intensity,
                                 chosen, now_s + AVOID_SIDE_HOLD_S)
    # aucun cap libre à 35° ou moins : il ralentit à la vitesse du coéquipier le long de sa course, 50 % au plus.
    # L'intensité est une part de sa vitesse max : la ramener dans le rapport (vitesse du coéquipier / sa vitesse)
    # vise la vitesse du coéquipier sans lire de note (aucun attribut, règle R1).
    nearest = min(blocking, key=lambda m: m.position.distance_to(player.position))
    along = max(0.0, nearest.velocity.x * direction.x + nearest.velocity.y * direction.y)
    wanted = intensity * along / speed
    return Avoidance(target, target_velocity, max(intensity * (1.0 - AVOID_MAX_BRAKE), min(intensity, wanted)), keep.side,
                     side_until_s)

"""Temps additionnel (ticket v2-coach-et-gestion-de-match/03).

Loi 7 et directive IFAB 2023 : l'arbitre rattrape le temps réellement perdu (célébrations, remplacements, blessures,
sanctions, VAR, penalties), pas les touches, sorties de but, corners ni coups francs ordinaires, qui font partie du jeu
(leur ballon mort s'écoule déjà dans l'horloge, `restart.DEAD_S`).

Constantes validées le 04/11/2026 par délégation du propriétaire (sources dans le ticket) :
- `GOAL_LOST_S`, `PENALTY_LOST_S` : temps perdu par but et par penalty ;
- `BACKGROUND_S` : fond par période pour les causes que le moteur ne joue pas encore (blessures, VAR, cartons, et
  remplacements en 2e période jusqu'au ticket 05a), tiré uniformément, proportionnel à la durée de la période ;
- `GRACE_S` : un coup de pied arrêté accordé à la fin est joué, l'action va à son terme 30 s au plus ;
- `HARD_STOP_S` : butoir après la fin annoncée.

Tirage : sha256 d'une clé stable, pour ne pas consommer le flux `random` du match (D-V06 reste vrai : même graine,
mêmes événements, même clé, même temps additionnel)."""

from __future__ import annotations

import hashlib
import random

GOAL_LOST_S = 60.0
PENALTY_LOST_S = 60.0
BACKGROUND_S = {1: (60.0, 150.0), 2: (180.0, 330.0)}
GRACE_S = 30.0
HARD_STOP_S = 180.0
_REGULAR_HALF_MIN = 45.0


def added_minutes(period: int, half_minutes: float, goals: int, penalties: int, key: str,
                  fouls: int = 0, restarts: int = 0) -> int:
    """Minutes annoncées par le 4e arbitre à la fin de la période `period` (1 ou 2) d'une durée réglementaire de
    `half_minutes`. `key` identifie le match (équipes) ; les événements de la période complètent la clé : `fouls` et
    `restarts` (fautes et remises en jeu de la période) n'ajoutent pas de temps, ils font varier le fond d'un rejeu
    à l'autre de la même affiche (réserve A1 de l'expert, 04/11/2026)."""
    seed = hashlib.sha256(f"{key}|{period}|{goals}|{penalties}|{fouls}|{restarts}".encode()).digest()
    low, high = BACKGROUND_S[period]
    background = random.Random(int.from_bytes(seed[:8], "big")).uniform(low, high) * half_minutes / _REGULAR_HALF_MIN
    return round((background + goals * GOAL_LOST_S + penalties * PENALTY_LOST_S) / 60.0)


def played_minute(minute: float, second_half_start: float | None, half_minutes: float) -> float:
    """Temps de jeu pour la fatigue : l'horloge du moteur, moins en 2e période le temps additionnel de la 1re (la
    fatigue est calée sur 90 min, `movement.MATCH_END_MINUTE`)."""
    if second_half_start is None or minute < second_half_start:
        return minute
    return half_minutes + minute - second_half_start


def display_minute(minute: float, second_half_start: float | None, half_minutes: float = _REGULAR_HALF_MIN) -> str:
    """Minute affichée d'un instant de la trace : `12'`, `45+2'`, `67'`, `90+4'`. `minute` est l'horloge du moteur
    (continue, temps additionnel compris) ; `second_half_start` la minute moteur du coup d'envoi de la 2e période."""
    if second_half_start is None or minute < second_half_start:
        elapsed, base = minute, 0.0
    else:
        elapsed, base = minute - second_half_start, half_minutes
    if elapsed < half_minutes:
        return f"{int(base + elapsed)}'"
    return f"{int(base + half_minutes)}+{int(elapsed - half_minutes) + 1}'"

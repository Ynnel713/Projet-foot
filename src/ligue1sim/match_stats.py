"""Statistiques de match (possession, tirs, tirs cadrés, xG) -- demande du
29/09/2026 ("un volet stats avec la possession... mais aussi tirs, tirs
cadrés, XG").

Le moteur ne simule PAS d'actions individuelles : comme le reste du jeu
(buteurs/passeurs dans events.py, mise en scène dans animation/), ces stats
sont fabriquées APRÈS COUP à partir de ce qui est déjà décidé -- ici le score
final et le lambda (buts attendus) déjà calculé par simulation._draw_score --
plutôt que par une reconstruction indépendante qui risquerait de raconter une
autre histoire que le score réel.

Cohérence garantie : le xG affiché est centré sur le lambda RÉEL de l'équipe
(donc aligné avec ses buts attendus), et les tirs cadrés ne descendent jamais
sous le nombre de buts marqués (un but est par définition un tir cadré)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# --- Possession ------------------------------------------------------------
#
# Dérivée de l'écart de note entre les deux compos du jour (même signal que
# le proxy "qui a l'ascendant" utilisé par le style Contre-attaque, voir
# simulation._draw_score) et du style "Possession" du coach, s'il est coché.
# Volontairement borné assez large (35-65%) : la possession réelle varie
# beaucoup même entre équipes de niveaux proches.
_POSSESSION_BASE = 50.0
_POSSESSION_RATING_SENSITIVITY = 220.0  # points de possession par unité d'écart relatif de note
_POSSESSION_STYLE_BONUS = 4.0  # points de possession pour le style "Possession"
_POSSESSION_NOISE_STD = 3.0
_POSSESSION_BOUNDS = (35.0, 65.0)

# --- Tirs / tirs cadrés / xG -------------------------------------------------
#
# Repères réalistes (football pro, ordre de grandeur) : ~0.10-0.12 xG par
# tir tous types confondus, ~35-40% des tirs cadrés.
_AVG_XG_PER_SHOT = 0.11
_SHOT_ON_TARGET_RATIO = 0.37
_XG_LOG_NOISE_HALF_WIDTH = 0.25  # bruit multiplicatif sur le xG (voir simulation._blend_lambda, même idiome)
_SHOT_COUNT_NOISE_STD = 0.15  # bruit multiplicatif sur le nombre de tirs déduit du xG
_MIN_SHOTS = 3
_MAX_SHOTS = 28


@dataclass(frozen=True)
class TeamMatchStats:
    possession: float  # 0-100, home+away == 100
    shots: int
    shots_on_target: int
    xg: float


@dataclass(frozen=True)
class MatchStats:
    home: TeamMatchStats
    away: TeamMatchStats


def _possession_split(home_rating: float, away_rating: float, home_style_possession: bool, away_style_possession: bool) -> tuple[float, float]:
    avg_rating = (home_rating + away_rating) / 2 or 1.0
    relative_gap = (home_rating - away_rating) / avg_rating
    home_possession = _POSSESSION_BASE + _POSSESSION_RATING_SENSITIVITY * relative_gap
    if home_style_possession:
        home_possession += _POSSESSION_STYLE_BONUS
    if away_style_possession:
        home_possession -= _POSSESSION_STYLE_BONUS
    home_possession += np.random.normal(0.0, _POSSESSION_NOISE_STD)
    home_possession = min(_POSSESSION_BOUNDS[1], max(_POSSESSION_BOUNDS[0], home_possession))
    return round(home_possession, 1), round(100.0 - home_possession, 1)


def _team_shots_stats(lam: float, goals: int) -> tuple[int, int, float]:
    """(tirs, tirs cadrés, xG) pour une équipe dont le lambda (buts attendus,
    déjà calculé par simulation._draw_score) est `lam` et qui a marqué
    `goals` buts réels."""
    xg = max(0.3, lam * float(np.exp(np.random.uniform(-_XG_LOG_NOISE_HALF_WIDTH, _XG_LOG_NOISE_HALF_WIDTH))))

    raw_shots = xg / _AVG_XG_PER_SHOT
    shots = round(raw_shots * float(np.exp(np.random.normal(0.0, _SHOT_COUNT_NOISE_STD))))
    shots = min(_MAX_SHOTS, max(_MIN_SHOTS, shots))

    shots_on_target = round(shots * _SHOT_ON_TARGET_RATIO * float(np.exp(np.random.normal(0.0, _SHOT_COUNT_NOISE_STD))))
    shots_on_target = max(goals, min(shots_on_target, shots))  # un but est toujours un tir cadré
    shots = max(shots, shots_on_target)  # ne jamais avoir moins de tirs que de tirs cadrés

    return shots, shots_on_target, round(xg, 2)


def compute_match_stats(
    home_lambda: float,
    away_lambda: float,
    home_rating: float,
    away_rating: float,
    home_goals: int,
    away_goals: int,
    home_styles: frozenset[str] = frozenset(),
    away_styles: frozenset[str] = frozenset(),
) -> MatchStats:
    """Statistiques de match complètes, dérivées du lambda et du score déjà
    décidés par `simulation._draw_score` -- jamais l'inverse (voir docstring
    du module)."""
    home_possession, away_possession = _possession_split(
        home_rating, away_rating, "Possession" in home_styles, "Possession" in away_styles
    )
    home_shots, home_shots_on_target, home_xg = _team_shots_stats(home_lambda, home_goals)
    away_shots, away_shots_on_target, away_xg = _team_shots_stats(away_lambda, away_goals)

    return MatchStats(
        home=TeamMatchStats(home_possession, home_shots, home_shots_on_target, home_xg),
        away=TeamMatchStats(away_possession, away_shots, away_shots_on_target, away_xg),
    )

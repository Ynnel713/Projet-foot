"""Moteur de simulation des matchs : loi de Poisson pondérée par les ratings.

Le lambda (buts attendus) de chaque équipe est calibré sur la moyenne de la
ligue chargée (voir LeagueContext), donc ce module fonctionne pour n'importe
quel championnat, pas seulement la Ligue 1.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ligue1sim.clubs import Club
from ligue1sim.schedule import Journee

LEAGUE_AVG_GOALS = 1.14  # buts moyens attendus par équipe et par match (recalibré pour RATING_EXPONENT=1.8)
HOME_ADVANTAGE = 1.10  # bonus de 10% sur le lambda de l'équipe à domicile
MAX_GOALS = 6  # plafond réaliste de buts par équipe et par match

# Exposant appliqué aux écarts de rating (attaque/défense). À 1.0, l'écart
# entre le meilleur et le pire club ne suffit pas à empêcher des saisons
# aberrantes (le favori peut finir n'importe où). Un exposant > 1 accentue
# les écarts de lambda entre équipes fortes et faibles, donc les favoris
# dominent plus nettement, tout en laissant des surprises ponctuelles grâce
# à la variance de Poisson. Calibré par simulation de saisons sur les 5
# championnats (voir README) : certains championnats ont un écart de notes
# beaucoup plus large que d'autres (le favori peut être un gros outlier,
# ex. le club le mieux noté très loin devant le 2e), donc un exposant plus
# faible qu'avec un seul championnat est nécessaire pour rester réaliste
# partout à la fois.
RATING_EXPONENT = 1.8


@dataclass(frozen=True)
class LeagueContext:
    """Moyenne de la ligue, utilisée pour calibrer les lambdas de Poisson."""

    avg_rating: float

    @classmethod
    def from_clubs(cls, clubs: list[Club]) -> LeagueContext:
        return cls(avg_rating=sum(c.rating for c in clubs) / len(clubs))


def simulate_match(home: Club, away: Club, context: LeagueContext) -> tuple[int, int]:
    """Simule un match et retourne (buts_domicile, buts_exterieur)."""
    lambda_home = _expected_goals(home, away, context, home_advantage=True)
    lambda_away = _expected_goals(away, home, context, home_advantage=False)
    home_goals = min(MAX_GOALS, int(np.random.poisson(lambda_home)))
    away_goals = min(MAX_GOALS, int(np.random.poisson(lambda_away)))
    return home_goals, away_goals


def simulate_journee(
    journee: Journee, clubs_by_name: dict[str, Club], context: LeagueContext
) -> None:
    """Simule tous les matchs non encore joués d'une journée (en place)."""
    for match in journee.matches:
        if match.played:
            continue
        home = clubs_by_name[match.home]
        away = clubs_by_name[match.away]
        match.home_goals, match.away_goals = simulate_match(home, away, context)


def _expected_goals(
    attacker: Club, defender: Club, context: LeagueContext, home_advantage: bool
) -> float:
    attack = (attacker.rating / context.avg_rating) ** RATING_EXPONENT
    defense = (context.avg_rating / defender.rating) ** RATING_EXPONENT
    lam = LEAGUE_AVG_GOALS * attack * defense
    if home_advantage:
        lam *= HOME_ADVANTAGE
    return lam

"""Moteur de simulation des matchs : loi de Poisson pondérée par la force
actuelle des équipes (voir lineup.club_strength), plus la génération des
événements de match (compos, buteurs/passeurs, cartons, blessures, notes) et
la mise à jour des indisponibilités pour les matchs suivants.

Le lambda (buts attendus) de chaque équipe est calibré sur la moyenne de la
ligue chargée (voir LeagueContext), donc ce module fonctionne pour n'importe
quel championnat, pas seulement la Ligue 1.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ligue1sim.clubs import Club
from ligue1sim.events import (
    AvailabilityTracker,
    MatchEvents,
    collect_new_bans,
    generate_match_events,
    settle_trackers,
)
from ligue1sim.lineup import Lineup, club_strength, pick_best_formation
from ligue1sim.schedule import Journee

LEAGUE_AVG_GOALS = 1.14  # buts moyens attendus par équipe et par match (recalibré pour RATING_EXPONENT=1.8)
HOME_ADVANTAGE = 1.10  # bonus de 10% sur le lambda de l'équipe à domicile
MAX_GOALS = 6  # plafond réaliste de buts par équipe et par match

# Exposant appliqué aux écarts de force actuelle (attaque/défense). Voir
# README pour le détail du calibrage (centaines de saisons simulées sur les
# 5 puis 8 championnats).
RATING_EXPONENT = 1.8


@dataclass(frozen=True)
class LeagueContext:
    """Moyenne de la ligue, utilisée pour calibrer les lambdas de Poisson."""

    avg_rating: float

    @classmethod
    def from_clubs(cls, clubs: list[Club]) -> LeagueContext:
        return cls(avg_rating=sum(club_strength(c) for c in clubs) / len(clubs))


def simulate_match(
    home: Club,
    away: Club,
    context: LeagueContext,
    unavailable_home: frozenset[str] = frozenset(),
    unavailable_away: frozenset[str] = frozenset(),
) -> tuple[int, int, MatchEvents | None]:
    """Simule un match : compos du jour (dispositif + indisponibilités),
    score, puis événements si les deux clubs ont un effectif réel (les clubs
    synthétiques sans effectif, utilisés par certains tests, n'ont pas
    d'événements -- juste un score, calculé avec la force de repli
    lineup.DEFAULT_RATING)."""
    home_lineup = pick_best_formation(home, unavailable_home)
    away_lineup = pick_best_formation(away, unavailable_away)

    home_goals, away_goals = _draw_score(home_lineup, away_lineup, context)

    events = None
    if home.players and away.players:
        events = generate_match_events(
            home, away, home_lineup, away_lineup, home_goals, away_goals, unavailable_home, unavailable_away
        )

    return home_goals, away_goals, events


def simulate_journee(
    journee: Journee,
    clubs_by_name: dict[str, Club],
    context: LeagueContext,
    suspensions: AvailabilityTracker | None = None,
    injuries: AvailabilityTracker | None = None,
) -> None:
    """Simule tous les matchs non encore joués d'une journée (en place).

    `suspensions`/`injuries` : si fournis, sont lus pour exclure les joueurs
    indisponibles des compos, puis mis à jour après coup (décrément des
    indisponibilités déjà en cours, puis application des nouvelles issues de
    cette journée). Si omis, des registres éphémères sont utilisés (aucune
    persistance -- comportement inchangé pour les appelants qui ne s'en
    soucient pas, y compris tous les tests existants).
    """
    suspensions = suspensions if suspensions is not None else AvailabilityTracker()
    injuries = injuries if injuries is not None else AvailabilityTracker()

    clubs_played: set[str] = set()
    new_suspensions: list[tuple[str, str, int]] = []
    new_injuries: list[tuple[str, str, int]] = []

    for match in journee.matches:
        if match.played:
            continue

        home, away = clubs_by_name[match.home], clubs_by_name[match.away]
        unavailable_home = suspensions.unavailable_players(home.name) | injuries.unavailable_players(home.name)
        unavailable_away = suspensions.unavailable_players(away.name) | injuries.unavailable_players(away.name)

        home_goals, away_goals, events = simulate_match(home, away, context, unavailable_home, unavailable_away)
        match.home_goals, match.away_goals, match.events = home_goals, away_goals, events
        clubs_played.update({home.name, away.name})

        if events is not None:
            match_suspensions, match_injuries = collect_new_bans(events)
            new_suspensions += match_suspensions
            new_injuries += match_injuries

    settle_trackers(suspensions, injuries, clubs_played, new_suspensions, new_injuries)


def _draw_score(home_lineup: Lineup, away_lineup: Lineup, context: LeagueContext) -> tuple[int, int]:
    lambda_home = _expected_goals(home_lineup.rating, away_lineup.rating, context, home_advantage=True)
    lambda_away = _expected_goals(away_lineup.rating, home_lineup.rating, context, home_advantage=False)
    home_goals = min(MAX_GOALS, int(np.random.poisson(lambda_home)))
    away_goals = min(MAX_GOALS, int(np.random.poisson(lambda_away)))
    return home_goals, away_goals


def _expected_goals(
    attack_rating: float, defense_rating: float, context: LeagueContext, home_advantage: bool
) -> float:
    attack = (attack_rating / context.avg_rating) ** RATING_EXPONENT
    defense = (context.avg_rating / defense_rating) ** RATING_EXPONENT
    lam = LEAGUE_AVG_GOALS * attack * defense
    if home_advantage:
        lam *= HOME_ADVANTAGE
    return lam

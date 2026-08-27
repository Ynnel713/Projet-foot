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
# 5 puis 8 championnats). Remonté 1.8 -> 1.98 -> 2.2 -> 5.5 -> 7.0 : les
# classements restaient trop condensés (trop d'upsets, un champion dominant
# ne dépassait quasiment jamais les 75-78 pts sur 38 journées alors qu'en
# réalité un champion très supérieur dépasse régulièrement les 90 pts). Le
# taux de nuls reste stable (~22-27%, vérifié sur plusieurs milliers de
# matchs) quel que soit l'exposant : contrairement à VARIANCE_SHRINK
# (abandonné, voir plus bas), il n'agit que sur l'espérance de buts, jamais
# sur la variance du tirage -- donc sans risque de gonfler artificiellement
# les nuls. À 9.0, un champion dépasse déjà les 100 pts en médiane : trop
# haut, 7.0 (champion médian ~87 pts, entre 80 et 94 sur 20 saisons testées)
# reste la valeur retenue. Revalidé sans changement après le passage aux
# forces sectorielles GK/DEF/MID/ATT (`_attack_strength`/`_defense_strength`
# ci-dessous, remplaçant la moyenne plate de la compo) : 20 saisons de
# Ligue 1 simulées avec ce nouveau calcul donnent un champion médian à 85
# pts (74-90) et ~21% de nuls -- toujours dans la fourchette ci-dessus, pas
# de raison de retoucher l'exposant pour ce changement.
RATING_EXPONENT = 7.0

# Plafond appliqué au lambda (buts attendus) d'une équipe, APRÈS RATING_EXPONENT.
# Nécessaire à un exposant aussi élevé : sans lui, le match le plus
# déséquilibré d'un championnat (le mieux noté à domicile contre le moins
# bien noté) atteignait un lambda > 4 buts attendus, avec ~29% de scores du
# type 5-0/6-0 rien que sur cette affiche précise (vérifié sur 3000 tirages)
# -- irréaliste, un score aussi large ne devrait rester qu'un accident rare.
# Plafonné à 2.0 buts attendus : ce taux retombe à ~3.5% pour l'affiche la
# plus déséquilibrée, et ~1.4% en moyenne sur des paires aléatoires (contre
# 2.0% sans plafond), sans dégrader la séparation des classements (champion
# médian ~81 pts sur 15 saisons testées, contre ~87-88 sans plafond -- effet
# marginal car ce plafond ne joue que sur les quelques affiches vraiment
# déséquilibrées d'un championnat, pas sur l'essentiel des matchs).
MAX_LAMBDA = 2.0

# Réduction de la variance du tirage de buts autour de sa moyenne (1.0 =
# Poisson pur, non modifié -- voir _draw_goals). Piste explorée puis
# ABANDONNÉE : resserrer le tirage avant arrondi entier fait s'écrouler
# quasi tous les scores sur le même entier dès que les deux lambdas sont
# proches (fréquent en championnat), ce qui fait exploser le taux de nuls
# (26% à 1.0, jusqu'à 54% à 0.45 -- vérifié sur 6000 matchs). Laissé à 1.0
# (Poisson pur) : la variance du tirage doit rester intacte, seul l'écart de
# force (RATING_EXPONENT) doit influencer le résultat.
VARIANCE_SHRINK = 1.0

# Poids du gardien dans la force défensive d'une équipe (le reste va aux
# défenseurs de champ) : un grand gardien ne suffit pas à masquer une
# défense fébrile, mais compte nettement plus qu'un joueur de champ de plus
# dans le secteur -- 35% a été choisi comme point de départ raisonnable
# (pas de série de saisons dédiée à ce réglage précis, contrairement à
# RATING_EXPONENT/MAX_LAMBDA ci-dessus -- à affiner si le comportement en
# jeu le justifie).
GK_WEIGHT_IN_DEFENSE = 0.35

# Influence (légère, volontairement douce) du milieu sur l'attaque ET la
# défense de sa propre équipe : un milieu nettement au-dessus du niveau
# moyen de l'équipe tire les deux vers le haut, un milieu à la traîne les
# tire vers le bas -- mesuré par l'écart RELATIF entre `mid_rating` et la
# moyenne globale de la compo (`rating`), pas par une comparaison à la
# moyenne de la ligue (garde le calcul local à l'équipe, pas de dépendance
# au contexte). Plafonné à ±10% (`_MID_MODIFIER_BOUNDS`) pour rester un
# ajustement, pas un second levier de force capable de rivaliser avec
# RATING_EXPONENT.
MID_INFLUENCE = 0.6
_MID_MODIFIER_BOUNDS = (0.90, 1.10)


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
    lambda_home = _expected_goals(_attack_strength(home_lineup), _defense_strength(away_lineup), context, home_advantage=True)
    lambda_away = _expected_goals(_attack_strength(away_lineup), _defense_strength(home_lineup), context, home_advantage=False)
    home_goals = _draw_goals(lambda_home)
    away_goals = _draw_goals(lambda_away)
    return home_goals, away_goals


def _mid_modifier(lineup: Lineup) -> float:
    """Modulateur (autour de 1.0) appliqué à l'attaque ET à la défense d'une
    équipe selon que son milieu est au-dessus ou en-dessous du niveau moyen
    de SA PROPRE compo (voir MID_INFLUENCE/_MID_MODIFIER_BOUNDS)."""
    relative_gap = (lineup.mid_rating - lineup.rating) / lineup.rating
    modifier = 1.0 + MID_INFLUENCE * relative_gap
    return min(_MID_MODIFIER_BOUNDS[1], max(_MID_MODIFIER_BOUNDS[0], modifier))


def _attack_strength(lineup: Lineup) -> float:
    """Force d'attaque d'une équipe pour un match : la note de ses
    attaquants alignés, modulée par son milieu (voir `_mid_modifier`)."""
    return lineup.att_rating * _mid_modifier(lineup)


def _defense_strength(lineup: Lineup) -> float:
    """Force défensive d'une équipe pour un match : gardien + défenseurs
    alignés (voir GK_WEIGHT_IN_DEFENSE), modulée par son milieu (voir
    `_mid_modifier`)."""
    combined = GK_WEIGHT_IN_DEFENSE * lineup.gk_rating + (1 - GK_WEIGHT_IN_DEFENSE) * lineup.def_rating
    return combined * _mid_modifier(lineup)


def _draw_goals(lam: float) -> int:
    """Tire un nombre de buts autour de `lam`, avec une variance resserrée
    par rapport à un Poisson pur (voir VARIANCE_SHRINK juste au-dessus) :
    l'écart du tirage brut à son espérance est réduit avant arrondi, ce qui
    borne les scores aberrants sans changer le nombre de buts moyen
    attendu."""
    sample = np.random.poisson(lam)
    shrunk = lam + VARIANCE_SHRINK * (sample - lam)
    return int(min(MAX_GOALS, max(0, round(shrunk))))


def _expected_goals(
    attack_rating: float, defense_rating: float, context: LeagueContext, home_advantage: bool
) -> float:
    attack = (attack_rating / context.avg_rating) ** RATING_EXPONENT
    defense = (context.avg_rating / defense_rating) ** RATING_EXPONENT
    lam = LEAGUE_AVG_GOALS * attack * defense
    if home_advantage:
        lam *= HOME_ADVANTAGE
    return min(lam, MAX_LAMBDA)

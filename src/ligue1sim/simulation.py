"""Moteur de simulation des matchs : loi de Poisson pondérée par la force
actuelle des équipes (voir lineup.club_strength), plus la génération des
événements de match (compos, buteurs/passeurs, cartons, blessures, notes) et
la mise à jour des indisponibilités pour les matchs suivants.

Le lambda (buts attendus) de chaque équipe est calibré sur la moyenne de la
ligue chargée (voir LeagueContext), donc ce module fonctionne pour n'importe
quel championnat, pas seulement la Ligue 1.

Historique de calibrage (audit complet + campagne de simulations menée en
août 2026, voir la conversation associée pour le détail des chiffres) :
l'ancienne formule élevait le ratio note/moyenne à un exposant très agressif
(RATING_EXPONENT=7.0) pour forcer les classements de saison à se séparer
suffisamment. Mesuré après coup : cet exposant produisait des lambdas bruts
allant jusqu'à 13.6 buts attendus, avec `MAX_LAMBDA` (alors 2.0) atteint sur
35% des matchs -- un plafond qui masquait en permanence une formule
fondamentalement mal calibrée, plutôt qu'un vrai garde-fou pour cas
exceptionnels. Remplacée par une formule ratio attaque/défense à puissance
modérée (façon Dixon-Coles), qui ne dépasse jamais son plafond en pratique
(max observé 2.67 sur 3.0), donne une distribution de scores et un rapport
favori/outsider bien plus réalistes (voir ATTACK_DEFENSE_POWER ci-dessous),
au prix d'un classement de saison moins étiré -- compensé par la couche de
forme (FormTracker, plus bas) plutôt que par un second exposant artificiel.

Deuxième calibrage (audit du 28/08/2026, signalé par Olivier : Crystal
Palace/Everton finissaient trop souvent sur le podium de Premier League,
Arsenal -- effectif le mieux noté -- pas assez souvent devant). Cause
racine : le calibrage d'août ci-dessus ne validait QUE des stats
match-par-match (nuls, 0-0, écarts, rapport favori/outsider), jamais le
classement de FIN DE SAISON -- or un léger avantage par match, même
statistiquement correct match par match, peut ne pas se cumuler sur 38
journées si ATTACK_DEFENSE_POWER est trop bas. Mesuré sur 220 saisons de
Premier League simulées via le pipeline réel (Season, pas une
réimplémentation séparée) à ATTACK_DEFENSE_POWER=1.8 : Crystal Palace
(note 77.5) finissait dans le top 3 sur 7 à 25% des saisons selon la
graine, Everton (note 76.2) sur 5 à 10% -- bien trop pour des effectifs
milieu de tableau. Porté à 2.6 (voir plus bas) : Crystal Palace 7-12%,
Everton 5-8%, sans bouger les stats match-par-match (nuls/0-0/buts par
match quasi identiques) ni jamais saturer MAX_LAMBDA (max observé 2.16 sur
les 20 clubs réels de Premier League, encore loin du plafond) -- la marge
de progression venait donc bien de l'exposant, pas d'un plafond mal réglé.
Le milieu/bas de tableau garde du brassage (ex. Hull City, note la plus
faible, reste hors du trio de relégation 42 à 45% des saisons) : ce n'est
pas un classement figé par note. `scripts/calibrate_engine.py` reporte
maintenant aussi cette distribution de classement de fin de saison par
club, pour ne plus valider un futur réglage sur les seules stats
match-par-match.

Troisième calibrage (même jour, demande de pousser encore plus loin :
Arsenal top 1-2 dans >95% des saisons, Crystal Palace/Everton top 3 dans
<1%). Testé empiriquement (donnée à l'appui, pas juste en théorie) :
ATTACK_DEFENSE_POWER=3.4 puis 4.0 -- résultat CONTRAIRE à l'objectif, sur
80 saisons Premier League chacun : le taux de "top 1-2" d'Arsenal RECULE
(31% à 2.6, 34% à 3.4, 28% à 4.0) au lieu de progresser, et les buts par
match d'Arsenal à domicile reculent aussi (1.54 à 1.61, jamais les
2.5-3.0 demandés). Cause : Arsenal (note 85.2) n'est séparé de Manchester
City (83.9) et Liverpool (83.4) que d'1 à 2 points sur 100 -- pousser
l'exposant écarte tout le trio de force moyenne du reste de la ligue
SANS les départager entre eux, donc Arsenal continue de se partager le
podium avec eux à peu près à parts égales. Aucune valeur globale de
ATTACK_DEFENSE_POWER ne peut faire dominer Arsenal >95% du temps sans
soit gonfler sa note au-dessus de City/Liverpool (hors périmètre : les
notes viennent de l'effectif scouté, pas d'un réglage moteur), soit
supprimer la variance du tirage Poisson au point de rendre le
classement quasi déterministe par note plutôt que simulé -- dans les
deux cas, plus un calibrage mais un changement de nature de l'outil.
ATTACK_DEFENSE_POWER reste donc à 2.6. Seul HOME_ADVANTAGE (voir plus
bas) a été relevé, un levier qui améliore réellement les stats de match
mesurées sans ce plafond structurel.

Quatrième calibrage (même jour) : ajout de deux facteurs manquants
demandés (BENCH_INFLUENCE, BIG_MATCH_BONUS -- voir plus bas), en gardant
le même principe que MID_INFLUENCE/FormTracker : des modulateurs BORNÉS,
secondaires à ATTACK_DEFENSE_POWER, jamais un second levier de force. Le
troisième facteur demandé (fatigue calendaire -- "malus si 2 matchs en 4
jours") N'A PAS été implémenté : `schedule.py`/`season.py` n'ont aucune
notion de date, et la Ligue des Champions (`champions_league.py`) est une
compétition entièrement séparée du calendrier de championnat (pas de
calendrier unique inter-compétitions) -- il n'existe donc aucune donnée
réelle de congestion de calendrier à partir de laquelle calculer une
fatigue. Fabriquer un signal de fatigue sans base réelle aurait été un
faux-semblant, pas une fonctionnalité. Nécessiterait un vrai système de
calendrier daté partagé entre compétitions -- hors périmètre de ce
calibrage.

Cinquième calibrage (29/08/2026, signalé par Olivier : classement de
Premier League "totalement impossible" -- AFC Bournemouth et Coventry City
en tête, Manchester City 14e). Investigation (voir `scripts/
calibrate_engine.py`, sortie complète sur 40 saisons) : la hiérarchie des
notes est correcte (Arsenal 85.0 en tête, Hull City 71.1 en dernier) et la
corrélation force réelle <-> points moyens sur plusieurs saisons est
mesurée à 0.91 -- donc PAS un bug de données ni de calcul de force. Le
vrai problème : sur 40 saisons à ATTACK_DEFENSE_POWER=2.6 (réglage du
troisième calibrage ci-dessus, jamais retouché depuis), Arsenal (note la
plus haute de la ligue) finissait 19e sur 20 dans au moins une saison, et
Hull City (note la plus basse) finissait 2e dans au moins une saison --
bien au-delà de toute variance réaliste. Cause racine identifiée : PAS
ATTACK_DEFENSE_POWER (déjà poussé à 2.6 puis testé jusqu'à 4.0 lors du
troisième calibrage, sans effet sur ce problème précis -- voir plus haut)
mais `_FORM_BOUNDS` (±15%), qui module l'attaque ET la défense d'un club à
CHAQUE match de la saison via un EMA persistant (contrairement à
MID_INFLUENCE/BENCH_INFLUENCE, recalculés indépendamment à chaque match) :
un club en série positive prolongée cumule un avantage soutenu sur des
dizaines de journées, largement capable de renverser un écart de note de
14 points sur une saison entière.

Hypothèse testée : resserrer `_FORM_BOUNDS` à ±15% aurait dû réduire ces
extrêmes -- confirmé, mais casse un invariant existant (voir tests
`TestFormTracker`) : `_FORM_SIGNAL_CLIP`/`_FORM_SIGNAL_SHRINK` n'avaient
jamais été recalibrés pour la nouvelle borne, donc UN SEUL match extrême
(6-0 contre 1.3 but attendu) saturait immédiatement la nouvelle borne
étroite -- exactement le risque qu'`_FORM_SIGNAL_CLIP`/`_FORM_SIGNAL_SHRINK`
étaient censés empêcher (voir plus haut, "un seul match chanceux ne doit
pas transformer durablement la force d'une équipe"). Corrigé en resserrant
`_FORM_SCALE` (1.0 -> 2.5) dans la même proportion que `_FORM_BOUNDS`
(±15% -> ±6%), ce qui compresse l'amplitude finale du modulateur sans
changer la dynamique relative de l'EMA : un match extrême isolé reste à
~60% de la nouvelle borne (comme avant, à l'échelle de l'ancienne borne),
une série de 20 matchs forts la sature toujours pleinement.

Résultat mesuré sur 40 saisons de Premier League après correctif : Arsenal
top 3 dans 88% des saisons (55% avant), jamais relégué, pire classement
8e (19e avant) ; Hull City jamais top 3, meilleur classement 7e (2e avant). Stats match par match quasi inchangées (victoire domicile
45.6%->46.1%, nul 24.8%->24.1%, moyenne de buts 2.59->2.60) : la forme
n'a jamais été le levier des indicateurs match par match validés lors des
calibrages précédents, seulement de la séparation de saison.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from ligue1sim.clubs import Club
from ligue1sim.events import (
    AvailabilityTracker,
    MatchEvents,
    collect_new_bans,
    generate_match_events,
    settle_trackers,
)
from ligue1sim.lineup import Lineup, bench, pick_best_formation
from ligue1sim.players import Player
from ligue1sim.schedule import Journee

LEAGUE_AVG_GOALS = 1.14  # buts moyens attendus par équipe et par match, pour une confrontation entre deux équipes de force moyenne

# Bonus sur le lambda de l'équipe à domicile. Relevé de 1.20 à 1.35 lors du
# troisième calibrage (28/08/2026, voir docstring du module) : mesuré sur
# 80 saisons de Premier League à ATTACK_DEFENSE_POWER=2.6, 1.35 donne un
# taux de victoires à domicile toutes équipes confondues de 45% (proche du
# réel, ~43-46%) et, pour Arsenal spécifiquement (effectif le mieux noté),
# 57% à domicile -- 1.5 pousse Arsenal à 62% mais fait aussi monter la
# moyenne TOUTE la ligue à 49%, au-dessus du réel : un home advantage plus
# fort profite à TOUTES les équipes à domicile, pas seulement aux
# meilleures, donc le pousser au-delà de ce qui est réaliste en moyenne de
# ligue pour gonfler le seul cas d'Arsenal dégraderait le reste du
# classement.
HOME_ADVANTAGE = 1.35
MAX_GOALS = 6  # plafond réaliste de buts par équipe et par match

# Puissance appliquée aux ratios attaque/moyenne-ligue et moyenne-ligue/défense
# (façon Dixon-Coles : force = ratio à la moyenne, pas un exposant écrasant
# l'écart brut). Remplace l'ancien RATING_EXPONENT=7.0, dont l'agressivité
# masquait un plafond systématiquement atteint (voir docstring du module).
# Testé de 1.0 (ratio pur) à 2.0 sur 122 400 matchs des 18 vrais clubs de
# Ligue 1 : 1.8 donnait le meilleur compromis MATCH PAR MATCH -- taux de
# nuls (~24-25%) et de 0-0 (~7-9%) proches du réel (~25-27% / ~8-10%),
# fréquence d'écarts de 3+ buts (~14-17%) et de clean sheets (~48-50%)
# également réalistes, et un rapport favori/outsider par tranche d'écart de
# force qui laisse une vraie place à la surprise même pour un très gros
# favori.
#
# Relevé à 2.6 lors du deuxième calibrage (voir docstring du module) : ce
# premier passage ne vérifiait jamais le CLASSEMENT DE SAISON, seulement
# les stats match par match -- or celles-ci restent quasi identiques entre
# 1.8 et 2.6 (le nombre de journées moyennes/proches domine ces stats),
# alors que la corrélation force réelle <-> classement final progresse
# nettement : sur 220 saisons de Premier League simulées, la présence en
# top 3 d'un effectif milieu de tableau (Crystal Palace, Everton) passe de
# 7-25% à 5-12%, sans écraser le brassage du milieu/bas de tableau.
ATTACK_DEFENSE_POWER = 2.6

# Plafond appliqué au lambda (buts attendus) d'une équipe. À
# ATTACK_DEFENSE_POWER=2.6, jamais atteint pour aucune confrontation de
# Premier League (max observé 2.16 sur les 20 clubs réels), et seulement
# pour les confrontations les plus extrêmes des championnats aux écarts de
# niveau plus marqués -- 0.3 à 2.1% des confrontations possibles selon la
# ligue (ex. Paris SG-Le Mans, Real Madrid-Málaga), jamais la majorité des
# matchs comme avec l'ancien RATING_EXPONENT=7.0 (voir docstring du
# module) : reste un vrai garde-fou pour un écart extrême (y compris
# Compétition Perso, sélections nationales très déséquilibrées), pas un
# correctif systématique.
MAX_LAMBDA = 3.0

# Réduction de la variance du tirage de buts autour de sa moyenne (1.0 =
# Poisson pur, non modifié -- voir _draw_goals). Piste explorée puis
# ABANDONNÉE : resserrer le tirage avant arrondi entier fait s'écrouler
# quasi tous les scores sur le même entier dès que les deux lambdas sont
# proches (fréquent en championnat), ce qui fait exploser le taux de nuls
# (26% à 1.0, jusqu'à 54% à 0.45 -- vérifié sur 6000 matchs). Laissé à 1.0
# (Poisson pur) : la variance du tirage doit rester intacte, seul l'écart de
# force (ATTACK_DEFENSE_POWER) doit influencer le résultat.
VARIANCE_SHRINK = 1.0

# Poids du gardien dans la force défensive d'une équipe (le reste va aux
# défenseurs de champ) : un grand gardien ne suffit pas à masquer une
# défense fébrile, mais compte nettement plus qu'un joueur de champ de plus
# dans le secteur -- 35% a été choisi comme point de départ raisonnable
# (pas de série de saisons dédiée à ce réglage précis, contrairement à
# ATTACK_DEFENSE_POWER/MAX_LAMBDA ci-dessus -- à affiner si le comportement
# en jeu le justifie).
GK_WEIGHT_IN_DEFENSE = 0.35

# Influence (légère, volontairement douce) du milieu sur l'attaque ET la
# défense de sa propre équipe : un milieu nettement au-dessus du niveau
# moyen de l'équipe tire les deux vers le haut, un milieu à la traîne les
# tire vers le bas -- mesuré par l'écart RELATIF entre `mid_rating` et la
# moyenne globale de la compo (`rating`), pas par une comparaison à la
# moyenne de la ligue (garde le calcul local à l'équipe, pas de dépendance
# au contexte). Plafonné à ±10% (`_MID_MODIFIER_BOUNDS`) pour rester un
# ajustement, pas un second levier de force capable de rivaliser avec
# ATTACK_DEFENSE_POWER.
MID_INFLUENCE = 0.6
_MID_MODIFIER_BOUNDS = (0.90, 1.10)

# Influence de la profondeur du banc (les remplaçants disponibles, hors les
# 11 titulaires) sur l'attaque ET la défense d'une équipe : un banc mieux
# noté que la moyenne des titulaires de la ligue (`context.avg_rating`)
# donne un léger avantage (rotation sans perte de niveau, joker offensif ou
# défensif en cours de match), un banc creux un léger désavantage --
# mesuré par l'écart RELATIF entre la note moyenne du banc et cette
# moyenne de ligue. Plafonné à ±6% (`_BENCH_MODIFIER_BOUNDS`), plus
# resserré que MID_INFLUENCE (±10%) : le banc pèse par nature moins sur un
# match que les 11 qui le débutent.
BENCH_INFLUENCE = 0.5
_BENCH_MODIFIER_BOUNDS = (0.94, 1.06)

# Bonus d'intensité pour un "gros match" -- les deux équipes du top tiers
# de la ligue (voir `_BIG_MATCH_FRACTION`, calculé par ligue dans
# `LeagueContext.from_clubs`) s'affrontent. Appliqué symétriquement à
# l'attaque des deux équipes (jamais à la défense, pour ne pas s'annuler
# avec lui-même) : les grosses affiches sont jouées à intensité plus
# élevée des deux côtés, sans favoriser l'une ou l'autre. Modeste et
# borné, comme les autres modulateurs de cette section -- pas un second
# ATTACK_DEFENSE_POWER.
_BIG_MATCH_FRACTION = 1 / 3  # ex. 6-7 clubs sur 18-20 : approxime le "top 6" habituel
BIG_MATCH_BONUS = 0.05

# --- Forme (inertie sportive persistante, EMA de performance réelle) -----
#
# Chaque club a une forme offensive et une forme défensive distinctes
# (testé contre une forme unique : la version séparée donne un taux de
# nuls/0-0/clean-sheets mesurablement plus proche du réel, pour une seule
# variable de plus -- voir FormTracker). Mise à jour après CHAQUE match avec
# la PERFORMANCE réelle par rapport à l'attendu du moment (`buts réels -
# lambda`), jamais avec le seul résultat (victoire/nul/défaite) : une équipe
# qui gagne 1-0 en étant dominée n'améliore pas sa forme offensive pour
# autant.
#
# Le signal brut (buts - lambda) est BRUYANT : un seul match à forte
# variance (ex. 4 buts marqués pour 1.3 attendus, delta=+2.7) sature quasi
# instantanément une forme bornée à ±15% si on l'injecte tel quel dans l'EMA
# -- vérifié : avec alpha=0.12, un signal brut donne un pic de forme de
# +0.32 après UN SEUL match extrême (le plafond ±0.15 est immédiatement
# dépassé), contre +0.09 avec le signal plafonné puis rétréci ci-dessous --
# un seul match chanceux ne doit pas transformer durablement la force d'une
# équipe.
FORM_ALPHA = 0.12  # mémoire de l'EMA : ~1/alpha ~ 8 matchs de mémoire effective
_FORM_SIGNAL_CLIP = 1.5  # écart (buts réels - lambda) plafonné à cette valeur avant traitement
_FORM_SIGNAL_SHRINK = 0.5  # puis multiplié par ce facteur -- amortit encore le bruit match-à-match
_FORM_SCALE = 2.5  # échelle de conversion forme -> modulateur (voir _form_modifier)
_FORM_BOUNDS = (0.94, 1.06)  # amplitude maximale du modulateur de forme -- cinquième calibrage (29/08/2026, voir docstring du module), ancienne valeur (0.85, 1.15)


@dataclass(frozen=True)
class LeagueContext:
    """Moyennes de la ligue, utilisées pour calibrer les lambdas de Poisson :
    `avg_rating` (moyenne plate, têtes de série/affichage -- inchangé),
    `avg_attack`/`avg_defense` (moyennes sectorielles, voir
    `_attack_strength`/`_defense_strength`) pour la conversion ratio
    attaque/défense de `_expected_goals`. `big_match_clubs` : noms des clubs
    du tiers le mieux noté de CETTE ligue (voir BIG_MATCH_BONUS) -- vide par
    défaut pour les `LeagueContext` construits directement (ex. tests), donc
    aucun bonus de rivalité tant qu'il n'est pas explicitement peuplé via
    `from_clubs`."""

    avg_rating: float
    avg_attack: float
    avg_defense: float
    big_match_clubs: frozenset[str] = frozenset()

    @classmethod
    def from_clubs(cls, clubs: list[Club]) -> LeagueContext:
        lineups = [pick_best_formation(c) for c in clubs]
        nb_big_match_clubs = max(1, round(len(lineups) * _BIG_MATCH_FRACTION))
        top_by_rating = sorted(lineups, key=lambda lu: -lu.rating)[:nb_big_match_clubs]
        return cls(
            avg_rating=sum(lu.rating for lu in lineups) / len(lineups),
            avg_attack=sum(_attack_strength(lu) for lu in lineups) / len(lineups),
            avg_defense=sum(_defense_strength(lu) for lu in lineups) / len(lineups),
            big_match_clubs=frozenset(lu.club_name for lu in top_by_rating),
        )


def simulate_match(
    home: Club,
    away: Club,
    context: LeagueContext,
    unavailable_home: frozenset[str] = frozenset(),
    unavailable_away: frozenset[str] = frozenset(),
    form: FormTracker | None = None,
) -> tuple[int, int, MatchEvents | None]:
    """Simule un match : compos du jour (dispositif + indisponibilités),
    score, puis événements si les deux clubs ont un effectif réel (les clubs
    synthétiques sans effectif, utilisés par certains tests, n'ont pas
    d'événements -- juste un score, calculé avec la force de repli
    lineup.DEFAULT_RATING).

    `form` : si fourni, module l'attaque/la défense de chaque club selon sa
    forme actuelle avant le tirage, puis est mis à jour avec la performance
    réelle de ce match (voir FormTracker). Si omis, aucune forme n'est
    appliquée -- comportement inchangé pour les appelants qui ne s'en
    soucient pas, y compris tous les tests existants."""
    home_lineup = pick_best_formation(home, unavailable_home)
    away_lineup = pick_best_formation(away, unavailable_away)
    home_bench_mod = _bench_modifier(bench(home, home_lineup, unavailable_home), context)
    away_bench_mod = _bench_modifier(bench(away, away_lineup, unavailable_away), context)

    home_goals, away_goals, lambda_home, lambda_away = _draw_score(
        home_lineup, away_lineup, context, home.name, away.name, form, home_bench_mod, away_bench_mod
    )
    if form is not None:
        form.record_match(home.name, away.name, lambda_home, lambda_away, home_goals, away_goals)

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
    form: FormTracker | None = None,
) -> None:
    """Simule tous les matchs non encore joués d'une journée (en place).

    `suspensions`/`injuries` : si fournis, sont lus pour exclure les joueurs
    indisponibles des compos, puis mis à jour après coup (décrément des
    indisponibilités déjà en cours, puis application des nouvelles issues de
    cette journée). Si omis, des registres éphémères sont utilisés (aucune
    persistance -- comportement inchangé pour les appelants qui ne s'en
    soucient pas, y compris tous les tests existants).

    `form` : voir `simulate_match` -- même logique d'omission optionnelle.
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

        home_goals, away_goals, events = simulate_match(home, away, context, unavailable_home, unavailable_away, form)
        match.home_goals, match.away_goals, match.events = home_goals, away_goals, events
        clubs_played.update({home.name, away.name})

        if events is not None:
            match_suspensions, match_injuries = collect_new_bans(events)
            new_suspensions += match_suspensions
            new_injuries += match_injuries

    settle_trackers(suspensions, injuries, clubs_played, new_suspensions, new_injuries)


def _draw_score(
    home_lineup: Lineup,
    away_lineup: Lineup,
    context: LeagueContext,
    home_name: str,
    away_name: str,
    form: FormTracker | None,
    home_bench_mod: float = 1.0,
    away_bench_mod: float = 1.0,
) -> tuple[int, int, float, float]:
    home_off_mod = form.offense_modifier(home_name) if form is not None else 1.0
    home_def_mod = form.defense_modifier(home_name) if form is not None else 1.0
    away_off_mod = form.offense_modifier(away_name) if form is not None else 1.0
    away_def_mod = form.defense_modifier(away_name) if form is not None else 1.0
    big_match_mod = (
        1.0 + BIG_MATCH_BONUS
        if home_name in context.big_match_clubs and away_name in context.big_match_clubs
        else 1.0
    )

    attack_home = _attack_strength(home_lineup) * home_off_mod * home_bench_mod * big_match_mod
    defense_home = _defense_strength(home_lineup) * home_def_mod * home_bench_mod
    attack_away = _attack_strength(away_lineup) * away_off_mod * away_bench_mod * big_match_mod
    defense_away = _defense_strength(away_lineup) * away_def_mod * away_bench_mod

    lambda_home = _expected_goals(attack_home, defense_away, context, home_advantage=True)
    lambda_away = _expected_goals(attack_away, defense_home, context, home_advantage=False)
    home_goals = _draw_goals(lambda_home)
    away_goals = _draw_goals(lambda_away)
    return home_goals, away_goals, lambda_home, lambda_away


def _bench_modifier(reserves: list[Player], context: LeagueContext) -> float:
    """Modulateur (autour de 1.0) appliqué à l'attaque ET à la défense d'une
    équipe selon que son banc (remplaçants disponibles, hors les 11
    titulaires) est mieux ou moins bien noté que la moyenne des titulaires
    de la ligue (voir BENCH_INFLUENCE/_BENCH_MODIFIER_BOUNDS). 1.0 (neutre)
    si le banc est vide (aucun remplaçant disponible)."""
    if not reserves:
        return 1.0
    bench_rating = sum(p.note for p in reserves) / len(reserves)
    relative_gap = (bench_rating - context.avg_rating) / context.avg_rating
    modifier = 1.0 + BENCH_INFLUENCE * relative_gap
    return min(_BENCH_MODIFIER_BOUNDS[1], max(_BENCH_MODIFIER_BOUNDS[0], modifier))


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
    attack_strength: float, defense_strength: float, context: LeagueContext, home_advantage: bool
) -> float:
    """Buts attendus (lambda) pour une équipe dont la force d'attaque est
    `attack_strength`, face à une défense adverse `defense_strength` --
    ratio à la moyenne de la ligue, façon Dixon-Coles (voir
    ATTACK_DEFENSE_POWER pour le calibrage). `home_advantage=True`
    n'affecte QUE ce lambda (celui de l'équipe qui reçoit), jamais celui de
    l'adversaire -- voir HOME_ADVANTAGE."""
    attack_ratio = (attack_strength / context.avg_attack) ** ATTACK_DEFENSE_POWER
    defense_ratio = (context.avg_defense / defense_strength) ** ATTACK_DEFENSE_POWER
    lam = LEAGUE_AVG_GOALS * attack_ratio * defense_ratio
    if home_advantage:
        lam *= HOME_ADVANTAGE
    return min(lam, MAX_LAMBDA)


@dataclass
class ClubForm:
    offense: float = 0.0
    defense: float = 0.0


@dataclass
class FormTracker:
    """Forme persistante (offensive et défensive séparées) par club --
    inertie sportive légère, PAS un second levier de force : voir la
    section 'Forme' en tête de ce module pour la justification de chaque
    paramètre. Même pattern d'utilisation que `events.AvailabilityTracker` :
    une instance créée une fois, réutilisée et mise à jour au fil des
    journées d'une même saison/compétition."""

    _forms: dict[str, ClubForm] = field(default_factory=dict)

    def offense_modifier(self, club_name: str) -> float:
        return _form_modifier(self._forms.get(club_name, ClubForm()).offense)

    def defense_modifier(self, club_name: str) -> float:
        return _form_modifier(self._forms.get(club_name, ClubForm()).defense)

    def record_match(
        self,
        home_name: str,
        away_name: str,
        lambda_home: float,
        lambda_away: float,
        home_goals: int,
        away_goals: int,
    ) -> None:
        """Met à jour la forme des deux clubs avec leur performance réelle
        de CE match par rapport à l'attendu du moment (`lambda_home`/
        `lambda_away`, tels qu'effectivement utilisés pour le tirage --
        forme du match déjà incluse), jamais avec le seul résultat."""
        self._update(home_name, raw_offense=home_goals - lambda_home, raw_defense=lambda_away - away_goals)
        self._update(away_name, raw_offense=away_goals - lambda_away, raw_defense=lambda_home - home_goals)

    def _update(self, club_name: str, raw_offense: float, raw_defense: float) -> None:
        current = self._forms.setdefault(club_name, ClubForm())
        current.offense = FORM_ALPHA * _process_form_signal(raw_offense) + (1 - FORM_ALPHA) * current.offense
        current.defense = FORM_ALPHA * _process_form_signal(raw_defense) + (1 - FORM_ALPHA) * current.defense


def _process_form_signal(raw: float) -> float:
    """Plafonne puis rétrécit l'écart (buts réels - lambda) avant de
    l'injecter dans l'EMA de forme -- un signal brut sature quasi
    instantanément une forme bornée dès qu'un seul match a une forte
    variance (vérifié : +0.32 après un seul match à delta=+2.7 avec
    alpha=0.12, contre +0.09 avec ce traitement -- voir la section 'Forme'
    en tête de ce module)."""
    clipped = min(_FORM_SIGNAL_CLIP, max(-_FORM_SIGNAL_CLIP, raw))
    return clipped * _FORM_SIGNAL_SHRINK


def _form_modifier(value: float) -> float:
    return min(_FORM_BOUNDS[1], max(_FORM_BOUNDS[0], 1.0 + value / _FORM_SCALE))

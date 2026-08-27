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
from ligue1sim.lineup import Lineup, pick_best_formation
from ligue1sim.schedule import Journee

LEAGUE_AVG_GOALS = 1.14  # buts moyens attendus par équipe et par match, pour une confrontation entre deux équipes de force moyenne
HOME_ADVANTAGE = 1.20  # bonus sur le lambda de l'équipe à domicile -- voir ATTACK_DEFENSE_POWER pour le détail du calibrage
MAX_GOALS = 6  # plafond réaliste de buts par équipe et par match

# Puissance appliquée aux ratios attaque/moyenne-ligue et moyenne-ligue/défense
# (façon Dixon-Coles : force = ratio à la moyenne, pas un exposant écrasant
# l'écart brut). Remplace l'ancien RATING_EXPONENT=7.0, dont l'agressivité
# masquait un plafond systématiquement atteint (voir docstring du module).
# Testé de 1.0 (ratio pur) à 2.0 sur 122 400 matchs des 18 vrais clubs de
# Ligue 1 : 1.8 donne le meilleur compromis mesuré -- taux de nuls (~24-25%)
# et de 0-0 (~7-9%) proches du réel (~25-27% / ~8-10%), fréquence d'écarts
# de 3+ buts (~14-17%) et de clean sheets (~48-50%) également réalistes,
# et un rapport favori/outsider par tranche d'écart de force qui laisse une
# vraie place à la surprise même pour un très gros favori (~10% de défaite
# à l'écart de force maximal, contre <2% avec l'ancien exposant).
ATTACK_DEFENSE_POWER = 1.8

# Plafond appliqué au lambda (buts attendus) d'une équipe. Avec
# ATTACK_DEFENSE_POWER=1.8, ce plafond n'est en pratique jamais atteint (max
# observé 2.67 sur les 18 clubs de Ligue 1, voir docstring du module) : il
# reste un vrai garde-fou pour un futur effectif extrême (Compétition Perso,
# sélections nationales très déséquilibrées), pas un correctif systématique
# comme avec l'ancienne formule.
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
_FORM_SCALE = 1.0  # échelle de conversion forme -> modulateur (voir _form_modifier)
_FORM_BOUNDS = (0.85, 1.15)  # amplitude maximale du modulateur de forme, même esprit que _MID_MODIFIER_BOUNDS


@dataclass(frozen=True)
class LeagueContext:
    """Moyennes de la ligue, utilisées pour calibrer les lambdas de Poisson :
    `avg_rating` (moyenne plate, têtes de série/affichage -- inchangé),
    `avg_attack`/`avg_defense` (moyennes sectorielles, voir
    `_attack_strength`/`_defense_strength`) pour la conversion ratio
    attaque/défense de `_expected_goals`."""

    avg_rating: float
    avg_attack: float
    avg_defense: float

    @classmethod
    def from_clubs(cls, clubs: list[Club]) -> LeagueContext:
        lineups = [pick_best_formation(c) for c in clubs]
        return cls(
            avg_rating=sum(lu.rating for lu in lineups) / len(lineups),
            avg_attack=sum(_attack_strength(lu) for lu in lineups) / len(lineups),
            avg_defense=sum(_defense_strength(lu) for lu in lineups) / len(lineups),
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

    home_goals, away_goals, lambda_home, lambda_away = _draw_score(home_lineup, away_lineup, context, home.name, away.name, form)
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
) -> tuple[int, int, float, float]:
    home_off_mod = form.offense_modifier(home_name) if form is not None else 1.0
    home_def_mod = form.defense_modifier(home_name) if form is not None else 1.0
    away_off_mod = form.offense_modifier(away_name) if form is not None else 1.0
    away_def_mod = form.defense_modifier(away_name) if form is not None else 1.0

    attack_home = _attack_strength(home_lineup) * home_off_mod
    defense_home = _defense_strength(home_lineup) * home_def_mod
    attack_away = _attack_strength(away_lineup) * away_off_mod
    defense_away = _defense_strength(away_lineup) * away_def_mod

    lambda_home = _expected_goals(attack_home, defense_away, context, home_advantage=True)
    lambda_away = _expected_goals(attack_away, defense_home, context, home_advantage=False)
    home_goals = _draw_goals(lambda_home)
    away_goals = _draw_goals(lambda_away)
    return home_goals, away_goals, lambda_home, lambda_away


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

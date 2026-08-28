"""Ce qui se passe pendant un match : buteurs, passeurs, cartons, blessures,
remplacements, note /10 par joueur -- et les registres d'indisponibilité
(suspensions, blessures) qui influencent les compos des matchs suivants.

Les probabilités ci-dessous (cartons, blessures) sont des constantes
calibrées à la main, dans le même esprit que LEAGUE_AVG_GOALS/RATING_EXPONENT
dans simulation.py : ajustables, documentées, pas une vérité absolue.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from ligue1sim.clubs import Club
from ligue1sim.lineup import Lineup, bench
from ligue1sim.players import ASSIST_WEIGHT, GOALKEEPER, SCORER_WEIGHT, Player

# --- Cartons -----------------------------------------------------------
# Par joueur ayant joué, indépendamment. Cible ~3-5 jaunes et ~1 rouge
# (direct ou 2e jaune confondus) toutes les quelques rencontres, sur les
# ~24 joueurs qui foulent la pelouse (titulaires + entrants) d'un match.
P_RED_DIRECT = 0.006
P_SECOND_YELLOW_RED = 0.010
P_SINGLE_YELLOW = 0.160

# --- Blessures -----------------------------------------------------------
# Volontairement rare et courte : "un petit côté réaliste", pas une
# hécatombe ni des indisponibilités de plusieurs mois.
P_INJURY = 0.010
INJURY_MIN_MATCHES = 1
INJURY_MAX_MATCHES = 3

# --- Buts/passes -----------------------------------------------------------
NOTE_EXPONENT = 0.8  # amplifie l'effet de la qualité générale du joueur sur le tirage des passes décisives
# Exposant dédié au tirage du buteur, plus fort que NOTE_EXPONENT -- sans ça,
# deux attaquants de note proche se disputent les buts à parts quasi égales,
# ce qui noyait des buteurs pourtant nettement supérieurs (ex. Haaland hors
# du top 10 des buteurs malgré une note parmi les toutes meilleures de son
# championnat). Avant la suppression des caractéristiques par joueur au
# profit d'une seule note globale, ce même effet passait par une
# caractéristique "Finition" dédiée (amplifiée par un exposant 2.2 en plus
# du NOTE_EXPONENT=0.8 de base) ; les deux sont fusionnés ici (0.8 + 2.2).
GOAL_NOTE_EXPONENT = 3.0
UNASSISTED_GOAL_PROBABILITY = 0.25
SUB_EVENT_WEIGHT = 0.4  # poids réduit des entrants (moins de temps de jeu)

# --- Remplacements -----------------------------------------------------------
MIN_SUBSTITUTIONS = 3
MAX_SUBSTITUTIONS = 5
SUB_MIN_MINUTE = 46  # les remplacements simulés n'interviennent qu'en 2e mi-temps
SUB_MAX_MINUTE = 90
# Taille des "paquets" de remplacements tactiques (hors blessure) : la
# plupart des entraîneurs groupent leurs changements par 2 ou 3 plutôt que
# d'en faire un isolé à chaque arrêt de jeu (voir `_batch_substitution_minutes`).
SUB_BATCH_SIZES = (2, 3)

# --- Pénalties -----------------------------------------------------------
PENALTY_GOAL_PROBABILITY = 0.09  # part des buts marqués inscrits sur penalty
P_MATCH_HAS_MISSED_PENALTY = 0.05  # probabilité qu'un penalty manqué survienne dans le match

# --- Notes /10 -----------------------------------------------------------
BASE_RATING = 6.0
RATING_MIN = 3.0
RATING_MAX = 10.0
# Bruit gaussien ajouté à la note /10 de chaque joueur, indépendamment de sa
# performance réelle (but/passe/carton/résultat, déjà pris en compte par
# ailleurs dans `_rate_player`). Baissé de 0.4 à 0.3 (l'aléatoire perçu en
# jeu restait un peu trop présent) : à 0.4, l'écart-type dépassait à lui
# seul l'effet d'un carton jaune (-0.3) sur la note, ce qui noyait le signal
# de performance dans le bruit. Le tirage de score (simulation.py,
# RATING_EXPONENT/MAX_LAMBDA) n'est volontairement pas retouché ici : il
# reste dans la fourchette déjà validée (champion médian ~85 pts, ~21% de
# nuls sur 20 saisons de Ligue 1 simulées après le passage aux forces
# sectorielles GK/DEF/MID/ATT, voir simulation.py) -- pas de raison d'y
# retoucher tant que ce n'est pas explicitement ce qui pose problème.
RATING_NOISE_STD = 0.3


@dataclass
class AvailabilityTracker:
    """Registre générique d'indisponibilité (sert aussi bien aux suspensions
    qu'aux blessures -- même mécanique, deux instances distinctes en pratique
    pour un affichage séparé).

    Séquence à respecter par l'appelant pour chaque match/journée simulée :
    1. `unavailable_players` (état hérité des matchs précédents, avant de
       simuler) ;
    2. simuler ;
    3. `record_matchday(clubs_qui_ont_joue)` pour décrémenter les
       indisponibilités déjà en cours ;
    4. `apply_new_ban` pour les nouvelles indisponibilités déclenchées par ce
       match (elles démarrent au match suivant, pas au match qui vient
       d'avoir lieu).
    """

    _bans: dict[tuple[str, str], int] = field(default_factory=dict)

    def unavailable_players(self, club_name: str) -> frozenset[str]:
        return frozenset(p for (c, p), n in self._bans.items() if c == club_name and n > 0)

    def apply_new_ban(self, club_name: str, player_name: str, matches: int) -> None:
        key = (club_name, player_name)
        self._bans[key] = max(matches, self._bans.get(key, 0))

    def record_matchday(self, clubs_played: set[str]) -> None:
        for key in list(self._bans):
            club_name, _ = key
            if club_name in clubs_played:
                self._bans[key] -= 1
                if self._bans[key] <= 0:
                    del self._bans[key]

    def active_bans(self) -> list[tuple[str, str, int]]:
        return sorted((c, p, n) for (c, p), n in self._bans.items())


@dataclass(frozen=True)
class PlayerMatchStat:
    player_name: str
    club_name: str
    poste: str
    started: bool
    goals: int = 0
    assists: int = 0
    yellow_cards: int = 0
    red_card_type: str | None = None  # "direct" | "second_yellow" | None
    injured: bool = False
    injury_duration: int = 0
    rating: float = BASE_RATING
    # Indice de ligne dans le dispositif (voir lineup.Lineup.bands), None si
    # inconnu (dispositif absent de l'onglet "Dispositifs tactiques" -- voir
    # pitch_layout._group_into_lines, qui retombe alors sur un regroupement
    # générique par grande famille de poste).
    band: int | None = None
    # Profil du joueur (indépendant du match), pour la fiche cliquable côté UI.
    age: int = 0
    nationalite: str = ""
    note: float = 0.0


@dataclass(frozen=True)
class GoalEvent:
    club_name: str
    scorer: str
    assist: str | None
    minute: int = 1
    penalty: bool = False


@dataclass(frozen=True)
class SubstitutionEvent:
    club_name: str
    player_off: str
    player_on: str
    minute: int = SUB_MIN_MINUTE


@dataclass(frozen=True)
class CardEvent:
    club_name: str
    player: str
    minute: int
    card_type: str  # "yellow" | "second_yellow" | "direct"


@dataclass(frozen=True)
class InjuryEvent:
    club_name: str
    player: str
    minute: int


@dataclass(frozen=True)
class PenaltyMissedEvent:
    club_name: str
    player: str
    minute: int


@dataclass(frozen=True)
class MatchEvents:
    home_formation: str
    away_formation: str
    home_lineup: list[PlayerMatchStat]
    away_lineup: list[PlayerMatchStat]
    goals: list[GoalEvent] = field(default_factory=list)
    substitutions: list[SubstitutionEvent] = field(default_factory=list)
    cards: list[CardEvent] = field(default_factory=list)
    injuries: list[InjuryEvent] = field(default_factory=list)
    penalties_missed: list[PenaltyMissedEvent] = field(default_factory=list)


def generate_match_events(
    home_club: Club,
    away_club: Club,
    home_lineup: Lineup,
    away_lineup: Lineup,
    home_goals: int,
    away_goals: int,
    unavailable_home: frozenset[str] = frozenset(),
    unavailable_away: frozenset[str] = frozenset(),
) -> MatchEvents:
    """Construit tout ce qui s'est passé pendant le match à partir du score
    déjà tiré : remplacements, buteurs/passeurs, cartons, blessures, notes."""
    home_squad, home_subs, home_starter_injuries = _play_match_squad(home_club, home_lineup, unavailable_home)
    away_squad, away_subs, away_starter_injuries = _play_match_squad(away_club, away_lineup, unavailable_away)

    goals = _generate_goals(home_club.name, home_squad, home_goals) + _generate_goals(
        away_club.name, away_squad, away_goals
    )

    home_result = _result(home_goals, away_goals)
    away_result = _result(away_goals, home_goals)

    home_stats, home_cards, home_injuries = _build_stats(
        home_squad, home_lineup, goals, home_result, away_goals, home_starter_injuries
    )
    away_stats, away_cards, away_injuries = _build_stats(
        away_squad, away_lineup, goals, away_result, home_goals, away_starter_injuries
    )

    penalties_missed = _generate_missed_penalties(
        [(home_club.name, home_squad), (away_club.name, away_squad)]
    )

    return MatchEvents(
        home_formation=home_lineup.formation,
        away_formation=away_lineup.formation,
        home_lineup=home_stats,
        away_lineup=away_stats,
        goals=goals,
        substitutions=home_subs + away_subs,
        cards=home_cards + away_cards,
        injuries=home_injuries + away_injuries,
        penalties_missed=penalties_missed,
    )


def _random_minute(low: int = 1, high: int = 90) -> int:
    return random.randint(low, high)


def _batch_substitution_minutes(nb_subs: int) -> list[int]:
    """Minute de chacun des `nb_subs` remplacements tactiques (hors
    blessure), groupés par paquets de `SUB_BATCH_SIZES` joueurs partageant
    la même minute -- comme la plupart des entraîneurs, qui font un double
    ou triple changement d'un coup plutôt qu'un remplacement isolé à
    chaque fois."""
    minutes: list[int] = []
    remaining = nb_subs
    while remaining > 0:
        batch_size = min(remaining, random.choice(SUB_BATCH_SIZES)) if remaining > 1 else 1
        minute = _random_minute(SUB_MIN_MINUTE, SUB_MAX_MINUTE)
        minutes += [minute] * batch_size
        remaining -= batch_size
    return sorted(minutes)


def _result(goals_for: int, goals_against: int) -> str:
    if goals_for > goals_against:
        return "victoire"
    if goals_for < goals_against:
        return "defaite"
    return "nul"


@dataclass(frozen=True)
class _SquadEntry:
    player: Player
    started: bool
    weight_multiplier: float
    minute_on: int | None = None  # None pour un titulaire (sur le terrain depuis la 1re minute)
    minute_off: int | None = None  # None si le joueur termine le match (jamais remplacé)
    band: int | None = None  # voir lineup.Lineup.bands ; un entrant hérite de la ligne du sortant qu'il remplace

    def minute_range(self) -> tuple[int, int]:
        """Fenêtre [min, max] pendant laquelle ce joueur est effectivement sur
        le terrain, pour tirer un but/carton/blessure à une minute cohérente
        avec son temps de jeu réel."""
        return self.minute_on or 1, self.minute_off or 90


def _play_match_squad(
    club: Club, lineup: Lineup, unavailable: frozenset[str]
) -> tuple[list[_SquadEntry], list[SubstitutionEvent], dict[str, tuple[bool, int, int]]]:
    """Titulaires (poids plein) + remplaçants entrés en jeu (poids réduit),
    la liste des remplacements effectués (pour l'affichage), et les
    blessures des titulaires (name -> (blessé, durée, minute)), tirées ici
    -- avant les remplacements -- pour qu'un titulaire blessé, gardien
    compris, sorte en priorité s'il reste un remplaçant du même groupe."""
    reserves = bench(club, lineup, unavailable)
    starters = list(lineup.players)

    starter_injuries: dict[str, tuple[bool, int, int]] = {}
    for p in starters:
        injured, duration = _draw_injury()
        starter_injuries[p.name] = (injured, duration, _random_minute(1, 90) if injured else 0)

    substitutions: list[SubstitutionEvent] = []
    subs_on: list[tuple[Player, int, int | None]] = []
    used_reserve_names: set[str] = set()
    subbed_off_names: set[str] = set()

    if reserves:
        nb_subs_total = random.randint(MIN_SUBSTITUTIONS, MAX_SUBSTITUTIONS)

        # 1. Remplacements forcés par blessure (gardien compris) : priorité
        #    absolue, dans l'ordre chronologique des blessures.
        injured_starters = sorted(
            (p for p in starters if starter_injuries[p.name][0]), key=lambda p: starter_injuries[p.name][2]
        )
        for player_off in injured_starters:
            if len(subs_on) >= nb_subs_total:
                break
            pool = [p for p in reserves if p.group == player_off.group and p.name not in used_reserve_names]
            if not pool:
                continue  # pas de remplaçant du même groupe (ex. aucun gardien sur le banc) : il reste sur le terrain
            player_on = max(pool, key=lambda p: p.note)
            used_reserve_names.add(player_on.name)
            subbed_off_names.add(player_off.name)
            minute = starter_injuries[player_off.name][2]
            subs_on.append((player_on, minute, lineup.bands.get(player_off.name)))
            substitutions.append(
                SubstitutionEvent(
                    club_name=club.name, player_off=player_off.name, player_on=player_on.name, minute=minute
                )
            )

        # 2. Remplacements tactiques restants, comme avant (jamais le
        #    gardien -- sauf blessure, déjà traité ci-dessus).
        remaining_slots = nb_subs_total - len(subs_on)
        if remaining_slots > 0:
            candidates_off = [
                p for p in starters if p.group != GOALKEEPER and p.name not in subbed_off_names
            ]
            random.shuffle(candidates_off)
            nb_subs = min(remaining_slots, len(candidates_off), len(reserves) - len(used_reserve_names))
            sub_minutes = _batch_substitution_minutes(nb_subs)

            for index, player_off in enumerate(candidates_off[:nb_subs]):
                same_group = [
                    p for p in reserves if p.group == player_off.group and p.name not in used_reserve_names
                ]
                pool = same_group or [p for p in reserves if p.name not in used_reserve_names]
                if not pool:
                    break
                player_on = max(pool, key=lambda p: p.note)
                used_reserve_names.add(player_on.name)
                subs_on.append((player_on, sub_minutes[index], lineup.bands.get(player_off.name)))
                substitutions.append(
                    SubstitutionEvent(
                        club_name=club.name,
                        player_off=player_off.name,
                        player_on=player_on.name,
                        minute=sub_minutes[index],
                    )
                )

    minute_off_by_name = {sub.player_off: sub.minute for sub in substitutions}
    entries = [
        _SquadEntry(
            p, started=True, weight_multiplier=1.0, minute_off=minute_off_by_name.get(p.name), band=lineup.bands.get(p.name)
        )
        for p in starters
    ]
    entries += [
        _SquadEntry(p, started=False, weight_multiplier=SUB_EVENT_WEIGHT, minute_on=minute_on, band=band)
        for p, minute_on, band in subs_on
    ]
    return entries, substitutions, starter_injuries


def _generate_goals(club_name: str, squad: list[_SquadEntry], nb_goals: int) -> list[GoalEvent]:
    scorable = [e for e in squad if e.player.group != GOALKEEPER]
    if not scorable or nb_goals <= 0:
        return []

    scorer_weights = np.array(
        [
            SCORER_WEIGHT.get(e.player.poste, 0.0) * (e.player.note**GOAL_NOTE_EXPONENT) * e.weight_multiplier
            for e in scorable
        ]
    )
    if scorer_weights.sum() <= 0:
        scorer_weights = np.ones(len(scorable))

    goals: list[GoalEvent] = []
    for _ in range(nb_goals):
        scorer_entry = _weighted_choice(scorable, scorer_weights)
        minute = _random_minute(*scorer_entry.minute_range())
        penalty = random.random() < PENALTY_GOAL_PROBABILITY

        assist_name = None
        if not penalty and random.random() > UNASSISTED_GOAL_PROBABILITY:
            # Seul un joueur effectivement sur le terrain à cette minute peut
            # être crédité d'une passe décisive.
            assist_pool = [
                e
                for e in scorable
                if e.player.name != scorer_entry.player.name
                and e.minute_range()[0] <= minute <= e.minute_range()[1]
            ]
            if assist_pool:
                assist_weights = np.array(
                    [
                        ASSIST_WEIGHT.get(e.player.poste, 0.0) * (e.player.note**NOTE_EXPONENT) * e.weight_multiplier
                        for e in assist_pool
                    ]
                )
                if assist_weights.sum() > 0:
                    assist_name = _weighted_choice(assist_pool, assist_weights).player.name

        goals.append(
            GoalEvent(
                club_name=club_name,
                scorer=scorer_entry.player.name,
                assist=assist_name,
                minute=minute,
                penalty=penalty,
            )
        )

    return goals


def _weighted_choice(entries: list[_SquadEntry], weights: np.ndarray) -> _SquadEntry:
    probabilities = weights / weights.sum()
    index = np.random.choice(len(entries), p=probabilities)
    return entries[index]


def _build_stats(
    squad: list[_SquadEntry],
    lineup: Lineup,
    all_goals: list[GoalEvent],
    result: str,
    goals_conceded: int,
    starter_injuries: dict[str, tuple[bool, int, int]],
) -> tuple[list[PlayerMatchStat], list[CardEvent], list[InjuryEvent]]:
    goals_by_scorer: dict[str, int] = {}
    assists_by_player: dict[str, int] = {}
    for g in all_goals:
        goals_by_scorer[g.scorer] = goals_by_scorer.get(g.scorer, 0) + 1
        if g.assist:
            assists_by_player[g.assist] = assists_by_player.get(g.assist, 0) + 1

    stats = []
    cards: list[CardEvent] = []
    injuries: list[InjuryEvent] = []
    for entry in squad:
        player = entry.player
        goals = goals_by_scorer.get(player.name, 0)
        assists = assists_by_player.get(player.name, 0)
        yellow_cards, red_card_type = _draw_card()
        if entry.started:
            # déjà tirée dans _play_match_squad, avant les remplacements.
            injured, injury_duration, injury_minute = starter_injuries[player.name]
        else:
            injured, injury_duration = _draw_injury()
            injury_minute = _random_minute(*entry.minute_range()) if injured else 0
        rating = _rate_player(player, result, goals, assists, yellow_cards, red_card_type, goals_conceded)

        stats.append(
            PlayerMatchStat(
                player_name=player.name,
                club_name=lineup.club_name,
                poste=player.poste,
                started=entry.started,
                goals=goals,
                assists=assists,
                yellow_cards=yellow_cards,
                red_card_type=red_card_type,
                injured=injured,
                injury_duration=injury_duration,
                rating=rating,
                band=entry.band,
                age=player.age,
                nationalite=player.nationalite,
                note=player.note,
            )
        )
        if yellow_cards or red_card_type is not None:
            cards.append(
                CardEvent(
                    club_name=lineup.club_name,
                    player=player.name,
                    minute=_random_minute(*entry.minute_range()),
                    card_type=red_card_type or "yellow",
                )
            )
        if injured:
            injuries.append(InjuryEvent(club_name=lineup.club_name, player=player.name, minute=injury_minute))
    return stats, cards, injuries


def _draw_card() -> tuple[int, str | None]:
    r = random.random()
    if r < P_RED_DIRECT:
        return 0, "direct"
    r -= P_RED_DIRECT
    if r < P_SECOND_YELLOW_RED:
        return 2, "second_yellow"
    r -= P_SECOND_YELLOW_RED
    if r < P_SINGLE_YELLOW:
        return 1, None
    return 0, None


def _draw_injury() -> tuple[bool, int]:
    if random.random() < P_INJURY:
        return True, random.randint(INJURY_MIN_MATCHES, INJURY_MAX_MATCHES)
    return False, 0


def _generate_missed_penalties(sides: list[tuple[str, list[_SquadEntry]]]) -> list[PenaltyMissedEvent]:
    """Au plus un penalty manqué par match, tiré indépendamment du score : un
    tir au but raté n'a pas besoin d'un but marqué pour exister."""
    if random.random() >= P_MATCH_HAS_MISSED_PENALTY:
        return []
    club_name, squad = random.choice(sides)
    scorable = [e for e in squad if e.player.group != GOALKEEPER]
    if not scorable:
        return []
    weights = np.array([SCORER_WEIGHT.get(e.player.poste, 0.0) * e.weight_multiplier for e in scorable])
    if weights.sum() <= 0:
        weights = np.ones(len(scorable))
    taker = _weighted_choice(scorable, weights)
    minute = _random_minute(*taker.minute_range())
    return [PenaltyMissedEvent(club_name=club_name, player=taker.player.name, minute=minute)]


def _rate_player(
    player: Player,
    result: str,
    goals: int,
    assists: int,
    yellow_cards: int,
    red_card_type: str | None,
    goals_conceded: int,
) -> float:
    rating = BASE_RATING
    rating += {"victoire": 0.3, "nul": 0.0, "defaite": -0.3}[result]
    rating += 0.6 * goals + 0.4 * assists
    rating -= 0.3 * yellow_cards
    if red_card_type is not None:
        rating -= 1.0

    if player.group == GOALKEEPER:
        rating += 0.8 if goals_conceded == 0 else -0.15 * goals_conceded

    rating += random.gauss(0, RATING_NOISE_STD)
    return round(min(RATING_MAX, max(RATING_MIN, rating)), 1)


def collect_new_bans(events: MatchEvents) -> tuple[list[tuple[str, str, int]], list[tuple[str, str, int]]]:
    """Nouvelles suspensions/blessures déclenchées par ce match (à appliquer
    APRÈS avoir décrémenté les indisponibilités déjà en cours, voir
    `settle_trackers`)."""
    new_suspensions: list[tuple[str, str, int]] = []
    new_injuries: list[tuple[str, str, int]] = []
    for stat in events.home_lineup + events.away_lineup:
        if stat.red_card_type == "direct":
            new_suspensions.append((stat.club_name, stat.player_name, 2))
        elif stat.red_card_type == "second_yellow":
            new_suspensions.append((stat.club_name, stat.player_name, 1))
        if stat.injured:
            new_injuries.append((stat.club_name, stat.player_name, stat.injury_duration))
    return new_suspensions, new_injuries


def settle_trackers(
    suspensions: AvailabilityTracker,
    injuries: AvailabilityTracker,
    clubs_played: set[str],
    new_suspensions: list[tuple[str, str, int]],
    new_injuries: list[tuple[str, str, int]],
) -> None:
    """Décrémente les indisponibilités déjà en cours pour les clubs qui ont
    joué, PUIS applique les nouvelles (un rouge pris à ce match ne compte pas
    comme un match déjà manqué)."""
    suspensions.record_matchday(clubs_played)
    injuries.record_matchday(clubs_played)
    for club_name, player_name, nb_matches in new_suspensions:
        suspensions.apply_new_ban(club_name, player_name, nb_matches)
    for club_name, player_name, nb_matches in new_injuries:
        injuries.apply_new_ban(club_name, player_name, nb_matches)


def compute_leaderboards(matches: list) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Classements buteurs et passeurs à partir de tous les matchs joués
    (avec événements) transmis. Fonctionne pour n'importe quelle liste de
    Match, quel que soit le format de compétition d'où ils viennent."""
    goals: dict[tuple[str, str], int] = {}
    assists: dict[tuple[str, str], int] = {}

    for match in matches:
        if match.events is None:
            continue
        for stat in match.events.home_lineup + match.events.away_lineup:
            key = (stat.player_name, stat.club_name)
            if stat.goals:
                goals[key] = goals.get(key, 0) + stat.goals
            if stat.assists:
                assists[key] = assists.get(key, 0) + stat.assists

    buteurs = _leaderboard_df(goals, "Buts")
    passeurs = _leaderboard_df(assists, "Passes")
    return buteurs, passeurs


def _leaderboard_df(counts: dict[tuple[str, str], int], column: str) -> pd.DataFrame:
    rows = [{"Joueur": name, "Club": club, column: n} for (name, club), n in counts.items() if n > 0]
    df = pd.DataFrame(rows, columns=["Joueur", "Club", column])
    return df.sort_values(by=column, ascending=False).reset_index(drop=True)

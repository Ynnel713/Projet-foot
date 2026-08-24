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
NOTE_EXPONENT = 1.5  # amplifie l'effet de la qualité du joueur sur le tirage
UNASSISTED_GOAL_PROBABILITY = 0.25
SUB_EVENT_WEIGHT = 0.4  # poids réduit des entrants (moins de temps de jeu)

# --- Remplacements -----------------------------------------------------------
MIN_SUBSTITUTIONS = 3
MAX_SUBSTITUTIONS = 5

# --- Notes /10 -----------------------------------------------------------
BASE_RATING = 6.0
RATING_MIN = 3.0
RATING_MAX = 10.0
RATING_NOISE_STD = 0.4


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


@dataclass(frozen=True)
class GoalEvent:
    club_name: str
    scorer: str
    assist: str | None


@dataclass(frozen=True)
class SubstitutionEvent:
    club_name: str
    player_off: str
    player_on: str


@dataclass(frozen=True)
class MatchEvents:
    home_formation: str
    away_formation: str
    home_lineup: list[PlayerMatchStat]
    away_lineup: list[PlayerMatchStat]
    goals: list[GoalEvent] = field(default_factory=list)
    substitutions: list[SubstitutionEvent] = field(default_factory=list)


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
    home_squad, home_subs = _play_match_squad(home_club, home_lineup, unavailable_home)
    away_squad, away_subs = _play_match_squad(away_club, away_lineup, unavailable_away)

    goals = _generate_goals(home_club.name, home_squad, home_goals) + _generate_goals(
        away_club.name, away_squad, away_goals
    )

    home_result = _result(home_goals, away_goals)
    away_result = _result(away_goals, home_goals)

    home_stats = _build_stats(home_squad, home_lineup, goals, home_result, away_goals)
    away_stats = _build_stats(away_squad, away_lineup, goals, away_result, home_goals)

    return MatchEvents(
        home_formation=home_lineup.formation,
        away_formation=away_lineup.formation,
        home_lineup=home_stats,
        away_lineup=away_stats,
        goals=goals,
        substitutions=home_subs + away_subs,
    )


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


def _play_match_squad(
    club: Club, lineup: Lineup, unavailable: frozenset[str]
) -> tuple[list[_SquadEntry], list[SubstitutionEvent]]:
    """Titulaires (poids plein) + remplaçants entrés en jeu (poids réduit),
    et la liste des remplacements effectués (pour l'affichage)."""
    reserves = bench(club, lineup, unavailable)
    starters = list(lineup.players)

    substitutions: list[SubstitutionEvent] = []
    subs_on: list[Player] = []
    if reserves:
        outfield_starters = [p for p in starters if p.group != GOALKEEPER]
        nb_subs = min(len(outfield_starters), len(reserves), random.randint(MIN_SUBSTITUTIONS, MAX_SUBSTITUTIONS))
        candidates_off = list(outfield_starters)
        random.shuffle(candidates_off)
        used_reserve_names: set[str] = set()

        for player_off in candidates_off[:nb_subs]:
            same_group = [
                p for p in reserves if p.group == player_off.group and p.name not in used_reserve_names
            ]
            pool = same_group or [p for p in reserves if p.name not in used_reserve_names]
            if not pool:
                break
            player_on = max(pool, key=lambda p: p.note)
            used_reserve_names.add(player_on.name)
            subs_on.append(player_on)
            substitutions.append(
                SubstitutionEvent(club_name=club.name, player_off=player_off.name, player_on=player_on.name)
            )

    entries = [_SquadEntry(p, started=True, weight_multiplier=1.0) for p in starters]
    entries += [_SquadEntry(p, started=False, weight_multiplier=SUB_EVENT_WEIGHT) for p in subs_on]
    return entries, substitutions


def _generate_goals(club_name: str, squad: list[_SquadEntry], nb_goals: int) -> list[GoalEvent]:
    scorable = [e for e in squad if e.player.group != GOALKEEPER]
    if not scorable or nb_goals <= 0:
        return []

    scorer_weights = np.array(
        [SCORER_WEIGHT.get(e.player.poste, 0.0) * (e.player.note**NOTE_EXPONENT) * e.weight_multiplier for e in scorable]
    )
    if scorer_weights.sum() <= 0:
        scorer_weights = np.ones(len(scorable))

    goals: list[GoalEvent] = []
    for _ in range(nb_goals):
        scorer_entry = _weighted_choice(scorable, scorer_weights)

        assist_name = None
        if random.random() > UNASSISTED_GOAL_PROBABILITY:
            assist_pool = [e for e in scorable if e.player.name != scorer_entry.player.name]
            if assist_pool:
                assist_weights = np.array(
                    [
                        ASSIST_WEIGHT.get(e.player.poste, 0.0) * (e.player.note**NOTE_EXPONENT) * e.weight_multiplier
                        for e in assist_pool
                    ]
                )
                if assist_weights.sum() > 0:
                    assist_name = _weighted_choice(assist_pool, assist_weights).player.name

        goals.append(GoalEvent(club_name=club_name, scorer=scorer_entry.player.name, assist=assist_name))

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
) -> list[PlayerMatchStat]:
    goals_by_scorer: dict[str, int] = {}
    assists_by_player: dict[str, int] = {}
    for g in all_goals:
        goals_by_scorer[g.scorer] = goals_by_scorer.get(g.scorer, 0) + 1
        if g.assist:
            assists_by_player[g.assist] = assists_by_player.get(g.assist, 0) + 1

    stats = []
    for entry in squad:
        player = entry.player
        goals = goals_by_scorer.get(player.name, 0)
        assists = assists_by_player.get(player.name, 0)
        yellow_cards, red_card_type = _draw_card()
        injured, injury_duration = _draw_injury()
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
            )
        )
    return stats


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

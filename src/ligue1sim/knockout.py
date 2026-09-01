"""Tableau à élimination directe (bracket), avec exemptions pour les
effectifs qui ne sont pas une puissance de 2, et confrontations à 1, 2 ou 4
manches.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from ligue1sim.clubs import Club
from ligue1sim.events import AvailabilityTracker, collect_new_bans, settle_trackers
from ligue1sim.lineup import club_strength
from ligue1sim.schedule import Match
from ligue1sim.simulation import FormTracker, LeagueContext, simulate_match


@dataclass
class Tie:
    """Une confrontation du tableau. `away` est None uniquement pour une
    exemption ("bye") : `home` est alors qualifié d'office."""

    home: str
    away: str | None
    legs: list[Match] = field(default_factory=list)
    winner: str | None = None
    # True quand l'agrégat est resté à égalité après toutes les manches et
    # que le vainqueur a dû être départagé (voir `_resolve_tiebreak`) --
    # sans ça, l'écran ne montre qu'un score nul sans expliquer qui a gagné.
    decided_by_penalties: bool = False

    def __post_init__(self) -> None:
        if self.away is None:
            self.winner = self.home

    @property
    def is_bye(self) -> bool:
        return self.away is None

    @property
    def played(self) -> bool:
        return self.winner is not None

    def aggregate(self) -> tuple[int, int]:
        """Score agrégé (buts pour `home`, buts pour `away`) sur toutes les manches."""
        agg_home = sum(m.home_goals if m.home == self.home else m.away_goals for m in self.legs)
        agg_away = sum(m.away_goals if m.away == self.away else m.home_goals for m in self.legs)
        return agg_home, agg_away


@dataclass
class Round:
    number: int
    ties: list[Tie]

    @property
    def played(self) -> bool:
        return all(t.played for t in self.ties)


@dataclass
class Bracket:
    rounds: list[Round]

    @property
    def current_round(self) -> Round:
        return self.rounds[-1]

    @property
    def is_complete(self) -> bool:
        return len(self.current_round.ties) == 1 and self.current_round.played

    @property
    def champion(self) -> str | None:
        return self.current_round.ties[0].winner if self.is_complete else None


def generate_bracket(clubs: list[Club]) -> Bracket:
    """Construit le 1er tour du tableau, tête de série par note décroissante.

    Si l'effectif n'est pas une puissance de 2, les clubs les mieux notés
    sont exemptés du 1er tour (qualifiés d'office pour le tour 2).
    """
    if len(clubs) < 2:
        raise ValueError("Il faut au moins 2 clubs pour un tableau à élimination directe.")

    seeds = sorted(clubs, key=lambda c: -club_strength(c))
    bracket_size = _next_power_of_two(len(seeds))
    order = _seed_order(bracket_size)
    slots = [seeds[s - 1].name if s <= len(seeds) else None for s in order]

    ties = [Tie(home=slots[i], away=slots[i + 1]) for i in range(0, bracket_size, 2)]
    # Un bye ne peut survenir que côté "away" par construction de _seed_order
    # (le meilleur reste toujours dans slots[i]) : rien d'autre à corriger.
    return Bracket(rounds=[Round(number=1, ties=ties)])


def simulate_tie(
    tie: Tie,
    legs: int,
    clubs_by_name: dict[str, Club],
    context: LeagueContext,
    suspensions: AvailabilityTracker | None = None,
    injuries: AvailabilityTracker | None = None,
    form: FormTracker | None = None,
) -> None:
    """Simule une confrontation non encore jouée (`legs` manches).

    Chaque manche est un vrai match qu'un joueur suspendu/blessé peut
    manquer : les indisponibilités sont donc lues et mises à jour manche par
    manche, pas une fois pour toute la confrontation (voir simulation.simulate_journee
    pour la même séquence appliquée à une journée de championnat)."""
    if tie.played:
        return

    suspensions = suspensions if suspensions is not None else AvailabilityTracker()
    injuries = injuries if injuries is not None else AvailabilityTracker()

    home_club, away_club = clubs_by_name[tie.home], clubs_by_name[tie.away]
    for leg_index in range(legs):
        host, guest = (home_club, away_club) if leg_index % 2 == 0 else (away_club, home_club)
        unavailable_host = suspensions.unavailable_players(host.name) | injuries.unavailable_players(host.name)
        unavailable_guest = suspensions.unavailable_players(guest.name) | injuries.unavailable_players(guest.name)

        host_goals, guest_goals, events = simulate_match(host, guest, context, unavailable_host, unavailable_guest, form)
        tie.legs.append(Match(host.name, guest.name, host_goals, guest_goals, events))

        new_suspensions, new_injuries = ([], []) if events is None else collect_new_bans(events)
        settle_trackers(suspensions, injuries, {host.name, guest.name}, new_suspensions, new_injuries)

    agg_home, agg_away = tie.aggregate()
    if agg_home > agg_away:
        tie.winner = tie.home
    elif agg_away > agg_home:
        tie.winner = tie.away
    else:
        tie.winner = _resolve_tiebreak(home_club, away_club)
        tie.decided_by_penalties = True


def simulate_round(
    round_: Round,
    legs: int,
    clubs_by_name: dict[str, Club],
    context: LeagueContext,
    suspensions: AvailabilityTracker | None = None,
    injuries: AvailabilityTracker | None = None,
    form: FormTracker | None = None,
) -> None:
    suspensions = suspensions if suspensions is not None else AvailabilityTracker()
    injuries = injuries if injuries is not None else AvailabilityTracker()
    for tie in round_.ties:
        simulate_tie(tie, legs, clubs_by_name, context, suspensions, injuries, form)


def advance_round(bracket: Bracket) -> None:
    """Construit le tour suivant à partir des vainqueurs du tour courant."""
    current = bracket.current_round
    if not current.played:
        raise ValueError("Le tour courant n'est pas terminé.")
    if len(current.ties) == 1:
        return

    winners = [t.winner for t in current.ties]
    next_ties = [Tie(home=winners[i], away=winners[i + 1]) for i in range(0, len(winners), 2)]
    bracket.rounds.append(Round(number=current.number + 1, ties=next_ties))


def _resolve_tiebreak(home_club: Club, away_club: Club) -> str:
    """Égalité agrégée après toutes les manches : mini séance de tirs au
    but, tirage pondéré par l'écart de note (pas une nouvelle loi de
    Poisson, juste une probabilité logistique façon Elo)."""
    diff = (club_strength(home_club) - club_strength(away_club)) / 10
    p_home = 1 / (1 + 10 ** (-diff))
    return home_club.name if np.random.random() < p_home else away_club.name


def _next_power_of_two(n: int) -> int:
    size = 1
    while size < n:
        size *= 2
    return size


def _seed_order(size: int) -> list[int]:
    """Ordre de têtes de série standard d'un tableau à élimination directe
    (1 vs size, 2 vs size-1 en tour 1 pour un tableau non exempté, etc.),
    pour que les meilleures têtes de série ne se rencontrent qu'au plus tard."""
    if size == 1:
        return [1]
    previous = _seed_order(size // 2)
    order: list[int] = []
    for seed in previous:
        order.append(seed)
        order.append(size + 1 - seed)
    return order

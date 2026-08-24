"""Phase de groupes façon Coupe du Monde : poules de 4, les 2 premiers de
chaque poule se qualifient pour l'élimination directe.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from ligue1sim.clubs import Club
from ligue1sim.events import AvailabilityTracker
from ligue1sim.lineup import club_strength
from ligue1sim.schedule import Journee, generate_calendar
from ligue1sim.simulation import LeagueContext, simulate_journee
from ligue1sim.standings import compute_standings

GROUP_SIZE = 4
QUALIFIERS_PER_GROUP = 2


@dataclass
class Group:
    name: str
    clubs: list[Club]
    calendar: list[Journee]

    @property
    def is_complete(self) -> bool:
        return all(j.played for j in self.calendar)

    def standings(self) -> pd.DataFrame:
        return compute_standings(self.clubs, self.calendar)

    def qualified(self) -> list[Club]:
        clubs_by_name = {c.name: c for c in self.clubs}
        top_names = self.standings()["Club"].head(QUALIFIERS_PER_GROUP).tolist()
        return [clubs_by_name[name] for name in top_names]


def make_groups(clubs: list[Club], legs: int = 1) -> list[Group]:
    """Répartit les clubs en poules d'au plus 4, têtes de série par note
    décroissante ("chapeaux" façon Coupe du Monde), pour équilibrer le
    niveau de chaque poule. Si l'effectif n'est pas multiple de 4, les
    dernières poules ont 3 clubs plutôt que 4 (pas d'équipe fictive) :
    chacune joue quand même un mini-championnat complet et qualifie 2
    équipes, exactement comme les autres.
    """
    if len(clubs) < 2 * QUALIFIERS_PER_GROUP:
        raise ValueError(f"Il faut au moins {2 * QUALIFIERS_PER_GROUP} clubs pour une phase de groupes.")

    num_groups = -(-len(clubs) // GROUP_SIZE)  # arrondi à l'entier supérieur
    seeds = sorted(clubs, key=lambda c: -club_strength(c))
    buckets: list[list[Club]] = [[] for _ in range(num_groups)]
    for index, club in enumerate(seeds):
        buckets[index % num_groups].append(club)

    groups = []
    for index, group_clubs in enumerate(buckets):
        name = f"Groupe {chr(ord('A') + index)}"
        calendar = generate_calendar(group_clubs, legs=legs)
        groups.append(Group(name=name, clubs=group_clubs, calendar=calendar))
    return groups


def simulate_group_matchday(
    group: Group,
    matchday_index: int,
    context: LeagueContext,
    suspensions: AvailabilityTracker | None = None,
    injuries: AvailabilityTracker | None = None,
) -> None:
    """Simule la journée `matchday_index` (0-indexée) de la poule."""
    clubs_by_name = {c.name: c for c in group.clubs}
    simulate_journee(group.calendar[matchday_index], clubs_by_name, context, suspensions, injuries)


def qualified_from_groups(groups: list[Group]) -> list[Club]:
    qualifiers: list[Club] = []
    for group in groups:
        qualifiers.extend(group.qualified())
    return qualifiers

"""État d'une Compétition Perso (championnat libre, élimination directe, ou
championnat + élimination façon Coupe du Monde), persisté dans
st.session_state.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import streamlit as st

from ligue1sim.clubs import Club
from ligue1sim.groups import Group, make_groups, qualified_from_groups, simulate_group_matchday
from ligue1sim.knockout import Bracket, advance_round, generate_bracket, simulate_round
from ligue1sim.season import Season
from ligue1sim.simulation import LeagueContext

_SESSION_KEY = "custom_competition"


class CompetitionFormat:
    LEAGUE = "LEAGUE"
    KNOCKOUT = "KNOCKOUT"
    HYBRID = "HYBRID"


@dataclass
class CustomCompetition:
    """Orchestration d'une compétition perso ; le comportement dépend de
    `format` (championnat pur / élimination directe / groupes + élimination).
    """

    format: str
    legs: int
    clubs: list[Club]

    context: LeagueContext = field(init=False)
    season: Season | None = field(default=None, init=False)
    bracket: Bracket | None = field(default=None, init=False)
    groups: list[Group] | None = field(default=None, init=False)
    groups_matchday: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        self.context = LeagueContext.from_clubs(self.clubs)
        if self.format == CompetitionFormat.LEAGUE:
            self.season = Season("Compétition Perso", self.clubs, legs=self.legs)
        elif self.format == CompetitionFormat.KNOCKOUT:
            self.bracket = generate_bracket(self.clubs)
        elif self.format == CompetitionFormat.HYBRID:
            self.groups = make_groups(self.clubs, legs=self.legs)
        else:
            raise ValueError(f"Format de compétition inconnu : {self.format}")

    # --- phase de groupes (HYBRID uniquement) ---

    @property
    def groups_complete(self) -> bool:
        return self.groups is not None and all(g.is_complete for g in self.groups)

    def simulate_groups_matchday(self) -> None:
        """Simule la prochaine journée de chaque poule (certaines poules ont
        parfois moins de journées que d'autres si leurs effectifs diffèrent ;
        on ignore simplement celles déjà terminées)."""
        for group in self.groups:
            if self.groups_matchday < len(group.calendar):
                simulate_group_matchday(group, self.groups_matchday, self.context)
        self.groups_matchday += 1

    def start_knockout_from_groups(self) -> None:
        qualifiers = qualified_from_groups(self.groups)
        self.bracket = generate_bracket(qualifiers)

    # --- phase à élimination directe (KNOCKOUT, et HYBRID après les groupes) ---

    def simulate_bracket_round(self) -> None:
        clubs_by_name = {c.name: c for c in self.clubs}
        simulate_round(self.bracket.current_round, self.legs, clubs_by_name, self.context)

    def advance_bracket_round(self) -> None:
        advance_round(self.bracket)

    # --- état global ---

    @property
    def is_over(self) -> bool:
        if self.format == CompetitionFormat.LEAGUE:
            return self.season.is_season_over
        return self.bracket is not None and self.bracket.is_complete

    @property
    def champion(self) -> str | None:
        if self.format == CompetitionFormat.LEAGUE:
            return self.season.standings().iloc[0]["Club"] if self.season.is_season_over else None
        return self.bracket.champion if self.bracket else None


def get_custom_competition() -> CustomCompetition | None:
    return st.session_state.get(_SESSION_KEY)


def start_custom_competition(format: str, legs: int, clubs: list[Club]) -> None:
    st.session_state[_SESSION_KEY] = CustomCompetition(format=format, legs=legs, clubs=clubs)


def clear_custom_competition() -> None:
    st.session_state.pop(_SESSION_KEY, None)

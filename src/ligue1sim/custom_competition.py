"""État d'une Compétition Perso (championnat libre, élimination directe, ou
championnat + élimination façon Coupe du Monde), persisté dans
st.session_state.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

import streamlit as st

from ligue1sim.clubs import Club
from ligue1sim.events import AvailabilityTracker
from ligue1sim.groups import Group, make_groups, qualified_from_groups, simulate_group_matchday
from ligue1sim.knockout import Bracket, advance_round, generate_bracket, simulate_round
from ligue1sim.schedule import Match
from ligue1sim.season import Season
from ligue1sim.simulation import FormTracker, LeagueContext

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
    # Poules déjà construites (ex. tirage par chapeau de la Ligue des
    # Champions, voir champions_league.py), utilisées telles quelles au lieu
    # du tirage par force `groups.make_groups` -- ignoré si `format` n'est
    # pas HYBRID. None (par défaut) : comportement inchangé pour la
    # Compétition Perso.
    preset_groups: list[Group] | None = None
    # Nom d'affichage (ex. "Ligue des Champions") utilisé par app.py à la
    # place de "Compétition Perso" dans les titres d'écran -- None (par
    # défaut) : comportement inchangé.
    label: str | None = None
    # Nombre de manches par confrontation à élimination directe (hors
    # finale), et pour la finale seule -- distincts de `legs` (qui reste la
    # phase de championnat/poules) depuis l'assistant Compétition Perso du
    # 28/09/2026 ("championnat + élimination" / "élimination directe" avec un
    # réglage séparé par phase). `None` (par défaut) : reprend `legs`, donc
    # AUCUN changement de comportement pour tout appelant existant
    # (Ligue des Champions, Coupe du Monde, anciens appels) qui ne les passe
    # pas -- voir `_knockout_legs`/`_final_legs`.
    knockout_legs: int | None = None
    final_legs: int | None = None
    # Construit le tableau à partir des poules terminées, à la place de `generate_bracket(qualifiés)` (têtes de série par force) :
    # Ligue des Champions (barrages puis 8es avec les 8 premiers de la phase de ligue). None : comportement inchangé.
    knockout_builder: Callable[[list[Group]], Bracket] | None = None
    # True : la « phase de poules » est la PHASE DE LIGUE de la Ligue des Champions (un seul classement de 36 clubs, 8 journées) ;
    # l'UI affiche alors les zones de qualification (8 directs, 16 barragistes) au lieu de « 2 premiers de chaque poule ».
    league_phase: bool = False

    context: LeagueContext = field(init=False)
    season: Season | None = field(default=None, init=False)
    bracket: Bracket | None = field(default=None, init=False)
    groups: list[Group] | None = field(default=None, init=False)
    groups_matchday: int = field(default=0, init=False)
    suspensions: AvailabilityTracker = field(init=False)
    injuries: AvailabilityTracker = field(init=False)
    form: FormTracker = field(init=False)

    def __post_init__(self) -> None:
        self.context = LeagueContext.from_clubs(self.clubs)
        if self.format == CompetitionFormat.LEAGUE:
            self.season = Season("Compétition Perso", self.clubs, legs=self.legs)
            # même objet que la saison : pas de double comptabilité des
            # indisponibilités/forme pour un format LEAGUE.
            self.suspensions = self.season.suspensions
            self.injuries = self.season.injuries
            self.form = self.season.form
        elif self.format == CompetitionFormat.KNOCKOUT:
            self.suspensions = AvailabilityTracker()
            self.injuries = AvailabilityTracker()
            self.form = FormTracker()
            self.bracket = generate_bracket(self.clubs)
        elif self.format == CompetitionFormat.HYBRID:
            # une seule instance pour toute la durée de la compétition : elle
            # survit telle quelle à la transition poules -> élimination
            # (start_knockout_from_groups ne la recrée pas).
            self.suspensions = AvailabilityTracker()
            self.injuries = AvailabilityTracker()
            self.form = FormTracker()
            self.groups = self.preset_groups if self.preset_groups is not None else make_groups(self.clubs, legs=self.legs)
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
                simulate_group_matchday(
                    group, self.groups_matchday, self.context, self.suspensions, self.injuries, self.form
                )
        self.groups_matchday += 1

    def start_knockout_from_groups(self) -> None:
        if self.knockout_builder is not None:
            self.bracket = self.knockout_builder(self.groups)
            return
        qualifiers = qualified_from_groups(self.groups)
        self.bracket = generate_bracket(qualifiers)

    # --- phase à élimination directe (KNOCKOUT, et HYBRID après les groupes) ---

    @property
    def _round_legs(self) -> int:
        """Nombre de manches à appliquer au tour COURANT du tableau : celui
        de la finale si un seul tie reste à jouer (voir `Bracket.is_complete`,
        même détection), celui des autres tours sinon."""
        is_final_round = len(self.bracket.current_round.ties) == 1
        knockout_legs = self.knockout_legs if self.knockout_legs is not None else self.legs
        if is_final_round:
            return self.final_legs if self.final_legs is not None else knockout_legs
        return knockout_legs

    def simulate_bracket_round(self) -> None:
        clubs_by_name = {c.name: c for c in self.clubs}
        simulate_round(
            self.bracket.current_round, self._round_legs, clubs_by_name, self.context, self.suspensions, self.injuries, self.form
        )

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

    @property
    def all_matches(self) -> list[Match]:
        """Tous les matchs déjà générés, quel que soit le format/la phase --
        pour les classements buteurs/passeurs (voir events.compute_leaderboards)."""
        matches: list[Match] = []
        if self.season is not None:
            matches += self.season.all_matches
        if self.groups is not None:
            for group in self.groups:
                matches += [m for journee in group.calendar for m in journee.matches]
        if self.bracket is not None:
            for round_ in self.bracket.rounds:
                for tie in round_.ties:
                    matches += tie.legs
        return matches


def get_custom_competition() -> CustomCompetition | None:
    return st.session_state.get(_SESSION_KEY)


def start_custom_competition(format: str, legs: int, clubs: list[Club]) -> None:
    st.session_state[_SESSION_KEY] = CustomCompetition(format=format, legs=legs, clubs=clubs)


def store_custom_competition(competition: CustomCompetition) -> None:
    """Stocke une `CustomCompetition` déjà construite ailleurs (ex. tirage
    par chapeau de la Ligue des Champions, voir champions_league.py) --
    même emplacement de session que `start_custom_competition`."""
    st.session_state[_SESSION_KEY] = competition


def clear_custom_competition() -> None:
    st.session_state.pop(_SESSION_KEY, None)

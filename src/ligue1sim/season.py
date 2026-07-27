"""État de la saison en cours, persisté dans st.session_state pour Streamlit."""

from __future__ import annotations

import streamlit as st

from ligue1sim.clubs import Club, load_clubs
from ligue1sim.schedule import Journee, generate_calendar
from ligue1sim.simulation import LeagueContext, simulate_journee
from ligue1sim.standings import compute_standings

CLUBS_PATH = "data/clubs.xlsx"
_SEASON_KEY = "season"
_CHAMPIONNAT_KEY = "championnat"


class Season:
    """Encapsule le calendrier, la progression et le classement d'une saison."""

    def __init__(self, championnat: str, clubs: list[Club], legs: int = 2):
        self.championnat = championnat
        self.clubs = clubs
        self.clubs_by_name = {c.name: c for c in clubs}
        self.context = LeagueContext.from_clubs(clubs)
        self.calendar: list[Journee] = generate_calendar(clubs, legs=legs)
        self.current_journee_number = 1

    @property
    def total_journees(self) -> int:
        return len(self.calendar)

    @property
    def current_journee(self) -> Journee:
        return self.calendar[self.current_journee_number - 1]

    @property
    def is_season_over(self) -> bool:
        return self.current_journee_number >= self.total_journees and self.current_journee.played

    def simulate_current_journee(self) -> None:
        simulate_journee(self.current_journee, self.clubs_by_name, self.context)

    def next_journee(self) -> None:
        if self.current_journee_number < self.total_journees:
            self.current_journee_number += 1

    def standings(self):
        return compute_standings(self.clubs, self.calendar)


def get_selected_championnat() -> str | None:
    """Retourne le championnat choisi sur l'écran d'accueil, ou None si aucun."""
    return st.session_state.get(_CHAMPIONNAT_KEY)


def select_championnat(championnat: str) -> None:
    """Choisit un championnat et démarre une saison fraîche pour celui-ci."""
    st.session_state[_CHAMPIONNAT_KEY] = championnat
    st.session_state.pop(_SEASON_KEY, None)


def go_to_home() -> None:
    """Revient à l'écran d'accueil (efface le championnat et la saison en cours)."""
    st.session_state.pop(_CHAMPIONNAT_KEY, None)
    st.session_state.pop(_SEASON_KEY, None)


def get_season() -> Season:
    """Retourne la saison stockée en session, en la créant si besoin."""
    if _SEASON_KEY not in st.session_state:
        championnat = get_selected_championnat()
        st.session_state[_SEASON_KEY] = Season(championnat, load_clubs(CLUBS_PATH, championnat))
    return st.session_state[_SEASON_KEY]


def reset_season() -> None:
    """Réinitialise la saison du championnat en cours (retour à J1, plus aucun score)."""
    championnat = get_selected_championnat()
    st.session_state[_SEASON_KEY] = Season(championnat, load_clubs(CLUBS_PATH, championnat))

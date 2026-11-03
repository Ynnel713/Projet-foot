"""Feuille de match d'une manche d'élimination directe (route `/pitch`, refonte UI lot 4) :
l'UI envoie le domicile de la manche, inversé au retour par rapport au tie.
Appelle les fonctions de vue directement (pas de TestClient, voir tests/test_competitions.py)."""

import pytest
from fastapi import HTTPException

from ligue1sim.clubs import load_clubs
from ligue1sim.custom_competition import CompetitionFormat, CustomCompetition
from ligue1sim.season import CLUBS_PATH

from api import store
from api.routers.competitions import get_pitch_view, simulate_bracket_round


@pytest.fixture
def played_two_leg_tie():
    clubs = load_clubs(CLUBS_PATH, "Ligue 1")[:4]
    competition = CustomCompetition(format=CompetitionFormat.KNOCKOUT, legs=2, clubs=clubs, label="Test")
    comp_id = store.create(competition)
    simulate_bracket_round(comp_id)
    tie = competition.bracket.rounds[0].ties[0]
    return comp_id, tie


def test_return_leg_found_with_its_own_home_club(played_two_leg_tie):
    comp_id, tie = played_two_leg_tie
    retour = tie.legs[1]
    assert retour.home == tie.away  # le retour inverse bien les rôles

    sheet = get_pitch_view(comp_id, retour.home, retour.away, round_number=1, leg=1)

    assert (sheet.home, sheet.away) == (retour.home, retour.away)
    assert (sheet.home_goals, sheet.away_goals) == (retour.home_goals, retour.away_goals)


def test_first_leg_still_found_and_unknown_pair_still_404(played_two_leg_tie):
    comp_id, tie = played_two_leg_tie
    aller = tie.legs[0]

    sheet = get_pitch_view(comp_id, aller.home, aller.away, round_number=1, leg=0)
    assert (sheet.home_goals, sheet.away_goals) == (aller.home_goals, aller.away_goals)

    with pytest.raises(HTTPException) as unknown:
        get_pitch_view(comp_id, tie.home, "Nope FC", round_number=1, leg=1)
    assert unknown.value.status_code == 404

"""Feuille de match d'une manche d'élimination directe (route `/pitch`, refonte UI lot 4) :
l'UI envoie le domicile de la manche, inversé au retour par rapport au tie.
Appelle les fonctions de vue directement (pas de TestClient, voir tests/test_competitions.py)."""

import pytest
from fastapi import HTTPException

from ligue1sim.clubs import load_clubs
from ligue1sim.custom_competition import CompetitionFormat, CustomCompetition
from ligue1sim.season import CLUBS_PATH

from api import store
from api.routers.competitions import advance_bracket, get_bracket, get_pitch_view, simulate_bracket_leg, simulate_bracket_round


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


def test_simulate_leg_one_leg_at_a_time_then_conflict():
    clubs = load_clubs(CLUBS_PATH, "Ligue 1")[:4]
    competition = CustomCompetition(format=CompetitionFormat.KNOCKOUT, legs=2, clubs=clubs, label="Test")
    comp_id = store.create(competition)

    first = simulate_bracket_leg(comp_id)
    assert (first.current_legs, first.current_legs_played) == (2, 1)
    assert not first.rounds[0].played
    tie = first.rounds[0].ties[0]
    assert len(tie.legs) == 1 and tie.winner is None
    assert (tie.home_goals, tie.away_goals) == (tie.legs[0].home_goals, tie.legs[0].away_goals)  # cumul provisoire = score de l'aller

    with pytest.raises(HTTPException) as early:
        advance_bracket(comp_id)
    assert early.value.status_code == 409

    second = simulate_bracket_leg(comp_id)
    assert second.rounds[0].played and second.current_legs_played == 2
    assert all(t.winner for t in second.rounds[0].ties)

    with pytest.raises(HTTPException) as done:
        simulate_bracket_leg(comp_id)
    assert done.value.status_code == 409

    assert len(advance_bracket(comp_id).rounds) == 2
    assert get_bracket(comp_id).current_legs_played == 0


def test_simulate_round_after_first_leg_finishes_the_round():
    clubs = load_clubs(CLUBS_PATH, "Ligue 1")[:4]
    competition = CustomCompetition(format=CompetitionFormat.KNOCKOUT, legs=2, clubs=clubs, label="Test")
    comp_id = store.create(competition)
    simulate_bracket_leg(comp_id)
    out = simulate_bracket_round(comp_id)
    assert out.rounds[0].played and all(len(t.legs) == 2 for t in out.rounds[0].ties)


def test_final_with_two_legs_while_other_rounds_have_one():
    clubs = load_clubs(CLUBS_PATH, "Ligue 1")[:4]
    competition = CustomCompetition(format=CompetitionFormat.KNOCKOUT, legs=1, final_legs=2, clubs=clubs, label="Test")
    comp_id = store.create(competition)

    semi = simulate_bracket_leg(comp_id)  # manche unique : le tour est joué d'un coup
    assert semi.current_legs == 1 and semi.rounds[0].played
    final = advance_bracket(comp_id)
    assert final.current_legs == 2 and final.current_legs_played == 0

    first = simulate_bracket_leg(comp_id)
    assert not first.rounds[-1].played and first.current_legs_played == 1 and first.champion is None
    second = simulate_bracket_leg(comp_id)
    assert second.is_complete and second.champion is not None

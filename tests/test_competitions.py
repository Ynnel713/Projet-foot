"""Tests de l'ajout à api/routers/competitions.py pour l'écran équipe de la
PWA (get_roster, 26/09/2026) -- le reste du routeur n'a pas de couverture
existante, pas dans le périmètre de cette tâche (voir le rapport de tâche).
Appelle les fonctions de vue directement (pas de TestClient : httpx2 n'est
pas une dépendance du projet)."""

import pytest
from fastapi import HTTPException

from ligue1sim.clubs import load_clubs
from ligue1sim.custom_competition import CustomCompetition
from ligue1sim.season import CLUBS_PATH

from api import store
from api.routers.competitions import get_club_fixtures, get_roster


@pytest.fixture
def competition_id():
    clubs = load_clubs(CLUBS_PATH, "Ligue 1")
    competition = CustomCompetition(format="LEAGUE", legs=2, clubs=clubs, label="Ligue 1")
    return store.create(competition), clubs


def test_get_roster_returns_the_requested_clubs_squad(competition_id):
    comp_id, clubs = competition_id
    club = clubs[0]

    out = get_roster(comp_id, club.name)

    assert out.club == club.name
    assert len(out.players) == len(club.players)


def test_get_roster_404_for_unknown_club(competition_id):
    comp_id, _ = competition_id

    with pytest.raises(HTTPException) as exc_info:
        get_roster(comp_id, "Club Qui N'Existe Pas")

    assert exc_info.value.status_code == 404


def test_get_roster_404_for_unknown_competition():
    with pytest.raises(HTTPException) as exc_info:
        get_roster("id-inconnu", "AJ Auxerre")

    assert exc_info.value.status_code == 404


def test_fixtures_fresh_season_lists_every_match_unplayed(competition_id):
    comp_id, clubs = competition_id
    out = get_club_fixtures(comp_id, clubs[0].name)
    assert len(out.fixtures) == 2 * (len(clubs) - 1)
    assert [f.journee for f in out.fixtures] == sorted(f.journee for f in out.fixtures)
    assert not any(f.played or f.result for f in out.fixtures) and out.form == []
    assert {f.home_away for f in out.fixtures} == {"home", "away"}
    assert all(clubs[0].name in (f.home, f.away) and f.opponent not in (clubs[0].name,) for f in out.fixtures)


def test_fixtures_result_and_form_after_matchdays(competition_id):
    comp_id, clubs = competition_id
    name = clubs[0].name
    season = store.get(comp_id).season
    for _ in range(7):
        season.simulate_current_journee()
        season.next_journee()
    out = get_club_fixtures(comp_id, name)
    played = [f for f in out.fixtures if f.played]
    assert len(played) == 7 and len(out.form) == 5
    assert out.form == [f.result for f in played][-5:]
    for f in played:
        mine, theirs = (f.home_goals, f.away_goals) if f.home_away == "home" else (f.away_goals, f.home_goals)
        assert f.result == ("W" if mine > theirs else "L" if mine < theirs else "D")


def test_fixtures_is_read_only(competition_id):
    comp_id, clubs = competition_id
    season = store.get(comp_id).season
    season.simulate_current_journee()
    before = (season.current_journee_number, [(m.home_goals, m.away_goals) for j in season.calendar for m in j.matches])
    get_club_fixtures(comp_id, clubs[0].name)
    assert before == (season.current_journee_number, [(m.home_goals, m.away_goals) for j in season.calendar for m in j.matches])


def test_fixtures_errors(competition_id):
    comp_id, _ = competition_id
    with pytest.raises(HTTPException) as unknown_club:
        get_club_fixtures(comp_id, "Club Qui N'Existe Pas")
    assert unknown_club.value.status_code == 404
    with pytest.raises(HTTPException) as unknown_comp:
        get_club_fixtures("id-inconnu", "AJ Auxerre")
    assert unknown_comp.value.status_code == 404
    clubs = load_clubs(CLUBS_PATH, "Ligue 1")[:4]
    knockout_id = store.create(CustomCompetition(format="KNOCKOUT", legs=2, clubs=clubs, label="Coupe"))
    with pytest.raises(HTTPException) as no_calendar:
        get_club_fixtures(knockout_id, clubs[0].name)
    assert no_calendar.value.status_code == 409

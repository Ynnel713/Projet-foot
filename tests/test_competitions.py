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
from api.routers.competitions import get_roster


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

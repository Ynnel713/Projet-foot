import pandas as pd
import pytest

from ligue1sim.clubs import (
    ClubDataError,
    list_championnats,
    load_all_clubs,
    load_clubs,
)

DATA_PATH = "data/joueurs.xlsx"


def test_list_championnats_excludes_autres_clubs_and_returns_the_eight_leagues():
    assert list_championnats(DATA_PATH) == [
        "Bundesliga",
        "Eredivisie",
        "Jupiler Pro League",
        "LaLiga",
        "Liga Portugal",
        "Ligue 1",
        "Premier League",
        "Serie A",
    ]


@pytest.mark.parametrize(
    "championnat,expected_club_count",
    [
        ("Premier League", 20),
        ("LaLiga", 20),
        ("Bundesliga", 18),
        ("Serie A", 20),
        ("Ligue 1", 18),
        ("Liga Portugal", 18),
        ("Jupiler Pro League", 18),
        ("Eredivisie", 18),
    ],
)
def test_load_clubs_returns_expected_club_count(championnat, expected_club_count):
    clubs = load_clubs(DATA_PATH, championnat)

    assert len(clubs) == expected_club_count
    assert len({c.name for c in clubs}) == expected_club_count


def test_load_clubs_populates_players_with_valid_notes_and_full_squads():
    clubs = load_clubs(DATA_PATH, "Ligue 1")

    for club in clubs:
        assert len(club.players) >= 11
        assert all(0 <= p.note <= 100 for p in club.players)
        assert all(p.club == club.name for p in club.players)
        assert all(p.championnat == "Ligue 1" for p in club.players)


def test_load_clubs_rejects_odd_number_of_clubs(tmp_path):
    df = pd.DataFrame(
        {
            "Championnat": ["TEST"] * 33,
            "Club": ["A"] * 11 + ["B"] * 11 + ["C"] * 11,
            "Prénom": [f"P{i}" for i in range(33)],
            "Nom": [f"N{i}" for i in range(33)],
            "Nationalité": ["France"] * 33,
            "Âge": [25] * 33,
            "Poste": ["Central Midfield"] * 33,
            "Note /100": [70] * 33,
        }
    )
    path = tmp_path / "joueurs.xlsx"
    df.to_excel(path, index=False)

    with pytest.raises(ClubDataError):
        load_clubs(path, "TEST")


def test_load_clubs_rejects_understaffed_club(tmp_path):
    df = pd.DataFrame(
        {
            "Championnat": ["TEST"] * 22 + ["TEST"] * 3,
            "Club": ["A"] * 11 + ["B"] * 11 + ["C"] * 3,
            "Prénom": [f"P{i}" for i in range(25)],
            "Nom": [f"N{i}" for i in range(25)],
            "Nationalité": ["France"] * 25,
            "Âge": [25] * 25,
            "Poste": ["Central Midfield"] * 25,
            "Note /100": [70] * 25,
        }
    )
    path = tmp_path / "joueurs.xlsx"
    df.to_excel(path, index=False)

    with pytest.raises(ClubDataError):
        load_clubs(path, "TEST")


def test_load_all_clubs_includes_autres_clubs_and_covers_the_whole_file():
    options = load_all_clubs(DATA_PATH)

    championnats = {o.championnat for o in options}
    assert "Autres clubs" in championnats
    assert {
        "Premier League",
        "LaLiga",
        "Bundesliga",
        "Serie A",
        "Ligue 1",
        "Liga Portugal",
        "Jupiler Pro League",
        "Eredivisie",
    } <= championnats

    ligue1_clubs = [o for o in options if o.championnat == "Ligue 1"]
    assert len(ligue1_clubs) == 18
    assert all(len(o.players) >= 11 for o in ligue1_clubs)


def test_club_option_as_club_carries_players_through():
    options = load_all_clubs(DATA_PATH)
    option = next(o for o in options if o.championnat == "Ligue 1")

    club = option.as_club()

    assert club.name == option.name
    assert club.players == option.players


def test_load_clubs_rejects_out_of_range_note(tmp_path):
    df = pd.DataFrame(
        {
            "Championnat": ["TEST"] * 22,
            "Club": ["A"] * 11 + ["B"] * 11,
            "Prénom": [f"P{i}" for i in range(22)],
            "Nom": [f"N{i}" for i in range(22)],
            "Nationalité": ["France"] * 22,
            "Âge": [25] * 22,
            "Poste": ["Central Midfield"] * 22,
            "Note /100": [70] * 21 + [150],
        }
    )
    path = tmp_path / "joueurs.xlsx"
    df.to_excel(path, index=False)

    with pytest.raises(ClubDataError):
        load_clubs(path, "TEST")


def test_load_clubs_allows_missing_nom_for_mononym_players(tmp_path):
    df = pd.DataFrame(
        {
            "Championnat": ["TEST"] * 22,
            "Club": ["A"] * 11 + ["B"] * 11,
            "Prénom": ["Vitinha"] + [f"P{i}" for i in range(21)],
            "Nom": [None] + [f"N{i}" for i in range(21)],
            "Nationalité": ["France"] * 22,
            "Âge": [25] * 22,
            "Poste": ["Central Midfield"] * 22,
            "Note /100": [70] * 22,
        }
    )
    path = tmp_path / "joueurs.xlsx"
    df.to_excel(path, index=False)

    clubs = load_clubs(path, "TEST")
    vitinha = next(p for c in clubs for p in c.players if p.prenom == "Vitinha")
    assert vitinha.nom == ""
    assert vitinha.name == "Vitinha"

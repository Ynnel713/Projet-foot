import pandas as pd
import pytest

from ligue1sim.clubs import ClubDataError, list_championnats, load_all_clubs, load_clubs

DATA_PATH = "data/clubs.xlsx"


def test_list_championnats_excludes_autres_and_returns_the_five_leagues():
    assert list_championnats(DATA_PATH) == [
        "BUNDESLIGA",
        "LIGA",
        "LIGUE 1",
        "PREMIER LEAGUE",
        "SERIE A",
    ]


@pytest.mark.parametrize(
    "championnat,expected_count",
    [("LIGUE 1", 18), ("BUNDESLIGA", 18), ("LIGA", 20), ("SERIE A", 20), ("PREMIER LEAGUE", 20)],
)
def test_load_clubs_returns_expected_club_count(championnat, expected_count):
    clubs = load_clubs(DATA_PATH, championnat)

    assert len(clubs) == expected_count
    assert all(0 <= c.rating <= 100 for c in clubs)
    assert len({c.name for c in clubs}) == expected_count


def test_load_clubs_rejects_odd_number_of_clubs(tmp_path):
    df = pd.DataFrame(
        {
            "Championnat": ["TEST"] * 3,
            "Club": ["A", "B", "C"],
            "Note_globale": [70, 60, 50],
        }
    )
    path = tmp_path / "clubs.xlsx"
    df.to_excel(path, index=False)

    with pytest.raises(ClubDataError):
        load_clubs(path, "TEST")


def test_load_all_clubs_includes_autres_and_covers_the_whole_file():
    options = load_all_clubs(DATA_PATH)

    championnats = {o.championnat for o in options}
    assert "AUTRES" in championnats
    assert {"LIGUE 1", "BUNDESLIGA", "LIGA", "SERIE A", "PREMIER LEAGUE"} <= championnats
    assert all(0 <= o.rating <= 100 for o in options)

    # cohérent avec le nombre de clubs par championnat déjà validé ailleurs
    assert len([o for o in options if o.championnat == "LIGUE 1"]) == 18


def test_load_clubs_rejects_duplicate_club_names(tmp_path):
    df = pd.DataFrame(
        {
            "Championnat": ["TEST"] * 4,
            "Club": ["A", "B", "A", "C"],
            "Note_globale": [70, 60, 55, 50],
        }
    )
    path = tmp_path / "clubs.xlsx"
    df.to_excel(path, index=False)

    with pytest.raises(ClubDataError):
        load_clubs(path, "TEST")

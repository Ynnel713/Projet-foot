from ligue1sim.clubs import Club
from ligue1sim.schedule import Journee, Match
from ligue1sim.standings import compute_standings

CLUBS = [
    Club(name="A"),
    Club(name="B"),
    Club(name="C"),
]

CALENDAR = [
    Journee(1, [Match("A", "B", 2, 1)]),
    Journee(2, [Match("B", "C", 0, 0)]),
    Journee(3, [Match("C", "A", 1, 3)]),
]


def test_compute_standings_points_and_goal_stats():
    df = compute_standings(CLUBS, CALENDAR)
    row_a = df[df["Club"] == "A"].iloc[0]

    assert row_a["J"] == 2
    assert row_a["G"] == 2
    assert row_a["N"] == 0
    assert row_a["P"] == 0
    assert row_a["BP"] == 5
    assert row_a["BC"] == 2
    assert row_a["Diff"] == 3
    assert row_a["Pts"] == 6


def test_compute_standings_ranking_order():
    df = compute_standings(CLUBS, CALENDAR)

    assert df["Club"].tolist() == ["A", "B", "C"]


def test_compute_standings_ignores_unplayed_matches():
    calendar_with_unplayed = CALENDAR + [Journee(4, [Match("A", "C")])]
    df = compute_standings(CLUBS, calendar_with_unplayed)

    row_a = df[df["Club"] == "A"].iloc[0]
    assert row_a["J"] == 2

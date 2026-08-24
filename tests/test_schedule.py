import pytest

from ligue1sim.clubs import Club
from ligue1sim.schedule import generate_calendar


def _make_clubs(n: int) -> list[Club]:
    return [Club(name=f"Club {i}") for i in range(n)]


@pytest.mark.parametrize("n_clubs,expected_journees,expected_matches", [(18, 34, 9), (20, 38, 10)])
def test_calendar_has_expected_number_of_journees_and_matches(
    n_clubs, expected_journees, expected_matches
):
    calendar = generate_calendar(_make_clubs(n_clubs))

    assert len(calendar) == expected_journees
    assert all(len(journee.matches) == expected_matches for journee in calendar)


@pytest.mark.parametrize("n_clubs", [18, 20])
def test_each_club_plays_everyone_home_and_away_exactly_once(n_clubs):
    calendar = generate_calendar(_make_clubs(n_clubs))

    home_count = {}
    away_count = {}
    pair_meetings = {}

    for journee in calendar:
        for match in journee.matches:
            home_count[match.home] = home_count.get(match.home, 0) + 1
            away_count[match.away] = away_count.get(match.away, 0) + 1
            pair = tuple(sorted((match.home, match.away)))
            pair_meetings[pair] = pair_meetings.get(pair, 0) + 1

    expected_games_per_club = n_clubs - 1
    assert all(count == expected_games_per_club for count in home_count.values())
    assert all(count == expected_games_per_club for count in away_count.values())
    assert len(pair_meetings) == n_clubs * (n_clubs - 1) // 2
    assert all(count == 2 for count in pair_meetings.values())


def test_generate_calendar_supports_odd_number_of_clubs_with_byes():
    clubs = _make_clubs(5)
    calendar = generate_calendar(clubs, legs=1)

    assert len(calendar) == 5  # round-robin sur 6 entités (5 clubs + bye) -> 5 journées
    total_matches = sum(len(j.matches) for j in calendar)
    assert total_matches == 5 * 4 // 2  # chaque club joue les 4 autres une fois

    byes_per_club = {c.name: 0 for c in clubs}
    for journee in calendar:
        playing = {name for m in journee.matches for name in (m.home, m.away)}
        for c in clubs:
            if c.name not in playing:
                byes_per_club[c.name] += 1

    assert all(count == 1 for count in byes_per_club.values())


@pytest.mark.parametrize("legs,expected_meetings_per_pair", [(1, 1), (2, 2), (4, 4)])
def test_legs_controls_number_of_meetings_per_pair(legs, expected_meetings_per_pair):
    calendar = generate_calendar(_make_clubs(4), legs=legs)

    pair_meetings = {}
    for journee in calendar:
        for match in journee.matches:
            pair = tuple(sorted((match.home, match.away)))
            pair_meetings[pair] = pair_meetings.get(pair, 0) + 1

    assert all(count == expected_meetings_per_pair for count in pair_meetings.values())


def test_generate_calendar_rejects_invalid_legs():
    with pytest.raises(ValueError):
        generate_calendar(_make_clubs(4), legs=3)


def test_generate_calendar_rejects_too_few_clubs():
    with pytest.raises(ValueError):
        generate_calendar(_make_clubs(1))

import pytest

from ligue1sim.clubs import Club
from ligue1sim.groups import make_groups, qualified_from_groups, simulate_group_matchday
from ligue1sim.players import Player
from ligue1sim.simulation import LeagueContext


def _player(note: float, name: str) -> Player:
    return Player(
        prenom=name, nom="", nationalite="France", age=25,
        poste="MC", note=note, club=name, championnat="TEST",
    )


def _make_clubs(n: int) -> list[Club]:
    return [Club(name=f"Club {i}", players=[_player(100 - i, f"Club {i}")]) for i in range(n)]  # Club 0 = meilleure note


def test_make_groups_rejects_too_few_clubs():
    with pytest.raises(ValueError):
        make_groups(_make_clubs(3))


@pytest.mark.parametrize("n_clubs,expected_group_count", [(8, 2), (9, 3), (16, 4), (6, 2)])
def test_make_groups_splits_into_expected_number_of_groups(n_clubs, expected_group_count):
    groups = make_groups(_make_clubs(n_clubs))

    assert len(groups) == expected_group_count
    total_clubs = sum(len(g.clubs) for g in groups)
    assert total_clubs == n_clubs
    assert all(len(g.clubs) >= 2 for g in groups)


def test_make_groups_seeds_top_clubs_into_different_groups():
    groups = make_groups(_make_clubs(8))  # 2 groupes -> tetes de serie 1 et 2 separees

    group_of = {c.name: g.name for g in groups for c in g.clubs}
    assert group_of["Club 0"] != group_of["Club 1"]


def test_group_qualification_returns_top_two_after_full_simulation():
    clubs = _make_clubs(4)
    groups = make_groups(clubs)
    group = groups[0]
    context = LeagueContext.from_clubs(clubs)

    for i in range(len(group.calendar)):
        simulate_group_matchday(group, i, context)

    assert group.is_complete
    qualified = group.qualified()
    assert len(qualified) == 2
    assert all(c in group.clubs for c in qualified)


def test_qualified_from_groups_aggregates_two_per_group():
    clubs = _make_clubs(9)  # 3 groupes de 3
    groups = make_groups(clubs)
    context = LeagueContext.from_clubs(clubs)

    for group in groups:
        for i in range(len(group.calendar)):
            simulate_group_matchday(group, i, context)

    qualifiers = qualified_from_groups(groups)
    assert len(qualifiers) == 2 * len(groups)

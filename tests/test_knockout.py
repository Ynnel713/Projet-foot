import pytest

from ligue1sim.clubs import Club
from ligue1sim.knockout import advance_round, generate_bracket, simulate_round, simulate_tie
from ligue1sim.lineup import club_strength
from ligue1sim.players import Player
from ligue1sim.simulation import LeagueContext


def _player(note: float, name: str) -> Player:
    return Player(
        prenom=name, nom="", nationalite="France", age=25,
        poste="MC", note=note, club=name, championnat="TEST",
    )


def _make_clubs(n: int) -> list[Club]:
    return [Club(name=f"Club {i}", players=[_player(50 + i, f"Club {i}")]) for i in range(n)]


def test_generate_bracket_size_and_byes_for_non_power_of_two():
    clubs = _make_clubs(6)  # bracket de 8 -> 2 exemptions pour les 2 meilleures notes
    bracket = generate_bracket(clubs)

    round1 = bracket.rounds[0]
    assert len(round1.ties) == 4
    byes = [t for t in round1.ties if t.is_bye]
    assert len(byes) == 2
    assert all(t.played for t in byes)

    top2_names = {c.name for c in sorted(clubs, key=lambda c: -club_strength(c))[:2]}
    assert {t.home for t in byes} == top2_names


def test_generate_bracket_power_of_two_has_no_byes():
    bracket = generate_bracket(_make_clubs(8))

    assert len(bracket.rounds[0].ties) == 4
    assert not any(t.is_bye for t in bracket.rounds[0].ties)


def test_generate_bracket_rejects_less_than_two_clubs():
    with pytest.raises(ValueError):
        generate_bracket(_make_clubs(1))


@pytest.mark.parametrize("legs", [1, 2, 4])
def test_simulate_tie_produces_correct_number_of_legs_and_a_winner(legs):
    clubs = _make_clubs(2)
    by_name = {c.name: c for c in clubs}
    context = LeagueContext.from_clubs(clubs)
    tie = generate_bracket(clubs).rounds[0].ties[0]

    simulate_tie(tie, legs, by_name, context)

    assert len(tie.legs) == legs
    assert tie.winner in {tie.home, tie.away}


def test_full_tournament_reaches_a_champion_with_byes():
    clubs = _make_clubs(6)
    by_name = {c.name: c for c in clubs}
    context = LeagueContext.from_clubs(clubs)
    bracket = generate_bracket(clubs)

    while not bracket.is_complete:
        simulate_round(bracket.current_round, 1, by_name, context)
        advance_round(bracket)

    assert bracket.champion in by_name
    assert len(bracket.rounds) == 3  # 6 clubs -> tableau de 8 -> 3 tours

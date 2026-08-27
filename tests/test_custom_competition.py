from ligue1sim.clubs import Club
from ligue1sim.custom_competition import CompetitionFormat, CustomCompetition
from ligue1sim.players import Player


def _player(note: float, name: str) -> Player:
    return Player(
        prenom=name, nom="", nationalite="France", age=25,
        poste="MC", note=note, club=name, championnat="TEST",
    )


def _make_clubs(n: int) -> list[Club]:
    return [Club(name=f"Club {i}", players=[_player(100 - i, f"Club {i}")]) for i in range(n)]


def test_league_format_plays_out_like_a_season():
    competition = CustomCompetition(format=CompetitionFormat.LEAGUE, legs=1, clubs=_make_clubs(5))

    assert not competition.is_over
    while not competition.is_over:
        competition.season.simulate_current_journee()
        competition.season.next_journee()

    assert competition.champion in {c.name for c in competition.clubs}


def test_knockout_format_reaches_a_champion_with_byes():
    competition = CustomCompetition(format=CompetitionFormat.KNOCKOUT, legs=1, clubs=_make_clubs(6))

    assert not competition.is_over
    while not competition.is_over:
        competition.simulate_bracket_round()
        competition.advance_bracket_round()

    assert competition.champion in {c.name for c in competition.clubs}


def test_hybrid_format_transitions_from_groups_to_knockout():
    clubs = _make_clubs(9)  # 3 poules de 3
    competition = CustomCompetition(format=CompetitionFormat.HYBRID, legs=1, clubs=clubs)

    assert not competition.groups_complete
    while not competition.groups_complete:
        competition.simulate_groups_matchday()

    competition.start_knockout_from_groups()
    assert competition.bracket is not None
    qualifiers_in_bracket = {t.home for t in competition.bracket.rounds[0].ties} | {
        t.away for t in competition.bracket.rounds[0].ties if t.away is not None
    }
    assert len(qualifiers_in_bracket) == 2 * len(competition.groups)

    while not competition.is_over:
        competition.simulate_bracket_round()
        competition.advance_bracket_round()

    qualified_names = {c.name for g in competition.groups for c in g.qualified()}
    assert competition.champion in qualified_names

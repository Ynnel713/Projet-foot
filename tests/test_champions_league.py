from ligue1sim.champions_league import draw_pools, load_champions_league_clubs, start_champions_league
from ligue1sim.custom_competition import CompetitionFormat

DATA_PATH = "data/joueurs.xlsx"


def test_load_champions_league_clubs_returns_the_36_qualified_clubs():
    clubs = load_champions_league_clubs(DATA_PATH)

    assert len(clubs) == 36
    assert len({c.name for c in clubs}) == 36
    assert all(len(c.players) >= 11 for c in clubs)


def test_draw_pools_builds_nine_pools_of_four():
    groups = draw_pools(DATA_PATH)

    assert len(groups) == 9
    assert all(len(g.clubs) == 4 for g in groups)
    all_names = [c.name for g in groups for c in g.clubs]
    assert len(all_names) == 36
    assert len(set(all_names)) == 36  # aucun club dans deux poules


def test_draw_pools_puts_exactly_one_club_per_pot_in_each_pool():
    from ligue1sim.champions_league import _read_pots

    pots = _read_pots(DATA_PATH)
    club_to_pot = {name: pot for pot, names in pots.items() for name in names}

    groups = draw_pools(DATA_PATH)

    for group in groups:
        pots_in_group = sorted(club_to_pot[c.name] for c in group.clubs)
        assert pots_in_group == [1, 2, 3, 4]


def test_start_champions_league_returns_a_ready_to_simulate_hybrid_competition():
    competition = start_champions_league(DATA_PATH, legs=1)

    assert competition.format == CompetitionFormat.HYBRID
    assert len(competition.clubs) == 36
    assert len(competition.groups) == 9
    assert not competition.groups_complete

    competition.simulate_groups_matchday()
    assert competition.groups_matchday == 1


def test_champions_league_can_be_simulated_end_to_end_to_a_champion():
    competition = start_champions_league(DATA_PATH, legs=1)

    while not competition.groups_complete:
        competition.simulate_groups_matchday()
    competition.start_knockout_from_groups()

    # 9 poules * top 2 = 18 qualifiés -> tableau de 32 (14 exemptés au 1er tour).
    assert len(competition.bracket.current_round.ties) == 16

    while not competition.is_over:
        competition.simulate_bracket_round()
        if not competition.is_over:
            competition.advance_bracket_round()

    assert competition.champion is not None
    assert competition.champion in {c.name for c in competition.clubs}

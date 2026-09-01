from ligue1sim.custom_competition import CompetitionFormat
from ligue1sim.world_cup import draw_pools, qualified_teams, start_world_cup

DATA_PATH = "data/joueurs.xlsx"


def test_qualified_teams_returns_the_32_strongest_selections():
    teams = qualified_teams(DATA_PATH)

    assert len(teams) == 32
    assert len({t.name for t in teams}) == 32
    assert all(len(t.players) >= 11 for t in teams)


def test_draw_pools_builds_eight_pools_of_four():
    groups = draw_pools(DATA_PATH)

    assert len(groups) == 8
    assert all(len(g.clubs) == 4 for g in groups)
    all_names = [c.name for g in groups for c in g.clubs]
    assert len(all_names) == 32
    assert len(set(all_names)) == 32  # aucune sélection dans deux groupes


def test_start_world_cup_returns_a_ready_to_simulate_hybrid_competition():
    competition = start_world_cup(DATA_PATH)

    assert competition.format == CompetitionFormat.HYBRID
    assert len(competition.clubs) == 32
    assert len(competition.groups) == 8
    assert not competition.groups_complete
    assert competition.label == "Coupe du Monde"

    competition.simulate_groups_matchday()
    assert competition.groups_matchday == 1


def test_world_cup_can_be_simulated_end_to_end_to_a_champion():
    competition = start_world_cup(DATA_PATH)

    while not competition.groups_complete:
        competition.simulate_groups_matchday()
    competition.start_knockout_from_groups()

    # 8 groupes * top 2 = 16 qualifiés -> tableau de 16, aucun exempt.
    assert len(competition.bracket.current_round.ties) == 8

    while not competition.is_over:
        competition.simulate_bracket_round()
        if not competition.is_over:
            competition.advance_bracket_round()

    assert competition.champion is not None
    assert competition.champion in {c.name for c in competition.clubs}

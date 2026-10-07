import collections

from ligue1sim.clubs import Club
from ligue1sim.custom_competition import CompetitionFormat
from ligue1sim.nations import confederation
from ligue1sim.players import Player
from ligue1sim.world_cup import NB_POOLS, _attempt_draw, _group_uefa_caps, draw_pools, qualified_teams, start_world_cup

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


class TestConfederationBalance:
    """Équilibre des confédérations dans le tirage (retour utilisateur du
    29/09/2026 -- un groupe à 4 sélections UEFA constaté en jeu, voir
    docstring de world_cup.py)."""

    def test_group_uefa_caps_sum_to_the_real_uefa_count_and_stay_evenly_spread(self):
        caps = _group_uefa_caps(20)

        assert len(caps) == NB_POOLS
        assert sum(caps) == 20
        assert max(caps) - min(caps) <= 1  # jamais un groupe très favorisé par rapport aux autres

    def test_group_uefa_caps_handle_a_multiple_of_the_pool_count(self):
        caps = _group_uefa_caps(16)

        assert caps == [2] * NB_POOLS

    def _synthetic_club(self, name: str) -> Club:
        return Club(
            name=name,
            players=[Player(prenom=name, nom="", nationalite="?", age=25, poste="MC", note=70.0, club=name, championnat="TEST")],
        )

    def test_attempt_draw_never_exceeds_the_uefa_cap_or_duplicates_a_non_uefa_confederation(self):
        # 4 chapeaux de 8, dont un très majoritairement UEFA (6/8) --
        # reproduit la situation qui faisait échouer un tirage chapeau par
        # chapeau sans retour en arrière global (voir _attempt_draw).
        confeds: dict[str, str] = {}
        pots: list[list[Club]] = []
        pot_confeds = [
            ["UEFA"] * 6 + ["CAF", "CONMEBOL"],
            ["UEFA"] * 5 + ["CAF", "CONMEBOL", "AFC"],
            ["UEFA"] * 5 + ["CAF", "CONMEBOL", "CONCACAF"],
            ["UEFA"] * 4 + ["CAF", "CONMEBOL", "CONCACAF", "AFC"],
        ]
        for pot_index, confed_list in enumerate(pot_confeds):
            pot: list[Club] = []
            for team_index, confed in enumerate(confed_list):
                name = f"pot{pot_index}_team{team_index}"
                club = self._synthetic_club(name)
                confeds[name] = confed
                pot.append(club)
            pots.append(pot)

        uefa_count = sum(1 for c in confeds.values() if c == "UEFA")  # 20, comme sur le vivier réel

        found = False
        for _ in range(50):
            caps = _group_uefa_caps(uefa_count)
            buckets = _attempt_draw(pots, confeds, caps)
            if buckets is not None:
                found = True
                break
        assert found, "aucune tentative n'a abouti sur 50 essais"

        for group_teams in buckets:
            group_confeds = [confeds[c.name] for c in group_teams]
            counts = collections.Counter(group_confeds)
            assert counts.get("UEFA", 0) <= max(caps) + 1  # jamais un groupe hors de tout plafond raisonnable
            for confed, n in counts.items():
                if confed != "UEFA":
                    assert n == 1, f"{confed} en double dans un groupe"

    def test_draw_pools_never_duplicates_a_non_uefa_confederation_on_real_data(self):
        for _ in range(10):
            groups = draw_pools(DATA_PATH)
            for g in groups:
                confs = [confederation(DATA_PATH, c.name) for c in g.clubs]
                counts = collections.Counter(confs)
                for confed, n in counts.items():
                    if confed != "UEFA":
                        assert n == 1, f"{g.name}: {confed} en double ({confs})"

    def test_draw_pools_keeps_uefa_close_to_the_tightest_achievable_cap_on_real_data(self):
        qualified = qualified_teams(DATA_PATH)
        uefa_count = sum(1 for t in qualified if confederation(DATA_PATH, t.name) == "UEFA")
        tightest_cap = -(-uefa_count // NB_POOLS)  # ceil

        for _ in range(10):
            groups = draw_pools(DATA_PATH)
            for g in groups:
                uefa_in_group = sum(1 for c in g.clubs if confederation(DATA_PATH, c.name) == "UEFA")
                assert uefa_in_group <= tightest_cap, f"{g.name}: {uefa_in_group} UEFA (plafond {tightest_cap})"

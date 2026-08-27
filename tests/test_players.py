from ligue1sim.players import (
    ASSIST_WEIGHT,
    ATTACKER,
    DEFENDER,
    GOALKEEPER,
    MIDFIELDER,
    POSITION_GROUP,
    SCORER_WEIGHT,
    Player,
    best_distance_to_group,
    nearest_distance_to_group,
    position_group,
    poste_distance,
)

ALL_POSTE_TAGS = [
    "GK",
    "DC",
    "LB",
    "RB",
    "MDC",
    "MC",
    "MOC",
    "AG",
    "AD",
    "SA",
    "BU",
    "ATT",
]


def test_every_known_poste_has_a_position_group():
    for poste in ALL_POSTE_TAGS:
        assert position_group(poste) in {GOALKEEPER, DEFENDER, MIDFIELDER, ATTACKER}


def test_every_known_poste_has_scorer_and_assist_weights():
    for poste in ALL_POSTE_TAGS:
        assert poste in SCORER_WEIGHT
        assert poste in ASSIST_WEIGHT


def test_goalkeeper_has_zero_scorer_and_assist_weight():
    assert SCORER_WEIGHT["GK"] == 0.0
    assert ASSIST_WEIGHT["GK"] == 0.0


def test_attackers_weighted_higher_than_defenders_for_scoring():
    assert SCORER_WEIGHT["BU"] > SCORER_WEIGHT["DC"]


def test_unknown_poste_falls_back_to_midfielder():
    assert position_group("Sweeper") == MIDFIELDER


def test_player_name_and_group():
    p = Player(
        prenom="Kylian",
        nom="Mbappé",
        nationalite="France",
        age=27,
        poste="BU",
        note=98.6,
        club="Real Madrid",
        championnat="LaLiga",
    )
    assert p.name == "Kylian Mbappé"
    assert p.group == ATTACKER


def test_player_with_empty_nom_uses_prenom_only():
    p = Player(
        prenom="Vitinha",
        nom="",
        nationalite="Portugal",
        age=26,
        poste="MDC",
        note=95.0,
        club="Paris Saint-Germain",
        championnat="Ligue 1",
    )
    assert p.name == "Vitinha"


def test_position_group_mapping_is_exhaustive_dict_too():
    assert set(POSITION_GROUP.keys()) == set(ALL_POSTE_TAGS)


def test_player_defaults_to_no_secondary_postes():
    p = Player(
        prenom="Kylian",
        nom="Mbappé",
        nationalite="France",
        age=27,
        poste="BU",
        note=98.6,
        club="Real Madrid",
        championnat="LaLiga",
    )
    assert p.poste_secondaire == ()


def test_player_can_declare_secondary_postes():
    p = Player(
        prenom="Kylian",
        nom="Mbappé",
        nationalite="France",
        age=27,
        poste="BU",
        note=98.6,
        club="Real Madrid",
        championnat="LaLiga",
        poste_secondaire=("AG", "AD"),
    )
    assert p.poste_secondaire == ("AG", "AD")


class TestBestDistanceToGroup:
    def test_falls_back_to_secondary_poste_when_primary_is_too_far(self):
        # Un DC pur est à 2 crans de l'attaque, mais avec "AD" en poste
        # secondaire, il est à 0 cran (poste natif de ATT).
        assert best_distance_to_group(("DC",), ATTACKER) == 2
        assert best_distance_to_group(("DC", "AD"), ATTACKER) == 0

    def test_picks_the_minimum_across_all_postes(self):
        # MC seul est à 2 crans de la défense ; en ajoutant AG (à 1 cran via
        # LB), le minimum doit l'emporter.
        assert best_distance_to_group(("MC",), DEFENDER) == 2
        assert best_distance_to_group(("AG",), DEFENDER) == 1
        assert best_distance_to_group(("MC", "AG"), DEFENDER) == 1

    def test_returns_none_when_no_poste_reaches_the_group(self):
        assert best_distance_to_group(("GK",), ATTACKER) is None


class TestPosteAdjacency:
    def test_same_poste_has_zero_distance(self):
        assert poste_distance("AG", "AG") == 0

    def test_full_back_is_one_step_from_matching_wing(self):
        assert poste_distance("LB", "AG") == 1
        assert poste_distance("RB", "AD") == 1

    def test_centre_back_is_far_from_wingers(self):
        # DC -> LB -> AG : jamais un dépannage direct.
        assert poste_distance("DC", "AG") == 2

    def test_goalkeeper_is_unreachable_from_any_outfield_poste(self):
        assert poste_distance("DC", "GK") is None
        assert poste_distance("BU", "GK") is None

    def test_every_known_poste_has_zero_distance_to_its_own_group(self):
        for poste in ALL_POSTE_TAGS:
            if poste == "GK":
                continue
            assert nearest_distance_to_group(poste, position_group(poste)) == 0

    def test_nearest_distance_to_group_picks_the_closest_matching_poste(self):
        # AG touche à la fois le milieu (via MC/MOC) et l'attaque (poste
        # natif) en 1 pas.
        assert nearest_distance_to_group("AG", MIDFIELDER) == 1
        assert nearest_distance_to_group("AG", ATTACKER) == 0

    def test_goalkeeper_has_no_distance_to_any_outfield_group(self):
        for group in (DEFENDER, MIDFIELDER, ATTACKER):
            assert nearest_distance_to_group("GK", group) is None

from ligue1sim.players import (
    ASSIST_WEIGHT,
    ATTACKER,
    DEFENDER,
    GOALKEEPER,
    MIDFIELDER,
    POSITION_GROUP,
    SCORER_WEIGHT,
    Player,
    position_group,
)

ALL_TRANSFERMARKT_POSTES = [
    "Goalkeeper",
    "Centre-Back",
    "Left-Back",
    "Right-Back",
    "Defensive Midfield",
    "Central Midfield",
    "Attacking Midfield",
    "Left Midfield",
    "Right Midfield",
    "Left Winger",
    "Right Winger",
    "Second Striker",
    "Centre-Forward",
    "Striker",
]


def test_every_known_poste_has_a_position_group():
    for poste in ALL_TRANSFERMARKT_POSTES:
        assert position_group(poste) in {GOALKEEPER, DEFENDER, MIDFIELDER, ATTACKER}


def test_every_known_poste_has_scorer_and_assist_weights():
    for poste in ALL_TRANSFERMARKT_POSTES:
        assert poste in SCORER_WEIGHT
        assert poste in ASSIST_WEIGHT


def test_goalkeeper_has_zero_scorer_and_assist_weight():
    assert SCORER_WEIGHT["Goalkeeper"] == 0.0
    assert ASSIST_WEIGHT["Goalkeeper"] == 0.0


def test_attackers_weighted_higher_than_defenders_for_scoring():
    assert SCORER_WEIGHT["Centre-Forward"] > SCORER_WEIGHT["Centre-Back"]


def test_unknown_poste_falls_back_to_midfielder():
    assert position_group("Sweeper") == MIDFIELDER


def test_player_name_and_group():
    p = Player(
        prenom="Kylian",
        nom="Mbappé",
        nationalite="France",
        age=27,
        poste="Centre-Forward",
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
        poste="Defensive Midfield",
        note=95.0,
        club="Paris Saint-Germain",
        championnat="Ligue 1",
    )
    assert p.name == "Vitinha"


def test_position_group_mapping_is_exhaustive_dict_too():
    assert set(POSITION_GROUP.keys()) == set(ALL_TRANSFERMARKT_POSTES)

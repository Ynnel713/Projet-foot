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
    weighted_attributes,
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


class TestWeightedAttributes:
    """weighted_attributes (28/09/2026, décision utilisateur -- voir
    _RAW_IMPORTANCE) : seuls les attributs jugés pertinents pour `poste`
    (importance 1=utile ou 2=fondamentale) entrent dans la moyenne de
    référence ET sont recalés vers `note` -- répartis INVERSEMENT à leur
    importance (fondamental corrigé 2x moins qu'utile). Les autres ("notes
    annexes") sont rendus tels quels, jamais modifiés. Sans `poste` connu,
    ou si aucun attribut n'est marqué, rien n'est recalé."""

    def test_returns_falsy_attributes_unchanged(self):
        assert weighted_attributes({}, note=80.0) == {}
        assert weighted_attributes(None, note=80.0) is None

    def test_without_poste_nothing_is_marked_so_nothing_is_rescaled(self):
        # Aucune table de pertinence sans `poste` -- rien de "pertinent",
        # donc rien à recaler : les attributs bruts ressortent inchangés.
        result = weighted_attributes({"Pace": 60, "Passing": 80}, note=90.0)
        assert result == {"Pace": 60, "Passing": 80}

    def test_unknown_poste_also_leaves_everything_unchanged(self):
        result = weighted_attributes({"Pace": 60, "Passing": 80}, note=90.0, poste="???")
        assert result == {"Pace": 60, "Passing": 80}

    def test_attributes_absent_from_the_table_for_this_poste_are_never_touched(self):
        # "AG" (ailier) : Marking n'est marqué pour aucun poste offensif --
        # note annexe, jamais recalée, même quand d'autres attributs du même
        # joueur le sont largement (Pace, marqué "fondamental" pour AG).
        result = weighted_attributes({"Pace": 60, "Marking": 40}, note=90.0, poste="AG")
        assert result["Marking"] == 40

    def test_correction_is_shared_inversely_to_importance(self):
        # "AG" : Pace = fondamental (2), Determination = utile (1), Marking
        # = note annexe (0, exclue). Moyenne pondérée des deux marqués =
        # (60*2+60*1)/3 = 60, écart à note=80 -> 20 à répartir. La correction
        # par point d'importance est 60/2=30 (voir _RAW_IMPORTANCE : 2
        # attributs marqués, gap total = 20*3 = 60) : Determination (poids 1)
        # absorbe toute cette unité (+30), Pace (poids 2) seulement la
        # moitié (+15) -- deux fois moins de correction pour l'attribut
        # fondamental, comme demandé.
        result = weighted_attributes({"Pace": 60, "Determination": 60, "Marking": 60}, note=80.0, poste="AG")
        assert result == {"Pace": 75, "Determination": 90, "Marking": 60}
        # La moyenne pondérée des deux attributs recalés retombe exactement sur `note`.
        assert (result["Pace"] * 2 + result["Determination"] * 1) / 3 == 80.0

    def test_clips_rescaled_values_to_the_0_99_range(self):
        # "BU" (buteur) : Finishing = fondamental (2). Moyenne (95) déjà
        # proche de note=99 mais la correction pousserait au-delà de 99 sans
        # bornage.
        result = weighted_attributes({"Finishing": 95}, note=99.0, poste="BU")
        assert result["Finishing"] == 99

    def test_gordon_like_profile_stays_close_to_its_true_ceiling(self):
        # Cas réel (retour utilisateur du 28/09/2026) : un ailier avec
        # Moyenne joueur (82) nettement au-dessus de sa moyenne brute
        # pondérée -- même situation qu'Anthony Gordon. Dribbling/Pace
        # (fondamentaux, 85 bruts, déjà son plafond réel) ne doivent
        # PAS finir à 99 : la correction, répartie inversement à
        # l'importance, doit les laisser nettement sous le plafond.
        attrs = {
            "Dribbling": 85, "Pace": 85, "Determination": 45,  # fondamental/fondamental/utile
            "Marking": 40, "Tackling": 55, "Heading": 35,  # notes annexes pour un ailier
        }
        result = weighted_attributes(attrs, note=82.0, poste="AG")
        assert result["Dribbling"] < 90
        assert result["Pace"] < 90
        # Notes annexes : rigoureusement inchangées.
        assert result["Marking"] == 40
        assert result["Tackling"] == 55
        assert result["Heading"] == 35

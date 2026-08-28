import pytest

from ligue1sim.clubs import Club
from ligue1sim.lineup import (
    DEFAULT_RATING,
    FORMATIONS,
    bench,
    club_strength,
    parse_formation,
    pick_best_formation,
    select_best_xi,
)
from ligue1sim.players import Player


def _player(poste: str, note: float, name: str, poste_secondaire: tuple[str, ...] = ()) -> Player:
    return Player(
        prenom=name,
        nom="",
        nationalite="France",
        age=25,
        poste=poste,
        note=note,
        club="Test FC",
        championnat="TEST",
        poste_secondaire=poste_secondaire,
    )


def _full_squad(note: float = 70.0) -> list[Player]:
    """Un effectif standard : 3 GK, 8 DEF, 8 MID (varié), 8 ATT (varié)."""
    squad = [_player("GK", note, f"gk{i}") for i in range(3)]
    squad += [_player("DC", note, f"cb{i}") for i in range(4)]
    squad += [_player("LB", note, f"lb{i}") for i in range(2)]
    squad += [_player("RB", note, f"rb{i}") for i in range(2)]
    squad += [_player("MC", note, f"cm{i}") for i in range(4)]
    squad += [_player("MDC", note, f"dm{i}") for i in range(2)]
    squad += [_player("MOC", note, f"am{i}") for i in range(2)]
    squad += [_player("AG", note, f"lw{i}") for i in range(2)]
    squad += [_player("AD", note, f"rw{i}") for i in range(2)]
    squad += [_player("BU", note, f"cf{i}") for i in range(4)]
    return squad


def test_select_best_xi_respects_formation_quotas():
    # Postes exacts du 4-4-2 (onglet "Dispositifs tactiques") : GK, LB, DC,
    # DC, RB, MC ou MDC (x2), AD, AG, BU, BU.
    club = Club(name="Test FC", players=_full_squad())
    lineup = select_best_xi(club, "4-4-2")

    assert len(lineup.players) == 11
    postes = [p.poste for p in lineup.players]
    assert postes.count("GK") == 1
    assert postes.count("LB") == 1
    assert postes.count("DC") == 2
    assert postes.count("RB") == 1
    assert postes.count("AD") == 1
    assert postes.count("AG") == 1
    assert postes.count("BU") == 2
    assert postes.count("MC") + postes.count("MDC") == 2


def test_select_best_xi_picks_highest_notes_within_each_group():
    players = _full_squad(note=50.0)
    players.append(_player("DC", 99.0, "star_cb"))
    club = Club(name="Test FC", players=players)

    lineup = select_best_xi(club, "4-3-3")

    assert any(p.name == "star_cb" for p in lineup.players)


def test_select_best_xi_excludes_unavailable_players():
    club = Club(name="Test FC", players=_full_squad())
    lineup_full = select_best_xi(club, "4-4-2")
    a_starter = lineup_full.players[0].name

    lineup_without = select_best_xi(club, "4-4-2", unavailable=frozenset({a_starter}))

    assert a_starter not in {p.name for p in lineup_without.players}
    assert len(lineup_without.players) == 11  # backfill comble le trou


def test_select_best_xi_backfills_when_a_group_is_short():
    # Aucun gardien du tout : le poste GK reste vide, backfill par le reste.
    players = [p for p in _full_squad() if p.group != "GK"]
    club = Club(name="Test FC", players=players)

    lineup = select_best_xi(club, "4-4-2")

    assert len(lineup.players) == 11
    assert all(p.group != "GK" for p in lineup.players)


def test_select_best_xi_degrades_gracefully_with_tiny_squad():
    club = Club(name="Test FC", players=[_player("MC", 70.0, "only")])

    lineup = select_best_xi(club, "4-3-3")

    assert len(lineup.players) == 1
    assert lineup.rating == 70.0


def test_select_best_xi_falls_back_to_default_rating_with_no_eligible_players():
    club = Club(name="Test FC", players=[])

    lineup = select_best_xi(club, "4-3-3")

    assert lineup.players == []
    assert lineup.rating == DEFAULT_RATING


def test_pick_best_formation_favors_squad_shape():
    # Un seul vrai buteur (BU) dans l'effectif -> devrait éviter les
    # dispositifs qui réclament deux BU (4-4-2, 3-5-2, voir "Dispositifs
    # tactiques"), qui forceraient un dépannage hors poste sur la 2e place
    # d'attaquant, au profit d'un dispositif qui n'en réclame qu'un.
    players = [_player("GK", 70.0, "gk0")]
    players += [_player("DC", 70.0, f"cb{i}") for i in range(2)]
    players += [_player("LB", 70.0, "lb0")]
    players += [_player("RB", 70.0, "rb0")]
    players += [_player("MC", 70.0, f"cm{i}") for i in range(2)]
    players += [_player("MDC", 70.0, f"dm{i}") for i in range(2)]
    players += [_player("MOC", 70.0, "am0")]
    players += [_player("AG", 70.0, "lw0")]
    players += [_player("AD", 70.0, "rw0")]
    players += [_player("BU", 90.0, "star_striker")]
    club = Club(name="One Striker FC", players=players)

    best = pick_best_formation(club)

    assert best.formation not in {"4-4-2", "3-5-2"}


def test_club_strength_matches_best_formation_rating():
    club = Club(name="Test FC", players=_full_squad(note=65.0))
    assert club_strength(club) == pick_best_formation(club).rating


class TestLineupSectorRatings:
    def test_computes_a_separate_average_per_sector(self):
        players = [_player("GK", 60.0, "gk0")]
        players += [_player("DC", 70.0, f"cb{i}") for i in range(2)]
        players += [_player("LB", 70.0, "lb0")]
        players += [_player("RB", 70.0, "rb0")]
        players += [_player("MC", 80.0, f"cm{i}") for i in range(4)]
        players += [_player("AG", 90.0, "lw0")]
        players += [_player("AD", 90.0, "rw0")]
        players += [_player("BU", 90.0, f"cf{i}") for i in range(2)]
        club = Club(name="Test FC", players=players)

        lineup = select_best_xi(club, "4-4-2")

        assert lineup.gk_rating == 60.0
        assert lineup.def_rating == 70.0
        assert lineup.mid_rating == 80.0
        assert lineup.att_rating == 90.0
        # La moyenne globale reste la moyenne plate des 11, inchangée.
        assert lineup.rating == pytest.approx(sum(p.note for p in lineup.players) / 11)

    def test_falls_back_to_overall_rating_when_a_sector_is_empty(self):
        # Aucun gardien du tout dans l'effectif (voir
        # test_select_best_xi_backfills_when_a_group_is_short) : le secteur
        # GK est vide dans la compo, gk_rating retombe sur la moyenne globale
        # plutôt que de s'effondrer à 0.
        players = [p for p in _full_squad(note=65.0) if p.group != "GK"]
        club = Club(name="Test FC", players=players)

        lineup = select_best_xi(club, "4-4-2")

        assert lineup.gk_rating == lineup.rating


def test_bench_excludes_starters_and_unavailable():
    club = Club(name="Test FC", players=_full_squad())
    lineup = select_best_xi(club, "4-4-2")
    starters = {p.name for p in lineup.players}

    reserves = bench(club, lineup)

    assert starters.isdisjoint({p.name for p in reserves})
    assert len(reserves) == len(club.players) - len(lineup.players)


def test_all_formations_sum_to_eleven():
    for quotas in FORMATIONS.values():
        assert sum(quotas.values()) == 11


class TestParseFormation:
    def test_matches_the_predefined_formations_dict(self):
        for formation, quotas in FORMATIONS.items():
            assert parse_formation(formation) == quotas

    def test_supports_arbitrary_formations_not_in_the_predefined_dict(self):
        assert parse_formation("3-5-2") == {"GK": 1, "DEF": 3, "MID": 5, "ATT": 2}
        assert parse_formation("3-4-3") == {"GK": 1, "DEF": 3, "MID": 4, "ATT": 3}
        assert parse_formation("4-1-4-1") == {"GK": 1, "DEF": 4, "MID": 5, "ATT": 1}

    def test_rejects_a_formation_that_does_not_sum_to_ten_outfield_players(self):
        with pytest.raises(ValueError):
            parse_formation("4-4-4")

    def test_ignores_a_trailing_qualifier_from_transfermarkt(self):
        # Transfermarkt qualifie parfois la formation préférentielle d'un
        # entraîneur d'un adjectif (ex. "4-3-3 offensif", "3-4-3 plat") :
        # seul le préfixe numérique compte pour les quotas.
        assert parse_formation("4-3-3 offensif") == {"GK": 1, "DEF": 4, "MID": 3, "ATT": 3}
        assert parse_formation("3-4-3 plat") == {"GK": 1, "DEF": 3, "MID": 4, "ATT": 3}

    def test_rejects_a_formation_with_no_numeric_prefix(self):
        with pytest.raises(ValueError):
            parse_formation("libéro")


class TestSelectBestXiCoherentBricolage:
    def test_secondary_poste_is_preferred_over_a_higher_rated_player_with_no_matching_poste(self):
        # Aucun latéral droit (RB) primaire dispo : un joueur qui déclare RB
        # en poste secondaire doit être préféré pour cette place à un joueur
        # bien mieux noté mais sans aucun rapport avec le poste (ni
        # principal, ni secondaire) -- qui lui doit rester sur le banc,
        # aucune place de la formation ne correspondant à son poste (MOC).
        players = [_player("GK", 70.0, "gk0")]
        players += [_player("LB", 70.0, "lb0")]
        players += [_player("DC", 70.0, f"cb{i}") for i in range(2)]
        players += [_player("MC", 70.0, f"cm{i}") for i in range(2)]
        players += [_player("MDC", 70.0, "dm0")]
        players += [_player("AD", 70.0, "rw0")]
        players += [_player("AG", 70.0, "lw0")]
        players += [_player("BU", 70.0, "cf0"), _player("BU", 70.0, "cf1")]
        players += [_player("MC", 60.0, "utility", poste_secondaire=("RB",))]
        players += [_player("MOC", 90.0, "star_playmaker")]
        club = Club(name="Test FC", players=players)

        lineup = select_best_xi(club, "4-4-2")

        names = {p.name for p in lineup.players}
        assert len(lineup.players) == 11
        assert "utility" in names
        assert "star_playmaker" not in names

    def test_never_backfills_a_defensive_shortfall_with_a_pure_attacker(self):
        # Aucun défenseur du tout dans l'effectif (ni au poste principal, ni
        # en secondaire) : les places défensives (LB, DC, DC, RB) restent
        # vides -- même quand des joueurs d'autres secteurs (ici 2 MC en
        # surplus, la formation n'en réclamant que 2 sur les 4 dispo)
        # pourraient techniquement combler le compte, seul le poste déclaré
        # (principal ou secondaire) donne droit à une place.
        players = [_player("GK", 70.0, "gk0")]
        players += [_player("MC", 70.0, f"cm{i}") for i in range(4)]
        players += [_player("BU", 70.0, f"cf{i}") for i in range(2)]
        club = Club(name="Test FC", players=players)

        lineup = select_best_xi(club, "4-4-2")

        assert not any(p.group == "DEF" for p in lineup.players)
        assert len(lineup.players) == 7  # GK + 4 MC (surplus compris) + 2 BU, secteur défensif non comblé

    def test_full_back_can_deputize_as_winger_via_declared_secondary_poste(self):
        # Deux latéraux gauche (LB) pour une seule place de LB : le mieux
        # noté la pourvoit normalement, le surnuméraire dépanne à l'aile
        # gauche (AG) -- à condition d'avoir AG déclaré en poste secondaire
        # (le poste principal seul ne suffit plus, voir la classe ci-dessus).
        players = [_player("GK", 70.0, "gk0")]
        players += [_player("DC", 70.0, f"cb{i}") for i in range(4)]  # surplus, 2 places de DC seulement
        players += [_player("MC", 70.0, f"cm{i}") for i in range(3)]
        players += [_player("LB", 70.0, "main_lb")]
        players += [_player("LB", 65.0, "extra_lb", poste_secondaire=("AG",))]
        club = Club(name="Test FC", players=players)

        lineup = select_best_xi(club, "4-3-3")

        names = {p.name for p in lineup.players}
        assert "main_lb" in names
        assert "extra_lb" in names
        assert len(lineup.players) == 10  # effectif de 10 entièrement utilisé (RB/MDC/AD/BU non couverts)

    def test_prefers_a_tactically_close_player_over_a_higher_rated_out_of_position_one(self):
        # Aucun BU (avant-centre) dans l'effectif, ni en principal ni en
        # secondaire : le "4-3-3" de l'onglet "Dispositifs tactiques" n'a
        # qu'une seule place de BU (GK, LB, DC, DC, RB, MDC, MC, MC, AG, AD,
        # BU). Un ailier surnuméraire (AG), tactiquement voisin de BU
        # (distance 1, voir players._POSTE_NEIGHBORS), doit être préféré pour
        # dépanner cette place plutôt qu'un défenseur surnuméraire bien mieux
        # noté mais sans aucun rapport avec l'attaque (distance 3) -- la
        # cohérence positionnelle prime sur la seule note au moment du
        # dernier recours.
        players = [_player("GK", 70.0, "gk0")]
        players += [_player("LB", 70.0, "lb0")]
        players += [_player("RB", 70.0, "rb0")]
        players += [_player("DC", 75.0, f"cb{i}") for i in range(2)]  # pourvoient les 2 places de DC
        players += [_player("MDC", 70.0, "dm0")]
        players += [_player("MC", 70.0, f"cm{i}") for i in range(2)]
        players += [_player("AD", 70.0, "rw0")]
        players += [_player("AG", 80.0, "starter_winger")]  # pourvoit la place d'AG
        players += [_player("AG", 65.0, "close_winger")]  # surplus, voisin de BU (distance 1)
        players += [_player("DC", 72.0, "far_defender")]  # surplus, distance 3 de BU (trop loin)
        club = Club(name="Test FC", players=players)

        lineup = select_best_xi(club, "4-3-3")

        names = {p.name for p in lineup.players}
        assert "close_winger" in names
        assert "far_defender" not in names

    def test_a_much_better_secondary_candidate_wins_the_slot_over_a_weak_primary_match(self):
        # Cas Barcelone/Hamza Abdelkarim : un très jeune BU (poste principal
        # exact, mais note faible) ne doit plus systématiquement rafler la
        # place d'avant-centre. Deux ailiers déclarent BU en poste secondaire
        # (comme Raphinha/Gordon) : le premier (best_winger) reste à son
        # poste naturel (AG, où il est imbattable), ce qui libère le second
        # (backup_winger) pour dépanner en pointe via son poste secondaire,
        # nettement devant le jeune BU malgré la pénalité de 5%.
        players = [_player("GK", 70.0, "gk0")]
        players += [_player("LB", 70.0, "lb0")]
        players += [_player("RB", 70.0, "rb0")]
        players += [_player("DC", 70.0, f"cb{i}") for i in range(2)]
        players += [_player("MDC", 70.0, "dm0")]
        players += [_player("MC", 70.0, f"cm{i}") for i in range(2)]
        players += [_player("AD", 70.0, "rw0")]
        players += [_player("AG", 83.0, "best_winger", poste_secondaire=("BU",))]
        players += [_player("AG", 80.0, "backup_winger", poste_secondaire=("BU",))]
        players += [_player("BU", 59.0, "young_striker")]
        club = Club(name="Test FC", players=players)

        lineup = select_best_xi(club, "4-3-3")

        names = {p.name for p in lineup.players}
        assert "best_winger" in names
        assert "backup_winger" in names
        assert "young_striker" not in names

    def test_primary_match_still_wins_over_a_marginally_better_secondary_candidate(self):
        # À écart de note faible, le poste principal doit continuer à primer
        # -- la pénalité (5%) doit rester modeste, pas renverser deux joueurs
        # de niveau proche. "winger" perd d'abord sa place naturelle d'AG
        # face à un titulaire mieux noté, puis se présente en BU secondaire
        # (72 * 0.95 = 68.4) face au titulaire BU (70) : le titulaire l'emporte.
        players = [_player("GK", 70.0, "gk0")]
        players += [_player("LB", 70.0, "lb0")]
        players += [_player("RB", 70.0, "rb0")]
        players += [_player("DC", 70.0, f"cb{i}") for i in range(2)]
        players += [_player("MDC", 70.0, "dm0")]
        players += [_player("MC", 70.0, f"cm{i}") for i in range(2)]
        players += [_player("AD", 70.0, "rw0")]
        players += [_player("AG", 85.0, "ag_starter")]
        players += [_player("AG", 72.0, "winger", poste_secondaire=("BU",))]
        players += [_player("BU", 70.0, "main_striker")]
        club = Club(name="Test FC", players=players)

        lineup = select_best_xi(club, "4-3-3")

        names = {p.name for p in lineup.players}
        assert "main_striker" in names
        assert "winger" not in names

    def test_secondary_poste_lets_a_player_deputize_when_primary_poste_is_too_far(self):
        # Un pur avant-centre est à 2 crans de la défense (bricolage refusé
        # par le poste principal seul -- voir
        # test_never_backfills_a_defensive_shortfall_with_a_pure_attacker).
        # Mais avec "LB" déclaré en poste secondaire, il redevient un
        # candidat légitime pour dépanner un secteur défensif en pénurie.
        players = [_player("GK", 70.0, "gk0")]
        players += [_player("MC", 70.0, f"cm{i}") for i in range(4)]
        players += [_player("BU", 90.0, "cf0"), _player("BU", 90.0, "cf1")]
        players += [_player("BU", 70.0, "versatile", poste_secondaire=("LB",))]
        club = Club(name="Test FC", players=players)

        lineup = select_best_xi(club, "4-4-2")

        names = {p.name for p in lineup.players}
        assert "versatile" in names
        assert len(lineup.players) == 8  # GK + 4 MID + 2 ATT(quota) + 1 dépannage DEF via poste secondaire

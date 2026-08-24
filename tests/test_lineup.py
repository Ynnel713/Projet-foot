from ligue1sim.clubs import Club
from ligue1sim.lineup import (
    DEFAULT_RATING,
    FORMATIONS,
    bench,
    club_strength,
    pick_best_formation,
    select_best_xi,
)
from ligue1sim.players import Player


def _player(poste: str, note: float, name: str) -> Player:
    return Player(
        prenom=name,
        nom="",
        nationalite="France",
        age=25,
        poste=poste,
        note=note,
        club="Test FC",
        championnat="TEST",
    )


def _full_squad(note: float = 70.0) -> list[Player]:
    """Un effectif standard : 3 GK, 8 DEF, 8 MID (varié), 8 ATT (varié)."""
    squad = [_player("Goalkeeper", note, f"gk{i}") for i in range(3)]
    squad += [_player("Centre-Back", note, f"cb{i}") for i in range(4)]
    squad += [_player("Left-Back", note, f"lb{i}") for i in range(2)]
    squad += [_player("Right-Back", note, f"rb{i}") for i in range(2)]
    squad += [_player("Central Midfield", note, f"cm{i}") for i in range(4)]
    squad += [_player("Defensive Midfield", note, f"dm{i}") for i in range(2)]
    squad += [_player("Attacking Midfield", note, f"am{i}") for i in range(2)]
    squad += [_player("Left Winger", note, f"lw{i}") for i in range(2)]
    squad += [_player("Right Winger", note, f"rw{i}") for i in range(2)]
    squad += [_player("Centre-Forward", note, f"cf{i}") for i in range(4)]
    return squad


def test_select_best_xi_respects_formation_quotas():
    club = Club(name="Test FC", players=_full_squad())
    lineup = select_best_xi(club, "4-4-2")

    assert len(lineup.players) == 11
    groups = [p.group for p in lineup.players]
    assert groups.count("GK") == 1
    assert groups.count("DEF") == 4
    assert groups.count("MID") == 4
    assert groups.count("ATT") == 2


def test_select_best_xi_picks_highest_notes_within_each_group():
    players = _full_squad(note=50.0)
    players.append(_player("Centre-Back", 99.0, "star_cb"))
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
    club = Club(name="Test FC", players=[_player("Central Midfield", 70.0, "only")])

    lineup = select_best_xi(club, "4-3-3")

    assert len(lineup.players) == 1
    assert lineup.rating == 70.0


def test_select_best_xi_falls_back_to_default_rating_with_no_eligible_players():
    club = Club(name="Test FC", players=[])

    lineup = select_best_xi(club, "4-3-3")

    assert lineup.players == []
    assert lineup.rating == DEFAULT_RATING


def test_pick_best_formation_favors_squad_shape():
    # Effectif riche en ailiers/attaquants, pauvre au milieu -> devrait
    # préférer un dispositif qui a besoin de moins de milieux (4-3-3 ou 4-4-2)
    # plutôt que le 4-2-3-1 qui en réclame 5 (forcerait un repli sur des
    # ailiers/attaquants hors de position).
    players = [_player("Goalkeeper", 70.0, "gk0")]
    players += [_player("Centre-Back", 70.0, f"cb{i}") for i in range(2)]
    players += [_player("Left-Back", 70.0, "lb0")]
    players += [_player("Right-Back", 70.0, "rb0")]
    players += [_player("Central Midfield", 60.0, f"cm{i}") for i in range(3)]
    players += [_player("Left Winger", 90.0, f"lw{i}") for i in range(3)]
    players += [_player("Right Winger", 90.0, f"rw{i}") for i in range(3)]
    players += [_player("Centre-Forward", 90.0, f"cf{i}") for i in range(3)]
    club = Club(name="Wingers FC", players=players)

    best = pick_best_formation(club)

    assert best.formation != "4-2-3-1"


def test_club_strength_matches_best_formation_rating():
    club = Club(name="Test FC", players=_full_squad(note=65.0))
    assert club_strength(club) == pick_best_formation(club).rating


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

"""Côté des joueurs au coup d'envoi (ticket v2-realisme/02a) : LB et AG à gauche de leur équipe, RB et AD à droite, jamais
selon le nom. y croît vers le bas de l'écran : attaquer vers +x met la gauche de l'équipe en y petit, vers x=0 en y grand."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from ligue1sim.clubs import load_clubs
from ligue1sim.lineup import Lineup, pick_best_formation
from ligue1sim.season import CLUBS_PATH
from v2engine.formation import initial_positions

_LEFT, _RIGHT = ("LB", "AG"), ("RB", "AD")


def _lineup(postes_by_name: dict[str, str], bands: dict[str, int]) -> Lineup:
    players = [SimpleNamespace(name=n, poste=p) for n, p in postes_by_name.items()]
    return Lineup(club_name="T", formation="4-4-2", players=players, rating=60.0, bands=bands)


def _four_four_two_reverse_alphabetical() -> Lineup:
    # les noms inversent l'ordre alphabétique : Zed (LB) ... Abel (RB), Zoe (AG) ... Ada (AD)
    postes = {"Gardien": "GK", "Zed": "LB", "Yan": "DC", "Xav": "DC", "Abel": "RB",
              "Zoe": "AG", "Wil": "MC", "Vic": "MC", "Ada": "AD", "Utz": "BU", "Tom": "ATT"}
    bands = {"Gardien": 0, "Zed": 1, "Yan": 1, "Xav": 1, "Abel": 1, "Zoe": 2, "Wil": 2, "Vic": 2, "Ada": 2, "Utz": 3, "Tom": 3}
    return _lineup(postes, bands)


@pytest.mark.parametrize("attacking_right", [True, False])
def test_lateral_postes_take_their_own_side_whatever_their_name(attacking_right: bool) -> None:
    pos = initial_positions(_four_four_two_reverse_alphabetical(), attacking_right=attacking_right)
    left_is_lower_y = attacking_right
    for left, axis, right in (("Zed", "Yan", "Abel"), ("Zoe", "Wil", "Ada")):
        assert (pos[left].y < pos[axis].y < pos[right].y) == left_is_lower_y
        assert (pos[left].y > pos[axis].y > pos[right].y) == (not left_is_lower_y)


def test_the_two_sides_mirror_each_other() -> None:
    lineup = _four_four_two_reverse_alphabetical()
    home, away = initial_positions(lineup, attacking_right=True), initial_positions(lineup, attacking_right=False)
    assert home["Zed"].y < home["Abel"].y and away["Zed"].y > away["Abel"].y


def test_same_poste_order_is_stable_and_does_not_depend_on_the_name() -> None:
    a = initial_positions(_four_four_two_reverse_alphabetical(), attacking_right=True)
    renamed = _lineup({"Z1": "GK", "Z2": "DC", "Z3": "DC", "Z4": "MC"}, {"Z1": 0, "Z2": 1, "Z3": 1, "Z4": 1})
    b = initial_positions(renamed, attacking_right=True)
    assert len({b["Z2"].y, b["Z3"].y, b["Z4"].y}) == 3 and b["Z2"].y == pytest.approx(34.0)  # 1er de la lineup au centre
    renamed_back = _lineup({"A": "GK", "B": "DC", "C": "DC", "D": "MC"}, {"A": 0, "B": 1, "C": 1, "D": 1})
    c = initial_positions(renamed_back, attacking_right=True)
    assert [c[n].y for n in "BCD"] == [b[n].y for n in ("Z2", "Z3", "Z4")]  # mêmes places, noms sans effet
    assert a == initial_positions(_four_four_two_reverse_alphabetical(), attacking_right=True)


@pytest.mark.parametrize("attacking_right", [True, False])
def test_every_lateral_of_the_whole_base_is_on_the_right_side(attacking_right: bool) -> None:
    checked = 0
    for club in load_clubs(CLUBS_PATH, "Ligue 1"):
        lineup = pick_best_formation(club)
        pos = initial_positions(lineup, attacking_right=attacking_right)
        for band in set(lineup.bands.values()) or {1, 2, 3}:
            names = [p.name for p in lineup.players if (lineup.bands.get(p.name) == band)]
            for p in lineup.players:
                if p.name not in names or p.poste not in _LEFT + _RIGHT:
                    continue
                others = [q for q in lineup.players if q.name in names and q is not p]
                is_left = (p.poste in _LEFT) == attacking_right
                for q in others:
                    if (q.poste in _LEFT) == (p.poste in _LEFT) and (q.poste in _RIGHT) == (p.poste in _RIGHT):
                        continue  # même couloir : pas de contrainte
                    lane_q = 0 if q.poste in _LEFT else 2 if q.poste in _RIGHT else 1
                    lane_p = 0 if p.poste in _LEFT else 2
                    below = (pos[p.name].y < pos[q.name].y) == ((lane_p < lane_q) == attacking_right)
                    assert below, (club.name, p.name, p.poste, q.name, q.poste)
                checked += 1
    assert checked > 0


# --- ticket v2-realisme/02b : largeur de référence propre à chaque poste ---------------------------------------------

def _four_three_three() -> Lineup:
    postes = {"G": "GK", "D1": "LB", "D2": "DC", "D3": "DC", "D4": "RB", "M1": "MC", "M2": "MDC", "M3": "MC",
              "A1": "AG", "A2": "BU", "A3": "AD"}
    bands = {"G": 0, "D1": 1, "D2": 1, "D3": 1, "D4": 1, "M1": 2, "M2": 2, "M3": 2, "A1": 3, "A2": 3, "A3": 3}
    return _lineup(postes, bands)


@pytest.mark.parametrize("attacking_right", [True, False])
def test_wingers_are_wider_than_full_backs_and_the_lone_pivot_sits_on_the_axis(attacking_right: bool) -> None:
    pos = initial_positions(_four_three_three(), attacking_right=attacking_right)
    axis = 34.0
    assert abs(pos["A1"].y - axis) > abs(pos["D1"].y - axis) > abs(pos["D2"].y - axis)
    assert abs(pos["A3"].y - axis) > abs(pos["D4"].y - axis)
    assert abs(pos["A2"].y - axis) < 1e-9  # un seul BU : dans l'axe
    assert abs(pos["G"].y - axis) < 1e-9


@pytest.mark.parametrize("attacking_right", [True, False])
def test_several_players_of_one_axial_poste_are_symmetric_about_the_axis(attacking_right: bool) -> None:
    pos = initial_positions(_four_three_three(), attacking_right=attacking_right)
    assert pos["D2"].y + pos["D3"].y == pytest.approx(68.0)  # deux DC, de part et d'autre de l'axe
    assert pos["M1"].y + pos["M3"].y == pytest.approx(68.0)
    assert abs(pos["M2"].y - 34.0) < 1e-9  # le MDC seul est dans l'axe, au milieu des deux MC


def test_a_single_pivot_in_a_four_two_three_one_is_on_the_axis_whatever_the_squad() -> None:
    postes = {"G": "GK", "D1": "LB", "D2": "DC", "D3": "DC", "D4": "RB", "P1": "MDC", "P2": "MDC",
              "AG": "AG", "O": "MOC", "AD": "AD", "N": "BU"}
    bands = {"G": 0, "D1": 1, "D2": 1, "D3": 1, "D4": 1, "P1": 2, "P2": 2, "AG": 3, "O": 3, "AD": 3, "N": 4}
    pos = initial_positions(_lineup(postes, bands), attacking_right=True)
    assert abs(pos["O"].y - 34.0) < 1e-9 and abs(pos["N"].y - 34.0) < 1e-9
    assert pos["P1"].y + pos["P2"].y == pytest.approx(68.0)


@pytest.mark.parametrize("order", [("M1", "M2", "M3"), ("M2", "M1", "M3"), ("M3", "M1", "M2")])
def test_the_lone_pivot_stays_between_the_two_midfielders_whatever_the_lineup_order(order: tuple[str, ...]) -> None:
    postes = {"M1": "MC", "M2": "MDC", "M3": "MC"}
    lineup = _lineup({"G": "GK", **{n: postes[n] for n in order}}, {"G": 0, "M1": 1, "M2": 1, "M3": 1})
    pos = initial_positions(lineup, attacking_right=True)
    assert pos["M2"].y == pytest.approx(34.0) and pos["M1"].y + pos["M3"].y == pytest.approx(68.0)


@pytest.mark.parametrize("order", [("LB", "AG"), ("AG", "LB")])
def test_the_winger_stays_outside_the_full_back_on_the_same_side_whatever_the_lineup_order(order: tuple[str, ...]) -> None:
    lineup = _lineup({"G": "GK", "x": order[0], "y": order[1]}, {"G": 0, "x": 1, "y": 1})
    pos = initial_positions(lineup, attacking_right=True)
    by_poste = {lineup.players[1 + i].poste: pos[n] for i, n in enumerate(("x", "y"))}
    assert 34.0 - by_poste["AG"].y > 34.0 - by_poste["LB"].y > 0

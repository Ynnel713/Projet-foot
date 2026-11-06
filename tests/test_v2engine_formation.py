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
    assert b["Z2"].y < b["Z3"].y < b["Z4"].y  # ordre de la lineup, pas du nom
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

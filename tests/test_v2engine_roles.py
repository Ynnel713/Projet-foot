"""Rôle de chaque joueur (ticket v2-realisme/02c) : un rôle par défaut par poste, un rôle dédié selon la colonne
« Catégorie » de la base, rôle écrit dans la trace, aucun effet sur le jeu."""

from __future__ import annotations

import random

import pytest

from ligue1sim.clubs import load_clubs, list_championnats
from ligue1sim.lineup import pick_best_formation
from ligue1sim.season import CLUBS_PATH
from v2engine.match import simulate_match
from v2engine.roles import _CATEGORY_ROLE, DEFAULT_ROLE, ROLES, _normalize, role_of

_POSTES = ("GK", "DC", "LB", "RB", "MDC", "MC", "MOC", "AG", "AD", "SA", "BU", "ATT")


def test_every_poste_has_a_default_role_and_every_role_is_documented() -> None:
    assert all(DEFAULT_ROLE[p] in ROLES for p in _POSTES)
    assert set(_CATEGORY_ROLE.values()) <= set(ROLES)
    assert set(ROLES) == set(DEFAULT_ROLE.values()) | set(_CATEGORY_ROLE.values())  # aucun rôle orphelin
    assert all(ROLES.values())


def test_a_player_without_category_gets_the_standard_role_of_his_poste() -> None:
    assert [role_of(p) for p in _POSTES] == [DEFAULT_ROLE[p] for p in _POSTES]
    assert role_of("MC", None) == role_of("MC", "") == "milieu relayeur"


@pytest.mark.parametrize("poste,categorie,role", [
    ("MC", "box to box", "box to box"), ("MC", "mezzala", "mezzala"), ("MC", "Mezzala", "mezzala"),
    ("MDC", "milieu récupérateur", "récupérateur"), ("MDC", "regista", "regista"), ("MOC", "meneur", "meneur"),
    ("BU", "pivot", "pivot"), ("BU", "pivot ", "pivot"), ("BU", "buteur axial", "buteur axial"),
    ("BU", "second attaquant ", "second attaquant"), ("AG", "ailier inverse", "ailier intérieur"),
    ("RB", "piston", "piston"), ("LB", "lateral defensif", "latéral défensif"),
])
def test_a_category_gives_a_dedicated_role_whatever_the_case_accents_or_trailing_spaces(poste, categorie, role) -> None:
    assert role_of(poste, categorie) == role


def test_a_pivot_and_an_axial_striker_do_not_share_a_role() -> None:
    assert role_of("BU", "pivot") != role_of("BU", "buteur axial") != role_of("BU")


@pytest.mark.parametrize("poste,categorie", [("DC", "lateral defensif"), ("BU", "ailier inverse"), ("RB", "box to box"),
                                             ("GK", "pivot"), ("MC", "inconnue")])
def test_a_category_not_planned_for_the_poste_falls_back_to_the_default_role(poste, categorie) -> None:
    assert role_of(poste, categorie) == DEFAULT_ROLE[poste]


def test_an_unknown_poste_has_no_role_and_does_not_raise() -> None:
    assert role_of("XX", "pivot") == ""


# combinaisons (poste, catégorie) de la base assumées sans rôle dédié : rôle par défaut du poste
_ASSUMED_UNPLANNED = {("DC", "lateral defensif"), ("DC", "second attaquant"), ("BU", "ailier inverse"),
                      ("RB", "box to box"), ("MOC", "ailier inverse")}


def test_every_player_of_the_whole_base_gets_a_documented_role_and_no_real_category_is_missed() -> None:
    checked, unplanned = 0, set()
    for championnat in list_championnats(CLUBS_PATH):
        for club in load_clubs(CLUBS_PATH, championnat):
            for player in club.players:
                assert role_of(player.poste, player.categorie) in ROLES, (player.name, player.poste, player.categorie)
                key = (player.poste, _normalize(player.categorie))
                if key[1] and key not in _CATEGORY_ROLE:
                    unplanned.add(key)
                checked += 1
    assert checked > 4000
    assert unplanned <= _ASSUMED_UNPLANNED, unplanned - _ASSUMED_UNPLANNED  # le repli ne doit jamais être silencieux


def test_underscores_count_as_spaces() -> None:
    assert role_of("BU", "buteur_axial") == "buteur axial" and role_of("MC", "box_to_box") == "box to box"


def test_the_role_is_written_in_every_snapshot_of_the_trace() -> None:
    clubs = load_clubs(CLUBS_PATH, "Ligue 1")
    home, away = clubs[4], clubs[5]
    expected = {p.name: role_of(p.poste, p.categorie)
                for lineup in (pick_best_formation(home), pick_best_formation(away)) for p in lineup.players}
    random.seed(20260927)
    trace = simulate_match(home, away, duration_minutes=1.0, record_every=10)
    assert trace.ticks
    for tick in trace.ticks:
        assert {p.name: p.role for p in tick.players} == expected

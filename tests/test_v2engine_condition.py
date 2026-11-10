"""Façade des notes (ticket v2-realisme/19a) : `condition.effective_rating` est le seul point d'entrée pour lire une
note en jeu, et rend aujourd'hui la note intrinsèque à l'identique."""

from __future__ import annotations

import ast
import pathlib
from types import SimpleNamespace

import pytest

from v2engine.attributes import player_attribute
from v2engine.condition import FAMILIES, PlayerCondition, effective_rating, family, intrinsic_rating
from v2engine.geometry import Vec2
from v2engine.movement import PlayerState, step

ENGINE = pathlib.Path(__file__).resolve().parents[1] / "v2engine"
CARTE = pathlib.Path(__file__).resolve().parents[1] / "docs" / "CARTE_ATTRIBUTS_V2.md"


def _state(note: int, attributes: dict[str, int] | None) -> PlayerState:
    return PlayerState(name="X", team="home", poste="MC", position=Vec2(50, 34), velocity=Vec2(0, 0), pace=note,
                       acceleration=note, stamina=note, home_target=Vec2(50, 34), attributes=attributes)


@pytest.mark.parametrize("note", [11, 55, 99])
def test_effective_rating_is_the_intrinsic_rating_for_every_attribute(note: int) -> None:
    state = _state(note, dict.fromkeys(FAMILIES, note))
    for attribute in FAMILIES:
        assert effective_rating(state, attribute) == note == intrinsic_rating(state, attribute)


def test_a_player_without_data_keeps_the_default_rating() -> None:
    for player in (SimpleNamespace(attributes=None), _state(60, None)):
        for attribute in ("Passing", "Decisions", "Reflexes"):
            assert effective_rating(player, attribute) == player_attribute(player, attribute) == 60


def test_physical_capacities_are_read_from_the_state_not_the_sheet() -> None:
    # le champ peut différer de la fiche (profil forcé d'un banc) : c'est lui que le jeu utilise
    state = _state(80, {"Pace": 20, "Acceleration": 20, "Stamina": 20})
    assert [effective_rating(state, a) for a in ("Pace", "Acceleration", "Stamina")] == [80, 80, 80]
    assert intrinsic_rating(state, "Pace") == 20


def test_the_condition_travels_with_the_player() -> None:
    state = _state(60, None)
    assert state.condition == PlayerCondition()
    assert step(state, 0.1, Vec2(60, 34), minute=10.0).condition is state.condition


def test_every_attribute_of_the_map_has_one_family() -> None:
    names = {line.split("**")[1] for line in CARTE.read_text(encoding="utf-8").splitlines()[:80]
             if line.startswith("| **")}
    assert names == set(FAMILIES)
    assert {family(a) for a in FAMILIES} == {"physique", "mental", "technique", "gardien"}
    with pytest.raises(KeyError):
        family("Inconnu")


def _offenders(module: str, tree: ast.AST) -> set[tuple[str, str]]:
    """Lectures brutes d'une note dans `tree` : `player_attribute(...)` hors `attributes` et `condition`, champ
    `.pace`, `.acceleration` ou `.stamina` hors `movement` (chemin chaud de `step`)."""
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, "id", getattr(node.func, "attr", None)) == "player_attribute":
            if module not in {"attributes", "condition"}:
                found.add(("player_attribute", module))
        if (isinstance(node, ast.Attribute) and node.attr in ("pace", "acceleration", "stamina")
                and isinstance(node.ctx, ast.Load) and module != "movement"):
            found.add((node.attr, module))
    return found


def test_ratings_are_read_only_through_the_facade() -> None:
    offenders = set()
    for path in sorted(ENGINE.rglob("*.py")):
        offenders |= _offenders(path.stem, ast.parse(path.read_text(encoding="utf-8")))
    assert not offenders, f"note lue hors de la façade condition.effective_rating : {sorted(offenders)}"


def test_the_guard_catches_a_raw_read() -> None:
    tree = ast.parse("x = player_attribute(p, 'Passing') + p.pace + effective_rating(p, 'Pace')")
    assert _offenders("decision", tree) == {("player_attribute", "decision"), ("pace", "decision")}
    assert _offenders("movement", tree) == {("player_attribute", "movement")}

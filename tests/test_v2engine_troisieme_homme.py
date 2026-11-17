"""Tests du moteur V2, ticket v2-collectif/15b1 (chercher le troisième homme en construction, contexte « lecture du
pressing »). Voir .scratch/v2-collectif/issues/15b1-chercher-le-troisieme-homme.md, critères d'acceptation."""

from __future__ import annotations

import random

import pytest

import v2engine.decision as decision
from v2engine.bloc import build_up_pressed
from v2engine.contextes import LECTURE_DU_PRESSING, contextual_rating
from v2engine.decision import (FIRST_LINE_RANK, THIRD_MAN_BONUS, choose_action, evaluate_options,
                               first_pressing_line, reads_third_man_probability)
from v2engine.geometry import Vec2
from v2engine.movement import PlayerState

GOAL = Vec2(105.0, 34.0)


def _player(name: str, team: str = "home", poste: str = "DC", x: float = 50.0, y: float = 34.0,
            attributes: dict[str, int] | None = None) -> PlayerState:
    position = Vec2(x, y)
    return PlayerState(name=name, team=team, poste=poste, position=position, velocity=Vec2(0.0, 0.0), pace=60,
                       acceleration=60, stamina=60, home_target=position, attributes=attributes)


def _scene(note: int = 55, pressers: bool = True, b_x: float = 16.0) -> tuple[PlayerState, list[PlayerState]]:
    """Central porteur à 12 m de son but ; B (latéral) devant la première ligne, C (milieu) libre juste derrière, un
    autre central à l'opposé. Sous pressing : trois adversaires à 18-21 m (première ligne à 21 m). C reste à moins de
    15 m de gain vers le but : le porteur le voit sans tirage de repérage (Vision, autre effet)."""
    reading = {"Vision": note, "Anticipation": note, "Decisions": note}
    holder = _player("DC", x=12.0, y=34.0, attributes=reading)
    mates = [_player("B", poste="LB", x=b_x, y=20.0), _player("C", poste="MC", x=26.0, y=22.0),
             _player("DCd", x=14.0, y=54.0)]
    front = [_player("A0", "away", "BU", 18.0, 28.0), _player("A1", "away", "BU", 18.0, 42.0),
             _player("A2", "away", "MOC", 21.0, 34.0)] if pressers else \
        [_player("A0", "away", "BU", 40.0, 28.0), _player("A1", "away", "BU", 40.0, 42.0),
         _player("A2", "away", "MOC", 42.0, 34.0)]
    rivals = [*front, _player("A3", "away", "MC", 45.0, 40.0), _player("A4", "away", "DC", 60.0, 25.0)]
    return holder, [holder, *mates, *rivals]


def _value_to(options, name: str) -> float:
    return next(o.value for o in options if o.kind == "pass" and o.target.name == name)


def test_reading_chance_follows_the_validated_points() -> None:
    # constantes validées le 17/11/2026 : 11 -> 15 %, 55 -> 45 %, 99 -> 80 %, par le contexte « lecture du pressing »
    for note, expected in ((11, 0.15), (55, 0.45), (99, 0.80)):
        holder = _player("P", attributes={"Vision": note, "Anticipation": note, "Decisions": note})
        assert contextual_rating(holder, LECTURE_DU_PRESSING) == pytest.approx(note)
        assert reads_third_man_probability(holder) == pytest.approx(expected)
    mixed = _player("P", attributes={"Vision": 99, "Anticipation": 11, "Decisions": 11})  # 0,5 x 99 + 0,5 x 11 = 55
    assert reads_third_man_probability(mixed) == pytest.approx(0.45)


def test_first_pressing_line_is_the_third_closest_outfield_rival() -> None:
    assert FIRST_LINE_RANK == 3
    rivals = [_player("GK", "away", "GK", 2.0, 34.0), _player("A", "away", x=30.0), _player("B", "away", x=18.0),
              _player("C", "away", x=25.0), _player("D", "away", x=60.0)]
    assert first_pressing_line("home", rivals) == 30.0  # 18, 25, 30 : le gardien adverse ne compte pas
    assert first_pressing_line("away", rivals) == pytest.approx(105.0 - 25.0)  # en miroir : 45, 75, 80 -> 80
    assert first_pressing_line("home", rivals[:3]) is None


def test_build_up_pressed_needs_the_zone_and_two_rivals() -> None:
    holder, players = _scene()
    assert build_up_pressed(holder, players)
    holder_far, players_far = _scene(pressers=False)
    assert not build_up_pressed(holder_far, players_far)  # adversaires hors de ses 35 m
    midfielder = _player("MC", poste="MC", x=12.0, y=34.0)
    assert not build_up_pressed(midfielder, [midfielder, *players[1:]])  # pas un bâtisseur


def test_a_read_third_man_raises_the_pass_to_the_one_in_front(monkeypatch) -> None:
    holder, players = _scene()
    values = {}
    for chance in (0.0, 1.0):
        monkeypatch.setattr(decision, "reads_third_man_probability", lambda _h, c=chance: c)
        random.seed(20261117)
        values[chance] = evaluate_options(holder, players, GOAL, None, build_up=True, pressed=True)
    assert _value_to(values[1.0], "B") > _value_to(values[0.0], "B") * 1.2  # suite vers C majorée de 50 %
    assert next(o for o in values[1.0] if o.kind == "pass" and o.target.name == "B").follow == "C"
    assert _value_to(values[1.0], "DCd") == pytest.approx(_value_to(values[0.0], "DCd"))  # suite sans ligne cassée
    assert THIRD_MAN_BONUS == 0.5


def test_no_change_without_pressing_or_when_the_receiver_is_already_behind(monkeypatch) -> None:
    monkeypatch.setattr(decision, "reads_third_man_probability", lambda _h: 1.0)
    holder, players = _scene()
    random.seed(20261117)
    not_pressed = evaluate_options(holder, players, GOAL, None, build_up=True, pressed=False)
    monkeypatch.setattr(decision, "reads_third_man_probability", lambda _h: 0.0)
    random.seed(20261117)
    unread = evaluate_options(holder, players, GOAL, None, build_up=True, pressed=True)
    assert _value_to(not_pressed, "B") == pytest.approx(_value_to(unread, "B"))
    # B déjà derrière la première ligne (22 m > 21 m) : pas de troisième homme, aucune majoration
    holder, players = _scene(b_x=22.0)
    values = {}
    for chance in (0.0, 1.0):
        monkeypatch.setattr(decision, "reads_third_man_probability", lambda _h, c=chance: c)
        random.seed(20261117)
        values[chance] = evaluate_options(holder, players, GOAL, None, build_up=True, pressed=True)
    assert _value_to(values[1.0], "B") == pytest.approx(_value_to(values[0.0], "B"))


def _share_to_b(note: int, pressed: bool, draws: int = 1000) -> float:
    holder, players = _scene(note)
    random.seed(20261117)
    return sum(getattr(choose_action(holder, players, GOAL, None, build_up=True, pressed=pressed).target, "name", None)
               == "B" for _ in range(draws)) / draws


def test_a_good_reader_finds_the_third_man_more_often_than_a_poor_one() -> None:
    # même scène, même profil : la lecture du pressing ajoute des passes vers B (qui remet à C) ; l'ajout est net pour
    # une lecture à 99 (80 % de chance de lire), faible à 11 (15 %), probabiliste dans les deux cas
    gain_99 = _share_to_b(99, True) - _share_to_b(99, False)
    gain_11 = _share_to_b(11, True) - _share_to_b(11, False)
    assert gain_99 > 0.08
    assert gain_99 > gain_11 + 0.05

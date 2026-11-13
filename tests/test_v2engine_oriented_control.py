"""Contrôle orienté (ticket v2-collectif/31b) : First Touch règle la chance d'orienter son contrôle (25 / 50 / 75 % à
11 / 55 / 99) ; orienté, le temps avant la première décision est x 0,6 et le corps se tourne aussitôt vers le jeu, côté
but, en gardant devant lui le ballon reçu ; non orienté, x 1,4 et le cap ne bouge pas. La moyenne attendue garde le
rythme calé avant (1,84 / 2,3 / 2,76 s)."""

from __future__ import annotations

import math
from dataclasses import replace

import pytest

from v2engine.ball_state import BallState
from v2engine.flux import seed_streams
from v2engine.geometry import Vec2
from v2engine.match import _step_ball
from v2engine.possession import (ORIENTED_FACTOR, RECEPTION_CALM_S, UNORIENTED_FACTOR, oriented_control_probability,
                                 orients_control, reception_delay_s)
from v2engine.reception import facing_to_goal_deg
from tests.scenes import player

WEST = Vec2(-1.0, 0.0)


def _touch(note: int):
    return player("R", x=50.0, y=34.0, **{"First_Touch": note})


def test_first_touch_sets_the_chance_to_orient_never_certain_nor_impossible() -> None:
    chances = [oriented_control_probability(_touch(n)) for n in (11, 55, 99)]
    assert chances == pytest.approx([0.25, 0.50, 0.75])
    assert oriented_control_probability(_touch(1)) == pytest.approx(0.25)  # bornée hors des repères
    assert oriented_control_probability(_touch(100)) == pytest.approx(0.75)


def test_oriented_control_shortens_the_time_before_the_next_action() -> None:
    """Critère du ticket : orienté 1,38 s, non orienté 3,22 s (x 0,6 et x 1,4 de 2,3 s), quelle que soit la note."""
    receiver = _touch(55)
    oriented, plain = reception_delay_s(receiver, oriented=True), reception_delay_s(receiver, oriented=False)
    assert oriented == pytest.approx(RECEPTION_CALM_S * ORIENTED_FACTOR) == pytest.approx(1.38)
    assert plain == pytest.approx(RECEPTION_CALM_S * UNORIENTED_FACTOR) == pytest.approx(3.22)
    assert plain - oriented == pytest.approx(1.84)


def test_expected_time_keeps_the_rhythm_and_matches_the_draws() -> None:
    """Moyenne attendue (ballon gagné hors passe, sans tirage) = moyenne des tirages, à 2 % près sur 4 000 tirages."""
    for note, expected in ((11, 2.76), (55, 2.3), (99, 1.84)):
        receiver = _touch(note)
        assert reception_delay_s(receiver) == pytest.approx(expected)
        seed_streams(note)
        drawn = [reception_delay_s(receiver, oriented=orients_control(receiver)) for _ in range(4000)]
        assert sum(drawn) / len(drawn) == pytest.approx(expected, rel=0.02)


def _receive(monkeypatch, oriented: bool):
    """Receveur au milieu, dos au but adverse (cap vers l'ouest), passe qui arrive de l'ouest (il fait face au ballon)."""
    monkeypatch.setattr("v2engine.match.attempt_control", lambda *args: True)
    monkeypatch.setattr("v2engine.match.orients_control", lambda p: oriented)
    monkeypatch.setattr("v2engine.match.thinks_one_touch", lambda *args: False)
    receiver = replace(_touch(55), facing=WEST)
    ball = BallState(position=Vec2(49.6, 34.0), velocity=Vec2(6.0, 0.0), receiver="R", released_by="Passeur")
    passer = player("Passeur", x=30.0, y=34.0)
    _step_ball(ball, 0.1, [receiver, passer], 10.0, None, None, None)
    return receiver, ball


def test_oriented_control_turns_the_body_towards_the_play_keeping_the_ball_in_front(monkeypatch) -> None:
    receiver, ball = _receive(monkeypatch, True)
    assert ball.holder == "R"
    assert facing_to_goal_deg(receiver.facing, receiver.position, "home") == pytest.approx(90.0)  # de profil, ouvert
    ball_from = math.degrees(math.acos(receiver.facing.x * WEST.x + receiver.facing.y * WEST.y))
    assert ball_from <= 90.0 + 1e-6  # le ballon reçu reste devant lui
    assert ball.next_decision_s == pytest.approx(10.0 + 1.38)


def test_plain_control_keeps_the_body_and_takes_longer(monkeypatch) -> None:
    receiver, ball = _receive(monkeypatch, False)
    assert receiver.facing == WEST
    assert ball.next_decision_s == pytest.approx(10.0 + 3.22)

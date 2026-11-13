"""Agility règle la vitesse de rotation du corps (ticket v2-realisme/07f) : demi-tour en 0,67 s à 11, 0,5 s à 55,
0,4 s à 99 (repères linéaires, comme Pace et Acceleration). Le cap reste sans effet sur le déplacement."""

from __future__ import annotations

import math

import pytest

from v2engine.geometry import Vec2
from v2engine.movement import TURN_RATE_RAD_S, step, turn_rate_rad_s
from tests.scenes import player, with_attribute

DT = 0.02


def _angle(v: Vec2) -> float:
    return math.degrees(math.atan2(v.y, v.x))


def _half_turn_s(agility: int) -> float:
    """Durée d'un demi-tour demandé (ballon dans le dos, joueur arrêté), au pas `DT`."""
    p = player("A", x=50.0, y=34.0, Agility=agility)
    p = p.__class__(**{**p.__dict__, "facing": Vec2(1.0, 0.0)})
    ball = Vec2(40.0, 34.0001)
    steps = 0
    while abs(_angle(p.facing)) < 179.9 and steps < 500:
        p = step(p, DT, p.position, 0.0, look_at=ball)
        steps += 1
    return steps * DT


def test_turn_rate_points_and_bounds() -> None:
    assert math.degrees(turn_rate_rad_s(11)) == pytest.approx(270.0)
    assert math.degrees(turn_rate_rad_s(55)) == pytest.approx(360.0)
    assert math.degrees(turn_rate_rad_s(99)) == pytest.approx(450.0)
    assert turn_rate_rad_s(55) == pytest.approx(TURN_RATE_RAD_S)  # joueur moyen : la rotation du 07a
    assert turn_rate_rad_s(1) == turn_rate_rad_s(11) and turn_rate_rad_s(100) == turn_rate_rad_s(99)  # bornée
    rates = [turn_rate_rad_s(n) for n in range(11, 100)]
    assert all(b > a for a, b in zip(rates, rates[1:]))


def test_agility_99_turns_faster_than_11_by_the_validated_ratio() -> None:
    """Scène A/B : demi-tour 0,40 s contre 0,67 s (rapport 1,67), à un pas près."""
    fast, slow = _half_turn_s(99), _half_turn_s(11)
    assert fast == pytest.approx(0.4, abs=DT)
    assert slow == pytest.approx(180.0 / 270.0, abs=DT)
    assert slow / fast == pytest.approx(450.0 / 270.0, rel=0.06)
    assert _half_turn_s(55) == pytest.approx(0.5, abs=DT)


def test_agility_changes_the_facing_only_not_the_run() -> None:
    """Même course, deux Agility : positions et vitesses identiques, seul le cap diffère (sans effet sur le jeu)."""
    base = player("A", x=50.0, y=34.0)
    base = base.__class__(**{**base.__dict__, "facing": Vec2(-1.0, 0.0)})
    low, high = with_attribute([base], "Agility", 11)[0], with_attribute([base], "Agility", 99)[0]
    ball = Vec2(70.0, 40.0)
    target = Vec2(60.0, 30.0)
    for _ in range(10):
        low = step(low, DT, target, 0.6, look_at=ball)
        high = step(high, DT, target, 0.6, look_at=ball)
    assert low.position == high.position and low.velocity == high.velocity
    to_ball = _angle(ball - high.position)
    assert abs(_angle(high.facing) - to_ball) < abs(_angle(low.facing) - _angle(ball - low.position))

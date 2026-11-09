"""Déviation au contact d'un corps (ticket v2-realisme/05d) : la direction de sortie dépend du point d'impact sur le corps
et d'un coefficient de restitution, avec un écart aléatoire borné ; utilisée par le contre (05c)."""

from __future__ import annotations

import math
import random

from v2engine import match
from v2engine.geometry import Vec2
from v2engine.possession import DEFLECTION_NOISE_DEG, DEFLECTION_RESTITUTION, deflect
from v2engine.shooting import BLOCK_BODY_M

BODY = Vec2(50.0, 34.0)
SHOT = Vec2(30.0, 0.0)  # tir vers les x croissants
REACH = 1.0


def _angle_deg(a: Vec2, b: Vec2) -> float:
    cos = (a.x * b.x + a.y * b.y) / (a.length() * b.length())
    return math.degrees(math.acos(max(-1.0, min(1.0, cos))))


def _outs(offset_y: float, n: int = 200) -> list[Vec2]:
    rng = random.Random(5)
    return [deflect(SHOT, Vec2(BODY.x, BODY.y + offset_y), BODY, REACH, rng) for _ in range(n)]


def test_a_contact_in_the_axis_sends_the_ball_back_towards_the_shooter_slower() -> None:
    for out in _outs(0.0):
        assert _angle_deg(out, SHOT) >= 180.0 - DEFLECTION_NOISE_DEG - 1e-9  # renvoyé vers le tireur, à l'écart près
        assert math.isclose(out.length(), DEFLECTION_RESTITUTION * SHOT.length(), rel_tol=1e-9)


def test_an_off_centre_contact_deflects_the_ball_on_the_side_of_the_impact() -> None:
    left, right = _outs(0.5), _outs(-0.5)  # ballon passé à 0,5 m à gauche, puis à droite du centre du corps
    assert all(out.y > 0.0 for out in left) and all(out.y < 0.0 for out in right)
    mean = sum(_angle_deg(out, SHOT) for out in left) / len(left)
    assert 60.0 < mean < 150.0  # dévié de côté, ni continué ni renvoyé dans l'axe


def test_a_grazing_contact_barely_changes_the_ball() -> None:
    for out in _outs(0.98):
        assert _angle_deg(out, SHOT) < DEFLECTION_NOISE_DEG + 30.0 and out.length() > 0.9 * SHOT.length()


def test_the_more_central_the_impact_the_more_the_ball_turns_back() -> None:
    means = [sum(_angle_deg(o, SHOT) for o in _outs(y)) / 200 for y in (0.9, 0.6, 0.3, 0.0)]
    assert means == sorted(means)


def test_a_block_starts_from_the_point_where_the_ball_enters_the_reach_and_traces_its_exit(monkeypatch) -> None:
    # réserve A1 de l'expert du 05c : défenseur à 2 m dans l'axe, son corps seul (0,41 m) : contact à 1,59 m du tireur
    from tests.test_v2engine_contre import SHOOTER_AT, _shoot

    monkeypatch.setattr(match, "BLOCK_CHANCE", 1.0)
    shot, ball = _shoot(monkeypatch, SHOOTER_AT + Vec2(2.0, 0.0), error=(0.0, 0.0))
    assert shot.outcome == "contré"
    assert math.isclose(shot.block_x - SHOOTER_AT.x, 2.0 - BLOCK_BODY_M, abs_tol=1e-6)
    assert shot.block_exit_deg is not None and shot.block_exit_deg > 150.0  # dans l'axe : renvoyé vers le tireur
    assert ball.velocity.x < 0.0

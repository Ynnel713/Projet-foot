"""Gardien (tickets v2-realisme/03a et 03b) : placement sur la bissectrice de l'angle ballon-poteaux."""

from __future__ import annotations

import math

import pytest

from tests.scenes import Scene, player, run
from v2engine import cerveau, gardien
from v2engine.ball_state import BallState
from v2engine.geometry import PENALTY_AREA_DEPTH_M, PENALTY_AREA_WIDTH_M, PITCH_LENGTH_M, Vec2

GOAL_HOME, GOAL_AWAY = Vec2(0.0, 34.0), Vec2(PITCH_LENGTH_M, 34.0)


def _keeper(team: str = "home", x: float = 5.0):
    return player("G", team, x, 34.0, "GK")


def _angle(a: Vec2, b: Vec2, c: Vec2) -> float:
    """Angle (rad) en `a` entre les directions vers `b` et `c`."""
    u, v = (b - a).normalized(), (c - a).normalized()
    return math.acos(max(-1.0, min(1.0, u.x * v.x + u.y * v.y)))


def test_the_point_is_on_the_bisector_of_the_angle_between_the_posts() -> None:
    for ball in (Vec2(30, 34), Vec2(25, 12), Vec2(20, 50), Vec2(45, 30)):
        point = gardien.bisector_point(_keeper(), ball)
        post_low, post_high = Vec2(0.0, 34.0 - 3.66), Vec2(0.0, 34.0 + 3.66)
        assert _angle(ball, post_low, point) == pytest.approx(_angle(ball, point, post_high), abs=0.01)


def test_depth_grows_with_the_ball_distance_and_stays_in_the_area() -> None:
    depths = [gardien.bisector_point(_keeper(), Vec2(x, 34.0)).x for x in (4.0, 12.0, 20.0, 30.0, 40.0, 60.0)]
    assert depths[0] == pytest.approx(gardien.DEPTH_M[0])  # ballon à 4 m de sa ligne : près de sa ligne
    assert depths[1] == pytest.approx(gardien.DEPTH_M[0]) and depths[4] == pytest.approx(gardien.DEPTH_M[1])
    assert depths[5] == pytest.approx(gardien.DEPTH_M[1])
    assert depths[1] < depths[2] < depths[3] < depths[4]
    for ball in (Vec2(50, 2), Vec2(2, 2), Vec2(3, 66), Vec2(0.3, 34), Vec2(40, 34)):
        p = gardien.bisector_point(_keeper(), ball)
        assert 0.0 <= p.x <= PENALTY_AREA_DEPTH_M and abs(p.y - 34.0) <= PENALTY_AREA_WIDTH_M / 2.0


def test_the_keeper_follows_the_ball_side_symmetrically_and_for_both_teams() -> None:
    left, right = gardien.bisector_point(_keeper(), Vec2(25, 10)), gardien.bisector_point(_keeper(), Vec2(25, 58))
    assert left.y < 34.0 < right.y and left.x == pytest.approx(right.x)
    assert 34.0 - left.y == pytest.approx(right.y - 34.0)
    # l'équipe visiteuse défend x = 105 : image dans un miroir de l'équipe domicile
    away = gardien.bisector_point(_keeper("away", PITCH_LENGTH_M - 5.0), Vec2(PITCH_LENGTH_M - 25, 10))
    assert away.x == pytest.approx(PITCH_LENGTH_M - left.x) and away.y == pytest.approx(left.y)


def test_a_ball_beside_the_goal_line_puts_the_keeper_at_the_minimum_depth() -> None:
    near_post = gardien.bisector_point(_keeper(), Vec2(3.0, 10.0))
    assert near_post.x == pytest.approx(gardien.DEPTH_M[0])  # le ballon est plus près de la ligne que 4 m : profondeur minimale


def test_the_placement_state_targets_the_bisector_point() -> None:
    keeper, far = _keeper(), player("D", "home", 30.0, 34.0, "DC")
    ball = BallState(position=Vec2(40.0, 20.0), velocity=Vec2(0.0, 0.0))
    intention = cerveau.think(keeper, ball, [keeper, far], 1.0, {})
    assert intention.reason.startswith("placement") and intention.target == gardien.bisector_point(keeper, ball.position)


@pytest.mark.parametrize("ball_at", [Vec2(52.0, 34.0), Vec2(30.0, 12.0), Vec2(30.0, 56.0), Vec2(45.0, 20.0)])
def test_the_keeper_reaches_the_bisector_point_within_three_seconds(ball_at: Vec2) -> None:
    # ballon libre et immobile ; un coéquipier plus proche du ballon, qui ne peut pas le toucher, laisse le gardien en
    # état de placement (le plus proche de son équipe sortirait)
    keeper, mate = _keeper(), player("D", "home", ball_at.x - 3.0, ball_at.y, "DC")
    ball = BallState(position=ball_at, velocity=Vec2(0.0, 0.0))
    ball.control_ban_until_s[mate.name] = 99.0
    scene = Scene([keeper, mate], ball, runs={}, intentions={})
    run(scene, 3.0)
    assert scene.get("G").position.distance_to(gardien.bisector_point(keeper, ball_at)) < 0.5

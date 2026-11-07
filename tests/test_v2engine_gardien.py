"""Gardien (tickets v2-realisme/03a, 03b et 03c) : placement sur la bissectrice de l'angle ballon-poteaux, plus avancé
quand la ligne défensive est haute et le ballon loin."""

from __future__ import annotations

import math

import pytest

from tests.scenes import Scene, player, run
from v2engine import cerveau, gardien
from v2engine.ball_state import BallState
from v2engine.bloc import Bloc
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


def test_a_higher_line_pushes_the_keeper_forward_when_the_ball_is_far() -> None:
    far = Vec2(60.0, 34.0)
    low, high = gardien.bisector_point(_keeper(), far, 20.0).x, gardien.bisector_point(_keeper(), far, 40.0).x
    assert low == pytest.approx(gardien.DEPTH_M[1])  # ligne à 20 m : 0,4 x 20 = 8 m, pas plus loin que le 03b
    assert high == pytest.approx(gardien.DEPTH_LINE_MAX_M) and high > low + 5.0
    assert gardien.bisector_point(_keeper(), far, None).x == pytest.approx(low)  # sans ligne connue : le 03b


def test_the_depth_grows_with_the_line_and_stays_capped_inside_the_area() -> None:
    depths = [gardien.bisector_point(_keeper(), Vec2(60.0, 34.0), line).x for line in (5.0, 20.0, 25.0, 30.0, 35.0, 40.0, 55.0)]
    assert depths == sorted(depths) and depths[2] < depths[3] < depths[4]
    assert max(depths) == pytest.approx(gardien.DEPTH_LINE_MAX_M) and max(depths) < PENALTY_AREA_DEPTH_M


def test_the_line_counts_in_proportion_to_the_ball_distance_and_not_at_all_near_the_goal() -> None:
    near = Vec2(12.0, 34.0)  # ballon à 12 m : la ligne ne change rien (la bissectrice du 03b reste entière)
    assert gardien.bisector_point(_keeper(), near, 45.0) == gardien.bisector_point(_keeper(), near)
    middle = [gardien.bisector_point(_keeper(), Vec2(x, 34.0), 40.0).x for x in (12.0, 20.0, 30.0, 40.0)]
    assert middle == sorted(middle) and middle[0] == pytest.approx(gardien.DEPTH_M[0])


def test_the_point_stays_on_the_bisector_with_a_high_line() -> None:
    for ball in (Vec2(55, 34), Vec2(45, 12), Vec2(48, 60)):
        point = gardien.bisector_point(_keeper(), ball, 45.0)
        post_low, post_high = Vec2(0.0, 34.0 - 3.66), Vec2(0.0, 34.0 + 3.66)
        assert _angle(ball, post_low, point) == pytest.approx(_angle(ball, point, post_high), abs=0.01)


def test_the_brain_reads_the_line_of_the_bloc_of_its_own_team_at_that_instant() -> None:
    keeper, mate = _keeper(), player("D", "home", 40.0, 34.0, "DC")
    ball = BallState(position=Vec2(70.0, 34.0), velocity=Vec2(0.0, 0.0))
    bloc = Bloc(shapes={}, lines={"home": 40.0, "away": 10.0})
    with_line = cerveau.think(keeper, ball, [keeper, mate], 1.0, {}, bloc=bloc)
    assert with_line.target == gardien.bisector_point(keeper, ball.position, 40.0) and with_line.target.x > gardien.DEPTH_M[1]
    without = cerveau.think(keeper, ball, [keeper, mate], 1.0, {})
    assert without.target == gardien.bisector_point(keeper, ball.position)
    away = player("G2", "away", PITCH_LENGTH_M - 5.0, 34.0, "GK")  # l'équipe visiteuse lit sa propre ligne (10 m)
    other = cerveau.think(away, ball, [away, player("D2", "away", 80.0, 34.0, "DC")], 1.0, {}, bloc=bloc)
    assert other.target == gardien.bisector_point(away, ball.position, 10.0)


# --- Sortie sur un ballon libre (ticket v2-realisme/03d) -------------------------------------------------------------
def _loose_ball(at: Vec2, rival_x: float | None, keeper_x: float = 5.0):
    keeper = _keeper(x=keeper_x)
    players = [keeper]
    if rival_x is not None:
        players.append(player("A", "away", rival_x, 34.0, "BU"))
    return keeper, BallState(position=at, velocity=Vec2(0.0, 0.0)), players


def test_the_keeper_rushes_when_the_attacker_is_much_farther_and_stays_when_he_is_closer() -> None:
    keeper, ball, far = _loose_ball(Vec2(25.0, 34.0), rival_x=55.0)  # lui à 20 m du ballon, l'attaquant à 30 m
    assert gardien.race(keeper, ball, far).rush
    out = cerveau.think(keeper, ball, far, 1.0, {})
    assert out.reason.startswith("sortie") and "il arrive en" in out.reason  # décision tracée avec les deux temps
    keeper, ball, close = _loose_ball(Vec2(25.0, 34.0), rival_x=35.0)  # l'attaquant à 10 m
    assert not gardien.race(keeper, ball, close).rush
    stays = cerveau.think(keeper, ball, close, 1.0, {})
    assert stays.reason.startswith("placement") and "arrive avant lui" in stays.reason
    assert stays.target == gardien.bisector_point(keeper, ball.position)


def test_the_margin_decides_between_two_attackers_a_little_before_and_after() -> None:
    from v2engine.movement import max_speed_mps
    speed = max_speed_mps(60)
    for gap_s, expected in ((gardien.RUSH_MARGIN_S - 0.2, False), (gardien.RUSH_MARGIN_S + 0.2, True)):
        keeper, ball, players = _loose_ball(Vec2(25.0, 34.0), rival_x=25.0 + 20.0 + gap_s * speed)  # même vitesse et même montée
        assert gardien.race(keeper, ball, players).rush is expected


def test_no_rush_beyond_the_distance_cap_even_without_any_attacker() -> None:
    near = _loose_ball(Vec2(gardien.RUSH_MAX_FROM_GOAL_M - 3.0, 34.0), rival_x=None, keeper_x=20.0)
    far = _loose_ball(Vec2(gardien.RUSH_MAX_FROM_GOAL_M + 3.0, 34.0), rival_x=None, keeper_x=20.0)
    assert gardien.race(near[0], near[1], near[2]).rush and not gardien.race(far[0], far[1], far[2]).rush
    assert "trop loin de son but" in cerveau.think(far[0], far[1], far[2], 1.0, {}).reason


def test_the_rival_goalkeeper_does_not_count_as_a_rival_and_the_race_is_mirrored_for_the_away_team() -> None:
    keeper, ball, players = _loose_ball(Vec2(25.0, 34.0), rival_x=None)
    players.append(player("G2", "away", 24.0, 34.0, "GK"))  # le gardien adverse, tout près : ignoré
    assert gardien.race(keeper, ball, players).rush
    away = player("G", "away", PITCH_LENGTH_M - 5.0, 34.0, "GK")
    mirror = [away, player("A", "home", PITCH_LENGTH_M - 55.0, 34.0, "BU")]
    mirror_ball = BallState(position=Vec2(PITCH_LENGTH_M - 25.0, 34.0), velocity=Vec2(0.0, 0.0))
    assert gardien.race(away, mirror_ball, mirror).rush
    assert gardien.race(away, mirror_ball, [away, player("A", "home", PITCH_LENGTH_M - 35.0, 34.0, "BU")]).rush is False


def test_the_keeper_does_not_chase_a_pass_of_his_own_team_but_chases_the_same_ball_when_it_is_loose() -> None:
    keeper, ball, players = _loose_ball(Vec2(20.0, 34.0), rival_x=None, keeper_x=8.0)
    mate = player("D", "home", 30.0, 34.0, "DC")
    players.append(mate)
    ball.velocity, ball.receiver, ball.last_pass_team = Vec2(-5.0, 0.0), "D", "home"  # passe de son équipe, en vol
    assert cerveau.think(keeper, ball, players, 1.0, {}).reason.startswith("placement")
    ball.receiver = None  # la passe est ratée : ballon libre
    assert cerveau.think(keeper, ball, players, 1.0, {}).reason.startswith("sortie")


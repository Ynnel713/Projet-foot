"""Orientation du corps (ticket v2-realisme/07a) : un cap propre à chaque joueur, distinct de sa vitesse, qui tourne vers
la direction voulue à `TURN_RATE_RAD_S` au plus ; le ballon par défaut, le sens de course en course rapide. Tracé et
transmis à l'écran, sans effet sur le jeu."""

from __future__ import annotations

import math

import pytest

from v2engine.geometry import PITCH_LENGTH_M, PITCH_WIDTH_M, Vec2
from v2engine.match import _build_players, _facing_at_kickoff
from v2engine.movement import (FACING_RUN_SPEED_MPS, TURN_RATE_RAD_S, desired_facing, step, turn_rate_rad_s,
                               turn_toward)
from tests.scenes import player

DT = 0.1


def _angle(v: Vec2) -> float:
    return math.degrees(math.atan2(v.y, v.x))


def test_turn_rate_is_a_half_turn_in_half_a_second() -> None:
    assert math.isclose(TURN_RATE_RAD_S, math.radians(360.0))
    assert math.isclose(FACING_RUN_SPEED_MPS, 19.8 / 3.6)


def test_half_turn_takes_180_degrees_over_the_turn_rate_to_one_step() -> None:
    """Demi-tour demandé (ballon dans son dos, joueur arrêté) : durée = 180° / vitesse angulaire, à un pas près."""
    p = player("A", x=50.0, y=34.0)
    p = p.__class__(**{**p.__dict__, "facing": Vec2(1.0, 0.0)})
    ball = Vec2(40.0, 34.0001)  # derrière lui, à peine décalé : le côté du demi-tour est défini
    steps = 0
    while abs(_angle(p.facing)) < 179.9 and steps < 100:
        p = step(p, DT, p.position, 0.0, look_at=ball)
        steps += 1
    expected = math.pi / turn_rate_rad_s(60) / DT  # Agility par défaut des scènes : 60 (ticket 07f)
    assert abs(steps - expected) <= 1.0
    assert p.velocity.length() < 1e-9  # il n'a pas bougé : le cap ne déplace pas le joueur


def test_turn_toward_is_bounded_and_takes_the_short_side() -> None:
    east = Vec2(1.0, 0.0)
    out = turn_toward(east, Vec2(0.0, 1.0), math.radians(30.0))
    assert math.isclose(_angle(out), 30.0, abs_tol=1e-9)
    out = turn_toward(east, Vec2(0.0, -1.0), math.radians(30.0))
    assert math.isclose(_angle(out), -30.0, abs_tol=1e-9)
    assert math.isclose(_angle(turn_toward(east, Vec2(1.0, 1.0), math.radians(90.0))), 45.0, abs_tol=1e-9)
    assert turn_toward(east, Vec2(0.0, 0.0), 1.0) == east  # rien à regarder : le cap ne bouge pas
    assert math.isclose(turn_toward(Vec2(0.0, 1.0), east, 1.0).length(), 1.0)


def test_facing_looks_at_the_ball_unless_running_fast() -> None:
    at = Vec2(50.0, 34.0)
    ball = Vec2(50.0, 44.0)
    slow, fast = Vec2(3.0, 0.0), Vec2(FACING_RUN_SPEED_MPS + 0.1, 0.0)
    assert _angle(desired_facing(at, slow, ball)) == pytest.approx(90.0)
    assert _angle(desired_facing(at, fast, ball)) == pytest.approx(0.0)
    assert _angle(desired_facing(at, slow, None)) == pytest.approx(0.0)  # pas de ballon : sens de course


def test_sprinting_player_turns_his_body_to_his_run() -> None:
    p = player("A", x=30.0, y=34.0, Pace=99, Acceleration=99)
    p = p.__class__(**{**p.__dict__, "facing": Vec2(-1.0, 0.0)})
    ball = Vec2(10.0, 34.0)  # derrière lui
    for _ in range(40):  # 4 s de sprint vers x croissant
        p = step(p, DT, Vec2(100.0, 34.0), 0.0, look_at=ball)
    assert p.velocity.length() >= FACING_RUN_SPEED_MPS
    assert abs(_angle(p.facing)) < 1.0


def test_facing_does_not_change_the_movement() -> None:
    """Même joueur, même cible : position et vitesse identiques quel que soit le ballon regardé."""
    a = b = player("A", x=30.0, y=20.0)
    for _ in range(30):
        a = step(a, DT, Vec2(60.0, 40.0), 0.0, look_at=Vec2(0.0, 0.0))
        b = step(b, DT, Vec2(60.0, 40.0), 0.0, look_at=Vec2(100.0, 68.0))
    assert (a.position, a.velocity) == (b.position, b.velocity)
    assert a.facing != b.facing


def test_kickoff_facing_points_at_the_centre_spot() -> None:
    centre = Vec2(PITCH_LENGTH_M / 2.0, PITCH_WIDTH_M / 2.0)
    f = _facing_at_kickoff(Vec2(20.0, 34.0), "home")
    assert _angle(f) == pytest.approx(0.0)
    assert _angle(_facing_at_kickoff(Vec2(80.0, 10.0), "away")) == pytest.approx(_angle(centre - Vec2(80.0, 10.0)))
    assert _facing_at_kickoff(centre, "away") == Vec2(-1.0, 0.0)  # au point central : vers le but adverse


def test_built_players_start_facing_the_ball() -> None:
    from ligue1sim.clubs import load_clubs
    from ligue1sim.lineup import pick_best_formation
    from ligue1sim.season import CLUBS_PATH

    club = load_clubs(CLUBS_PATH, "Ligue 1")[0]
    lineup = pick_best_formation(club)
    positions = {p.name: Vec2(10.0 + i, 5.0 + 3.0 * i) for i, p in enumerate(lineup.players)}
    for p in _build_players(lineup, "home", positions):
        assert math.isclose(p.facing.length(), 1.0)
        assert p.facing == _facing_at_kickoff(p.position, "home")


def test_trace_and_api_carry_the_facing() -> None:
    from api.routers.v2 import _tick_out
    from v2engine.trace import BallSnapshot, PlayerSnapshot, Tick

    players = (PlayerSnapshot(name="A", team="home", poste="MC", position=Vec2(1.0, 2.0), facing=Vec2(0.0, -1.0)),)
    out = _tick_out(Tick(minute=1.0, players=players, ball=BallSnapshot(Vec2(10.0, 20.0)))).players[0]
    assert out.facing == -90.0


def test_simulated_match_traces_a_turning_unit_facing() -> None:
    import random

    from ligue1sim.clubs import load_clubs
    from ligue1sim.season import CLUBS_PATH
    from v2engine.match import simulate_match

    clubs = load_clubs(CLUBS_PATH, "Ligue 1")
    random.seed(20260923)
    trace = simulate_match(clubs[0], clubs[1], duration_minutes=2.0)
    facings = [p.facing for tick in trace.ticks for p in tick.players]
    assert all(math.isclose(f.length(), 1.0, rel_tol=1e-9) for f in facings)
    assert len({(round(f.x, 3), round(f.y, 3)) for f in facings}) > 22  # il tourne pendant le jeu

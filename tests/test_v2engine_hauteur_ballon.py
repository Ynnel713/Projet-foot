"""Hauteur du ballon dans le moteur V2 (ticket v2-hauteur-ballon/02a1) : vol en chute libre, point de chute, rebonds,
mode « aérien » calculé sur la hauteur, et scène d'un joueur sous la trajectoire."""

from __future__ import annotations

import math
import random

import pytest

from v2engine.ball_state import BallState
from v2engine.geometry import Vec2
from v2engine.match import _step_ball
from v2engine.movement import PlayerState
from v2engine.possession import BALL_FRICTION_PER_S, BALL_STOPPED_MPS, IDEAL_ARRIVAL_MPS
from v2engine.restart import AERIEN, SOL
from v2engine.vol import (AERIAL_HEIGHT_M, BOUNCE_HORIZONTAL_KEEP, BOUNCE_STOP_M, GRAVITY_MPS2, GROUND_RESTITUTION,
                          MAX_FLIGHT_S, flight_time_s, height_at, launch_vz, step_height)

DT = 0.1
LAMBDA = -math.log(BALL_FRICTION_PER_S)


def _p(name: str, x: float, y: float, team: str = "home") -> PlayerState:
    return PlayerState(name=name, team=team, poste="MC", position=Vec2(x, y), velocity=Vec2(0.0, 0.0), pace=60,
                       acceleration=60, stamina=60, home_target=Vec2(x, y))


def test_constants_validated_by_the_owner() -> None:
    assert (GRAVITY_MPS2, GROUND_RESTITUTION, BOUNCE_HORIZONTAL_KEEP, BOUNCE_STOP_M, MAX_FLIGHT_S, AERIAL_HEIGHT_M) == (
        9.81, 0.70, 0.85, 0.15, 4.0, 2.5)


def test_free_flight_apex_and_duration_match_the_closed_form() -> None:
    vz0 = 12.0
    z, vz, peak, t = 0.0, vz0, 0.0, 0.0
    while True:
        z, vz, impacts = step_height(z, vz, DT)
        t += DT
        if impacts:
            break
        peak = max(peak, z)
    assert peak == pytest.approx(vz0 ** 2 / (2.0 * GRAVITY_MPS2), rel=0.02)
    assert abs(t - 2.0 * vz0 / GRAVITY_MPS2) <= DT  # durée de vol à moins d'un pas
    assert height_at(0.0, vz0, 2.0 * vz0 / GRAVITY_MPS2 - 1e-9) == pytest.approx(0.0, abs=1e-6)


def test_bounce_reaches_049_of_the_previous_apex_then_the_ball_rolls() -> None:
    z, vz = 10.0, 0.0
    apexes, current, rising, steps = [], 0.0, False, 0
    while (z > 0.0 or vz > 0.0) and steps < 1000:
        z, vz, impacts = step_height(z, vz, 0.01)
        steps += 1
        if impacts:
            rising, current = True, 0.0
        if rising:
            current = max(current, z)
            if vz < 0.0:
                apexes.append(current)
                rising = False
    assert z == 0.0 and vz == 0.0 and steps < 1000  # il finit par rouler
    previous = 10.0
    for apex in apexes[:3]:
        assert apex == pytest.approx(GROUND_RESTITUTION ** 2 * previous, rel=0.05)
        previous = apex
    assert all(apex >= BOUNCE_STOP_M for apex in apexes)


def test_impact_is_cut_at_its_exact_instant_and_never_under_the_ground() -> None:
    z, vz, impacts = step_height(0.05, -5.0, DT)  # le sol est atteint en 0,01 s : rebond dans le même pas
    assert impacts == 1 and z > 0.0 and vz > 0.0
    for start in (0.0, 0.3, 2.0, 15.0):
        for speed in (-12.0, -1.0, 0.0, 4.0, 20.0):
            for dt in (0.01, 0.1, 0.5):
                assert step_height(start, speed, dt)[0] >= 0.0


def test_flight_time_follows_the_braked_distance_and_is_capped() -> None:
    v0 = IDEAL_ARRIVAL_MPS + 30.0 * LAMBDA  # passe de 30 m qui arrive à 6 m/s
    t = flight_time_s(30.0, v0)
    assert v0 * (1.0 - BALL_FRICTION_PER_S ** t) / LAMBDA == pytest.approx(30.0, rel=1e-9)
    q = BALL_FRICTION_PER_S ** DT  # sur l'avance pas à pas du moteur : n pas de v·dt freinés
    n = flight_time_s(30.0, v0, DT) / DT
    assert v0 * DT * (1.0 - q ** n) / (1.0 - q) == pytest.approx(30.0, rel=1e-9)
    assert flight_time_s(55.0, 30.0) == MAX_FLIGHT_S  # sans plafond : 5,4 s et 36 m de haut
    assert flight_time_s(80.0, 30.0) == MAX_FLIGHT_S  # n'arriverait jamais : retombe avant
    assert launch_vz(55.0, 30.0) ** 2 / (2.0 * GRAVITY_MPS2) == pytest.approx(19.6, abs=0.1)


def _landing(distance: float, speed: float) -> tuple[float, int]:
    """Distance parcourue par un ballon en l'air au premier impact, et nombre de pas."""
    ball = BallState(position=Vec2(5.0, 34.0), velocity=Vec2(speed, 0.0), vz=launch_vz(distance, speed, DT))
    for i in range(200):
        vz_before = ball.vz
        _step_ball(ball, DT, [], i * DT)
        if vz_before < 0.0 and ball.vz >= 0.0:  # il descendait, il remonte ou roule : impact pendant le pas
            return ball.position.x - 5.0, i + 1
    raise AssertionError("le ballon ne retombe pas")


@pytest.mark.parametrize("distance", [20.0, 30.0, 40.0, 45.0])
def test_aerial_pass_lands_on_its_aimed_point(distance: float) -> None:
    speed = IDEAL_ARRIVAL_MPS + distance * LAMBDA
    travelled, _ = _landing(distance, speed)
    # au premier impact, à 1 pas près : le ballon fait au plus vitesse d'arrivée x pas au-delà
    assert abs(travelled - distance) <= 1.0


def test_capped_flight_lands_short_of_its_target() -> None:
    travelled, steps = _landing(60.0, 30.0)
    assert travelled < 60.0 - 5.0 and abs(steps * DT - MAX_FLIGHT_S) <= DT


def test_mode_follows_the_height_while_the_ball_flies() -> None:
    ball = BallState(position=Vec2(5.0, 34.0), velocity=Vec2(26.0, 0.0), vz=launch_vz(40.0, 26.0))
    seen = set()
    for i in range(80):
        _step_ball(ball, DT, [], i * DT)
        assert ball.z >= 0.0
        assert (ball.mode == AERIEN) == (ball.z > AERIAL_HEIGHT_M)
        seen.add(ball.mode)
    assert seen == {AERIEN, SOL}


def test_player_under_the_flight_lets_it_pass_and_the_target_takes_it() -> None:
    under = _p("Sous", 25.0, 34.0, team="away")
    target = _p("Cible", 45.0, 34.0)
    speed = IDEAL_ARRIVAL_MPS + 40.0 * LAMBDA
    ball = BallState(position=Vec2(5.0, 34.0), velocity=Vec2(speed, 0.0), vz=launch_vz(40.0, speed, DT), receiver="Cible",
                     last_pass_team="home")
    random.seed(20261123)
    for i in range(60):
        _step_ball(ball, DT, [under, target], i * DT)
        if ball.holder is not None or ball.last_toucher is not None:
            break
    assert ball.last_toucher == "Cible"  # « Sous » ne l'a pas touché : il est passé au-dessus de lui
    assert ball.z == 0.0 or ball.holder is None


def test_ground_pass_never_leaves_the_ground() -> None:
    ball = BallState(position=Vec2(5.0, 34.0), velocity=Vec2(20.0, 0.0))
    for i in range(50):
        _step_ball(ball, DT, [], i * DT)
        assert ball.z == 0.0 and ball.mode == SOL
    assert ball.velocity.length() < BALL_STOPPED_MPS or ball.position.x > 5.0


def test_match_ball_is_never_under_the_ground_and_traced_mode_follows_its_height() -> None:
    from ligue1sim.clubs import load_clubs
    from ligue1sim.season import CLUBS_PATH
    from v2engine.match import simulate_match
    clubs = load_clubs(CLUBS_PATH, "Ligue 1")
    random.seed(20261123)
    trace = simulate_match(clubs[0], clubs[1], duration_minutes=15.0, tick_seconds=0.1)
    heights = [b.z for b in trace.ball_track]
    assert min(heights) >= 0.0 and max(heights) > AERIAL_HEIGHT_M  # des ballons en l'air en 15 minutes
    assert all((b.mode == AERIEN) == (b.z > AERIAL_HEIGHT_M) for b in trace.ball_track)
    assert all(t.ball.z == 0.0 for t in trace.ticks if t.ball.holder is not None)


def test_missed_control_in_the_air_falls_from_where_it_was_touched(monkeypatch) -> None:
    # réserve A3 de l'expert (choix du propriétaire, 23/11/2026) : un ballon raté pendant qu'il remonte d'un rebond garde
    # sa hauteur au contact mais ne monte plus ; il ne repasse jamais au-dessus de 2,5 m
    import v2engine.match as match
    monkeypatch.setattr(match, "attempt_control", lambda *args, **kwargs: False)
    player = _p("Rate", 10.5, 34.0)
    ball = BallState(position=Vec2(10.0, 34.0), velocity=Vec2(5.0, 0.0), z=1.0, vz=8.0)
    random.seed(20261123)
    _step_ball(ball, DT, [player], 0.0)
    assert ball.last_toucher == "Rate"
    assert ball.vz <= 0.0 and 1.0 <= ball.z <= AERIAL_HEIGHT_M and ball.mode == SOL
    for i in range(1, 30):
        _step_ball(ball, DT, [], i * DT)
        assert ball.z <= AERIAL_HEIGHT_M

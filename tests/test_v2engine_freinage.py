"""Loi de freinage du ballon : cohérence des fonctions entre elles (ticket v2-realisme/14a1, indépendante de la loi), un
seul module qui la connaît, et valeurs de la loi roulement + traînée (ticket v2-realisme/14a2a)."""

from __future__ import annotations

import math
import pathlib
import re

import pytest

from v2engine import freinage
from v2engine.geometry import Vec2

DT = 0.1
SPEEDS = (3.0, 8.0, 15.0, 22.5, 30.0)


@pytest.mark.parametrize("speed", SPEEDS)
@pytest.mark.parametrize("dt", (0.0, DT))
def test_travel_time_inverts_distance_after(speed: float, dt: float) -> None:
    for t in (0.3, 1.0, 2.5):
        if t >= freinage.time_to_slow(speed, 0.0) - dt:
            continue  # arrêt en temps fini (14a2a) : l'inverse n'existe qu'avant l'arrêt
        distance = freinage.distance_after(speed, t, dt)
        assert freinage.travel_time_s(distance, speed, dt) == pytest.approx(t, rel=1e-9)


def test_travel_time_edge_cases() -> None:
    assert freinage.travel_time_s(0.0, 5.0) == 0.0
    assert freinage.travel_time_s(10.0, 0.0) is None
    assert freinage.travel_time_s(freinage.distance_to_slow(5.0, 0.0) * 1.01, 5.0) is None  # s'arrête avant


@pytest.mark.parametrize("speed", SPEEDS)
def test_stepped_quantities_follow_the_engine_step(speed: float) -> None:
    """Au pas du moteur (`match._step_ball` : avance de v·dt puis `step_velocity`), distance et temps de trajet sont ceux
    de la boucle."""
    position, velocity, elapsed = 0.0, Vec2(speed, 0.0), 0.0
    for _ in range(30):
        position += velocity.x * DT
        velocity = freinage.step_velocity(velocity, DT)
        elapsed += DT
        assert freinage.distance_after(speed, elapsed, DT) == pytest.approx(position, abs=1e-9)  # réserve A3 du 14a2a
        assert velocity.x == pytest.approx(freinage.speed_after(speed, elapsed), rel=1e-9)
    target = 0.5 * position
    t = freinage.stepped_travel_time_s(target, speed, DT)
    assert t is not None and freinage.distance_after(speed, math.floor(t / DT + 1e-9) * DT, DT) <= target + 1e-9


@pytest.mark.parametrize("speed", SPEEDS)
def test_speed_distance_and_time_agree(speed: float) -> None:
    for distance in (2.0, 10.0):
        arrival = freinage.arrival_speed(speed, distance)
        if arrival <= 0.0:
            continue
        assert freinage.launch_speed(distance, arrival) == pytest.approx(speed)
        assert freinage.distance_to_slow(speed, arrival) == pytest.approx(distance)
        t = freinage.time_to_slow(speed, arrival)
        assert freinage.speed_after(speed, t) == pytest.approx(arrival)
        assert freinage.distance_after(speed, t) == pytest.approx(distance)


def test_positions_lie_on_the_straight_path() -> None:
    start, velocity = Vec2(30.0, 34.0), Vec2(9.0, -12.0)  # 15 m/s
    for t in (0.5, 1.5):
        point = freinage.position_after(start, velocity, t)
        assert start.distance_to(point) == pytest.approx(freinage.distance_after(15.0, t))
        assert (point - start).x * velocity.y == pytest.approx((point - start).y * velocity.x)
    stop = freinage.stop_position(start, velocity)
    assert start.distance_to(stop) == pytest.approx(freinage.distance_to_slow(15.0, 0.0))


def test_only_the_braking_module_knows_the_law() -> None:
    """Aucun autre module du moteur, script ou module d'API ne lit la constante de freinage ni ne la reçoit en paramètre."""
    root = pathlib.Path(__file__).resolve().parents[1]
    sources = [p for p in (root / "v2engine").glob("*.py") if p.name != "freinage.py"]
    sources += list((root / "scripts").glob("*.py")) + list((root / "api").rglob("*.py"))
    offenders = [p.name for p in sources if re.search(r"BALL_FRICTION_PER_S|friction_per_s", p.read_text(encoding="utf-8"))]
    assert offenders == []


# --- loi roulement + traînée (ticket v2-realisme/14a2a) -------------------------------------------------------------

def test_drag_coefficients_follow_the_validated_constants() -> None:
    from v2engine.match import BALL_RADIUS_M
    assert freinage.BALL_RADIUS_M == BALL_RADIUS_M
    assert freinage.K_LOW == pytest.approx(0.0244, abs=1e-4)  # Cd 0,45
    assert freinage.K_HIGH == pytest.approx(0.01354, abs=1e-4)  # Cd 0,25


def test_deceleration_values_and_drag_crisis() -> None:
    assert freinage.deceleration(25.0) == pytest.approx(9.66, abs=0.01)
    assert freinage.deceleration(10.0) == pytest.approx(3.64, abs=0.01)
    assert freinage.deceleration(0.0) == 0.0
    # crise en palier : juste sous 15 m/s, le ballon freine plus fort que juste au-dessus
    assert freinage.deceleration(14.99) > freinage.deceleration(15.0)


def test_reference_distances_and_speeds() -> None:
    assert freinage.distance_to_slow(15.0, 0.0) == pytest.approx(35.2, abs=0.2)  # passe au sol à 15 m/s (29 m avant)
    assert freinage.distance_to_slow(30.0, 0.5) == pytest.approx(77.6, abs=0.3)  # portée max d'une passe (57,8 avant)
    assert freinage.launch_speed(20.0, 6.0) == pytest.approx(13.3, abs=0.1)  # passe de 20 m arrivant à 6 m/s (16,2 avant)


@pytest.mark.parametrize("speed", SPEEDS)
def test_the_ball_stops_in_finite_time_and_never_goes_backwards(speed: float) -> None:
    stop_t = freinage.time_to_slow(speed, 0.0)
    assert math.isfinite(stop_t)
    assert freinage.speed_after(speed, stop_t + 0.01) == 0.0
    velocity, steps = Vec2(speed, 0.0), 0
    while velocity.x > 0.0:
        velocity = freinage.step_velocity(velocity, DT)
        steps += 1
        assert velocity.x >= 0.0
    assert steps == pytest.approx(stop_t / DT, abs=1.0)


@pytest.mark.parametrize("speed, distance", [(25.0, 10.0), (20.0, 30.0), (12.0, 5.0)])
def test_piecewise_solution_matches_a_fine_integration(speed: float, distance: float) -> None:
    """Solution exacte par morceaux contre une intégration fine (pas de 0,1 ms) de dv/dt = −(a + k(v)·v²)."""
    v, x, t, h = speed, 0.0, 0.0, 1e-4
    while x < distance:
        v -= freinage.deceleration(v) * h
        x += v * h
        t += h
    assert freinage.arrival_speed(speed, distance) == pytest.approx(v, abs=2e-3)
    assert freinage.travel_time_s(distance, speed) == pytest.approx(t, abs=2e-3)


def _with_rolling(monkeypatch, value: float) -> None:
    monkeypatch.setattr(freinage, "_A", value)


def test_a_20_m_pass_lies_inside_the_sourced_rolling_band(monkeypatch) -> None:
    """Encadrement par la source du roulement (FIFA, 0,6 à 1,5 m/s² ; fourchette du propriétaire 1,0 à 1,5) : passe de
    20 m partie à 14 m/s, temps de trajet et vitesse d'arrivée entre ceux d'un roulement à 1,0 et à 1,5 m/s²."""
    def pass_20m() -> tuple[float, float]:
        return freinage.travel_time_s(20.0, 14.0), freinage.arrival_speed(14.0, 20.0)
    time_ref, arrival_ref = pass_20m()
    _with_rolling(monkeypatch, 1.0)
    time_fast, arrival_fast = pass_20m()
    _with_rolling(monkeypatch, 1.5)
    time_slow, arrival_slow = pass_20m()
    assert time_fast < time_ref < time_slow
    assert arrival_slow < arrival_ref < arrival_fast
    assert time_ref == pytest.approx(2.06, abs=0.01) and arrival_ref == pytest.approx(6.58, abs=0.01)  # calcul analytique


def test_shots_use_the_engine_step_travel_time() -> None:
    """Fusion du temps de vol des tirs (recommandation de l'expert du 14a1) : `shooting` lit `travel_time_s` au pas."""
    from v2engine.shooting import _ENGINE_TICK_S, _flight_distance_m, _flight_time_s
    for distance in (5.0, 16.0, 30.0):
        assert _flight_time_s(distance) == freinage.travel_time_s(distance, 30.0, _ENGINE_TICK_S, airborne=True)
        assert _flight_distance_m(_flight_time_s(distance)) == pytest.approx(distance, abs=1e-9)
    assert _flight_time_s(1000.0) == math.inf


# --- en vol : traînée seule (ticket v2-realisme/14a2b) ---

def test_in_flight_drag_only_without_rolling() -> None:
    """En vol, pas de roulement : décélération `k·v²` seule (8,46 m/s² à 25 m/s, 2,44 à 10 m/s, calcul analytique),
    soit exactement celle du sol moins le roulement."""
    assert freinage.deceleration(25.0, airborne=True) == pytest.approx(8.46, abs=0.01)
    assert freinage.deceleration(10.0, airborne=True) == pytest.approx(2.44, abs=0.01)
    for speed in (3.0, 14.9, 15.0, 30.0):
        assert freinage.deceleration(speed) - freinage.deceleration(speed, airborne=True) == pytest.approx(
            freinage.ROLLING_DECEL_M_S2)


def test_in_flight_values() -> None:
    """Calcul analytique : de 30 à 15 m/s en vol, 51,2 m ; passe aérienne de 50 m à 23,4 m/s, 3,19 s de vol continu ;
    le ballon ne s'arrête pas en l'air."""
    t_half = freinage.travel_time_s(51.2, 30.0, airborne=True)
    assert freinage.speed_after(30.0, t_half, airborne=True) == pytest.approx(15.0, abs=0.05)
    assert freinage.travel_time_s(50.0, 23.4, airborne=True) == pytest.approx(3.19, abs=0.02)
    assert freinage.speed_after(30.0, 60.0, airborne=True) > 0.0
    for speed in (5.0, 20.0, 30.0):  # distance et temps continus inverses l'un de l'autre
        t = freinage.travel_time_s(40.0, speed, airborne=True)
        assert freinage.distance_after(speed, t, airborne=True) == pytest.approx(40.0, abs=1e-9)


def test_in_flight_finer_integration_agrees() -> None:
    """Solution exacte en vol contre une intégration fine (pas de 0,1 ms) de `dv/dt = −k(v)·v²`."""
    speed, x, h = 28.0, 0.0, 1e-4
    for _ in range(int(2.0 / h)):
        x += speed * h
        speed -= freinage.deceleration(speed, airborne=True) * h
    assert freinage.speed_after(28.0, 2.0, airborne=True) == pytest.approx(speed, abs=0.01)
    assert freinage.distance_after(28.0, 2.0, airborne=True) == pytest.approx(x, abs=0.01)


@pytest.mark.parametrize("speed", [6.0, 15.0, 23.4, 30.0])
def test_in_flight_stepped_quantities_follow_the_engine(speed: float) -> None:
    """Moteur réel (`match._step_ball`, ballon haut, sans joueur) : en vol, la vitesse suit `step_velocity` en vol et la
    distance au pas `distance_after(..., dt, airborne=True)` (écart absolu < 1e-9 m) ; le temps de trajet au pas en vol la
    retrouve."""
    from v2engine.ball_state import BallState
    from v2engine.match import TICK_SECONDS, _step_ball

    ball = BallState(position=Vec2(0.0, 34.0), velocity=Vec2(speed, 0.0), z=60.0, vz=0.0)  # haut : en vol tout du long
    elapsed = 0.0
    for i in range(25):
        _step_ball(ball, TICK_SECONDS, [], i * TICK_SECONDS)
        elapsed += TICK_SECONDS
        assert ball.z > 0.0
        assert ball.position.x == pytest.approx(freinage.distance_after(speed, elapsed, TICK_SECONDS, airborne=True),
                                                abs=1e-9)
        assert ball.velocity.x == pytest.approx(freinage.speed_after(speed, elapsed, airborne=True), rel=1e-12)
    target = 0.6 * ball.position.x
    t = freinage.travel_time_s(target, speed, TICK_SECONDS, airborne=True)
    assert freinage.distance_after(speed, t, TICK_SECONDS, airborne=True) == pytest.approx(target, abs=1e-9)


def test_ground_ball_keeps_the_rolling_law_in_the_engine() -> None:
    """Ballon au sol (`z = 0`, `vz = 0`) : le moteur garde la loi du 14a2a (roulement compris)."""
    from v2engine.ball_state import BallState
    from v2engine.match import TICK_SECONDS, _step_ball

    ball = BallState(position=Vec2(0.0, 34.0), velocity=Vec2(20.0, 0.0))
    _step_ball(ball, TICK_SECONDS, [], 0.0)
    assert ball.velocity.x == pytest.approx(freinage.speed_after(20.0, TICK_SECONDS))
    assert ball.velocity.x < freinage.speed_after(20.0, TICK_SECONDS, airborne=True)

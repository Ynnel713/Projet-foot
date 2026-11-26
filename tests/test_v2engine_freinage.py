"""Loi de freinage du ballon regroupée (ticket v2-realisme/14a1) : cohérence des fonctions entre elles (indépendante de la
loi, elle doit tenir après le 14a2), loi actuelle, et un seul module qui la connaît."""

from __future__ import annotations

import math
import pathlib
import re

import pytest

from v2engine import freinage
from v2engine.geometry import Vec2

DT = 0.1
SPEEDS = (3.0, 8.0, 15.0, 22.5, 30.0)


def test_current_law_is_the_exponential_braking() -> None:
    """Loi inchangée au 14a1 : vitesse × 0,6 par seconde (sera remplacée au 14a2)."""
    assert freinage.speed_after(10.0, 1.0) == pytest.approx(6.0)
    assert freinage.distance_to_slow(30.0, 0.5) == pytest.approx(57.8, abs=0.1)  # portée max d'une passe


@pytest.mark.parametrize("speed", SPEEDS)
@pytest.mark.parametrize("dt", (0.0, DT))
def test_travel_time_inverts_distance_after(speed: float, dt: float) -> None:
    for t in (0.3, 1.0, 2.5):
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
        assert freinage.distance_after(speed, elapsed, DT) == pytest.approx(position, rel=1e-9)
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


def test_shot_travel_time_is_the_stepped_travel_time() -> None:
    """Forme gardée pour les tirs (`shooting`) : même valeur que `travel_time_s` au pas du moteur, à l'arrondi près."""
    for distance in (5.0, 16.0, 30.0):
        assert freinage.shot_travel_time_s(distance, 30.0, DT) == pytest.approx(freinage.travel_time_s(distance, 30.0, DT))
    assert freinage.shot_travel_time_s(1000.0, 30.0, DT) == math.inf

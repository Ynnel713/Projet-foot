"""Freinage selon Agility (ticket v2-realisme/12a) : le freinage maximal n'est plus commun (7 m/s²) mais suit Agility
(6 m/s² à 11, 7 à 55, 8 à 99) ; un joueur agile s'arrête plus court, à tout pas de calcul."""

from __future__ import annotations

import pytest

from v2engine.geometry import Vec2
from v2engine.movement import DECEL_MAX_MPS2, PlayerState, decel_max_mps2, step
from tests.scenes import player

STEPS = (0.05, 0.1, 0.15)


def test_braking_curve_keeps_the_former_value_at_55() -> None:
    assert decel_max_mps2(11) == pytest.approx(6.0)
    assert decel_max_mps2(55) == pytest.approx(DECEL_MAX_MPS2) == pytest.approx(7.0)
    assert decel_max_mps2(99) == pytest.approx(8.0)
    assert decel_max_mps2(1) == pytest.approx(6.0) and decel_max_mps2(100) == pytest.approx(8.0)  # bornée


def _stop_from_7(agility: int, dt: float) -> tuple[float, float]:
    """Joueur lancé à 7 m/s vers l'est, à qui l'on demande de s'arrêter net (cible sur lui, à 40 % d'intensité nulle) :
    distance parcourue jusqu'à l'arrêt et pire freinage mesuré (m/s²)."""
    state: PlayerState = player("P", x=30.0, y=34.0, pace=99, acceleration=99, Agility=agility)
    state = PlayerState(**{**state.__dict__, "velocity": Vec2(7.0, 0.0), "facing": Vec2(1.0, 0.0)})
    start, worst = state.position, 0.0
    for _ in range(round(5.0 / dt)):
        before = state.velocity.length()
        state = step(state, dt, state.position, 0.0)  # cible : là où il est, il doit freiner
        worst = max(worst, (before - state.velocity.length()) / dt)
        if state.velocity.length() < 1e-6:
            break
    return state.position.distance_to(start), worst


@pytest.mark.parametrize("dt", STEPS)
def test_an_agile_player_stops_shorter(dt) -> None:
    """Scène A/B : Agility 99 contre 11, même vitesse de départ (7 m/s) : arrêt plus court, freinage borné par la courbe."""
    low, low_worst = _stop_from_7(11, dt)
    high, high_worst = _stop_from_7(99, dt)
    assert high < low
    assert low == pytest.approx(7.0 ** 2 / (2 * 6.0), abs=0.6)  # 4,1 m, à un pas près
    assert high == pytest.approx(7.0 ** 2 / (2 * 8.0), abs=0.6)  # 3,1 m
    assert low_worst <= 6.0 * 1.01 and high_worst <= 8.0 * 1.01


def test_arrival_law_uses_the_players_own_braking() -> None:
    """Loi d'arrivée : vers une cible à 10 m, l'agile garde sa vitesse plus tard (il freine plus fort) sans la dépasser."""
    def approach(agility: int) -> tuple[float, float]:
        state = player("P", x=30.0, y=34.0, pace=99, acceleration=99, Agility=agility)
        state = PlayerState(**{**state.__dict__, "velocity": Vec2(8.0, 0.0), "facing": Vec2(1.0, 0.0)})
        target, overshoot, speed_at_5m = Vec2(40.0, 34.0), 0.0, None
        for _ in range(60):
            state = step(state, 0.1, target, 0.0)
            overshoot = max(overshoot, state.position.x - target.x)
            if speed_at_5m is None and state.position.x >= 35.0:
                speed_at_5m = state.velocity.length()
        return speed_at_5m, overshoot
    (low_speed, low_over), (high_speed, high_over) = approach(11), approach(99)
    assert high_speed > low_speed
    assert low_over <= 0.5 and high_over <= 0.5

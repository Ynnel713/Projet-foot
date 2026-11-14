"""Sprints répétés (ticket v2-realisme/12f) : une réserve rapide (anaérobie) se vide de l'excès de vitesse au-dessus de
25 km/h et se recharge sous ce seuil (constante de temps selon Stamina : 40 s à 5, 30 s à 55, 20 s à 99) ; sous 80 % de
réserve, la part de vitesse au-dessus de 25 km/h baisse ; vide, il ne sprinte plus. Scène du ticket : 5 sprints de 30 m
espacés de 10 s, vitesse décroissante ; espacés de 60 s, stable."""

from __future__ import annotations

import math
from dataclasses import replace

import pytest

from v2engine.geometry import Vec2
from v2engine.movement import (SPRINT_KNEE, SPRINT_SPEED_MPS, max_speed_mps, spend_sprint_energy, sprint_cap_mps,
                               step)
from tests.scenes import player


def test_cap_is_full_above_the_knee_and_the_sprint_threshold_when_empty() -> None:
    fast = max_speed_mps(80)
    assert sprint_cap_mps(fast, 1.0) == pytest.approx(fast)
    assert sprint_cap_mps(fast, SPRINT_KNEE) == pytest.approx(fast)
    assert sprint_cap_mps(fast, 0.0) == pytest.approx(SPRINT_SPEED_MPS)  # vide : plus de sprint
    assert SPRINT_SPEED_MPS < sprint_cap_mps(fast, 0.4) < fast
    slow = SPRINT_SPEED_MPS * 0.95  # joueur qui n'atteint pas le seuil : rien ne change
    assert sprint_cap_mps(slow, 0.0) == pytest.approx(slow)


def test_reserve_drains_above_the_threshold_and_recovers_with_stamina() -> None:
    assert spend_sprint_energy(1.0, 55, SPRINT_SPEED_MPS + 2.0, 1.0) == pytest.approx(1.0 - 2.0 / 20.0)
    assert spend_sprint_energy(0.0, 55, SPRINT_SPEED_MPS + 50.0, 1.0) == 0.0  # bornée
    # sous le seuil : moitié du manque rendue en 30 s x ln 2 à Stamina 55, plus vite avec Stamina
    half = spend_sprint_energy(0.5, 55, 3.0, 30.0 * math.log(2.0))
    assert half == pytest.approx(0.75)
    assert spend_sprint_energy(0.5, 99, 3.0, 10.0) > spend_sprint_energy(0.5, 55, 3.0, 10.0) > spend_sprint_energy(
        0.5, 5, 3.0, 10.0)


def _series(gap_s: float, stamina: int = 55, n: int = 5, dt: float = 0.1) -> list[float]:
    """Vitesse de pointe de chacun des `n` sprints de 30 m départ arrêté, espacés de `gap_s` secondes de repos."""
    state = player("P", x=10.0, y=34.0, pace=80, acceleration=70, stamina=stamina)
    peaks = []
    for _ in range(n):
        start, peak = state.position.x, 0.0
        while state.position.x < start + 30.0:
            state = step(state, dt, Vec2(start + 40.0, 34.0), 0.0)
            peak = max(peak, state.velocity.length())
        peaks.append(peak)
        for _ in range(round(gap_s / dt)):  # il s'arrête puis récupère
            state = step(state, dt, state.position, 0.0)
        state = replace(state, position=Vec2(10.0, 34.0), velocity=Vec2(0.0, 0.0))
    return peaks


def test_sprints_ten_seconds_apart_get_slower() -> None:
    peaks = _series(10.0)
    assert all(b < a for a, b in zip(peaks, peaks[1:]))
    assert peaks[-1] < peaks[0] * 0.97  # environ -5 % au 5e sprint


def test_sprints_a_minute_apart_stay_stable() -> None:
    peaks = _series(60.0)
    assert peaks[-1] >= peaks[0] * 0.99


def test_stamina_recovers_faster_between_sprints() -> None:
    assert _series(20.0, stamina=99)[-1] > _series(20.0, stamina=55)[-1] > _series(20.0, stamina=5)[-1]


def test_one_short_sprint_is_untouched(monkeypatch) -> None:
    """Un sprint de 30 m départ arrêté n'est pas bridé : même pointe qu'avec une réserve rapide infinie (réserve A1 de
    l'expert au 12f : la référence passe par `SPRINT_RESERVE_M`, une réserve de départ au-dessus de 1 retombait à 1)."""
    fresh = _series(60.0, n=1)[0]
    monkeypatch.setattr("v2engine.movement.SPRINT_RESERVE_M", float("inf"))  # réserve infinie : la référence
    state = player("P", x=10.0, y=34.0, pace=80, acceleration=70)
    peak = 0.0
    while state.position.x < 40.0:
        state = step(state, 0.1, Vec2(50.0, 34.0), 0.0)
        peak = max(peak, state.velocity.length())
    assert fresh == pytest.approx(peak, abs=0.02)

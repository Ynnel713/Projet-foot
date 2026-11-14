"""Perte de vitesse en virage (ticket v2-realisme/12b) : la part de la variation de vitesse perpendiculaire à la course
est bornée selon Agility (4,5 m/s² à 11, 5,5 à 55, 6,5 à 99) ; un virage à 90° à pleine vitesse fait passer sous la
vitesse de départ, moins pour un joueur agile ; pas de cumul au-delà du réel avec le 07b (scène mesurée)."""

from __future__ import annotations

from dataclasses import replace

import pytest

from v2engine.geometry import Vec2
from v2engine.movement import LATERAL_FREE_MPS, lateral_max_mps2, limit_turn, max_speed_mps, step
from tests.scenes import player

STEPS = (0.05, 0.1, 0.15)


def test_lateral_curve() -> None:
    assert lateral_max_mps2(11) == pytest.approx(4.5)
    assert lateral_max_mps2(55) == pytest.approx(5.5)
    assert lateral_max_mps2(99) == pytest.approx(6.5)


def test_limit_turn_keeps_the_along_part_and_caps_the_lateral_part() -> None:
    v = Vec2(8.0, 0.0)
    capped = limit_turn(v, Vec2(7.5, 2.0), 5.0, 0.1)  # demande 2 m/s de travers en 0,1 s : 20 m/s²
    assert capped.x == pytest.approx(7.5) and capped.y == pytest.approx(0.5)
    assert limit_turn(v, Vec2(7.9, 0.3), 5.0, 0.1) == Vec2(7.9, 0.3)  # 3 m/s² : sous la borne
    slow = Vec2(LATERAL_FREE_MPS * 0.9, 0.0)
    assert limit_turn(slow, Vec2(0.0, 1.8), 5.0, 0.1) == Vec2(0.0, 1.8)  # pivot sur un appui


def _turn(agility: int, dt: float) -> tuple[float, float]:
    """Joueur lancé à pleine vitesse vers l'est, cap vers l'est, à qui l'on donne une cible loin au nord (virage à 90°) :
    vitesse minimale pendant le virage et pire accélération latérale mesurée."""
    state = player("P", x=30.0, y=10.0, pace=80, acceleration=80, Agility=agility)
    vmax = max_speed_mps(80)
    state = replace(state, velocity=Vec2(vmax, 0.0), facing=Vec2(1.0, 0.0), facing_run=True)
    target = Vec2(30.0, 60.0)
    lowest, worst = vmax, 0.0
    for _ in range(round(3.0 / dt)):
        before = state.velocity
        state = step(state, dt, target, 0.0)
        lowest = min(lowest, state.velocity.length())
        speed = before.length()
        if speed >= LATERAL_FREE_MPS:
            change = state.velocity - before
            along = (change.x * before.x + change.y * before.y) / speed
            lateral = (change.length() ** 2 - along ** 2) ** 0.5
            worst = max(worst, lateral / dt)
    return lowest, worst


@pytest.mark.parametrize("dt", STEPS)
def test_a_90_degree_turn_at_full_speed_costs_speed(dt) -> None:
    vmax = max_speed_mps(80)
    lowest, worst = _turn(55, dt)
    assert lowest < vmax * 0.8  # nettement sous la vitesse de départ
    assert worst <= lateral_max_mps2(55) * 1.01


@pytest.mark.parametrize("dt", STEPS)
def test_an_agile_player_loses_less_speed_in_the_turn(dt) -> None:
    low, _ = _turn(11, dt)
    high, _ = _turn(99, dt)
    assert high > low


def test_the_turn_does_not_stop_the_runner() -> None:
    """Pas de cumul excessif avec le plafond du 07b (corps pas encore tourné) : au plus bas du virage à 90°, il garde
    plus du tiers de sa vitesse (réel : un changement de direction à 90° en course se fait à 2 à 4 m/s, ordre de
    grandeur des tests de changement de direction ; il ne s'arrête pas)."""
    lowest, _ = _turn(55, 0.1)
    assert lowest > 2.0


def _cut(agility: int, monkeypatch=None) -> float:
    """Crochet à vitesse moyenne (3,5 m/s vers l'est, cible au nord-ouest) : pire accélération latérale mesurée."""
    state = player("P", x=30.0, y=10.0, pace=80, acceleration=80, Agility=agility)
    state = replace(state, velocity=Vec2(3.5, 0.0), facing=Vec2(1.0, 0.0))
    worst = 0.0
    for _ in range(15):
        before = state.velocity
        state = step(state, 0.1, Vec2(20.0, 30.0), 0.0)
        speed = before.length()
        if speed >= LATERAL_FREE_MPS:
            change = state.velocity - before
            along = (change.x * before.x + change.y * before.y) / speed
            worst = max(worst, max(0.0, change.length() ** 2 - along ** 2) ** 0.5 / 0.1)
    return worst


def test_the_cap_binds_on_a_sharp_cut_at_moderate_speed(monkeypatch) -> None:
    """Où la borne agit : un crochet serré à vitesse moyenne demanderait plus que l'accélération latérale permise (le
    freinage, 12a, borne déjà les virages à pleine vitesse sous elle : mesure en scène du ticket)."""
    assert _cut(11) <= lateral_max_mps2(11) * 1.01
    monkeypatch.setattr("v2engine.movement.limit_turn", lambda velocity, new_velocity, lateral_max, dt: new_velocity)
    assert _cut(11) > lateral_max_mps2(11) * 1.1  # sans la borne, le crochet serait plus sec

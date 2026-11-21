"""Ballon devant le porteur (ticket v2-realisme/04e) : en conduite, le ballon a sa position propre, devant le porteur dans
la direction de sa course, par touches (`match.TOUCH_PERIOD_S`) ; avance plus courte pour un bon dribbleur, nulle à
l'arrêt ; aucun tirage."""

from __future__ import annotations

from dataclasses import replace

import pytest

from tests.scenes import player
from v2engine.ball_state import BallState
from v2engine.geometry import Vec2
from v2engine.match import (CONTROL_RADIUS_M, TOUCH_PERIOD_S, TOUCH_PUSH_SHARE, TOUCH_REFERENCE_MPS, _step_ball,
                            carried_ball_position, touch_lead_m)


def _runner(dribbling: int = 55, speed: float = 6.0):
    return replace(player("P", "home", 50.0, 34.0, "MC", Dribbling=dribbling), velocity=Vec2(speed, 0.0),
                   facing=Vec2(1.0, 0.0))


def _leads(holder, steps: int = 60, dt: float = 0.1) -> list[float]:
    """Avance du ballon (m, le long de la course) sur `steps` pas d'une conduite rectiligne."""
    return [carried_ball_position(holder, i * dt).x - holder.position.x for i in range(steps)]


def test_touch_lead_follows_the_validated_points() -> None:
    for note, lead in ((11, 2.0), (55, 1.4), (99, 0.8)):
        assert touch_lead_m(player("P", Dribbling=note)) == pytest.approx(lead)


def test_straight_carry_at_6_mps_keeps_the_ball_ahead_within_bounds() -> None:
    holder = _runner(55, 6.0)
    leads = _leads(holder)
    bound = CONTROL_RADIUS_M + 1.4 * 6.0 / TOUCH_REFERENCE_MPS
    assert all(CONTROL_RADIUS_M - 1e-9 <= lead <= bound + 1e-9 for lead in leads)
    assert max(leads) > CONTROL_RADIUS_M + 1.0  # le ballon s'éloigne vraiment à chaque touche
    assert all(abs(carried_ball_position(holder, i * 0.1).y - 34.0) < 1e-9 for i in range(60))  # dans l'axe de la course
    # une touche par période : le ballon revient au pied
    assert carried_ball_position(holder, TOUCH_PERIOD_S).x - holder.position.x == pytest.approx(CONTROL_RADIUS_M)


def test_good_dribbler_keeps_the_ball_closer_and_a_slow_carry_too() -> None:
    assert max(_leads(_runner(99))) < max(_leads(_runner(55))) < max(_leads(_runner(11)))
    assert max(_leads(_runner(55, 2.0))) < max(_leads(_runner(55, 6.0)))
    assert max(_leads(_runner(55, 9.0))) == pytest.approx(max(_leads(_runner(55, TOUCH_REFERENCE_MPS))))


def test_standing_or_receiving_holder_keeps_the_ball_at_his_feet() -> None:
    still = _runner(55, 0.0)
    assert carried_ball_position(still, 0.3) == Vec2(50.0 + CONTROL_RADIUS_M, 34.0)
    assert carried_ball_position(_runner(55, 6.0), 0.3, receiving=True) == Vec2(50.0 + CONTROL_RADIUS_M, 34.0)


def test_the_engine_moves_the_held_ball_ahead_of_its_carrier() -> None:
    holder = _runner(55, 6.0)
    ball = BallState(position=holder.position, velocity=Vec2(0.0, 0.0), holder="P", next_decision_s=99.0)
    _step_ball(ball, 0.1, [holder], now_s=0.0)  # nouveau porteur : première touche
    _step_ball(ball, 0.1, [holder], now_s=TOUCH_PUSH_SHARE * TOUCH_PERIOD_S)  # avance maximale (04f)
    assert ball.holder == "P"
    assert ball.position.x - holder.position.x == pytest.approx(CONTROL_RADIUS_M + 1.4 * 6.0 / TOUCH_REFERENCE_MPS)


@pytest.mark.parametrize("dribbling,speed", [(11, 7.0), (11, 9.0), (11, 3.0), (55, 7.0), (99, 5.0)])
def test_the_ball_never_rolls_back_towards_its_carrier(dribbling: int, speed: float) -> None:
    """Ticket v2-realisme/04f (réserve A1 de l'expert au 04e) : sur le sol, le ballon avance toujours ; au retour, au moins
    à 1 - L / (7 x 0,6 x 0,6) de la vitesse du porteur (0,21 à Dribbling 11, avance maximale 2 m)."""
    holder = _runner(dribbling, speed)
    dt = 0.001
    ground = [holder.position.x + speed * i * dt + carried_ball_position(holder, i * dt).x - holder.position.x
              for i in range(int(TOUCH_PERIOD_S / dt) - 1)]
    steps = [(b - a) / dt for a, b in zip(ground, ground[1:])]
    assert min(steps) >= 0.2 * speed


def test_touch_profile_pushes_fast_then_returns_linearly() -> None:
    """Poussée pendant `TOUCH_PUSH_SHARE` de la période, avance maximale à sa fin, puis retour linéaire au pied."""
    holder = _runner(55, TOUCH_REFERENCE_MPS)
    lead = lambda t: carried_ball_position(holder, t).x - holder.position.x - CONTROL_RADIUS_M
    top = TOUCH_PUSH_SHARE * TOUCH_PERIOD_S
    assert lead(top) == pytest.approx(1.4)
    assert lead(top / 2.0) == pytest.approx(1.4 * 0.75)  # fin en douceur : trois quarts de l'avance à mi-poussée
    middle = (top + TOUCH_PERIOD_S) / 2.0
    assert lead(middle) == pytest.approx(0.7)  # retour linéaire
    assert lead(TOUCH_PERIOD_S - 1e-9) == pytest.approx(0.0, abs=1e-6)


def test_the_bench_measures_carry_speed_and_ball_lead_by_dribbling_band() -> None:
    """Reprise A2 du 04d (ticket 04e) : en conduite, le banc relève la vitesse du porteur rapportée à sa vitesse maximale
    et l'avance du ballon, par tranche de Dribbling ; rien hors conduite."""
    from scripts.v2_indicators import Collector
    from v2engine.movement import max_speed_mps

    holder = _runner(80, 6.0)
    collector = Collector()
    ball = BallState(position=carried_ball_position(holder, TOUCH_PERIOD_S / 2.0), velocity=Vec2(0.0, 0.0), holder="P",
                     dribble=("P", Vec2(70.0, 34.0)))
    collector._carry_speed(ball, {"P": holder})
    band = "Dribbling [70 ; +["
    speed = collector.stats[f"conduite, {band} : vitesse balle au pied (part de la vitesse max)"].values
    lead = collector.stats[f"conduite, {band} : avance du ballon (m)"].values
    assert speed == [pytest.approx(6.0 / max_speed_mps(holder.pace))]
    assert lead == [pytest.approx(ball.position.distance_to(holder.position))]
    collector._carry_speed(BallState(position=holder.position, velocity=Vec2(0.0, 0.0), holder="P"), {"P": holder})
    assert len(collector.stats[f"conduite, {band} : avance du ballon (m)"].values) == 1  # pas en conduite : rien

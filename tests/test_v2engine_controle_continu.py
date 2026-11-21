"""Contrôle imparfait continu (ticket v2-realisme/26a) : le tirage unique du contrôle donne la distance du ballon après le
contact ; au pied, contrôle long (le ballon file à `LONG_CONTROL_M`), ou raté (la queue, comme avant). La chance de
garder le ballon ne change pas ; la part de contrôles longs croît avec la difficulté et décroît avec First Touch."""

from __future__ import annotations

from dataclasses import replace

import pytest

from tests.scenes import player
from v2engine.ball_state import BallState
from v2engine.geometry import Vec2
from v2engine.match import CONTROL_RADIUS_M, MISS_RETRY_S, _step_ball
from v2engine.movement import max_speed_mps
from v2engine.possession import (CONTROL_REACH_M, LONG_CONTROL_M, LONG_CONTROL_START, RECEPTION_SPEED_FACTOR, ControlTouch,
                                 attempt_control, control_probability, control_touch, long_chase_s)
from v2engine.trace import CONTROLE_LONG, EventLog

GRID = [(i + 0.5) / 4000 for i in range(4000)]  # tirages uniformes réguliers


def _outcomes(p: float) -> list[ControlTouch]:
    return [control_touch(u, p) for u in GRID]


def _long_share(p: float) -> float:
    """Part des contrôles longs parmi les contrôles réussis."""
    kept = [t for t in _outcomes(p) if t]
    return sum(t.long_m > 0.0 for t in kept) / len(kept)


def test_success_is_unchanged_u_below_p() -> None:
    for p in (0.3, 0.8, 0.98):
        assert all(bool(control_touch(u, p)) == (u < p) for u in GRID)


def test_distance_is_continuous_and_grows_with_the_draw() -> None:
    p = 0.9
    kept = [control_touch(u, p) for u in GRID if u < p]
    distances = [t.long_m for t in kept]
    assert distances == sorted(distances)  # croît avec le tirage
    longs = [d for d in distances if d > 0.0]
    assert LONG_CONTROL_M[0] <= min(longs) < LONG_CONTROL_M[0] + 0.05  # pas de saut au début du contrôle long
    assert LONG_CONTROL_M[1] - 0.05 < max(longs) <= LONG_CONTROL_M[1]
    assert len(set(round(d, 3) for d in longs)) > 100  # continue, pas deux valeurs


@pytest.mark.parametrize("p,share", [(0.98, 0.044), (0.95, 0.07), (0.8, 0.132), (0.6, 0.168)])
def test_long_control_share_grows_with_difficulty(p: float, share: float) -> None:
    assert _long_share(p) == pytest.approx(share, abs=0.005)


def test_faster_ball_and_lower_first_touch_give_longer_controls() -> None:
    """Même joueur, ballon à 8 puis 20 m/s : moins de contrôles au pied à 20 ; First Touch 99 contre 11 à vitesse égale."""
    mid = player("R", "home", 50.0, 34.0, "MC", First_Touch=55)

    def at_foot(pl, speed: float) -> float:
        p = control_probability(pl, Vec2(-speed, 0.0))
        return sum(bool(t) and t.long_m == 0.0 for t in _outcomes(p)) / len(GRID)

    assert at_foot(mid, 20.0) < at_foot(mid, 8.0)
    assert at_foot(replace(mid, attributes={**mid.attributes, "First Touch": 99}), 20.0) > at_foot(
        replace(mid, attributes={**mid.attributes, "First Touch": 11}), 20.0)


def test_goalkeeper_and_still_ball_never_give_a_long_control(monkeypatch) -> None:
    monkeypatch.setattr("v2engine.possession.PASSE.random", lambda: 0.0 + 0.999 * control_probability(keeper, fast))
    keeper = player("G", "home", 5.0, 34.0, "GK")
    fast = Vec2(-15.0, 0.0)
    assert attempt_control(keeper, fast) == ControlTouch(True)
    field = player("D", "home", 30.0, 34.0, "DC")
    monkeypatch.setattr("v2engine.possession.PASSE.random", lambda: 0.999 * control_probability(field, Vec2(0.2, 0.0)))
    assert attempt_control(field, Vec2(0.2, 0.0)) == ControlTouch(True)
    monkeypatch.setattr("v2engine.possession.PASSE.random", lambda: 0.999 * control_probability(field, fast))
    assert attempt_control(field, fast).long_m > 0.0  # même tirage, joueur de champ, ballon rapide : contrôle long


def test_engine_long_control_with_a_closer_opponent_frees_the_ball(monkeypatch) -> None:
    """Contrôle long de 2 m, adversaire plus près que lui du point d'arrêt : le ballon part dans sa direction, s'arrête
    vers 2 m du joueur, qui ne peut le reprendre qu'après `MISS_RETRY_S` ; journal : « contrôle long »."""
    monkeypatch.setattr("v2engine.match.attempt_control", lambda *a, **k: ControlTouch(True, 2.0))
    receiver = player("R", "home", 50.0, 34.0, "MC")
    rival = player("X", "away", 52.0, 35.2, "DC")  # 1,2 m du point d'arrêt (52 ; 34), à plus de 2 m du ballon au contact
    events = []
    ball = BallState(position=Vec2(49.0, 34.0), velocity=Vec2(6.0, 0.0), receiver="R", readers={})
    ball.log = EventLog(events)
    _step_ball(ball, 0.1, [receiver, rival], now_s=1.0)
    assert ball.holder is None
    assert [e.kind for e in events] == [CONTROLE_LONG]
    assert ball.control_ban_until_s["R"] == pytest.approx(1.0 + MISS_RETRY_S)
    assert ball.position.x == pytest.approx(50.0 + CONTROL_RADIUS_M)
    assert ball.velocity.x > 0.0 and abs(ball.velocity.y) < 1e-9
    for i in range(1, 80):  # personne d'autre ne bouge : le ballon roule puis meurt
        _step_ball(ball, 0.1, [], now_s=1.0 + 0.1 * i)
    assert ball.position.x - 50.0 == pytest.approx(2.0, abs=0.05)


def test_engine_long_control_kept_costs_the_time_to_fetch_the_ball(monkeypatch) -> None:
    """Contrôle long de 2 m, personne de plus près : il garde le ballon, mais décide plus tard, du temps d'aller le
    chercher à sa vitesse de réception ; pas de jeu en une touche."""
    receiver = player("R", "home", 50.0, 34.0, "MC")
    far = player("X", "away", 56.0, 34.0, "DC")  # 4 m du point d'arrêt : plus loin que lui
    delays = {}
    for touch in (ControlTouch(True), ControlTouch(True, 2.0)):
        monkeypatch.setattr("v2engine.match.attempt_control", lambda *a, t=touch, **k: t)
        monkeypatch.setattr("v2engine.match.orients_control", lambda *a, **k: True)
        monkeypatch.setattr("v2engine.match.thinks_one_touch", lambda *a, **k: False)
        ball = BallState(position=Vec2(49.0, 34.0), velocity=Vec2(6.0, 0.0), receiver="R", readers={})
        _step_ball(ball, 0.1, [replace(receiver), replace(far)], now_s=1.0)
        assert ball.holder == "R"
        delays[touch.long_m] = ball.next_decision_s - 1.0
    expected = (2.0 - CONTROL_REACH_M) / (RECEPTION_SPEED_FACTOR * max_speed_mps(60))
    assert long_chase_s(receiver, 2.0) == pytest.approx(expected)
    assert delays[2.0] - delays[0.0] == pytest.approx(expected)


def test_engine_long_control_never_plays_first_time(monkeypatch) -> None:
    monkeypatch.setattr("v2engine.match.attempt_control", lambda *a, **k: ControlTouch(True, 1.5))
    monkeypatch.setattr("v2engine.match.thinks_one_touch", lambda *a, **k: True)
    ball = BallState(position=Vec2(49.0, 34.0), velocity=Vec2(6.0, 0.0), receiver="R", readers={})
    _step_ball(ball, 0.1, [player("R", "home", 50.0, 34.0, "MC")], now_s=1.0)
    assert ball.holder == "R" and ball.one_touch is None and ball.next_decision_s > 1.0


def test_engine_clean_control_still_takes_the_ball(monkeypatch) -> None:
    monkeypatch.setattr("v2engine.match.attempt_control", lambda *a, **k: ControlTouch(True))
    receiver = player("R", "home", 50.0, 34.0, "MC")
    ball = BallState(position=Vec2(49.0, 34.0), velocity=Vec2(6.0, 0.0), receiver="R", readers={})
    _step_ball(ball, 0.1, [receiver], now_s=1.0)
    assert ball.holder == "R"


def test_constants() -> None:
    assert LONG_CONTROL_START == 0.8 and LONG_CONTROL_M == (1.0, 2.0)
    assert CONTROL_REACH_M == round(CONTROL_RADIUS_M, 2)

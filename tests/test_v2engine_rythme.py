"""Tests du moteur V2, ticket v2-socle/06 (rythme : temps de réception avant la première décision). Voir
.scratch/v2-socle/issues/06-volume-de-passes.md."""

from __future__ import annotations

import math

from v2engine.ball_state import BallState
from v2engine.geometry import Vec2
from v2engine.match import _step_ball
from v2engine.movement import PlayerState
from v2engine.possession import reception_delay_s


def _player(name: str = "P", team: str = "home", poste: str = "MC", position: Vec2 = Vec2(50.0, 34.0),
            attributes: dict[str, int] | None = None) -> PlayerState:
    return PlayerState(
        name=name, team=team, poste=poste, position=position, velocity=Vec2(0.0, 0.0),
        pace=60, acceleration=60, stamina=60, home_target=position, attributes=attributes,
    )


def test_reception_time_follows_first_touch_validated_points() -> None:
    for note, expected in ((99, 1.7), (55, 2.3), (11, 2.9)):
        assert math.isclose(reception_delay_s(_player(attributes={"First Touch": note})), expected)


def test_pressure_halves_reception_time_at_contact() -> None:
    player = _player(attributes={"First Touch": 55})
    marker = _player("M", team="away", position=player.position)  # au contact
    assert math.isclose(reception_delay_s(player, [marker]), 1.15)


def test_keeper_never_plays_before_three_and_a_half_seconds_without_pressure() -> None:
    assert math.isclose(reception_delay_s(_player(poste="GK", attributes={"First Touch": 99})), 3.5)


def test_receiver_does_not_decide_during_his_reception_time(monkeypatch) -> None:
    receiver = _player("R", attributes={"First Touch": 55})
    ball = BallState(position=receiver.position, velocity=Vec2(0.0, 0.0))
    monkeypatch.setattr("v2engine.match.attempt_control", lambda player, *args: True)
    _step_ball(ball, 0.1, [receiver], now_s=10.0)
    assert ball.holder == "R" and math.isclose(ball.next_decision_s, 12.3)
    monkeypatch.setattr("v2engine.match.choose_action",
                        lambda *args: (_ for _ in ()).throw(AssertionError("décision pendant la réception")))
    _step_ball(ball, 0.1, [receiver], now_s=12.2)  # toujours en réception : pas de décision


def test_receiver_decides_once_his_reception_time_is_over(monkeypatch) -> None:
    receiver = _player("R", attributes={"First Touch": 55})
    ball = BallState(position=receiver.position, velocity=Vec2(0.0, 0.0))
    monkeypatch.setattr("v2engine.match.attempt_control", lambda player, *args: True)
    _step_ball(ball, 0.1, [receiver], now_s=10.0)
    assert ball.receiving
    monkeypatch.setattr("v2engine.match.choose_action", lambda *args: type("A", (), {"kind": "dribble"})())
    monkeypatch.setattr("v2engine.match.dribble_lost", lambda *args, **kwargs: False)  # ticket 04a : pas de perte tirée ici
    _step_ball(ball, 0.1, [receiver], now_s=12.3)
    assert not ball.receiving and math.isclose(ball.next_decision_s, 12.8)


def test_holder_moves_at_control_pace_while_receiving_then_at_dribble_pace() -> None:
    from v2engine.match import _step_player

    def speed(receiving: bool) -> float:
        holder = _player("R", position=Vec2(50.0, 34.0))
        ball = BallState(position=holder.position, velocity=Vec2(0.0, 0.0), holder="R", receiving=receiving)
        for _ in range(30):  # 3 s : vitesse établie
            holder = _step_player(holder, ball, 0.1, 10.0, [holder])
        return holder.velocity.length()
    assert speed(True) < 0.6 * speed(False)  # 0,4 contre 0,85 de la vitesse max

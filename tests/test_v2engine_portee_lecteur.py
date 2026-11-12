"""Portée du défenseur qui a lu la passe (ticket v2-realisme/18j) : il court la couper et tend la jambe, il touche le
ballon à `READER_REACH_M` ; un adversaire qui ne l'a pas lue garde `CONTROL_RADIUS_M` ; le receveur visé garde
`RECEIVER_REACH_M` (ticket 18i)."""

from __future__ import annotations

from v2engine.ball_state import BallState
from v2engine.geometry import Vec2
from v2engine.match import CONTROL_RADIUS_M, READER_REACH_M, RECEIVER_REACH_M, _step_ball
from v2engine.movement import PlayerState


def _player(name: str, team: str, position: Vec2) -> PlayerState:
    return PlayerState(name=name, team=team, poste="DC", position=position, velocity=Vec2(0.0, 0.0), pace=60,
                       acceleration=60, stamina=99, home_target=position)


def _roll(ball: BallState, players: list[PlayerState], dt: float = 0.1, seconds: float = 2.0) -> None:
    for i in range(int(seconds / dt)):
        _step_ball(ball, dt, players, i * dt)
        if ball.holder is not None or ball.velocity.length() < 1e-9:
            break


def _pass(readers: dict[str, Vec2] | None = None) -> BallState:
    """Passe de (50 ; 34) vers R, loin au bout du trajet (90 ; 50)."""
    return BallState(position=Vec2(50.0, 34.0), velocity=Vec2(10.0, 0.0), receiver="R", readers=readers or {})


def test_reader_reach_is_the_receiver_reach() -> None:
    assert READER_REACH_M == RECEIVER_REACH_M == 1.0
    assert READER_REACH_M > CONTROL_RADIUS_M


def test_reader_touches_a_pass_at_08_m(monkeypatch) -> None:
    monkeypatch.setattr("v2engine.match.attempt_control", lambda *a, **k: True)
    reader = _player("L", "away", Vec2(60.0, 34.8))
    receiver = _player("R", "home", Vec2(90.0, 50.0))
    ball = _pass({"L": Vec2(60.0, 34.0)})
    _roll(ball, [reader, receiver])
    assert ball.holder == "L"


def test_non_reader_at_08_m_does_not_touch(monkeypatch) -> None:
    """Même place, même passe : l'adversaire qui ne l'a pas lue la laisse passer à 0,8 m."""
    monkeypatch.setattr("v2engine.match.attempt_control", lambda *a, **k: True)
    other = _player("X", "away", Vec2(60.0, 34.8))
    receiver = _player("R", "home", Vec2(90.0, 50.0))
    ball = _pass({"L": Vec2(70.0, 34.0)})  # un autre lecteur, ailleurs
    _roll(ball, [other, receiver])
    assert ball.holder is None and ball.last_toucher != "X"


def test_reader_beyond_his_reach_does_not_touch(monkeypatch) -> None:
    monkeypatch.setattr("v2engine.match.attempt_control", lambda *a, **k: True)
    reader = _player("L", "away", Vec2(60.0, 35.1))
    receiver = _player("R", "home", Vec2(90.0, 50.0))
    ball = _pass({"L": Vec2(60.0, 34.0)})
    _roll(ball, [reader, receiver])
    assert ball.holder is None and ball.last_toucher != "L"


def test_receiver_keeps_his_reach_with_readers_on_the_pass(monkeypatch) -> None:
    monkeypatch.setattr("v2engine.match.attempt_control", lambda *a, **k: True)
    receiver = _player("R", "home", Vec2(60.0, 34.9))
    reader = _player("L", "away", Vec2(80.0, 40.0))  # lecteur loin du trajet
    ball = _pass({"L": Vec2(80.0, 34.0)})
    _roll(ball, [reader, receiver])
    assert ball.holder == "R"


def test_first_reached_tries_first_between_reader_and_receiver(monkeypatch) -> None:
    """Le lecteur, plus près du passeur sur le trajet, est atteint avant le receveur : il tente le premier."""
    tried: list[str] = []
    monkeypatch.setattr("v2engine.match.attempt_control", lambda player, *a, **k: tried.append(player.name) or True)
    reader = _player("L", "away", Vec2(55.0, 34.9))
    receiver = _player("R", "home", Vec2(60.0, 34.9))
    ball = _pass({"L": Vec2(55.0, 34.0)})
    _roll(ball, [receiver, reader])
    assert tried[0] == "L" and ball.holder == "L"


def test_no_readers_after_the_pass_is_touched(monkeypatch) -> None:
    """Le premier contact finit la passe : plus de lecteur, plus de portée élargie."""
    monkeypatch.setattr("v2engine.match.attempt_control", lambda *a, **k: False)
    reader = _player("L", "away", Vec2(60.0, 34.8))
    receiver = _player("R", "home", Vec2(90.0, 50.0))
    ball = _pass({"L": Vec2(60.0, 34.0)})
    _step_ball(ball, 1.2, [reader, receiver])
    assert ball.last_toucher == "L" and ball.readers == {}

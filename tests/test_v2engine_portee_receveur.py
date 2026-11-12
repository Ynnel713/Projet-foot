"""Portée du receveur visé d'une passe (ticket v2-realisme/18i) : il tend la jambe et touche le ballon à
`RECEIVER_REACH_M` ; tout autre joueur, coéquipier ou adversaire, ne le touche qu'à `CONTROL_RADIUS_M`."""

from __future__ import annotations

import pytest

from v2engine.ball_state import BallState
from v2engine.geometry import Vec2
from v2engine.match import CONTROL_RADIUS_M, RECEIVER_REACH_M, _step_ball
from v2engine.movement import PlayerState
from v2engine.shooting import BLOCK_WIDTH_M


def _player(name: str, team: str, position: Vec2) -> PlayerState:
    return PlayerState(name=name, team=team, poste="MC", position=position, velocity=Vec2(0.0, 0.0), pace=60,
                       acceleration=60, stamina=99, home_target=position)


def _roll(ball: BallState, players: list[PlayerState], dt: float = 0.1, seconds: float = 2.0) -> None:
    for i in range(int(seconds / dt)):
        _step_ball(ball, dt, players, i * dt)
        if ball.holder is not None or ball.velocity.length() < 1e-9:
            break


def test_receiver_reach_is_the_stretched_leg_of_the_block() -> None:
    assert RECEIVER_REACH_M == BLOCK_WIDTH_M == 1.0
    assert RECEIVER_REACH_M > CONTROL_RADIUS_M


@pytest.mark.parametrize("gap", (0.6, 0.8, 0.95))
def test_intended_receiver_touches_a_pass_passing_beside_him(monkeypatch, gap) -> None:
    monkeypatch.setattr("v2engine.match.attempt_control", lambda *a, **k: True)
    receiver = _player("R", "home", Vec2(60.0, 34.0 + gap))
    ball = BallState(position=Vec2(50.0, 34.0), velocity=Vec2(10.0, 0.0), receiver="R")
    _roll(ball, [receiver])
    assert ball.holder == "R"


@pytest.mark.parametrize("team", ("home", "away"))
def test_any_other_player_keeps_the_body_radius(monkeypatch, team) -> None:
    """Même ballon, même écart de 0,8 m : un joueur qui n'est pas le receveur visé (adversaire ou autre coéquipier) ne
    le touche pas."""
    monkeypatch.setattr("v2engine.match.attempt_control", lambda *a, **k: True)
    other = _player("X", team, Vec2(60.0, 34.8))
    receiver = _player("R", "home", Vec2(90.0, 50.0))  # loin du trajet
    ball = BallState(position=Vec2(50.0, 34.0), velocity=Vec2(10.0, 0.0), receiver="R")
    _roll(ball, [other, receiver])
    assert ball.holder is None and ball.last_toucher != "X"


def test_receiver_beyond_his_reach_does_not_touch(monkeypatch) -> None:
    monkeypatch.setattr("v2engine.match.attempt_control", lambda *a, **k: True)
    receiver = _player("R", "home", Vec2(60.0, 35.1))
    ball = BallState(position=Vec2(50.0, 34.0), velocity=Vec2(10.0, 0.0), receiver="R")
    _roll(ball, [receiver])
    assert ball.holder is None


def test_opponent_on_the_path_before_the_receiver_still_touches_first(monkeypatch) -> None:
    tried: list[str] = []
    monkeypatch.setattr("v2engine.match.attempt_control", lambda player, *a, **k: tried.append(player.name) or True)
    opponent = _player("O", "away", Vec2(55.0, 34.2))
    receiver = _player("R", "home", Vec2(60.0, 34.8))
    ball = BallState(position=Vec2(50.0, 34.0), velocity=Vec2(10.0, 0.0), receiver="R")
    _roll(ball, [receiver, opponent])
    assert tried[0] == "O" and ball.holder == "O"


def test_receiver_reached_first_by_his_reach_tries_first(monkeypatch) -> None:
    """Dans le même pas, le receveur atteint à 1 m avant l'adversaire au corps plus loin : il tente le premier."""
    tried: list[str] = []
    monkeypatch.setattr("v2engine.match.attempt_control", lambda player, *a, **k: tried.append(player.name) or True)
    receiver = _player("R", "home", Vec2(51.0, 34.9))
    opponent = _player("O", "away", Vec2(51.8, 34.0))
    ball = BallState(position=Vec2(49.5, 34.0), velocity=Vec2(30.0, 0.0), receiver="R")
    _step_ball(ball, 0.15, [opponent, receiver])
    assert tried[0] == "R" and ball.holder == "R"

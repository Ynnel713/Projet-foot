"""Tests du moteur V2, ticket v2-socle/01 (le receveur vient au-devant de la passe). Voir
.scratch/v2-socle/issues/01-receveur-vient-au-ballon.md."""

from __future__ import annotations

from v2engine.anticipation import meeting_point
from v2engine.ball_state import BallState
from v2engine.geometry import Vec2
from v2engine.match import BALL_FRICTION_PER_S, _step_ball, _step_player
from v2engine.movement import PlayerState


def _player(name: str, team: str = "home", position: Vec2 = Vec2(50.0, 34.0)) -> PlayerState:
    return PlayerState(
        name=name, team=team, poste="MC", position=position, velocity=Vec2(0.0, 0.0),
        pace=60, acceleration=60, stamina=60, home_target=position,
    )


def test_meeting_point_is_on_the_ball_path_and_reachable_in_time() -> None:
    receiver = _player("Receveur", position=Vec2(45.0, 40.0))
    point = meeting_point(receiver, Vec2(30.0, 34.0), Vec2(15.0, 0.0), BALL_FRICTION_PER_S)
    assert abs(point.y - 34.0) < 1e-9  # sur la trajectoire réelle du ballon
    assert 30.0 < point.x < 45.0  # il coupe le ballon avant qu'il n'arrive à sa hauteur


def test_receiver_runs_to_meet_the_pass_instead_of_his_space() -> None:
    receiver = _player("Receveur", position=Vec2(45.0, 40.0))
    ball = BallState(position=Vec2(30.0, 34.0), velocity=Vec2(15.0, 0.0), receiver="Receveur")
    moved = _step_player(receiver, ball, 0.1, 0.0, [receiver], {})
    assert moved.position.y < receiver.position.y  # descend vers la trajectoire


def test_receiver_is_cleared_once_someone_controls_the_ball(monkeypatch) -> None:
    receiver = _player("Receveur", position=Vec2(30.0, 34.0))
    ball = BallState(position=Vec2(30.0, 34.0), velocity=Vec2(0.0, 0.0), receiver="Receveur")
    monkeypatch.setattr("v2engine.match.attempt_control", lambda player, *args: True)
    _step_ball(ball, 0.1, [receiver])
    assert ball.holder == "Receveur" and ball.receiver is None


def test_receiver_is_released_when_the_pass_dies_or_control_fails(monkeypatch) -> None:
    receiver = _player("Receveur", position=Vec2(60.0, 34.0))
    dead = BallState(position=Vec2(30.0, 34.0), velocity=Vec2(0.1, 0.0), receiver="Receveur")
    _step_ball(dead, 0.1, [receiver])
    assert dead.receiver is None

    receiver = _player("Receveur", position=Vec2(30.5, 34.0))  # là où le ballon arrive ce tick
    missed = BallState(position=Vec2(30.0, 34.0), velocity=Vec2(5.0, 0.0), receiver="Receveur")
    monkeypatch.setattr("v2engine.match.attempt_control", lambda player, *args: False)
    _step_ball(missed, 0.1, [receiver])
    assert missed.receiver is None


def test_nearest_player_of_each_team_always_goes_for_a_loose_ball() -> None:
    far = _player("Loin", position=Vec2(10.0, 34.0))  # 40 m du ballon, mais le plus proche de son équipe
    ball = BallState(position=Vec2(50.0, 34.0), velocity=Vec2(0.0, 0.0))
    moved = _step_player(far, ball, 0.1, 0.0, [far], {})
    assert moved.position.x > far.position.x

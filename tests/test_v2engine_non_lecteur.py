"""Interception par l'adversaire qui n'a pas lu la passe (ticket v2-realisme/29b) : sur une passe au sol, il touche le
ballon à `NON_READER_REACH_M` s'il l'a vue partir depuis `NON_READER_REACTION_S` et fait face au ballon ; sinon il garde
`CONTROL_RADIUS_M`. Ni le coéquipier du passeur, ni le gardien, ni une passe aérienne ne sont concernés."""

from __future__ import annotations

from v2engine.ball_state import BallState
from v2engine.geometry import Vec2
from v2engine.match import CONTROL_RADIUS_M, NON_READER_REACH_M, NON_READER_REACTION_S, RECEIVER_REACH_M, _step_ball
from v2engine.movement import PlayerState
from v2engine.restart import AERIEN


def _player(name: str, team: str, position: Vec2, facing: Vec2, poste: str = "DC") -> PlayerState:
    return PlayerState(name=name, team=team, poste=poste, position=position, velocity=Vec2(0.0, 0.0), pace=60,
                       acceleration=60, stamina=99, home_target=position, facing=facing)


def _roll(ball: BallState, players: list[PlayerState], dt: float = 0.1, seconds: float = 2.0) -> None:
    for i in range(int(seconds / dt)):
        _step_ball(ball, dt, players, i * dt)
        if ball.holder is not None or ball.velocity.length() < 1e-9:
            break


def _pass(**kwargs) -> BallState:
    """Passe au sol de « home », de (50 ; 34) vers R, loin au bout du trajet ; partie à l'instant 0."""
    return BallState(position=Vec2(50.0, 34.0), velocity=Vec2(10.0, 0.0), receiver="R", readers={},
                     last_pass_team="home", pass_started_s=0.0, **kwargs)


FACING_BALL = Vec2(-0.7071, -0.7071)  # tourné vers le trajet, du côté du passeur
BACK_TO_BALL = Vec2(0.7071, 0.7071)  # dos au trajet


def _receiver() -> PlayerState:
    return _player("R", "home", Vec2(90.0, 50.0), FACING_BALL)


def _accept_all(monkeypatch) -> None:
    monkeypatch.setattr("v2engine.match.attempt_control", lambda *a, **k: True)


def test_constants_between_control_radius_and_receiver_reach() -> None:
    assert CONTROL_RADIUS_M < NON_READER_REACH_M == 0.8 < RECEIVER_REACH_M
    assert NON_READER_REACTION_S == 0.25


def test_non_reader_facing_the_ball_touches_at_07_m(monkeypatch) -> None:
    _accept_all(monkeypatch)
    defender = _player("X", "away", Vec2(60.0, 34.7), FACING_BALL)
    ball = _pass()
    _roll(ball, [defender, _receiver()])
    assert ball.holder == "X"


def test_non_reader_with_his_back_to_the_ball_does_not_touch(monkeypatch) -> None:
    """Le ballon passe dans son dos puis ressort devant lui, hors de sa portée : il ne le touche pas."""
    _accept_all(monkeypatch)
    defender = _player("X", "away", Vec2(60.0, 34.7), BACK_TO_BALL)
    ball = _pass()
    _roll(ball, [defender, _receiver()])
    assert ball.holder is None and ball.last_toucher != "X"


def test_non_reader_before_the_reaction_time_does_not_touch(monkeypatch) -> None:
    """Ballon à sa hauteur 0,15 s après le départ : il n'a pas eu le temps de réagir."""
    _accept_all(monkeypatch)
    defender = _player("X", "away", Vec2(51.5, 34.7), FACING_BALL)
    ball = _pass()
    _roll(ball, [defender, _receiver()])
    assert ball.holder is None and ball.last_toucher != "X"


def test_non_reader_beyond_his_reach_does_not_touch(monkeypatch) -> None:
    _accept_all(monkeypatch)
    defender = _player("X", "away", Vec2(60.0, 34.9), FACING_BALL)
    ball = _pass()
    _roll(ball, [defender, _receiver()])
    assert ball.holder is None and ball.last_toucher != "X"


def test_landing_aerial_pass_keeps_the_control_radius(monkeypatch) -> None:
    """Passe aérienne qui retombe (pas où elle touche le sol) : la portée de jambe tendue ne s'applique pas."""
    _accept_all(monkeypatch)
    defender = _player("X", "away", Vec2(51.0, 34.7), FACING_BALL)
    ball = _pass(mode=AERIEN)
    ball.pass_started_s = -1.0  # partie depuis longtemps : seul le vol aérien la protège
    _roll(ball, [defender, _receiver()], seconds=0.1)
    assert ball.last_toucher != "X"


def test_passer_team_mate_and_goalkeeper_are_not_concerned(monkeypatch) -> None:
    _accept_all(monkeypatch)
    mate = _player("M", "home", Vec2(60.0, 34.7), FACING_BALL)
    keeper = _player("G", "away", Vec2(70.0, 34.7), FACING_BALL, poste="GK")
    ball = _pass()
    _roll(ball, [mate, keeper, _receiver()])
    assert ball.last_toucher not in ("M", "G")


def test_pass_without_start_time_keeps_the_former_rule(monkeypatch) -> None:
    """Scène sans instant de départ (balle posée par un test, remise en jeu ancienne) : comme avant le 29b."""
    _accept_all(monkeypatch)
    defender = _player("X", "away", Vec2(60.0, 34.7), FACING_BALL)
    ball = _pass()
    ball.pass_started_s = None
    _roll(ball, [defender, _receiver()])
    assert ball.last_toucher != "X"

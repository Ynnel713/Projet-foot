"""Tir en vol (ticket v2-realisme/05a) : le ballon part vers son point d'arrivée et l'issue se lit sur la ligne de but,
jamais au départ du tir. Seul chemin du tir en jeu depuis le 05h (interrupteur retiré)."""

from __future__ import annotations

import math

import pytest

from ligue1sim.pitch_geometry import GOAL_HEIGHT_M, GOAL_WIDTH_M

from v2engine import match
from v2engine.ball_state import BallState
from v2engine.decision import Action
from v2engine.flux import TIR
from v2engine.geometry import PITCH_LENGTH_M, Vec2
from v2engine.match import GOAL_CENTER_Y, _step_ball
from v2engine.movement import PlayerState
from v2engine.restart import GOAL_KICK, KICKOFF
from v2engine.shooting import FLYING, OVER, SHOT_AIM_HEIGHT_M, WIDE, draw_shot_error, shot_error_sigma

DISTANCE_M = 20.0


def _player(name: str, team: str, poste: str, position: Vec2) -> PlayerState:
    return PlayerState(name=name, team=team, poste=poste, position=position, velocity=Vec2(0.0, 0.0), pace=60,
                       acceleration=60, stamina=60, home_target=position, attributes=None)


def _fly(monkeypatch, lateral_m: float, height_m: float = SHOT_AIM_HEIGHT_M):
    """Tir de 20 m, face au but, réglé pour arriver sur la ligne à `lateral_m` du centre et à `height_m` du sol."""
    shooter = _player("Buteur", "home", "BU", Vec2(PITCH_LENGTH_M - DISTANCE_M, GOAL_CENTER_Y))
    keeper = _player("Gardien", "away", "GK", Vec2(PITCH_LENGTH_M - 1.0, GOAL_CENTER_Y + 10.0))
    ball = BallState(position=shooter.position, velocity=Vec2(0.0, 0.0), holder="Buteur")
    monkeypatch.setattr(match, "should_attempt_tackle", lambda aggression, dt: False)
    monkeypatch.setattr(match, "choose_action", lambda *args: Action("shot", 1.0))
    monkeypatch.setattr(match, "BLOCK_CHANCE", 0.0)  # pas de contre (05c)
    error = (math.atan2(lateral_m, DISTANCE_M), math.atan2(height_m - SHOT_AIM_HEIGHT_M, DISTANCE_M))
    monkeypatch.setattr(match, "draw_shot_error", lambda *args: error)
    shots, path, scored = [], [], None
    for tick in range(40):
        scored = _step_ball(ball, 0.1, [shooter, keeper], tick * 0.1, shots=shots)
        path.append(ball.position)
        if scored is not None or ball.restart is not None:
            break
        assert shots[0].outcome == FLYING and ball.shot_in_flight  # rien n'est décidé avant la ligne
    return ball, shots, path, scored


def test_the_goal_is_never_drawn_at_the_shot_any_more() -> None:
    # garde du 05h : plus d'interrupteur ni de tirage du but au départ dans le moteur (garde en match : test_v2engine_issues_tir)
    assert not any(hasattr(match, name) for name in ("SHOT_FLIGHT_RESOLUTION", "attempt_shot", "classify_unscored"))


def test_a_shot_inside_the_post_is_a_goal_only_when_it_crosses_the_line(monkeypatch) -> None:
    ball, shots, path, scored = _fly(monkeypatch, GOAL_WIDTH_M / 2.0 - 0.2)
    assert scored == "home" and ball.restart.kind == KICKOFF and shots[0].outcome == "but"
    assert len(path) > 3  # plusieurs pas de vol avant le but (20 m à 30 m/s, freiné)
    assert abs(ball.position.x - PITCH_LENGTH_M) < 1e-6
    assert abs(ball.position.y - (GOAL_CENTER_Y + GOAL_WIDTH_M / 2.0 - 0.2)) < 0.01


def test_a_shot_one_metre_outside_the_post_is_a_goal_kick(monkeypatch) -> None:
    ball, shots, _, scored = _fly(monkeypatch, -(GOAL_WIDTH_M / 2.0 + 1.0))
    assert scored is None and ball.restart.kind == GOAL_KICK and ball.restart.team == "away"
    assert shots[0].outcome == WIDE


def test_a_shot_over_the_bar_is_a_goal_kick(monkeypatch) -> None:
    ball, shots, _, scored = _fly(monkeypatch, 0.0, GOAL_HEIGHT_M + 0.3)
    assert scored is None and ball.restart.kind == GOAL_KICK and shots[0].outcome == OVER


def test_the_ball_travels_in_a_straight_line_from_the_shooter_to_its_arrival_point(monkeypatch) -> None:
    lateral = 2.0
    _, _, path, _ = _fly(monkeypatch, lateral)
    for point in path:
        progress = point.x - (PITCH_LENGTH_M - DISTANCE_M)
        assert abs((point.y - GOAL_CENTER_Y) - lateral * progress / DISTANCE_M) < 1e-6


def test_the_drawn_error_follows_the_35b_spread(monkeypatch) -> None:
    shooter = _player("Buteur", "home", "BU", Vec2(PITCH_LENGTH_M - DISTANCE_M, GOAL_CENTER_Y))
    TIR.seed(5)
    draws = [draw_shot_error(shooter, Vec2(PITCH_LENGTH_M, GOAL_CENTER_Y), []) for _ in range(4000)]
    flying = [d for d in draws if d is not None]
    assert 0 < len(draws) - len(flying) < 0.1 * len(draws)  # quelques dévissés, rares
    spread = math.sqrt(sum(d[0] ** 2 for d in flying) / len(flying))
    assert spread == pytest.approx(shot_error_sigma(shooter, Vec2(PITCH_LENGTH_M, GOAL_CENTER_Y), []), rel=0.05)

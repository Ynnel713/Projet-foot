"""xG neutre et xG après frappe (ticket v2-realisme/06a) : chaque tir trace son xG neutre (tireur et gardien moyens), son
xG après frappe (chance qu'un gardien moyen, placé où est le vrai, n'atteigne pas le ballon ; 0 hors du cadre) et son
issue."""

from __future__ import annotations

import math

from ligue1sim.pitch_geometry import GOAL_HEIGHT_M, GOAL_WIDTH_M

from v2engine import match
from v2engine.ball_state import BallState
from v2engine.decision import Action
from v2engine.flux import TIR
from v2engine.geometry import PITCH_LENGTH_M, Vec2
from v2engine.match import GOAL_CENTER_Y, _step_ball
from v2engine.movement import PlayerState
from v2engine.shooting import FLYING, SHOT_AIM_HEIGHT_M, keeper_reach_m, post_shot_xg


def _player(name: str, team: str, poste: str, position: Vec2, attributes: dict | None = None) -> PlayerState:
    return PlayerState(name=name, team=team, poste=poste, position=position, velocity=Vec2(0.0, 0.0), pace=60,
                       acceleration=60, stamina=60, home_target=position, attributes=attributes)


def _shoot(monkeypatch, distance_m: float, lateral_m: float | None, height_m: float = SHOT_AIM_HEIGHT_M,
           note: int | None = None, opponents: list[PlayerState] = ()):
    """Tir face au but depuis `distance_m` ; `lateral_m` : point d'arrivée imposé (sinon écart tiré comme en match) ;
    gardien au centre, 1 m devant sa ligne. Retourne le tir tracé une fois son issue connue."""
    attributes = {"Finishing": note, "Long Shots": note, "Composure": 60} if note is not None else None
    shooter = _player("Buteur", "home", "BU", Vec2(PITCH_LENGTH_M - distance_m, GOAL_CENTER_Y), attributes)
    keeper = _player("Gardien", "away", "GK", Vec2(PITCH_LENGTH_M - 1.0, GOAL_CENTER_Y))
    monkeypatch.setattr(match, "should_attempt_tackle", lambda aggression, dt: False)
    monkeypatch.setattr(match, "choose_action", lambda *args: Action("shot", 1.0))
    if lateral_m is not None:
        error = (math.atan2(lateral_m, distance_m), math.atan2(height_m - SHOT_AIM_HEIGHT_M, distance_m))
        monkeypatch.setattr(match, "draw_shot_error", lambda *args: error)
    ball = BallState(position=shooter.position, velocity=Vec2(0.0, 0.0), holder="Buteur")
    players = [shooter, keeper, *opponents]
    shots = []
    for tick in range(40):
        _step_ball(ball, 0.1, players, tick * 0.1, shots=shots)
        if shots and shots[0].outcome != FLYING:
            break
    return shots[0]


def test_post_shot_xg_is_one_half_at_the_edge_of_the_reach_and_grows_with_the_gap() -> None:
    assert math.isclose(post_shot_xg(keeper_reach_m(0.5), 0.5), 0.5)
    assert post_shot_xg(0.0, 0.5) < 0.05 < 0.95 < post_shot_xg(keeper_reach_m(0.5) + 1.0, 0.5)


def test_a_shot_into_the_top_corner_is_close_to_one(monkeypatch) -> None:
    shot = _shoot(monkeypatch, 8.0, GOAL_WIDTH_M / 2.0 - 0.3, GOAL_HEIGHT_M - 0.3)
    assert shot.outcome == "but" and shot.post_shot_xg > 0.9


def test_a_shot_at_the_keeper_is_close_to_zero(monkeypatch) -> None:
    shot = _shoot(monkeypatch, 20.0, 0.0)
    assert shot.outcome in ("capté", "repoussé", "claqué") and shot.post_shot_xg < 0.05


def test_an_off_target_shot_is_zero_and_the_neutral_xg_is_traced(monkeypatch) -> None:
    shot = _shoot(monkeypatch, 20.0, GOAL_WIDTH_M / 2.0 + 1.0)
    assert shot.outcome == "à côté" and shot.post_shot_xg == 0.0
    assert 0.0 < shot.xg < 1.0


def test_a_blocked_shot_has_no_post_shot_xg(monkeypatch) -> None:
    monkeypatch.setattr(match, "BLOCK_CHANCE", 1.0)
    defender = _player("Defenseur", "away", "DC", Vec2(PITCH_LENGTH_M - 15.0, GOAL_CENTER_Y))
    shot = _shoot(monkeypatch, 20.0, 0.0, opponents=[defender])
    assert shot.outcome == "contré" and shot.post_shot_xg is None and shot.xg is not None


def test_the_neutral_xg_ignores_the_shooter_and_the_post_shot_xg_rewards_the_better_one(monkeypatch) -> None:
    def shots(note: int) -> list:
        TIR.seed(7)
        return [_shoot(monkeypatch, 16.0, None, note=note) for _ in range(300)]

    sharp, poor = shots(99), shots(11)
    assert {s.xg for s in sharp} == {s.xg for s in poor} and len({s.xg for s in sharp}) == 1  # même place : même xG neutre
    def mean(xs):
        values = [s.post_shot_xg for s in xs if s.post_shot_xg is not None]
        return sum(values) / len(values)
    assert mean(sharp) > mean(poor) + 0.02

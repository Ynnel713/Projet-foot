"""Tests du moteur V2, Phase 5, ticket v2-cerveau-joueurs/04 (Anticipation : interceptions et ballon libre).
Voir .scratch/v2-cerveau-joueurs/issues/04-anticipation-interceptions.md, critères d'acceptation."""

from __future__ import annotations

import random

from v2engine.anticipation import loose_ball_lead, loose_ball_target, pass_readers, read_pass_probability
from v2engine.ball_state import BallState
from v2engine.geometry import Vec2
from v2engine.match import BALL_FRICTION_PER_S, _step_ball, _step_player
from v2engine.movement import PlayerState


def _player(name: str = "P", team: str = "away", position: Vec2 = Vec2(50.0, 34.0),
            attributes: dict[str, int] | None = None) -> PlayerState:
    return PlayerState(
        name=name, team=team, poste="MC", position=position, velocity=Vec2(0.0, 0.0),
        pace=60, acceleration=60, stamina=60, home_target=position, attributes=attributes,
    )


def test_anticipation_curves_match_validated_points() -> None:
    assert [round(read_pass_probability(v), 6) for v in (99, 55, 11)] == [0.8, 0.4, 0.1]
    assert [round(loose_ball_lead(v), 6) for v in (99, 55, 11)] == [1.0, 0.5, 0.0]


def test_only_opponents_in_the_lane_who_can_get_there_first_read_the_pass(monkeypatch) -> None:
    monkeypatch.setattr("v2engine.flux.PERCEPTION.random", lambda: 0.0)  # la lecture réussit toujours
    start, aim = Vec2(20.0, 34.0), Vec2(50.0, 34.0)
    in_lane = _player("Couloir", position=Vec2(40.0, 39.0))  # 5 m de la trajectoire
    off_lane = _player("Loin", position=Vec2(40.0, 50.0))  # 16 m
    too_late = _player("Retard", position=Vec2(22.0, 41.0))  # 7 m, mais le ballon y passe tout de suite
    readers = pass_readers(start, Vec2(15.0, 0.0), aim, [in_lane, off_lane, too_late])
    assert set(readers) == {"Couloir"}
    assert readers["Couloir"] == Vec2(40.0, 34.0)


def test_reader_runs_to_cut_the_pass_and_reading_is_cleared_on_control(monkeypatch) -> None:
    reader = _player("Lecteur", position=Vec2(40.0, 39.0))
    ball = BallState(position=Vec2(30.0, 34.0), velocity=Vec2(15.0, 0.0), readers={"Lecteur": Vec2(40.0, 34.0)})
    moved = _step_player(reader, ball, 0.1, 0.0, [reader], {})
    assert moved.position.y < reader.position.y  # se rapproche de la trajectoire, pas du ballon

    ball.position, ball.velocity = moved.position, Vec2(0.0, 0.0)  # le ballon arrive sur lui
    monkeypatch.setattr("v2engine.match.attempt_control", lambda player, *args: True)
    _step_ball(ball, 0.1, [moved])
    assert ball.holder == "Lecteur" and ball.readers == {}


def test_loose_ball_target_moves_toward_stop_point_with_anticipation() -> None:
    ball_pos, ball_vel = Vec2(50.0, 34.0), Vec2(10.0, 0.0)
    low = loose_ball_target(_player(attributes={"Anticipation": 11}), ball_pos, ball_vel, BALL_FRICTION_PER_S)
    high = loose_ball_target(_player(attributes={"Anticipation": 99}), ball_pos, ball_vel, BALL_FRICTION_PER_S)
    assert low == ball_pos  # 11 : comportement d'avant, il court après le ballon
    assert high.x > ball_pos.x + 15.0  # 99 : file vers le point d'arrêt (~19,6 m plus loin)


def test_high_anticipation_reads_more_passes_than_low() -> None:
    def reads(note: int) -> int:
        random.seed(20260923)
        opponent = _player(position=Vec2(40.0, 39.0), attributes={"Anticipation": note})
        return sum(bool(pass_readers(Vec2(20.0, 34.0), Vec2(15.0, 0.0), Vec2(50.0, 34.0), [opponent])) for _ in range(2000))

    assert reads(90) >= 1.5 * reads(30)

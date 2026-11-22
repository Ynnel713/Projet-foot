"""Prise de balle du gardien (ticket v2-attributs-restants/03b2) : Handling règle la part captée d'un arrêt et les prises
relâchées devant lui (boulettes). Gardien moyen : Handling 60, médiane des gardiens de Ligue 1 de la base ; un gardien
sans note vaut le gardien moyen."""

from __future__ import annotations

import math

import pytest

from tests.scenes import player
from v2engine import match, shooting
from v2engine.ball_state import BallState
from v2engine.decision import Action
from v2engine.flux import TIR
from v2engine.geometry import PITCH_LENGTH_M, Vec2, in_penalty_area
from v2engine.match import GOAL_CENTER_Y, _step_ball
from v2engine.possession import BALL_FRICTION_PER_S, BALL_STOPPED_MPS
from v2engine.shooting import (FUMBLE_BOUNDS, HANDLING_REFERENCE_NOTE, HELD, NEUTRAL_ATTRIBUTES, PARRIED, SAVE_HELD_BOUNDS,
                               fumble_share, fumble_velocity, fumbles, keeper_handling, save_shares)

GOAL = Vec2(PITCH_LENGTH_M, GOAL_CENTER_Y)
CENTRAL = Vec2(PITCH_LENGTH_M - 14.0, GOAL_CENTER_Y)
WIDE = Vec2(PITCH_LENGTH_M - 12.0, GOAL_CENTER_Y + 10.0)


def _keeper(handling: int = 60, x: float = PITCH_LENGTH_M - 1.0):
    return player("Gardien", "away", x, GOAL_CENTER_Y, "GK", Handling=handling)


def test_the_average_keeper_and_a_keeper_without_ratings_keep_the_former_shares() -> None:
    assert keeper_handling(None) == HANDLING_REFERENCE_NOTE == 60.0
    assert keeper_handling(player("G", "away", 104, 34, "GK")) == HANDLING_REFERENCE_NOTE  # sans notes
    rated = _keeper(handling=99)
    assert keeper_handling(rated.__class__(**{**rated.__dict__, "attributes": NEUTRAL_ATTRIBUTES})) == 60.0
    assert keeper_handling(_keeper(handling=60)) == 60.0
    for chance, origin in ((0.0, CENTRAL), (0.15, WIDE), (0.5, CENTRAL)):
        assert save_shares(chance, origin, GOAL, 60.0) == save_shares(chance, origin, GOAL)
    held, _, tipped = save_shares(0.0, CENTRAL, GOAL)
    assert held == pytest.approx(0.70) and tipped == pytest.approx(0.30 * 0.25)  # constantes du ticket 28b


def test_handling_shifts_the_held_share_and_keeps_the_split_of_the_rest() -> None:
    for chance, origin in ((0.05, CENTRAL), (0.15, WIDE)):
        average, good, poor = (save_shares(chance, origin, GOAL, note) for note in (60.0, 99.0, 40.0))
        assert good[0] == pytest.approx(average[0] + 0.195)
        assert poor[0] == pytest.approx(average[0] - 0.10)
        for shares in (average, good, poor):
            assert sum(shares) == pytest.approx(1.0)
            assert shares[2] / (shares[1] + shares[2]) == pytest.approx(average[2] / (average[1] + average[2]))
    # bornes : jamais sûr de capter, jamais sans prise possible
    assert save_shares(0.0, CENTRAL, GOAL, 120.0)[0] == SAVE_HELD_BOUNDS[1]  # 99 sur un tir facile : 0,895
    assert save_shares(1.0, CENTRAL, GOAL, 1.0)[0] == SAVE_HELD_BOUNDS[0]


def test_a_poor_keeper_still_holds_some_of_the_hardest_shots() -> None:
    # parade d'exception d'un gardien à 40 sur le tir le plus difficile : 0,25 − 0,10 = 0,15 captés
    assert save_shares(1.0, CENTRAL, GOAL, 40.0)[0] == pytest.approx(0.15)


def test_the_fumble_share_is_rare_never_nil_and_higher_for_a_poor_keeper() -> None:
    assert fumble_share(60.0) == pytest.approx(0.04)
    assert fumble_share(99.0) == pytest.approx(0.01075)
    assert fumble_share(40.0) == pytest.approx(0.055)
    assert fumble_share(500.0) == FUMBLE_BOUNDS[0] and fumble_share(-500.0) == FUMBLE_BOUNDS[1]
    assert fumble_share() == fumble_share(60.0)


def test_a_great_keeper_still_fumbles_over_500_matches_and_a_poor_one_more_often() -> None:
    # environ 1 500 prises sur 500 matchs (3 arrêts par match, dont la moitié captés) : 99, rares mais présentes
    TIR.seed(20261122)
    great = sum(fumbles(99.0) for _ in range(1500))
    poor = sum(fumbles(40.0) for _ in range(1500))
    assert 5 <= great <= 35  # attendu : 16
    assert poor > 2 * great  # attendu : 82


def test_a_fumbled_ball_drops_slowly_in_front_of_the_keeper() -> None:
    TIR.seed(7)
    decay = -math.log(BALL_FRICTION_PER_S)
    for _ in range(200):
        velocity = fumble_velocity(GOAL, CENTRAL)
        assert velocity.x < 0.0  # vers le terrain
        assert abs(math.degrees(math.atan2(velocity.y, -velocity.x))) <= shooting.FUMBLE_ANGLE_DEG + 1e-9
        speed = velocity.length()
        assert 1.0 <= speed <= 2.0
        assert (speed - BALL_STOPPED_MPS) / decay < 3.0  # arrêté à moins de 3 m de lui


def _save(monkeypatch, keeper, fumbled: bool):
    shooter = player("Buteur", "home", PITCH_LENGTH_M - 12.0, GOAL_CENTER_Y, "BU")
    ball = BallState(position=shooter.position, velocity=Vec2(0.0, 0.0), holder="Buteur")
    monkeypatch.setattr(match, "should_attempt_tackle", lambda aggression, dt: False)
    monkeypatch.setattr(match, "choose_action", lambda *args: Action("shot", 1.0))
    monkeypatch.setattr(match, "BLOCK_CHANCE", 0.0)
    monkeypatch.setattr(match, "draw_shot_error", lambda *args: (math.atan2(0.3, 12.0), 0.0))  # sur le gardien
    monkeypatch.setattr(match, "save_outcome", lambda *args: HELD)
    handlings = []
    monkeypatch.setattr(match, "fumbles", lambda handling: handlings.append(handling) or fumbled)
    shots = []
    for tick in range(40):
        _step_ball(ball, 0.1, [shooter, keeper], tick * 0.1, shots=shots)
        if not ball.shot_in_flight:
            break
    return shots[0], ball, handlings


def test_in_the_match_loop_a_fumbled_catch_is_a_loose_ball_in_the_box(monkeypatch) -> None:
    keeper = _keeper(handling=40)
    shot, ball, handlings = _save(monkeypatch, keeper, fumbled=True)
    assert handlings == [40.0]  # la note du gardien qui arrête
    assert shot.outcome == PARRIED and shot.fumbled  # rangé avec les repoussés, marqué dans la trace
    assert ball.holder is None and ball.rebound
    assert ball.velocity.length() <= 2.0 and ball.velocity.x < 0.0
    assert in_penalty_area("home", ball.position) and (ball.position - keeper.position).length() < 1.5
    held, ball, _ = _save(monkeypatch, _keeper(handling=40), fumbled=False)
    assert held.outcome == HELD and not held.fumbled and ball.holder == "Gardien"

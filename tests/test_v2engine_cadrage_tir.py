"""Cadrage du tir (ticket v2-collectif/35b) : le ballon s'écarte de la visée selon la note du tireur, la pression et la
distance ; tir non converti : cadré (arrêté), à côté, au-dessus ou dévissé. La chance de but ne change pas."""

from __future__ import annotations

from collections import Counter

from v2engine.ball_state import BallState
from v2engine.decision import Action
from v2engine.flux import TIR
from v2engine.geometry import PITCH_LENGTH_M, Vec2
from v2engine.match import GOAL_CENTER_Y, SHOT_SPEED_MPS, _step_ball
from v2engine.movement import PlayerState
from v2engine.shooting import (CADRE, FLYING, OVER, SHANKED, WIDE, classify_unscored, on_target_axes, shot_error_sigma,
                               shot_probability)

GOAL = Vec2(PITCH_LENGTH_M, GOAL_CENTER_Y)


def _player(name: str = "P", team: str = "home", poste: str = "BU", position: Vec2 = Vec2(0.0, 0.0),
            attributes: dict[str, int] | None = None) -> PlayerState:
    return PlayerState(name=name, team=team, poste=poste, position=position, velocity=Vec2(0.0, 0.0), pace=60,
                       acceleration=60, stamina=60, home_target=position, attributes=attributes)


def _shooter(note: int, distance: float = 18.0) -> PlayerState:
    return _player(position=Vec2(PITCH_LENGTH_M - distance, GOAL_CENTER_Y),
                   attributes={"Finishing": note, "Long Shots": note, "Composure": 60})


def _marker(gap_m: float, shooter: PlayerState) -> PlayerState:
    return _player("Marqueur", team="away", poste="DC", position=Vec2(shooter.position.x + gap_m, GOAL_CENTER_Y + 0.5))


def _draws(shooter: PlayerState, opponents: list[PlayerState], n: int = 4000) -> Counter:
    TIR.seed(35)
    return Counter(classify_unscored(shooter, GOAL, None, opponents) for _ in range(n))


def test_a_better_shooter_keeps_the_ball_closer_to_his_aim() -> None:
    assert shot_error_sigma(_shooter(95), GOAL, []) < shot_error_sigma(_shooter(50), GOAL, []) < shot_error_sigma(
        _shooter(10), GOAL, [])
    good, poor = on_target_axes(_shooter(95), GOAL, []), on_target_axes(_shooter(10), GOAL, [])
    assert good[0] * good[1] > poor[0] * poor[1]


def test_pressure_and_distance_make_the_ball_stray_more() -> None:
    free, closer = _shooter(60), _shooter(60)
    assert shot_error_sigma(closer, GOAL, [_marker(1.0, closer)]) > shot_error_sigma(free, GOAL, [])
    near, far = on_target_axes(_shooter(60, 8.0), GOAL, []), on_target_axes(_shooter(60, 28.0), GOAL, [])
    assert near[0] * near[1] > far[0] * far[1]


def test_a_low_note_misses_the_frame_more_often_than_a_high_note_from_the_same_spot() -> None:
    low, high = _draws(_shooter(10), []), _draws(_shooter(95), [])
    assert low[CADRE] < high[CADRE]
    assert low[WIDE] + low[OVER] + low[SHANKED] > high[WIDE] + high[OVER] + high[SHANKED]


def test_pressure_increases_the_shots_off_the_frame() -> None:
    shooter = _shooter(60)
    free, pressed = _draws(shooter, []), _draws(shooter, [_marker(1.0, shooter)])
    assert pressed[CADRE] < free[CADRE]


def test_shanked_shots_are_rare_never_zero_and_commoner_with_a_low_note_or_under_pressure() -> None:
    shooter = _shooter(60)
    average = _draws(shooter, [])
    assert 0 < average[SHANKED] < 0.1 * sum(average.values())
    assert _draws(_shooter(99), [])[SHANKED] > 0  # même le meilleur dévisse, rarement
    assert _draws(_shooter(10), [])[SHANKED] > average[SHANKED]
    assert _draws(shooter, [_marker(1.0, shooter)])[SHANKED] > average[SHANKED]


def test_the_unscored_shots_decompose_the_goal_chance_without_changing_it() -> None:
    # P(but) = P(cadré) x P(but | cadré) : la part de cadrés non marqués vaut (cadré - but) / (1 - but)
    shooter = _shooter(60, 12.0)
    chance = shot_probability(shooter, GOAL, None, [])
    wide, high = on_target_axes(shooter, GOAL, [])
    expected = (max(wide * high, chance) - chance) / (1.0 - chance)
    draws = _draws(shooter, [], 20000)
    assert abs(draws[CADRE] / sum(draws.values()) - expected) < 0.02


def _shot(monkeypatch, error):
    shooter = _player("Buteur", position=Vec2(PITCH_LENGTH_M - 22.0, GOAL_CENTER_Y))
    keeper = _player("Gardien", team="away", poste="GK", position=Vec2(PITCH_LENGTH_M - 1.0, GOAL_CENTER_Y))
    ball = BallState(position=shooter.position, velocity=Vec2(0.0, 0.0), holder="Buteur")
    monkeypatch.setattr("v2engine.match.should_attempt_tackle", lambda aggression, dt: False)
    monkeypatch.setattr("v2engine.match.choose_action", lambda *args: Action("shot", 1.0))
    monkeypatch.setattr("v2engine.match.draw_blocker", lambda *args: None)
    monkeypatch.setattr("v2engine.match.draw_shot_error", lambda *args: error)  # tir en vol (05h) : écart imposé
    shots = []
    _step_ball(ball, 0.1, [shooter, keeper], 0.0, shots=shots)
    return ball, shots, [shooter, keeper]


def test_an_over_the_bar_shot_is_traced_over_and_flies_out_like_a_wide_one(monkeypatch) -> None:
    ball, shots, players = _shot(monkeypatch, (0.0, 0.3))  # 0,3 rad vers le haut : au-dessus de la barre
    assert shots[0].outcome == FLYING and ball.shot_wide and ball.holder is None
    assert abs(ball.velocity.length() - SHOT_SPEED_MPS) < 1e-6
    for i in range(1, 40):
        _step_ball(ball, 0.1, players, i * 0.1, shots=shots)
        if ball.restart is not None:
            break
    assert shots[0].outcome == OVER and ball.restart.kind == "sortie de but"


def test_a_shanked_shot_is_slow_wide_of_the_goal_axis_and_free_for_everyone(monkeypatch) -> None:
    ball, shots, _ = _shot(monkeypatch, None)
    assert shots[0].outcome == SHANKED and not ball.shot_wide and ball.holder is None
    assert ball.last_toucher == "Buteur" and ball.control_ban_until_s["Buteur"] > 0.0
    assert abs(ball.velocity.length() - 0.4 * SHOT_SPEED_MPS) < 1e-6
    angle = abs(ball.velocity.y) / ball.velocity.length()  # sinus de l'écart à l'axe du but (axe x)
    assert 0.6 < angle < 1.0  # 40 à 90° de l'axe

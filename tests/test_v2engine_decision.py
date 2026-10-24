"""Tests du moteur V2, Phase 5, ticket v2-cerveau-joueurs/01 (décision du porteur). Voir
.scratch/v2-cerveau-joueurs/issues/01-decision-du-porteur.md, critères d'acceptation."""

from __future__ import annotations

import random

from v2engine.ball_state import BallState
from v2engine.decision import (
    DECISION_INTERVAL_S,
    best_choice_probability,
    choose_action,
    evaluate_options,
)
from v2engine.geometry import PITCH_LENGTH_M, Vec2
from v2engine.match import GOAL_CENTER_Y, _step_ball, _step_player
from v2engine.movement import PlayerState, max_speed_mps

GOAL = Vec2(PITCH_LENGTH_M, GOAL_CENTER_Y)


def _player(name: str = "P", team: str = "home", poste: str = "BU", position: Vec2 = Vec2(50.0, 34.0),
            attributes: dict[str, int] | None = None) -> PlayerState:
    return PlayerState(
        name=name, team=team, poste=poste, position=position, velocity=Vec2(0.0, 0.0),
        pace=60, acceleration=60, stamina=60, home_target=position, attributes=attributes,
    )


def _kinds(options) -> set[str]:
    return {o.kind for o in options}


def test_decisions_curve_matches_validated_points() -> None:
    assert abs(best_choice_probability(99) - 0.95) < 1e-9
    assert abs(best_choice_probability(55) - 0.70) < 1e-9
    assert abs(best_choice_probability(11) - 0.45) < 1e-9


def test_shot_option_exists_up_to_30_m_and_not_beyond() -> None:
    at_25 = _player(position=Vec2(PITCH_LENGTH_M - 25.0, GOAL_CENTER_Y))
    at_32 = _player(position=Vec2(PITCH_LENGTH_M - 32.0, GOAL_CENTER_Y))
    assert "shot" in _kinds(evaluate_options(at_25, [at_25], GOAL, None))
    assert "shot" not in _kinds(evaluate_options(at_32, [at_32], GOAL, None))


def test_pressure_lowers_shot_and_dribble_values() -> None:
    holder = _player(position=Vec2(PITCH_LENGTH_M - 15.0, GOAL_CENTER_Y))
    marker = _player("Marqueur", team="away", position=holder.position + Vec2(0.5, 0.0))
    free = {o.kind: o.value for o in evaluate_options(holder, [holder], GOAL, None)}
    pressed = {o.kind: o.value for o in evaluate_options(holder, [holder, marker], GOAL, None)}
    assert pressed["shot"] < free["shot"]
    assert pressed["dribble"] < free["dribble"]


def test_pass_prefers_open_teammate_closer_to_goal_over_nearest_marked_one() -> None:
    holder = _player(position=Vec2(40.0, 34.0))
    near_marked = _player("Proche", position=Vec2(43.0, 34.0))
    marker = _player("Marqueur", team="away", position=Vec2(43.5, 34.0))
    far_open = _player("Demarque", position=Vec2(60.0, 20.0))
    options = evaluate_options(holder, [holder, near_marked, marker, far_open], GOAL, None)
    assert next(o for o in options if o.kind == "pass").target.name == "Demarque"


def test_high_decisions_picks_best_option_more_often_than_low() -> None:
    def best_rate(decisions: int) -> float:
        holder = _player(position=Vec2(PITCH_LENGTH_M - 10.0, GOAL_CENTER_Y), attributes={"Decisions": decisions})
        mate = _player("Coequipier", position=Vec2(60.0, 20.0))
        players = [holder, mate]
        best = max(evaluate_options(holder, players, GOAL, None), key=lambda o: o.value).kind
        random.seed(20260923)
        return sum(choose_action(holder, players, GOAL, None).kind == best for _ in range(2000)) / 2000

    assert best_rate(95) > best_rate(20) + 0.2


def test_lone_holder_dribbles_toward_goal_at_reduced_speed() -> None:
    holder = _player("Seul", position=Vec2(30.0, 34.0))
    ball = BallState(position=holder.position, velocity=Vec2(0.0, 0.0), holder="Seul")
    _step_ball(ball, 0.1, [holder], now_s=0.0)
    assert ball.holder == "Seul"

    for _ in range(60):  # 6 s : vitesse de croisière atteinte
        holder = _step_player(holder, ball, 0.1, 0.0)
    assert holder.position.x > 30.0
    assert holder.velocity.length() <= 0.85 * max_speed_mps(60) + 1e-9


def test_holder_keeps_his_choice_until_next_decision(monkeypatch) -> None:
    holder = _player("Porteur")
    mate = _player("Coequipier", position=Vec2(70.0, 34.0))
    ball = BallState(position=holder.position, velocity=Vec2(0.0, 0.0), holder="Porteur",
                     next_decision_s=DECISION_INTERVAL_S)
    monkeypatch.setattr("v2engine.match.choose_action", lambda *args: (_ for _ in ()).throw(AssertionError("décision trop tôt")))
    _step_ball(ball, 0.1, [holder, mate], now_s=DECISION_INTERVAL_S - 0.1)
    assert ball.holder == "Porteur"


def test_heavily_pressed_holder_at_15_m_prefers_open_pass_over_shot() -> None:
    holder = _player(position=Vec2(PITCH_LENGTH_M - 15.0, GOAL_CENTER_Y + 10.0))
    marker = _player("Marqueur", team="away", position=holder.position + Vec2(0.3, 0.0))
    open_mate = _player("Demarque", position=Vec2(PITCH_LENGTH_M - 8.0, GOAL_CENTER_Y))
    options = {o.kind: o.value for o in evaluate_options(holder, [holder, marker, open_mate], GOAL, None)}
    assert options["pass"] > options["shot"]


def test_new_holder_decides_immediately_after_winning_the_ball(monkeypatch) -> None:
    holder = _player("Porteur")
    tackler = _player("Tacleur", team="away", position=holder.position + Vec2(0.5, 0.0))
    ball = BallState(position=holder.position, velocity=Vec2(0.0, 0.0), holder="Porteur", next_decision_s=10.0)
    monkeypatch.setattr("v2engine.match.should_attempt_tackle", lambda aggression: True)
    monkeypatch.setattr("v2engine.match.resolve_tackle", lambda tackler, holder: type("W", (), {"won": True})())
    _step_ball(ball, 0.1, [holder, tackler], now_s=3.0)
    assert ball.holder == "Tacleur" and ball.next_decision_s == 3.0

"""Tacle par derrière en dernier recours (ticket v2-realisme/11h) : hors urgence défensive, le taux de tentative est
multiplié selon l'angle d'approche (1,0 de face, 0,6 de côté, 0,15 par derrière à Decisions 55) et le discernement
(Decisions) ; en urgence (porteur à moins de 20 m avec un angle de tir, ou dernier rempart), facteur 1,0 ; dans sa
surface, pas d'urgence et prudence de surface (Decisions 99 -> 0,35, 55 -> 0,5, 11 -> 0,75)."""

from __future__ import annotations

from dataclasses import replace

import pytest

from scenes import player
from v2engine.ball_state import BallState
from v2engine.duel import defensive_urgency, tackle_attempt_factor
from v2engine.geometry import Vec2, in_penalty_area
from v2engine.match import _OPPONENT_GOAL, _step_ball

GOAL = _OPPONENT_GOAL["home"]  # but défendu par l'équipe « away », attaqué par le porteur « home » (x = 105)


def _holder(x: float, y: float = 34.0):
    return replace(player("Porteur", "home", x, y, "BU"), facing=Vec2(1.0, 0.0))  # face au but adverse


def _tackler(x: float, y: float = 34.0, decisions: int = 55):
    return player("Def", "away", x, y, "DC", Decisions=decisions, Aggression=60)


def _cover(x: float, y: float = 34.0):
    return player("Couverture", "away", x, y, "DC")


def test_behind_far_from_goal_with_cover_is_rarely_attempted() -> None:
    holder, tackler = _holder(70.0), _tackler(69.0)  # 35 m du but, tacleur dans son dos
    players = [holder, tackler, _cover(95.0)]

    assert not defensive_urgency(holder, GOAL, players, tackler)
    assert tackle_attempt_factor(tackler, holder, False) == pytest.approx(0.15)


def test_last_defender_is_an_urgency() -> None:
    # décision du propriétaire du 16/11/2026 : le dernier rempart ne laisse pas l'attaquant marcher vers le but
    holder, tackler = _holder(60.0), _tackler(59.0)  # 45 m du but, aucun coéquipier de champ plus près du but
    keeper = player("Gardien", "away", 104.0, 34.0, "GK")  # le gardien ne compte pas comme rempart
    assert defensive_urgency(holder, GOAL, [holder, tackler, keeper], tackler)
    assert not defensive_urgency(holder, GOAL, [holder, tackler, keeper, _cover(90.0)], tackler)


def test_urgency_outside_the_box_keeps_the_base_rate() -> None:
    holder, tackler = _holder(86.0), _tackler(85.0)  # 19 m, dans l'axe, hors surface (16,5 m)
    assert defensive_urgency(holder, GOAL, [holder, tackler, _cover(100.0)], tackler)
    assert not in_penalty_area("home", holder.position)
    assert tackle_attempt_factor(tackler, holder, True) == 1.0


def test_front_and_side_factors_outside_urgency() -> None:
    holder = _holder(70.0)
    assert tackle_attempt_factor(_tackler(71.0), holder, False) == pytest.approx(1.0)  # de face : inchangé
    assert tackle_attempt_factor(_tackler(70.0, 35.0), holder, False) == pytest.approx(0.6)  # de côté


@pytest.mark.parametrize(("decisions", "side", "behind"), [(99, 0.553, 0.05), (55, 0.6, 0.15), (11, 0.718, 0.40)])
def test_decisions_sets_the_discernment(decisions: int, side: float, behind: float) -> None:
    holder = _holder(70.0)
    assert tackle_attempt_factor(_tackler(69.0, decisions=decisions), holder, False) == pytest.approx(behind)
    assert tackle_attempt_factor(_tackler(70.0, 35.0, decisions), holder, False) == pytest.approx(side, abs=1e-3)
    assert tackle_attempt_factor(_tackler(71.0, decisions=decisions), holder, False) == pytest.approx(1.0)


def test_close_without_shooting_angle_is_not_urgent_while_covered() -> None:
    holder, tackler = _holder(97.0, 20.0), _tackler(96.0, 20.0)  # 16 m du but, à 60° de l'axe
    assert holder.position.distance_to(GOAL) < 20.0
    assert not defensive_urgency(holder, GOAL, [holder, tackler, _cover(102.0)], tackler)
    assert defensive_urgency(holder, GOAL, [holder, tackler, _cover(80.0)], tackler)  # dernier rempart
    covered = [_holder(88.0, 30.0), tackler, _cover(100.0)]
    assert defensive_urgency(covered[0], GOAL, covered, tackler)  # 17 m, à 13° de l'axe


@pytest.mark.parametrize(("decisions", "box"), [(99, 0.35), (55, 0.5), (11, 0.75)])
def test_in_own_box_there_is_no_urgency_and_tackles_are_cautious(decisions: int, box: float) -> None:
    holder = _holder(95.0)  # 10 m, dans l'axe : urgence hors surface, mais faute = penalty
    front, behind = _tackler(96.0, decisions=decisions), _tackler(94.0, decisions=decisions)
    assert in_penalty_area("home", holder.position) and defensive_urgency(holder, GOAL, [holder, front], front)
    assert tackle_attempt_factor(front, holder, True, True) == pytest.approx(box)
    assert tackle_attempt_factor(behind, holder, True, True) == pytest.approx(
        box * tackle_attempt_factor(behind, holder, False))


def test_the_match_uses_the_factor_as_exposure_time(monkeypatch) -> None:
    holder, tackler = _holder(70.0), _tackler(69.0)
    ball = BallState(position=holder.position, velocity=Vec2(0.0, 0.0), holder="Porteur")
    seen: list[float] = []
    monkeypatch.setattr("v2engine.match.should_attempt_tackle", lambda aggression, dt: seen.append(dt) or False)

    _step_ball(ball, 0.1, [holder, tackler, _cover(95.0)])

    assert seen == [pytest.approx(0.1 * 0.15)]


def test_the_match_applies_box_caution(monkeypatch) -> None:
    holder, tackler = _holder(95.0), _tackler(96.0)  # de face, dans la surface, Decisions 55
    ball = BallState(position=holder.position, velocity=Vec2(0.0, 0.0), holder="Porteur")
    seen: list[float] = []
    monkeypatch.setattr("v2engine.match.should_attempt_tackle", lambda aggression, dt: seen.append(dt) or False)

    _step_ball(ball, 0.1, [holder, tackler])

    assert seen == [pytest.approx(0.1 * 0.5)]

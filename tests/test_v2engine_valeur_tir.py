"""Valeur du tir dans la décision (ticket v2-realisme/18k) : la chance de but moins ce que coûte un tir non marqué,
comme la perte d'une passe ou d'une conduite. Contré : ballon perdu près du tireur ; sinon (à côté, arrêté) : rendu à
l'adversaire à son but."""

from __future__ import annotations

import random

import pytest

from v2engine.danger import loss_cost
from v2engine.decision import CONSERVATION, CONTRE_ATTAQUE, evaluate_options, shot_value
from v2engine.geometry import Vec2
from v2engine.shooting import occasion_quality, physical_block_probability, shot_outcome_shares
from tests.scenes import player

GOAL = Vec2(105.0, 34.0)


def _options(holder, players):
    random.seed(1)
    options = evaluate_options(holder, players, GOAL, None)
    shot = next(o for o in options if o.kind == "shot")
    other = max((o for o in options if o.kind != "shot"), key=lambda o: o.value)
    return shot, other


def test_outcome_shares_are_the_occasion_quality_and_the_physical_block() -> None:
    shooter = player("A", x=85.0)
    defenders = [player("D", "away", x=90.0), player("E", "away", x=95.0, y=36.0)]
    goal_chance, blocked = shot_outcome_shares(shooter, GOAL, None, defenders)
    assert goal_chance == pytest.approx(occasion_quality(shooter, GOAL, None, defenders))
    assert blocked == pytest.approx(physical_block_probability(shooter, GOAL, defenders))


def test_shot_value_pays_the_loss_of_a_missed_shot() -> None:
    shooter = player("A", x=80.0)
    value = shot_value(shooter, None, 0.1, 0.2, GOAL)
    expected = 0.1 - (0.2 * loss_cost(shooter.position, "home") + 0.7 * loss_cost(GOAL, "home"))
    assert value == pytest.approx(expected)
    assert value < 0.1
    # pondération de la perte selon la transition, comme les autres options
    cost = 0.1 - value
    assert shot_value(shooter, CONTRE_ATTAQUE, 0.1, 0.2, GOAL) == pytest.approx(0.1 - 0.7 * cost)
    assert shot_value(shooter, CONSERVATION, 0.1, 0.2, GOAL) == pytest.approx(0.1 - 1.3 * cost)
    assert shot_value(shooter, None, 1.0, 0.0, GOAL) == pytest.approx(1.0)  # but sûr : rien à perdre


def test_a_blocked_shot_costs_more_than_a_shot_out_at_the_goal() -> None:
    shooter = player("A", x=75.0)
    assert loss_cost(shooter.position, "home") > loss_cost(GOAL, "home")
    assert shot_value(shooter, None, 0.05, 0.5, GOAL) < shot_value(shooter, None, 0.05, 0.0, GOAL)


def test_long_low_chance_shot_loses_to_safe_possession() -> None:
    """Tir à 28 m, axe libre, coéquipier libre à côté : la conservation l'emporte, alors que la chance de but seule
    (valeur du tir avant le 18k) battait toutes les autres options."""
    holder, mate = player("H", x=77.0), player("M", x=70.0, y=24.0)
    players = [holder, mate, player("D", "away", x=95.0), player("D2", "away", x=95.0, y=40.0)]
    shot, other = _options(holder, players)
    goal_chance, _ = shot_outcome_shares(holder, GOAL, None, players[2:])
    assert goal_chance < 0.08
    assert goal_chance > other.value  # avant le 18k, le tir l'emportait
    assert shot.value < other.value


def test_close_shot_facing_goal_still_wins() -> None:
    holder = player("H", x=97.0)
    players = [holder, player("M", x=80.0, y=20.0), player("D", "away", x=90.0, y=50.0)]
    shot, other = _options(holder, players)
    assert shot.value > other.value

"""Durée de réception selon le ballon reçu et Technique (ticket v2-collectif/31c) : un ballon dur, plus rapide que les
6 m/s idéaux (jusqu'à 30 m/s), s'oriente moins souvent ; Technique en compense une part (0,2 / 0,5 / 0,8 à 11 / 55 /
99). Le temps avant la première décision suit, par le contrôle orienté (31b)."""

from __future__ import annotations

import pytest

from v2engine.flux import seed_streams
from v2engine.geometry import Vec2
from v2engine.possession import (hard_ball_share, hard_ball_technique_share, oriented_control_probability,
                                 orients_control, reception_delay_s)
from tests.scenes import player


def _receiver(technique: int, first_touch: int = 55):
    return player("R", **{"First_Touch": first_touch, "Technique": technique})


def _expected_delay(receiver, ball: Vec2) -> float:
    p = oriented_control_probability(receiver, ball)
    return p * reception_delay_s(receiver, oriented=True) + (1.0 - p) * reception_delay_s(receiver, oriented=False)


def test_hardness_runs_from_the_ideal_speed_to_the_fastest_pass() -> None:
    assert hard_ball_share(Vec2(3.0, 0.0)) == 0.0 and hard_ball_share(Vec2(6.0, 0.0)) == 0.0
    assert hard_ball_share(Vec2(18.0, 0.0)) == pytest.approx(0.5)
    assert hard_ball_share(Vec2(30.0, 0.0)) == 1.0 and hard_ball_share(Vec2(40.0, 0.0)) == 1.0
    assert [hard_ball_technique_share(_receiver(n)) for n in (11, 55, 99)] == pytest.approx([0.2, 0.5, 0.8])


def test_validated_example_at_eighteen_metres_per_second() -> None:
    """Exemple validé par le propriétaire : First Touch 55, ballon à 18 m/s ; Technique 11 / 55 / 99 : chance d'orienter
    30 / 37,5 / 45 %, temps moyen 2,668 / 2,53 / 2,392 s (annoncés arrondis à tort 2,65 / 2,53 / 2,38 s dans la
    proposition ; même loi) ; ballon à 6 m/s : 50 %, 2,3 s."""
    ball = Vec2(18.0, 0.0)
    for technique, chance, delay in ((11, 0.30, 2.668), (55, 0.375, 2.53), (99, 0.45, 2.392)):
        receiver = _receiver(technique)
        assert oriented_control_probability(receiver, ball) == pytest.approx(chance)
        assert _expected_delay(receiver, ball) == pytest.approx(delay)
    for technique in (11, 99):
        assert oriented_control_probability(_receiver(technique), Vec2(6.0, 0.0)) == pytest.approx(0.5)


def test_faster_ball_longer_reception_higher_technique_shorter() -> None:
    """Critères du ticket, en scène contrôlée."""
    receiver = _receiver(55)
    delays = [_expected_delay(receiver, Vec2(v, 0.0)) for v in (6.0, 12.0, 18.0, 24.0, 30.0)]
    assert delays == sorted(delays) and delays[0] < delays[-1]
    fast = Vec2(24.0, 0.0)
    assert _expected_delay(_receiver(99), fast) < _expected_delay(_receiver(55), fast) < _expected_delay(_receiver(11), fast)


def test_the_draws_follow_the_law() -> None:
    receiver, ball = _receiver(55), Vec2(18.0, 0.0)
    seed_streams(7)
    share = sum(orients_control(receiver, ball) for _ in range(4000)) / 4000
    assert share == pytest.approx(0.375, abs=0.025)

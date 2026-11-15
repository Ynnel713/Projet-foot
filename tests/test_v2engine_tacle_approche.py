"""Tacle selon l'angle d'approche et la vitesse de rapprochement (ticket v2-realisme/11d) : de face, de côté, par
derrière, la réussite baisse et la faute monte ; une approche trop rapide ajoute faute et ratés ; aucun attribut en jeu
(Tackling, Strength et Aggression gardent leur seul rôle, règle R1)."""

from __future__ import annotations

import math
from dataclasses import replace

import pytest

from v2engine.duel import (TACKLE_FOUL_MAX, foul_probability, resolve_tackle, tackle_approach_angle_deg,
                           tackle_approach_factors, tackle_closing_speed_mps, tackle_probabilities,
                           tackle_success_probability)
from v2engine.geometry import Vec2
from tests.scenes import player, seed_scene

HOLDER_AT = Vec2(50.0, 34.0)


def _duel(angle_deg: float, closing_mps: float = 0.0, *, tackling: int = 62, strength: int = 62, aggression: int = 62):
    """Porteur arrêté, corps tourné vers +x ; tacleur à 1 m, venant de `angle_deg` (0 = de face), lancé vers lui à
    `closing_mps`."""
    a = math.radians(angle_deg)
    side = Vec2(math.cos(a), math.sin(a))
    holder = replace(player("Porteur", "home", HOLDER_AT.x, HOLDER_AT.y, "MC", Strength=strength),
                     facing=Vec2(1.0, 0.0))
    tackler = replace(player("Tacleur", "away", HOLDER_AT.x + side.x, HOLDER_AT.y + side.y, "DC",
                             Tackling=tackling, Aggression=aggression), velocity=side * -closing_mps)
    return tackler, holder


def test_angle_and_closing_speed_are_read_from_the_scene() -> None:
    for angle in (0.0, 45.0, 90.0, 135.0, 180.0):
        tackler, holder = _duel(angle, 5.0)
        assert tackle_approach_angle_deg(tackler, holder) == pytest.approx(angle, abs=1e-6)
        assert tackle_closing_speed_mps(tackler, holder) == pytest.approx(5.0)
    tackler, holder = _duel(0.0)
    assert tackle_closing_speed_mps(replace(tackler, velocity=Vec2(3.0, 0.0)), holder) == pytest.approx(-3.0)


@pytest.mark.parametrize("angle, success, foul", [(0.0, 1.0, 1.0), (90.0, 0.9, 1.3), (180.0, 0.6, 2.0),
                                                  (45.0, 0.95, 1.15), (135.0, 0.75, 1.65)])
def test_angle_factors_at_the_validated_points(angle: float, success: float, foul: float) -> None:
    assert tackle_approach_factors(*_duel(angle)) == pytest.approx((success, foul))


def test_same_duel_front_side_behind_success_decreases_and_foul_increases() -> None:
    front, side, behind = (tackle_probabilities(*_duel(a)) for a in (0.0, 90.0, 180.0))
    assert front[0] > side[0] > behind[0]
    assert front[1] < side[1] < behind[1]
    # tacleur et porteur moyens : faute ~30 % de face, ~60 % par derrière
    assert front[1] == pytest.approx(0.30, abs=0.01) and behind[1] == pytest.approx(0.60, abs=0.02)


@pytest.mark.parametrize("closing, success, foul", [(0.0, 1.0, 1.0), (2.0, 1.0, 1.0), (4.0, 0.94, 1.2),
                                                    (7.0, 0.85, 1.5), (12.0, 0.85, 1.5)])
def test_closing_speed_above_two_mps_adds_fouls_and_misses_with_caps(closing: float, success: float,
                                                                      foul: float) -> None:
    assert tackle_approach_factors(*_duel(0.0, closing)) == pytest.approx((success, foul))


def test_behind_at_six_mps_combines_both_factors() -> None:
    assert tackle_approach_factors(*_duel(180.0, 6.0)) == pytest.approx((0.6 * 0.88, 2.0 * 1.4))


def test_foul_probability_is_capped() -> None:
    _, foul = tackle_probabilities(*_duel(180.0, 9.0, aggression=99))
    assert foul == TACKLE_FOUL_MAX


def test_front_standing_tackle_keeps_the_attribute_probabilities() -> None:
    tackler, holder = _duel(0.0)
    assert tackle_probabilities(tackler, holder) == (tackle_success_probability(tackler, holder),
                                                     foul_probability(62))


def test_approach_factors_read_no_attribute() -> None:
    """R1 : l'approche est une situation, pas un attribut -- mêmes facteurs à attributs extrêmes."""
    for angle in (0.0, 90.0, 180.0):
        ref = tackle_approach_factors(*_duel(angle, 5.0))
        assert tackle_approach_factors(*_duel(angle, 5.0, tackling=99, strength=11, aggression=99)) == ref
        assert tackle_approach_factors(*_duel(angle, 5.0, tackling=11, strength=99, aggression=11)) == ref


def test_resolved_tackles_from_behind_win_less_and_foul_more() -> None:
    """Même duel tiré 4 000 fois de face et par derrière (flux DUEL semé) : écart conforme aux probabilités."""
    rates = {}
    for angle in (0.0, 180.0):
        seed_scene(11)
        results = [resolve_tackle(*_duel(angle)) for _ in range(4000)]
        rates[angle] = (sum(r.won for r in results) / 4000, sum(r.foul for r in results) / 4000)
    assert rates[0.0][0] > rates[180.0][0] + 0.15  # gagnés (sans faute) : ~0,35 contre ~0,12
    assert rates[180.0][1] > rates[0.0][1] + 0.2  # fautes : ~0,30 contre ~0,60
    assert rates[0.0][1] == pytest.approx(0.30, abs=0.03) and rates[180.0][1] == pytest.approx(0.60, abs=0.03)

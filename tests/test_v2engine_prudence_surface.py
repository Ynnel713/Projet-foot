"""Prudence de surface commune aux fautes (ticket v2-realisme/21c1) : une seule courbe Decisions (99 -> 0,35,
55 -> 0,5, 11 -> 0,75, celle du 11h), utilisée par le tacle et par la faute de charge du duel d'épaule (11c) quand le
contact a lieu dans la surface que défend le chargeur ; jamais nulle, aucun tirage ajouté."""

from __future__ import annotations

from dataclasses import replace

import pytest

import v2engine.duel as duel
from scripts import bench_series as bs
from scenes import player, seed_scene
from v2engine.duel import box_prudence, resolve_shoulder_duel, shoulder_foul_probability, tackle_attempt_factor
from v2engine.geometry import Vec2, in_penalty_area


def _charger(decisions: int = 55, aggression: int = 80):
    return player("Def", "away", 100.0, 34.0, "DC", Decisions=decisions, Anticipation=decisions, Aggression=aggression, Strength=99)


def _attacker(x: float):
    return player("Att", "home", x, 34.8, "BU", Strength=1)


@pytest.mark.parametrize(("decisions", "factor"), [(99, 0.35), (55, 0.5), (11, 0.75), (33, 0.625), (1, 0.75),
                                                    (100, 0.35)])
def test_one_curve_set_by_decisions_and_never_zero(decisions: int, factor: float) -> None:
    assert box_prudence(_charger(decisions)) == pytest.approx(factor)


@pytest.mark.parametrize("decisions", [11, 55, 99])
def test_the_tackle_and_the_charge_share_the_same_prudence(decisions: int) -> None:
    charger = _charger(decisions)
    holder = replace(_attacker(95.0), position=Vec2(95.0, 34.0), facing=Vec2(1.0, 0.0))  # dans l'axe du tacleur
    assert tackle_attempt_factor(charger, holder, True, True) == pytest.approx(box_prudence(charger))  # de face
    outside = shoulder_foul_probability(charger)
    assert outside > 0.0
    assert shoulder_foul_probability(charger, in_own_box=True) == pytest.approx(outside * box_prudence(charger))


def test_the_box_is_judged_where_the_charged_player_stands(monkeypatch) -> None:
    """Chargeur « away » : sa surface est celle que « home » attaque (x proche de 105) ; perdant pris pour le lieu."""
    seen: list[bool] = []
    monkeypatch.setattr(duel, "shoulder_foul_probability", lambda charger, in_own_box=False: seen.append(in_own_box)
                        or 0.0)
    for x in (100.0, 60.0):
        seed_scene(1)
        result = resolve_shoulder_duel(_charger(), _attacker(x))
        assert result.winner.name == "Def" and result.loser.name == "Att"
        assert in_penalty_area("home", result.loser.position) == (x == 100.0)
    assert seen == [True, False]


def _foul_rate(x: float, decisions: int, draws: int, seed: int = 7) -> float:
    seed_scene(seed)
    return sum(resolve_shoulder_duel(_charger(decisions), _attacker(x)).foul for _ in range(draws)) / draws


def test_charges_in_own_box_are_rarer_but_still_happen() -> None:
    """Même scène (chargeur dominant, Aggression 80), 6 000 duels : dans sa surface, faute plus rare, jamais nulle."""
    outside, inside = _foul_rate(60.0, 55, 6000), _foul_rate(100.0, 55, 6000)
    assert outside > 0.03
    assert 0.0 < inside < 0.7 * outside
    assert inside / outside == pytest.approx(0.5, abs=0.15)
    assert _foul_rate(100.0, 99, 6000) < _foul_rate(100.0, 11, 6000)  # plus de discernement, moins de fautes


def test_same_seed_same_draws() -> None:
    assert _foul_rate(100.0, 55, 500, seed=3) == _foul_rate(100.0, 55, 500, seed=3)


def test_the_bench_can_neutralise_21c1() -> None:
    charger = _charger()
    real = duel.shoulder_foul_probability
    with bs.neutralised(["21c1"]):
        assert duel.shoulder_foul_probability(charger, True) == pytest.approx(real(charger))
    assert duel.shoulder_foul_probability is real

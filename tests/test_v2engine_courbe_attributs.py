"""Forme de la courbe partagée des attributs (ticket v2-realisme/24, objectif révisé et validé le 14/11/2026) : de vrais
écarts entre notes proches, là où sont les joueurs (60 à 80)."""

import math

import pytest

from v2engine.attributes import duel_probability, success_probability

# Réglages réels des actions du moteur (baseline, amplitude, min, max), plus les réglages par défaut.
_SETTINGS = [(0.6, 0.35, 0.05, 0.95), (0.5, 0.5, 0.0, 1.0), (0.7, 0.25, 0.05, 0.95), (0.75, 0.25, 0.5, 1.0),
             (0.4, 0.4, 0.05, 0.95), (0.3, 0.25, 0.05, 0.95)]


@pytest.mark.parametrize("baseline,amplitude,low,high", _SETTINGS)
def test_notes_70_and_80_really_differ(baseline: float, amplitude: float, low: float, high: float) -> None:
    def p(n: float) -> float:
        return success_probability(n, baseline=baseline, amplitude=amplitude, min_prob=low, max_prob=high)
    full = p(99) - p(50)
    assert (p(70) - p(60)) / full >= 0.25  # au moins le quart de l'écart 50 -> 99 (4 % avec l'ancienne forme)
    assert (p(80) - p(70)) / full >= 0.20  # au moins le cinquième (14 % avant)


def test_ten_points_in_a_duel_give_at_least_58_percent() -> None:
    assert duel_probability(80, 70) >= 0.58  # 50,6 % avec l'ancienne forme
    assert duel_probability(70, 60) == pytest.approx(duel_probability(80, 70))  # seul l'écart compte
    assert duel_probability(80, 70) == pytest.approx(0.6286, abs=1e-4)
    assert duel_probability(90, 70) == pytest.approx(0.7427, abs=1e-4)


def test_never_binary_monotone_and_bounded() -> None:
    values = [success_probability(n) for n in range(0, 100)]
    assert all(0.05 <= v <= 0.95 for v in values)
    assert all(b >= a for a, b in zip(values, values[1:]))
    duels = [duel_probability(n, 50) for n in range(0, 100)]
    assert all(0.05 <= v <= 0.95 for v in duels) and all(b >= a for a, b in zip(duels, duels[1:]))
    assert success_probability(11) == pytest.approx(0.25) and success_probability(5) == pytest.approx(0.25)


def test_duel_is_symmetric() -> None:
    for a, b in ((80, 70), (99, 11), (62, 61), (55, 90)):
        assert duel_probability(a, b) + duel_probability(b, a) == pytest.approx(1.0)


def test_curve_is_centred_on_the_median_note() -> None:
    assert success_probability(62) == pytest.approx(0.6)  # note médiane réelle (60 tous joueurs, 65 titulaires)
    assert success_probability(99) == pytest.approx(0.95)  # extrêmes validés inchangés : 99 -> maximum, 11 -> minimum
    assert success_probability(11) == pytest.approx(0.25)
    shaped = math.tanh(2.0 * 18.0 / 37.0) / math.tanh(2.0)  # 80 : t = 18/37, pente 2, normalisée (t = 1 -> amplitude)
    assert success_probability(80) == pytest.approx(0.6 + 0.35 * shaped)
    shaped = math.tanh(2.0 * -12.0 / 51.0) / math.tanh(2.0)  # 50 : t = -12/51
    assert success_probability(50) == pytest.approx(0.6 + 0.35 * shaped)

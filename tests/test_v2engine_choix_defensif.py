"""Tests du moteur V2, ticket v2-attributs-contextes/04a (contexte « choix défensif », Decisions 0,7 et Anticipation
0,3) : le renoncement au tacle du ticket v2-realisme/11h lit le contexte, à l'identique à notes égales ; le tacle plongé,
lancé à plus de 2 m/s hors urgence, est multiplié par 11 -> 1,3, 55 -> 1,0, 99 -> 0,5. Voir
.scratch/v2-attributs-contextes/issues/04a-decisions-en-defense.md, critères d'acceptation."""

from __future__ import annotations

from dataclasses import replace

import pytest

from scenes import player
from v2engine.contextes import CHOIX_DEFENSIF, contextual_rating
from v2engine.duel import (TACKLE_DIVE_FACTOR_BY_CHOICE, should_attempt_tackle, tackle_attempt_factor,
                           tackle_closing_speed_mps)
from v2engine.flux import DUEL
from v2engine.geometry import Vec2


def _holder():
    return replace(player("Porteur", "home", 70.0, 34.0, "BU"), facing=Vec2(1.0, 0.0))  # face au but adverse


def _tackler(x: float, y: float = 34.0, decisions: int = 55, anticipation: int | None = None, speed: float = 0.0):
    tackler = player("Def", "away", x, y, "DC", Decisions=decisions,
                     Anticipation=decisions if anticipation is None else anticipation, Aggression=60)
    return replace(tackler, velocity=Vec2(-speed, 0.0))  # de face, il court vers le porteur (x décroissant)


def test_the_11h_discernment_is_unchanged_at_equal_notes() -> None:
    holder = _holder()
    for note, behind in ((11, 0.40), (55, 0.15), (99, 0.05)):
        assert tackle_attempt_factor(_tackler(69.0, decisions=note), holder, False) == pytest.approx(behind)
    mixed = _tackler(69.0, decisions=99, anticipation=11)  # 0,7 x 99 + 0,3 x 11 = 72,6
    assert contextual_rating(mixed, CHOIX_DEFENSIF) == pytest.approx(72.6)
    assert 0.05 < tackle_attempt_factor(mixed, holder, False) < 0.15


def test_a_diving_tackle_follows_the_validated_points() -> None:
    assert TACKLE_DIVE_FACTOR_BY_CHOICE == (1.3, 1.0, 0.5)
    holder = _holder()
    for note, expected in ((11, 1.3), (33, 1.15), (55, 1.0), (99, 0.5)):
        diving = _tackler(71.0, decisions=note, speed=4.0)
        assert tackle_closing_speed_mps(diving, holder) == pytest.approx(4.0)
        assert tackle_attempt_factor(diving, holder, False) == pytest.approx(expected)  # de face, plongé


def test_no_dive_factor_at_walking_pace_or_in_urgency() -> None:
    holder = _holder()
    for note in (11, 99):
        assert tackle_attempt_factor(_tackler(71.0, decisions=note, speed=1.5), holder, False) == pytest.approx(1.0)
        assert tackle_attempt_factor(_tackler(71.0, decisions=note, speed=4.0), holder, True) == 1.0


def _attempts(note: int, steps: int = 40000, dt: float = 0.1) -> int:
    """Tentatives sur `steps` pas d'exposition (flux DUEL du tirage, semé puis rendu dans son état)."""
    holder, tackler = _holder(), _tackler(71.0, decisions=note, speed=4.0)
    state = DUEL.getstate()
    DUEL.seed(20261117)
    try:
        return sum(should_attempt_tackle(60, dt * tackle_attempt_factor(tackler, holder, False)) for _ in range(steps))
    finally:
        DUEL.setstate(state)


def test_a_good_defender_dives_in_less_often_than_a_poor_one() -> None:
    # même exposition, même Aggression : le plongé reste possible à 99, jamais binaire
    good, poor = _attempts(99), _attempts(11)
    assert 0 < good < poor
    assert good / poor == pytest.approx(0.5 / 1.3, rel=0.15)

"""Collision asymétrique (ticket v2-realisme/11b) : la poussée et le choc mou du 11a sont partagés selon Strength
(`duel.contact_share`, courbe de duel partagée) ; le plus faible au contact est le plus déplacé et le plus freiné."""

from __future__ import annotations

from dataclasses import replace

import pytest

from v2engine.duel import contact_share
from v2engine.geometry import Vec2
from v2engine.match import _resolve_player_collisions
from tests.scenes import player


def _pair(strength_a: int, strength_b: int, va: Vec2 = Vec2(0.0, 0.0), vb: Vec2 = Vec2(0.0, 0.0), gap: float = 0.4):
    """A à gauche, B à droite, chevauchement de 0,2 m (rayons 0,3 + 0,3)."""
    a = replace(player("A", x=50.0, y=34.0, Strength=strength_a), velocity=va)
    b = replace(player("B", "away", x=50.0 + gap, y=34.0, Strength=strength_b), velocity=vb)
    return a, b


def _displacements(strength_a: int, strength_b: int) -> tuple[float, float]:
    a, b = _pair(strength_a, strength_b)
    _resolve_player_collisions([a, b])
    return abs(a.position.x - 50.0), abs(b.position.x - 50.4)


def test_equal_strength_shares_half() -> None:
    a, b = _pair(70, 70)
    assert contact_share(a, b) == pytest.approx(0.5)
    da, db = _displacements(70, 70)
    assert da == pytest.approx(0.1) and db == pytest.approx(0.1)


def test_share_is_symmetric_and_bounded() -> None:
    a, b = _pair(90, 40)
    assert contact_share(a, b) + contact_share(b, a) == pytest.approx(1.0)
    assert contact_share(a, b) == pytest.approx(0.75)  # 50 points d'écart : au plafond
    weakest, strongest = _pair(1, 99)
    assert contact_share(weakest, strongest) == pytest.approx(0.25)


def test_strength_90_against_40_moved_at_least_twice_less() -> None:
    """Scène A/B du ticket : Strength 90 contre 40, le plus fort subit au moins deux fois moins de déplacement."""
    strong, weak = _displacements(90, 40)
    assert strong * 2.0 <= weak
    assert strong + weak == pytest.approx(0.2)  # le chevauchement est toujours entièrement résorbé
    assert strong == pytest.approx(0.05) and weak == pytest.approx(0.15)


def test_share_grows_with_the_gap() -> None:
    shares = [contact_share(*_pair(60 + gap, 60)) for gap in (0, 10, 20, 30, 39)]
    assert shares == sorted(shares) and len(set(shares)) == len(shares)
    assert shares[1] == pytest.approx(0.58, abs=0.005) and shares[2] == pytest.approx(0.652, abs=0.005)


def test_closing_speed_cancelled_and_momentum_conserved_with_strength_masses() -> None:
    """Choc mou du 11a conservé : plus de vitesse de rapprochement ; quantité de mouvement conservée avec des masses
    dans le rapport share / (1 - share)."""
    a, b = _pair(90, 40, va=Vec2(6.0, 0.0), vb=Vec2(-2.0, 0.0))
    share = contact_share(a, b)
    mass_a, mass_b = share, 1.0 - share
    before = mass_a * a.velocity.x + mass_b * b.velocity.x
    _resolve_player_collisions([a, b])
    assert a.velocity.x == pytest.approx(b.velocity.x)
    assert mass_a * a.velocity.x + mass_b * b.velocity.x == pytest.approx(before)


def test_runner_into_stronger_standing_player_loses_more() -> None:
    """Coureur faible (40) à 6 m/s contre joueur fort (90) arrêté : le coureur garde 1,5 m/s (25 %), pas 3 (11a)."""
    a, b = _pair(40, 90, va=Vec2(6.0, 0.0))
    _resolve_player_collisions([a, b])
    assert a.velocity.x == pytest.approx(1.5) and b.velocity.x == pytest.approx(1.5)


def test_tangential_speed_still_kept() -> None:
    a = replace(player("A", x=50.0, y=34.0, Strength=90), velocity=Vec2(5.0, 1.0))
    b = replace(player("B", "away", x=50.0, y=34.5, Strength=40), velocity=Vec2(5.0, -1.0))
    _resolve_player_collisions([a, b])
    assert a.velocity.x == pytest.approx(5.0) and b.velocity.x == pytest.approx(5.0)

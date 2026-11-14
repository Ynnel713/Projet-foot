"""Collision : la vitesse change aussi (ticket v2-realisme/11a). Choc mou, masses égales : au contact, deux joueurs
perdent la vitesse qui les rapproche, moitié chacun ; la vitesse qui ne les rapproche pas (tangentielle, ou qui les
éloigne) est gardée."""

from __future__ import annotations

from dataclasses import replace

import pytest

from v2engine.geometry import Vec2
from v2engine.match import COLLISION_RESTITUTION, _resolve_player_collisions
from tests.scenes import player


def _pair(va: Vec2, vb: Vec2, gap: float = 0.5):
    """A à gauche, B à droite, distants de `gap` (rayons 0,3 + 0,3 : chevauchement si gap < 0,6)."""
    a = replace(player("A", x=50.0, y=34.0), velocity=va)
    b = replace(player("B", "away", x=50.0 + gap, y=34.0), velocity=vb)
    return [a, b]


def test_soft_collision_by_default() -> None:
    assert COLLISION_RESTITUTION == 0.0


def test_head_on_at_5_mps_cancels_the_closing_speed() -> None:
    """Scène du ticket : face à face à 5 m/s chacun, au contact : vitesses de rapprochement nulles."""
    a, b = _pair(Vec2(5.0, 0.0), Vec2(-5.0, 0.0))
    _resolve_player_collisions([a, b])
    assert a.velocity.x == pytest.approx(0.0) and b.velocity.x == pytest.approx(0.0)
    assert b.position.x - a.position.x == pytest.approx(0.6)  # écartés, comme avant


def test_runner_into_a_standing_player_shares_his_speed() -> None:
    """Masses égales : le coureur à 6 m/s qui heurte un joueur arrêté le pousse ; les deux repartent à 3 m/s."""
    a, b = _pair(Vec2(6.0, 0.0), Vec2(0.0, 0.0))
    _resolve_player_collisions([a, b])
    assert a.velocity.x == pytest.approx(3.0) and b.velocity.x == pytest.approx(3.0)


def test_tangential_speed_is_kept() -> None:
    """Contact d'épaule en courant côte à côte : la vitesse le long de la course n'est pas touchée."""
    a = replace(player("A", x=50.0, y=34.0), velocity=Vec2(5.0, 1.0))
    b = replace(player("B", "away", x=50.0, y=34.5), velocity=Vec2(5.0, -1.0))  # B à côté de A, ils se resserrent
    _resolve_player_collisions([a, b])
    assert a.velocity.x == pytest.approx(5.0) and b.velocity.x == pytest.approx(5.0)
    assert a.velocity.y == pytest.approx(0.0) and b.velocity.y == pytest.approx(0.0)


def test_players_moving_apart_keep_their_speed() -> None:
    a, b = _pair(Vec2(-2.0, 0.0), Vec2(3.0, 0.0))
    _resolve_player_collisions([a, b])
    assert a.velocity.x == pytest.approx(-2.0) and b.velocity.x == pytest.approx(3.0)


def test_no_contact_no_change() -> None:
    a, b = _pair(Vec2(5.0, 0.0), Vec2(-5.0, 0.0), gap=0.7)
    _resolve_player_collisions([a, b])
    assert a.velocity.x == pytest.approx(5.0) and b.velocity.x == pytest.approx(-5.0)


def test_momentum_is_conserved() -> None:
    a, b = _pair(Vec2(4.0, 1.5), Vec2(-1.0, 2.0))
    before = a.velocity + b.velocity
    _resolve_player_collisions([a, b])
    after = a.velocity + b.velocity
    assert after.x == pytest.approx(before.x) and after.y == pytest.approx(before.y)

"""Balance : rester debout et continuer après un contact (ticket v2-realisme/12c). Après un contact perdu (collision
dont on reçoit la plus petite part, à plus de 2 m/s de rapprochement, ou tacle subi sans perdre le ballon), le
joueur perd une part de sa vitesse et attend un délai avant d'agir, les deux réduits par Balance. Balance n'entre
plus dans le tacle (Strength seule, dérogation A3 levée)."""

from __future__ import annotations

from dataclasses import dataclass, replace

import pytest

from v2engine.ball_state import BallState
from v2engine.duel import (CONTACT_MIN_CLOSING_MPS, after_contact_delay_s, after_contact_speed_loss,
                           tackle_success_probability)
from v2engine.geometry import Vec2
from v2engine.match import _resolve_player_collisions, _step_ball, _unsettle
from tests.scenes import player, seed_scene


@pytest.mark.parametrize("balance, loss, delay", [(99, 0.05, 0.1), (62, 0.20, 0.3), (11, 0.40, 0.6)])
def test_curve_anchors(balance: int, loss: float, delay: float) -> None:
    p = player("J", Balance=balance)
    assert after_contact_speed_loss(p) == pytest.approx(loss)
    assert after_contact_delay_s(p) == pytest.approx(delay)


def test_curves_decrease_with_balance() -> None:
    notes = range(1, 100, 7)
    losses = [after_contact_speed_loss(player("J", Balance=b)) for b in notes]
    delays = [after_contact_delay_s(player("J", Balance=b)) for b in notes]
    assert losses == sorted(losses, reverse=True) and delays == sorted(delays, reverse=True)


def test_balance_no_longer_enters_the_tackle() -> None:
    tackler = player("T", "away", Tackling=60)
    steady, wobbly = player("P", Strength=60, Balance=99), player("P", Strength=60, Balance=11)
    assert tackle_success_probability(tackler, steady) == tackle_success_probability(tackler, wobbly)
    assert tackle_success_probability(tackler, player("P", Strength=90)) < tackle_success_probability(
        tackler, player("P", Strength=30))


def _pair(strength_a: int, strength_b: int, va: Vec2, vb: Vec2 = Vec2(0.0, 0.0)):
    a = replace(player("A", x=50.0, y=34.0, Strength=strength_a), velocity=va)
    b = replace(player("B", "away", x=50.4, y=34.0, Strength=strength_b), velocity=vb)
    return a, b


def test_the_weaker_loses_a_frank_contact() -> None:
    a, b = _pair(40, 90, Vec2(6.0, 0.0))
    assert [p.name for p in _resolve_player_collisions([a, b])] == ["A"]


def test_equal_strength_both_lose() -> None:
    a, b = _pair(60, 60, Vec2(6.0, 0.0))
    assert {p.name for p in _resolve_player_collisions([a, b])} == {"A", "B"}


def test_slow_contact_is_not_a_lost_contact() -> None:
    """Frôlement au pas : sous le seuil de rapprochement, rien ne déséquilibre."""
    a, b = _pair(40, 90, Vec2(CONTACT_MIN_CLOSING_MPS - 0.5, 0.0))
    assert _resolve_player_collisions([a, b]) == []


def test_off_ball_loser_can_neither_tackle_nor_control_during_the_delay() -> None:
    p = replace(player("J", Balance=11), velocity=Vec2(5.0, 0.0))
    ball = BallState(position=Vec2(0.0, 0.0), velocity=Vec2(0.0, 0.0), holder="Autre")
    _unsettle(p, ball, 10.0)
    assert p.velocity.x == pytest.approx(3.0)  # 40 % perdus
    assert ball.unsettled_until_s["J"] == pytest.approx(10.6)
    assert "J" not in ball.control_ban_until_s and "J" not in ball.tackle_ban_until_s  # pas un contrôle raté


def test_unsettled_off_ball_player_triggers_no_team_press(monkeypatch) -> None:
    """Rejet A1 de l'expert (passage 1) : un contact perdu loin du ballon n'est pas un contrôle raté, il ne lance pas
    le pressing d'équipe adverse (`defense._watch_triggers`)."""
    from v2engine.defense import DefensiveRoles
    started = []
    monkeypatch.setattr(DefensiveRoles, "start_team_press", lambda self, team, players, now_s, *a: started.append(team))
    p = replace(player("J", x=30.0, y=20.0, Balance=11), velocity=Vec2(5.0, 0.0))
    other = player("Autre", "away", x=80.0, y=34.0)
    ball = BallState(position=other.position, velocity=Vec2(0.0, 0.0), holder="Autre")
    _unsettle(p, ball, 10.0)
    DefensiveRoles()._watch_triggers([p, other], ball, None, 10.0)
    assert started == []


def test_unsettled_player_does_not_play_a_ball_reaching_him() -> None:
    """Le ballon libre qui arrive sur un joueur déséquilibré lui échappe pendant le délai, il le joue après."""
    for now_s, expected in ((10.0, None), (11.0, "J")):
        p = player("J", x=50.0, y=34.0, Balance=11)
        ball = BallState(position=Vec2(49.0, 34.0), velocity=Vec2(10.0, 0.0), holder=None)
        ball.unsettled_until_s["J"] = 10.6
        seed_scene(1)
        _step_ball(ball, 0.1, [p], now_s)
        assert ball.holder == expected


def test_holder_decision_is_postponed_and_delays_do_not_stack() -> None:
    p = replace(player("J", Balance=62), velocity=Vec2(4.0, 0.0))
    ball = BallState(position=Vec2(0.0, 0.0), velocity=Vec2(0.0, 0.0), holder="J", next_decision_s=10.5)
    _unsettle(p, ball, 10.0)
    assert ball.next_decision_s == pytest.approx(10.5)  # décision déjà plus tardive : gardée
    _unsettle(p, ball, 10.4)
    assert ball.next_decision_s == pytest.approx(10.7)
    assert "J" not in ball.tackle_ban_until_s


def test_same_contact_balance_99_against_11() -> None:
    """Scène A/B du ticket : même contact, Balance 99 contre 11 : délai plus court et moins de vitesse perdue."""
    results = {}
    for balance in (99, 11):
        a = replace(player("A", x=50.0, y=34.0, Strength=40, Balance=balance), velocity=Vec2(6.0, 1.0))
        b = replace(player("B", "away", x=50.4, y=34.0, Strength=90), velocity=Vec2(0.0, 0.0))
        ball = BallState(position=Vec2(0.0, 0.0), velocity=Vec2(0.0, 0.0), holder="Autre")
        for loser in _resolve_player_collisions([a, b]):
            _unsettle(loser, ball, 0.0)
        results[balance] = (a.velocity.length(), ball.unsettled_until_s["A"])
    (speed_99, delay_99), (speed_11, delay_11) = results[99], results[11]
    assert speed_99 > speed_11 and delay_99 < delay_11
    assert delay_99 == pytest.approx(0.1) and delay_11 == pytest.approx(0.6)


@dataclass
class _MissedTackle:
    won: bool = False
    foul: bool = False


def test_holder_who_survives_a_tackle_is_unsettled(monkeypatch) -> None:
    holder = replace(player("Porteur", x=50.0, y=34.0, Balance=11), velocity=Vec2(5.0, 0.0))
    challenger = player("Adversaire", "away", x=50.5, y=34.0)
    ball = BallState(position=Vec2(50.0, 34.0), velocity=Vec2(0.0, 0.0), holder="Porteur")
    monkeypatch.setattr("v2engine.match.should_attempt_tackle", lambda aggression, dt: True)
    monkeypatch.setattr("v2engine.match.resolve_tackle", lambda tackler, h: _MissedTackle())
    _step_ball(ball, 0.1, [holder, challenger], 3.0)
    assert ball.holder == "Porteur"
    assert holder.velocity.x == pytest.approx(3.0)
    assert ball.next_decision_s == pytest.approx(3.6)


def test_foul_does_not_unsettle_through_this_path(monkeypatch) -> None:
    holder = replace(player("Porteur", x=50.0, y=34.0, Balance=11), velocity=Vec2(5.0, 0.0))
    challenger = player("Adversaire", "away", x=50.5, y=34.0)
    ball = BallState(position=Vec2(50.0, 34.0), velocity=Vec2(0.0, 0.0), holder="Porteur")
    monkeypatch.setattr("v2engine.match.should_attempt_tackle", lambda aggression, dt: True)
    monkeypatch.setattr("v2engine.match.resolve_tackle", lambda tackler, h: _MissedTackle(foul=True))
    _step_ball(ball, 0.1, [holder, challenger], 3.0)
    assert holder.velocity.x == pytest.approx(5.0)

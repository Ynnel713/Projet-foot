"""Duel d'épaule à la course (ticket v2-realisme/11c) : deux adversaires au contact, côte à côte, courant vers le même
ballon libre ; Strength décide le gagnant, le perdant est décalé puis perd le contact (12c, Balance) ; faute de charge
possible (Aggression du gagnant)."""

from __future__ import annotations

from dataclasses import replace

import pytest

import v2engine.duel as duel
from v2engine.ball_state import BallState
from v2engine.duel import (SHOULDER_COOLDOWN_S, SHOULDER_FOUL_FACTOR, SHOULDER_PUSH_M, SHOULDER_PUSH_STEPS, foul_probability,
                           shoulder_contact, shoulder_foul_probability, shoulder_win_probability)
from v2engine.geometry import Vec2
from v2engine.match import _shoulder_duels
from v2engine.trace import DUEL_EPAULE, EventLog
from tests.scenes import Scene, player, run, seed_scene


def _runners(sa: int = 65, sb: int = 65, va: Vec2 = Vec2(6.0, 0.0), vb: Vec2 = Vec2(6.0, 0.0), dy: float = 0.8,
             dx: float = 0.0, team_b: str = "away"):
    a = replace(player("Rouge", "home", 60.0, 34.0 - dy / 2, "BU", Strength=sa, Aggression=50), velocity=va)
    b = replace(player("Bleu", team_b, 60.0 + dx, 34.0 + dy / 2, "DC", Strength=sb, Aggression=50), velocity=vb)
    return a, b


BALL = Vec2(72.0, 34.0)


def test_side_by_side_runners_toward_the_same_loose_ball_are_in_shoulder_contact() -> None:
    a, b = _runners()
    assert shoulder_contact(a, b, BALL) and shoulder_contact(b, a, BALL)


@pytest.mark.parametrize("case", ["coéquipiers", "un seul court", "l'un derrière l'autre", "trop loin",
                                  "courses divergentes", "ballon derrière", "ballon trop loin"])
def test_no_shoulder_contact_outside_the_trigger(case: str) -> None:
    ball = BALL
    if case == "coéquipiers":
        a, b = _runners(team_b="home")
    elif case == "un seul court":
        a, b = _runners(vb=Vec2(2.0, 0.0))
    elif case == "l'un derrière l'autre":
        a, b = _runners(dy=0.0, dx=0.8)  # axe des deux joueurs dans le sens de la course
    elif case == "trop loin":
        a, b = _runners(dy=1.0)  # rayons 0,3 + 0,3 + marge 0,3 = 0,9 m
    elif case == "courses divergentes":
        a, b = _runners(vb=Vec2(4.0, 4.6))  # 49° d'écart
    elif case == "ballon derrière":
        a, b = _runners()
        ball = Vec2(50.0, 34.0)
    else:
        a, b = _runners()
        ball = Vec2(81.0, 34.0)  # 21 m
    assert not shoulder_contact(a, b, ball)


def test_strength_decides_the_winner_on_the_shared_curve() -> None:
    a, b = _runners(65, 65)
    assert shoulder_win_probability(a, b) == pytest.approx(0.5)
    strong, weak = _runners(90, 40)
    assert shoulder_win_probability(strong, weak) > 0.75
    assert shoulder_win_probability(strong, weak) + shoulder_win_probability(weak, strong) == pytest.approx(1.0)
    ten_up, ten_down = _runners(80, 70)
    assert shoulder_win_probability(ten_up, ten_down) >= 0.58  # objectif du ticket 24 : 10 points, au moins 58 / 42


def test_charge_foul_is_a_fixed_share_of_the_tackle_foul() -> None:
    for aggression in (11, 62, 99):
        p = player("X", Aggression=aggression)
        assert shoulder_foul_probability(p) == pytest.approx(SHOULDER_FOUL_FACTOR * foul_probability(aggression))
    assert shoulder_foul_probability(player("X", Aggression=62)) == pytest.approx(0.045, abs=0.002)


def _ball() -> BallState:
    ball = BallState(position=BALL, velocity=Vec2(0.0, 0.0))
    ball.log = EventLog([])
    return ball


def test_the_loser_is_pushed_aside_unsettled_and_the_duel_is_logged() -> None:
    a, b = _runners(65, 65)
    ball = _ball()
    seed_scene(3)
    _shoulder_duels([a, b], ball, 10.0, [])
    [event] = [e for e in ball.log.events if e.kind == DUEL_EPAULE]
    winner, loser = (a, b) if event.player == a.name else (b, a)
    assert event.other == loser.name and event.detail == "égalité"
    start_y = 34.0 - 0.4 if loser is a else 34.0 + 0.4
    # décalage réparti sur les pas suivants (réserve A2) : jamais plus d'un tiers par pas, 0,5 m en tout
    side = 1.0 if loser.position.y > winner.position.y else -1.0
    steps = []
    for k in range(1, SHOULDER_PUSH_STEPS + 2):
        before = loser.position.y
        _shoulder_duels([a, b], ball, 10.0 + 0.1 * k, [])
        steps.append(loser.position.y - before)
    assert max(abs(d) for d in steps) <= SHOULDER_PUSH_M / SHOULDER_PUSH_STEPS + 1e-9 <= 0.25
    assert steps[-1] == 0.0  # fini après SHOULDER_PUSH_STEPS pas
    assert (loser.position.y - start_y) * side == pytest.approx(SHOULDER_PUSH_M, abs=1e-6)  # à l'opposé du gagnant
    assert ball.unsettled_until_s[loser.name] > 10.0  # contact perdu du 12c
    assert winner.name not in ball.unsettled_until_s
    assert loser.velocity.length() < 6.0 and winner.velocity.length() == pytest.approx(6.0)


def test_one_duel_per_pair_per_cooldown_and_none_on_a_held_ball() -> None:
    ball = _ball()
    seed_scene(3)
    for t in (10.0, 10.5):
        a, b = _runners(65, 65)
        _shoulder_duels([a, b], ball, t, [])
    assert sum(e.kind == DUEL_EPAULE for e in ball.log.events) == 1
    a, b = _runners(65, 65)
    ball.shoulder_push.clear()  # nouveaux coureurs au contact : seul le délai par paire est éprouvé ici
    _shoulder_duels([a, b], ball, 10.0 + SHOULDER_COOLDOWN_S, [])
    assert sum(e.kind == DUEL_EPAULE for e in ball.log.events) == 2
    held = _ball()
    held.holder = "Rouge"
    a, b = _runners(65, 65)
    _shoulder_duels([a, b], held, 10.0, [])
    assert not held.log.events


def test_a_foul_charge_is_whistled_for_the_loser_team(monkeypatch) -> None:
    monkeypatch.setattr(duel, "shoulder_foul_probability", lambda charger, in_own_box=False: 1.0)
    a, b = _runners(65, 65)
    ball, fouls = _ball(), []
    seed_scene(3)
    _shoulder_duels([a, b], ball, 10.0, fouls)
    [foul] = fouls
    [event] = [e for e in ball.log.events if e.kind == DUEL_EPAULE]
    assert event.detail.endswith(", faute") and foul.player == event.player and foul.victim == event.other
    assert ball.restart is not None and ball.restart.team == ("away" if foul.team == "home" else "home")


def _race(strength_red: int, strength_blue: int, seed: int) -> tuple[str | None, int]:
    """Deux joueurs lancés côte à côte vers un ballon arrêté à 12 m ; côtés alternés selon la graine."""
    a, b = _runners(strength_red, strength_blue, dy=0.8 if seed % 2 else -0.8)
    scene = Scene.full([a, b, player("Gardien", "away", 104.0, 34.0, "GK")], ball_at=BALL)
    scene.ball.log = EventLog([])
    seed_scene(seed)
    run(scene, 4.0, until=lambda s: s.ball.holder is not None)
    return scene.ball.holder, sum(e.kind == DUEL_EPAULE for e in scene.ball.log.events)


def test_the_stronger_runner_reaches_the_ball_more_often() -> None:
    """Scène A/B du ticket : Strength 90 contre 40, le plus fort atteint le ballon plus souvent (60 graines)."""
    equal = [_race(65, 65, s) for s in range(60)]
    strong = [_race(90, 40, s) for s in range(60)]
    assert all(duels >= 1 for _, duels in equal + strong)  # le duel a lieu dans chaque course
    red_equal = sum(holder == "Rouge" for holder, _ in equal)
    red_strong = sum(holder == "Rouge" for holder, _ in strong)
    assert 20 <= red_equal <= 40  # à force égale, environ une fois sur deux (27 / 60 le 15/11/2026)
    assert red_strong >= 48  # 54 / 60 le 15/11/2026
    assert [_race(90, 40, s) for s in range(4)] == strong[:4]  # déterministe à graine fixée


def test_a_foul_charge_during_an_advantage_keeps_both_fouls(monkeypatch) -> None:
    """Réserve A1 de l'expert : une faute laissée en avantage reste tracée quand une charge fautive est sifflée."""
    from v2engine.trace import FoulEvent
    monkeypatch.setattr(duel, "shoulder_foul_probability", lambda charger, in_own_box=False: 1.0)
    a, b = _runners(65, 65)
    ball, fouls = _ball(), []
    first = FoulEvent(0.15, "away", "Autre", "Rouge", 50.0, 34.0, "imprudente", "avantage")
    ball.advantage = (first, 12.0)
    seed_scene(3)
    _shoulder_duels([a, b], ball, 10.0, fouls)
    assert len(fouls) == 2 and fouls[0] is first and ball.advantage is None

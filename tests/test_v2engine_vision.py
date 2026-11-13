"""Champ de vision (ticket v2-realisme/08a) : ± 100° autour du cap ; ce qui est dans le dos n'est pas vu. Calculé et tracé
à chaque décision du porteur, sans effet sur le jeu."""

from __future__ import annotations

import math
from dataclasses import replace

import v2engine.match as match
from v2engine.ball_state import BallState
from v2engine.decision import Action
from v2engine.geometry import Vec2
from v2engine.match import _step_ball
from v2engine.trace import DecisionRecord
from v2engine.vision import FIELD_OF_VIEW_HALF_DEG, sees, unseen
from tests.scenes import player


def _facing_east(p):
    return replace(p, facing=Vec2(1.0, 0.0))


def test_field_of_view_is_100_degrees_each_side() -> None:
    assert FIELD_OF_VIEW_HALF_DEG == 100.0
    me = _facing_east(player("P", x=50.0, y=34.0))
    at = lambda deg: Vec2(50.0 + 10.0 * math.cos(math.radians(deg)), 34.0 + 10.0 * math.sin(math.radians(deg)))
    assert sees(me, at(0.0)) and sees(me, at(90.0)) and sees(me, at(-99.0))
    assert not sees(me, at(101.0)) and not sees(me, at(180.0)) and not sees(me, at(-150.0))
    assert sees(me, me.position)


def test_opponent_two_metres_behind_is_not_seen_ahead_is() -> None:
    me = _facing_east(player("P", x=50.0, y=34.0))
    behind, ahead = player("Dos", "away", x=48.0, y=34.0), player("Face", "away", x=52.0, y=34.0)
    far_behind = player("Loin", "away", x=30.0, y=34.0)
    assert [p.name for p in unseen(me, [me, behind, ahead, far_behind])] == ["Dos", "Loin"]
    assert [p.name for p in unseen(me, [me, behind, ahead, far_behind], within_m=5.0)] == ["Dos"]


def test_holder_decision_traces_what_he_does_not_see(monkeypatch) -> None:
    holder = _facing_east(player("P", x=50.0, y=34.0))
    players = [holder, player("Dos", "away", x=47.0, y=34.0), player("Face", "away", x=60.0, y=34.0),
               player("Loin", "away", x=30.0, y=30.0)]
    monkeypatch.setattr(match, "choose_action", lambda *args, **kwargs: Action("dribble", 1.0))
    monkeypatch.setattr(match, "dribble_lost", lambda *args, **kwargs: False)
    monkeypatch.setattr(match, "should_attempt_tackle", lambda *args, **kwargs: False)
    ball = BallState(position=holder.position, velocity=Vec2(0.0, 0.0), holder="P")
    decisions: list[DecisionRecord] = []
    _step_ball(ball, 0.1, players, 0.0, decisions=decisions)
    assert (decisions[0].unseen_opponents, decisions[0].unseen_near) == (2, 1)


def test_vision_draws_nothing_and_changes_no_state() -> None:
    """Sans effet sur le jeu : la visibilité est une lecture pure (ni tirage, ni mutation)."""
    import v2engine.flux as flux
    me = _facing_east(player("P", x=50.0, y=34.0))
    others = [player("A", "away", x=45.0, y=34.0)]
    before = [s.getstate() for s in (flux.PERCEPTION, flux.DECISION, flux.DUEL, flux.PASSE, flux.TIR)]
    unseen(me, others, 5.0)
    sees(me, others[0].position)
    assert before == [s.getstate() for s in (flux.PERCEPTION, flux.DECISION, flux.DUEL, flux.PASSE, flux.TIR)]
    assert me.facing == Vec2(1.0, 0.0) and others[0].position == Vec2(45.0, 34.0)

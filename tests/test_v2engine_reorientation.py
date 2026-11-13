"""Se réorienter avant une passe ou un tir, et la talonnade (ticket v2-realisme/07e) : hors du cône libre (± 90° pour
la passe, ± 60° pour le tir), le geste part après la rotation qui manque (Agility, 07f) ; la décision applique à la
valeur de l'option le risque de perdre le ballon pendant cette rotation, l'exécution le tire avec le même délai. La
talonnade part sans rotation vers un coéquipier dans le dos à 10 m au plus, plus difficile (Technique), et Flair règle
la chance d'y penser."""

from __future__ import annotations

import math
from dataclasses import replace

import pytest

import v2engine.decision as decision
import v2engine.match as match
from v2engine.ball_state import BallState
from v2engine.decision import (PASS_FREE_CONE_DEG, SHOT_FREE_CONE_DEG, Action, backheel_idea_probability,
                               evaluate_options, rotation_delay_s, rotation_keep_probability, with_rotation)
from v2engine.flux import DECISION
from v2engine.geometry import Vec2
from v2engine.match import _step_ball
from v2engine.movement import FACING_RUN_SPEED_MPS, desired_facing, step, turn_rate_rad_s
from v2engine.possession import BACKHEEL_MAX_M, pass_accuracy_probability, pass_success_probability
from tests.scenes import player

GOAL = Vec2(105.0, 34.0)


def _facing(p, direction: Vec2):
    return replace(p, facing=direction.normalized())


def test_cones_and_delay_follow_agility() -> None:
    assert PASS_FREE_CONE_DEG == 90.0 and SHOT_FREE_CONE_DEG == 60.0
    holder = _facing(player("P", x=50.0, y=34.0, Agility=55), Vec2(1.0, 0.0))
    assert rotation_delay_s(holder, Vec2(1.0, 0.5), PASS_FREE_CONE_DEG) == 0.0  # devant lui : immédiate
    assert rotation_delay_s(holder, Vec2(0.0, 1.0), PASS_FREE_CONE_DEG) == 0.0  # à son côté : immédiate
    assert rotation_delay_s(holder, Vec2(-1.0, 0.0), PASS_FREE_CONE_DEG) == pytest.approx(0.25)  # 90° / 360°/s
    assert rotation_delay_s(holder, Vec2(-1.0, 0.0), SHOT_FREE_CONE_DEG) == pytest.approx(120.0 / 360.0)
    agile = _facing(player("A", Agility=99), Vec2(1.0, 0.0))
    assert rotation_delay_s(agile, Vec2(-1.0, 0.0), PASS_FREE_CONE_DEG) == pytest.approx(
        math.radians(90.0) / turn_rate_rad_s(99))


def test_rotation_costs_value_only_under_pressure_and_only_with_a_delay() -> None:
    holder = player("P", x=50.0, y=34.0)
    assert rotation_keep_probability(holder, 1.0, 0.0) == 1.0
    assert with_rotation(0.05, holder, None, 1.0) == 0.05
    free, pressed = rotation_keep_probability(holder, 0.0, 0.25), rotation_keep_probability(holder, 1.0, 0.25)
    assert 1.0 > free > pressed
    assert with_rotation(0.05, holder, None, pressed) < with_rotation(0.05, holder, None, free) < 0.05


def test_decision_carries_the_delay_of_each_pass() -> None:
    holder = _facing(player("P", x=50.0, y=34.0, Flair=1), Vec2(1.0, 0.0))  # Flair minimal : pas de talonnade
    ahead, behind = player("Devant", x=62.0, y=34.0), player("Derriere", x=35.0, y=34.0)
    options = {o.target.name: o for o in evaluate_options(holder, [holder, ahead, behind], GOAL, None)
               if o.kind == "pass" and not o.backheel}
    assert options["Devant"].rotation_s == 0.0
    assert options["Derriere"].rotation_s == pytest.approx(rotation_delay_s(holder, behind.position - holder.position,
                                                                            PASS_FREE_CONE_DEG))
    assert options["Derriere"].rotation_s > 0.0


def _ball_with(monkeypatch, action: Action, holder, players):
    monkeypatch.setattr(match, "choose_action", lambda *args, **kwargs: action)
    return BallState(position=holder.position, velocity=Vec2(0.0, 0.0), holder=holder.name)


def test_pass_behind_leaves_after_the_rotation_ahead_leaves_at_once(monkeypatch) -> None:
    holder = _facing(player("P", x=50.0, y=34.0, Agility=55), Vec2(1.0, 0.0))
    behind, ahead = player("Derriere", x=35.0, y=34.0), player("Devant", x=65.0, y=34.0)
    players = [holder, behind, ahead]
    monkeypatch.setattr(match, "dribble_lost", lambda *args, **kwargs: False)
    # dans l'axe du corps : immédiate
    ball = _ball_with(monkeypatch, Action("pass", 1.0, ahead), holder, players)
    _step_ball(ball, 0.1, players, 0.0)
    assert ball.holder is None and ball.receiver == "Devant"
    # dans le dos : il garde le ballon et se retourne, la passe part au bout de 0,25 s
    turn = rotation_delay_s(holder, behind.position - holder.position, PASS_FREE_CONE_DEG)
    ball = _ball_with(monkeypatch, Action("pass", 1.0, behind, rotation_s=turn), holder, players)
    _step_ball(ball, 0.1, players, 0.0)
    assert ball.holder == "P" and ball.pending is not None and ball.next_decision_s == pytest.approx(turn)
    _step_ball(ball, 0.1, players, 0.2)
    assert ball.holder == "P"  # 0,2 s : encore en rotation
    _step_ball(ball, 0.1, players, 0.3)
    assert ball.holder is None and ball.receiver == "Derriere" and ball.pending is None


def test_execution_draws_the_loss_with_the_decision_delay(monkeypatch) -> None:
    holder = _facing(player("P", x=50.0, y=34.0), Vec2(1.0, 0.0))
    behind = player("Derriere", x=35.0, y=34.0)
    players = [holder, behind]
    durations = []

    def lost(h, rivals, duration_s=decision.DECISION_INTERVAL_S):
        durations.append(duration_s)
        return False
    monkeypatch.setattr(match, "dribble_lost", lost)
    ball = _ball_with(monkeypatch, Action("pass", 1.0, behind, rotation_s=0.25), holder, players)
    _step_ball(ball, 0.1, players, 0.0)
    _step_ball(ball, 0.1, players, 0.3)
    assert durations == [0.25]


def test_ball_lost_while_turning_goes_like_a_lost_carry(monkeypatch) -> None:
    holder = _facing(player("P", x=50.0, y=34.0), Vec2(1.0, 0.0))
    behind, rival = player("Derriere", x=35.0, y=34.0), player("R", "away", x=50.8, y=34.0)
    players = [holder, behind, rival]
    monkeypatch.setattr(match, "dribble_lost", lambda *args, **kwargs: True)
    monkeypatch.setattr(match, "should_attempt_tackle", lambda *args, **kwargs: False)
    monkeypatch.setattr(match, "lost_carry_outcome", lambda h, rivals, heading: (rivals[0], None))
    ball = _ball_with(monkeypatch, Action("pass", 1.0, behind, rotation_s=0.25), holder, players)
    _step_ball(ball, 0.1, players, 0.0)
    _step_ball(ball, 0.1, players, 0.3)
    assert ball.holder == "R" and ball.receiver is None


def test_pending_gesture_is_forgotten_when_someone_else_has_the_ball(monkeypatch) -> None:
    holder = _facing(player("P", x=50.0, y=34.0), Vec2(1.0, 0.0))
    behind, other = player("Derriere", x=35.0, y=34.0), player("Autre", x=70.0, y=34.0)
    players = [holder, behind, other]
    monkeypatch.setattr(match, "dribble_lost", lambda *args, **kwargs: False)
    ball = _ball_with(monkeypatch, Action("pass", 1.0, behind, rotation_s=0.25), holder, players)
    _step_ball(ball, 0.1, players, 0.0)
    ball.holder = "Autre"
    monkeypatch.setattr(match, "choose_action", lambda *args, **kwargs: Action("dribble", 1.0))
    _step_ball(ball, 0.1, players, 0.3)
    assert ball.pending is None and ball.holder == "Autre"


def test_free_kick_taker_does_not_turn(monkeypatch) -> None:
    holder = _facing(player("P", x=50.0, y=34.0), Vec2(1.0, 0.0))
    behind = player("Derriere", x=35.0, y=34.0)
    players = [holder, behind]
    ball = _ball_with(monkeypatch, Action("pass", 1.0, behind, rotation_s=0.25), holder, players)
    ball.set_piece = type("SP", (), {"taker": "P", "minute": 0.0, "kind": "coup franc", "team": "home",
                                     "spot": holder.position, "last_toucher": None})()
    _step_ball(ball, 0.1, players, 0.0)
    assert ball.holder is None and ball.receiver == "Derriere"


def test_backheel_needs_a_mate_behind_within_reach_and_the_idea() -> None:
    holder = _facing(player("P", x=50.0, y=34.0, Flair=99), Vec2(1.0, 0.0))
    near, far = player("Pres", x=50.0 - (BACKHEEL_MAX_M - 2.0), y=34.0), player("Loin", x=30.0, y=34.0)
    side = player("Cote", x=50.0, y=40.0)
    seen = set()
    DECISION.seed(20261113)  # tirage « il y pense » fixé (réserve A4 de l'expert)
    for _ in range(400):  # la talonnade n'est envisagée qu'à certaines décisions (Flair)
        for o in evaluate_options(holder, [holder, near, far, side], GOAL, None):
            if o.kind == "pass" and o.backheel:
                seen.add(o.target.name)
                assert o.rotation_s == 0.0
    assert seen == {"Pres"}


def test_flair_sets_how_often_he_thinks_of_it() -> None:
    assert backheel_idea_probability(player("A", Flair=99)) == pytest.approx(0.12)
    assert backheel_idea_probability(player("A", Flair=55)) == pytest.approx(0.06)
    assert backheel_idea_probability(player("A", Flair=11)) == pytest.approx(0.005)


def test_backheel_accuracy_reads_technique_not_passing() -> None:
    target = player("R", x=43.0, y=34.0)
    tech = _facing(player("P", x=50.0, y=34.0, Technique=90, Passing=20), Vec2(1.0, 0.0))
    plain = _facing(player("P", x=50.0, y=34.0, Technique=30, Passing=95), Vec2(1.0, 0.0))
    assert pass_accuracy_probability(tech, target, [], backheel=True) > pass_accuracy_probability(plain, target, [],
                                                                                                   backheel=True)
    # plus difficile que la même passe après rotation, à note égale
    same = _facing(player("P", x=50.0, y=34.0, Technique=60, Passing=60), Vec2(1.0, 0.0))
    assert pass_accuracy_probability(same, target, [], backheel=True) < pass_accuracy_probability(same, target, [])
    assert pass_success_probability(same, target, [], backheel=True) < pass_success_probability(same, target, [])


def test_pass_is_dropped_when_its_lane_closes_during_the_turn(monkeypatch) -> None:
    """Réserve A1 de l'expert : un adversaire entre dans la ligne pendant la rotation ; à l'échéance, la passe ne part
    pas, le porteur redécide (ici : il conduit)."""
    holder = _facing(player("P", x=50.0, y=34.0), Vec2(1.0, 0.0))
    behind = player("Derriere", x=35.0, y=34.0)
    players = [holder, behind]
    monkeypatch.setattr(match, "dribble_lost", lambda *args, **kwargs: False)
    monkeypatch.setattr(match, "should_attempt_tackle", lambda *args, **kwargs: False)
    ball = _ball_with(monkeypatch, Action("pass", 1.0, behind, rotation_s=0.25), holder, players)
    _step_ball(ball, 0.1, players, 0.0)
    assert ball.pending is not None and ball.pending[3] > 0.9  # ligne libre à la décision
    cutter = player("Coupeur", "away", x=42.0, y=34.0)  # sur la ligne, à mi-chemin
    players = players + [cutter]
    monkeypatch.setattr(match, "choose_action", lambda *args, **kwargs: Action("dribble", 1.0))
    _step_ball(ball, 0.1, players, 0.3)
    assert ball.holder == "P" and ball.receiver is None and ball.pending is None


def test_a_pass_already_risky_at_the_decision_still_leaves() -> None:
    holder = _facing(player("P", x=50.0, y=34.0), Vec2(1.0, 0.0))
    behind, cutter = player("Derriere", x=35.0, y=34.0), player("Coupeur", "away", x=42.0, y=34.0)
    chance = pass_success_probability(holder, behind, [cutter])
    assert chance < decision.OPEN_LANE_PROBABILITY
    assert not decision.lane_closed_during_turn(holder, behind, [cutter], False, chance)  # rien n'a changé : elle part
    assert decision.lane_closed_during_turn(holder, behind, [cutter], False, 0.95)  # fermée depuis la décision


def test_turning_holder_faces_his_gesture_even_running_fast() -> None:
    """Réserve A2 de l'expert : pendant la rotation, la direction du geste prime sur le sens de course."""
    fast = Vec2(FACING_RUN_SPEED_MPS + 1.5, 0.0)
    at, behind = Vec2(50.0, 34.0), Vec2(35.0, 34.0)
    assert desired_facing(at, fast, behind) == fast  # en course rapide, sans rotation : sens de course
    assert desired_facing(at, fast, behind, turning=True) == behind - at
    p = replace(player("P", x=50.0, y=34.0, Agility=55), velocity=fast, facing=Vec2(1.0, 0.0))
    for _ in range(3):  # 0,3 s : départ de la passe pleine arrière (délai 0,25 s)
        p = step(p, 0.1, p.position, 0.0, look_at=behind, turning=True)
    to_pass = math.degrees(math.atan2((behind - p.position).y, (behind - p.position).x))
    gap = abs((math.degrees(math.atan2(p.facing.y, p.facing.x)) - to_pass + 180.0) % 360.0 - 180.0)
    assert gap <= 90.0 + 1e-6  # le cône libre de la passe est atteint au départ

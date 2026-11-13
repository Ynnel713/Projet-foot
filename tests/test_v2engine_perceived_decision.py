"""Le porteur décide sur ce qu'il perçoit (ticket v2-realisme/08d) : tirs, passes et conduites jugés sur les positions perçues
des adversaires (mémoire de perception, 08b) ; la valeur RÉELLE (journal du meilleur choix) et l'exécution restent sur les
vraies positions."""

from __future__ import annotations

from dataclasses import replace

import pytest

import v2engine.decision as decision
import v2engine.flux as flux
import v2engine.match as match
from v2engine.ball_state import BallState
from v2engine.decision import Action, choose_action, evaluate_options
from v2engine.geometry import PITCH_LENGTH_M, Vec2
from v2engine.match import GOAL_CENTER_Y, _step_ball
from v2engine.perception_memory import PerceptionMemory
from v2engine.possession import pass_success_probability
from v2engine.trace import DecisionRecord
from tests.scenes import player

GOAL = Vec2(PITCH_LENGTH_M, GOAL_CENTER_Y)


def _scene():
    """Le porteur regarde vers l'est ; son coéquipier est derrière lui, à l'ouest ; un adversaire est sur la ligne de passe,
    dans son dos : il ne le voit pas."""
    holder = replace(player("H", x=60.0, y=34.0, Vision=99, Decisions=99), facing=Vec2(1.0, 0.0))
    mate = player("M", x=40.0, y=34.0)
    rival = replace(player("R", "away", x=50.0, y=34.0), velocity=Vec2(0.0, 0.0))
    return holder, mate, rival


def _pass(options):
    return next(o for o in options if o.kind == "pass")


def test_an_unseen_defender_on_the_lane_is_not_counted_so_the_pass_looks_safer_than_it_is() -> None:
    holder, mate, rival = _scene()
    believed = replace(rival, position=Vec2(50.0, 60.0))  # il le croit loin de la ligne de passe
    options = evaluate_options(holder, [holder, mate, rival], GOAL, None, seen_opponents=[believed])
    option = _pass(options)
    assert option.seen_value is not None and option.seen_value > option.value  # jugée plus sûre qu'elle ne l'est
    real = pass_success_probability(holder, mate, [rival])
    assert pass_success_probability(holder, mate, [believed]) > real  # la réussite réelle reste celle de l'exécution


def test_a_defender_he_sees_is_counted_where_he_really_is() -> None:
    holder, mate, rival = _scene()
    seen_there = replace(rival)  # perçu à sa vraie place
    option = _pass(evaluate_options(holder, [holder, mate, rival], GOAL, None, seen_opponents=[seen_there]))
    assert option.seen_value == pytest.approx(option.value)
    assert _pass(evaluate_options(holder, [holder, mate, rival], GOAL, None)).seen_value is None  # sans mémoire : perçu = réel


def test_the_real_value_is_the_same_whatever_he_perceives() -> None:
    holder, mate, rival = _scene()
    plain = evaluate_options(holder, [holder, mate, rival], GOAL, None)
    seen = evaluate_options(holder, [holder, mate, rival], GOAL, None,
                            seen_opponents=[replace(rival, position=Vec2(50.0, 60.0))])
    assert [(o.kind, o.value) for o in plain] == [(o.kind, o.value) for o in seen]


def test_the_perceived_evaluation_draws_nothing_more() -> None:
    holder, mate, rival = _scene()
    states = []
    for seen in (None, [replace(rival, position=Vec2(50.0, 60.0))]):
        flux.seed_streams(9)
        evaluate_options(holder, [holder, mate, rival], GOAL, None, planned="M", seen_opponents=seen)
        states.append([s.getstate() for s in (flux.DECISION, flux.PERCEPTION, flux.PASSE, flux.TIR)])
    assert states[0] == states[1]  # un seul passage pour les deux étages : aucun tirage de plus


def test_he_chooses_on_the_perceived_value_and_the_journal_keeps_the_real_one(monkeypatch) -> None:
    holder, mate, rival = _scene()
    real = decision.evaluate_options

    def rigged(*args, **kwargs):  # la passe vaut peu en réalité, beaucoup à ses yeux
        options = real(*args, **kwargs)
        return [replace(o, seen_value=50.0) if o.kind == "pass" else o for o in options]
    monkeypatch.setattr(decision, "evaluate_options", rigged)
    monkeypatch.setattr(flux.PERCEPTION, "gauss", lambda *a, **k: 0.0)
    chosen = choose_action(holder, [holder, mate, rival], GOAL, None, seen_opponents=[rival])
    assert chosen.kind == "pass"
    assert chosen.value < 1.0 and not chosen.best and chosen.gap > 0.0  # la valeur réelle perdue est tracée


def test_without_perceived_opponents_nothing_changes(monkeypatch) -> None:
    holder, mate, rival = _scene()
    monkeypatch.setattr(flux.PERCEPTION, "gauss", lambda *a, **k: 0.0)
    flux.seed_streams(4)
    plain = choose_action(holder, [holder, mate, rival], GOAL, None)
    flux.seed_streams(4)
    same = choose_action(holder, [holder, mate, rival], GOAL, None, seen_opponents=[replace(rival)])
    assert (plain.kind, plain.target, plain.point) == (same.kind, same.target, same.point)


def test_perceived_opponents_are_exact_when_seen_and_extrapolated_when_not() -> None:
    me = replace(player("Obs", x=50.0, y=34.0, Anticipation=55), facing=Vec2(1.0, 0.0))
    ahead = replace(player("Face", "away", x=60.0, y=34.0), velocity=Vec2(0.0, 3.0))
    behind = replace(player("Dos", "away", x=45.0, y=34.0), velocity=Vec2(0.0, 4.0))
    keeper = replace(player("GK", "away", x=95.0, y=34.0, poste="GK"), velocity=Vec2(0.0, 1.0))
    everyone = [me, ahead, behind, keeper]
    memory = PerceptionMemory(everyone, 0.0)
    memory.update(everyone, 0.0)
    moved = [me, replace(ahead, position=Vec2(60.0, 35.0)), replace(behind, position=Vec2(45.0, 38.0)),
             replace(keeper, position=Vec2(95.0, 35.0))]
    memory.update(moved, 1.0)
    result = {p.name: p for p in memory.perceived_opponents(me, moved[1:], 1.0, real="GK")}
    assert result["Face"].position == Vec2(60.0, 35.0)  # vu : exact
    assert result["GK"] is moved[3]  # gardé à sa vraie place
    assert result["Dos"].position.y == pytest.approx(34.0 + decision.anticipation_share(me) * 4.0 * 1.0)  # extrapolé
    assert result["Dos"].velocity == Vec2(0.0, 4.0) and result["Dos"].position.y < 38.0  # en retard sur la réalité


def test_the_match_gives_the_holder_his_perceived_world(monkeypatch) -> None:
    holder, mate, rival = _scene()
    keeper = replace(player("GK", "away", x=100.0, y=34.0, poste="GK"))
    players = [holder, mate, rival, keeper]
    memory = PerceptionMemory(players, 0.0)
    memory.update(players, 0.0)
    moved = [holder, mate, replace(rival, position=Vec2(50.0, 40.0)), keeper]
    memory.update(moved, 2.0)  # 2 s sans le voir courir de 6 m
    seen = {}

    def spy(*args, **kwargs):
        seen["opponents"] = args[-1] if len(args) > 7 else kwargs.get("seen_opponents")
        return Action("dribble", 1.0)
    monkeypatch.setattr(match, "choose_action", spy)
    monkeypatch.setattr(match, "dribble_lost", lambda *a, **k: False)
    monkeypatch.setattr(match, "should_attempt_tackle", lambda *a, **k: False)
    ball = BallState(position=holder.position, velocity=Vec2(0.0, 0.0), holder="H")
    _step_ball(ball, 0.1, moved, 2.0, decisions=[], memory=memory)
    by_name = {p.name: p for p in seen["opponents"]}
    assert by_name["R"].position != Vec2(50.0, 40.0) and by_name["R"].position.y < 40.0  # il le croit encore là où il l'a vu
    assert by_name["GK"] is keeper
    plain: dict = {}
    monkeypatch.setattr(match, "choose_action", lambda *a, **k: plain.setdefault("seen", k.get("seen_opponents", a[-1] if len(a) > 7 else None)) or Action("dribble", 1.0))
    _step_ball(BallState(position=holder.position, velocity=Vec2(0.0, 0.0), holder="H"), 0.1, moved, 2.0, decisions=[])
    assert plain["seen"] is None  # sans mémoire : il perçoit les vraies positions


def test_the_decision_traces_stale_ghosts(monkeypatch) -> None:
    holder, mate, rival = _scene()
    players = [holder, mate, rival]
    memory = PerceptionMemory(players, 0.0)
    memory.update(players, 0.0)
    moved = [holder, mate, replace(rival, position=Vec2(50.0, 60.0))]  # a couru 26 m pendant qu'on ne le voyait pas
    memory.update(moved, 5.0)
    monkeypatch.setattr(match, "choose_action", lambda *a, **k: Action("dribble", 1.0))
    monkeypatch.setattr(match, "dribble_lost", lambda *a, **k: False)
    monkeypatch.setattr(match, "should_attempt_tackle", lambda *a, **k: False)
    decisions: list[DecisionRecord] = []
    _step_ball(BallState(position=holder.position, velocity=Vec2(0.0, 0.0), holder="H"), 0.1, moved, 5.0,
               decisions=decisions, memory=memory)
    assert decisions[0].memory_age_s == pytest.approx(5.0) and decisions[0].memory_stale == 1

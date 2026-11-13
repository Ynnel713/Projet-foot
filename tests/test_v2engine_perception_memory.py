"""Mémoire de perception (ticket v2-realisme/08b) : dernière position et vitesse vues, extrapolées avec l'âge de la vue
selon l'Anticipation. Calculée et tracée à la décision du porteur et à la réception, sans effet sur le jeu."""

from __future__ import annotations

from dataclasses import replace

import pytest

import v2engine.match as match
import v2engine.flux as flux
from v2engine.ball_state import BallState
from v2engine.decision import Action, anticipation_share
from v2engine.geometry import Vec2
from v2engine.match import _step_ball
from v2engine.perception_memory import EXTRAPOLATION_HORIZON_S, MemoryReading, PerceptionMemory
from v2engine.trace import DecisionRecord
from v2engine.vision import seen_by, unseen
from tests.scenes import player

SPEED = 4.0  # m/s vers le nord


def _scene(anticipation: int = 55):
    """Observateur à l'est, adversaire à 10 m devant lui, qui court vers le nord à 4 m/s."""
    me = replace(player("Obs", x=50.0, y=34.0, Anticipation=anticipation), facing=Vec2(1.0, 0.0))
    rival = replace(player("Riv", "away", x=60.0, y=34.0), velocity=Vec2(0.0, SPEED))
    return me, rival


def _run_hidden(me, rival, seconds: float, tick: float = 0.1):
    """Vu au pas 0, puis l'observateur tourne le dos : le rival court `seconds` sans être revu."""
    memory = PerceptionMemory([me, rival], 0.0)
    memory.update([me, rival], 0.0)
    me = replace(me, facing=Vec2(-1.0, 0.0))
    t = 0.0
    while t < seconds - 1e-9:
        t += tick
        rival = replace(rival, position=rival.position + rival.velocity * tick)
        memory.update([me, rival], t)
    return memory, me, rival, t


def test_a_player_in_view_is_perceived_exactly() -> None:
    me, rival = _scene()
    memory = PerceptionMemory([me, rival], 0.0)
    rival = replace(rival, position=Vec2(60.0, 35.0))
    memory.update([me, rival], 0.1)
    assert memory.age_s("Obs", "Riv", 0.1) == 0.0
    assert memory.perceived_position(me, "Riv", 0.1) == Vec2(60.0, 35.0)
    assert memory.reading(me, [rival], 0.1) == MemoryReading()


def test_hidden_for_two_seconds_is_extrapolated_with_a_bounded_displacement() -> None:
    me, rival = _scene(anticipation=55)
    memory, me, rival, t = _run_hidden(me, rival, 2.0)
    assert memory.age_s("Obs", "Riv", t) == pytest.approx(2.0, abs=0.11)  # dernière vue : le pas où il était encore devant
    share = anticipation_share(me)
    perceived = memory.perceived_position(me, "Riv", t)
    last_seen_y = 34.0 + SPEED * (t - memory.age_s("Obs", "Riv", t))
    assert perceived.x == pytest.approx(60.0)
    assert perceived.y == pytest.approx(last_seen_y + share * SPEED * memory.age_s("Obs", "Riv", t))
    # déplacement extrapolé borné par l'horizon × sa vitesse ; erreur = ce que sa part ne rattrape pas
    assert perceived.distance_to(Vec2(60.0, last_seen_y)) <= EXTRAPOLATION_HORIZON_S * SPEED + 1e-9
    assert memory.error_m(me, rival, t) == pytest.approx((1.0 - share) * SPEED * memory.age_s("Obs", "Riv", t))


def test_extrapolation_stops_at_the_horizon() -> None:
    me, rival = _scene(anticipation=99)
    memory, me, rival, t = _run_hidden(me, rival, 5.0)
    at_horizon = memory.perceived_position(me, "Riv", t - memory.age_s("Obs", "Riv", t) + EXTRAPOLATION_HORIZON_S)
    assert memory.perceived_position(me, "Riv", t) == at_horizon  # figé au-delà de 2 s
    assert memory.error_m(me, rival, t) > 0.0  # l'erreur, elle, continue de croître tant qu'il n'est pas revu


def test_anticipation_sets_the_quality_of_the_extrapolation() -> None:
    errors = {}
    for note in (99, 55, 11):
        me, rival = _scene(anticipation=note)
        memory, me, rival, t = _run_hidden(me, rival, 2.0)
        errors[note] = memory.error_m(me, rival, t)
    assert errors[99] < errors[55] < errors[11]
    assert errors[99] == pytest.approx(0.0, abs=1e-6)  # course rectiligne, extrapolée en entier


def test_everyone_knows_everyone_at_kickoff_and_a_new_player_is_known_on_arrival() -> None:
    me = replace(player("Obs", x=50.0, y=34.0), facing=Vec2(-1.0, 0.0))
    rival = player("Riv", "away", x=60.0, y=34.0)  # dans son dos
    memory = PerceptionMemory([me, rival], 0.0)
    assert memory.age_s("Obs", "Riv", 0.0) == 0.0 and memory.perceived_position(me, "Riv", 0.0) == rival.position
    newcomer = player("New", "away", x=40.0, y=20.0)
    memory.update([me, rival, newcomer], 3.0)
    assert memory.perceived_position(me, "New", 3.0) == newcomer.position


def test_memory_refreshes_exactly_what_the_field_of_view_shows() -> None:
    me, rival = _scene()
    behind, aside = player("Dos", "away", x=45.0, y=34.0), player("Cote", "away", x=50.0, y=40.0)
    everyone = [me, rival, behind, aside]
    memory = PerceptionMemory(everyone, 0.0)
    moved = [me] + [replace(p, position=p.position + Vec2(1.0, 0.0)) for p in everyone[1:]]
    memory.update(moved, 1.0)
    others = moved[1:]
    fresh = {p.name for p in others if memory.age_s("Obs", p.name, 1.0) == 0.0}
    assert fresh == {p.name for p in seen_by(me, moved)}
    assert {p.name for p in others} - fresh == {p.name for p in unseen(me, moved)} == {"Dos"}


def test_memory_draws_nothing_and_changes_no_state() -> None:
    me, rival = _scene(anticipation=11)
    before = [s.getstate() for s in (flux.PERCEPTION, flux.DECISION, flux.DUEL, flux.PASSE, flux.TIR)]
    memory, me, rival, t = _run_hidden(me, rival, 2.0)
    memory.reading(me, [rival], t)
    assert before == [s.getstate() for s in (flux.PERCEPTION, flux.DECISION, flux.DUEL, flux.PASSE, flux.TIR)]
    assert rival.velocity == Vec2(0.0, SPEED) and me.facing == Vec2(-1.0, 0.0)


def test_reading_averages_only_players_not_in_view() -> None:
    me, rival = _scene(anticipation=11)
    memory, me, rival, t = _run_hidden(me, rival, 2.0)
    reading = memory.reading(me, [rival], t)
    assert reading.unseen == 1 and reading.age_mean_s == pytest.approx(memory.age_s("Obs", "Riv", t))
    assert reading.error_mean_m == reading.error_max_m == pytest.approx(memory.error_m(me, rival, t))
    assert memory.reading(me, [], t) == MemoryReading()


def test_holder_decision_traces_what_his_memory_holds(monkeypatch) -> None:
    holder = replace(player("P", x=50.0, y=34.0, Anticipation=11), facing=Vec2(1.0, 0.0))
    behind = replace(player("Dos", "away", x=47.0, y=34.0), velocity=Vec2(0.0, 5.0))
    players = [holder, behind, player("Face", "away", x=60.0, y=34.0)]
    memory = PerceptionMemory(players, 0.0)
    memory.update(players, 0.0)
    moved = [holder, replace(behind, position=Vec2(47.0, 36.0)), players[2]]
    memory.update(moved, 2.0)  # 2 s sans le voir : il a couru 10 m (en vrai : seulement 2 m ici)
    monkeypatch.setattr(match, "choose_action", lambda *args, **kwargs: Action("dribble", 1.0))
    monkeypatch.setattr(match, "dribble_lost", lambda *args, **kwargs: False)
    monkeypatch.setattr(match, "should_attempt_tackle", lambda *args, **kwargs: False)
    ball = BallState(position=holder.position, velocity=Vec2(0.0, 0.0), holder="P")
    decisions: list[DecisionRecord] = []
    _step_ball(ball, 0.1, moved, 2.0, decisions=decisions, memory=memory)
    record = decisions[0]
    assert record.unseen_opponents == 1 and record.memory_age_s == pytest.approx(2.0)
    assert record.memory_error_mean_m == record.memory_error_max_m > 0.0
    plain: list[DecisionRecord] = []
    _step_ball(BallState(position=holder.position, velocity=Vec2(0.0, 0.0), holder="P"), 0.1, moved, 2.0, decisions=plain)
    assert (plain[0].memory_age_s, plain[0].memory_error_max_m) == (0.0, 0.0)


def test_receiver_traces_his_memory_at_the_reception(monkeypatch) -> None:
    monkeypatch.setattr("v2engine.match.attempt_control", lambda *a, **k: True)
    receiver = replace(player("R", x=60.0, y=34.0, Anticipation=11), facing=Vec2(1.0, 0.0))
    rival = replace(player("Riv", "away", x=57.0, y=34.0), velocity=Vec2(0.0, 5.0))  # dans son dos
    players = [receiver, rival]
    memory = PerceptionMemory(players, 0.0)
    memory.update(players, 0.0)
    ball = BallState(position=Vec2(50.0, 34.0), velocity=Vec2(10.0, 0.0), receiver="R", last_pass_team="home",
                     pass_from=Vec2(50.0, 34.0))
    receptions: list = []
    for i in range(20):
        rival = replace(rival, position=rival.position + rival.velocity * 0.1)
        players = [receiver, rival]
        memory.update(players, (i + 1) * 0.1)
        _step_ball(ball, 0.1, players, (i + 1) * 0.1, receptions=receptions, memory=memory)
        if ball.holder is not None:
            break
    event = receptions[0]
    assert event.memory_age_s > 0.5 and event.memory_error_max_m > 0.0

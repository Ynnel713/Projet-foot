"""Tests du lot rendu V2 (US-29, docs/PLAN_V2.md Phase 4) : buts horodatés dans la trace et route
API `/api/v2/matches`."""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from api.routers.v2 import SimulateV2Request, create_match
from v2engine.trace import GoalEvent, MatchTrace


def test_record_goal_keeps_score_and_minute_of_each_goal() -> None:
    trace = MatchTrace(home="A", away="B", tick_seconds=1.0)
    trace.record_goal("home", 12.5)
    trace.record_goal("away", 80.0)
    assert (trace.home_goals, trace.away_goals) == (1, 1)
    assert trace.goals == [GoalEvent(minute=12.5, team="home"), GoalEvent(minute=80.0, team="away")]


def test_live_match_exposes_ticks_while_the_simulation_runs(monkeypatch) -> None:
    # Rejeu en direct : l'écran lit les images déjà calculées pendant que le calcul continue, puis le reste à la fin.
    import threading

    from api.routers import v2
    from v2engine.trace import BallSnapshot, PlayerSnapshot
    from v2engine.geometry import Vec2

    reached_two, may_finish = threading.Event(), threading.Event()

    def fake_simulate(home, away, **kwargs):
        trace = MatchTrace(home=home.name, away=away.name, tick_seconds=1.0)
        kwargs["on_start"](trace)
        for i in range(2):
            trace.record(float(i), [PlayerSnapshot("A", "home", "BU", Vec2(1.0, 2.0))], BallSnapshot(Vec2(1.0, 2.0), "A"))
        reached_two.set()
        may_finish.wait(5)
        trace.record_goal("home", 1.0)
        trace.record(2.0, [PlayerSnapshot("A", "home", "BU", Vec2(1.0, 2.0))], BallSnapshot(Vec2(1.0, 2.0)))
        return trace

    class _Club:
        def __init__(self, name):
            self.name = name

    monkeypatch.setattr(v2, "simulate_match", fake_simulate)
    monkeypatch.setattr(v2, "_find_club", lambda name: _Club(name))
    job_id = v2.start_match(SimulateV2Request(home="X", away="Y")).id
    assert reached_two.wait(5)

    partial = v2.match_progress(job_id, 0)
    assert not partial.done and len(partial.ticks) == 2 and partial.ticks[0].ball.holder == "A"
    assert partial.decisions == [] and partial.intentions == []

    may_finish.set()
    for _ in range(100):
        final = v2.match_progress(job_id, 2)
        if final.done:
            break
        threading.Event().wait(0.05)
    assert final.done and final.first_tick == 2 and len(final.ticks) == 1  # seulement les images nouvelles
    assert final.home_goals == 1 and final.ticks[0].ball.holder is None


def test_starting_a_new_live_match_cancels_the_previous_computation(monkeypatch) -> None:
    # Un seul écran : relancer un match arrête le calcul du précédent au lieu de les empiler (revue expert, réserve A2).
    import threading

    from api.routers import v2

    started = threading.Event()

    def endless_simulate(home, away, **kwargs):
        kwargs["on_start"](MatchTrace(home=home.name, away=away.name, tick_seconds=1.0))
        started.set()
        for i in range(10_000):
            kwargs["observer"](float(i), [], None, None)
            threading.Event().wait(0.01)
        raise AssertionError("calcul jamais annulé")

    class _Club:
        def __init__(self, name):
            self.name = name

    monkeypatch.setattr(v2, "simulate_match", endless_simulate)
    monkeypatch.setattr(v2, "_find_club", lambda name: _Club(name))
    first = v2.start_match(SimulateV2Request(home="X", away="Y")).id
    assert started.wait(5)
    v2.start_match(SimulateV2Request(home="X", away="Y"))
    for _ in range(100):
        progress = v2.match_progress(first, 0)
        if progress.done:
            break
        threading.Event().wait(0.05)
    assert progress.done and progress.error == "annulé"


def test_v2_match_route_rejects_unknown_club() -> None:
    with pytest.raises(HTTPException) as error:
        create_match(SimulateV2Request(home="Club inexistant", away="Autre inexistant"))
    assert error.value.status_code == 404


def test_numbered_lineup_keeper_first_then_bench_from_12() -> None:
    # Feuille de match V2 : gardien 1, onze numérotés 1 à 11, au plus 9 remplaçants dont un gardien, à partir de 12.
    from api.routers.v2 import numbered_lineup
    from ligue1sim.clubs import Club
    from ligue1sim.players import Player

    postes = ["GK"] * 3 + ["DC"] * 5 + ["LB", "RB"] * 2 + ["MC"] * 5 + ["MDC", "MOC"] * 2 + ["AG", "AD", "BU"] * 2
    players = [Player(prenom=f"p{i}", nom="", nationalite="France", age=25, poste=poste, note=60.0 + i % 7, club="T",
                      championnat="TEST") for i, poste in enumerate(postes)]
    lineup = numbered_lineup(Club(name="T", players=players))
    assert [p.number for p in lineup.starters] == list(range(1, 12))
    assert lineup.starters[0].poste == "GK"
    assert len(lineup.bench) == 9 and [p.number for p in lineup.bench] == list(range(12, 21))
    assert sum(p.poste == "GK" for p in lineup.bench) == 1
    assert not {p.name for p in lineup.bench} & {p.name for p in lineup.starters}


def test_lineup_route_rejects_unknown_club() -> None:
    from api.routers.v2 import club_lineup

    with pytest.raises(HTTPException) as error:
        club_lineup("Club inexistant")
    assert error.value.status_code == 404

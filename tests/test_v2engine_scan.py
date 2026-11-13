"""Scan visuel (ticket v2-realisme/08c) : un tour de tête rafraîchit la mémoire de perception de ce que le cône ne montre
pas. Fréquence réglée par Vision, réduite par la gêne et la vitesse, et par la tête basse du porteur (Dribbling et
Technique cumulés). Calculé et tracé, sans effet sur le jeu."""

from __future__ import annotations

from dataclasses import replace

import pytest

import v2engine.flux as flux
from v2engine.flux import seed_streams
from v2engine.geometry import Vec2
from v2engine.match import simulate_match
from v2engine.perception_memory import PerceptionMemory
from v2engine.scan import (DRIBBLING_PART, PRESSURE_PENALTY, SCAN_DURATION_S, SPEED_PENALTY, TECHNIQUE_PART, ScanTracker,
                           head_up_share, scan_rate_per_s)
from v2engine.trace import ScanEvent
from ligue1sim.clubs import load_clubs
from ligue1sim.season import CLUBS_PATH
from tests.scenes import player

FAR = player("Loin", "away", x=95.0, y=60.0)  # adversaire hors de la gêne (plus de 5 m)


def _rate(**attributes) -> float:
    me = player("P", x=50.0, y=34.0, **attributes)
    return scan_rate_per_s(me, [FAR], False)


def test_vision_sets_the_base_rate() -> None:
    assert _rate(Vision=99) == pytest.approx(0.6)  # Lampard 0,62, Gerrard 0,61 scan/s (Jordet 2013)
    assert _rate(Vision=55) == pytest.approx(0.3)  # environ 3 scans en 10 s (Jordet et al. 2020)
    assert _rate(Vision=11) == pytest.approx(0.1)
    assert _rate(Vision=99) > _rate(Vision=75) > _rate(Vision=55) > _rate(Vision=30) > _rate(Vision=11)


def test_pressure_halves_the_rate_at_most() -> None:
    me = player("P", x=50.0, y=34.0, Vision=55)
    free = scan_rate_per_s(me, [FAR], False)
    at_contact = scan_rate_per_s(me, [player("Col", "away", x=50.0, y=34.0)], False)
    half = scan_rate_per_s(me, [player("Moitie", "away", x=52.5, y=34.0)], False)  # 2,5 m : gêne 0,5
    assert at_contact == pytest.approx(free * (1.0 - PRESSURE_PENALTY))
    assert half == pytest.approx(free * (1.0 - PRESSURE_PENALTY * 0.5))
    assert scan_rate_per_s(me, [], False) == pytest.approx(free)


def test_speed_lowers_the_rate() -> None:
    me = player("P", x=50.0, y=34.0, Vision=55, Pace=60)
    from v2engine.movement import max_speed_mps
    still = scan_rate_per_s(me, [FAR], False)
    flat_out = scan_rate_per_s(replace(me, velocity=Vec2(max_speed_mps(60), 0.0)), [FAR], False)
    assert flat_out == pytest.approx(still * (1.0 - SPEED_PENALTY))
    assert scan_rate_per_s(replace(me, velocity=Vec2(5.0, 0.0)), [FAR], False) < still


def test_the_carrier_keeps_his_head_up_by_dribbling_and_technique() -> None:
    assert (DRIBBLING_PART, TECHNIQUE_PART) == (0.6, 0.4)
    assert head_up_share(player("P", Dribbling=99, Technique=99)) == pytest.approx(1.0)
    assert head_up_share(player("P", Dribbling=55, Technique=55)) == pytest.approx(0.6)
    assert head_up_share(player("P", Dribbling=11, Technique=11)) == pytest.approx(0.25)
    # cumul : 0,6 Dribbling + 0,4 Technique, un peu de chacun ; le Dribbling pèse plus que la Technique
    assert head_up_share(player("P", Dribbling=99, Technique=11)) > head_up_share(player("P", Dribbling=11, Technique=99))
    assert 0.25 < head_up_share(player("P", Dribbling=99, Technique=11)) < 1.0
    me = player("P", Vision=55, Dribbling=11, Technique=11)
    assert scan_rate_per_s(me, [FAR], True) == pytest.approx(scan_rate_per_s(me, [FAR], False) * 0.25)


def test_a_scan_shows_what_is_in_the_back_and_is_traced() -> None:
    me = replace(player("Obs", x=50.0, y=34.0), facing=Vec2(1.0, 0.0))
    behind = replace(player("Dos", "away", x=45.0, y=34.0), velocity=Vec2(0.0, 4.0))
    players = [me, behind]
    memory = PerceptionMemory(players, 0.0)
    moved = [me, replace(behind, position=Vec2(45.0, 38.0))]
    memory.update(moved, 1.0)
    assert memory.age_s("Obs", "Dos", 1.0) == pytest.approx(1.0)  # dans son dos : pas vu au cône
    memory.update(moved, 1.1, scanning={"Obs"})
    assert memory.age_s("Obs", "Dos", 1.1) == 0.0 and memory.perceived_position(me, "Dos", 1.1) == Vec2(45.0, 38.0)


def test_a_scan_lasts_a_fixed_short_time_and_starts_at_the_rate(monkeypatch) -> None:
    me = player("P", x=50.0, y=34.0, Vision=99)
    tracker, events = ScanTracker(), []
    monkeypatch.setattr(flux.REGARD, "random", lambda: 0.0)  # tout tirage déclenche
    assert tracker.update([me], None, 0.0, 0.1, events) == {"P"}
    monkeypatch.setattr(flux.REGARD, "random", lambda: 1.0)  # plus rien ne déclenche
    seen = [tracker.update([me], None, 0.1 * k, 0.1) == {"P"} for k in range(1, 5)]
    assert seen == [True, True, False, False]  # 0,3 s : trois pas au total, le premier compris
    assert SCAN_DURATION_S == 0.3
    assert events == [ScanEvent(0.0, "home", "P", False)]


def test_vision_99_scans_much_more_than_vision_11() -> None:
    counts = {}
    for note in (99, 11):
        seed_streams(5)
        me = player("P", x=50.0, y=34.0, Vision=note)
        tracker, events = ScanTracker(), []
        for k in range(6000):  # 10 min
            tracker.update([me, FAR], None, k * 0.1, 0.1, events)
        counts[note] = sum(1 for e in events if e.player == "P") / 10.0  # par minute
    assert counts[99] == pytest.approx(0.6 * 60.0 / (1.0 + 0.6 * SCAN_DURATION_S), rel=0.15)  # 36/min, moins le temps du scan
    assert counts[11] == pytest.approx(0.1 * 60.0 / (1.0 + 0.1 * SCAN_DURATION_S), rel=0.25)
    assert counts[99] > 4.0 * counts[11]


def test_scans_draw_only_from_their_own_stream() -> None:
    seed_streams(3)
    others = (flux.PERCEPTION, flux.DECISION, flux.DUEL, flux.PASSE, flux.TIR, flux.PLACEMENT, flux.DEFENSE, flux.ARBITRAGE)
    before = [s.getstate() for s in others]
    me = player("P", x=50.0, y=34.0)
    tracker = ScanTracker()
    for k in range(100):
        tracker.update([me, FAR], None, k * 0.1, 0.1, [])
    assert before == [s.getstate() for s in others]
    assert flux.REGARD.getstate() != flux.REGARD.__class__(0).getstate()


def test_same_seed_gives_the_same_scans() -> None:
    def run():
        seed_streams(11)
        me, tracker, events = player("P", x=50.0, y=34.0, Vision=70), ScanTracker(), []
        for k in range(600):
            tracker.update([me, FAR], None, k * 0.1, 0.1, events)
        return events
    assert run() == run() and len(run()) > 0


def test_a_simulated_match_traces_scans_and_the_memory_they_refresh_feeds_the_decision(monkeypatch) -> None:
    """Depuis le ticket 08d, la mémoire que les scans rafraîchissent nourrit la décision du porteur : sans aucun scan,
    il juge sur des positions plus vieilles et ne joue plus pareil (au 08c, ce test affirmait le contraire)."""
    clubs = load_clubs(CLUBS_PATH, "Ligue 1")
    outcomes = []
    for scanning in (True, False):
        if not scanning:  # contre-épreuve : plus aucun scan ne démarre
            monkeypatch.setattr("v2engine.flux.REGARD.random", lambda: 1.0)
        import random
        random.seed(20260923)
        trace = simulate_match(clubs[0], clubs[1], duration_minutes=3.0)
        outcomes.append(trace)
    with_scans, without = outcomes
    assert len(with_scans.scans) > 0 and len(without.scans) == 0
    assert {s.team for s in with_scans.scans} == {"home", "away"} and any(s.has_ball for s in with_scans.scans)
    assert len(with_scans.decisions) > 0 and len(without.decisions) > 0
    # sans scan, la mémoire du porteur vieillit davantage
    unseen_age = lambda t: [d.memory_age_s for d in t.decisions if d.unseen_opponents > 0]
    assert sum(unseen_age(without)) / len(unseen_age(without)) > sum(unseen_age(with_scans)) / len(unseen_age(with_scans))

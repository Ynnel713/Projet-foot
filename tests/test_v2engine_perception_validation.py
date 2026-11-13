"""Validation de la perception (ticket v2-realisme/08f) : indicateurs de mesure seulement, sans effet sur le jeu.
Adversaires proches (5 m au plus) à la décision, perte de balle au contact (tacle, conduite, rotation) sur un adversaire
que le porteur voyait ou non, scans par minute et par poste, déterminisme à graine fixée."""

from __future__ import annotations

import random
from dataclasses import replace
from types import SimpleNamespace

import pytest

import v2engine.match as match
from scripts import v2_indicators as ind
from scripts.measure_v2 import report
from v2engine.ball_state import BallState
from v2engine.decision import Action
from v2engine.geometry import Vec2
from v2engine.match import _step_ball
from v2engine.perception_memory import PerceptionMemory
from v2engine.trace import PERTE, DecisionRecord, EventLog, ScanEvent, TraceEvent
from tests.scenes import player


def _east(p):
    return replace(p, facing=Vec2(1.0, 0.0))


def _memory(players, scanning=(), now_s=1.0):
    """Mémoire à l'instant `now_s` : tous connus au coup d'envoi (0 s), puis chacun voit ce que son cône ou son scan montre."""
    memory = PerceptionMemory(players, 0.0)
    memory.update(players, now_s, scanning)
    return memory


def test_is_seen_follows_the_field_of_view_and_the_scan() -> None:
    me = _east(player("P", x=50.0, y=34.0))
    ahead, behind = player("Face", "away", x=55.0, y=34.0), player("Dos", "away", x=47.0, y=34.0)
    players = [me, ahead, behind]
    seen = _memory(players)
    assert seen.is_seen("P", "Face", 1.0) and not seen.is_seen("P", "Dos", 1.0)
    assert _memory(players, scanning={"P"}).is_seen("P", "Dos", 1.0)  # le tour de tête montre le dos
    assert not seen.is_seen("P", "Face", 2.0)  # sans mise à jour, la vue vieillit


def test_decision_traces_the_opponents_within_five_metres_seen_or_not(monkeypatch) -> None:
    holder = _east(player("P", x=50.0, y=34.0))
    players = [holder, player("Dos", "away", x=47.0, y=34.0), player("Face", "away", x=53.0, y=34.0),
               player("Loin", "away", x=30.0, y=30.0)]
    monkeypatch.setattr(match, "choose_action", lambda *args, **kwargs: Action("dribble", 1.0))
    monkeypatch.setattr(match, "dribble_lost", lambda *args, **kwargs: False)
    monkeypatch.setattr(match, "should_attempt_tackle", lambda *args, **kwargs: False)
    ball = BallState(position=holder.position, velocity=Vec2(0.0, 0.0), holder="P")
    decisions: list[DecisionRecord] = []
    _step_ball(ball, 0.1, players, 0.0, decisions=decisions)
    record = decisions[0]
    assert record.near_opponents == 2  # Dos (3 m) et Face (3 m) ; Loin est à plus de 5 m
    assert record.unseen_near == 1 and record.unseen_opponents == 2


def _tackle_scene(monkeypatch, tackler_x: float):
    """Le porteur regarde vers l'est ; le tacleur gagne son duel, devant (x > 50) ou dans son dos (x < 50)."""
    holder = _east(player("P", x=50.0, y=34.0))
    tackler = player("T", "away", x=tackler_x, y=34.0)
    players = [holder, tackler]
    monkeypatch.setattr(match, "should_attempt_tackle", lambda *args, **kwargs: True)
    monkeypatch.setattr(match, "resolve_tackle", lambda challenger, carrier: SimpleNamespace(won=True, foul=False))
    ball = BallState(position=holder.position, velocity=Vec2(0.0, 0.0), holder="P")
    ball.log = EventLog([])
    return ball, players


@pytest.mark.parametrize("tackler_x, seen", [(51.0, True), (49.0, False)])
def test_a_won_tackle_records_whether_the_holder_saw_the_tackler(monkeypatch, tackler_x, seen) -> None:
    ball, players = _tackle_scene(monkeypatch, tackler_x)
    _step_ball(ball, 0.1, players, 1.0, memory=_memory(players))
    loss = next(e for e in ball.log.events if e.kind == PERTE)
    assert (loss.detail, loss.player, loss.other, loss.seen) == ("tacle", "P", "T", seen)


def test_a_scan_makes_the_tackler_behind_a_seen_one(monkeypatch) -> None:
    ball, players = _tackle_scene(monkeypatch, 49.0)
    _step_ball(ball, 0.1, players, 1.0, memory=_memory(players, scanning={"P"}))
    assert next(e for e in ball.log.events if e.kind == PERTE).seen is True


def test_without_memory_the_loss_is_not_judged(monkeypatch) -> None:
    ball, players = _tackle_scene(monkeypatch, 49.0)
    _step_ball(ball, 0.1, players, 0.0)
    assert next(e for e in ball.log.events if e.kind == PERTE).seen is None


@pytest.mark.parametrize("kind, detail", [("dribble", "conduite"), ("pass", "rotation")])
def test_a_ball_lost_on_the_move_records_the_taker_seen_or_not(monkeypatch, kind, detail) -> None:
    holder = _east(player("P", x=50.0, y=34.0))
    taker = player("T", "away", x=48.0, y=34.0)  # dans son dos
    players = [holder, taker]
    action = Action(kind, 1.0, target=player("M", x=60.0, y=34.0)) if kind == "pass" else Action(kind, 1.0)
    monkeypatch.setattr(match, "lost_carry_outcome", lambda *args, **kwargs: (taker, Vec2(0.0, 0.0)))
    monkeypatch.setattr(match, "should_attempt_tackle", lambda *args, **kwargs: False)
    ball = BallState(position=holder.position, velocity=Vec2(0.0, 0.0), holder="P")
    ball.log = EventLog([])
    match._execute(ball, holder, action, players, [taker], Vec2(105.0, 34.0), None, 1.0, False, None, None,
                   lost=True, memory=_memory(players))
    loss = next(e for e in ball.log.events if e.kind == PERTE)
    assert (loss.detail, loss.other, loss.seen) == (detail, "T", False)


def test_a_pass_intercepted_is_not_a_contact_loss() -> None:
    """Seules les pertes au contact sont jugées : une passe coupée reste sans verdict (`seen` vide)."""
    log = EventLog([])
    log.add(1.0, PERTE, "home", "P", "passe interceptée", "T")
    assert log.events[0].seen is None


def test_collector_counts_contact_losses_on_an_unseen_opponent() -> None:
    c = ind.Collector()
    c.matches = 2
    events = [TraceEvent(0, 1.0, PERTE, "home", "P", None, "tacle", "T", True),
              TraceEvent(1, 2.0, PERTE, "home", "P", None, "tacle", "T", False),
              TraceEvent(2, 3.0, PERTE, "away", "Q", None, "conduite", "U", False),
              TraceEvent(3, 4.0, PERTE, "away", "Q", None, "passe interceptée", "U"),  # hors périmètre
              TraceEvent(4, 5.0, PERTE, "home", "P", None, "rotation", "T", True)]
    c.on_events(events)
    out = report(c)
    assert out["pertes de balle au contact par match (tacle, conduite, rotation)"] == 2.0
    assert out["pertes au contact sur adversaire non vu (part des pertes au contact)"] == 0.5
    assert out["pertes au contact : tacle, par match"] == 1.0
    assert out["pertes au contact : tacle, sur adversaire non vu (part)"] == 0.5
    assert out["pertes au contact : conduite, sur adversaire non vu (part)"] == 1.0
    assert out["pertes au contact : rotation, sur adversaire non vu (part)"] == 0.0


def test_collector_gives_the_share_of_near_opponents_not_seen() -> None:
    c = ind.Collector()
    records = [DecisionRecord(1.0, "P", "home", "pass", None, 3, True, unseen_opponents=3, unseen_near=1, near_opponents=2),
               DecisionRecord(2.0, "P", "home", "dribble", None, 1, True, unseen_opponents=0, unseen_near=0, near_opponents=2)]
    c.on_decisions(records)
    out = report(c)
    assert out["vision : adversaires à 5 m au plus par décision (moyenne)"] == 2.0
    assert out["vision : adversaires à 5 m au plus non vus à la décision (part des adversaires proches)"] == 0.25


def test_collector_gives_scans_per_minute_and_per_poste() -> None:
    c = ind.Collector()
    c.poste = {"Milieu": "MC", "Defenseur": "DC"}
    c.count["temps sur le terrain (s) : MC"] = 120.0  # deux minutes de milieu
    c.count["temps sur le terrain (s) : DC"] = 600.0  # dix minutes de défenseur
    scans = [ScanEvent(0.5, "home", "Milieu", True), ScanEvent(1.0, "home", "Milieu", False),
             ScanEvent(1.5, "home", "Milieu", False), ScanEvent(2.0, "home", "Milieu", False),
             ScanEvent(2.5, "home", "Defenseur", False)]
    c.on_scans(scans, [])
    out = report(c)
    assert out["scans par minute et par joueur : MC"] == pytest.approx(2.0)
    assert out["scans par minute et par joueur : DC"] == pytest.approx(0.1)
    assert out["scans par minute et par joueur (temps réellement sur le terrain, temps additionnel compris)"] == pytest.approx(5 / 12.0)


def test_collector_time_on_pitch_is_counted_per_poste() -> None:
    c = ind.Collector()
    players = [replace(player("A", x=50.0, y=30.0), poste="MC"), replace(player("B", x=50.0, y=40.0), poste="GK")]
    c._speeds(players, 1.0, 0.1)
    c._speeds(players, 1.0, 0.1)
    assert c.count["temps sur le terrain (s) : MC"] == pytest.approx(0.2)
    assert c.count["temps sur le terrain (s) : GK"] == pytest.approx(0.2)  # le gardien scanne aussi


def test_indicators_are_reproducible_for_a_fixed_seed() -> None:
    """Deux exécutions à graine fixée : mêmes valeurs (la mesure ne tire rien)."""
    from scripts.measure_v2 import run
    keys = ("vision : adversaires à 5 m au plus non vus à la décision (part des adversaires proches)",
            "pertes au contact sur adversaire non vu (part des pertes au contact)", "scans par minute et par joueur : MC")
    outs = []
    for _ in range(2):
        random.seed(20260923)
        out = report(run(1, duration_minutes=2.0))
        outs.append({k: out[k] for k in keys if k in out})
    assert outs[0] == outs[1] and outs[0]

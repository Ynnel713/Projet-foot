"""Diagnostic du volume de tacles (ticket v2-realisme/11r) : lecture seule (le match est identique avec ou sans
l'instrumentation, le moteur est rétabli), confrontations et leur issue, contextes des tirages, déterminisme."""

from __future__ import annotations

import math
import random
from types import SimpleNamespace

from ligue1sim.clubs import load_clubs
from ligue1sim.season import CLUBS_PATH

import v2engine.match as match
from scripts import diagnostic_tacles as d
from v2engine.geometry import Vec2


def _player(name: str, team: str, x: float, y: float = 34.0):
    return SimpleNamespace(name=name, team=team, position=Vec2(x, y), facing=Vec2(1.0, 0.0))


def _ball(holder: str | None, restart=None):
    return SimpleNamespace(holder=holder, restart=restart, offside_out_until={}, unsettled_until_s={},
                           tackle_ban_until_s={}, engaged=set())


def _fingerprint(trace) -> tuple:
    return (trace.home_goals, trace.away_goals, len(trace.events), len(trace.fouls), len(trace.decisions),
            [(e.minute, e.kind, e.team) for e in trace.events][-20:])


def test_the_match_is_unchanged_by_the_instrumentation_and_the_engine_is_restored() -> None:
    clubs = load_clubs(CLUBS_PATH, "Ligue 1")
    real = (match.tackle_attempt_factor, match.should_attempt_tackle)
    random.seed(d.AUDIT_SEED)
    plain = match.simulate_match(clubs[0], clubs[1], duration_minutes=3.0)
    diag = d.TackleDiagnostic()
    restore = d.hooked(diag)
    try:
        random.seed(d.AUDIT_SEED)
        observed = match.simulate_match(clubs[0], clubs[1], duration_minutes=3.0,
                                        observer=lambda now, players, ball, scoring: diag.on_tick(now, players, ball, 0.1))
    finally:
        restore()
    assert (match.tackle_attempt_factor, match.should_attempt_tackle) == real
    assert _fingerprint(observed) == _fingerprint(plain)
    assert diag.count["ballon tenu (s)"] > 0.0


def test_a_confrontation_is_closed_by_separation_by_a_pass_and_by_a_tackle() -> None:
    diag = d.TackleDiagnostic()
    holder, defender = _player("A", "home", 50.0), _player("D", "away", 51.0)
    diag.on_tick(0.0, [holder, defender], _ball("A"), 0.1)  # à 1 m : confrontation ouverte
    diag.on_tick(0.5, [holder, _player("D", "away", 53.0)], _ball("A"), 0.1)  # à 3 m : séparation
    assert diag.count["confrontations, issue : séparation"] == 1 and diag.durations == [0.5]
    diag.on_tick(1.0, [holder, defender], _ball("A"), 0.1)
    diag.on_tick(1.2, [holder, defender], _ball(None), 0.1)  # passe : ballon libre
    assert diag.count["confrontations, issue : porteur joue ou perd le ballon"] == 1
    diag.on_tick(2.0, [holder, defender], _ball("A"), 0.1)
    diag.on_context(defender, holder, False, False, 0.5)
    diag.on_draw(62.0, 0.05, True)
    diag.on_tick(2.1, [holder, defender], _ball("A"), 0.1)  # tacle tenté : close, pas rouverte tant qu'il reste à portée
    diag.on_tick(2.2, [holder, defender], _ball("A"), 0.1)
    assert diag.count["confrontations, issue : tacle tenté"] == 1 and not diag.open
    assert diag.count["exposition, 1 à portée (s)"] > 0.0


def test_a_draw_is_counted_in_its_context_at_its_base_rate() -> None:
    diag = d.TackleDiagnostic()
    holder, defender = _player("A", "home", 50.0), _player("D", "away", 49.0)  # derrière le porteur tourné vers +x
    diag.on_context(defender, holder, False, False, 0.25)
    diag.on_draw(62.0, 0.1 * 0.25, False)
    assert diag.count["tirages, hors urgence, par derrière (s)"] == 0.1
    assert diag.count["tirages, hors urgence, par derrière : facteur x s"] == 0.025
    diag.on_context(defender, holder, True, True, 0.4)  # dans sa surface : jamais l'urgence
    diag.on_draw(62.0, 0.04, False)
    assert math.isclose(diag.count["tirages, dans sa surface (s)"], 0.1)
    diag.on_draw(62.0, 0.1, True)  # tirage sans contexte (hors moteur) : ignoré
    assert sum(v for key, v in diag.count.items() if key.endswith("tacles tentés")) == 0


def test_duration_bands_cover_every_duration() -> None:
    assert d.duration_band(0.0) == "moins de 0,3 s"
    assert d.duration_band(0.3) == "0,3 à 1 s"
    assert d.duration_band(2.99) == "1 à 3 s"
    assert d.duration_band(90.0) == "3 s et plus"


def test_two_runs_give_the_same_report() -> None:
    assert d.report(d.run(1, 0, 2.0)) == d.report(d.run(1, 0, 2.0))

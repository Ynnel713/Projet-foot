"""Indicateurs du ballon libre (ticket v2-realisme/11k, réserve A1 du 11g) : stabilité du chasseur désigné et issue des
ballons libres disputés. Le banc observe sans changer le jeu."""

from __future__ import annotations

from types import SimpleNamespace

import scripts.v2_indicators as ind
from scripts.measure_v2 import free_ball_report
from v2engine.cerveau import BALLON_LIBRE, REPLACEMENT
from tests.scenes import player

A, B, C = player("A", "home"), player("B", "home"), player("X", "away")


def _collector() -> ind.Collector:
    c = ind.Collector(geometry_every_s=1e9)
    c.team_of = {"A": "home", "B": "home", "X": "away"}
    c.team = "home"  # l'équipe qui avait le ballon
    return c


def _tick(c: ind.Collector, now: float, chasers: list, holder: str | None = None, restart=None) -> None:
    c.now = now
    for p in (A, B, C):
        c.on_free_ball_role(p, SimpleNamespace(role=BALLON_LIBRE if p in chasers else REPLACEMENT))
    c._free_ball_chase(SimpleNamespace(holder=holder, restart=restart))


def test_stable_chaser_then_ball_taken_back() -> None:
    c = _collector()
    for i in range(10):
        _tick(c, i * 0.1, [A])
    _tick(c, 1.0, [], holder="A")
    k = c.count
    assert k["ballon libre : désignations"] == 1 and k["ballon libre : changements de chasseur"] == 0
    assert k["ballon libre : épisodes disputés"] == 1 and k["ballon libre : repris par l'équipe qui l'avait"] == 1
    assert abs(k["ballon libre : délai avant la prise (somme, s)"] - 1.0) < 1e-9


def test_quick_and_slow_chaser_switches() -> None:
    c = _collector()
    _tick(c, 0.0, [A])
    _tick(c, 0.5, [B])  # 0,5 s après la désignation de A : rapide
    _tick(c, 2.0, [A])  # 1,5 s après celle de B : lent
    k = c.count
    assert k["ballon libre : changements de chasseur"] == 2
    assert k["ballon libre : changements de chasseur en moins de 1 s"] == 1


def test_two_chasers_in_a_team_are_counted_and_opponent_take_and_stoppage() -> None:
    c = _collector()
    _tick(c, 0.0, [A, B, C])
    _tick(c, 0.1, [], holder="X")
    _tick(c, 0.2, [A])
    _tick(c, 0.3, [], restart=object())
    k = c.count
    assert k["ballon libre : pas avec plus d'un chasseur par équipe"] == 1
    assert k["ballon libre : épisodes disputés"] == 2
    assert k["ballon libre : pris par l'adversaire"] == 1 and k["ballon libre : arrêt de jeu"] == 1


def test_report_without_cases_gives_zero_not_nan() -> None:
    out: dict = {}
    free_ball_report(ind.Counter(), 1, out)
    assert out and all(v == 0 for v in out.values())

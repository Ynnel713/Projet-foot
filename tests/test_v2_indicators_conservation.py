"""Conservation du ballon après un contact perdu par le porteur (ticket v2-realisme/11i) : perte sans faute dans les 3 s,
délai avant la perte et avant sa prochaine action, par tranche de Balance ; porteurs suivis vidés en fin de match. Le banc
observe sans changer le jeu."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

import scripts.v2_indicators as ind
from scripts.measure_v2 import contact_report
from tests.scenes import player

P, Q = player("P", "home", Balance=60), player("Q", "away")
BY_NAME = {"P": P, "Q": Q}
BAND = "porteurs bousculés, Balance 50-64"


def _bumped() -> ind.Collector:
    c = ind.Collector(geometry_every_s=1e9)
    c.now = 10.0
    c.on_unsettle(P, SimpleNamespace(holder="P"))
    return c


def _at(c: ind.Collector, t: float, holder: str | None = "P", restart=None) -> None:
    c.now = t
    ball = SimpleNamespace(holder=holder, last_toucher=holder or "P", restart=restart)
    if c.unsettled_carriers:
        c._close_unsettled_carriers(ball, BY_NAME)
    if c.carrier_windows:
        c._close_carrier_windows(ball, BY_NAME)


def test_tackled_after_two_seconds_is_a_loss_at_3_s_not_at_1_s() -> None:
    c = _bumped()
    _at(c, 11.0)  # 1 s : il a encore le ballon
    _at(c, 12.0, holder="Q")  # 2 s : taclé
    assert c.count[f"{BAND} : ballon gardé 1 s après"] == 1
    assert c.count[f"{BAND} : perte sans faute en 3 s"] == 1
    assert c.count[f"{BAND} : délai avant la perte (somme, s)"] == pytest.approx(2.0)
    assert not c.carrier_windows


def test_foul_suffered_is_not_a_loss() -> None:
    c = _bumped()
    _at(c, 12.0, holder=None, restart=SimpleNamespace(team="home"))
    assert c.count["porteurs bousculés suivis 3 s, Balance 50-64"] == 1
    assert c.count[f"{BAND} : perte sans faute en 3 s"] == 0


def test_ball_out_for_an_opponent_restart_is_a_loss() -> None:
    c = _bumped()
    _at(c, 11.5, holder=None, restart=SimpleNamespace(team="away"))
    assert c.count[f"{BAND} : perte sans faute en 3 s"] == 1


def test_ball_kept_for_3_s_is_not_a_loss() -> None:
    c = _bumped()
    _at(c, 12.9)
    assert c.carrier_windows  # pas encore 3 s
    _at(c, 13.0)
    assert c.count["porteurs bousculés suivis 3 s, Balance 50-64"] == 1
    assert c.count[f"{BAND} : perte sans faute en 3 s"] == 0


def test_next_action_delay_from_the_decision_log() -> None:
    c = _bumped()
    other = SimpleNamespace(player="Q", minute=10.1 / 60.0)
    before = SimpleNamespace(player="P", minute=9.0 / 60.0)  # avant le contact : ignorée
    after = SimpleNamespace(player="P", minute=11.5 / 60.0)
    c._carrier_next_action([before, other, after])
    assert c.count[f"{BAND} : action dans les 3 s"] == 1
    assert c.count[f"{BAND} : délai avant l'action (somme, s)"] == pytest.approx(1.5)


def test_no_action_within_3_s_is_not_counted() -> None:
    c = _bumped()
    c._carrier_next_action([SimpleNamespace(player="P", minute=14.0 / 60.0)])
    assert c.count[f"{BAND} : suivis jusqu'à l'action"] == 1 and c.count[f"{BAND} : action dans les 3 s"] == 0


def test_carriers_followed_at_full_time_are_dropped_without_counting() -> None:
    c = _bumped()
    c.end_match()
    assert not c.unsettled_carriers and not c.carrier_windows and not c.carrier_log
    assert c.count[f"{BAND} : perte sans faute en 3 s"] == 0 and c.count["porteurs bousculés suivis 3 s, Balance 50-64"] == 0


def test_report_gives_the_3_s_shares_without_nan() -> None:
    out: dict = {}
    contact_report(ind.Counter(), 1, out)
    assert out[f"{BAND} : perte sans faute en 3 s (part)"] == 0
    assert out[f"{BAND} : action dans les 3 s (part)"] == 0

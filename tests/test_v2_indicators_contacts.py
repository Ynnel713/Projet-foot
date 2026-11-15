"""Indicateurs des contacts physiques (ticket v2-realisme/11e) : collisions, duels d'épaule par écart de Strength,
contact perdu par Balance (12c), tacles par angle d'approche (11d). Le banc observe sans changer le jeu."""

from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace

import pytest

import scripts.v2_indicators as ind
import v2engine.match as match
from scripts.measure_v2 import _hook, contact_report
from v2engine.duel import after_contact_delay_s, after_contact_speed_loss
from v2engine.geometry import Vec2
from tests.scenes import player


def _collector() -> ind.Collector:
    return ind.Collector(geometry_every_s=1e9)


@pytest.mark.parametrize("gap, band", [(0, "0-9"), (9.5, "0-9"), (10, "10-19"), (19, "10-19"), (20, "20-39"),
                                       (39, "20-39"), (40, "40+"), (88, "40+")])
def test_strength_gap_bands(gap: float, band: str) -> None:
    assert ind.strength_gap_band(gap) == band


@pytest.mark.parametrize("angle, band", [(0, "de face"), (59.9, "de face"), (60, "de côté"), (120, "de côté"),
                                         (120.1, "par derrière"), (180, "par derrière")])
def test_approach_bands(angle: float, band: str) -> None:
    assert ind.approach_band(angle) == band


def test_balance_bands() -> None:
    assert [ind.balance_band(r) for r in (11, 49, 50, 64, 65, 79, 80, 99)] == [
        "moins de 50", "moins de 50", "50-64", "50-64", "65-79", "65-79", "80+", "80+"]


def test_collision_counts_frank_contacts_and_the_stronger_share() -> None:
    c = _collector()
    a = replace(player("A", "home", 50.0, 34.0, Strength=80), velocity=Vec2(3.0, 0.0))
    b = replace(player("B", "away", 50.5, 34.0, Strength=60), velocity=Vec2(0.0, 0.0))
    c.on_collision(a, b, 0.65)  # A plus fort de 20 : il garde 0,65
    c.on_collision(b, a, 0.35)  # même contact vu de B
    c.on_collision(replace(a, velocity=Vec2(1.5, 0.0)), b, 0.65)  # 1,5 m/s : chevauchement, pas contact franc
    c.on_collision(replace(a, team="away"), b, 0.65)  # coéquipiers
    assert c.count["contacts : chevauchements (pas)"] == 4
    assert c.count["contacts francs"] == 3 and c.count["contacts francs entre coéquipiers"] == 1
    assert c.count["contacts francs, écart de Strength 20-39"] == 3
    assert c.count["contacts francs, écart de Strength 20-39 : part du plus fort (somme)"] == pytest.approx(3 * 0.65)


def test_shoulder_duel_by_strength_gap_and_balance_at_equal_strength() -> None:
    c = _collector()
    strong, weak = player("F", "home", Strength=80, Balance=50), player("f", "away", Strength=55, Balance=70)
    c.on_shoulder_duel(strong, weak, strong)
    c.on_shoulder_duel(weak, strong, weak)
    assert c.count["duels d'épaule, écart de Strength 20-39"] == 2
    assert c.count["duels d'épaule, écart de Strength 20-39 : gagnés par le plus fort"] == 1
    assert c.count["duels d'épaule à Strength quasi égale, Balance différente"] == 0  # écart de Strength 25
    steady, shaky = player("S", "home", Strength=62, Balance=90), player("s", "away", Strength=60, Balance=40)
    c.on_shoulder_duel(steady, shaky, shaky)
    assert c.count["duels d'épaule à Strength quasi égale, Balance différente"] == 1
    assert c.count["duels d'épaule à Strength quasi égale : gagnés par le meilleur en Balance"] == 0
    assert c.count["duels d'épaule, écart de Strength 0-9"] == 1


def test_unsettled_carrier_is_followed_one_second() -> None:
    c = _collector()
    carrier, other = player("P", "home", Balance=85), player("Q", "away", Balance=30)
    ball = SimpleNamespace(holder="P", last_toucher="P", restart=None)
    c.on_unsettle(carrier, ball)
    c.on_unsettle(other, ball)  # sans ballon : pas suivi
    assert c.count["contacts perdus"] == 2 and c.count["contacts perdus : porteur"] == 1
    assert c.count["contacts perdus, Balance 80+ : vitesse perdue (somme)"] == pytest.approx(after_contact_speed_loss(carrier))
    assert c.count["contacts perdus, Balance moins de 50 : délai (somme, s)"] == pytest.approx(after_contact_delay_s(other))
    by_name = {"P": carrier, "Q": other}
    c.now = 0.9
    c._close_unsettled_carriers(SimpleNamespace(holder="Q", last_toucher="Q", restart=None), by_name)
    assert c.unsettled_carriers and c.count["porteurs bousculés, Balance 80+"] == 0  # pas encore 1 s
    c.now = 1.0
    c._close_unsettled_carriers(SimpleNamespace(holder="Q", last_toucher="Q", restart=None), by_name)
    assert not c.unsettled_carriers
    assert c.count["porteurs bousculés, Balance 80+"] == 1
    assert c.count["porteurs bousculés, Balance 80+ : ballon gardé 1 s après"] == 0  # l'adversaire l'a


@pytest.mark.parametrize("ball, kept", [
    (SimpleNamespace(holder="P", last_toucher="P", restart=None), True),
    (SimpleNamespace(holder=None, last_toucher="P", restart=None), True),  # passe en vol de son équipe
    (SimpleNamespace(holder=None, last_toucher="P", restart=SimpleNamespace(team="away")), False),  # remise adverse
    (SimpleNamespace(holder=None, last_toucher="Q", restart=SimpleNamespace(team="home")), True),  # faute subie
])
def test_unsettled_carrier_keeps_the_ball_for_his_team(ball, kept: bool) -> None:
    c = _collector()
    carrier, other = player("P", "home", Balance=60), player("Q", "away")
    c.on_unsettle(carrier, SimpleNamespace(holder="P"))
    c.now = 1.0
    c._close_unsettled_carriers(ball, {"P": carrier, "Q": other})
    assert c.count["porteurs bousculés, Balance 50-64 : ballon gardé 1 s après"] == kept


def test_tackle_approach_bands_count_attempts_wins_and_fouls() -> None:
    c = _collector()
    holder = replace(player("P", "home", 50.0, 34.0), facing=Vec2(1.0, 0.0))
    front, behind = player("D", "away", 51.0, 34.0), player("E", "away", 49.0, 34.0)
    c.on_tackle_approach(front, holder, won=True, foul=False)
    c.on_tackle_approach(behind, holder, won=False, foul=True)
    c.on_tackle_approach(behind, holder, won=False, foul=False)
    assert c.count["tacles de face"] == 1 and c.count["tacles de face : gagnés"] == 1
    assert c.count["tacles par derrière"] == 2 and c.count["tacles par derrière : fautes"] == 1


def test_contact_report_without_cases_gives_zero_not_nan() -> None:
    out: dict = {}
    contact_report(ind.Counter(), 1, out)
    assert out and all(v == 0 for v in out.values())


def test_contact_hooks_are_restored() -> None:
    real = (match.contact_share, match._unsettle, match.resolve_shoulder_duel, match.resolve_tackle)
    restore = _hook(_collector(), {})
    assert match.contact_share is not real[0] and match._unsettle is not real[1]
    restore()
    assert (match.contact_share, match._unsettle, match.resolve_shoulder_duel, match.resolve_tackle) == real

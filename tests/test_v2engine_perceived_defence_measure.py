"""Mesure de la ligne et du marquage perçus (ticket v2-realisme/08f, réserve A1 du 08e) : la ligne recalculée sur les
vraies positions (ombre) donne l'effet exact de la perception ; le banc ne change pas le jeu ; l'interrupteur A/B retire
la perception de la défense."""

from __future__ import annotations

import random

import pytest

import v2engine.bloc as bloc_module
import v2engine.defense as defense
import v2engine.match as match
from ligue1sim.clubs import load_clubs
from ligue1sim.season import CLUBS_PATH
from scripts import v2_indicators as ind
from scripts.measure_v2 import _hook, report, run


def test_line_gap_is_the_perceived_line_minus_the_real_one() -> None:
    c = ind.Collector()
    c.matches = 1
    c.on_line("home", 0.0, 30.0, 30.0, 0.1)
    c.on_line("home", 0.1, 31.5, 30.0, 0.1)  # le défenseur le plus bas n'a pas vu la course : ligne 1,5 m trop haute
    c.on_line("home", 0.2, 29.95, 30.0, 0.1)
    out = report(c)
    assert out["ligne perçue : écart absolu à la ligne sur vraies positions (moyenne, m)"] == pytest.approx((0 + 1.5 + 0.05) / 3)
    assert out["ligne perçue : écart signé, perçue - réelle (moyenne, m ; positif = ligne plus haute)"] == pytest.approx(1.45 / 3)
    assert out["ligne perçue : ticks avec un écart de plus de 1 m (part)"] == pytest.approx(1 / 3)
    assert out["ligne perçue : ticks avec un écart de plus de 0.1 m (part)"] == pytest.approx(1 / 3)  # l'écart de 5 cm ne compte pas
    assert out["ligne perçue : écart maximal (m)"] == pytest.approx(1.5)


def test_line_oscillation_counts_jumps_and_changes_of_direction_for_both_series() -> None:
    c = ind.Collector()
    c.matches = 1
    perceived = [30.0, 31.0, 30.0, 31.0, 30.0]  # saute de 1 m à chaque tick, change de sens 3 fois
    for i, value in enumerate(perceived):
        c.on_line("home", i * 0.1, value, 30.0, 0.1)  # sur les vraies positions : ligne immobile
    out = report(c)
    assert out["ligne perçue : sauts de plus de 0.5 m par match"] == 4
    assert out["ligne perçue : changements de sens par match"] == 3
    assert out["ligne réelle : sauts de plus de 0.5 m par match"] == 0
    assert out["ligne réelle : changements de sens par match"] == 0
    assert out["ligne perçue : variation moyenne d'un tick à l'autre (m)"] == pytest.approx(1.0)


def test_a_gap_in_the_series_is_not_a_variation() -> None:
    """Un tick où l'adversaire n'avait pas le ballon rompt la série : pas de saut compté sur un trou."""
    c = ind.Collector()
    c.on_line("home", 0.0, 30.0, 30.0, 0.1)
    c.on_line("home", 5.0, 40.0, 40.0, 0.1)
    assert c.count["ligne perçue : variations (nombre)"] == 0


def test_a_new_match_starting_at_zero_does_not_continue_the_previous_line_series() -> None:
    """Le premier tick d'un nouveau match (instant 0) ne fait pas de variation avec le dernier tick du précédent."""
    c = ind.Collector()
    c.on_line("home", 5400.0, 40.0, 40.0, 0.1)
    c.on_line("home", 0.0, 25.0, 25.0, 0.1)
    assert c.count["ligne perçue : variations (nombre)"] == 0


def test_marking_counts_unseen_attackers_and_the_size_of_the_error() -> None:
    c = ind.Collector()
    c.matches = 1
    c.on_marking(True, 0.0)
    c.on_marking(False, 4.0)
    c.on_marking(False, 1.0)
    c.on_marking(True, 0.0)
    c.on_marker_choice(True)
    c.on_marker_choice(False)
    out = report(c)
    assert out["marquage : attaquant non vu par son marqueur (part des marqueur-ticks)"] == 0.5
    assert out["marquage : erreur de place de l'attaquant (moyenne, m)"] == pytest.approx(1.25)
    assert out["marquage : erreur de place quand l'attaquant n'est pas vu (moyenne, m)"] == pytest.approx(2.5)
    assert out["marquage : erreur de plus de 2 m (part des marqueur-ticks)"] == 0.25
    assert out["marquage : erreur maximale (m)"] == 4.0
    assert out["marquage : marqueur différent de celui des vraies positions (part des choix)"] == 0.5


def _simulate(hooked: bool, defence_perception: bool = True):
    clubs = load_clubs(CLUBS_PATH, "Ligue 1")
    random.seed(20260923)
    collector = ind.Collector()
    restore = _hook(collector, {"now": 0.0, "dt": match.TICK_SECONDS}, True, defence_perception) if hooked else (lambda: None)
    try:
        trace = match.simulate_match(clubs[0], clubs[1], duration_minutes=2.0)
    finally:
        restore()
    return trace, collector


def test_the_bench_hook_reads_and_does_not_change_the_match() -> None:
    plain, _ = _simulate(hooked=False)
    hooked, collector = _simulate(hooked=True)
    assert [(t.minute, [(p.name, p.position) for p in t.players], t.ball.position) for t in plain.ticks] == \
           [(t.minute, [(p.name, p.position) for p in t.players], t.ball.position) for t in hooked.ticks]
    assert (plain.home_goals, plain.away_goals) == (hooked.home_goals, hooked.away_goals)
    assert collector.count["ligne : ticks adversaire porteur"] > 0 and collector.count["marquage : marqueur-ticks"] > 0
    assert bloc_module.Bloc.update.__name__ == "update" and defense.DefensiveRoles._seen_at.__name__ == "_seen_at"  # restauré


def test_without_defence_perception_the_bench_measures_nothing_of_it() -> None:
    _, collector = _simulate(hooked=True, defence_perception=False)
    assert collector.count["ligne : ticks adversaire porteur"] == 0 and collector.count["marquage : marqueur-ticks"] == 0


def test_the_report_of_a_real_run_gives_the_line_and_marking_indicators() -> None:
    random.seed(20260923)
    out = report(run(1, duration_minutes=2.0))
    for key in ("ligne perçue : écart absolu à la ligne sur vraies positions (moyenne, m)",
                "ligne perçue : variation moyenne d'un tick à l'autre (m)", "ligne réelle : variation moyenne d'un tick à l'autre (m)",
                "marquage : attaquant non vu par son marqueur (part des marqueur-ticks)",
                "marquage : marqueur différent de celui des vraies positions (part des choix)"):
        assert out[key] >= 0.0
    assert out["ligne perçue : ticks avec l'adversaire porteur par match"] > 0
    # le marquage précède la mise à jour de la mémoire : « vu » = vu au tick précédent (sinon tous « non vus », 100 %)
    assert 0.0 < out["marquage : attaquant non vu par son marqueur (part des marqueur-ticks)"] < 0.9

"""Distribution des résultats selon l'écart de niveau (ticket v2-realisme/27d) : affiches par niveau, lecture du score
à la 70e, intervalles de Wilson, nuls attendus par Poisson, déterminisme à graine fixée."""

from __future__ import annotations

import math
from types import SimpleNamespace

import pytest

from ligue1sim.clubs import load_clubs
from ligue1sim.season import CLUBS_PATH
from scripts import v2_resultats as vr
from scripts.graines_validation import RESERVED_END, RESERVED_START
from v2engine.trace import GoalEvent


def _goal(minute: float, team: str) -> GoalEvent:
    return GoalEvent(minute=minute, team=team, scorer=None, last_toucher=None, own_goal=False)


def _trace(goals: list[GoalEvent], second_half_start: float | None = 47.0) -> SimpleNamespace:
    return SimpleNamespace(goals=goals, second_half_start_minute=second_half_start,
                           home_goals=sum(g.team == "home" for g in goals),
                           away_goals=sum(g.team == "away" for g in goals))


def test_each_level_keeps_only_pairs_in_its_gap_band_with_the_stronger_team_as_favourite() -> None:
    clubs = load_clubs(CLUBS_PATH, "Ligue 1")
    notes = {c.name: vr.team_note(c) for c in clubs}
    for level, (low, high) in vr.LEVELS.items():
        pairs = vr.affiches(clubs, level)
        assert pairs, level
        for a in pairs:
            assert low <= a.gap < high
            assert notes[a.favourite] >= notes[a.outsider]
        assert pairs == vr.affiches(clubs, level)  # ordre stable


def test_seed_ranges_stay_out_of_the_validation_reserve_and_do_not_overlap() -> None:
    starts = sorted(vr.LEVEL_START.values())
    for s in starts:
        assert not (RESERVED_START <= s < RESERVED_END)
    assert all(b - a >= 1000 for a, b in zip(starts, starts[1:]))


def test_seventy_minute_follows_the_second_half_kick_off() -> None:
    assert vr.seventy_minute(48.5) == pytest.approx(73.5)  # 25 min après la reprise
    assert vr.seventy_minute(None) == 70.0


def test_match_record_reads_the_score_from_the_favourite_side_and_the_trailing_team_at_70() -> None:
    # favori à l'extérieur, mené 0-1 à la 70e (but à la 20e), égalise à la 85e : il ne perd pas
    trace = _trace([_goal(20.0, "home"), _goal(88.0, "away")])
    r = vr.match_record(trace, "away")
    assert (r["favori"], r["outsider"]) == (1, 1)
    assert r["70e"] == [0, 1] and r["menée à la 70e"] == "favori" and r["menée ne perd pas"] is True
    # outsider mené 0-1 qui perd 0-2 ; un but marqué après la 70e (minute moteur 73,5) ne compte pas dans le score à la 70e
    r = vr.match_record(_trace([_goal(10.0, "home"), _goal(74.0, "home")], 48.5), "home")
    assert r["70e"] == [1, 0] and r["menée à la 70e"] == "outsider" and r["menée ne perd pas"] is False
    # deux buts d'écart à la 70e : hors de l'indicateur
    r = vr.match_record(_trace([_goal(10.0, "home"), _goal(30.0, "home")]), "home")
    assert r["menée à la 70e"] is None and r["menée ne perd pas"] is None


def test_wilson_interval_brackets_the_share_and_narrows_with_more_matches() -> None:
    lo, hi = vr.wilson(25, 100)
    assert lo < 0.25 < hi
    assert hi - lo == pytest.approx(0.17, abs=0.01)  # ± 8,5 points environ sur 100 matchs
    lo2, hi2 = vr.wilson(250, 1000)
    assert hi2 - lo2 < hi - lo
    assert vr.wilson(0, 10)[0] == pytest.approx(0.0, abs=1e-12) and vr.wilson(0, 10)[1] > 0


def test_poisson_draw_falls_as_goals_rise() -> None:
    assert vr.poisson_draw(0.0, 0.0) == pytest.approx(1.0)
    assert vr.poisson_draw(1.35, 1.35) == pytest.approx(0.258, abs=0.01)
    assert vr.poisson_draw(2.43, 2.43) == pytest.approx(0.186, abs=0.01)
    assert vr.poisson_draw(2.43, 2.43) < vr.poisson_draw(1.35, 1.35)


def test_level_report_counts_from_the_favourite_point_of_view() -> None:
    base = {"favori nom": "A", "outsider nom": "B", "écart": 12.0, "70e": [0, 0]}
    records = [
        {**base, "favori": 2, "outsider": 0, "menée à la 70e": None, "menée ne perd pas": None},
        {**base, "favori": 1, "outsider": 1, "menée à la 70e": "favori", "menée ne perd pas": True},
        {**base, "favori": 0, "outsider": 1, "menée à la 70e": "favori", "menée ne perd pas": False},
        {**base, "favori": 3, "outsider": 1, "menée à la 70e": "outsider", "menée ne perd pas": False},
    ]
    rep = vr.level_report(records)
    assert rep["victoires du favori"]["n"] == 2 and rep["nuls"]["n"] == 1 and rep["victoires de l'outsider"]["n"] == 1
    assert rep["buts par match"] == pytest.approx(9 / 4)
    t = rep["menée d'un but à la 70e"]
    assert t["matchs"] == 3 and t["ne perd pas"] == 1 and t["dont favori mené"] == 2
    assert rep["écart de buts (favori - outsider)"] == {-1: 1, 0: 1, 2: 2}


def test_same_seed_gives_the_same_fingerprint() -> None:
    a = vr.run_series(2, ["gros"], duration=3.0)
    b = vr.run_series(2, ["gros"], duration=3.0)
    assert a["empreinte"] == b["empreinte"]
    first, second = a["matchs"]
    assert first["favori nom"] == second["favori nom"]  # même affiche jouée deux fois
    assert first["domicile"] == second["extérieur"]  # camps inversés
    assert first["graine"] != second["graine"]
    assert math.isfinite(a["niveaux"]["gros"]["buts par match"])


def test_implied_probabilities_remove_the_bookmaker_margin() -> None:
    p = vr.implied(2.0, 3.5, 4.0)
    assert sum(p) == pytest.approx(1.0)
    assert p[0] > p[2] > 0 and p[0] / p[2] == pytest.approx(2.0)


def test_market_references_average_home_and_away_favourites_with_equal_weight(monkeypatch) -> None:
    notes = {"A": 80.0, "B": 66.0}  # gros écart, A favori
    rows = [  # A reçoit : 70 % ; A se déplace : 50 % (cotes sans marge)
        {"HomeTeam": "A", "AwayTeam": "B", "AvgCH": 1 / 0.7, "AvgCD": 1 / 0.2, "AvgCA": 1 / 0.1, "FTR": "H"},
        {"HomeTeam": "B", "AwayTeam": "A", "AvgCH": 1 / 0.3, "AvgCD": 1 / 0.2, "AvgCA": 1 / 0.5, "FTR": "D"},
        {"HomeTeam": "B", "AwayTeam": "A", "AvgCH": 1 / 0.3, "AvgCD": 1 / 0.2, "AvgCA": 1 / 0.5, "FTR": "H"},
    ]
    monkeypatch.setattr(vr, "ODDS_NAMES", {"A": "A", "B": "B"})
    ref = vr.market_references(rows, notes)
    g = ref["gros"]
    assert g["matchs"] == 3 and g["favori à domicile"] == 1 and g["favori à l'extérieur"] == 2
    assert g["victoire du favori"] == pytest.approx(0.6)  # (0,7 + 0,5) / 2, pas (0,7 + 0,5 + 0,5) / 3
    assert g["victoire de l'outsider"] == pytest.approx(0.2)
    assert g["résultats réels (favori, nul, outsider)"] == [1, 1, 1]
    assert ref["egal"] == {"matchs": 0}


def test_every_club_of_the_odds_file_maps_to_a_ligue_1_club_of_the_data() -> None:
    clubs = {c.name for c in load_clubs(CLUBS_PATH, "Ligue 1")}
    assert set(vr.ODDS_NAMES.values()) == clubs

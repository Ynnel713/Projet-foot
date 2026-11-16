"""Neutralisation d'un ticket dans le banc pour les essais A/B (ticket v2-realisme/11q) : `--neutraliser 11h` remplace
le facteur de tentative de tacle par 1,0 le temps de chaque match, puis rétablit le moteur."""

from __future__ import annotations

import pytest

from scripts import bench_series as bs
from v2engine import match


def test_names_are_parsed_deduplicated_and_unknown_ones_refused() -> None:
    assert bs.parse_neutralised(None) == ()
    assert bs.parse_neutralised("11h, 11h") == ("11h",)
    with pytest.raises(ValueError, match="inconnue : zz.*connues : 11h"):
        bs.parse_neutralised("11h,zz")


def test_the_engine_is_restored_after_the_match_even_on_error() -> None:
    real = match.tackle_attempt_factor
    with bs.neutralised(["11h"]):
        assert match.tackle_attempt_factor(None, None, False, True) == 1.0
    assert match.tackle_attempt_factor is real
    with pytest.raises(RuntimeError), bs.neutralised(["11h"]):
        raise RuntimeError
    assert match.tackle_attempt_factor is real


def test_a_neutralised_series_records_it_and_avoids_no_tackle() -> None:
    series = bs.run_series(1, duration=1.0, neutral=["11h"])
    assert series["paramètres"]["neutralisés"] == ["11h"]
    assert series["agrégé"]["renoncements au tacle (tacle évité par 11h), par match"] == 0
    assert "neutralisés" not in bs.run_series(1, duration=1.0)["paramètres"]


def test_the_command_line_refuses_an_unknown_ticket() -> None:
    with pytest.raises(SystemExit):
        bs.main(["1", "--neutraliser", "zz"])

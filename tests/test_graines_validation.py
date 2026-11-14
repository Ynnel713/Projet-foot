"""Graines réservées à la validation indépendante (ticket v2-realisme/18b) : le banc refuse de calibrer dessus et
refuse de valider ailleurs."""

from __future__ import annotations

import pytest

from scripts import bench_series as bs
from scripts import graines_validation as gv
from scripts.measure_v2 import AUDIT_SEED, report, run


def test_reserved_range_is_the_one_validated_by_the_owner() -> None:
    assert (gv.RESERVED_START, gv.BLOCK_SIZE) == (100_000, 2_000)
    assert AUDIT_SEED + gv.RESERVED_START == 20_360_923
    assert gv.is_reserved(100_000) and gv.is_reserved(gv.RESERVED_END - 1)
    assert not gv.is_reserved(99_999) and not gv.is_reserved(gv.RESERVED_END)


@pytest.mark.parametrize("start, n", [(0, 20), (50, 60), (1000, 500), (2000, 120), (99_000, 1000)])
def test_series_already_used_by_the_tickets_stay_allowed(start: int, n: int) -> None:
    gv.check_series(start, n)  # aucune exception : les commandes existantes ne changent pas


@pytest.mark.parametrize("start, n", [(100_000, 1), (99_999, 2), (101_500, 500), (0, 200_001)])
def test_calibration_series_touching_the_reserve_is_refused(start: int, n: int) -> None:
    with pytest.raises(gv.ReservedSeedError, match="réservée"):
        gv.check_series(start, n)


def test_validation_series_must_stay_inside_the_reserve() -> None:
    gv.check_series(100_000, 1_000, validation=True)
    gv.check_series(102_000, 2_000, validation=True)  # deuxième passage : bloc suivant
    for start, n in [(0, 10), (99_999, 2), (gv.RESERVED_END - 1, 2)]:
        with pytest.raises(gv.ReservedSeedError, match="hors de la réserve"):
            gv.check_series(start, n, validation=True)


def test_profile_series_are_checked_on_the_seeds_they_really_play() -> None:
    # avec un profil, le match i joue la graine i // 2 : les matchs 200 000 et 200 001 jouent la graine 100 000
    assert gv.seed_indices(200_000, 2, profile=True) == range(100_000, 100_001)
    assert gv.seed_indices(199_998, 2, profile=True) == range(99_999, 100_000)
    gv.check_series(199_998, 2, profile=True)
    with pytest.raises(gv.ReservedSeedError):
        gv.check_series(199_998, 4, profile=True)


def test_bench_refuses_a_reserved_seed_in_calibration_mode() -> None:
    with pytest.raises(gv.ReservedSeedError):
        run(1, duration_minutes=1.0, start=100_000)
    with pytest.raises(gv.ReservedSeedError):
        bs.run_series(2, processes=1, duration=1.0, start=99_999)
    with pytest.raises(gv.ReservedSeedError):
        run(1, duration_minutes=1.0, start=0, validation=True)
    with pytest.raises(gv.ReservedSeedError):
        bs.main(["2", "--processus", "1", "--debut", "100000"])


def test_validation_series_plays_the_reserved_seed_and_is_deterministic() -> None:
    first = report(run(1, duration_minutes=1.0, start=100_000, validation=True))
    second = report(run(1, duration_minutes=1.0, start=100_000, validation=True))
    for r in (first, second):
        r.pop("temps de calcul par match (s)")  # horloge : seule valeur qui varie
    assert first == second
    series = bs.run_series(1, processes=1, duration=1.0, start=100_000, validation=True)
    assert series["matchs"] == [100_000]

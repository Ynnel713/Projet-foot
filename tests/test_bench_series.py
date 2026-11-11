"""Séries longues du banc V2 (ticket v2-realisme/01e) : agrégation exacte, intervalles de confiance, comparaison
appariée, résultats indépendants du nombre de processus."""

from __future__ import annotations

import math

import pytest

from scripts import bench_series as bs
from scripts.measure_v2 import report, run


def test_summary_gives_mean_sample_deviation_and_a_95_percent_interval() -> None:
    s = bs.summary([1.0, 2.0, 3.0, 4.0])
    sd = math.sqrt(5.0 / 3.0)  # écart-type d'échantillon de 1, 2, 3, 4
    assert s["n"] == 4 and s["moyenne"] == 2.5 and math.isclose(s["écart-type"], sd)
    half = 1.96 * sd / 2.0
    assert math.isclose(s["ic95"][0], 2.5 - half) and math.isclose(s["ic95"][1], 2.5 + half)
    assert bs.summary([7.0])["ic95"] == (7.0, 7.0)


def test_paired_comparison_works_match_by_match_and_refuses_unpaired_series() -> None:
    before = {"matchs": [0, 1, 2], "par match": {"buts": [2.0, 4.0, 3.0], "tirs": [10.0, None, 12.0]}}
    after = {"matchs": [0, 1, 2], "par match": {"buts": [3.0, 5.0, 4.0], "tirs": [11.0, 9.0, 14.0]}}
    diff = bs.compare(before, after)
    assert diff["buts"]["moyenne"] == 1.0 and diff["buts"]["ic95"] == (1.0, 1.0)  # +1 à chaque match
    assert diff["tirs"]["n"] == 2 and diff["tirs"]["moyenne"] == 1.5  # le match sans valeur est écarté
    with pytest.raises(ValueError):
        bs.compare(before, {**after, "matchs": [3, 4, 5]})


def test_machine_time_is_estimated_before_launch(monkeypatch) -> None:
    monkeypatch.setattr(bs.os, "cpu_count", lambda: 8)
    assert bs.estimate_seconds(10, 1) == 10 * bs.SECONDS_PER_MATCH
    assert bs.estimate_seconds(10, 1, duration=45.0) == 5 * bs.SECONDS_PER_MATCH
    # 7 processus sur 8 fils (4 cœurs) : 2,6 fois plus vite, comme l'essai de 100 matchs du ticket (48,5 min)
    assert math.isclose(bs.estimate_seconds(100, 7) / 60.0, 100 * 75.0 / 2.6 / 60.0)
    assert bs.estimate_seconds(100, 7) == bs.estimate_seconds(100, 32)  # pas plus de processus utiles que de cœurs
    assert bs.speedup(2) == 1.3


def test_results_do_not_depend_on_the_number_of_processes() -> None:
    one = bs.run_series(4, processes=1, duration=1.0)
    four = bs.run_series(4, processes=4, duration=1.0)
    assert one["matchs"] == four["matchs"] == [0, 1, 2, 3]
    assert one["agrégé"] == four["agrégé"] and one["par match"] == four["par match"]
    assert one["paramètres"] == {"durée (min)": 1.0, "profil": None, "pas (s)": bs.TICK_S, "plans": True}
    # même mesure que `measure_v2` sur les mêmes matchs (aux arrondis près : sommes regroupées par match)
    sequential = report(run(4, duration_minutes=1.0))
    for key in ("passes par minute", "tirs tracés par équipe", "temps de jeu effectif (part)", "buts par match"):
        assert one["agrégé"][key] == pytest.approx(sequential[key], rel=1e-9)
    assert all(len(v) == 4 for v in one["par match"].values())
    assert any(k.startswith("km par joueur de champ, par poste : ") for k in one["par match"])  # km par poste
    # ticket v2-realisme/19d : rendement par tranche fusionné comme dans un seul `run`
    merged, single = one["agrégé"]["rendement par tranche de 15 min"], sequential["rendement par tranche de 15 min"]
    assert merged.keys() == single.keys() and merged
    assert all(merged[k] == pytest.approx(single[k], abs=1e-3) for k in merged)
    by_player = "rendement par joueur (tranches de 15 min)"
    assert one["agrégé"][by_player]["synthèse"] == pytest.approx(sequential[by_player]["synthèse"], rel=1e-9)


def test_every_indicator_of_any_match_gets_per_match_values() -> None:
    results = [{"indicateurs": {"buts par match": 2.0, "km par joueur de champ, par poste : MOC": 11.0}},
               {"indicateurs": {"buts par match": 4.0, "tirs, origine : centre (part)": 0.5}},
               {"indicateurs": {"buts par match": 3.0, "tirs, origine : centre (part)": 0.25}}]
    per_match = bs._per_match(results)
    # part tirée d'un compteur, absente du premier match : elle y vaut 0 ; un poste absent d'une formation est écarté
    assert per_match["tirs, origine : centre (part)"] == [0.0, 0.5, 0.25]
    assert per_match["km par joueur de champ, par poste : MOC"] == [11.0, None, None]
    ci = bs.confidence({"par match": per_match})
    assert ci["tirs, origine : centre (part)"]["n"] == 3 and ci["km par joueur de champ, par poste : MOC"]["n"] == 1

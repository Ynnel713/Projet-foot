"""Séries longues du banc V2 (ticket v2-realisme/01e) : N matchs répartis sur plusieurs processus, une graine par
match (celle de `scripts/measure_v2.run`), agrégés dans l'ordre des matchs : le résultat ne dépend pas du nombre de
processus. Pour chaque indicateur : valeur agrégée (celle de `measure_v2`), puis moyenne par match, écart-type et
intervalle de confiance à 95 % de cette moyenne. Comparaison appariée de deux séries (mêmes matchs, deux versions ou
deux profils) : écart moyen par match et son intervalle de confiance.

Usage :
  uv run python -m scripts.bench_series 500 --processus 6 --json serie.json [--profil "Work Rate"] [--pas 0.1]
  uv run python -m scripts.bench_series --comparer avant.json apres.json

La durée machine est estimée et affichée avant le lancement (`SECONDS_PER_MATCH`, mesuré au ticket 01d).
Intervalle de confiance : approximation normale (1,96 écart-type de la moyenne), valable pour les séries longues
(500 matchs et plus) ; indicatif sous une trentaine de matchs. Pour une part, l'intervalle porte sur la moyenne des
parts match par match, qui peut différer de la valeur agrégée (sommes) : la sortie le signale.
Mémoire : le collecteur fusionné garde toutes les valeurs brutes, comme `measure_v2` ; mesurer le pic sur 100 matchs
avant une série de 2 000 (environ 8 à 12 Go estimés par l'expert au ticket 01e)."""

from __future__ import annotations

import argparse
import json
import math
import os
import statistics
import sys
import time
from collections.abc import Sequence
from concurrent.futures import ProcessPoolExecutor

from scripts.measure_v2 import TICK_S, report, run
from scripts.v2_indicators import Collector

Z_95 = 1.96
# Parts tirées des compteurs (`measure_v2.report`) : absentes d'un match quand le compteur y est nul, elles y valent 0
# (point A2 de l'expert, ticket 01e). Les autres indicateurs absents d'un match (poste absent de la formation) sont
# écartés de ses valeurs.
ZERO_WHEN_ABSENT = ("choix ", "tirs, origine : ", "part du temps en ", "récupération ")
SECONDS_PER_MATCH = 75.0  # un match de 90 min, un processus (référence du ticket v2-realisme/01d : 74,9 s)
# Accélération en parallèle, mesurée au ticket 01e : 100 matchs sur 7 processus en 48,5 min, soit 2,6 fois plus vite
# qu'un seul processus, sur 8 fils logiques (4 cœurs physiques supposés). Modèle : 0,65 par cœur physique occupé.
# ponytail: modèle calé sur une seule machine ; à recaler si l'estimation s'écarte de plus de 30 % de la durée réelle
PARALLEL_EFFICIENCY = 0.65


def summary(values: Sequence[float]) -> dict[str, float]:
    """Moyenne, écart-type (échantillon) et intervalle de confiance à 95 % de la moyenne."""
    n = len(values)
    mean = statistics.fmean(values)
    sd = statistics.stdev(values) if n > 1 else 0.0
    half = Z_95 * sd / math.sqrt(n)
    return {"n": n, "moyenne": mean, "écart-type": sd, "ic95": (mean - half, mean + half)}


def _one_match(args: tuple[int, str | None, float, float, bool]) -> dict:
    """Un match (indice `i`, donc sa graine) dans un processus : ses compteurs bruts et ses indicateurs."""
    i, profile, duration, tick_s, plans = args
    c = run(1, profile, duration_minutes=duration, tick_s=tick_s, plans=plans, start=i)
    return {
        "match": i,
        "count": dict(c.count),
        "stats": {name: s.values for name, s in c.stats.items()},
        "km": dict(c.km),
        "secondes": c.seconds_per_match,
        "indicateurs": _numeric(report(c)),
    }


def _numeric(indicators: dict) -> dict[str, float]:
    """Indicateurs numériques d'un rapport ; les dictionnaires (km par poste) sont dépliés en « clé : poste »."""
    out = {}
    for key, value in indicators.items():
        if isinstance(value, dict):
            out.update({f"{key} : {sub}": v for sub, v in value.items() if isinstance(v, (int, float))})
        elif isinstance(value, (int, float)) and key != "matchs":
            out[key] = value
    return out


def _per_match(results: list[dict]) -> dict[str, list[float | None]]:
    """Valeurs par match de chaque indicateur, sur l'union des clés de tous les matchs (ordre trié, stable)."""
    keys = sorted({k for r in results for k in r["indicateurs"]})

    def default(key: str) -> float | None:
        return 0.0 if key.startswith(ZERO_WHEN_ABSENT) else None

    return {k: [r["indicateurs"].get(k, default(k)) for r in results] for k in keys}


def _merge_into(merged: Collector, r: dict) -> None:
    """Ajoute un match au collecteur fusionné, équivalent à un seul `run` sur tous les matchs : compteurs sommés,
    valeurs mises bout à bout, dans l'ordre des matchs (le découpage par zone, score et minute n'est pas repris)."""
    merged.matches += 1
    merged.count.update(r["count"])
    for name, values in r["stats"].items():
        merged.stats[name].values.extend(values)
    for poste, values in r["km"].items():
        merged.km[poste].extend(values)


def run_series(n_matches: int, processes: int = 1, profile: str | None = None, duration: float = 90.0,
               tick_s: float = TICK_S, plans: bool = True, start: int = 0) -> dict:
    jobs = [(i, profile, duration, tick_s, plans) for i in range(start, start + n_matches)]
    merged, results = Collector(), []
    merged.minutes_per_match = duration
    # fusion au fil de l'eau, dans l'ordre des matchs : les valeurs brutes d'un match ne sont gardées qu'une fois, dans
    # le collecteur fusionné (point A3 de l'expert, ticket 01e)
    pool = ProcessPoolExecutor(max_workers=processes) if processes > 1 else None
    try:
        stream = pool.map(_one_match, jobs) if pool else map(_one_match, jobs)
        for r in stream:
            _merge_into(merged, r)
            results.append({"match": r["match"], "indicateurs": r["indicateurs"], "secondes": r["secondes"]})
    finally:
        if pool:
            pool.shutdown()
    per_match = _per_match(results)
    per_match.pop("temps de calcul par match (s)", None)
    return {
        "paramètres": {"durée (min)": duration, "profil": profile, "pas (s)": tick_s, "plans": plans},
        "matchs": [r["match"] for r in results],
        "agrégé": {k: v for k, v in report(merged).items() if k != "temps de calcul par match (s)"},
        "par match": per_match,
        "secondes par match": statistics.fmean(r["secondes"] for r in results),
    }


def confidence(series: dict) -> dict[str, dict]:
    """Intervalle de confiance de la moyenne par match de chaque indicateur (valeurs absentes ignorées)."""
    out = {}
    for key, values in series["par match"].items():
        present = [v for v in values if v is not None]
        if present:
            out[key] = summary(present)
    return out


def compare(before: dict, after: dict) -> dict[str, dict]:
    """Écart apparié après − avant, match par match (mêmes matchs exigés)."""
    if before["matchs"] != after["matchs"]:
        raise ValueError("séries non appariées : les deux séries doivent porter sur les mêmes matchs")
    if before.get("paramètres") != after.get("paramètres"):  # deux profils, par exemple : voulu, mais à savoir
        print(f"attention, paramètres différents : {before.get('paramètres')} contre {after.get('paramètres')}",
              file=sys.stderr)
    out = {}
    for key in before["par match"].keys() & after["par match"].keys():
        pairs = [(a, b) for a, b in zip(before["par match"][key], after["par match"][key]) if a is not None and b is not None]
        if pairs:
            out[key] = summary([b - a for a, b in pairs])
    return out


def speedup(processes: int) -> float:
    """Accélération attendue avec `processes` processus (1 pour un seul) : cœurs physiques supposés = fils / 2."""
    if processes <= 1:
        return 1.0
    return max(1.0, min(processes, max(1, (os.cpu_count() or 2) // 2)) * PARALLEL_EFFICIENCY)


def estimate_seconds(n_matches: int, processes: int, duration: float = 90.0) -> float:
    return n_matches * SECONDS_PER_MATCH * duration / 90.0 / speedup(processes)


def _fmt(s: dict) -> str:
    low, high = s["ic95"]
    return f"{s['moyenne']:.4g} ± {(high - low) / 2:.2g} [{low:.4g} ; {high:.4g}] (é.-t. {s['écart-type']:.3g}, n = {s['n']})"


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("matches", nargs="?", type=int, default=500)
    parser.add_argument("--processus", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    parser.add_argument("--profil", default=None)
    parser.add_argument("--pas", type=float, default=TICK_S)
    parser.add_argument("--sans-plan", action="store_true")
    parser.add_argument("--debut", type=int, default=0)
    parser.add_argument("--json", default=None)
    parser.add_argument("--comparer", nargs=2, metavar=("AVANT", "APRES"))
    args = parser.parse_args(argv)
    if args.comparer:
        before, after = (json.load(open(p, encoding="utf-8")) for p in args.comparer)
        for key, s in sorted(compare(before, after).items()):
            low, high = s["ic95"]
            flag = "" if low <= 0.0 <= high else "  <- écart significatif"
            print(f"{key} : écart {_fmt(s)}{flag}")
        return
    eta = estimate_seconds(args.matches, args.processus)
    print(f"{args.matches} matchs sur {args.processus} processus : durée machine estimée {eta / 60:.0f} min", flush=True)
    started = time.perf_counter()
    series = run_series(args.matches, args.processus, args.profil, tick_s=args.pas, plans=not args.sans_plan,
                        start=args.debut)
    ci = confidence(series)
    for key, value in _numeric(series["agrégé"]).items():
        if key not in ci:
            print(f"{key} : {value}")
            continue
        low, high = ci[key]["ic95"]
        # point A1 de l'expert : pour une part, la valeur agrégée (sommes) et la moyenne par match diffèrent
        flag = "" if low <= value <= high else "  (valeur agrégée hors de l'IC de la moyenne par match)"
        print(f"{key} : {value:.4g} | par match : {_fmt(ci[key])}{flag}")
    print(f"durée machine réelle : {(time.perf_counter() - started) / 60:.1f} min", file=sys.stderr)
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(series, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()

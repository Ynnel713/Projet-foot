"""Taux de meilleur choix suivi en match (ticket v2-collectif/33) : par tranche de Decisions, part des décisions du
porteur qui prennent le meilleur choix factuel, comparée à la courbe validée (`decision.best_choice_probability`),
et écart de valeur des erreurs (voisines ou absurdes). Graine d'audit, matchs de Ligue 1.

Usage : uv run python -m scripts.measure_v2_meilleur_choix [nombre_de_matchs] [--minutes 90]"""

from __future__ import annotations

import argparse
import random
import statistics
import time

from ligue1sim.clubs import load_clubs
from ligue1sim.lineup import pick_best_formation
from ligue1sim.season import CLUBS_PATH

from v2engine import match
from v2engine.attributes import player_attribute
from v2engine.decision import best_choice_probability

AUDIT_SEED = 20260923
BANDS = ((0, 40), (40, 55), (55, 65), (65, 75), (75, 100))


def run(n_matches: int, minutes: float) -> dict:
    clubs = load_clubs(CLUBS_PATH, "Ligue 1")
    by_band: dict[tuple[int, int], list] = {band: [] for band in BANDS}
    kinds: dict[str, int] = {}
    started = time.perf_counter()
    for i in range(n_matches):
        random.seed(AUDIT_SEED + i)
        home, away = clubs[(2 * i) % len(clubs)], clubs[(2 * i + 1) % len(clubs)]
        notes = {p.name: player_attribute(p, "Decisions") for c in (home, away) for p in pick_best_formation(c).players}
        trace = match.simulate_match(home, away, duration_minutes=minutes)
        for d in trace.decisions:
            note = notes.get(d.player, 60)
            band = next(b for b in BANDS if b[0] <= note < b[1] or (b[1] == 100 and note >= b[0]))
            by_band[band].append((d.best, d.gap, note))
            kinds[d.action] = kinds.get(d.action, 0) + 1
    seconds = time.perf_counter() - started
    return {"bands": by_band, "kinds": kinds, "seconds_per_match": seconds / n_matches}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("matches", nargs="?", type=int, default=4)
    parser.add_argument("--minutes", type=float, default=90.0)
    args = parser.parse_args()
    result = run(args.matches, args.minutes)
    print(f"{args.matches} matchs de {args.minutes:g} min, {result['seconds_per_match']:.0f} s de calcul par match")
    print("Decisions | décisions | meilleur choix suivi | courbe validée | écart médian des erreurs")
    for (low, high), rows in result["bands"].items():
        if not rows:
            continue
        rate = sum(best for best, _, _ in rows) / len(rows)
        target = statistics.mean(best_choice_probability(note) for _, _, note in rows)
        gaps = [gap for best, gap, _ in rows if not best]
        median = statistics.median(gaps) if gaps else 0.0
        print(f"{low:>3}-{high:<3}   | {len(rows):>9} | {rate:>19.1%} | {target:>14.1%} | {median:.4f}")
    total = sum(result["kinds"].values())
    print("Choix faits : " + ", ".join(f"{k} {v / total:.1%}" for k, v in sorted(result["kinds"].items())))


if __name__ == "__main__":
    main()

"""Ticket 07c : répartition des types de réception (de face, de profil, dos au jeu) par poste, sur N matchs à graine
fixée (graine 20260923 + k, clubs de Ligue 1 par paires), lue dans `MatchTrace.receptions`.
Usage : uv run python .scratch/v2-realisme/mesures/07c-repartition.py N"""
from __future__ import annotations

import random
import sys
from collections import Counter
from concurrent.futures import ProcessPoolExecutor

from ligue1sim.clubs import load_clubs
from ligue1sim.season import CLUBS_PATH
import v2engine.match as match

AUDIT_SEED = 20260923
KINDS = ("de face", "de profil", "dos au jeu")


def one(k: int) -> Counter:
    clubs = load_clubs(CLUBS_PATH, "Ligue 1")
    random.seed(AUDIT_SEED + k)
    trace = match.simulate_match(clubs[(2 * k) % len(clubs)], clubs[(2 * k + 1) % len(clubs)])
    c: Counter = Counter()
    for r in trace.receptions:
        for group in (r.poste, "tous"):
            c[(group, r.kind)] += 1
            c[(group, r.kind, "contrôlé")] += r.controlled
    return c


if __name__ == "__main__":
    n = int(sys.argv[1])
    total: Counter = Counter()
    with ProcessPoolExecutor(4) as pool:
        for c in pool.map(one, range(n)):
            total.update(c)
    groups = sorted({key[0] for key in total if key[0] != "tous"}) + ["tous"]
    print(f"{n} matchs ; réceptions de passes au premier contact ; part par type (contrôle réussi)")
    for g in groups:
        count = sum(total[(g, kind)] for kind in KINDS)
        cells = "  ".join(f"{kind} {total[(g, kind)] / count:5.1%} ({total[(g, kind, 'contrôlé')] / max(1, total[(g, kind)]):.0%})"
                          for kind in KINDS)
        print(f"{g:5s} n={count:6d}  {cells}")

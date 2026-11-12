"""Ticket 07a : empreinte du jeu sur N matchs à graine fixée (positions, vitesses, ballon, événements), hors cap.
Usage : uv run python .scratch/v2-realisme/mesures/07a-empreinte.py N SORTIE.json"""
from __future__ import annotations

import hashlib
import json
import random
import sys
import time
from concurrent.futures import ProcessPoolExecutor

from ligue1sim.clubs import load_clubs
from ligue1sim.season import CLUBS_PATH
import v2engine.match as match

AUDIT_SEED = 20260923


def one(k: int) -> dict:
    clubs = load_clubs(CLUBS_PATH, "Ligue 1")
    random.seed(AUDIT_SEED + k)
    home, away = clubs[(2 * k) % len(clubs)], clubs[(2 * k + 1) % len(clubs)]
    h = hashlib.sha256()

    def observer(now_s, players, ball, scoring_team):
        for p in players:
            h.update(f"{p.name}|{p.position.x:.9f}|{p.position.y:.9f}|{p.velocity.x:.9f}|{p.velocity.y:.9f}|"
                     f"{p.condition.energy:.9f}".encode())
        h.update(f"B|{ball.position.x:.9f}|{ball.position.y:.9f}|{ball.holder}|{scoring_team}".encode())

    t0 = time.perf_counter()
    trace = match.simulate_match(home, away, observer=observer)
    dt = time.perf_counter() - t0
    for g in trace.goals:
        h.update(repr(g).encode())
    for s in trace.shots:
        h.update(repr(s).encode())
    for d in trace.decisions:
        h.update(repr(d).encode())
    facing = None
    if trace.ticks and hasattr(trace.ticks[0].players[0], "facing"):
        facing = hashlib.sha256("".join(f"{p.facing:.9f}" for t in trace.ticks for p in t.players).encode()).hexdigest()
    return {"k": k, "jeu": h.hexdigest(), "cap": facing, "buts": len(trace.goals), "tirs": len(trace.shots),
            "decisions": len(trace.decisions), "secondes": round(dt, 2)}


if __name__ == "__main__":
    n, out = int(sys.argv[1]), sys.argv[2]
    with ProcessPoolExecutor(4) as pool:
        rows = list(pool.map(one, range(n)))
    json.dump(rows, open(out, "w"), indent=1)
    print(sum(r["secondes"] for r in rows), "s de calcul ;", sum(r["buts"] for r in rows), "buts ;",
          sum(r["tirs"] for r in rows), "tirs")

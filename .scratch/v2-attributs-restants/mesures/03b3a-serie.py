"""Série du ticket v2-attributs-restants/03b3a (hors dépôt, lecture seule du moteur) : mêmes matchs du banc. Par match :
score ; pour chaque gardien, son Rushing Out, sa distance moyenne à sa ligne quand le ballon est à plus de 40 m de son
but (ballon en jeu), le nombre de sorties sur ballon libre (passages à l'état « sortie ») et de ballons pris hors de sa
surface. Option `--force N` : tous les gardiens jouent à Rushing Out N (style forcé, effet isolé), sinon notes réelles.

Utilisation : `PYTHONPATH=. PYTHONHASHSEED=0 <python> .scratch/v2-attributs-restants/mesures/03b3a-serie.py 50 4 sortie.json [--force 90]`."""

from __future__ import annotations

import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

FORCE: float | None = None


def one(args: tuple[int, float | None]) -> dict:
    i, force = args
    from scripts.v2_chain import play
    from v2engine import gardien
    from v2engine.geometry import in_penalty_area
    if force is not None:
        gardien.rushing_out = lambda keeper: float(force)
    trace = play(i)
    stats = {}
    for team in ("home", "away"):
        goal = gardien.own_goal(team)
        depths, sorties, prises, was_out, held = [], 0, 0, False, False
        name, note = None, None
        for tick in trace.ticks:
            keeper = next((p for p in tick.players if p.team == team and p.poste == "GK"), None)
            if keeper is None:
                continue
            name = keeper.name
            ball = tick.ball
            if not ball.dead and ball.position.distance_to(goal) > 40.0:
                depths.append(abs(keeper.position.x - goal.x))
            out = keeper.intention is not None and keeper.intention.reason.startswith("sortie")
            sorties += out and not was_out
            was_out = out
            has = ball.holder == keeper.name
            prises += has and not held and not in_penalty_area(team, keeper.position)
            held = has
        stats[team] = {"gardien": name, "hauteur": sum(depths) / len(depths) if depths else None,
                       "sorties": sorties, "prises hors surface": prises}
    return {"match": i, "score": [trace.home_goals, trace.away_goals], "gardiens": stats}


def notes() -> dict[str, float]:
    from ligue1sim.clubs import load_clubs
    from ligue1sim.lineup import pick_best_formation
    from scripts.measure_v2 import CLUBS_PATH
    out = {}
    for club in load_clubs(CLUBS_PATH, "Ligue 1"):
        gk = next(p for p in pick_best_formation(club).players if p.poste == "GK")
        out[gk.name] = (getattr(gk, "attributes", None) or {}).get("Rushing Out (Tendency)")
    return out


if __name__ == "__main__":
    n, procs, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    force = float(sys.argv[sys.argv.index("--force") + 1]) if "--force" in sys.argv else None
    with ProcessPoolExecutor(max_workers=procs, max_tasks_per_child=1) as pool:
        rows = list(pool.map(one, [(i, force) for i in range(n)]))
    table = notes()
    for row in rows:
        for s in row["gardiens"].values():
            s["rushing out"] = force if force is not None else table.get(s["gardien"])
    Path(out).write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    print("ok", n, sum(sum(r["score"]) for r in rows) / n)

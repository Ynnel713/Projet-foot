"""Série appariée du ticket v2-attributs-restants/03b1 (hors dépôt, lecture seule) : mêmes matchs du banc, moteur du
répertoire courant (avant : copie du dépôt à la révision d'avant le ticket ; après : dépôt). Par match : score, et
pour chaque tir son issue, la distance, l'écart et le temps au gardien, et le gardien qui l'affronte (Reflexes, One on
Ones). Usage, depuis la racine du moteur à mesurer :
PYTHONPATH=. PYTHONHASHSEED=0 <python du dépôt> <ce script> <matchs> <processus> <sortie.json>"""
from __future__ import annotations

import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path


def one(i: int) -> dict:
    from ligue1sim.lineup import pick_best_formation
    from scripts.v2_chain import play
    from scripts.measure_v2 import CLUBS_PATH
    from ligue1sim.clubs import load_clubs
    clubs = load_clubs(CLUBS_PATH, "Ligue 1")
    home, away = clubs[(2 * i) % len(clubs)], clubs[(2 * i + 1) % len(clubs)]
    keepers = {}
    for team, club in (("home", home), ("away", away)):
        gk = next(p for p in pick_best_formation(club).players if p.poste == "GK")
        a = getattr(gk, "attributes", None) or {}
        keepers[team] = {"Reflexes": a.get("Reflexes"), "One on Ones": a.get("One on Ones")}
    trace = play(i)
    shots = [{"équipe": s.team, "issue": s.outcome, "x": s.x, "y": s.y, "écart": s.keeper_gap_m,
              "temps": s.keeper_time_s, "xg": s.xg, "origine": s.origin,
              "gardien": keepers["away" if s.team == "home" else "home"]} for s in trace.shots]
    return {"match": i, "score": [trace.home_goals, trace.away_goals], "tirs": shots}


if __name__ == "__main__":
    n, procs, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    with ProcessPoolExecutor(max_workers=procs, max_tasks_per_child=1) as pool:
        rows = list(pool.map(one, range(n)))
    Path(out).write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    print("ok", n, sum(sum(r["score"]) for r in rows) / n)

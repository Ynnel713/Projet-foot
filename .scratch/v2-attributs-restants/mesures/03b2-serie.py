"""Série appariée du ticket v2-attributs-restants/03b2 (hors dépôt, lecture seule) : mêmes matchs du banc, moteur du
répertoire courant (avant : copie du dépôt à la révision d'avant le ticket ; après : dépôt). Par match : score, pour
chaque tir son issue (et s'il s'agit d'une prise relâchée), le Handling du gardien qui l'affronte ; corners, et corners
dont le dernier toucher est un gardien (issus d'un arrêt). Usage, depuis la racine du moteur à mesurer :
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
    keepers, names = {}, set()
    for team, club in (("home", home), ("away", away)):
        gk = next(p for p in pick_best_formation(club).players if p.poste == "GK")
        names.add(gk.name)
        keepers[team] = (getattr(gk, "attributes", None) or {}).get("Handling")
    trace = play(i)
    shots = [{"équipe": s.team, "issue": s.outcome, "relâché": getattr(s, "fumbled", False),
              "handling": keepers["away" if s.team == "home" else "home"]} for s in trace.shots]
    corners = [r for r in trace.restarts if r.kind == "corner"]
    return {"match": i, "score": [trace.home_goals, trace.away_goals], "tirs": shots, "corners": len(corners),
            "corners gardien": sum(r.last_toucher in names for r in corners)}


if __name__ == "__main__":
    n, procs, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    with ProcessPoolExecutor(max_workers=procs, max_tasks_per_child=1) as pool:
        rows = list(pool.map(one, range(n)))
    Path(out).write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    print("ok", n, sum(sum(r["score"]) for r in rows) / n)

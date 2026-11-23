"""Série du ticket v2-attributs-restants/03b3b (hors dépôt, lecture seule du moteur) : mêmes matchs du banc. Par match :
score ; pour chaque gardien, son Eccentricity, ses sorties (épisodes à l'état « sortie »), ses sorties inattendues
(raison « sortie inattendue »), celles où il a eu le ballon avant la fin de l'épisode (ou dans la seconde qui suit), et
les buts encaissés dans les 15 s qui suivent le début d'une sortie inattendue. Option `--force N` : tous les gardiens
jouent à Eccentricity N (style forcé, effet isolé), sinon notes réelles.

Utilisation : `PYTHONPATH=. PYTHONHASHSEED=0 <python> .scratch/v2-attributs-restants/mesures/03b3b-serie.py 50 4 sortie.json [--force 80]`."""

from __future__ import annotations

import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path


def one(args: tuple[int, float | None]) -> dict:
    i, force = args
    from scripts.v2_chain import play
    from v2engine import gardien
    if force is not None:
        gardien.eccentricity = lambda keeper: float(force)
    trace = play(i)
    stats = {}
    for team in ("home", "away"):
        name = None
        sorties, whims, won, starts = 0, 0, 0, []
        was_out, was_whim, open_until, credited = False, False, None, True
        for tick in trace.ticks:
            keeper = next((p for p in tick.players if p.team == team and p.poste == "GK"), None)
            if keeper is None:
                continue
            name = keeper.name
            reason = keeper.intention.reason if keeper.intention is not None else ""
            out = reason.startswith("sortie")
            w = out and "sortie inattendue" in reason
            sorties += out and not was_out
            if w and not was_whim:  # début d'un épisode de sortie inattendue
                whims += 1
                starts.append(tick.minute)
                credited = False
            if w:
                open_until = tick.minute + 1.0 / 60.0  # ballon compté gagné jusqu'à 1 s après la fin de l'épisode
            if not credited and open_until is not None and tick.minute <= open_until and tick.ball.holder == name:
                won += 1
                credited = True
            was_out, was_whim = out, w
        conceded = sum(1 for g in trace.goals if g.team != team and any(0.0 <= g.minute - s <= 0.25 for s in starts))
        stats[team] = {"gardien": name, "sorties": sorties, "inattendues": whims, "gagnees": won,
                       "buts apres": conceded}
    return {"match": i, "score": [trace.home_goals, trace.away_goals], "gardiens": stats}


def notes() -> dict[str, float]:
    from ligue1sim.clubs import load_clubs
    from ligue1sim.lineup import pick_best_formation
    from scripts.measure_v2 import CLUBS_PATH
    out = {}
    for club in load_clubs(CLUBS_PATH, "Ligue 1"):
        gk = next(p for p in pick_best_formation(club).players if p.poste == "GK")
        out[gk.name] = (getattr(gk, "attributes", None) or {}).get("Eccentricity")
    return out


if __name__ == "__main__":
    n, procs, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    force = float(sys.argv[sys.argv.index("--force") + 1]) if "--force" in sys.argv else None
    with ProcessPoolExecutor(max_workers=procs, max_tasks_per_child=1) as pool:
        rows = list(pool.map(one, [(i, force) for i in range(n)]))
    table = notes()
    for row in rows:
        for s in row["gardiens"].values():
            s["eccentricity"] = force if force is not None else table.get(s["gardien"])
    Path(out).write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    print("ok", n, sum(sum(r["score"]) for r in rows) / n)

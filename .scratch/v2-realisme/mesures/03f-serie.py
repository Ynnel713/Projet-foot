"""Série appariée du ticket v2-realisme/03f (hors dépôt, lecture seule) : mêmes matchs du banc ; avant = gardien sans
élan (vitesse à la frappe ignorée, moteur du 05l), après = moteur courant. Par match : score, et pour chaque tir son
issue, l'élan du gardien vers le ballon, l'écart, le temps de vol et l'xG après frappe.
Usage : PYTHONPATH=. PYTHONHASHSEED=0 uv run python .scratch/v2-realisme/mesures/03f-serie.py <matchs> <processus> <avant|après> <sortie.json>"""
from __future__ import annotations

import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

MODE = "après"


def one(i: int) -> dict:
    from scripts.v2_chain import play
    from v2engine import match, shooting
    from v2engine.geometry import Vec2
    if MODE == "avant":
        match.keeper_toward_mps = lambda *args: 0.0
        cover = shooting._keeper_cover
        shooting._keeper_cover = lambda origin, goal, axis, at, velocity=None: cover(origin, goal, axis, at, Vec2(0.0, 0.0))
    trace = play(i)
    shots = [{"issue": s.outcome, "élan": s.keeper_toward_mps, "écart": s.keeper_gap_m, "temps": s.keeper_time_s,
              "psxg": s.post_shot_xg, "xg": s.xg, "origine": s.origin} for s in trace.shots]
    return {"match": i, "score": [trace.home_goals, trace.away_goals], "tirs": shots}


def _init(mode: str) -> None:
    global MODE
    MODE = mode


if __name__ == "__main__":
    n, procs, mode, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3], sys.argv[4]
    with ProcessPoolExecutor(max_workers=procs, initializer=_init, initargs=(mode,)) as pool:
        rows = list(pool.map(one, range(n)))
    Path(out).write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    print("ok", mode, n, sum(sum(r["score"]) for r in rows) / n)

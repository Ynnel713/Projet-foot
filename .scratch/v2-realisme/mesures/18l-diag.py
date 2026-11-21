"""Diagnostic du ticket v2-realisme/18l (hors dépôt, lecture seule) : d'où viennent les buts et les tirs en plus.

Pour chaque match du banc (mêmes graines et affiches que `scripts/measure_v2.py`) : chaque tir (distance au centre du
but visé, surface ou non, issue, origine du ballon du tireur, xG neutre) et l'origine de chaque but (`scripts.v2_chain`).
Usage : PYTHONPATH=. PYTHONHASHSEED=0 uv run python .scratch/v2-realisme/mesures/18l-diag.py <matchs> <processus> <sortie.json>
(série du 21/11/2026 : 50 matchs, 4 processus ; synthèse 18l-diag-50-synthese.txt)
"""
from __future__ import annotations

import json
import math
import sys
from concurrent.futures import ProcessPoolExecutor

from scripts.v2_chain import goal_origin, goals, play
from v2engine.geometry import PITCH_LENGTH_M, PITCH_WIDTH_M

BOX_DEPTH_M, BOX_HALF_WIDTH_M = 16.5, 20.16


def _shot_row(i: int, s) -> dict:
    gx = 0.0 if s.x < PITCH_LENGTH_M / 2.0 else PITCH_LENGTH_M  # but visé : le plus proche du lieu du tir
    dist = math.hypot(s.x - gx, s.y - PITCH_WIDTH_M / 2.0)
    box = abs(s.x - gx) <= BOX_DEPTH_M and abs(s.y - PITCH_WIDTH_M / 2.0) <= BOX_HALF_WIDTH_M
    return {"match": i, "minute": s.minute, "équipe": s.team, "distance": dist, "surface": box,
            "issue": s.outcome, "origine": s.origin, "xg": s.xg, "qualité": s.quality}


def one(i: int) -> dict:
    trace = play(i)
    shots = [_shot_row(i, s) for s in trace.shots]
    gl = []
    for g in goals(trace.events):
        o = goal_origin(trace.events, g)
        gl.append({"match": i, "minute": g.minute, "équipe": g.team, "famille": o.family, "détail": o.detail,
                   "délai (s)": o.delay_s})
    return {"tirs": shots, "buts": gl, "score": list(trace.score) if hasattr(trace, "score") else None}


if __name__ == "__main__":
    n, procs, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    with ProcessPoolExecutor(max_workers=procs) as pool:
        rows = list(pool.map(one, range(n)))
    with open(out, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False)
    print("ok", n)

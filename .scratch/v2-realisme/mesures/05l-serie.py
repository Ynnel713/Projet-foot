"""Série appariée du ticket v2-realisme/05l (hors dépôt, lecture seule) : mêmes matchs du banc ; avant = plongeon
3 m/s et visée au centre (moteur du 05j), après = moteur courant ; 5e argument facultatif : `decision.LONG_SHOT_MARGIN`.
Par match : chaque tir avec sa situation (`10k-diag.py`), buts, origine des buts, passes et pertes.
Usage : PYTHONPATH=. PYTHONHASHSEED=0 uv run python .scratch/v2-realisme/mesures/05l-serie.py <matchs> <processus> <avant|après> <sortie.json> [marge]"""
from __future__ import annotations

import importlib.util
import json
import sys
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from v2engine import match as M
from v2engine.trace import PASSE, PERTE

_spec = importlib.util.spec_from_file_location("diag10k", Path(".scratch/v2-realisme/mesures/10k-diag.py"))
diag = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(diag)
MODE = "après"
MARGE = None


def one(i: int) -> dict:
    from scripts.v2_chain import goal_origin, goals, play
    from v2engine import decision, shooting
    if MODE == "avant":
        shooting.KEEPER_DIVE_MPS = 3.0
        shooting.aim_angles = lambda shooter, goal: (0.0,)
    if MARGE is not None:
        decision.LONG_SHOT_MARGIN = MARGE
    diag.ROWS.clear()
    M.ShotEvent = diag._capture
    trace = play(i)
    rows = [dict(r, match=i) for r in diag.ROWS]
    shots = [s for s in trace.shots if s.origin != "penalty"]
    for r, s in zip(rows, shots):
        r["issue"] = s.outcome
    gl = []
    for g in goals(trace.events):
        o = goal_origin(trace.events, g)
        gl.append({"équipe": g.team, "famille": o.family, "détail": o.detail})
    passes = Counter(e.team for e in trace.events if e.kind == PASSE)
    pertes = Counter(e.team for e in trace.events if e.kind == PERTE)
    return {"match": i, "tirs": rows, "penalties": len(trace.shots) - len(shots), "score": [trace.home_goals, trace.away_goals],
            "buts": gl, "passes": sum(passes.values()), "pertes": sum(pertes.values())}


def _init(mode: str, marge) -> None:
    global MODE, MARGE
    MODE, MARGE = mode, marge


if __name__ == "__main__":
    n, procs, mode, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3], sys.argv[4]
    marge = float(sys.argv[5]) if len(sys.argv) > 5 else None
    with ProcessPoolExecutor(max_workers=procs, initializer=_init, initargs=(mode, marge)) as pool:
        rows = list(pool.map(one, range(n)))
    Path(out).write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    print("ok", mode, n, sum(sum(r["score"]) for r in rows) / n)

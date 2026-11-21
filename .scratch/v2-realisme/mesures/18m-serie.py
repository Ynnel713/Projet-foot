"""Série appariée du ticket v2-realisme/18m (hors dépôt, lecture seule) : mêmes matchs du banc (graines et affiches de
`scripts/measure_v2.py`), marge des frappes de loin à 0 (avant, comportement identique au moteur d'avant le ticket) ou
à sa valeur (après). Par match : chaque tir (comme le 18l, plus le Long Shots du tireur), l'origine de chaque but
(`scripts.v2_chain`, famille et détail), passes et pertes de balle par équipe, xG neutre.
Usage : PYTHONPATH=. PYTHONHASHSEED=0 uv run python .scratch/v2-realisme/mesures/18m-serie.py <matchs> <processus> <avant|après> <sortie.json>
(série du 21/11/2026 : 50 matchs, 4 processus, 18m-avant-50.json, 18m-apres-003-50.json à 0,03, 18m-apres-005-50.json à 0,05)"""
from __future__ import annotations

import importlib.util
import json
import sys
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from scripts.v2_chain import goal_origin, goals, play
from v2engine import decision
from v2engine.trace import PASSE, PERTE

_spec = importlib.util.spec_from_file_location("diag18l", Path(".scratch/v2-realisme/mesures/18l-diag.py"))
diag = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(diag)
MODE = "après"


def _long_shots(i: int) -> dict[str, int]:
    from ligue1sim.clubs import load_clubs
    from scripts.measure_v2 import CLUBS_PATH
    clubs = load_clubs(CLUBS_PATH, "Ligue 1")
    out = {}
    for club in (clubs[(2 * i) % len(clubs)], clubs[(2 * i + 1) % len(clubs)]):
        for p in club.players:
            out[p.name] = (p.attributes or {}).get("Long Shots")
    return out


def one(i: int) -> dict:
    if MODE == "avant":
        decision.LONG_SHOT_MARGIN = 0.0
    ls = _long_shots(i)
    trace = play(i)
    shots = []
    for s in trace.shots:
        row = diag._shot_row(i, s)
        row["long_shots"] = ls.get(s.player)
        shots.append(row)
    gl = []
    for g in goals(trace.events):
        o = goal_origin(trace.events, g)
        gl.append({"équipe": g.team, "famille": o.family, "détail": o.detail, "délai (s)": o.delay_s})
    passes = Counter(e.team for e in trace.events if e.kind == PASSE)
    pertes = Counter(e.team for e in trace.events if e.kind == PERTE)
    return {"match": i, "tirs": shots, "buts": gl, "passes": sum(passes.values()), "pertes": sum(pertes.values())}


def _init(mode: str) -> None:
    global MODE
    MODE = mode


if __name__ == "__main__":
    n, procs, mode, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3], sys.argv[4]
    with ProcessPoolExecutor(max_workers=procs, initializer=_init, initargs=(mode,)) as pool:
        rows = list(pool.map(one, range(n)))
    Path(out).write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    print("ok", mode, n)

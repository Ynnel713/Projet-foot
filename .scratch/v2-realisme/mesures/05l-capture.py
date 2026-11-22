"""Capture (hors dépôt, lecture seule) de l'état complet à chaque tir de jeu : tireur, gardien et adversaires (copies des
`PlayerState`), but visé, issue finale. Sert à rejouer hors ligne la chance d'un tir (`shooting`) sous d'autres
constantes. Mêmes graines et affiches que le banc.
Usage : PYTHONPATH=. PYTHONHASHSEED=0 uv run python .scratch/v2-realisme/mesures/05l-capture.py <matchs> <processus> <sortie.pkl>"""
from __future__ import annotations

import copy
import pickle
import sys
from concurrent.futures import ProcessPoolExecutor

from v2engine import match as M
from v2engine.trace import ShotEvent

ROWS: list[dict] = []


def _capture(*args, **kw):
    ev = ShotEvent(*args, **kw)
    f = sys._getframe(1)
    loc = dict(f.f_back.f_locals) if f.f_code.co_name == "record" else {}
    loc.update(f.f_locals)
    holder, players, goal, keeper = loc.get("holder"), loc.get("players"), loc.get("goal"), loc.get("keeper")
    if ev.origin == "penalty":
        return ev  # écarté aussi de la trace lue plus bas
    if holder is None or players is None or goal is None or ev.origin == "coup franc":
        ROWS.append(None)
        return ev
    opp = [p for p in players if p.team != holder.team]
    ROWS.append({"shooter": copy.deepcopy(holder), "keeper": copy.deepcopy(keeper), "opponents": copy.deepcopy(opp),
                 "goal": goal, "origin": ev.origin})
    return ev


def one(i: int) -> list[dict]:
    from scripts.v2_chain import play
    ROWS.clear()
    M.ShotEvent = _capture
    trace = play(i)
    out = []
    shots = [s for s in trace.shots if s.origin != "penalty"]
    rows = [r for r in ROWS]
    for r, s in zip(rows, shots):
        if r is not None:
            r.update(match=i, outcome=s.outcome, xg=s.xg)
            out.append(r)
    return out


if __name__ == "__main__":
    n, procs, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    with ProcessPoolExecutor(max_workers=procs) as pool:
        rows = [r for m in pool.map(one, range(n)) for r in m]
    with open(out, "wb") as f:
        pickle.dump(rows, f)
    print("ok", n, len(rows))

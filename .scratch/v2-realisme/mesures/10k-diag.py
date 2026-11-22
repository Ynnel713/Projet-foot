"""Diagnostic du ticket v2-realisme/10k (hors dépôt, lecture seule) : situation des tirs à 16-25 m.

À chaque tir de jeu (hors penalty), on lit l'état exact du moteur au moment du tir (pile d'appel de `ShotEvent`, sans
rien modifier au jeu) : distance du plus proche défenseur de champ, défenseurs dans le triangle tireur-poteaux, ligne
tireur-centre du but couverte (défenseur à 1 m ou moins de la ligne, entre tireur et but), presseur sur le tireur,
intention du plus proche défenseur. Mêmes graines et affiches que le banc.
Usage : PYTHONPATH=. PYTHONHASHSEED=0 uv run python .scratch/v2-realisme/mesures/10k-diag.py <matchs> <processus> <sortie.json>
"""
from __future__ import annotations

import json
import math
import sys
from concurrent.futures import ProcessPoolExecutor

from ligue1sim.pitch_geometry import GOAL_WIDTH_M
from v2engine import match as M
from v2engine.geometry import PITCH_LENGTH_M, PITCH_WIDTH_M
from v2engine.trace import ShotEvent

BOX_DEPTH_M, BOX_HALF_WIDTH_M = 16.5, 20.16
ROWS: list[dict] = []


def _lat(p, a, b):
    """(distance latérale de p au segment a-b, fraction le long du segment)."""
    dx, dy = b.x - a.x, b.y - a.y
    L2 = dx * dx + dy * dy
    t = ((p.x - a.x) * dx + (p.y - a.y) * dy) / L2
    cx, cy = a.x + t * dx, a.y + t * dy
    return math.hypot(p.x - cx, p.y - cy), t


def _in_triangle(p, a, b, c):
    def s(p1, p2, p3):
        return (p1.x - p3.x) * (p2.y - p3.y) - (p2.x - p3.x) * (p1.y - p3.y)
    d1, d2, d3 = s(p, a, b), s(p, b, c), s(p, c, a)
    neg, pos = (d1 < 0) or (d2 < 0) or (d3 < 0), (d1 > 0) or (d2 > 0) or (d3 > 0)
    return not (neg and pos)


def _capture(*args, **kw):
    ev = ShotEvent(*args, **kw)
    f = sys._getframe(1)
    loc = dict(f.f_back.f_locals) if f.f_code.co_name == "record" else {}
    loc.update(f.f_locals)
    holder = loc.get("holder") or loc.get("taker")
    players, goal = loc.get("players"), loc.get("goal")
    intentions = None
    g = f
    while g is not None and intentions is None:
        intentions = g.f_locals.get("intentions") if isinstance(g.f_locals.get("intentions"), dict) else None
        g = g.f_back
    if holder is None or players is None or goal is None or ev.origin == "penalty":
        return ev
    sp = holder.position
    dist = math.hypot(sp.x - goal.x, sp.y - goal.y)
    box = abs(sp.x - goal.x) <= BOX_DEPTH_M and abs(sp.y - goal.y) <= BOX_HALF_WIDTH_M
    half = GOAL_WIDTH_M / 2.0
    p1, p2 = M.Vec2(goal.x, goal.y - half), M.Vec2(goal.x, goal.y + half)
    opp = [p for p in players if p.team != holder.team and p.poste != "GK"]
    ds = sorted((p.position.distance_to(sp), p) for p in opp)
    near_d, near = ds[0] if ds else (99.0, None)
    cone = [p for p in opp if _in_triangle(p.position, sp, p1, p2)]
    on_line = []
    for p in opp:
        lat, t = _lat(p.position, sp, goal)
        if 0.0 < t < 1.0 and lat <= 1.0:
            on_line.append(p.position.distance_to(sp))
    presser = None
    if intentions:
        for p in opp:
            it = intentions.get(p.name)
            if it is not None and it.action == "presser" and it.mate == holder.name:
                presser = p.position.distance_to(sp)
    it_near = intentions.get(near.name) if (intentions and near is not None) else None
    ROWS.append({"minute": ev.minute, "équipe": ev.team, "distance": dist, "surface": box,
                 "axe (m)": abs(sp.y - goal.y), "issue": ev.outcome, "origine": ev.origin, "xg": ev.xg,
                 "qualité": ev.quality, "plus proche (m)": near_d,
                 "intention du plus proche": (it_near.role, it_near.action) if it_near else None,
                 "rôle du plus proche": near.role if near else None,
                 "dans le cône": len(cone), "sur la ligne (m)": sorted(on_line),
                 "presseur (m)": presser, "à 5 m": sum(d <= 5.0 for d, _ in ds),
                 "coup franc": ev.origin == "coup franc"})
    return ev


def one(i: int) -> dict:
    ROWS.clear()
    M.ShotEvent = _capture
    from scripts.v2_chain import play
    trace = play(i)
    rows = [dict(r, match=i) for r in ROWS]
    # issue finale : appariement avec la trace (même ordre, hors penalty)
    shots = [s for s in trace.shots if s.origin != "penalty"]
    for r, s in zip(rows, shots):
        r["issue"] = s.outcome
    return {"tirs": rows, "buts": [trace.home_goals, trace.away_goals]}


if __name__ == "__main__":
    n, procs, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    with ProcessPoolExecutor(max_workers=procs) as pool:
        res = list(pool.map(one, range(n)))
    with open(out, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False)
    print("ok", n, sum(sum(r["buts"]) for r in res))

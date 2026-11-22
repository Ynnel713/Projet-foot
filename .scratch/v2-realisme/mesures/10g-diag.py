"""Diagnostic du ticket v2-realisme/10g (hors dépôt, lecture seule) : à chaque passe décidée vers un receveur dans la
surface adverse, état de la défense lu sur la pile d'appel (rôles de `DefensiveRoles`, positions) : receveur marqué
(rôle `marquage` sur lui), distance de son plus proche défenseur de champ, attaquants dans la surface et combien sont
marqués ou à 2 m ou moins d'un défenseur, rôle du plus proche. Mêmes graines et affiches que le banc.
Usage : PYTHONPATH=. PYTHONHASHSEED=0 uv run python .scratch/v2-realisme/mesures/10g-diag.py <matchs> <processus> <sortie.json>"""
from __future__ import annotations

import json
import sys
from collections import Counter
from concurrent.futures import ProcessPoolExecutor

from v2engine import match as M
from v2engine.defense import MARQUAGE, own_goal

ROWS: list[dict] = []
_orig = M._record_decision


def _box(p, goal) -> bool:
    return abs(p.position.x - goal.x) <= 16.5 and abs(p.position.y - goal.y) <= 20.16


def _wrap(decisions, memory, holder, rivals, action, now_s, set_piece):
    target = getattr(action, "target", None)
    if action.kind == "pass" and target is not None and not set_piece:
        f = sys._getframe(1)
        defense = players = None
        while f is not None and (defense is None or players is None):
            defense = defense or (f.f_locals.get("defense") if hasattr(f.f_locals.get("defense"), "assignments") else None)
            players = players or f.f_locals.get("players")
            f = f.f_back
        goal = own_goal("away" if holder.team == "home" else "home")
        if defense is not None and players is not None and _box(target, goal):
            defs = [p for p in players if p.team != holder.team and p.poste != "GK"]
            marked = {a.mate for a in defense.assignments.values() if a.role == MARQUAGE}
            att = [p for p in players if p.team == holder.team and p.poste != "GK" and p.name != holder.name and _box(p, goal)]
            near = min(defs, key=lambda d: d.position.distance_to(target.position))
            role = defense.assignments.get(near.name)
            ROWS.append({"minute": now_s / 60.0, "receveur marqué": target.name in marked,
                         "plus proche (m)": near.position.distance_to(target.position),
                         "rôle du plus proche": role.role if role else "aucun",
                         "attaquants dans la surface": len(att),
                         "attaquants marqués": sum(p.name in marked for p in att),
                         "attaquants à 2 m d'un défenseur": sum(any(d.position.distance_to(p.position) <= 2.0 for d in defs) for p in att),
                         "défenseurs de champ dans la surface": sum(_box(d, goal) for d in defs),
                         "rôles des défenseurs dans la surface": dict(Counter((defense.assignments[d.name].role if d.name in defense.assignments else "aucun") for d in defs if _box(d, goal)))})
    return _orig(decisions, memory, holder, rivals, action, now_s, set_piece)


def one(i: int) -> dict:
    from scripts.v2_chain import play
    ROWS.clear()
    M._record_decision = _wrap
    trace = play(i)
    return {"match": i, "passes": list(ROWS), "score": [trace.home_goals, trace.away_goals],
            "tirs surface": sum(1 for s in trace.shots if abs(s.x - (0.0 if s.x < 52.5 else 105.0)) <= 16.5 and abs(s.y - 34.0) <= 20.16)}


if __name__ == "__main__":
    n, procs, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    with ProcessPoolExecutor(max_workers=procs) as pool:
        rows = list(pool.map(one, range(n)))
    json.dump(rows, open(out, "w", encoding="utf-8"), ensure_ascii=False)
    print("ok", n, sum(len(r["passes"]) for r in rows))

"""Mesure préalable du ticket v2-realisme/18m (hors dépôt, lecture seule) : à chaque décision du porteur hors de la
surface avec un tir possible, valeur réelle du tir et de la meilleure autre option (passe, conduite), et option choisie.
Sert à proposer la marge de la frappe hors surface. Usage :
PYTHONPATH=. PYTHONHASHSEED=0 uv run python .scratch/v2-realisme/mesures/18m-marges.py <matchs> <processus> <sortie.json>"""
from __future__ import annotations

import json
import sys
from concurrent.futures import ProcessPoolExecutor

from scripts.v2_chain import play
from v2engine import decision, match
from v2engine.geometry import in_penalty_area


def one(i: int) -> list[dict]:
    rows, last = [], {}
    orig_eval, orig_choose = decision.evaluate_options, match.choose_action

    def ev(*a, **k):
        last["o"] = orig_eval(*a, **k)
        return last["o"]

    def ch(holder, players, goal, *a, **k):
        chosen = orig_choose(holder, players, goal, *a, **k)
        opts = last.get("o") or []
        shots = [o.value for o in opts if o.kind == "shot"]
        if shots and not in_penalty_area(holder.team, holder.position):
            others = [o.value for o in opts if o.kind != "shot"]
            rows.append({"d": holder.position.distance_to(goal), "shot": shots[0],
                         "other": max(others) if others else None, "kind": chosen.kind,
                         "ls": holder.attributes.get("Long Shots") if hasattr(holder, "attributes") else None})
        return chosen

    decision.evaluate_options, match.choose_action = ev, ch
    try:
        play(i)
    finally:
        decision.evaluate_options, match.choose_action = orig_eval, orig_choose
    return rows


if __name__ == "__main__":
    n, procs, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    with ProcessPoolExecutor(max_workers=procs) as pool:
        rows = [r for part in pool.map(one, range(n)) for r in part]
    with open(out, "w", encoding="utf-8") as f:
        json.dump(rows, f)
    print("ok", len(rows))

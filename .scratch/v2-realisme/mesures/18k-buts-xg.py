"""Ticket 18k : buts contre xG neutre par zone (surface / hors surface) sur les sorties de `18e-zones.py`.
Usage : uv run python .scratch/v2-realisme/mesures/18k-buts-xg.py DOSSIER [DOSSIER...]"""
import glob
import json
import math
import sys

sys.path.insert(0, ".")
from v2engine.geometry import Vec2, in_penalty_area

for d in sys.argv[1:]:
    R = [r for f in sorted(glob.glob(f"{d}/lot*.json")) for r in json.load(open(f)) if r["origin"] != "penalty"]
    for name, sel in (("surface", True), ("hors surface", False)):
        S = [r for r in R if in_penalty_area(r["team"], Vec2(r["x"], r["y"])) == sel]
        goals = sum(r["outcome"] == "but" for r in S)
        xg = sum(r["xg"] or 0.0 for r in S)
        var = sum((r["xg"] or 0.0) * (1 - (r["xg"] or 0.0)) for r in S)
        print(f"{d:<46} {name:<13} tirs {len(S):5d}  buts {goals:4d}  xG {xg:6.1f}  écart {(goals - xg) / math.sqrt(var):+5.2f} σ"
              f"  conversion {100 * goals / len(S):5.1f} %")

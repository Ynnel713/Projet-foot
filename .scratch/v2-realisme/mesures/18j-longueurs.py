"""Réussite des passes de jeu par longueur (ticket 18j), sur la sortie de `18i-diag-script.py` : réussie = un coéquipier
touche le ballon le premier (définition du 18i). Usage : uv run python .scratch/v2-realisme/mesures/18j-longueurs.py DOSSIER"""
import glob
import json
import sys

R = [r for f in sorted(glob.glob(f"{sys.argv[1]}/lot*.json")) for r in json.load(open(f))]
for name, lo, hi in (("courte (< 13,7 m)", 0, 13.7), ("moyenne", 13.7, 27.4), ("longue (>= 27,4 m)", 27.4, 1e9),
                     ("toutes", 0, 1e9)):
    S = [r for r in R if lo <= r["L"] < hi]
    ok = sum(1 for r in S if r.get("first") and r["first_team"] == r["team"])
    opp = sum(1 for r in S if r.get("first") and r["first_team"] != r["team"])
    acc = [r for r in S if r["acc"]]
    ok_acc = sum(1 for r in acc if r.get("first") and r["first_team"] == r["team"])
    print(f"{name:<20} n {len(S):6d}  réussie {100 * ok / len(S):5.1f} %  chez l'adversaire {100 * opp / len(S):5.1f} %"
          f"  précises réussies {100 * ok_acc / max(1, len(acc)):5.1f} %")

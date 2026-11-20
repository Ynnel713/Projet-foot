"""Contrôle du ticket v2-realisme/18n sur des matchs JOUÉS avec le moteur modifié (chance évaluée enregistrée au départ de
chaque passe par `18m-diag-script.py`) : calibration en 7 tranches (critère du propriétaire : au plus 4 points par tranche
d'au moins 500 passes, moyenne à 0,5 point), par longueur (critère du ticket : moins de 1 point sous 15 m et de 15 à
30 m), par Passing. Données : `18m-diag-script.py 12 2400 > D/ctrl-2400.json` (puis 2412, 2424, 2436 : 48 matchs).
Usage : python .scratch/v2-realisme/mesures/18n-controle.py D/ctrl-24*.json"""
import json
import math
import sys
from collections import defaultdict

R = [r for p in sys.argv[1:] for r in json.load(open(p))]


def lost(r):
    if r.get("first"):
        return r["first_team"] != r["team"]
    return bool(r.get("out")) and r.get("out_team") != r["team"]


def line(name, S):
    p = sum(r["chance"] for r in S) / len(S)
    o = sum(not lost(r) for r in S) / len(S)
    se = 1.96 * math.sqrt(o * (1 - o) / len(S))
    print(f"  {name:<22} n {len(S):6d}  évaluée {p:.3f}  non perdue {o:.3f} ± {se:.3f}  écart {100 * (p - o):+.1f}")
    return p - o


print(f"{len(R)} passes de jeu au sol")
bins = defaultdict(list)
for r in R:
    bins[min(6, int(r["chance"] * 7))].append(r)
worst = 0.0
for b in sorted(bins):
    d = line(f"[{b / 7:.2f} ; {(b + 1) / 7:.2f}[", bins[b])
    if len(bins[b]) >= 500:
        worst = max(worst, abs(d))
line("toutes", R)
print(f"  pire tranche (n >= 500) : {100 * worst:.1f} points")
for lo, hi in ((0, 8), (0, 15), (8, 15), (15, 30), (30, 99)):
    line(f"longueur {lo} à {hi} m", [r for r in R if lo <= r["L"] < hi])
for name, sel in (("Passing < 50", lambda r: r["passing"] < 50), ("Passing 50 à 70", lambda r: 50 <= r["passing"] < 70),
                  ("Passing >= 70", lambda r: r["passing"] >= 70)):
    line(name, [r for r in R if sel(r)])

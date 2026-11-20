"""Contrôle du ticket v2-realisme/18o sur des matchs JOUÉS avec le moteur modifié (`18o-diag-script.py 12 2500`, puis
2512, 2524, 2536 : 48 matchs). Critère 1 : adversaire à moins de 1,5 m du receveur, entre le passeur et lui (avancée dans
le trajet), écart évaluée / non perdue à moins de 4 points. Critère 2 (18n) : au plus 4 points par tranche d'au moins 500
passes (7 tranches), moyenne à 0,5 point, moins de 15 m et 15 à 30 m à moins de 1 point. Pour suivi : Passing, position
de l'adversaire le plus proche du receveur.
Usage : python .scratch/v2-realisme/mesures/18o-controle.py D/ctrl-25*.json"""
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
    if not S:
        return 0.0
    p = sum(r["chance"] for r in S) / len(S)
    o = sum(not lost(r) for r in S) / len(S)
    se = 1.96 * math.sqrt(o * (1 - o) / len(S))
    print(f"  {name:<34} n {len(S):6d}  évaluée {p:.3f}  non perdue {o:.3f} ± {se:.3f}  écart {100 * (p - o):+.1f}")
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
print("Critère 1 : adversaire près du receveur, entre le passeur et lui")
line("à moins de 1,5 m", [r for r in R if any(o["to_recv"] < 1.5 and 0 < o["along"] < r["L"] for o in r["opp"])])
line("à moins de 1,5 m, sur la ligne (< 0,5 m)",
     [r for r in R if any(o["to_recv"] < 1.5 and 0 < o["along"] < r["L"] and o["gap"] < 0.5 for o in r["opp"])])
line("à moins de 2,5 m", [r for r in R if any(o["to_recv"] < 2.5 and 0 < o["along"] < r["L"] for o in r["opp"])])

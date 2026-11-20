"""Diagnostic du ticket v2-realisme/18o, quatrième passe : coupe et perte hors coupe, prévues / observées, selon l'écart
latéral réalisé au receveur (L x tan|angle réalisé|), par tranche de Passing ; et Passing < 50 selon la pression.
Usage : python .scratch/v2-realisme/mesures/18o-diagnostic-4.py D/rec-24*.json"""
import json
import math
import sys

R = [r for p in sys.argv[1:] for r in json.load(open(p))]
SHARES = (0.99, 0.99, 0.98, 0.80)


def lost(r):
    if r.get("first"):
        return r["first_team"] != r["team"]
    return bool(r.get("out")) and r.get("out_team") != r["team"]


def cut_obs(r):
    return bool(r.get("first")) and r["first_team"] != r["team"] and any(o["n"] == r["first"] and o["cut"] > 0 for o in r["opp"])


def line(name, S):
    if len(S) < 30:
        return
    n = len(S)
    o = sum(not lost(r) for r in S) / n
    p = sum(r["chance"] for r in S) / n
    pc = sum(1 - r["keep"] for r in S) / n
    oc = sum(cut_obs(r) for r in S) / n
    po = sum(r["keep"] * (1 - sum(w * s for w, s in zip(r["w"], SHARES))) for r in S) / n
    oo = sum(lost(r) and not cut_obs(r) for r in S) / n
    print(f"  {name:<30} n {n:6d}  écart {100 * (p - o):+5.1f} ± {196 * math.sqrt(o * (1 - o) / n):.1f}"
          f" | coupe prév {100 * pc:4.1f} obs {100 * oc:4.1f} | hors coupe prév {100 * po:4.1f} obs {100 * oo:4.1f}")


def dev(r):
    return r["L"] * math.tan(math.radians(abs(r["ang_deg"])))


for lo, hi in ((0, 50), (50, 70), (70, 100)):
    print(f"Passing {lo}-{hi}")
    for a, b in ((0, 0.5), (0.5, 1.0), (1.0, 2.0), (2.0, 4.0), (4.0, 99)):
        line(f"écart latéral {a}-{b} m", [r for r in R if lo <= r["passing"] < hi and a <= dev(r) < b])
print("Passing < 50, écart-type d'angle (pression comprise)")
for a, b in ((0, 5), (5, 6.5), (6.5, 8), (8, 99)):
    line(f"sigma {a}-{b}°", [r for r in R if r["passing"] < 50 and a <= r["sigma_deg"] < b])


def base_sigma(p):
    pts = ((11.0, 6.0), (55.0, 3.0), (99.0, 1.5))
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        if p <= x1:
            return y0 + (y1 - y0) * (max(p, x0) - x0) / (x1 - x0)
    return pts[-1][1]


print("Pression sur le passeur (sigma / sigma sans pression), hors première et talonnade")
for lo, hi in ((0, 50), (50, 70), (70, 100)):
    print(f" Passing {lo}-{hi}")
    for a, b in ((1.0, 1.0001), (1.0001, 1.25), (1.25, 1.5), (1.5, 9)):
        line(f"gêne x{a:.2f}-{b:.2f}", [r for r in R if lo <= r["passing"] < hi and not r["ot"] and not r["bh"]
                                       and a <= r["sigma_deg"] / base_sigma(r["passing"]) < b])
print("Vitesse du receveur au départ (dosage : le passeur faible joue où il est, pas où il va)")
for lo, hi in ((0, 50), (50, 70), (70, 100)):
    print(f" Passing {lo}-{hi}")
    for a, b in ((0, 1), (1, 3), (3, 5), (5, 99)):
        line(f"receveur {a}-{b} m/s", [r for r in R if lo <= r["passing"] < hi and a <= r["rv"] < b])
print("Adversaires de la table : coupe prévue / observée selon leur vitesse vers la ligne de passe (close, m/s)")
from collections import defaultdict
for lo, hi in ((0, 50), (50, 70), (70, 100)):
    rows = defaultdict(lambda: [0, 0.0, 0])
    for r in R:
        if not lo <= r["passing"] < hi:
            continue
        for o in sorted((o for o in r["opp"] if o["cut"] > 0), key=lambda o: o["along"]):
            k = next(i for i, b in enumerate((-1, 1, 3, 99)) if o["close"] < b)
            rows[k][0] += 1
            rows[k][1] += o["cut"]
            rows[k][2] += r.get("first") == o["n"]
            if r.get("first") and any(q["n"] == r["first"] and q["along"] <= o["along"] for q in r["opp"]):
                break
    tot = sum(v[0] for v in rows.values())
    print(f" Passing {lo}-{hi}")
    for k in sorted(rows):
        n, pc, oc = rows[k]
        print(f"  vers la ligne {('< -1', '-1 à 1', '1 à 3', '> 3')[k]:<7} part {n / tot:.2f} n {n:6d}  coupe prévue {pc / n:.3f} observée {oc / n:.3f}")

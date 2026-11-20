"""Diagnostic du ticket v2-realisme/18o sur les matchs joués du contrôle du 18n (`18m-diag-script.py`, graines 2400 à
2447). (1) Passing : écart évaluée / non perdue par tranche de Passing, croisé avec la longueur, et décomposé en coupe
(adversaire de la table qui touche le premier) et perte hors coupe (écart, sortie, adversaire hors table), prévues contre
observées. (2) Adversaires près du receveur : par distance au receveur et position (devant, à côté, derrière).
Usage : python .scratch/v2-realisme/mesures/18o-diagnostic.py D/ctrl-24*.json"""
import json
import math
import sys
from collections import defaultdict

R = [r for p in sys.argv[1:] for r in json.load(open(p))]
SHARES = (0.99, 0.99, 0.98, 0.80)


def lost(r):
    if r.get("first"):
        return r["first_team"] != r["team"]
    return bool(r.get("out")) and r.get("out_team") != r["team"]


def cut_obs(r):
    """Perdue par un adversaire de la table (coupe > 0) qui touche le premier."""
    if not r.get("first") or r["first_team"] == r["team"]:
        return False
    return any(o["n"] == r["first"] and o["cut"] > 0 for o in r["opp"])


def ci(o, n):
    return 1.96 * math.sqrt(max(o * (1 - o), 1e-4) / n)


def line(name, S):
    if not S:
        return
    n = len(S)
    p = sum(r["chance"] for r in S) / n
    o = sum(not lost(r) for r in S) / n
    pc = sum(1 - r["keep"] for r in S) / n
    oc = sum(cut_obs(r) for r in S) / n
    nl = [sum(w * s for w, s in zip(r["w"], SHARES)) for r in S]
    po = sum(r["keep"] * (1 - x) for r, x in zip(S, nl)) / n
    oo = sum(lost(r) and not cut_obs(r) for r in S) / n
    prec = sum(r["w"][0] for r in S) / n
    print(f"  {name:<30} n {n:6d}  év {p:.3f} obs {o:.3f}  écart {100 * (p - o):+5.1f} ± {100 * ci(o, n):.1f}"
          f" | coupe prév {100 * pc:4.1f} obs {100 * oc:4.1f} | hors coupe prév {100 * po:4.1f} obs {100 * oo:4.1f}"
          f" | précise {prec:.2f}")


print(f"{len(R)} passes de jeu au sol\n\n(1) Passing")
PB = ((0, 50), (50, 60), (60, 70), (70, 80), (80, 100))
for lo, hi in PB:
    line(f"Passing {lo}-{hi}", [r for r in R if lo <= r["passing"] < hi])
for lo, hi in ((0, 8), (8, 15), (15, 30), (30, 99)):
    print(f" longueur {lo}-{hi} m")
    for plo, phi in ((0, 50), (50, 70), (70, 100)):
        line(f"  Passing {plo}-{phi}", [r for r in R if lo <= r["L"] < hi and plo <= r["passing"] < phi])
print(" Passing < 50, par poids de la bande précise (part de passe précise prévue)")
for lo, hi in ((0, .5), (.5, .8), (.8, .95), (.95, 1.01)):
    line(f"  précise {lo}-{hi}", [r for r in R if r["passing"] < 50 and lo <= r["w"][0] < hi])
print(" Passing >= 70, idem")
for lo, hi in ((0, .5), (.5, .8), (.8, .95), (.95, 1.01)):
    line(f"  précise {lo}-{hi}", [r for r in R if r["passing"] >= 70 and lo <= r["w"][0] < hi])
print(" passe de première / talonnade (Passing < 50)")
line("  de première", [r for r in R if r["passing"] < 50 and r["ot"]])
line("  normale", [r for r in R if r["passing"] < 50 and not r["ot"] and not r["bh"]])
print(" sans adversaire de la table (keep = 1)")
for lo, hi in PB:
    line(f"  Passing {lo}-{hi}", [r for r in R if lo <= r["passing"] < hi and r["keep"] >= 0.9999])


def near(r, dmax):
    """Adversaire le plus proche du receveur, s'il est à moins de dmax."""
    c = [o for o in r["opp"] if o["to_recv"] < dmax]
    return min(c, key=lambda o: o["to_recv"]) if c else None


def where(r, o):
    rel = o["along"] - r["L"]
    if rel < -0.5 and o["gap"] < o["to_recv"] * 0.75:
        return "devant"
    if rel > 0.5:
        return "derrière"
    return "à côté"


print("\n(2) Adversaire le plus proche du receveur")
for lo, hi in ((0, 0.75), (0.75, 1.5), (1.5, 2.5), (2.5, 4.0), (4.0, 99)):
    S = [r for r in R if (o := near(r, 99)) and lo <= o["to_recv"] < hi]
    line(f"distance {lo}-{hi} m", S)
    for w in ("devant", "à côté", "derrière"):
        line(f"  {w}", [r for r in S if where(r, near(r, 99)) == w])
print(" moins de 1,5 m, devant, par écart à la ligne")
S = [r for r in R if (o := near(r, 1.5)) and where(r, o) == "devant"]
for lo, hi in ((0, 0.5), (0.5, 1.0), (1.0, 2.0)):
    line(f"  écart {lo}-{hi} m", [r for r in S if lo <= near(r, 1.5)["gap"] < hi])
print(" moins de 1,5 m, devant : qui touche le premier")
cnt = defaultdict(int)
for r in S:
    o = near(r, 1.5)
    if r.get("first") == r["recv"]:
        cnt["receveur"] += 1
    elif r.get("first") == o["n"]:
        cnt["cet adversaire"] += 1
    elif r.get("first") and r["first_team"] != r["team"]:
        cnt["autre adversaire"] += 1
    elif r.get("first"):
        cnt["autre coéquipier"] += 1
    else:
        cnt["sorti / mort"] += 1
print("  ", dict(cnt), " coupe prévue de cet adversaire :", round(sum(near(r, 1.5)["cut"] for r in S) / len(S), 3),
      " dt_aim moyen", round(sum(near(r, 1.5)["dt_aim"] for r in S) / len(S), 2))
print(" moins de 1,5 m, devant, par dt_aim (adversaire - receveur au point visé, s)")
for lo, hi in ((-9, -0.2), (-0.2, 0.0), (0.0, 0.2), (0.2, 9)):
    line(f"  dt {lo}-{hi}", [r for r in S if lo <= near(r, 1.5)["dt_aim"] < hi])
print(" moins de 1,5 m, devant, par temps : longueur")
for lo, hi in ((0, 10), (10, 20), (20, 99)):
    line(f"  L {lo}-{hi}", [r for r in S if lo <= r["L"] < hi])

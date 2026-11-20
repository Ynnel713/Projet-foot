"""Diagnostic du ticket v2-realisme/18o, deuxième passe, sur les enregistrements enrichis (`18o-diag-script.py`, graines
2400 à 2447, moteur du commit 0651cf3). (1) Passing : par poste du passeur ; erreur de vitesse réalisée (`v_ratio`) et
d'angle (`ang_deg` contre `sigma_deg`) ; perte selon l'erreur de vitesse. (2) Adversaire près du receveur : coupe
prévue / observée selon la course du receveur vers le ballon (`rv_back`) et le temps du ballon.
Usage : python .scratch/v2-realisme/mesures/18o-diagnostic-2.py D/rec-24*.json"""
import json
import math
import sys
from collections import defaultdict

R = [r for p in sys.argv[1:] for r in json.load(open(p))]
SHARES = (0.99, 0.99, 0.98, 0.80)
F = math.log(0.6)


def lost(r):
    if r.get("first"):
        return r["first_team"] != r["team"]
    return bool(r.get("out")) and r.get("out_team") != r["team"]


def cut_by(r, o):
    return r.get("first") == o["n"]


def cut_obs(r):
    return bool(r.get("first")) and r["first_team"] != r["team"] and any(o["n"] == r["first"] and o["cut"] > 0 for o in r["opp"])


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
    se = 196 * math.sqrt(max(o * (1 - o), 1e-4) / n)
    print(f"  {name:<28} n {n:6d}  év {p:.3f} obs {o:.3f}  écart {100 * (p - o):+5.1f} ± {se:.1f}"
          f" | coupe prév {100 * pc:4.1f} obs {100 * oc:4.1f} | hors coupe prév {100 * po:4.1f} obs {100 * oo:4.1f}")


def sd(xs):
    m = sum(xs) / len(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / len(xs))


print(f"{len(R)} passes de jeu au sol")
print("\n(1a) par poste du passeur, Passing < 50 puis tous")
for pp in sorted({r["pp"] for r in R}):
    line(f"{pp}, Passing < 50", [r for r in R if r["pp"] == pp and r["passing"] < 50])
for pp in sorted({r["pp"] for r in R}):
    line(f"{pp}, tous", [r for r in R if r["pp"] == pp])
print("\n(1b) erreurs réalisées par tranche de Passing (hors première et talonnade)")
for lo, hi in ((0, 50), (50, 60), (60, 70), (70, 80), (80, 100)):
    S = [r for r in R if lo <= r["passing"] < hi and not r["ot"] and not r["bh"]]
    z = [r["ang_deg"] / r["sigma_deg"] for r in S if r["sigma_deg"] > 0]
    print(f"  Passing {lo}-{hi}  n {len(S):6d}  vitesse réalisée/idéale : moy {sum(r['v_ratio'] for r in S) / len(S):.3f}"
          f" é-t {sd([r['v_ratio'] for r in S]):.3f} | angle/sigma é-t {sd(z):.3f} | sigma moy {sum(r['sigma_deg'] for r in S) / len(S):.2f}°")
print("\n(1c) perte selon l'erreur de vitesse (tous Passing), coupe et hors coupe")
for lo, hi in ((0, 0.8), (0.8, 0.9), (0.9, 0.97), (0.97, 1.03), (1.03, 1.1), (1.1, 1.2), (1.2, 9)):
    line(f"vitesse {lo}-{hi}", [r for r in R if lo <= r["v_ratio"] < hi])
print(" Passing < 50")
for lo, hi in ((0, 0.9), (0.9, 1.1), (1.1, 9)):
    line(f"  vitesse {lo}-{hi}", [r for r in R if lo <= r["v_ratio"] < hi and r["passing"] < 50])
print(" Passing >= 70")
for lo, hi in ((0, 0.9), (0.9, 1.1), (1.1, 9)):
    line(f"  vitesse {lo}-{hi}", [r for r in R if lo <= r["v_ratio"] < hi and r["passing"] >= 70])


def travel(L, along):
    v0 = min(30.0, 6.0 - L * F)
    at = max(0.5, v0 + along * F)  # BALL_STOPPED_MPS supposé 0,5 (même borne que le moteur ci-dessous vérifiée)
    return math.log(at / v0) / F


print("\n(2) adversaires de la table (coupe > 0) : coupe prévue / observée, par adversaire, selon la distance au receveur")
rows = defaultdict(lambda: [0, 0.0, 0])
for r in R:
    # ordre séquentiel : seuls les adversaires « atteints » (aucun plus près du passeur n'a touché avant) comptent
    for o in sorted((o for o in r["opp"] if o["cut"] > 0), key=lambda o: o["along"]):
        k = (min(4, int(o["to_recv"] / 1.0)), "devant" if o["along"] < r["L"] - 0.5 else "à côté")
        rows[k][0] += 1
        rows[k][1] += o["cut"]
        rows[k][2] += cut_by(r, o)
        if cut_by(r, o) or (r.get("first") and r["first"] != o["n"] and any(q["n"] == r["first"] and q["along"] < o["along"] for q in r["opp"])):
            break
for k in sorted(rows):
    n, pc, oc = rows[k]
    print(f"  receveur à {k[0]}-{k[0] + 1} m ({k[1]:<6}) n {n:6d}  coupe prévue {pc / n:.3f} observée {oc / n:.3f}  écart {100 * (pc - oc) / n:+5.1f}")
print("\n(2b) adversaire à moins de 2 m du receveur, de la table : selon la course du receveur vers le ballon (rv_back)")
rows = defaultdict(lambda: [0, 0.0, 0])
for r in R:
    for o in r["opp"]:
        if o["cut"] > 0 and o["to_recv"] < 2.0:
            k = -1 if r["rv_back"] < -1 else (0 if r["rv_back"] < 1 else (1 if r["rv_back"] < 3 else 2))
            rows[k][0] += 1
            rows[k][1] += o["cut"]
            rows[k][2] += cut_by(r, o)
for k in sorted(rows):
    n, pc, oc = rows[k]
    print(f"  rv_back classe {k:+d}  n {n:5d}  coupe prévue {pc / n:.3f} observée {oc / n:.3f}  écart {100 * (pc - oc) / n:+5.1f}")
print("\n(2c) adversaire à moins de 2 m du receveur, de la table : selon l'écart à la ligne et le temps du ballon")
rows = defaultdict(lambda: [0, 0.0, 0])
for r in R:
    for o in r["opp"]:
        if o["cut"] > 0 and o["to_recv"] < 2.0:
            t = travel(r["L"], o["along"])
            k = (0 if o["gap"] < 0.5 else (1 if o["gap"] < 1.0 else 2), 0 if t < 0.45 else (1 if t < 0.7 else (2 if t < 1.0 else 3)))
            rows[k][0] += 1
            rows[k][1] += o["cut"]
            rows[k][2] += cut_by(r, o)
for k in sorted(rows):
    n, pc, oc = rows[k]
    print(f"  écart cl {k[0]} temps cl {k[1]}  n {n:5d}  coupe prévue {pc / n:.3f} observée {oc / n:.3f}  écart {100 * (pc - oc) / n:+5.1f}")

print("\n(2d) adversaires de la table, estimateur séquentiel : selon le reste du trajet après lui (L - avancée) et l'écart")
rows = defaultdict(lambda: [0, 0.0, 0])
for r in R:
    for o in sorted((o for o in r["opp"] if o["cut"] > 0), key=lambda o: o["along"]):
        rest = r["L"] - o["along"]
        kr = next(i for i, b in enumerate((0.5, 1.0, 1.5, 2.0, 3.0, 5.0, 1e9)) if rest < b)
        kg = 0 if o["gap"] < 0.5 else (1 if o["gap"] < 1.0 else (2 if o["gap"] < 2.0 else 3))
        for k in ((kr, kg), (kr, 9)):
            rows[k][0] += 1
            rows[k][1] += o["cut"]
            rows[k][2] += cut_by(r, o)
        if r.get("first") and any(q["n"] == r["first"] and q["along"] <= o["along"] for q in r["opp"]):
            break
B = ("0-0,5", "0,5-1", "1-1,5", "1,5-2", "2-3", "3-5", "5+")
for k in sorted(rows):
    n, pc, oc = rows[k]
    g = "tous" if k[1] == 9 else ("<0,5", "0,5-1", "1-2", "2+")[k[1]]
    print(f"  reste {B[k[0]]:<6} m écart {g:<5} n {n:6d}  coupe prévue {pc / n:.3f} observée {oc / n:.3f}  rapport {oc / pc if pc else 0:.2f}")

"""Remesure de la table de coupe du 18g et des parts du 18h après la portée du receveur (ticket 18i), sur la sortie de
`18i-diag-script.py` (50 matchs, 4 lots). Ajustement sur les lots 0 et 2, contrôle sur les lots 1 et 3.
Perdue (définition du 18h) : un adversaire touche le ballon le premier, ou le ballon sort / est sifflé avec remise pour
l'adversaire. Usage : uv run python .scratch/v2-realisme/mesures/18i-ajustement.py DOSSIER"""
import json
import math
import sys
from collections import defaultdict

D = sys.argv[1]
NEAR_PASSER_M = 3.0
NEAR = [0.5, 1.0, 6.0]
PATH = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
CUR_NEAR = {0.5: 0.75, 1.0: 0.14, 6.0: 0.01}
CUR_PATH = {1.0: 0.31, 2.0: 0.16, 3.0: 0.07, 4.0: 0.04, 5.0: 0.02, 6.0: 0.01}
CUR_UNF, CUR_MISS = 0.05, {10.0: 0.78, math.inf: 0.64}


def load(ids):
    return [r for i in ids for r in json.load(open(f"{D}/lot{i}.json"))]


def lost(r):
    if r.get("first"):
        return r["first_team"] != r["team"]
    return bool(r.get("out")) and r.get("out_team") != r["team"]


def key(o, L):
    if not 0.0 < o["along"] < L:
        return None
    limits = NEAR if o["along"] <= NEAR_PASSER_M else PATH
    lim = next((x for x in limits if o["gap"] < x), None)
    return None if lim is None else ("près" if limits is NEAR else "trajet", lim)


def keep(r, near, path):
    k = 1.0
    for o in r["opp"]:
        b = key(o, r["L"])
        if b:
            k *= 1.0 - (near if b[0] == "près" else path)[b[1]]
    return k


def fit(R):
    n, hit = defaultdict(int), defaultdict(int)
    for r in R:
        if not r["acc"]:
            continue
        for o in r["opp"]:
            b = key(o, r["L"])
            if b:
                n[b] += 1
                hit[b] += r.get("first") == o["n"]
    near = {x: hit[("près", x)] / max(1, n[("près", x)]) for x in NEAR}
    path = {x: hit[("trajet", x)] / max(1, n[("trajet", x)]) for x in PATH}
    acc = [r for r in R if r["acc"]]
    unf = 1.0 - sum(not lost(r) for r in acc) / sum(keep(r, near, path) for r in acc)
    miss = {}
    for lo, hi in ((0.0, 10.0), (10.0, math.inf)):
        S = [r for r in R if not r["acc"] and lo <= r["L"] < hi]
        miss[hi] = sum(not lost(r) for r in S) / sum(keep(r, near, path) for r in S)
    return near, path, unf, miss, n


def check(R, near, path, unf, miss, label):
    def pred(r):
        k = keep(r, near, path)
        return k * (1.0 - unf) if r["acc"] else k * next(v for lim, v in sorted(miss.items()) if r["L"] < lim)
    print(f"  {label}")
    for name, sel in (("précises", lambda r: r["acc"]), ("imprécises", lambda r: not r["acc"]),
                      ("courtes (<13,7 m)", lambda r: r["L"] < 13.7), ("moyennes", lambda r: 13.7 <= r["L"] < 27.4),
                      ("longues", lambda r: r["L"] >= 27.4), ("toutes", lambda r: True)):
        S = [r for r in R if sel(r)]
        p = sum(map(pred, S)) / len(S)
        o = sum(not lost(r) for r in S) / len(S)
        print(f"    {name:<18} n {len(S):6d}  prévue {p:.3f}  non perdue {o:.3f}  écart {100 * (p - o):+.1f}")
    bins = defaultdict(list)
    for r in R:
        bins[min(9, int(pred(r) * 10))].append(r)
    for b in sorted(bins):
        S = bins[b]
        p = sum(map(pred, S)) / len(S)
        o = sum(not lost(r) for r in S) / len(S)
        print(f"    prévue [{b / 10:.1f} ; {(b + 1) / 10:.1f}[  n {len(S):6d}  prévue {p:.3f}  non perdue {o:.3f}  écart {100 * (p - o):+.1f}")


FIT, CTRL = load([0, 2]), load([1, 3])
near, path, unf, miss, n = fit(FIT)
print(f"Ajustement (lots 0 et 2) : {len(FIT)} passes ; contrôle (lots 1 et 3) : {len(CTRL)} passes")
print("  près du passeur :", {k: f"{v:.3f} (n {n[('près', k)]})" for k, v in near.items()})
print("  sur le trajet   :", {k: f"{v:.3f} (n {n[('trajet', k)]})" for k, v in path.items()})
print(f"  coupe imprévue : {unf:.3f} ; imprécise non perdue hors coupe : " + ", ".join(f"<{k} m {v:.3f}" for k, v in miss.items()))
n2, p2, u2, m2, _ = fit(CTRL)
print("  (contrôle ajusté seul : près", {k: round(v, 3) for k, v in n2.items()}, "trajet", {k: round(v, 3) for k, v in p2.items()},
      f"imprévue {u2:.3f}", {k: round(v, 3) for k, v in m2.items()}, ")")
check(CTRL, CUR_NEAR, CUR_PATH, CUR_UNF, CUR_MISS, "table actuelle (18g/18h), lots de contrôle")
check(CTRL, near, path, unf, miss, "table ajustée, lots de contrôle")

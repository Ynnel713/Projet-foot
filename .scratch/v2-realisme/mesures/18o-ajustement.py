"""Ajustement du ticket v2-realisme/18o sur les enregistrements enrichis (graines 2400 à 2447, moteur 0651cf3) : table de
coupe (distance à la trajectoire x temps du ballon) réestimée sur les seuls adversaires à au moins `REST_FULL_M` du bout
du trajet (le receveur), puis facteur par bande de reste du trajet sous ce seuil (observé / prévu par la nouvelle table).
Estimateur séquentiel du 18n : un adversaire compte s'il est atteint (aucun adversaire plus près du passeur n'a touché).
Puis contrôle EN ÉCHANTILLON de la chance recalculée (le contrôle hors échantillon se fait sur des matchs joués avec le
moteur modifié). Usage : python .scratch/v2-realisme/mesures/18o-ajustement.py D/rec-24*.json"""
import json
import math
import sys
from collections import defaultdict

sys.path.insert(0, ".")
import v2engine.possession as P

R = [r for p in sys.argv[1:] for r in json.load(open(p))]
SHARES = (0.99, 0.99, 0.98, 0.80)
F = math.log(P.BALL_FRICTION_PER_S)
GAPS = [lim for lim, _ in P._CUT_TABLE]
REST_FULL_M = 2.0
REST_BANDS = (0.5, 1.0, 1.5, 2.0)
GAP_SPLIT_M = 1.0  # facteur séparé pour les adversaires sur la ligne (écart < 1 m) et à côté


def cell(r, o):
    g = next((i for i, lim in enumerate(GAPS) if o["gap"] < lim), None)
    if g is None or not 0.0 < o["along"] < r["L"]:
        return None
    v0 = P._launch_speed(r["L"])
    at = max(P.BALL_STOPPED_MPS, v0 + o["along"] * F)
    t = math.log(at / v0) / F
    return g, next(i for i, lim in enumerate(P._CUT_TIME_S) if t < lim)


def reached(r):
    """Adversaires de la table atteints par le ballon, dans l'ordre du trajet, avec l'issue."""
    for o in sorted((o for o in r["opp"] if cell(r, o) is not None), key=lambda o: o["along"]):
        hit = r.get("first") == o["n"]
        yield o, hit
        if r.get("first") and any(q["n"] == r["first"] and q["along"] <= o["along"] for q in r["opp"]):
            return


cnt = defaultdict(lambda: [0, 0])
for r in R:
    for o, hit in reached(r):
        if r["L"] - o["along"] >= REST_FULL_M:
            c = cnt[cell(r, o)]
            c[0] += 1
            c[1] += hit
old = {(g, t): P._CUT_TABLE[g][1][t] for g in range(len(GAPS)) for t in range(len(P._CUT_TIME_S))}
new = {}
print(f"Table réestimée (reste >= {REST_FULL_M} m) : nouvelle (ancienne) [n] ; cases de moins de 40 adversaires gardées")
for g in range(len(GAPS)):
    cells = []
    for t in range(len(P._CUT_TIME_S)):
        n, h = cnt[(g, t)]
        new[(g, t)] = round(h / n, 2) if n >= 40 else old[(g, t)]
        cells.append(f"{new[(g, t)]:.2f}({old[(g, t)]:.2f})[{n}]")
    print(f"  < {GAPS[g]} m : " + " ".join(cells))

band = defaultdict(lambda: [0, 0.0, 0])
for r in R:
    for o, hit in reached(r):
        rest = r["L"] - o["along"]
        if rest < REST_FULL_M:
            b = (next(i for i, lim in enumerate(REST_BANDS) if rest < lim), int(o["gap"] >= GAP_SPLIT_M))
            band[b][0] += 1
            band[b][1] += new[cell(r, o)]
            band[b][2] += hit
factors = ([], [])
print("Facteur par bande de reste du trajet et classe d'écart (observée / prévue par la nouvelle table)")
for k in (0, 1):
    for b in range(len(REST_BANDS)):
        n, pc, oc = band[(b, k)]
        factors[k].append(round(oc / pc, 2))
        print(f"  écart {'< 1 m ' if k == 0 else '>= 1 m'} reste < {REST_BANDS[b]} m : n {n:5d}  prévue {pc / n:.3f}"
              f" observée {oc / n:.3f}  facteur {oc / pc:.2f}")


def chance(r, table, fac):
    keep = 1.0
    for o in r["opp"]:
        c = cell(r, o)
        if c is None:
            continue
        x = table[c]
        if fac:
            rest = r["L"] - o["along"]
            x *= next((f for lim, f in zip(REST_BANDS, fac[int(o["gap"] >= GAP_SPLIT_M)]) if rest < lim), 1.0)
        keep *= 1.0 - x
    return keep * sum(w * s for w, s in zip(r["w"], SHARES))


def lost(r):
    if r.get("first"):
        return r["first_team"] != r["team"]
    return bool(r.get("out")) and r.get("out_team") != r["team"]


def near(r):
    return any(o["to_recv"] < 1.5 and 0 < o["along"] < r["L"] for o in r["opp"])


print("Contrôle en échantillon : écart évaluée - non perdue (points), ancienne table / nouvelle table + facteur")
groups = [("toutes", lambda r: True), ("Passing < 50", lambda r: r["passing"] < 50),
          ("Passing >= 70", lambda r: r["passing"] >= 70), ("longueur < 15 m", lambda r: r["L"] < 15),
          ("longueur 15-30 m", lambda r: 15 <= r["L"] < 30), ("longueur >= 30 m", lambda r: r["L"] >= 30),
          ("adv. < 1,5 m du receveur", near)]
for name, sel in groups:
    S = [r for r in R if sel(r)]
    o = sum(not lost(r) for r in S) / len(S)
    a = sum(chance(r, old, None) for r in S) / len(S)
    b = sum(chance(r, new, factors) for r in S) / len(S)
    print(f"  {name:<26} n {len(S):6d}  {100 * (a - o):+5.1f} -> {100 * (b - o):+5.1f}")
worst = 0.0
bins = defaultdict(list)
for r in R:
    bins[min(6, int(chance(r, new, factors) * 7))].append(r)
for k in sorted(bins):
    S = bins[k]
    d = 100 * (sum(chance(r, new, factors) for r in S) / len(S) - sum(not lost(r) for r in S) / len(S))
    if len(S) >= 500:
        worst = max(worst, abs(d))
    print(f"  tranche {k}  n {len(S):6d}  écart {d:+5.1f}")
print(f"  pire tranche (n >= 500) : {worst:.1f} points")

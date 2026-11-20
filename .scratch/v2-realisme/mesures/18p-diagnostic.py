"""Diagnostic du ticket v2-realisme/18p sur les matchs du contrôle du 18o (`18o-diag-script.py`, graines 2600 à 2651,
moteur du commit 4c9e470). Chance recalculée hors ligne avec la table et les facteurs du moteur (`possession`), puis :
(A2) facteur du reste du trajet appliqué seulement si l'adversaire est plus près du bout que du passeur (`rest < along`) ;
(V) facteur selon la vitesse de l'adversaire vers la ligne de passe (`close`), estimé par classe (estimateur séquentiel) ;
effet sur Passing < 50, les longueurs, les tranches, l'adversaire près du receveur.
Usage : python .scratch/v2-realisme/mesures/18p-diagnostic.py D/ctrl-26*.json"""
import json
import math
import sys
from collections import defaultdict

sys.path.insert(0, ".")
import v2engine.possession as P

R = [r for p in sys.argv[1:] for r in json.load(open(p))]
SHARES = [s for _, s in P._LATERAL_NOT_LOST]
F = math.log(P.BALL_FRICTION_PER_S)
CLOSE = (-3.0, -1.0, 1.0, 3.0, 5.0, math.inf)  # bornes hautes des classes de vitesse vers la ligne (m/s)


def lost(r):
    if r.get("first"):
        return r["first_team"] != r["team"]
    return bool(r.get("out")) and r.get("out_team") != r["team"]


def table(r, o):
    row = next((c for lim, c in P._CUT_TABLE if o["gap"] < lim), None)
    if row is None or not 0.0 < o["along"] < r["L"]:
        return None
    v0 = P._launch_speed(r["L"])
    at = max(P.BALL_STOPPED_MPS, v0 + o["along"] * F)
    t = math.log(at / v0) / F
    return next(c for lim, c in zip(P._CUT_TIME_S, row) if t < lim)


def cut(r, o, a2=False, vel=None):
    c = table(r, o)
    if c is None:
        return 0.0
    rest = r["L"] - o["along"]
    if not a2 or rest < o["along"]:
        for lim, on, off in P._CUT_REST_FACTOR:
            if rest < lim:
                c *= on if o["gap"] < P.CUT_REST_GAP_M else off
                break
    if vel:
        c = min(1.0, c * vel[next(i for i, b in enumerate(CLOSE) if o["close"] < b)])
    return c


def chance(r, **kw):
    keep = 1.0
    for o in r["opp"]:
        keep *= 1.0 - cut(r, o, **kw)
    return keep * sum(w * s for w, s in zip(r["w"], SHARES))


def reached(r):
    for o in sorted((o for o in r["opp"] if table(r, o) is not None), key=lambda o: o["along"]):
        yield o, r.get("first") == o["n"]
        if r.get("first") and any(q["n"] == r["first"] and q["along"] <= o["along"] for q in r["opp"]):
            return


# vérification : chance recalculée contre chance enregistrée par le moteur
d = [abs(chance(r) - r["chance"]) for r in R]
print(f"{len(R)} passes ; chance recalculée - enregistrée : moyenne {sum(d) / len(d):.4f}, max {max(d):.3f}")

# (V) facteur par classe de vitesse vers la ligne (avec A2)
acc = defaultdict(lambda: [0, 0.0, 0])
for r in R:
    for o, hit in reached(r):
        k = next(i for i, b in enumerate(CLOSE) if o["close"] < b)
        acc[k][0] += 1
        acc[k][1] += cut(r, o, a2=True)
        acc[k][2] += hit
VEL = []
print("Facteur vitesse vers la ligne (observée / prévue, A2 compris)")
for k in range(len(CLOSE)):
    n, pc, oc = acc[k]
    VEL.append(round(oc / pc, 2))
    print(f"  classe < {CLOSE[k]:>4} m/s  n {n:6d}  prévue {pc / n:.3f} observée {oc / n:.3f}  facteur {oc / pc:.2f}")
print("  par Passing (observée / prévue)")
for lo, hi in ((0, 50), (50, 70), (70, 100)):
    acc2 = defaultdict(lambda: [0, 0.0, 0])
    for r in R:
        if lo <= r["passing"] < hi:
            for o, hit in reached(r):
                k = next(i for i, b in enumerate(CLOSE) if o["close"] < b)
                acc2[k][0] += 1
                acc2[k][1] += cut(r, o, a2=True)
                acc2[k][2] += hit
    print(f"   Passing {lo}-{hi} : " + "  ".join(f"{acc2[k][2] / acc2[k][1]:.2f}[{acc2[k][0]}]" for k in range(len(CLOSE))))


def near(r):
    return any(o["to_recv"] < 1.5 and 0 < o["along"] < r["L"] for o in r["opp"])


groups = [("toutes", lambda r: True), ("Passing < 50", lambda r: r["passing"] < 50),
          ("Passing 50-70", lambda r: 50 <= r["passing"] < 70), ("Passing >= 70", lambda r: r["passing"] >= 70),
          ("longueur < 8 m", lambda r: r["L"] < 8), ("longueur < 15 m", lambda r: r["L"] < 15),
          ("longueur 15-30 m", lambda r: 15 <= r["L"] < 30), ("longueur >= 30 m", lambda r: r["L"] >= 30),
          ("adv. < 1,5 m du receveur", near)]
VARS = (("moteur", {}), ("A2", {"a2": True}), ("A2 + vitesse", {"a2": True, "vel": VEL}))
print("\nÉcart évaluée - non perdue (points) : " + " | ".join(v for v, _ in VARS))
for name, sel in groups:
    S = [r for r in R if sel(r)]
    o = sum(not lost(r) for r in S) / len(S)
    se = 196 * math.sqrt(o * (1 - o) / len(S))
    vals = [100 * (sum(chance(r, **kw) for r in S) / len(S) - o) for _, kw in VARS]
    print(f"  {name:<26} n {len(S):6d} (± {se:.1f})  " + "  ".join(f"{v:+5.1f}" for v in vals))
for v, kw in VARS:
    bins = defaultdict(list)
    for r in R:
        bins[min(6, int(chance(r, **kw) * 7))].append(r)
    worst = max(abs(100 * (sum(chance(r, **kw) for r in S) - sum(not lost(r) for r in S)) / len(S))
                for S in bins.values() if len(S) >= 500)
    print(f"  pire tranche ({v}) : {worst:.1f}")

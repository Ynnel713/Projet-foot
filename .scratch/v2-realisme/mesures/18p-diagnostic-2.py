"""Diagnostic du ticket v2-realisme/18p, deuxième passe : attributs des adversaires (par leur nom, base des clubs) que la
table de coupe ignore. Coupe observée / prévue par adversaire (estimateur séquentiel) selon son Anticipation et sa Pace ;
Anticipation et Pace moyennes des adversaires de la table selon le Passing du passeur ; écart évaluée / non perdue par
Anticipation moyenne des adversaires proches de la ligne.
Usage : python .scratch/v2-realisme/mesures/18p-diagnostic-2.py D/ctrl-26*.json"""
import json
import math
import sys
from collections import defaultdict

sys.path.insert(0, ".")
import v2engine.possession as P
from ligue1sim.clubs import load_clubs
from ligue1sim.season import CLUBS_PATH
from v2engine.attributes import player_attribute

R = [r for p in sys.argv[1:] for r in json.load(open(p))]
A = {}
for club in load_clubs(CLUBS_PATH, "Ligue 1"):
    for pl in club.players:
        A[pl.name] = (player_attribute(pl, "Anticipation"), player_attribute(pl, "Pace"))
F = math.log(P.BALL_FRICTION_PER_S)


def lost(r):
    if r.get("first"):
        return r["first_team"] != r["team"]
    return bool(r.get("out")) and r.get("out_team") != r["team"]


def cut(r, o):
    row = next((c for lim, c in P._CUT_TABLE if o["gap"] < lim), None)
    if row is None or not 0.0 < o["along"] < r["L"]:
        return None
    v0 = P._launch_speed(r["L"])
    at = max(P.BALL_STOPPED_MPS, v0 + o["along"] * F)
    t = math.log(at / v0) / F
    c = next(c for lim, c in zip(P._CUT_TIME_S, row) if t < lim)
    rest = r["L"] - o["along"]
    for lim, on, off in P._CUT_REST_FACTOR:
        if rest < lim:
            return c * (on if o["gap"] < P.CUT_REST_GAP_M else off)
    return c


def reached(r):
    for o in sorted((o for o in r["opp"] if cut(r, o) is not None), key=lambda o: o["along"]):
        yield o, r.get("first") == o["n"]
        if r.get("first") and any(q["n"] == r["first"] and q["along"] <= o["along"] for q in r["opp"]):
            return


miss = sum(o["n"] not in A for r in R for o in r["opp"])
print(f"{len(R)} passes ; adversaires sans attributs trouvés : {miss}")
for idx, name, bands in ((0, "Anticipation", (45, 55, 65, 75, 101)), (1, "Pace", (55, 65, 75, 85, 101))):
    acc = defaultdict(lambda: [0, 0.0, 0])
    for r in R:
        for o, hit in reached(r):
            if o["n"] in A:
                k = next(i for i, b in enumerate(bands) if A[o["n"]][idx] < b)
                acc[k][0] += 1
                acc[k][1] += cut(r, o)
                acc[k][2] += hit
    print(f"Coupe observée / prévue selon l'{name} de l'adversaire")
    for k in sorted(acc):
        n, pc, oc = acc[k]
        print(f"  < {bands[k]:3d}  n {n:6d}  prévue {pc / n:.3f} observée {oc / n:.3f}  rapport {oc / pc:.2f}")
print("Adversaires de la table (atteints) : attributs moyens selon le Passing du passeur")
for lo, hi in ((0, 50), (50, 70), (70, 100)):
    v = [A[o["n"]] for r in R if lo <= r["passing"] < hi for o, _ in reached(r) if o["n"] in A]
    w = [cut(r, o) for r in R if lo <= r["passing"] < hi for o, _ in reached(r) if o["n"] in A]
    print(f"  Passing {lo}-{hi}  n {len(v):6d}  Anticipation {sum(a for a, _ in v) / len(v):.1f}  Pace {sum(p for _, p in v) / len(v):.1f}"
          f"  (pondérés par la coupe : {sum(a * c for (a, _), c in zip(v, w)) / sum(w):.1f} / {sum(p * c for (_, p), c in zip(v, w)) / sum(w):.1f})")

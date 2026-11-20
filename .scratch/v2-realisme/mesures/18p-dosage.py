"""Diagnostic du ticket v2-realisme/18p, cinquième passe : écart de dosage (part de la course du receveur que la passe ne
joue pas : vitesse du receveur x temps de vol x (1 - qualité du dosage), comme `possession.dosage_gap`) ; perte hors coupe
prévue (bandes) et observée selon cet écart, par Passing, pour les passes à l'angle juste (écart latéral réalisé sous 1 m)
et pour toutes.
Usage : python .scratch/v2-realisme/mesures/18p-dosage.py D/rec-26*.json"""
import json
import math
import sys

sys.path.insert(0, ".")
import v2engine.possession as P
from v2engine.attributes import success_probability

R = [r for p in sys.argv[1:] for r in json.load(open(p))]
F = math.log(P.BALL_FRICTION_PER_S)
SHARES = [s for _, s in P._LATERAL_NOT_LOST]


def lost(r):
    if r.get("first"):
        return r["first_team"] != r["team"]
    return bool(r.get("out")) and r.get("out_team") != r["team"]


def cut_obs(r):
    return bool(r.get("first")) and r["first_team"] != r["team"] and any(o["n"] == r["first"] and o["cut"] > 0 for o in r["opp"])


def dosage_gap(r):
    v0 = P._launch_speed(r["L"])
    arr = max(P.BALL_STOPPED_MPS, v0 + r["L"] * F)
    t = math.log(arr / v0) / F
    dq = success_probability(r["passing"], baseline=0.5, amplitude=0.5, min_prob=0.0, max_prob=1.0)
    return r["rv"] * t * (1.0 - dq)


def dev(r):
    return r["L"] * math.tan(math.radians(abs(r["ang_deg"])))


def line(name, S):
    if len(S) < 30:
        return
    n = len(S)
    pred = sum(r["keep"] * (1 - sum(w * s for w, s in zip(r["w"], SHARES))) for r in S) / n
    obs = sum(lost(r) and not cut_obs(r) for r in S) / n
    print(f"  {name:<24} n {n:6d}  perte hors coupe prévue {100 * pred:5.1f}  observée {100 * obs:5.1f}")


for title, sel0 in (("angle juste (écart latéral réalisé < 1 m)", lambda r: dev(r) < 1.0), ("toutes", lambda r: True)):
    print(f"Passes {title}, selon l'écart de dosage")
    for lo, hi in ((0, 50), (50, 70), (70, 100)):
        print(f" Passing {lo}-{hi}")
        for a, b in ((0, 0.5), (0.5, 1.0), (1.0, 2.0), (2.0, 4.0), (4.0, 99)):
            line(f"dosage {a}-{b} m", [r for r in R if lo <= r["passing"] < hi and sel0(r) and a <= dosage_gap(r) < b])

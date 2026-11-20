"""Diagnostic du ticket v2-realisme/18o, troisième passe : coupe prévue recalculée hors ligne (table du 18n) (a) avec la
vitesse de départ réalisée (`v_ratio`) au lieu de la vitesse idéale, (b) avec un facteur selon le reste du trajet après
l'adversaire (mesuré en 2d), (c) les deux ; écart à la non-perte observée par Passing et pour l'adversaire près du
receveur. Usage : python .scratch/v2-realisme/mesures/18o-diagnostic-3.py D/rec-24*.json"""
import json
import math
import sys

sys.path.insert(0, ".")
import v2engine.possession as P

R = [r for p in sys.argv[1:] for r in json.load(open(p))]
SHARES = (0.99, 0.99, 0.98, 0.80)
F = math.log(P.BALL_FRICTION_PER_S)
REST = ((0.5, 0.37), (1.0, 0.52), (1.5, 0.66), (2.0, 0.79))


def lost(r):
    if r.get("first"):
        return r["first_team"] != r["team"]
    return bool(r.get("out")) and r.get("out_team") != r["team"]


def cut(r, o, ratio, rest_f):
    if o["cut"] <= 0:
        return 0.0
    row = next((c for lim, c in P._CUT_TABLE if o["gap"] < lim), None)
    if row is None:  # écart arrondi à l'enregistrement, à la borne de la table
        return 0.0
    v0 = max(P.BALL_STOPPED_MPS, P._launch_speed(r["L"]) * ratio)
    at = max(P.BALL_STOPPED_MPS, v0 + o["along"] * F)  # même borne que le moteur
    t = math.log(at / v0) / F
    c = next(ch for lim, ch in zip(P._CUT_TIME_S, row) if t < lim)
    if rest_f:
        c *= next((f for lim, f in REST if r["L"] - o["along"] < lim), 1.0)
    return c


def chance(r, speed, rest_f):
    keep = 1.0
    for o in r["opp"]:
        keep *= 1.0 - cut(r, o, r["v_ratio"] if speed else 1.0, rest_f)
    return keep * sum(w * s for w, s in zip(r["w"], SHARES))


def near(r):
    return any(o["cut"] > 0 and o["to_recv"] < 1.5 and o["along"] < r["L"] for o in r["opp"])


groups = (("toutes", lambda r: True), ("Passing < 50", lambda r: r["passing"] < 50),
          ("Passing 50-70", lambda r: 50 <= r["passing"] < 70), ("Passing >= 70", lambda r: r["passing"] >= 70),
          ("longueur < 15 m", lambda r: r["L"] < 15), ("longueur 15-30 m", lambda r: 15 <= r["L"] < 30),
          ("adv. < 1,5 m du receveur", near))
for name, sel in groups:
    S = [r for r in R if sel(r)]
    o = sum(not lost(r) for r in S) / len(S)
    se = 196 * math.sqrt(o * (1 - o) / len(S))
    rec = sum(r["chance"] for r in S) / len(S)
    out = [sum(chance(r, s, f) for r in S) / len(S) for s, f in ((False, False), (True, False), (False, True), (True, True))]
    print(f"{name:<26} n {len(S):6d} obs {o:.3f} ± {se / 100:.3f} | écart : enregistrée {100 * (rec - o):+5.1f}  recalculée"
          f" {100 * (out[0] - o):+5.1f}  vitesse réalisée {100 * (out[1] - o):+5.1f}  facteur reste {100 * (out[2] - o):+5.1f}"
          f"  les deux {100 * (out[3] - o):+5.1f}")

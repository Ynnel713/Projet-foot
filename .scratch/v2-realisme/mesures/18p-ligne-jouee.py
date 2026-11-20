"""Diagnostic du ticket v2-realisme/18p, troisième passe : la coupe dépend-elle de la ligne JOUÉE (écart d'angle tiré,
`ang_deg`) plutôt que de la ligne idéale ? Chaque adversaire est replacé dans le repère de la ligne jouée (rotation de
`ang_deg` de son avancée et de son côté signé, `side`). Table de coupe (mêmes classes que le moteur : écart à la ligne x
temps du ballon, facteur du reste du trajet du 18o) réestimée sur les matchs pairs, sur la ligne idéale puis sur la ligne
jouée ; prévision contre observation sur les matchs impairs, par Passing et par longueur.
Usage : python .scratch/v2-realisme/mesures/18p-ligne-jouee.py D/rec-26*.json"""
import json
import math
import sys
from collections import defaultdict

sys.path.insert(0, ".")
import v2engine.possession as P

F = math.log(P.BALL_FRICTION_PER_S)
GAPS = [lim for lim, _ in P._CUT_TABLE]
REST = [(lim, on, off) for lim, on, off in P._CUT_REST_FACTOR]

R = []
for path in sys.argv[1:]:
    rows = json.load(open(path))
    # numéro de match : le temps de jeu repart à zéro à chaque match
    match, last = 0, -1.0
    for r in rows:
        if r["t"] < last - 60:
            match += 1
        last = r["t"]
        r["m"] = (path, match)
        R.append(r)
keys = sorted({r["m"] for r in R})
fit_set = set(keys[0::2])


def lost(r):
    if r.get("first"):
        return r["first_team"] != r["team"]
    return bool(r.get("out")) and r.get("out_team") != r["team"]


def geom(r, o, played):
    """(avancée, écart) de l'adversaire par rapport à la ligne idéale ou à la ligne jouée."""
    if not played:
        return o["along"], abs(o["side"])
    a = math.radians(r["ang_deg"])
    along = o["along"] * math.cos(a) + o["side"] * math.sin(a)
    return along, abs(o["side"] * math.cos(a) - o["along"] * math.sin(a))


def cell(r, o, played):
    along, gap = geom(r, o, played)
    g = next((i for i, lim in enumerate(GAPS) if gap < lim), None)
    if g is None or not 0.0 < along < r["L"]:
        return None
    v0 = P._launch_speed(r["L"])
    at = max(P.BALL_STOPPED_MPS, v0 + along * F)
    t = math.log(at / v0) / F
    rest = r["L"] - along
    k = next((i for i, (lim, _, _) in enumerate(REST) if rest < lim), None)
    return g, next(i for i, lim in enumerate(P._CUT_TIME_S) if t < lim), k, int(gap >= P.CUT_REST_GAP_M)


def reached(r, played):
    opp = [(o, cell(r, o, played)) for o in r["opp"]]
    opp = sorted(((o, c) for o, c in opp if c is not None), key=lambda x: geom(r, x[0], played)[0])
    for o, c in opp:
        yield o, c, r.get("first") == o["n"]
        if r.get("first") and any(q["n"] == r["first"] and geom(r, q, played)[0] <= geom(r, o, played)[0] for q in r["opp"]):
            return


def fit(played):
    full, near = defaultdict(lambda: [0, 0]), defaultdict(lambda: [0, 0.0])
    S = [r for r in R if r["m"] in fit_set]
    for r in S:
        for o, c, hit in reached(r, played):
            if c[2] is None:
                full[c[:2]][0] += 1
                full[c[:2]][1] += hit
    tab = {k: v[1] / v[0] for k, v in full.items() if v[0] >= 30}
    for r in S:
        for o, c, hit in reached(r, played):
            if c[2] is not None and c[:2] in tab:
                near[(c[2], c[3])][0] += hit
                near[(c[2], c[3])][1] += tab[c[:2]]
    fac = {k: v[0] / v[1] for k, v in near.items() if v[1] > 0}
    return tab, fac


def chance(r, model, played):
    tab, fac = model
    keep = 1.0
    for o in r["opp"]:
        c = cell(r, o, played)
        if c is None or c[:2] not in tab:
            continue
        x = tab[c[:2]] * (fac.get((c[2], c[3]), 1.0) if c[2] is not None else 1.0)
        keep *= 1.0 - min(1.0, x)
    return keep * sum(w * s for w, (_, s) in zip(r["w"], P._LATERAL_NOT_LOST))


print(f"{len(R)} passes, {len(keys)} matchs ({len(fit_set)} pour l'ajustement, les autres en contrôle)")
models = {p: fit(p) for p in (False, True)}
T = [r for r in R if r["m"] not in fit_set]
groups = [("toutes", lambda r: True), ("Passing < 50", lambda r: r["passing"] < 50),
          ("Passing 50-70", lambda r: 50 <= r["passing"] < 70), ("Passing >= 70", lambda r: r["passing"] >= 70),
          ("longueur < 8 m", lambda r: r["L"] < 8), ("longueur 8-15 m", lambda r: 8 <= r["L"] < 15),
          ("longueur 15-30 m", lambda r: 15 <= r["L"] < 30), ("longueur >= 30 m", lambda r: r["L"] >= 30),
          ("écart réalisé > 2 sigma", lambda r: abs(r["ang_deg"]) > 2 * r["sigma_deg"])]
print("Contrôle : écart prévision - non perdue (points) ; ligne idéale | ligne jouée (prévision avec l'angle réellement tiré)")
for name, sel in groups:
    S = [r for r in T if sel(r)]
    o = sum(not lost(r) for r in S) / len(S)
    se = 196 * math.sqrt(o * (1 - o) / len(S))
    a, b = (100 * (sum(chance(r, models[p], p) for r in S) / len(S) - o) for p in (False, True))
    print(f"  {name:<26} n {len(S):6d} (± {se:.1f})  {a:+5.1f} | {b:+5.1f}")

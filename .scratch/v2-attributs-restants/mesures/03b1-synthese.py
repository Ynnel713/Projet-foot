"""Synthèse de la série appariée du 03b1 : buts, part des cadrés jugés arrêtés, par distance et par Reflexes du gardien.
Usage : uv run python .scratch/v2-attributs-restants/mesures/03b1-synthese.py <avant.json> <après.json>"""
import json, math, statistics, sys

SAVED = ("capté", "repoussé", "claqué")
GOAL_X = {"home": 105.0, "away": 0.0}
before, after = (json.load(open(p, encoding="utf-8")) for p in sys.argv[1:3])


def framed(rows):
    return [s for r in rows for s in r["tirs"] if s["écart"] is not None and s["issue"] in SAVED + ("but",)]


def dist(s):
    return math.hypot(GOAL_X[s["équipe"]] - s["x"], 34.0 - s["y"])


def rate(g):
    return f"{sum(s['issue'] in SAVED for s in g) / len(g):.1%} ({len(g)})" if g else "-"


def paired(f):
    d = [f(b) - f(a) for a, b in zip(before, after)]
    m, se = statistics.mean(d), statistics.stdev(d) / math.sqrt(len(d))
    return f"{m:+.2f} [{m - 1.96 * se:+.2f} ; {m + 1.96 * se:+.2f}]"


n = len(before)
for name, rows in (("avant", before), ("après", after)):
    fr = framed(rows)
    print(f"{name}: buts/match {sum(sum(r['score']) for r in rows) / n:.2f} ; tirs/match "
          f"{sum(len(r['tirs']) for r in rows) / n:.1f} ; cadrés jugés arrêtés {rate(fr)}")
    for lo, hi in ((0, 10), (10, 16), (16, 99)):
        print(f"   distance [{lo} ; {hi}[ m : {rate([s for s in fr if lo <= dist(s) < hi])}")
    for lo, hi in ((0, 71), (71, 80), (80, 100)):
        print(f"   Reflexes du gardien [{lo} ; {hi}[ : {rate([s for s in fr if lo <= (s['gardien']['Reflexes'] or 60) < hi])}")
print("écart apparié buts/match", paired(lambda r: sum(r["score"])))

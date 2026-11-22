"""Synthèse de la série appariée du 03f : buts, cadrés jugés, part arrêtée, par élan du gardien (après).
Usage : uv run python .scratch/v2-realisme/mesures/03f-synthese.py <avant.json> <après.json>"""
import json, math, statistics, sys

SAVED = ("capté", "repoussé", "claqué")
before, after = (json.load(open(p, encoding="utf-8")) for p in sys.argv[1:3])


def framed(rows):
    return [s for r in rows for s in r["tirs"] if s["écart"] is not None and s["issue"] in SAVED + ("but",)]


def paired(f):
    d = [f(b) - f(a) for a, b in zip(before, after)]
    m, se = statistics.mean(d), statistics.stdev(d) / math.sqrt(len(d))
    return f"{m:+.2f} [{m - 1.96 * se:+.2f} ; {m + 1.96 * se:+.2f}]"


n = len(before)
for name, rows in (("avant", before), ("après", after)):
    fr = framed(rows)
    saves = sum(s["issue"] in SAVED for s in fr)
    psxg = sum(s["psxg"] for s in fr if s["psxg"] is not None)
    goals = sum(s["issue"] == "but" for s in fr)
    print(f"{name}: buts/match {sum(sum(r['score']) for r in rows) / n:.2f} ; tirs/match "
          f"{sum(len(r['tirs']) for r in rows) / n:.1f} ; cadrés jugés {len(fr)} ; arrêtés {saves / len(fr):.1%} ; "
          f"xG après frappe - buts (cadrés jugés) {(psxg - goals) / n:+.3f}/match")
print("écart apparié buts/match", paired(lambda r: sum(r["score"])))
fr = framed(after)
for lo, hi, label in ((-99, -0.5, "contre-pied (< -0,5 m/s)"), (-0.5, 0.5, "quasi immobile"), (0.5, 99, "lancé du bon côté (> 0,5)")):
    g = [s for s in fr if lo <= (s["élan"] or 0.0) < hi]
    if g:
        print(f"  {label}: {len(g)} tirs, arrêtés {sum(s['issue'] in SAVED for s in g) / len(g):.1%}")

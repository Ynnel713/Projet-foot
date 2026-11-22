"""Synthèse de la série appariée du 03b2 : buts, répartition des arrêts (capté, repoussé dont relâché, claqué), part
captée selon le Handling du gardien, corners et corners issus d'un arrêt (dernier toucher : un gardien).
Usage : uv run python .scratch/v2-attributs-restants/mesures/03b2-synthese.py <avant.json> <après.json>"""
import json, math, statistics, sys

SAVED = ("capté", "repoussé", "claqué")
before, after = (json.load(open(p, encoding="utf-8")) for p in sys.argv[1:3])


def saves(rows):
    return [s for r in rows for s in r["tirs"] if s["issue"] in SAVED]


def split(g):
    n = len(g)
    if not n:
        return "-"
    fumbled = sum(s.get("relâché", False) for s in g)
    return (f"capté {sum(s['issue'] == 'capté' for s in g) / n:.1%}, repoussé {sum(s['issue'] == 'repoussé' for s in g) / n:.1%}"
            f" (dont relâché {fumbled}), claqué {sum(s['issue'] == 'claqué' for s in g) / n:.1%} ({n})")


def paired(f):
    d = [f(b) - f(a) for a, b in zip(before, after)]
    m, se = statistics.mean(d), statistics.stdev(d) / math.sqrt(len(d))
    return f"{m:+.2f} [{m - 1.96 * se:+.2f} ; {m + 1.96 * se:+.2f}]"


n = len(before)
for name, rows in (("avant", before), ("après", after)):
    sv = saves(rows)
    corners = sum(r["corners"] for r in rows)
    print(f"{name}: buts/match {sum(sum(r['score']) for r in rows) / n:.2f} ; arrêts/match {len(sv) / n:.2f} ; {split(sv)}")
    print(f"   corners/match {corners / n:.2f} ; issus d'un arrêt (dernier toucher gardien) "
          f"{sum(r['corners gardien'] for r in rows) / max(1, corners):.1%}")
    for lo, hi in ((0, 55), (55, 65), (65, 100)):
        print(f"   Handling du gardien [{lo} ; {hi}[ : {split([s for s in sv if lo <= (s['handling'] or 60) < hi])}")
print("écart apparié buts/match", paired(lambda r: sum(r["score"])))

"""Synthèse du diagnostic 18l (lecture seule de 18l-diag-50.json). Usage : python3 .scratch/v2-realisme/mesures/18l-diag-synthese.py"""
import json
import statistics
import sys
from collections import Counter
from pathlib import Path

rows = json.loads((Path(__file__).parent / "18l-diag-50.json").read_text(encoding="utf-8"))
n = len(rows)
shots = [s for r in rows for s in r["tirs"]]
goals = [g for r in rows for g in r["buts"]]
out = sys.stdout
print(f"matchs {n} ; tirs par équipe {len(shots) / (2 * n):.2f} ; buts par match {len(goals) / n:.2f}", file=out)
for box in (True, False):
    ss = [s for s in shots if s["surface"] == box]
    g = sum(s["issue"] == "but" for s in ss)
    xg = [s["xg"] for s in ss if s["xg"] is not None]
    print(f"{'surface' if box else 'hors surface'} : tirs par équipe {len(ss) / (2 * n):.2f}, part {100 * len(ss) / len(shots):.1f} %, "
          f"conversion {100 * g / len(ss):.1f} %, buts par match {g / n:.2f}, xG neutre moyen {sum(xg) / len(xg):.3f}", file=out)
for lo, hi in ((0, 11), (11, 16.5), (16.5, 25), (25, 99)):
    ss = [s for s in shots if lo <= s["distance"] < hi]
    g = sum(s["issue"] == "but" for s in ss)
    print(f"distance {lo}-{hi} m : tirs par équipe {len(ss) / (2 * n):.2f}, conversion {100 * g / max(1, len(ss)):.1f} %, buts par match {g / n:.2f}", file=out)
c, cg = Counter(s["origine"] for s in shots), Counter(s["origine"] for s in shots if s["issue"] == "but")
for o, v in c.most_common():
    print(f"origine du ballon du tireur, {o} : tirs par équipe {v / (2 * n):.2f}, conversion {100 * cg[o] / v:.1f} %, buts par match {cg[o] / n:.2f}", file=out)
for o, v in Counter(g["famille"] for g in goals).most_common():
    print(f"origine des buts (19e), {o} : {100 * v / len(goals):.1f} %, {v / n:.2f} par match", file=out)
for o, v in Counter(g["famille"] + " : " + g["détail"] for g in goals).most_common(6):
    print(f"   {o} : {100 * v / len(goals):.1f} %", file=out)
delays = [g["délai (s)"] for g in goals if g["délai (s)"] is not None]
print(f"délai origine -> but : médiane {statistics.median(delays):.1f} s, moins de 15 s {100 * sum(d < 15 for d in delays) / len(delays):.1f} %", file=out)

"""Ticket v2-realisme/04f : calibration de la conduite (04c) regroupée sur plusieurs lots `scripts.measure_v2 N --debut D
--json lot.json` ; parts pondérées par le nombre d'intervalles de chaque lot (intervalles par match x matchs du lot).
Usage : python .scratch/v2-realisme/mesures/04f-calibration.py lot.json:matchs ..."""
import json
import sys
from collections import defaultdict

P = "calibration conduite, "
acc = defaultdict(lambda: defaultdict(float))
total = 0
for arg in sys.argv[1:]:
    path, n = arg.rsplit(":", 1)
    n = int(n)
    total += n
    d = json.load(open(path))
    for key, value in d.items():
        if not key.startswith(P) or not key.endswith("intervalles par match"):
            continue
        t = key[len(P):].rsplit(" : ", 1)[0]
        w = value * n
        acc[t]["n"] += w
        for part in ("risque évalué (part)", "perte tirée (part)", "perte avec tacle gagné (part)"):
            acc[t][part] += d[f"{P}{t} : {part}"] * w
print(f"{total} matchs")
print(f"{'tranche':22s} {'interv./match':>13s} {'évalué':>8s} {'tirée':>8s} {'écart':>7s} {'avec tacle':>10s} {'écart':>7s}")
for t in sorted(acc):
    a = acc[t]
    ev, dr, ta = (a[p] / a["n"] for p in ("risque évalué (part)", "perte tirée (part)", "perte avec tacle gagné (part)"))
    print(f"{t:22s} {a['n'] / total:13.1f} {ev:8.2%} {dr:8.2%} {100 * (dr - ev):+7.2f} {ta:10.2%} {100 * (ta - ev):+7.2f}")

"""Matchs appariés du ticket v2-realisme/18o : écarts par match entre deux séries `scripts/diag_passes_v2.py --json` sur
les mêmes graines du banc (avant : moteur du commit 0651cf3, série « après » du 18n, rejouée à l'identique : même
empreinte du match 3 ; après : moteur du 18o). Moyenne et IC 95 % de l'écart apparié.
Usage : python .scratch/v2-realisme/mesures/18o-apparies.py AVANT.json APRES.json"""
import json
import math
import sys

A = {m["k"]: m["count"] for m in json.load(open(sys.argv[1]))}
B = {m["k"]: m["count"] for m in json.load(open(sys.argv[2]))}
K = sorted(set(A) & set(B))
KEYS = ("passes (jeu)", "passes prises par l'adversaire (jeu)", "pertes (journal)", "pertes (journal) : passe interceptée",
        "passes ratées au tirage", "tirs", "buts")


def stat(f):
    a = [f(A[k]) for k in K]
    b = [f(B[k]) for k in K]
    d = [y - x for x, y in zip(a, b)]
    m = sum(d) / len(d)
    sd = math.sqrt(sum((x - m) ** 2 for x in d) / (len(d) - 1))
    return sum(a) / len(a), sum(b) / len(b), m, 1.96 * sd / math.sqrt(len(d))


print(f"{len(K)} matchs appariés, par match")
for key in KEYS:
    a, b, m, ci = stat(lambda c: c.get(key, 0))
    print(f"  {key:<42} {a:9.2f} -> {b:9.2f}  écart {m:+8.2f} ± {ci:.2f}")
a, b, m, ci = stat(lambda c: 100 * c["passes réussies (jeu)"] / c["passes (jeu)"])
print(f"  {'réussite des passes de jeu (%)':<42} {a:9.2f} -> {b:9.2f}  écart {m:+8.2f} ± {ci:.2f}")

"""Synthèse 31a : avant (07b, mêmes graines : .scratch/v2-realisme/mesures/07b-50b-lot*) / après, moyenne pondérée par
le nombre de matchs. Usage : python .scratch/v2-collectif/mesures/31a-synthese.py '<glob avant>' '<glob après>'"""
import glob
import json
import sys

KEYS = [
    "passes de première (part des passes décidées)", "passes de première par match",
    "passes de première : non perdues (part)", "passes de première : chance évaluée (part)",
    "passes par match", "passes par minute de jeu effectif", "passes réussies (part)", "passes par possession",
    "temps par possession de joueur (s)", "possession d'équipe (s)",
    "une-deux par équipe et par match", "troisième homme par équipe et par match",
    "retours au passeur en 3 s (part des passes réussies)", "talonnades par match",
    "pertes de balle par match", "tirs par équipe", "buts par match", "xG neutre par match",
    "face-à-face : tirs par match", "temps de calcul par match (s)",
]


def lots(pattern):
    return [json.load(open(f, encoding="utf-8")) for f in sorted(glob.glob(pattern))]


def mean(ds, k):
    vals = [(d["matchs"], d.get(k)) for d in ds if isinstance(d.get(k), (int, float))]
    n = sum(w for w, _ in vals)
    return sum(w * v for w, v in vals) / n if n else float("nan")


A, B = lots(sys.argv[1]), lots(sys.argv[2])
print(f"avant : {sum(d['matchs'] for d in A)} matchs ; après : {sum(d['matchs'] for d in B)} matchs")
for k in KEYS:
    a, b = mean(A, k), mean(B, k)
    print(f"  {k:<60} {a:10.3f} {b:10.3f} {b - a:+9.3f}")

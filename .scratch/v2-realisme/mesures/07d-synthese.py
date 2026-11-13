"""Synthèse 07d : avant (31c, mêmes graines : .scratch/v2-collectif/mesures/31c-50-lot*) / après, moyenne pondérée par
le nombre de matchs. Usage : python .scratch/v2-collectif/mesures/31a-synthese.py '<glob avant>' '<glob après>'"""
import glob
import json
import sys

KEYS = [
    "contrôles à l'aveugle (part des contrôles non orientés)", "temps par possession par réception : contrôles appariés (part)",
    "contrôles orientés (part des contrôles)",
    "contrôles de ballon dur, plus de 12 m/s (part des contrôles)", "contrôles orientés, ballon dur (part)",
    "passes de première (part des passes décidées)", "passes de première par match",
    "passes de première : non perdues (part)", "passes de première : chance évaluée (part)",
    "passes par match", "passes par minute de jeu effectif", "passes réussies (part)", "passes par possession",
    "temps par possession de joueur (s)", "possession d'équipe (s)",
    "une-deux par équipe et par match", "troisième homme par équipe et par match",
    "retours au passeur en 3 s (part des passes réussies)", "talonnades par match",
    "pertes de balle par match", "tirs par équipe", "buts par match", "xG neutre par match",
    "face-à-face : tirs par match", "rotation : passes décidés avec rotation (part)",
    "rotation : passes, durée moyenne quand il y en a une (s)", "temps de calcul par match (s)",
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

print("\nTemps par possession de joueur par type de réception (après seulement : indicateur nouveau)")
for k in sorted(B[0]):
    if k.startswith("temps par possession de joueur, réception") or k.startswith("réceptions "):
        print(f"  {k:<75} {mean(B, k):8.3f}")

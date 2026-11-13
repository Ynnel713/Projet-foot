"""Synthèse 07b : avant (08f, mêmes graines) / après, moyenne pondérée par le nombre de matchs.
Usage : python .scratch/v2-realisme/mesures/07b-synthese.py '<glob avant>' '<glob après>'"""
import glob
import json
import sys

KEYS = [
    "passes par match", "passes réussies (part)", "tirs par équipe", "buts par match", "xG neutre par match",
    "pertes de balle par match", "conduite : pertes par dépossession par match", "face-à-face : tirs par match",
    "distance au-dessus de 19,8 km/h (part)", "distance au-dessus de 25 km/h (part)",
    "temps au-dessus de 19,8 km/h (part)", "temps au-dessus de 25 km/h (part)",
    "vision : adversaires à 5 m au plus non vus à la décision (part des adversaires proches)",
    "temps de calcul par match (s)",
]


def lots(pattern):
    return [json.load(open(f, encoding="utf-8")) for f in sorted(glob.glob(pattern))]


def mean(ds, get):
    vals = [(d["matchs"], get(d)) for d in ds]
    vals = [(w, v) for w, v in vals if isinstance(v, (int, float))]
    n = sum(w for w, _ in vals)
    return sum(w * v for w, v in vals) / n if n else float("nan")


A, B = lots(sys.argv[1]), lots(sys.argv[2])
print(f"avant : {sum(d['matchs'] for d in A)} matchs ; après : {sum(d['matchs'] for d in B)} matchs")
for k in KEYS:
    a, b = mean(A, lambda d: d.get(k)), mean(B, lambda d: d.get(k))
    print(f"  {k:<95} {a:10.3f} {b:10.3f} {b - a:+9.3f}")
print("\nkm par joueur de champ, par poste")
for p in sorted(A[0]["km par joueur de champ, par poste"]):
    a = mean(A, lambda d: d["km par joueur de champ, par poste"].get(p))
    b = mean(B, lambda d: d["km par joueur de champ, par poste"].get(p))
    print(f"  {p:<6} {a:8.2f} {b:8.2f} {100 * (b - a) / a:+7.1f} %")
print("\ndistance au-dessus de 19,8 km/h par joueur (m)")
for k in sorted(k for k in A[0] if k.startswith("distance au-dessus de 19,8 km/h par joueur")):
    a, b = mean(A, lambda d: d.get(k)), mean(B, lambda d: d.get(k))
    print(f"  {k.split(' : ')[1]:<6} {a:8.0f} {b:8.0f} {100 * (b - a) / a:+7.1f} %")

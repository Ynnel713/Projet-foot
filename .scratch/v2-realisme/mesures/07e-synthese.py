"""Synthèse 07e : indicateurs généraux, rotation et talonnades, avant (lots du 18k) contre après.
Usage : python .scratch/v2-realisme/mesures/07e-synthese.py '<glob avant>' '<glob après>'"""
import glob
import json
import sys

KEYS = ["passes par match", "passes réussies (part)", "passes chez l'adversaire (part)", "receveur visé (part)",
        "passes par possession", "possession d'équipe (s)", "temps par possession de joueur (s)", "buts par match",
        "tirs par équipe et par match", "tirs tracés", "conduite : pertes par match", "passes longues (part)",
        "face-à-face : tirs par match", "corners par match", "fautes par match",
        "rotation : passes décidés avec rotation (part)", "rotation : passes, durée moyenne quand il y en a une (s)",
        "rotation : tirs décidés avec rotation (part)", "rotation : tirs, durée moyenne quand il y en a une (s)",
        "rotation : ballons perdus en se retournant par match", "talonnades par match", "talonnades : non perdues (part)",
        "talonnades : reçues par le receveur visé (part)", "talonnades : chance évaluée (part)",
        "rotation : passes abandonnées, ligne fermée, par match",
        "rotation : passes abandonnées, ligne fermée (part des passes jugées après la rotation)",
        "tirs tracés par équipe", "tirs cadrés (part)", "conversion des tirs (part)", "xG neutre par match",
        "temps de calcul par match (s)"]
BANDS = ["[0 ; 0.1[", "[0.1 ; 0.2[", "[0.2 ; 0.3[", "[0.3 ; 0.4[", "[0.4 ; 0.5[", "[0.5 ; 0.6[", "[0.6 ; 0.7[",
         "[0.7 ; 0.8[", "[0.8 ; 0.9[", "[0.9 ; +["]


def lots(pattern):
    return [json.load(open(f, encoding="utf-8")) for f in sorted(glob.glob(pattern))]


def mean(ds, key):
    vals = [(d["matchs"], d.get(key)) for d in ds if isinstance(d.get(key), (int, float))]
    n = sum(w for w, _ in vals)
    return sum(w * v for w, v in vals) / n if n else float("nan")


def calib(ds, band):
    pre = f"calibration passe, chance évaluée {band} : "
    w = [d["matchs"] * d.get(pre + "passes par match", 0.0) for d in ds]
    tot = sum(w)
    if not tot:
        return None
    f = lambda k: sum(wi * d.get(pre + k, 0.0) for wi, d in zip(w, ds)) / tot
    return tot, f("chance évaluée (part)"), f("non perdue (part)")


A, B = lots(sys.argv[1]), lots(sys.argv[2])
print(f"avant : {sum(d['matchs'] for d in A)} matchs ; après : {sum(d['matchs'] for d in B)} matchs")
for k in KEYS:
    print(f"  {k:<58} {mean(A, k):10.3f} -> {mean(B, k):10.3f}")
print("\nCalibration de la passe (après) : tranche, passes, évaluée, non perdue, écart (points)")
for band in BANDS:
    c = calib(B, band)
    if c:
        print(f"  {band:<13} {c[0]:8.0f} {c[1]:7.3f} {c[2]:7.3f} {100 * (c[1] - c[2]):+6.1f}")

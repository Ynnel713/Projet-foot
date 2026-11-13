"""Synthèse 08d : le porteur décide sur ce qu'il perçoit, avant (lots du 07e, jeu identique au 08c) contre après.
Usage : python .scratch/v2-realisme/mesures/08d-synthese.py '<glob avant>' '<glob après>'"""
import glob
import json
import sys

KEYS = ["passes par match", "passes par minute", "passes réussies (part)", "passes chez l'adversaire (part)",
        "receveur visé (part)", "passes par possession", "possession d'équipe (s)", "temps par possession de joueur (s)",
        "buts par match", "tirs tracés par équipe", "tirs cadrés (part)", "conversion des tirs (part)", "xG neutre par match",
        "conduite : pertes par match", "passes longues (part)", "face-à-face : tirs par match", "corners par match",
        "fautes par match", "pertes de balle par match", "grosses occasions par match",
        "grosses occasions, issue : interception (part)", "choix dribble (part)", "choix pass (part)", "choix shot (part)",
        "talonnades par match", "talonnades : non perdues (part)",
        "vision : adversaires non vus par le porteur à la décision (moyenne)",
        "vision : décisions avec un adversaire non vu à 5 m au plus (part)",
        "mémoire : âge de la dernière vue des adversaires non vus, porteur (s)",
        "mémoire : erreur de position perçue des adversaires non vus, porteur (m)",
        "mémoire : erreur maximale, porteur (m)",
        "mémoire : fantômes perçus par décision (adversaires perçus avec plus de 4 s de retard et 10 m d'erreur)",
        "mémoire : décisions avec un fantôme (part)",
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
    print(f"  {k:<100} {mean(A, k):10.3f} -> {mean(B, k):10.3f}")
print("\nCalibration de la passe : tranche de chance évaluée, passes par match, évaluée, non perdue, écart (points) ; avant puis après")
for band in BANDS:
    a, b = calib(A, band), calib(B, band)
    fmt = lambda c: f"{c[0]:8.0f} {c[1]:6.3f} {c[2]:6.3f} {100 * (c[1] - c[2]):+6.1f}" if c else " " * 28
    print(f"  {band:<13} {fmt(a)}   |   {fmt(b)}")

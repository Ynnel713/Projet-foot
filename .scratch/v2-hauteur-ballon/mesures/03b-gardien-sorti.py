"""Vérification A1 (03b) : calibration de l'estimateur face à un gardien sorti, scène de `scripts/shot_calibration`
(`scene_rate`) avec le gardien à 6, 8 et 10 m de sa ligne au lieu de `KEEPER_REFERENCE_M` = 1 m (attribut patché en
mémoire, aucun fichier modifié). Usage, racine du dépôt : python SCRIPT N"""
import sys
sys.path.insert(0, ".")
from scripts import shot_calibration as sc
from v2engine import shooting
n = int(sys.argv[1])
for depth in (6.0, 8.0, 10.0):
    shooting.KEEPER_REFERENCE_M = depth
    for dist in (25.0, 30.0, 35.0):
        for off in (0.0, 5.0):
            ev, rate = sc.scene_rate(dist, off, n)
            lo, hi = sc.wilson(round(rate * n), n)
            print(f"gardien {depth:4.0f} m, tir {dist:4.0f} m, écart {off:3.0f} m : évaluée {ev:.3f}  observé {rate:.3f} [{lo:.3f} ; {hi:.3f}]  {'calibrée' if lo <= ev <= hi else 'HORS'}", flush=True)

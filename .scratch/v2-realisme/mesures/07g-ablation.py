"""Ablations 07g (hors dépôt) : neutralise un mécanisme à l'exécution, puis lance le banc tel quel.
Usage (depuis la racine du dépôt) : python -m ... impossible ; lancer : python <ce fichier> <ablation> <n> <debut> <json>"""
import sys
sys.path.insert(0, ".")
import v2engine.possession as possession
import v2engine.movement as movement
from v2engine.reception import DE_FACE, DE_PROFIL, DOS_AU_JEU

name, n, start, out = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
if name == "sans07d":  # orientation du corps sans effet sur la durée du contrôle (facteurs 07d à 1, aveugle compris)
    possession.RECEPTION_KIND_FACTORS = {DE_FACE: 1.0, DE_PROFIL: 1.0, DOS_AU_JEU: 1.0}
elif name == "sans31c":  # ballon dur sans effet sur l'orientation du contrôle
    possession.hard_ball_share = lambda v: 0.0
elif name == "chasses90":  # piste du 07b : pas chassés à 90 % au lieu de 80 %
    movement._DIRECTION_SPEED_POINTS = ((45.0, 1.0), (90.0, 0.90), (180.0, 0.65))
elif name == "sans31b":  # contrôle orienté sans effet sur la durée (facteurs 1 / 1), types 07d gardés
    possession.ORIENTED_FACTOR = 1.0
    possession.UNORIENTED_FACTOR = 1.0
else:
    raise SystemExit(name)
from scripts import bench_series
bench_series.main([n, "--debut", start, "--processus", "4", "--json", out])

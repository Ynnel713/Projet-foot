"""Essai hors moteur du ticket 18e : `shooting.BLOCK_CHANCE` (et sa copie importée dans `match`) remplacée par la valeur
donnée, puis `scripts/measure_v2.py` (rien de commité dans le moteur).
Usage : uv run python .scratch/v2-realisme/mesures/18e-variante.py CHANCE N DEBUT JSON"""
import sys

sys.path.insert(0, ".")
import v2engine.match as match
import v2engine.shooting as shooting
from scripts.measure_v2 import main

shooting.BLOCK_CHANCE = match.BLOCK_CHANCE = float(sys.argv[1])
main([sys.argv[2], "--debut", sys.argv[3], "--json", sys.argv[4]])

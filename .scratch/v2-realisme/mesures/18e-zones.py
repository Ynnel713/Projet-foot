"""Diagnostic du ticket 18e : tirs par zone (dans ou hors de la surface, tranches de distance), issues et conversion,
sur des matchs du moteur (lecture seule : trace `shots`). Usage : uv run python .scratch/v2-realisme/mesures/18e-zones.py
N DEBUT > sortie.json (graines d'audit 20260923 + k, mêmes clubs que `scripts/measure_v2.py`)."""
import json
import random
import sys

sys.path.insert(0, ".")
import v2engine.match as match
from ligue1sim.clubs import load_clubs
from ligue1sim.season import CLUBS_PATH

AUDIT_SEED = 20260923
n, start = int(sys.argv[1]), int(sys.argv[2])
clubs = load_clubs(CLUBS_PATH, "Ligue 1")
rows = []
for k in range(start, start + n):
    random.seed(AUDIT_SEED + k)
    home, away = clubs[(2 * k) % len(clubs)], clubs[(2 * k + 1) % len(clubs)]
    trace = match.simulate_match(home, away)
    for s in trace.shots:
        rows.append(dict(m=k, team=s.team, x=s.x, y=s.y, outcome=s.outcome, origin=s.origin, xg=s.xg,
                         quality=s.quality))
json.dump(rows, sys.stdout)

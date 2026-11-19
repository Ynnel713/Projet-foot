"""Ticket 10d : empreinte d'un match complet à graine fixée (déterminisme D-V06), à lancer deux fois dans deux processus.
Empreinte : sha256 (12 premiers caractères) du score, des buts, tirs et réceptions (minute, joueur, place).
Usage : uv run python .scratch/v2-realisme/mesures/10d-empreinte.py GRAINE"""
import hashlib
import random
import sys

sys.path.insert(0, ".")
from ligue1sim.clubs import load_clubs
from ligue1sim.season import CLUBS_PATH
from v2engine.match import simulate_match

seed = int(sys.argv[1])
clubs = load_clubs(CLUBS_PATH, "Ligue 1")
random.seed(seed)
trace = simulate_match(clubs[0], clubs[1])
payload = repr((trace.home_goals, trace.away_goals, trace.goals, trace.shots,
                [(round(r.minute, 6), r.player, round(r.x, 6), round(r.y, 6)) for r in trace.receptions]))
print(seed, trace.home_goals, trace.away_goals, len(trace.receptions), hashlib.sha256(payload.encode()).hexdigest()[:12])

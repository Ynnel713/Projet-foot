"""Ticket 14a1 : empreinte complète d'un match à graine fixée (positions de tous les joueurs et du ballon à chaque tick,
score, tirs, réceptions). Sert à prouver que le regroupement de la loi de freinage ne change pas le jeu.
Usage : uv run python .scratch/v2-realisme/mesures/14a1-empreinte.py GRAINE [GRAINE...]"""
import hashlib
import random
import sys

sys.path.insert(0, ".")
from ligue1sim.clubs import load_clubs
from ligue1sim.season import CLUBS_PATH
from v2engine.match import simulate_match

clubs = load_clubs(CLUBS_PATH, "Ligue 1")
for seed in map(int, sys.argv[1:]):
    random.seed(seed)
    trace = simulate_match(clubs[seed % len(clubs)], clubs[(seed + 1) % len(clubs)])
    h = hashlib.sha256()
    for tick in trace.ticks:
        b = tick.ball
        h.update(repr((tick.minute, b.position.x, b.position.y, b.z, b.holder, b.mode, b.dead,
                       [(p.name, p.position.x, p.position.y) for p in tick.players])).encode())
    h.update(repr((trace.home_goals, trace.away_goals, trace.goals, trace.shots, trace.receptions)).encode())
    print(seed, trace.home_goals, trace.away_goals, len(trace.ticks), h.hexdigest()[:16], flush=True)

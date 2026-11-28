"""Empreinte complète d'un match V2 à graine fixée (positions de tous les joueurs et du ballon à chaque pas, score,
événements). Usage, depuis la racine du dépôt : python empreinte.py 0 1"""
import hashlib
import random
import sys

sys.path.insert(0, ".")
from scripts.measure_v2 import AUDIT_SEED, TICK_S  # noqa: E402
from ligue1sim.season import CLUBS_PATH  # noqa: E402
from ligue1sim.clubs import load_clubs  # noqa: E402
from v2engine import match  # noqa: E402

clubs = load_clubs(CLUBS_PATH, "Ligue 1")
for k in map(int, sys.argv[1:]):
    random.seed(AUDIT_SEED + k)
    h = hashlib.sha256()

    def observer(now_s, players, ball, scoring_team):
        h.update(repr((round(now_s, 6), ball.position, ball.z, ball.vz, ball.holder, scoring_team,
                       [(p.name, p.position, p.velocity) for p in players])).encode())

    trace = match.simulate_match(clubs[(2 * k) % len(clubs)], clubs[(2 * k + 1) % len(clubs)], duration_minutes=90.0,
                                 tick_seconds=TICK_S, observer=observer)
    h.update(repr((trace.home_goals, trace.away_goals, len(trace.events), len(trace.receptions))).encode())
    print(k, f"{trace.home_goals}-{trace.away_goals}", h.hexdigest()[:16], flush=True)

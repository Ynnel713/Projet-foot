"""Ticket 10a : presseur selon la zone, mesure avant/après sur des matchs complets (graines du banc, AUDIT_SEED + k).
`avant` : marge de zone à -inf, donc le premier arrivé de tous presse, exactement comme avant le ticket (le statut
« dans sa zone » reste tracé). `apres` : le moteur livré.
Usage : uv run python .scratch/v2-realisme/mesures/10a-presseur-zone.py avant|apres DEBUT FIN SORTIE.json"""
import json
import random
import sys
from collections import defaultdict

sys.path.insert(0, ".")
from ligue1sim.clubs import load_clubs
from ligue1sim.season import CLUBS_PATH

import v2engine.defense as defense
import v2engine.match as match

AUDIT_SEED = 20260923
mode, start, end, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
if mode == "avant":
    defense.PRESS_ZONE_MARGIN_S = float("-inf")
tackles = [0]
real_tackle = match.resolve_tackle


def counting(*a, **k):
    tackles[0] += 1
    return real_tackle(*a, **k)


match.resolve_tackle = counting
clubs = load_clubs(CLUBS_PATH, "Ligue 1")
rows = []
for k in range(start, end):
    random.seed(AUDIT_SEED + k)
    tackles[0] = 0
    home, away = clubs[(2 * k) % len(clubs)], clubs[(2 * k + 1) % len(clubs)]
    trace = match.simulate_match(home, away)
    end_min = trace.ticks[-1].minute
    # durée de chaque presseur : jusqu'au changement suivant de son équipe
    time_by = defaultdict(float)  # (poste, dans sa zone) -> minutes
    dist_by = defaultdict(float)  # poste -> somme (distance x minutes)
    last = {}
    for r in trace.pressers + [None]:
        teams = ("home", "away") if r is None else (r.team,)
        for team in teams:
            prev = last.get(team)
            if prev is not None and prev.player:
                d = (end_min if r is None else r.minute) - prev.minute
                time_by[f"{prev.poste}|{prev.in_zone}"] += d
                dist_by[prev.poste] += d * (prev.reference_distance_m or 0.0)
        if r is not None:
            last[r.team] = r
    rows.append({"k": k, "score": [trace.home_goals, trace.away_goals], "shots": len(trace.shots),
                 "offsides": len(trace.offsides), "fouls": len(trace.fouls), "tackles": tackles[0],
                 "changes": sum(1 for r in trace.pressers if r.player),
                 "time": dict(time_by), "dist": dict(dist_by),
                 "fingerprint": [len(trace.pressers), sum(len(trace.decisions) for _ in [0])]})
    print(k, rows[-1]["score"], flush=True)
    json.dump(rows, open(out, "w"))  # après chaque match : un lot interrompu garde ses matchs

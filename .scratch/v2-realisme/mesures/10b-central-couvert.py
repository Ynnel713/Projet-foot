"""Ticket 10b : le central ne quitte sa ligne que couvert, mesure avant/après sur des matchs complets (graines du banc,
AUDIT_SEED + k, mêmes matchs que le 10a). `avant` : vérification neutralisée (`_leaves_uncovered` toujours faux), donc
exactement le moteur du 10a (la trace des sorties reste écrite). `apres` : le moteur livré.
Usage : uv run python .scratch/v2-realisme/mesures/10b-central-couvert.py avant|apres DEBUT FIN SORTIE.json"""
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
    defense.DefensiveRoles._leaves_uncovered = lambda self, *a, **k: False
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
    # sorties des centraux : durée de chaque état jusqu'au changement suivant du même joueur
    exits = defaultdict(float)  # "rôle|couvert|menacé" -> minutes
    last = {}
    for r in trace.line_exits + [None]:
        names = list(last) if r is None else [r.player]
        for name in names:
            prev = last.get(name)
            if prev is not None and prev.exit:
                exits[f"{prev.role}|{prev.covered}|{prev.threatened}"] += (end_min if r is None else r.minute) - prev.minute
        if r is not None:
            last[r.player] = r
    # presseurs (comme au 10a) : temps des DC hors de leur zone
    press = defaultdict(float)
    lastp = {}
    for r in trace.pressers + [None]:
        teams = ("home", "away") if r is None else (r.team,)
        for team in teams:
            prev = lastp.get(team)
            if prev is not None and prev.player:
                press[f"{prev.poste}|{prev.in_zone}"] += (end_min if r is None else r.minute) - prev.minute
        if r is not None:
            lastp[r.team] = r
    rows.append({"k": k, "score": [trace.home_goals, trace.away_goals], "shots": len(trace.shots),
                 "offsides": len(trace.offsides), "fouls": len(trace.fouls), "tackles": tackles[0],
                 "exits": dict(exits), "press": dict(press), "exit_changes": len(trace.line_exits)})
    print(k, rows[-1]["score"], flush=True)
    json.dump(rows, open(out, "w"))  # après chaque match : un lot interrompu garde ses matchs

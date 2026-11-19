"""Ticket 10c : couverture de la profondeur ; mesure avant/après sur des matchs complets, par le collecteur des
indicateurs (`scripts.measure_v2.run`, graines AUDIT_SEED + k, mêmes affiches que le banc du 10b). `avant` : moteur du
10b2 livré (commit 1282f00), lancé depuis un worktree de ce commit (premier argument RACINE) ; `apres` : RACINE = `.`.
Relevés par match : buts, tirs, tacles, fautes, hors-jeu, passes en profondeur (et réussies), appels dans le dos,
minutes où une équipe a un défenseur qui couvre la profondeur (`MatchTrace.depth_covers`, absent avant).
Usage : uv run python .scratch/v2-realisme/mesures/10c-profondeur.py RACINE DEBUT FIN SORTIE.json"""
import json
import sys

root, start, end, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
sys.path.insert(0, root)
import v2engine.bloc as bloc
import v2engine.match as match
from scripts.measure_v2 import run

print("moteur :", bloc.__file__, flush=True)
KEYS = ("buts", "tirs", "tacles", "fautes", "hors-jeu", "passes", "passes en profondeur",
        "passes en profondeur réussies", "appels dans le dos")
real_simulate, last = match.simulate_match, {}


def keeping(*a, **k):
    last["trace"] = real_simulate(*a, **k)
    return last["trace"]


match.simulate_match = keeping
rows = []
for k in range(start, end):
    c = run(1, start=k)
    trace = last["trace"]
    end_min = trace.ticks[-1].minute
    cover = 0.0
    prev = {}
    for r in getattr(trace, "depth_covers", []) + [None]:
        for team in (("home", "away") if r is None else (r.team,)):
            p = prev.get(team)
            if p is not None and p.player:
                cover += (end_min if r is None else r.minute) - p.minute
        if r is not None:
            prev[r.team] = r
    rows.append({"k": k, "score": [trace.home_goals, trace.away_goals], **{key: c.count.get(key, 0) for key in KEYS},
                 "couverture (min)": cover})
    print(k, rows[-1]["score"], flush=True)
    json.dump(rows, open(out, "w"))

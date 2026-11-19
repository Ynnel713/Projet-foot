"""Ticket 10d : écran du milieu devant la défense ; mesure avant/après sur des matchs complets, par le collecteur des
indicateurs (`scripts.measure_v2.run`, graines AUDIT_SEED + k, mêmes affiches que le banc du 10c). `avant` : moteur du
ticket avec la désignation de l'écran neutralisée (`bloc.screen_player` rend None : plus aucun écran, jeu identique au
commit 2145ea1, la trace garde seulement la place du receveur) ; `apres` : moteur du ticket.
Relevés par match : buts, tirs, passes, passes reçues et passes reçues en zone 14, passes en profondeur (et réussies),
appels dans le dos, hors-jeu, tacles, fautes.
Usage : uv run python .scratch/v2-realisme/mesures/10d-ecran.py MODE DEBUT FIN SORTIE.json"""
import json
import os
import sys

sys.path.insert(0, ".")
import v2engine.bloc as bloc
import v2engine.match as match
from scripts.measure_v2 import run

mode, start, end, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
if mode == "avant":
    bloc.screen_player = lambda *a, **k: None
print("mode :", mode, flush=True)
KEYS = ("buts", "tirs", "tacles", "fautes", "hors-jeu", "passes", "passes reçues", "passes reçues en zone 14",
        "passes en profondeur", "passes en profondeur réussies", "appels dans le dos")
real_simulate, last = match.simulate_match, {}


def keeping(*a, **k):
    last["trace"] = real_simulate(*a, **k)
    return last["trace"]


match.simulate_match = keeping
rows = json.load(open(out)) if os.path.exists(out) else []  # reprise (processus courts : la mémoire croît par match)
done = {r["k"] for r in rows}
for k in range(start, end):
    if k in done:
        continue
    c = run(1, start=k)
    trace = last["trace"]
    rows.append({"k": k, "score": [trace.home_goals, trace.away_goals], "tirs": len(trace.shots),
                 **{key: c.count.get(key, 0) for key in KEYS if key not in ("buts", "tirs")}})
    print(k, rows[-1]["score"], rows[-1]["passes reçues en zone 14"], flush=True)
    json.dump(rows, open(out, "w"))

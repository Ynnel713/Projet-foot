"""Ticket 10b2 : la couverture du central suit la règle du 10b, couvreur réservé ; mesure avant/après sur des matchs
complets (graines du banc, AUDIT_SEED + k, mêmes matchs que le 10b). `avant` : moteur du 10b livré (commit 4e4a56d),
lancé depuis un worktree de ce commit (premier argument RACINE) ; `apres` : le moteur courant (RACINE = .).
Indicateur ajouté : minutes par match où un attaquant dangereux (hors porteur, à 25 m ou moins du but défendu, hors
hors-jeu sifflé) n'a pas de marqueur, mesuré après chaque mise à jour des rôles (ballon porté).
Usage : uv run python .scratch/v2-realisme/mesures/10b2-couverture.py RACINE DEBUT FIN SORTIE.json"""
import json
import random
import sys
from collections import defaultdict

root, start, end, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
sys.path.insert(0, root)
from ligue1sim.clubs import load_clubs
from ligue1sim.season import CLUBS_PATH

import v2engine.defense as defense
import v2engine.match as match

print("moteur :", defense.__file__, flush=True)
AUDIT_SEED = 20260923
tackles, unmarked = [0], [0.0]
real_tackle, real_update = match.resolve_tackle, defense.DefensiveRoles.update


def counting(*a, **k):
    tackles[0] += 1
    return real_tackle(*a, **k)


def watching(self, players, ball, bloc, now_s, *a, **k):
    real_update(self, players, ball, bloc, now_s, *a, **k)
    holder = next((p for p in players if p.name == ball.holder), None) if ball.holder else None
    if holder is None:
        return
    goal = defense.own_goal("away" if holder.team == "home" else "home")
    marked = {x.mate for x in self.assignments.values() if x.role == defense.MARQUAGE}
    unmarked[0] += match.TICK_SECONDS / 60.0 * sum(
        1 for p in players if p.team == holder.team and p.name != holder.name and p.poste != "GK"
        and p.position.distance_to(goal) <= defense.DANGER_M and ball.offside_out_until.get(p.name, 0.0) <= now_s
        and p.name not in marked)


match.resolve_tackle = counting
defense.DefensiveRoles.update = watching
clubs = load_clubs(CLUBS_PATH, "Ligue 1")
rows = []
for k in range(start, end):
    random.seed(AUDIT_SEED + k)
    tackles[0], unmarked[0] = 0, 0.0
    home, away = clubs[(2 * k) % len(clubs)], clubs[(2 * k + 1) % len(clubs)]
    trace = match.simulate_match(home, away)
    end_min = trace.ticks[-1].minute
    exits = defaultdict(float)  # "rôle|couvert|menacé" -> minutes (comme au 10b)
    last = {}
    for r in trace.line_exits + [None]:
        for name in (list(last) if r is None else [r.player]):
            prev = last.get(name)
            if prev is not None and prev.exit:
                exits[f"{prev.role}|{prev.covered}|{prev.threatened}"] += (end_min if r is None else r.minute) - prev.minute
        if r is not None:
            last[r.player] = r
    press = defaultdict(float)
    lastp = {}
    for r in trace.pressers + [None]:
        for team in (("home", "away") if r is None else (r.team,)):
            prev = lastp.get(team)
            if prev is not None and prev.player:
                press[f"{prev.poste}|{prev.in_zone}"] += (end_min if r is None else r.minute) - prev.minute
        if r is not None:
            lastp[r.team] = r
    rows.append({"k": k, "score": [trace.home_goals, trace.away_goals], "shots": len(trace.shots),
                 "offsides": len(trace.offsides), "fouls": len(trace.fouls), "tackles": tackles[0],
                 "exits": dict(exits), "press": dict(press), "unmarked": unmarked[0]})
    print(k, rows[-1]["score"], flush=True)
    json.dump(rows, open(out, "w"))

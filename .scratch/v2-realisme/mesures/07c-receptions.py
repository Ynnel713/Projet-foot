"""Ticket 07c : réceptions tracées (`trace.receptions`) sur des matchs du moteur, graines d'audit 20260923 + k, mêmes
clubs que `scripts/measure_v2.py`. Usage : uv run python .scratch/v2-realisme/mesures/07c-receptions.py N DEBUT > lot.json
puis 07c-receptions.py --synthese DOSSIER."""
import glob
import json
import random
import sys
from collections import Counter, defaultdict

sys.path.insert(0, ".")

if sys.argv[1] == "--synthese":
    R = [r for f in sorted(glob.glob(f"{sys.argv[2]}/lot*.json")) for r in json.load(open(f))]
    matches = len({r["m"] for r in R})
    kinds = ("de face", "de profil", "dos au jeu")

    def line(name, S):
        c = Counter(r["kind"] for r in S)
        n = len(S) or 1
        print(f"{name:<34} {len(S) / matches:7.1f} par match  " + "  ".join(f"{k} {100 * c[k] / n:5.1f} %" for k in kinds))
    print(f"{matches} matchs, {len(R)} réceptions")
    line("toutes", R)
    for name, sel in (("passes reçues (receveur visé)", lambda r: r["intended"]),
                      ("autres (récupération, rebond...)", lambda r: not r["intended"])):
        line(name, [r for r in R if sel(r)])
    by_origin = defaultdict(list)
    for r in R:
        by_origin[r["origin"]].append(r)
    for o in sorted(by_origin):
        line(f"origine : {o}", by_origin[o])
    by_poste = defaultdict(list)
    for r in R:
        by_poste[r["poste"]].append(r)
    for p in ("GK", "DC", "LB", "RB", "MDC", "MC", "MOC", "AG", "AD", "BU"):
        if by_poste.get(p):
            line(f"poste {p} (passes reçues)", [r for r in by_poste[p] if r["intended"]])
    sys.exit()

import v2engine.match as match
from ligue1sim.clubs import load_clubs
from ligue1sim.season import CLUBS_PATH

n, start = int(sys.argv[1]), int(sys.argv[2])
clubs = load_clubs(CLUBS_PATH, "Ligue 1")
rows = []
for k in range(start, start + n):
    random.seed(20260923 + k)
    trace = match.simulate_match(clubs[(2 * k) % len(clubs)], clubs[(2 * k + 1) % len(clubs)])
    rows += [dict(m=k, kind=r.kind, poste=r.poste, origin=r.origin, intended=r.intended,
                  fg=round(r.facing_goal_deg, 1), bf=round(r.ball_facing_deg, 1)) for r in trace.receptions]
json.dump(rows, sys.stdout)

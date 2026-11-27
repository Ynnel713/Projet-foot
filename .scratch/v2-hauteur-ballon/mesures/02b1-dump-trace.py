"""Trace JSON d'un match complet (API V2) à graine fixée, et instants remarquables du ballon (ticket 02b1)."""
import json, random, sys
from ligue1sim.clubs import load_clubs
from ligue1sim.season import CLUBS_PATH
from api.routers import v2

clubs = load_clubs(CLUBS_PATH, "Ligue 1")
by_name = {c.name: c for c in clubs}
v2._find_club = lambda name: by_name[name]
random.seed(20260923)
out = v2.create_match(v2.SimulateV2Request(home=clubs[0].name, away=clubs[1].name))
open(sys.argv[1], "w").write(out.model_dump_json())
track = out.ball_track
top = max(range(len(track)), key=lambda i: track[i].z)
mid = next(i for i in range(len(track)) if 4.5 <= track[i].z <= 5.5)
print(json.dumps({"top": {"minute": track[top].minute, "z": track[top].z}, "mid": {"minute": track[mid].minute, "z": track[mid].z},
                  "aerial_points": sum(1 for p in track if p.z > 0), "max_tick_z": max(t.ball.z for t in out.ticks)}))

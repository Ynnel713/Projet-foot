"""Poids JSON de la réponse POST /api/v2/matches pour un match complet à graine fixée (ticket v2-hauteur-ballon/02b1)."""
import hashlib, random, sys
from ligue1sim.clubs import load_clubs
from ligue1sim.season import CLUBS_PATH
from api.routers import v2

clubs = load_clubs(CLUBS_PATH, "Ligue 1")
by_name = {c.name: c for c in clubs}
v2._find_club = lambda name: by_name[name]
random.seed(int(sys.argv[1]) if len(sys.argv) > 1 else 20260923)
out = v2.create_match(v2.SimulateV2Request(home=clubs[0].name, away=clubs[1].name))
js = out.model_dump_json()
print("octets", len(js.encode()), "images", len(out.ticks), "piste", len(out.ball_track),
      "score", out.home_goals, out.away_goals, "sha256", hashlib.sha256(js.encode()).hexdigest()[:16])

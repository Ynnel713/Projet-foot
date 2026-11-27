"""Réponses d'API figées pour la mesure de fluidité du 02b2 : clubs, compositions et trace complète d'un match (graine fixée)."""
import json, random, sys
from api.routers.leagues import list_perso_club_pool
from api.routers.v2 import SimulateV2Request, club_lineup, create_match

out = sys.argv[1]
clubs = [c.model_dump() for c in list_perso_club_pool()]
home, away = clubs[0]["name"], clubs[1]["name"]
random.seed(20260923)
trace = create_match(SimulateV2Request(home=home, away=away)).model_dump()
json.dump(clubs, open(f"{out}/clubs.json", "w"))
for side, name in (("home", home), ("away", away)):
    json.dump(club_lineup(name).model_dump(), open(f"{out}/lineup-{side}.json", "w"))
json.dump({"home": home, "away": away}, open(f"{out}/names.json", "w"))
json.dump(trace, open(f"{out}/trace.json", "w"))
print(home, away, len(trace["ticks"]), trace["home_goals"], trace["away_goals"])

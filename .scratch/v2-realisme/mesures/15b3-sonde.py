import random
from collections import Counter
from ligue1sim.clubs import load_clubs
from ligue1sim.season import CLUBS_PATH
import v2engine.match as match
from v2engine.atteinte import BODY_SHARE, FOOT_SHARE, CORPS, PIED, reach_m
clubs = load_clubs(CLUBS_PATH, "Ligue 1")
state = {"players": []}
c = Counter()
orig = match.body_part
def spy(player, z):
    part = orig(player, z)
    if part in (PIED, CORPS) and z > 0.3:
        for b in state["players"]:
            if b.team != player.team and b.poste != "GK" and b.position.distance_to(player.position) <= 1.0:
                c[f"{part} : adversaire à 1 m"] += 1
                if BODY_SHARE * b.height_m < z <= reach_m(b):
                    c[f"{part} : ballon à hauteur de tête de l'adversaire"] += 1
                if FOOT_SHARE * b.height_m < z:
                    c[f"{part} : ballon au-dessus de la hanche de l'adversaire"] += 1
    if part == CORPS:
        c["contacts au corps"] += 1
    return part
match.body_part = spy
for k in (0, 1):
    random.seed(20260923 + k)
    match.simulate_match(clubs[2*k], clubs[2*k+1], observer=lambda t, ps, b, s: state.__setitem__("players", ps))
print(dict(c))

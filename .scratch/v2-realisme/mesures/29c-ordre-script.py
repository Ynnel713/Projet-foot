"""Ticket v2-realisme/29c, mesure en lecture seule : à chaque pas où le ballon en jeu touche quelqu'un
(`match._ball_contacts`), premier joueur selon l'instant d'entrée actuel de `match._contacts` et selon l'instant d'entrée
corrigé (pied de la perpendiculaire sur la droite du pas, pas le point rabattu sur le pas). Compte les pas où le premier
change, et s'il change d'équipe, par rôle (receveur visé, lecteur, autre). Moteur non modifié.
Usage : uv run python .scratch/v2-realisme/mesures/29c-ordre-script.py N DEBUT"""
import json
import math
import random
import sys

sys.path.insert(0, ".")
import v2engine.match as match
from ligue1sim.clubs import load_clubs
from ligue1sim.season import CLUBS_PATH

AUDIT_SEED = 20260923
real_contacts, real_bc = match._contacts, match._ball_contacts
fixed_mode = {"on": False}
stats = {"steps": 0, "changed": 0, "team": 0, "kinds": {}}


def fixed_contacts(start, end, dt, players, released_by=None, radius=match.CONTROL_RADIUS_M):
    if not fixed_mode["on"]:
        return real_contacts(start, end, dt, players, released_by, radius)
    hits = []
    for player in players:
        r0 = start - (player.position - player.velocity * dt)
        r1 = end - player.position
        seg = r1 - r0
        l2 = seg.x * seg.x + seg.y * seg.y
        if player.name == released_by and l2 >= 1e-12 and r0.length() < match.CONTROL_RADIUS_M and r1.length() >= r0.length():
            continue
        foot = 0.0 if l2 < 1e-12 else -(r0.x * seg.x + r0.y * seg.y) / l2
        s = min(1.0, max(0.0, foot))
        closest = r0 + seg * s
        if closest.length() < radius:
            if l2 < 1e-12 or r0.length() < radius:
                entry = 0.0
            else:
                perp = (r0 + seg * foot).length()
                entry = max(0.0, foot - math.sqrt(max(0.0, radius**2 - perp**2) / l2))
            hits.append((entry, closest.length(), player))
    hits.sort(key=lambda h: (h[0], h[1]))
    return hits


def role(ball, p):
    return "receveur" if p.name == ball.receiver else "lecteur" if p.name in ball.readers else "autre"


def ball_contacts(start, end, dt, players, ball, now_s=0.0, ground=True):
    fixed_mode["on"] = False
    old = real_bc(start, end, dt, players, ball, now_s, ground)
    fixed_mode["on"] = True
    new = real_bc(start, end, dt, players, ball, now_s, ground)
    fixed_mode["on"] = False
    if old:
        stats["steps"] += 1
        if new and new[0][2].name != old[0][2].name:
            stats["changed"] += 1
            stats["team"] += new[0][2].team != old[0][2].team
            k = f"{role(ball, old[0][2])} -> {role(ball, new[0][2])}" + (" (autre équipe)" if new[0][2].team != old[0][2].team else "")
            stats["kinds"][k] = stats["kinds"].get(k, 0) + 1
    return old


match._contacts, match._ball_contacts = fixed_contacts, ball_contacts
n, start = int(sys.argv[1]), int(sys.argv[2])
clubs = load_clubs(CLUBS_PATH, "Ligue 1")
for k in range(start, start + n):
    random.seed(AUDIT_SEED + k)
    match.simulate_match(clubs[(2 * k) % len(clubs)], clubs[(2 * k + 1) % len(clubs)])
json.dump(stats, sys.stdout, ensure_ascii=False)

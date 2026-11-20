"""Enregistrement du ticket v2-realisme/18p (copie de `18o-diag-script.py`, plus le côté signé de chaque adversaire par rapport à la ligne passeur -> receveur, `side`, positif à gauche, même convention que `ang_deg`) ; celui du 18o : en plus, postes du passeur et du receveur, vitesse de départ réalisée sur la vitesse idéale (`v_ratio`), écart d angle réalisé (`ang_deg`), vitesse du receveur (`rv`, composante vers le passeur `rv_back`), vitesse de chaque adversaire vers la ligne de passe (`close`). Moteur non modifié. Lecture seule
du moteur (enveloppes autour de fonctions, aucun tirage aléatoire en plus). Pour chaque passe de jeu au sol (hors remises
en jeu, hors passe longue en l'air) : chance évaluée au départ (`possession.pass_success_probability`, mêmes arguments
que la passe jouée), ses deux facteurs (coupe de la table, part non perdue par bande d'écart), Passing du passeur ; pour
chaque adversaire de champ : avancée et distance à la trajectoire passeur -> receveur, distance au receveur et au point
visé, temps d'arrivée au point visé (`defense.arrival_time_s`) contre celui du receveur ; issue : premier joueur à
toucher le ballon, ballon sorti ou sifflé avec remise pour l'adversaire, ballon mort.
Usage : uv run python .scratch/v2-realisme/mesures/18p-diag-script.py N DEBUT > sortie.json"""
import json
import math
import random
import sys

sys.path.insert(0, ".")
import v2engine.match as match
import v2engine.possession as P
from ligue1sim.clubs import load_clubs
from ligue1sim.season import CLUBS_PATH
from v2engine.condition import effective_rating
from v2engine.defense import arrival_time_s

AUDIT_SEED = 20260923
rows, state = [], {"pending": None, "restart": False, "now": 0.0}
real_vel, real_ctrl, real_restart = match.pass_velocity, match.attempt_control, match._play_restart


def seg_info(a, b, p):
    path = b - a
    L = path.length()
    if L < 1e-9:
        return 0.0, p.distance_to(a)
    d = path * (1.0 / L)
    rel = p - a
    along = rel.x * d.x + rel.y * d.y
    cl = max(0.0, min(L, along))
    return along, p.distance_to(a + d * cl)


def components(passer, target, opponents, backheel, one_touch):
    """Facteurs de `pass_success_probability` au sol : produit de coupe, poids des bandes d'écart."""
    keep = 1.0
    for o in opponents:
        keep *= 1.0 - P._cut_chance(passer.position, target.position, o)
    length = P._aim_distance(passer, target)
    sigma = P.pass_error_sigma_rad(passer, opponents, backheel, one_touch)
    along, across = P.dosage_gap(passer, target)
    weights, below = [], 0.0
    for limit, _share in P._LATERAL_NOT_LOST:
        within = P._within(limit, along, across, length, sigma)
        weights.append(round(within - below, 5))
        below = within
    return keep, weights


def pass_velocity(passer, target, opponents=(), backheel=False, one_touch=False, lofted=False):
    if state["restart"] or lofted:
        state["pending"] = None
        return real_vel(passer, target, opponents, backheel, one_touch, lofted)
    chance = P.pass_success_probability(passer, target, opponents, backheel, one_touch)
    keep, weights = components(passer, target, opponents, backheel, one_touch)
    aim = P.pass_aim(passer, target)
    t_recv = arrival_time_s(target, aim)
    opp = []
    for o in opponents:
        if o.poste == "GK" and o.position.distance_to(target.position) > 15.0:
            continue
        along, gap = seg_info(passer.position, target.position, o.position)
        foot = passer.position + (target.position - passer.position).normalized() * max(0.0, along)
        to_line = foot - o.position
        close = (o.velocity.x * to_line.x + o.velocity.y * to_line.y) / to_line.length() if to_line.length() > 1e-6 else 0.0
        line = target.position - passer.position
        side = (line.x * (o.position.y - passer.position.y) - line.y * (o.position.x - passer.position.x)) / line.length() \
            if line.length() > 1e-9 else 0.0
        opp.append(dict(n=o.name, close=round(close, 2), side=round(side, 2), along=round(along, 2), gap=round(gap, 2), cut=round(P._cut_chance(passer.position, target.position, o), 4),
                        to_recv=round(o.position.distance_to(target.position), 2),
                        to_aim=round(o.position.distance_to(aim), 2),
                        dt_aim=round(arrival_time_s(o, aim) - t_recv, 3)))
    v = real_vel(passer, target, opponents, backheel, one_touch, lofted)
    axis = aim - passer.position
    ideal = P._launch_speed(axis.length())
    ang = math.degrees(math.atan2(axis.x * v.y - axis.y * v.x, axis.x * v.x + axis.y * v.y)) if axis.length() > 1e-9 else 0.0
    back = passer.position - target.position
    rv_back = (target.velocity.x * back.x + target.velocity.y * back.y) / back.length() if back.length() > 1e-9 else 0.0
    state["pending"] = dict(pp=passer.poste, rp=target.poste, v_ratio=round(v.length() / ideal, 4), ang_deg=round(ang, 3),
                            sigma_deg=round(math.degrees(P.pass_error_sigma_rad(passer, opponents, backheel, one_touch)), 3),
                            rv=round(target.velocity.length(), 2), rv_back=round(rv_back, 2),t=state["now"], L=round(passer.position.distance_to(target.position), 2), team=passer.team,
                            recv=target.name, passing=round(effective_rating(passer, "Passing"), 1),
                            chance=round(chance, 5), keep=round(keep, 5), w=weights, bh=bool(backheel),
                            ot=bool(one_touch), recv_to_aim=round(target.position.distance_to(aim), 2), opp=opp)
    return v


def attempt_control(player, *args, **kw):
    ok = real_ctrl(player, *args, **kw)
    p = state["pending"]
    if p is not None:
        p.update(first=player.name, first_team=player.team)
        rows.append(p)
        state["pending"] = None
    return ok


def play_restart(*a, **k):
    state["restart"] = True
    try:
        return real_restart(*a, **k)
    finally:
        state["restart"] = False


match.pass_velocity, match.attempt_control, match._play_restart = pass_velocity, attempt_control, play_restart


def observer(now_s, players, ball, scoring):
    state["now"] = now_s
    p = state["pending"]
    if p is None:
        return
    if ball.restart is not None:
        p.update(first=None, out=True, out_team=ball.restart.team)
        rows.append(p)
        state["pending"] = None
    elif ball.holder is None and ball.receiver is None and ball.velocity.length() < P.BALL_STOPPED_MPS:
        p.update(first=None, dead=True)
        rows.append(p)
        state["pending"] = None


n, start = int(sys.argv[1]), int(sys.argv[2])
clubs = load_clubs(CLUBS_PATH, "Ligue 1")
for k in range(start, start + n):
    random.seed(AUDIT_SEED + k)
    home, away = clubs[(2 * k) % len(clubs)], clubs[(2 * k + 1) % len(clubs)]
    match.simulate_match(home, away, observer=observer)
    state["pending"] = None
json.dump(rows, sys.stdout)

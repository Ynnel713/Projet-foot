"""Enregistrement du ticket v2-realisme/29c (copie de `18o-diag-script.py`, mêmes passes) : en plus, pour chaque adversaire
collé au receveur au départ de la passe (moins de 1,5 m, entre le passeur et lui), suivi pas à pas du vol du ballon dans
`match._ball_contacts` : distance au ballon en mouvement relatif (comme `match._contacts`), au pas où elle est la plus
petite : lecteur ou non, passe vue (`NON_READER_REACTION_S`), tourné vers le ballon selon `match._faces_pass`, angle entre
son cap et la direction d'où vient le ballon, vitesse, distance au receveur, avance sur le receveur vers le ballon (`ahead`) et
écart latéral (`side`). Moteur non modifié, lecture seule.
Usage : uv run python .scratch/v2-realisme/mesures/29c-diag-script.py N DEBUT > sortie.json"""

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
        opp.append(dict(n=o.name, close=round(close, 2), along=round(along, 2), gap=round(gap, 2), cut=round(P._cut_chance(passer.position, target.position, o), 4),
                        to_recv=round(o.position.distance_to(target.position), 2),
                        to_aim=round(o.position.distance_to(aim), 2),
                        dt_aim=round(arrival_time_s(o, aim) - t_recv, 3)))
    marks = {}
    for o in opponents:
        along, gap = seg_info(passer.position, target.position, o.position)
        if o.poste != "GK" and o.position.distance_to(target.position) < 1.5 and 0.0 < along < passer.position.distance_to(target.position):
            marks[o.name] = dict(n=o.name, gap0=round(gap, 2), d0=round(o.position.distance_to(target.position), 2), dmin=99.0)
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
                            ot=bool(one_touch), recv_to_aim=round(target.position.distance_to(aim), 2), opp=opp, marks=marks)
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


real_bc = match._ball_contacts


def ball_contacts(start, end, dt, players, ball, now_s=0.0, ground=True):
    p = state["pending"]
    if p is not None and p.get("marks") and ball.receiver == p["recv"]:
        recv = next((q for q in players if q.name == p["recv"]), None)
        for q in players:
            m = p["marks"].get(q.name)
            if m is None:
                continue
            r0 = start - (q.position - q.velocity * dt)
            r1 = end - q.position
            seg = r1 - r0
            l2 = seg.x * seg.x + seg.y * seg.y
            s = 0.0 if l2 < 1e-12 else min(1.0, max(0.0, -(r0.x * seg.x + r0.y * seg.y) / l2))
            d = (r0 + seg * s).length()
            if d < m["dmin"]:
                bv = ball.velocity
                inc = bv * -1.0
                ang = 0.0 if inc.length() < 1e-9 else math.degrees(math.acos(max(-1.0, min(1.0, (q.facing.x * inc.x + q.facing.y * inc.y) / inc.length()))))
                m.update(dmin=round(d, 3), reader=q.name in ball.readers,
                         seen=ball.pass_started_s is not None and now_s - ball.pass_started_s >= match.NON_READER_REACTION_S,
                         faces=match._faces_pass(q, start, end, ball.last_pass_team), ang_in=round(ang, 1),
                         spd=round(q.velocity.length(), 2), ground=ground,
                         to_recv=round(q.position.distance_to(recv.position), 2) if recv else None,
                         since=round(now_s - (ball.pass_started_s or 0.0), 2))
                if recv is not None and inc.length() > 1e-9:
                    u = inc.normalized()
                    rel = q.position - recv.position
                    m.update(ahead=round(rel.x * u.x + rel.y * u.y, 2), side=round(abs(rel.x * u.y - rel.y * u.x), 2))
    return real_bc(start, end, dt, players, ball, now_s, ground)


match.pass_velocity, match.attempt_control, match._play_restart = pass_velocity, attempt_control, play_restart
match._ball_contacts = ball_contacts


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

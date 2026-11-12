"""Diagnostic du ticket 18i : pourquoi une passe PRÉCISE est coupée autant courte que longue. Lecture seule du moteur
(enveloppes autour de fonctions publiques, sans tirage aléatoire en plus). Pour chaque passe de jeu (hors remises en
jeu) : précise ou non, longueur, premier joueur à toucher le ballon, son rôle (intention `cerveau`) à cet instant,
lecteur ou non (`anticipation.pass_readers`), distance au départ à la trajectoire et au receveur, avancée du contact.
Usage : uv run python .scratch/v2-realisme/mesures/18i-diag-script.py N START > sortie.json"""
import json
import random
import sys

sys.path.insert(0, ".")
import v2engine.match as match
import v2engine.possession as P
from ligue1sim.clubs import load_clubs
from ligue1sim.lineup import pick_best_formation
from ligue1sim.season import CLUBS_PATH

AUDIT_SEED = 20260923
rows, state = [], {"pending": None, "restart": False, "now": 0.0, "last_aim_exact": None}
roles = {}

real_aim, real_vel, real_readers = P.pass_aim, match.pass_velocity, match.pass_readers
real_ctrl, real_think, real_restart = match.attempt_control, match.think, match._play_restart


def exact_aim(passer, target):  # point visé sans erreur (même calcul que `pass_aim`, sans tirage)
    import math
    d = passer.position.distance_to(target.position)
    speed = P._launch_speed(d)
    lf = math.log(P.BALL_FRICTION_PER_S)
    arrival = max(P.BALL_STOPPED_MPS, speed + d * lf)
    travel = math.log(arrival / speed) / lf
    return target.position + target.velocity * (travel * P.dosage_quality(passer))


def pass_aim(passer, target, opponents=()):
    aim = real_aim(passer, target, opponents)
    state["accurate"] = aim.distance_to(exact_aim(passer, target)) < 1e-6
    return aim


def seg_info(a, b, p):
    path = b - a
    L = path.length()
    d = path * (1.0 / L)
    rel = p - a
    along = rel.x * d.x + rel.y * d.y
    cl = max(0.0, min(L, along))
    return along, p.distance_to(a + d * cl)


def pass_velocity(passer, target, *args, **kw):
    opponents = args[0] if args else kw.get("opponents", ())
    v = real_vel(passer, target, *args, **kw)
    if state["restart"]:
        state["pending"] = None
        return v
    L = passer.position.distance_to(target.position)
    opp = []
    for o in opponents:
        along, gap = seg_info(passer.position, target.position, o.position)
        opp.append(dict(n=o.name, along=round(along, 2), gap=round(gap, 2),
                        to_passer=round(o.position.distance_to(passer.position), 2),
                        to_recv=round(o.position.distance_to(target.position), 2),
                        role=roles.get(o.name, "")))
    state["pending"] = dict(t=state["now"], L=round(L, 2), acc=state.get("accurate"), team=passer.team,
                            recv=target.name, passer=passer.name, speed=round(v.length(), 2),
                            recv_speed=round(target.velocity.length(), 2), opp=opp, readers=[],
                            start=(passer.position.x, passer.position.y),
                            tgt=(target.position.x, target.position.y))
    return v


def pass_readers(start, velocity, aim, opponents):
    r = real_readers(start, velocity, aim, opponents)
    if state["pending"] is not None and not state["restart"]:
        state["pending"]["readers"] = sorted(r)
    return r


def attempt_control(player, *args, **kw):
    ok = real_ctrl(player, *args, **kw)
    p = state["pending"]
    if p is not None:
        sx, sy = p["start"]
        tx, ty = p["tgt"]
        from v2engine.geometry import Vec2
        along, gap = seg_info(Vec2(sx, sy), Vec2(tx, ty), player.position)
        rcv = next((q for q in state.get("players", []) if q.name == p["recv"]), None)
        if rcv is not None:
            r_along, r_gap = seg_info(Vec2(sx, sy), Vec2(tx, ty), rcv.position)
            p.update(r_dist=round(rcv.position.distance_to(player.position), 2), r_along=round(r_along, 2),
                     r_gap=round(r_gap, 2), ball_speed=round(args[0].length(), 2) if args else None)
        p.update(first=player.name, first_team=player.team, ok=ok, dt=round(state["now"] - p["t"], 2),
                 c_along=round(along, 2), c_gap=round(gap, 2), first_role=roles.get(player.name, ""))
        rows.append(p)
        state["pending"] = None
    return ok


def think(player, *args, **kw):
    it = real_think(player, *args, **kw)
    roles[player.name] = f"{it.role}|{it.action}"
    return it


def play_restart(*a, **k):
    state["restart"] = True
    try:
        return real_restart(*a, **k)
    finally:
        state["restart"] = False


import os
REACH = float(os.environ.get("REACH_18I", "0"))  # essai : portée du receveur visé (0 = moteur tel quel)
real_contacts = match._contacts


def contacts(start, end, dt, players, released_by=None, radius=match.CONTROL_RADIUS_M):
    hits = real_contacts(start, end, dt, players, released_by, radius)
    ball = state.get("ball")
    if not REACH or ball is None or ball.receiver is None or ball.shot_flight is not None or radius != match.CONTROL_RADIUS_M:
        return hits
    rcv = [q for q in players if q.name == ball.receiver]
    extra = real_contacts(start, end, dt, rcv, released_by, REACH)
    hits = [h for h in hits if h[2].name != ball.receiver] + extra
    hits.sort(key=lambda h: (h[0], h[1]))
    return hits


if REACH:
    match._contacts = contacts
P.pass_aim, match.pass_velocity, match.pass_readers = pass_aim, pass_velocity, pass_readers
match.attempt_control, match.think, match._play_restart = attempt_control, think, play_restart


def observer(now_s, players, ball, scoring):
    state["now"] = now_s
    state["players"] = players
    state["ball"] = ball
    p = state["pending"]
    if p is not None:
        rcv = next((q for q in players if q.name == p["recv"]), None)
        if rcv is not None:
            d = rcv.position.distance_to(ball.position)
            if d < p.get("rmin", 1e9):
                p.update(rmin=round(d, 2), rmin_t=round(now_s - p["t"], 2), rmin_bs=round(ball.velocity.length(), 2),
                         rmin_rs=round(rcv.velocity.length(), 2), rmin_role=roles.get(rcv.name, ""))
            p.setdefault("rtrack", []).append((round(now_s - p["t"], 2), round(d, 2), round(rcv.velocity.length(), 2),
                                               round(ball.velocity.length(), 2)))
    if p is not None and ball.holder is None and ball.receiver is None and ball.velocity.length() < P.BALL_STOPPED_MPS:
        p.update(first=None, dead=True)
        rows.append(p)
        state["pending"] = None
    if p is not None and ball.restart is not None:
        p.update(first=None, out=True, out_team=ball.restart.team)
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

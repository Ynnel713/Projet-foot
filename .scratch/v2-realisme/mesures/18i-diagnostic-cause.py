"""Ticket 18i : diagnostic des coupes de passes précises (qui touche le premier, où, et pourquoi).
Usage : uv run python .scratch/v2-realisme/mesures/18i-diagnostic-cause.py N SORTIE.json [DÉBUT]
Lecture seule du moteur : enveloppes de `possession.pass_aim`, `match.pass_velocity`, `match.attempt_control` qui
appellent l'original sans tirage supplémentaire (la précision est déduite en recalculant le point visé sans tirage)."""
from __future__ import annotations

import json
import math
import os
import random
import sys
from collections import Counter
from concurrent.futures import ProcessPoolExecutor

from ligue1sim.clubs import load_clubs
from ligue1sim.season import CLUBS_PATH
import v2engine.match as match
import v2engine.possession as possession
from v2engine.geometry import Vec2
from v2engine.possession import BALL_FRICTION_PER_S, BALL_STOPPED_MPS, dosage_quality

AUDIT_SEED = 20260923
SHORT, MEDIUM = 13.7, 27.4  # catégories FBref en mètres (15 et 30 yards)


def _length_class(d: float) -> str:
    return "courte" if d < SHORT else "moyenne" if d < MEDIUM else "longue"


def _precise_aim(passer, target) -> Vec2:
    distance = passer.position.distance_to(target.position)
    speed = possession._launch_speed(distance)
    log_f = math.log(BALL_FRICTION_PER_S)
    arrival = max(BALL_STOPPED_MPS, speed + distance * log_f)
    travel_s = math.log(arrival / speed) / log_f
    return target.position + target.velocity * (travel_s * dosage_quality(passer))


def _along_gap(start: Vec2, end: Vec2, p: Vec2) -> tuple[float, float]:
    path = end - start
    length = path.length()
    d = path * (1.0 / length)
    rel = p - start
    along = rel.x * d.x + rel.y * d.y
    return along, abs(rel.x * d.y - rel.y * d.x)


def one(k: int) -> Counter:
    clubs = load_clubs(CLUBS_PATH, "Ligue 1")
    random.seed(AUDIT_SEED + k)
    home, away = clubs[(2 * k) % len(clubs)], clubs[(2 * k + 1) % len(clubs)]
    c: Counter = Counter()
    state: dict = {"open": None, "last_aim": None, "ball": None}
    real_aim, real_velocity, real_control = possession.pass_aim, match.pass_velocity, match.attempt_control

    def pass_aim(passer, target, opponents=()):
        aim = real_aim(passer, target, opponents)
        expected = _precise_aim(passer, target)
        state["last_aim"] = (aim, aim.distance_to(expected) < 1e-9)
        return aim

    def pass_velocity(passer, target, opponents=()):
        velocity = real_velocity(passer, target, opponents)
        aim, precise = state["last_aim"]
        length = passer.position.distance_to(target.position)
        nearest = min(opponents, key=lambda o: o.position.distance_to(passer.position)) if opponents else None
        marker = min(opponents, key=lambda o: o.position.distance_to(target.position)) if opponents else None
        state["open"] = {"recv_min": math.inf, "recv_late": False, "passer": passer, "target": target.name, "start": passer.position, "aim": aim,
                         "precise": precise, "cls": _length_class(length), "length": length,
                         "opp": {o.name: o.position for o in opponents},
                         "presser": nearest.name if nearest and nearest.position.distance_to(passer.position) < 3.0 else None,
                         "marker": marker.name if marker and marker.position.distance_to(target.position) < 2.0 else None,
                         "target_at": target.position, "readers": None, "restart": state["ball"] is not None
                         and state["ball"].restart is not None}
        return velocity

    def close(outcome: str, player=None) -> None:
        o = state["open"]
        state["open"] = None
        if o is None or o["restart"]:
            return
        kind = "précise" if o["precise"] else "imprécise"
        base = f"{kind}|{o['cls']}"
        c[f"{base}|passes"] += 1
        c[f"{base}|{outcome}"] += 1
        if outcome != "adversaire" or player is None:
            return
        name = player.name
        along, gap = _along_gap(o["start"], o["aim"], o["opp"].get(name, player.position))
        frac = _along_gap(o["start"], o["aim"], player.position)[0] / max(1e-9, (o["aim"] - o["start"]).length())
        role = ("presseur" if name == o["presser"] else "marqueur du receveur" if name == o["marker"]
                else "lecteur" if o["readers"] and name in o["readers"] else "autre")
        c[f"{base}|coupe : {role}"] += 1
        zone = "0-3 m du passeur" if frac * o["length"] < 3.0 else (
            "dernier quart" if frac > 0.75 else "milieu")
        c[f"{base}|coupe zone : {zone}"] += 1
        c[f"{base}|coupe : écart au départ (somme)"] += gap
        c[f"{base}|coupe : écart au départ < 1 m"] += gap < 1.0
        c[f"{base}|coupe : écart au départ > 3 m"] += gap > 3.0
        c[f"{base}|coupe : au-delà du point visé"] += frac > 1.0
        if frac > 1.0:  # le ballon a dépassé le point visé sans que le receveur le touche
            gap_min = o["recv_min"]
            c[f"{base}|au-delà : receveur au plus près (somme, m)"] += gap_min
            c[f"{base}|au-delà : receveur jamais à moins de 1 m"] += gap_min > 1.0
            c[f"{base}|au-delà : receveur à moins de 1 m"] += gap_min <= 1.0
            c[f"{base}|au-delà : receveur en retard (ballon passé avant lui)"] += o["recv_late"]

    def attempt_control(player, *args, **kwargs):
        result = real_control(player, *args, **kwargs)
        o = state["open"]
        if o is not None:
            if player.name == o["target"]:
                close("receveur visé" if result else "receveur visé, contrôle raté")
            elif player.team == o["passer"].team:
                close("autre coéquipier")
            else:
                close("adversaire", player)
        return result

    def observer(now_s, players, ball, scored):
        state["ball"] = ball
        o = state["open"]
        if o is None:
            return
        if o["readers"] is None:
            o["readers"] = dict(ball.readers)
            o["recv_min"], o["recv_late"] = math.inf, False
        receiver = next((p for p in players if p.name == o["target"]), None)
        if receiver is not None:
            d = receiver.position.distance_to(ball.position)
            o["recv_min"] = min(o["recv_min"], d)
            # ballon déjà plus loin que le receveur sur la trajectoire : il est passé devant lui
            along_ball = _along_gap(o["start"], o["aim"], ball.position)[0]
            along_recv = _along_gap(o["start"], o["aim"], receiver.position)[0]
            if along_ball > along_recv + 0.5 and d > 0.5:
                o["recv_late"] = True
        if ball.restart is not None:
            close("sortie ou arrêt")
        elif ball.holder is None and ball.velocity.length() < BALL_STOPPED_MPS:
            close("ballon arrêté sans contact")

    # Prototype (diagnostic seulement, hors moteur) : portée de jambe REACH_M pour le receveur visé ou pour tous.
    mode, reach = os.environ.get("REACH_MODE", "aucun"), float(os.environ.get("REACH_M", "1.0"))
    real_contacts = match._contacts

    def contacts(start, end, dt, players, released_by=None, radius=match.CONTROL_RADIUS_M, **kwargs):
        if mode == "aucun" or radius != match.CONTROL_RADIUS_M:
            return real_contacts(start, end, dt, players, released_by, radius, **kwargs)
        ball = state["ball"]
        if mode == "tous":
            body = real_contacts(start, end, dt, players, released_by, radius)
            wide = [h for h in real_contacts(start, end, dt, players, released_by, reach) if h[2].name != released_by]
            names = {h[2].name for h in wide}
            return sorted(wide + [h for h in body if h[2].name not in names], key=lambda h: (h[0], h[1]))
        expecting = {ball.receiver} if ball is not None else set()  # joueurs qui attendent le ballon
        if mode == "receveur+lecteurs" and ball is not None:
            expecting |= set(ball.readers)
        body = [h for h in real_contacts(start, end, dt, players, released_by, radius) if h[2].name not in expecting]
        wide = [h for h in real_contacts(start, end, dt, players, released_by, reach) if h[2].name in expecting]
        return sorted(body + wide, key=lambda h: (h[0], h[1]))

    possession.pass_aim, match.pass_velocity, match.attempt_control = pass_aim, pass_velocity, attempt_control
    match._contacts = contacts
    try:
        match.simulate_match(home, away, observer=observer)
    finally:
        possession.pass_aim, match.pass_velocity, match.attempt_control = real_aim, real_velocity, real_control
        match._contacts = real_contacts
    return c


if __name__ == "__main__":
    n, out = int(sys.argv[1]), sys.argv[2]
    start = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    total: Counter = Counter()
    with ProcessPoolExecutor(4) as pool:
        for c in pool.map(one, range(start, start + n)):
            total.update(c)
    json.dump(dict(total), open(out, "w"), indent=1, ensure_ascii=False, sort_keys=True)
    for kind in ("précise", "imprécise"):
        for cls in ("courte", "moyenne", "longue"):
            b = f"{kind}|{cls}"
            n_p = total[f"{b}|passes"]
            if not n_p:
                continue
            cut = total[f"{b}|adversaire"]
            print(f"{b}: n={n_p} reçue visé {total[b + '|receveur visé'] / n_p:.3f} coupée {cut / n_p:.3f}"
                  f" (presseur {total[b + '|coupe : presseur'] / n_p:.3f}, marqueur {total[b + '|coupe : marqueur du receveur'] / n_p:.3f},"
                  f" lecteur {total[b + '|coupe : lecteur'] / n_p:.3f}, autre {total[b + '|coupe : autre'] / n_p:.3f})")

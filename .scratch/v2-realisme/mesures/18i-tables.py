"""Ticket 18i : réussite des passes par longueur et relevé des tables de la chance évaluée (coupe par adversaire du 18g,
coupe imprévue, passe imprécise non perdue du 18h).
Usage : uv run python .scratch/v2-realisme/mesures/18i-tables.py N SORTIE.json [DÉBUT]
Lecture seule du moteur : enveloppes de `possession.pass_aim`, `match.pass_velocity`, `match.attempt_control` qui appellent
l'original sans tirage supplémentaire (la précision est déduite en recalculant le point visé sans tirage).
Définitions : perdue = un adversaire touche le ballon le premier, ou il sort ou est sifflé avec remise pour l'adversaire
(18h) ; réussie = premier contact par un coéquipier (18h) ; passes de remise en jeu exclues."""
from __future__ import annotations

import json
import math
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
NEAR_PASSER_M = 3.0
NEAR_BINS = (0.5, 1.0, 6.0)
PATH_BINS = (1.0, 2.0, 3.0, 4.0, 5.0, 6.0)


def _length_class(d: float) -> str:
    return "courte" if d < SHORT else "moyenne" if d < MEDIUM else "longue"


def _precise_aim(passer, target) -> Vec2:
    distance = passer.position.distance_to(target.position)
    speed = possession._launch_speed(distance)
    log_f = math.log(BALL_FRICTION_PER_S)
    arrival = max(BALL_STOPPED_MPS, speed + distance * log_f)
    travel_s = math.log(arrival / speed) / log_f
    return target.position + target.velocity * (travel_s * dosage_quality(passer))


def _bin(start: Vec2, end: Vec2, p: Vec2) -> str | None:
    """Case de la table du 18g pour un adversaire en `p` (passe de `start` vers `end`), comme `possession._cut_chance`."""
    path = end - start
    length = path.length()
    if length < 1e-9:
        return None
    d = path * (1.0 / length)
    rel = p - start
    along = rel.x * d.x + rel.y * d.y
    if not 0.0 < along < length:
        return None
    gap = p.distance_to(start + d * along)
    zone, bins = ("passeur", NEAR_BINS) if along <= NEAR_PASSER_M else ("trajet", PATH_BINS)
    return next((f"{zone}<{limit:g}" for limit in bins if gap < limit), None)


def one(k: int) -> dict:
    clubs = load_clubs(CLUBS_PATH, "Ligue 1")
    random.seed(AUDIT_SEED + k)
    home, away = clubs[(2 * k) % len(clubs)], clubs[(2 * k + 1) % len(clubs)]
    c: Counter = Counter()
    records: list = []  # une passe : [précise, longueur, non perdue, cases des adversaires, case du coupeur ou "hors"]
    state: dict = {"open": None, "last_aim": None, "ball": None}
    real_aim, real_velocity, real_control = possession.pass_aim, match.pass_velocity, match.attempt_control

    def pass_aim(passer, target, opponents=()):
        aim = real_aim(passer, target, opponents)
        state["last_aim"] = (aim, aim.distance_to(_precise_aim(passer, target)) < 1e-9)
        return aim

    def pass_velocity(passer, target, opponents=()):
        velocity = real_velocity(passer, target, opponents)
        _, precise = state["last_aim"]
        ball = state["ball"]
        state["open"] = {"team": passer.team, "target": target.name, "precise": precise,
                         "length": passer.position.distance_to(target.position),
                         "bins": {o.name: _bin(passer.position, target.position, o.position) for o in opponents},
                         "restart": ball is not None and ball.restart is not None}
        return velocity

    def close(lost: bool, outcome: str, cutter: str | None = None) -> None:
        o = state["open"]
        state["open"] = None
        if o is None or o["restart"]:
            return
        base = f"{'précise' if o['precise'] else 'imprécise'}|{_length_class(o['length'])}"
        c[f"{base}|passes"] += 1
        c[f"{base}|{outcome}"] += 1
        c[f"{base}|perdues"] += lost
        cut_bin = (o["bins"].get(cutter) or "hors") if cutter is not None else None
        records.append([o["precise"], round(o["length"], 2), not lost, [b for b in o["bins"].values() if b], cut_bin])

    def attempt_control(player, *args, **kwargs):
        result = real_control(player, *args, **kwargs)
        o = state["open"]
        if o is not None:
            if player.team == o["team"]:
                close(False, "receveur visé" if player.name == o["target"] else "autre coéquipier")
            else:
                close(True, "adversaire", player.name)
        return result

    def observer(now_s, players, ball, scored):
        state["ball"] = ball
        o = state["open"]
        if o is None:
            return
        if ball.restart is not None:
            close(ball.restart.team != o["team"], "sortie ou arrêt")
        elif ball.holder is None and ball.velocity.length() < BALL_STOPPED_MPS:
            close(False, "ballon arrêté sans contact")

    possession.pass_aim, match.pass_velocity, match.attempt_control = pass_aim, pass_velocity, attempt_control
    try:
        match.simulate_match(home, away, observer=observer)
    finally:
        possession.pass_aim, match.pass_velocity, match.attempt_control = real_aim, real_velocity, real_control
    return {"k": k, "counts": dict(c), "records": records}


if __name__ == "__main__":
    n, out = int(sys.argv[1]), sys.argv[2]
    start = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    with ProcessPoolExecutor(4) as pool:
        rows = list(pool.map(one, range(start, start + n)))
    json.dump(rows, open(out, "w"), ensure_ascii=False)
    total: Counter = Counter()
    for r in rows:
        total.update(r["counts"])
    for kind in ("précise", "imprécise", "toutes"):
        for cls in ("courte", "moyenne", "longue"):
            keys = ("précise", "imprécise") if kind == "toutes" else (kind,)
            n_p = sum(total[f"{x}|{cls}|passes"] for x in keys)
            if not n_p:
                continue
            get = lambda what: sum(total[f"{x}|{cls}|{what}"] for x in keys)  # noqa: E731
            ok = get("receveur visé") + get("autre coéquipier")
            print(f"{kind} {cls}: n={n_p} réussie {ok / n_p:.3f} reçue visé {get('receveur visé') / n_p:.3f}"
                  f" coupée {get('adversaire') / n_p:.3f} perdue {get('perdues') / n_p:.3f}")

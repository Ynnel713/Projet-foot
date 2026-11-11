"""Réglage du 12e (lecture seule du dépôt) : recharge candidate, 6 matchs du banc, course au-dessus de 19,8 km/h par
tranche de 15 min d'horloge, tous joueurs de champ et par bande de Stamina. Usage : python tune12e.py."""
import json
import random
import sys
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor

CONFIGS = {
    "A (actuel)": ((5.0, 0.03), (55.0, 0.08), (99.0, 0.16)),
    "B": ((5.0, 0.06), (55.0, 0.15), (99.0, 0.30)),
    "C": ((5.0, 0.05), (55.0, 0.12), (99.0, 0.24)),
}
HS = 5.5


def one(job):
    name, i = job
    from v2engine import movement
    movement._RECOVERY_POINTS = CONFIGS[name]
    from ligue1sim.clubs import load_clubs
    from scripts.measure_v2 import AUDIT_SEED, CLUBS_PATH, TICK_S
    from v2engine import match
    clubs = load_clubs(CLUBS_PATH, "Ligue 1")
    random.seed(AUDIT_SEED + i)
    home, away = clubs[(2 * i) % len(clubs)], clubs[(2 * i + 1) % len(clubs)]
    acc = defaultdict(float)
    last = {"t": 0.0}

    def obs(now_s, players, ball, scoring):
        dt = now_s - last["t"]
        last["t"] = now_s
        t = min(6, int(now_s // 900))
        for p in players:
            if p.poste == "GK":
                continue
            v = p.velocity.length()
            band = "<60" if p.stamina < 60 else ("60-75" if p.stamina < 75 else ">=75")
            for g in ("tous", band):
                acc[(g, t, "hs")] += v * dt if v > HS else 0.0
                acc[(g, t, "temps")] += dt
    match.simulate_match(home, away, duration_minutes=90.0, tick_seconds=TICK_S, observer=obs)
    return name, dict(acc)


if __name__ == "__main__":
    jobs = [(n, i) for n in CONFIGS for i in range(6)]
    tot = {n: defaultdict(float) for n in CONFIGS}
    with ProcessPoolExecutor(max_workers=6) as pool:
        for name, acc in pool.map(one, jobs):
            for k, v in acc.items():
                tot[name][k] += v
    out = {}
    for n, a in tot.items():
        row = {}
        for g in ("tous", "<60", "60-75", ">=75"):
            rate = [a[(g, t, "hs")] / a[(g, t, "temps")] * 60 if a[(g, t, "temps")] else None for t in range(7)]
            row[g] = {"m/min par tranche": [round(x, 1) if x else x for x in rate],
                      "75-90 / 0-15": round(rate[5] / rate[0], 3) if rate[0] and rate[5] else None}
        out[n] = row
    print(json.dumps(out, ensure_ascii=False, indent=1))

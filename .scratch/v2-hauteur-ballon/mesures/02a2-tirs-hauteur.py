"""Contrôle 02a2 : hauteur des tirs à la ligne contre leur issue, sur N matchs (graines de measure_v2)."""
import json, random, sys, hashlib
from concurrent.futures import ProcessPoolExecutor
sys.path.insert(0, ".")

def one(i):
    from ligue1sim.clubs import load_clubs
    from scripts.measure_v2 import CLUBS_PATH, AUDIT_SEED
    from v2engine import match
    clubs = load_clubs(CLUBS_PATH, "Ligue 1")
    random.seed(AUDIT_SEED + i)
    home, away = clubs[(2 * i) % len(clubs)], clubs[(2 * i + 1) % len(clubs)]
    live = {"trace": None}
    planned = {}
    real = match.line_height_m
    def spy(slope, sigma, d, diam):
        z = real(slope, sigma, d, diam)
        planned[len(live["trace"].shots) - 1] = (z, match.SHOT_AIM_HEIGHT_M + d * slope)
        return z
    match.line_height_m = spy
    zmax = [0.0]; zneg = [0]
    def obs(now, players, ball, scored):
        if ball.shot_flight is not None:
            zmax[0] = max(zmax[0], ball.z)
        if ball.z < 0: zneg[0] += 1
    trace = match.simulate_match(home, away, observer=obs, on_start=lambda t: live.update(trace=t))
    match.line_height_m = real
    shots = [dict(outcome=s.outcome, line_z=s.line_z_m, plan=planned.get(k)) for k, s in enumerate(trace.shots)]
    fp = hashlib.sha256(repr([t.ball for t in trace.ticks]).encode()).hexdigest()[:16]
    return dict(i=i, shots=shots, zmax_flight=zmax[0], zneg=zneg[0], score=(trace.home_goals, trace.away_goals), fp=fp)

if __name__ == "__main__":
    a, b, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    with ProcessPoolExecutor(int(sys.argv[4]) if len(sys.argv) > 4 else 4) as ex:
        res = list(ex.map(one, range(a, b)))
    json.dump(res, open(out, "w"), ensure_ascii=False)
    print("ok", len(res))

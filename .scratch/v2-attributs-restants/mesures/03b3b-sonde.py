"""Sonde du ticket v2-attributs-restants/03b3b (hors dépôt, lecture seule du moteur) : à chaque sortie inattendue
(gardiens forcés à Eccentricity 80), avance estimée du gardien sur l'adversaire (`rival_s - keeper_s`, négative : en
retard) et distance du point visé à son but ; issue dans les 6 s : premier à avoir le ballon (gardien, partenaire,
adversaire) ou ballon mort, et but encaissé dans les 15 s.

Utilisation : `PYTHONPATH=. PYTHONHASHSEED=0 <python> .scratch/v2-attributs-restants/mesures/03b3b-sonde.py 8`."""
import json, sys
from concurrent.futures import ProcessPoolExecutor

def one(i):
    from scripts.v2_chain import play
    from v2engine import gardien, match
    gardien.eccentricity = lambda k: 80.0
    events = []
    orig = gardien.whim
    def whim(player, course, ball):
        known = player.name in ball.keeper_whims
        r = orig(player, course, ball)
        if r and not known:
            events.append({"keeper": player.name, "team": player.team, "lead": course.rival_s - course.keeper_s,
                           "dist": course.point.distance_to(gardien.own_goal(player.team)), "t": match_now[0]})
        return r
    gardien.whim = whim
    import v2engine.cerveau as c
    c.gardien.whim = whim
    match_now = [0.0]
    orig_step = match._step_ball
    def step(ball, dt, players, now_s=0.0, *a, **k):
        match_now[0] = now_s / 60.0
        return orig_step(ball, dt, players, now_s, *a, **k)
    match._step_ball = step
    trace = play(i)
    teams = {p.name: p.team for t in trace.ticks[::120] for p in t.players}
    track = trace.ball_track
    out = []
    for e in events:
        issue = "rien"
        for b in track:
            if b.minute <= e["t"] or b.minute > e["t"] + 6 / 60:
                continue
            if b.dead:
                issue = "mort"; break
            if b.holder is not None:
                issue = "gardien" if b.holder == e["keeper"] else "partenaire" if teams.get(b.holder) == e["team"] else "adversaire"
                break
        goal = any(g.team != e["team"] and 0 <= g.minute - e["t"] <= 0.25 for g in trace.goals)
        out.append({"lead": e["lead"], "dist": e["dist"], "issue": issue, "but": goal})
    # issue : suivre la piste fine du ballon
    return out

if __name__ == "__main__":
    with ProcessPoolExecutor(2, max_tasks_per_child=1) as pool:
        rows = [x for r in pool.map(one, range(int(sys.argv[1]))) for x in r]
    print(len(rows))
    for r in sorted(rows, key=lambda r: r["lead"]):
        print(round(r["lead"], 2), round(r["dist"]), r["issue"], r["but"])

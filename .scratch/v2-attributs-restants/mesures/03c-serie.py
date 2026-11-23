"""Série des tickets v2-attributs-restants/03c1 et 03c2 (hors dépôt, lecture seule du moteur) : mêmes matchs du banc.
Pour chaque gardien : ses ballons joués (passes en jeu et remises), classés en longs ballons au pied (relance longue en
l'air, ou remise jouée à plus de 25 m), relances à la main (passe qui suit une prise en main : arrêt capté, ou ballon
pris dans sa surface ; 03c2) et autres passes ; pour chacun, longueur jusqu'au premier contact (ou ballon mort) et
équipe qui a le ballon ensuite. Option `--force NOTE` sur `--attr Kicking|Throwing` : tous les gardiens à cette note.

Utilisation : `PYTHONPATH=. PYTHONHASHSEED=0 <python> <script> 50 4 sortie.json [--attr Kicking --force 80]`."""

from __future__ import annotations

import bisect
import json
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path


def one(args):
    i, attr, force = args
    from scripts.v2_chain import play
    from v2engine import possession
    from v2engine.match import RELANCE_LONGUE
    from v2engine.restart import GOAL_KICK
    from v2engine.trace import PASSE, REMISE
    if force is not None:
        setattr(possession, attr.lower(), lambda keeper: float(force))
    in_hands_passes = set()
    if hasattr(possession, "keeper_throw"):  # 03c2 : passes jouées à la main, relevées à l'exécution
        original = possession.pass_velocity

        def spy(passer, target, opponents=(), backheel=False, one_touch=False, lofted=False):
            if possession.keeper_throw(passer, target, lofted):
                in_hands_passes.add((passer.name, round(passer.position.x, 3), round(passer.position.y, 3)))
            return original(passer, target, opponents, backheel, one_touch, lofted)
        possession.pass_velocity = spy
        import v2engine.match as m
        m.pass_velocity = spy
    trace = play(i)
    teams, keepers = {}, {}
    for tick in trace.ticks[::120]:  # remplaçants compris
        for pl in tick.players:
            teams[pl.name] = pl.team
            if pl.poste == "GK":
                keepers[pl.name] = pl.team
    track = trace.ball_track
    minutes = [b.minute for b in track]
    out = []
    for e in trace.events:
        if e.player not in keepers or e.kind not in (PASSE, REMISE):
            continue
        k = bisect.bisect_left(minutes, e.minute)
        if k >= len(track):
            continue
        start = track[k].position
        j = k + 1
        while j < len(track) and track[j].holder is None and not track[j].dead:
            j += 1
        if j >= len(track):
            continue
        end = track[j]
        length = start.distance_to(end.position)
        team = keepers[e.player]
        kept = None if end.dead else teams.get(end.holder) == team
        thrown = (e.player, round(start.x, 3), round(start.y, 3)) in in_hands_passes
        long_kick = e.detail == RELANCE_LONGUE or (e.kind == REMISE and length > 25.0)
        kind = "main" if thrown else "long" if long_kick else "autre"
        out.append({"gardien": e.player, "type": kind, "remise": e.detail if e.kind == REMISE else None,
                    "longueur": length, "gardé": kept})
    return {"match": i, "score": [trace.home_goals, trace.away_goals], "ballons": out}


if __name__ == "__main__":
    n, procs, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    attr = sys.argv[sys.argv.index("--attr") + 1] if "--attr" in sys.argv else "Kicking"
    force = float(sys.argv[sys.argv.index("--force") + 1]) if "--force" in sys.argv else None
    with ProcessPoolExecutor(max_workers=procs, max_tasks_per_child=1) as pool:
        rows = list(pool.map(one, [(i, attr, force) for i in range(n)]))
    Path(out).write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    print("ok", n, sum(sum(r["score"]) for r in rows) / n)

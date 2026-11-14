"""Diagnostic 12f (hors dépôt) : part des joueur-ticks sous le genou de la réserve rapide, sur 2 matchs du banc."""
import sys
sys.path.insert(0, ".")
from collections import Counter
import scripts.measure_v2 as mv
from scripts.v2_indicators import Collector
c = Counter(); low = []
orig = Collector.on_tick
def on_tick(self, now_s, players, ball, scoring_team, dt=0.1):
    for p in players:
        if p.poste == "GK":
            continue
        e = p.condition.sprint_energy
        c["ticks"] += 1
        c["<0.8"] += e < 0.8
        c["<0.5"] += e < 0.5
        c["<0.2"] += e < 0.2
        if p.velocity.length() > 6.94:
            c["sprint ticks"] += 1
            c["sprint ticks <0.8"] += e < 0.8
        low.append(e)
    return orig(self, now_s, players, ball, scoring_team, dt)
Collector.on_tick = on_tick
mv.run(2, start=50)
print({k: round(v / c["ticks"], 4) for k, v in c.items() if not k.startswith("sprint")})
print("part des ticks en sprint avec réserve < 0,8 :", round(c["sprint ticks <0.8"] / max(1, c["sprint ticks"]), 4))
print("minimum :", round(min(low), 3))

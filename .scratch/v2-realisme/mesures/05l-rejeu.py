"""Rejeu hors ligne (hors dépôt, lecture seule) des tirs capturés par 05l-capture.py : par zone (surface / hors
surface), chance de but non contré, cadrés et part des cadrés arrêtés selon les lois de `shooting`, sous les constantes
actuelles ou surchargées. Usage : PYTHONPATH=. uv run python 05l-rejeu.py <tirs.pkl> [NOM=valeur ...]"""
import pickle, sys
from v2engine import shooting as S
from v2engine.geometry import in_penalty_area

rows = pickle.load(open(sys.argv[1], "rb"))
for kv in sys.argv[2:]:
    k, v = kv.split("=")
    setattr(S, k, float(v))
out = {True: [], False: []}
for r in rows:
    sh, k, opp, g = r["shooter"], r["keeper"], r["opponents"], r["goal"]
    box = in_penalty_area(sh.team, sh.position)
    goal_share, blocked, goal_unblocked = S._flight_shares(sh, g, k, opp)
    kept = 1.0 - S._shank_share(sh, g, opp)
    w, u = S.on_target_axes(sh, g, opp)
    out[box].append((kept * goal_unblocked, kept * blocked, kept * w * u * (1 - 0), kept * goal_share, r["outcome"]))
for box, rs in out.items():
    n = len(rs)
    goal = sum(x[0] for x in rs) / n
    blk = sum(x[1] for x in rs) / n
    on = sum(x[2] for x in rs) / n  # cadrés hors contre (approx. : contre ignoré pour le cadrage)
    g_nb = sum(x[3] for x in rs) / n
    obs = sum(x[4] == "but" for x in rs) / n
    print(f"{'surface' if box else 'hors surface'} : {n} tirs, but prévu {goal:.3f} (observé {obs:.3f}), contré prévu {blk:.3f}, "
          f"cadré sans contre {on:.3f}, arrêtés parmi les cadrés (sans contre) {1 - g_nb / on:.3f}")

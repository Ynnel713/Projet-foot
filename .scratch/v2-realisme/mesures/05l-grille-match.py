"""Grille (hors dépôt) des constantes du gardien sur les tirs capturés : part des cadrés arrêtés par zone et but prévu.
Usage : PYTHONPATH=. uv run python 05l-grille-match.py <tirs.pkl>"""
import itertools, pickle, sys
from v2engine import shooting as S
from v2engine.geometry import in_penalty_area
rows = pickle.load(open(sys.argv[1], "rb"))
pre = [(r["shooter"], r["keeper"], r["opponents"], r["goal"], in_penalty_area(r["shooter"].team, r["shooter"].position)) for r in rows]
def stats():
    acc = {True: [0, 0, 0, 0], False: [0, 0, 0, 0]}
    for sh, k, opp, g, box in pre:
        gs, blk, gu = S._flight_shares(sh, g, k, opp)
        kept = 1 - S._shank_share(sh, g, opp)
        w, u = S.on_target_axes(sh, g, opp)
        a = acc[box]; a[0] += 1; a[1] += kept * gu; a[2] += kept * w * u; a[3] += kept * gs
    return {b: (a[1] / a[0], 1 - a[3] / a[2]) for b, a in acc.items()}
print("réaction plongeon portée | surface : but, arrêts | hors : but, arrêts")
for rea, mps, reach in itertools.product((0.25, 0.30), (3.0, 4.0, 5.0, 6.0), (2.8, 3.0, 3.2, 3.4)):
    S.KEEPER_REACTION_S, S.KEEPER_DIVE_MPS, S.KEEPER_DIVE_REACH_M = rea, mps, reach
    st = stats()
    print(f"{rea:.2f} {mps:.1f} {reach:.1f} | {st[True][0]:.3f} {st[True][1]:.3f} | {st[False][0]:.3f} {st[False][1]:.3f}")

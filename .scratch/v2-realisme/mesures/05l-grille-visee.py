"""Grille (hors dépôt) du plongeon du gardien AVEC la visée du tireur (`shooting._aimed`), sur les tirs capturés :
part des cadrés arrêtés par zone, but prévu, cadrés. Usage : PYTHONPATH=. uv run python 05l-grille-visee.py <tirs.pkl> [vitesses...]"""
import pickle, sys
from v2engine import shooting as S
from v2engine.geometry import in_penalty_area
rows = pickle.load(open(sys.argv[1], "rb"))
pre = [(r["shooter"], r["keeper"], r["opponents"], r["goal"], in_penalty_area(r["shooter"].team, r["shooter"].position)) for r in rows]
for mps in map(float, sys.argv[2:] or ["3", "4", "5", "6", "8", "10"]):
    S.KEEPER_DIVE_MPS = mps
    acc = {True: [0, 0.0, 0.0, 0.0], False: [0, 0.0, 0.0, 0.0]}
    for sh, k, opp, g, box in pre:
        kept, (gs, blk, gu), aim = S._aimed(sh, g, k, opp)
        _, under = S.on_target_axes(sh, g, opp)
        on = kept * S._wide_share(sh, g, S.shot_error_sigma(sh, g, opp), aim) * under
        a = acc[box]; a[0] += 1; a[1] += kept * gu; a[2] += on; a[3] += kept * gs
    out = " | ".join(f"{'surface' if b else 'hors'} but {a[1]/a[0]:.3f} cadrés {a[2]/a[0]:.3f} arrêts {1 - a[3]/a[2]:.3f}" for b, a in acc.items())
    print(f"plongeon {mps:4.1f} : {out}")

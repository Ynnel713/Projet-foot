"""Grille (hors dépôt) : visée d'un côté tiré au sort, distance au poteau x plongeon ; arrêts par zone sur les tirs
capturés et monotonie selon la note. Usage : PYTHONPATH=. uv run python 05l-grille-cote.py <tirs.pkl>"""
import itertools, pickle, sys
from tests.scenes import player
from v2engine import shooting as S
from v2engine.geometry import PITCH_LENGTH_M, Vec2, in_penalty_area
from v2engine.match import GOAL_CENTER_Y
rows = pickle.load(open(sys.argv[1], "rb"))
pre = [(r["shooter"], r["keeper"], r["opponents"], r["goal"], in_penalty_area(r["shooter"].team, r["shooter"].position)) for r in rows]
G = Vec2(PITCH_LENGTH_M, GOAL_CENTER_Y)
def mono():
    bad = 0
    for d, off in ((6, 0), (11, 0), (11, 8), (16, 0), (20, 0), (25, 0)):
        k = player("G", "away", x=PITCH_LENGTH_M - 1.0, y=GOAL_CENTER_Y, poste="GK")
        v = [S.occasion_quality(player("B", x=PITCH_LENGTH_M - d, y=GOAL_CENTER_Y + off, poste="BU", Finishing=n, Long_Shots=n), G, k, [k]) for n in (95, 60, 20)]
        bad += not (v[0] > v[1] > v[2])
    return bad
for inside, mps in itertools.product((1.0, 1.5, 2.0, 2.5), (3.0, 4.0, 5.0, 6.0)):
    S.AIM_INSIDE_POST_M, S.KEEPER_DIVE_MPS = inside, mps
    acc = {True: [0, 0.0, 0.0, 0.0], False: [0, 0.0, 0.0, 0.0]}
    for sh, k, opp, g, box in pre:
        _, (gs, blk, gu), aims = S._aimed(sh, g, k, opp)
        _, under = S.on_target_axes(sh, g, opp)
        sig = S.shot_error_sigma(sh, g, opp)
        on = sum(0.5 * (1 - S._shank_share(sh, g, opp, a)) * S._wide_share(sh, g, sig, a) * under for a in aims)
        a = acc[box]; a[0] += 1; a[1] += gu; a[2] += on; a[3] += gs
    out = " | ".join(f"{'surf' if b else 'hors'} but {a[1]/a[0]:.3f} cadrés {a[2]/a[0]:.3f} arrêts {1 - a[3]/a[2]:.3f}" for b, a in acc.items())
    print(f"poteau-{inside:.1f} plongeon {mps:.0f} : {out} | non monotones {mono()}/6")

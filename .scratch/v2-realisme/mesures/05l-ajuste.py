"""Recherche sur grille (hors dépôt) : constantes du gardien et de l'écart du tir qui rapprochent la chance physique
d'un tir propre de la table cible (log du rapport, 11 à 30 m, écarts 0, 5 et 10 m). Usage : PYTHONPATH=. uv run python 05l-ajuste.py"""
import itertools, math
from v2engine import shooting as S, match
from v2engine.geometry import PITCH_LENGTH_M, Vec2
from v2engine.movement import PlayerState

def make(at, team="home", poste="BU"):
    return PlayerState(name=poste, team=team, poste=poste, position=at, velocity=Vec2(0.0, 0.0), pace=60,
                       acceleration=60, stamina=60, home_target=at, attributes=None)
goal = Vec2(PITCH_LENGTH_M, match.GOAL_CENTER_Y)
GRID = [(d, o) for d in (11.0, 16.0, 20.0, 25.0, 30.0) for o in (0.0, 5.0, 10.0)]
SCENES = []
for d, o in GRID:
    at = Vec2(PITCH_LENGTH_M - d, match.GOAL_CENTER_Y + o)
    k = make(goal + (at - goal).normalized() * S.KEEPER_REFERENCE_M, "away", "GK")
    SCENES.append((make(at), k, S.base_chance(at, goal)))

def err():
    tot, worst = 0.0, 0.0
    for sh, k, t in SCENES:
        r = math.log(max(1e-4, S.physical_shot_chance(sh, goal, k, [k])) / t)
        tot += r * r; worst = max(worst, abs(r))
    return math.sqrt(tot / len(SCENES)), worst

base = (S.SHOT_ERROR_SIGMA_RAD, S.KEEPER_REACTION_S, S.KEEPER_DIVE_MPS, S.KEEPER_DIVE_REACH_M)
print("actuel", base, "rms log %.3f max %.3f" % err())
res = []
for sig, rea, mps, reach in itertools.product((0.18, 0.21, 0.24), (0.20, 0.25, 0.30), (3.0, 4.0, 5.0, 6.0), (2.8, 3.2, 3.6, 4.0)):
    S.SHOT_ERROR_SIGMA_RAD, S.KEEPER_REACTION_S, S.KEEPER_DIVE_MPS, S.KEEPER_DIVE_REACH_M = sig, rea, mps, reach
    res.append((err(), (sig, rea, mps, reach)))
res.sort()
for e, p in res[:12]:
    print(p, "rms %.3f max %.3f" % e)
print("σ fixe 0,18 :")
for e, p in [r for r in res if r[1][0] == 0.18][:6]:
    print(p, "rms %.3f max %.3f" % e)

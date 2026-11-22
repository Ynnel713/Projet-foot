"""Grille analytique (hors dépôt, lecture seule) : chance physique d'un tir propre (tireur et gardien neutres, gardien
bien placé, sans défenseur) contre la table cible du propriétaire (`shooting.base_chance`, logit `_XG_LOGIT`), cadrage
et part des cadrés arrêtés. Paramètres surchargeables : σ, réaction, plongeon, portée max, portée debout.
Usage : PYTHONPATH=. uv run python .scratch/v2-realisme/mesures/05l-grille.py [sigma reaction dive_mps dive_reach standing]"""
import sys
from v2engine import shooting as S
from v2engine import match
from v2engine.geometry import PITCH_LENGTH_M, Vec2
from v2engine.movement import PlayerState

if len(sys.argv) > 1:
    S.SHOT_ERROR_SIGMA_RAD, S.KEEPER_REACTION_S, S.KEEPER_DIVE_MPS, S.KEEPER_DIVE_REACH_M, S.KEEPER_STANDING_REACH_M = map(float, sys.argv[1:6])


def make(name, team, poste, at):
    return PlayerState(name=name, team=team, poste=poste, position=at, velocity=Vec2(0.0, 0.0), pace=60,
                       acceleration=60, stamina=60, home_target=at, attributes=None)


goal = Vec2(PITCH_LENGTH_M, match.GOAL_CENTER_Y)
print("dist écart | table  physique ratio | cadré  arrêtés/cadrés")
for d in (6.0, 11.0, 16.0, 20.0, 25.0, 30.0):
    for off in (0.0, 5.0, 10.0):
        at = Vec2(PITCH_LENGTH_M - d, match.GOAL_CENTER_Y + off)
        shooter = make("B", "home", "BU", at)
        keeper = make("G", "away", "GK", goal + (at - goal).normalized() * S.KEEPER_REFERENCE_M)
        phys = S.physical_shot_chance(shooter, goal, keeper, [keeper])
        table = S.base_chance(at, goal)
        w, u = S.on_target_axes(shooter, goal, [keeper])
        on = (1 - S._shank_share(shooter, goal, [keeper])) * w * u
        print(f"{d:4.0f} {off:5.0f} | {table:.3f}  {phys:.3f}  {phys / table:4.2f} | {on:.3f}  {1 - phys / on if on else 0:.2f}")

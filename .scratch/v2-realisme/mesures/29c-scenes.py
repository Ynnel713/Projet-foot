"""Ticket v2-realisme/29c : situations construites. Passe au sol de 12 m de (30 ; 34) vers un receveur immobile en (42 ; 34),
adversaire immobile devant, décalé, à côté ou derrière lui, tourné vers le ballon, vers le receveur ou de profil.
Moteur réel (`match._step_ball`) : premier joueur touché (contrôle toujours réussi), puis 400 tirages avec le vrai
contrôle (part où l'adversaire touche le premier, part où il garde le ballon).
Usage : uv run python .scratch/v2-realisme/mesures/29c-scenes.py"""
import random
import sys

sys.path.insert(0, ".")
from v2engine import match, possession
from v2engine.ball_state import BallState
from v2engine.geometry import Vec2
from v2engine.movement import PlayerState

ATTRS = ("First Touch", "Technique", "Composure", "Anticipation", "Positioning", "Passing", "Dribbling", "Decisions")


def player(name, team, pos, facing):
    return PlayerState(name=name, team=team, poste="DC", position=pos, velocity=Vec2(0, 0), pace=60, acceleration=60,
                       stamina=99, home_target=pos, facing=facing, attributes={k: 60 for k in ATTRS})


FACINGS = {"face ballon": Vec2(-1, 0), "face receveur": Vec2(1, 0), "profil": Vec2(0, 1)}
SPOTS = {"devant 0,5": Vec2(41.5, 34.0), "devant 1,0": Vec2(41.0, 34.0), "devant 0,5 décalé 0,5": Vec2(41.5, 34.5),
         "à côté 0,7": Vec2(42.0, 34.7), "derrière 0,5": Vec2(42.5, 34.0)}


def run(spot, facing, real, seed=0, dt=0.1):
    random.seed(seed)
    rec, mk = player("R", "home", Vec2(42, 34), Vec2(-1, 0)), player("M", "away", spot, facing)
    ball = BallState(position=Vec2(30, 34), velocity=Vec2(possession._launch_speed(12.0), 0), receiver="R", readers={},
                     last_pass_team="home", pass_started_s=0.0, released_by="passeur")
    orig, log = match.attempt_control, []

    def spy(p, *a, **k):
        log.append(p.name)
        return orig(p, *a, **k) if real else True

    match.attempt_control = spy
    try:
        for i in range(60):
            match._step_ball(ball, dt, [rec, mk], i * dt)
            if ball.holder is not None or ball.velocity.length() < 1e-9:
                break
    finally:
        match.attempt_control = orig
    return (log[0] if log else None), ball.holder


for sname, spot in SPOTS.items():
    for fname, f in FACINGS.items():
        first, _ = run(spot, f, real=False)
        runs = [run(spot, f, real=True, seed=s) for s in range(400)]
        print(f"{sname:24s} {fname:14s} premier touché : {first} | tirages : M premier "
              f"{sum(a == 'M' for a, _ in runs) / 400:.2f}, M garde {sum(h == 'M' for _, h in runs) / 400:.2f}")

"""Ticket v2-realisme/07a : orientation du corps, état propre et rotation bornée (`v2engine/orientation.py`)."""

from __future__ import annotations

import math
import random
from dataclasses import replace

from scenes import Scene, player, run, seed_scene
from v2engine.geometry import Vec2
from v2engine.orientation import (FAST_RUN_MPS, TURN_RATE_RAD_S, desired_facing, kickoff_facing, turn_towards,
                                  wrap)

DT = 0.1


def test_half_turn_lasts_180_degrees_over_the_turn_rate_within_one_step() -> None:
    # Critère du ticket : demi-tour demandé, durée = 180° / vitesse angulaire (0,5 s à 360°/s), à un pas près.
    facing, target, steps = 0.0, math.pi - 1e-6, 0
    while abs(wrap(target - facing)) > 1e-9:
        facing = turn_towards(facing, target, DT)
        steps += 1
        assert steps < 100
    expected = math.pi / TURN_RATE_RAD_S
    assert abs(steps * DT - expected) <= DT
    assert math.isclose(expected, 0.5)


def test_turn_is_bounded_per_step_and_takes_the_shortest_way() -> None:
    limit = TURN_RATE_RAD_S * DT
    # de 170° vers −170° : 20° par le plus court chemin (en passant par ±180°), pas 340° dans l'autre sens
    after = turn_towards(math.radians(170.0), math.radians(-170.0), DT)
    assert math.isclose(abs(wrap(after - math.radians(-170.0))), 0.0, abs_tol=1e-12)
    # grand écart : jamais plus que la limite d'un pas
    after = turn_towards(0.0, math.radians(120.0), DT)
    assert math.isclose(after, limit)
    assert -math.pi < turn_towards(math.radians(179.0), math.radians(-179.0), DT) <= math.pi


def test_desired_facing_running_fast_ball_otherwise_and_keeps_its_cap_with_the_ball_at_its_feet() -> None:
    at, ball = Vec2(50.0, 34.0), Vec2(40.0, 34.0)  # ballon derrière lui (vers x décroissant)
    fast = Vec2(0.0, FAST_RUN_MPS + 0.1)  # course rapide vers y croissant
    assert math.isclose(desired_facing(at, fast, ball, 0.0), math.pi / 2)
    slow = Vec2(0.0, FAST_RUN_MPS - 0.1)
    assert math.isclose(abs(desired_facing(at, slow, ball, 0.0)), math.pi)
    assert desired_facing(at, Vec2(0.0, 0.0), at + Vec2(0.05, 0.0), 1.234) == 1.234


def test_kickoff_facing_towards_the_opponent_goal() -> None:
    assert kickoff_facing("home") == 0.0  # `home` attaque vers x croissant
    assert kickoff_facing("away") == math.pi


def _scene(facing: float) -> Scene:
    players = [replace(player("A", "home", 50.0, 34.0, poste="MC"), facing=facing),
               replace(player("B", "away", 60.0, 30.0, poste="MC"), facing=math.pi)]
    return Scene.full(players, ball_at=Vec2(40.0, 34.0))


def test_in_play_the_cap_turns_at_most_at_the_turn_rate_and_ends_on_the_ball_or_the_run() -> None:
    seed_scene(7)
    scene = _scene(0.0)
    caps = []
    for _ in range(30):
        run(scene, DT)
        caps.append(scene.get("A").facing)
    steps = [abs(wrap(b - a)) for a, b in zip([0.0] + caps, caps)]
    assert max(steps) <= TURN_RATE_RAD_S * DT + 1e-9
    a = scene.get("A")
    expected = desired_facing(a.position, a.velocity, scene.ball.position, a.facing)
    assert abs(wrap(a.facing - expected)) < math.radians(40.0)  # il a rattrapé sa direction voulue, à un pas près


def test_the_cap_has_no_effect_on_play() -> None:
    # Critère « aucun effet sur le jeu » : même scène, même graine, cap de départ opposé -> mêmes positions et vitesses.
    logs = []
    for facing in (0.0, math.pi):
        seed_scene(11)
        scene = _scene(facing)
        run(scene, 5.0)
        logs.append(scene.log)
    assert logs[0] == logs[1]


def test_the_cap_reaches_the_trace_and_the_api_and_turns_within_the_rate() -> None:
    import v2engine.match as match
    from api.routers.v2 import _tick_out
    from ligue1sim.clubs import load_clubs
    from ligue1sim.season import CLUBS_PATH

    clubs = load_clubs(CLUBS_PATH, "Ligue 1")
    random.seed(20260923)
    caps: list[list[float]] = []  # cap de chaque joueur à chaque pas de simulation (0,1 s)
    times: list[float] = []
    trace = match.simulate_match(clubs[0], clubs[1], duration_minutes=2.0,
                                 observer=lambda now, players, ball, scored: (caps.append([p.facing for p in players]),
                                                                              times.append(now)))
    limit = TURN_RATE_RAD_S * match.TICK_SECONDS + 1e-9
    teams = [p.team for p in trace.ticks[0].players]
    # coup d'envoi : face au but adverse, à un pas de rotation près (le premier pas est déjà joué)
    assert all(abs(wrap(c - kickoff_facing(t))) <= limit for c, t in zip(caps[0], teams))
    assert len({round(c, 6) for row in caps for c in row}) > 50  # le cap vit pendant le match
    # mi-temps : tous replacés d'un coup, face au but adverse (à un pas près) ; ailleurs, rotation bornée à chaque pas
    half = next(k for k, now in enumerate(times) if now >= trace.second_half_start_minute * 60.0 - 1e-9)
    assert all(abs(wrap(c - kickoff_facing(t))) <= limit for c, t in zip(caps[half], teams))
    assert all(abs(wrap(b - a)) <= limit for k, (r0, r1) in enumerate(zip(caps, caps[1:]), start=1) if k != half
               for a, b in zip(r0, r1))
    out = _tick_out(trace.ticks[-1])
    assert [p.facing for p in out.players] == [p.facing for p in trace.ticks[-1].players] != [0.0] * 22


def test_the_holder_faces_where_he_carries_the_ball_never_backwards() -> None:
    # Réserve A1 de l'expert (12/11/2026) : le ballon du porteur est recopié sur sa position du pas précédent ; visé,
    # il retournait le porteur dos à sa course entre 1 et 5,5 m/s. Il regarde désormais où il conduit.
    seed_scene(3)
    players = [replace(player("A", "home", 40.0, 34.0, poste="MC"), facing=0.0),
               replace(player("B", "away", 95.0, 10.0, poste="DC"), facing=math.pi)]
    scene = Scene.full(players, holder="A")
    checked = 0
    for _ in range(30):
        run(scene, DT)
        a = scene.get("A")
        speed = a.velocity.length()
        if scene.ball.holder == "A" and 1.0 < speed < FAST_RUN_MPS:
            course = math.atan2(a.velocity.y, a.velocity.x)
            assert abs(wrap(a.facing - course)) < TURN_RATE_RAD_S * DT  # à moins d'un pas de rotation de sa course
            checked += 1
    assert checked >= 10  # la scène contient bien de la conduite entre 1 et 5,5 m/s


def test_a_still_holder_keeps_his_cap() -> None:
    at = Vec2(50.0, 34.0)
    assert desired_facing(at, Vec2(0.0, 0.0), at - Vec2(0.3, 0.0), 1.0, holding=True) == 1.0
    assert math.isclose(desired_facing(at, Vec2(2.0, 0.0), at - Vec2(0.2, 0.0), 1.0, holding=True), 0.0)

"""Type de réception (ticket v2-realisme/07c) : de face, de profil ou dos au jeu selon le cap du receveur et le but
adverse ; le receveur d'une passe en vol s'ouvre vers le but en gardant le ballon devant lui ; chaque contrôle est
tracé. Sans effet sur le jeu."""

from __future__ import annotations

import math

import pytest

from v2engine.ball_state import BallState
from v2engine.geometry import Vec2
from v2engine.match import _step_ball
from v2engine.movement import TURN_RATE_RAD_S, step
from v2engine.reception import (BACK_MIN_DEG, DE_FACE, DE_PROFIL, DOS_AU_JEU, FACE_MAX_DEG, OPEN_CONE_DEG,
                                attacking_goal, open_facing, reception_type)
from tests.scenes import player

AT = Vec2(60.0, 34.0)  # receveur « home », il attaque vers x = 105


def _angle(v: Vec2) -> float:
    return math.degrees(math.atan2(v.y, v.x))


def test_three_equal_sectors_and_a_half_plane_cone() -> None:
    assert (FACE_MAX_DEG, BACK_MIN_DEG, OPEN_CONE_DEG) == (60.0, 120.0, 90.0)
    assert attacking_goal("home") == Vec2(105.0, 34.0) and attacking_goal("away") == Vec2(0.0, 34.0)


@pytest.mark.parametrize("ball_from, expected", [
    (Vec2(40.0, 34.0), DOS_AU_JEU),  # ballon venant de derrière (de son camp) : il le regarde, dos au but
    (Vec2(60.0, 14.0), DE_PROFIL),  # de côté
    (Vec2(80.0, 34.0), DE_FACE),  # de face (passe en retrait venue du but adverse)
])
def test_receiver_looking_at_the_ball_gets_the_expected_type(ball_from, expected) -> None:
    """Receveur qui n'a pas eu le temps de s'ouvrir : son cap regarde le ballon (07a)."""
    facing = (ball_from - AT).normalized()
    assert reception_type(facing, AT, "home") == expected
    assert reception_type(Vec2(-facing.x, facing.y), Vec2(105.0 - AT.x, AT.y), "away") == expected  # symétrie


def test_sector_boundaries() -> None:
    def at(deg):
        return Vec2(math.cos(math.radians(deg)), math.sin(math.radians(deg)))
    assert reception_type(at(60.0), AT, "home") == DE_FACE
    assert reception_type(at(61.0), AT, "home") == DE_PROFIL
    assert reception_type(at(120.0), AT, "home") == DE_PROFIL
    assert reception_type(at(121.0), AT, "home") == DOS_AU_JEU


def test_open_facing_faces_the_goal_when_the_ball_is_in_front() -> None:
    target = open_facing(AT, Vec2(60.0, 14.0), "home", Vec2(0.0, -1.0))  # ballon de côté : à 90° du but
    assert _angle(target) == pytest.approx(0.0)


def test_open_facing_keeps_the_ball_at_the_edge_when_it_comes_from_behind() -> None:
    target = open_facing(AT, Vec2(40.0, 30.0), "home", Vec2(-1.0, 0.0))  # ballon derrière, un peu à droite (y < 34)
    to_ball = Vec2(40.0, 30.0) - AT
    between = math.degrees(math.acos((target.x * to_ball.x + target.y * to_ball.y) / to_ball.length()))
    assert between == pytest.approx(OPEN_CONE_DEG)
    assert reception_type(target, AT, "home") == DE_PROFIL
    assert target.y < 0.0  # il s'ouvre du côté du ballon : profil, pas dos au jeu


def test_open_facing_turns_to_the_side_he_already_faces_when_the_ball_is_exactly_behind() -> None:
    ball = Vec2(40.0, 34.0)
    assert open_facing(AT, ball, "home", Vec2(-1.0, 0.1)).y > 0.0
    assert open_facing(AT, ball, "home", Vec2(-1.0, -0.1)).y < 0.0


def test_receiver_with_time_ends_in_profile_without_time_back_to_play() -> None:
    """Ballon de derrière, receveur tourné vers lui : 90° à tourner. Avec 0,5 s il s'ouvre (profil) ; à un pas de
    l'arrivée, il reste dos au jeu (rotation bornée du 07a)."""
    ball = Vec2(40.0, 34.5)
    start = player("R", x=AT.x, y=AT.y)
    start = start.__class__(**{**start.__dict__, "facing": (ball - AT).normalized()})
    target = AT + open_facing(AT, ball, "home", start.facing) * 50.0

    def after(steps):
        p = start
        for _ in range(steps):
            p = step(p, 0.1, p.position, 0.0, look_at=target)
        return reception_type(p.facing, p.position, "home")
    assert after(1) == DOS_AU_JEU  # 36° tournés : encore à plus de 120° du but
    needed = math.ceil(math.radians(90.0) / (TURN_RATE_RAD_S * 0.1))
    assert after(needed) == DE_PROFIL


def test_controlled_ball_is_traced_with_its_type(monkeypatch) -> None:
    monkeypatch.setattr("v2engine.match.attempt_control", lambda *a, **k: True)
    receiver = player("R", x=60.0, y=34.0)
    receiver = receiver.__class__(**{**receiver.__dict__, "facing": Vec2(-1.0, 0.0)})  # dos au but adverse
    ball = BallState(position=Vec2(50.0, 34.0), velocity=Vec2(10.0, 0.0), receiver="R", last_pass_team="home",
                     pass_from=Vec2(50.0, 34.0))
    receptions: list = []
    for i in range(20):
        _step_ball(ball, 0.1, [receiver], i * 0.1, receptions=receptions)
        if ball.holder is not None:
            break
    assert ball.holder == "R" and len(receptions) == 1
    event = receptions[0]
    assert (event.player, event.team, event.poste, event.kind) == ("R", "home", receiver.poste, DOS_AU_JEU)
    assert event.facing_goal_deg == pytest.approx(180.0)
    assert event.ball_facing_deg == pytest.approx(0.0)  # il fait face au ballon
    assert event.intended and event.origin == "passe en profondeur"  # 10 m gagnés vers le but


def test_missed_control_is_not_a_reception(monkeypatch) -> None:
    monkeypatch.setattr("v2engine.match.attempt_control", lambda *a, **k: False)
    receiver = player("R", x=60.0, y=34.0)
    ball = BallState(position=Vec2(50.0, 34.0), velocity=Vec2(10.0, 0.0), receiver="R")
    receptions: list = []
    for i in range(12):
        _step_ball(ball, 0.1, [receiver], i * 0.1, receptions=receptions)
    assert receptions == []


def test_simulated_match_traces_receptions_of_every_type() -> None:
    import random

    from ligue1sim.clubs import load_clubs
    from ligue1sim.season import CLUBS_PATH
    from v2engine.match import simulate_match

    clubs = load_clubs(CLUBS_PATH, "Ligue 1")
    random.seed(20260923)
    trace = simulate_match(clubs[0], clubs[1], duration_minutes=10.0)
    kinds = {r.kind for r in trace.receptions}
    assert kinds == {DE_FACE, DE_PROFIL, DOS_AU_JEU}
    assert any(r.intended for r in trace.receptions)

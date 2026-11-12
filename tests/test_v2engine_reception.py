"""Ticket v2-realisme/07c : réception de face, de profil ou dos au jeu, et receveur qui s'ouvre avant le ballon."""

from __future__ import annotations

import math
from dataclasses import replace

from scenes import Scene, player, run, seed_scene
from v2engine.geometry import Vec2
from v2engine.orientation import DOS, FACE, PROFIL, desired_facing, reception_type

GOAL = Vec2(105.0, 34.0)  # but attaqué par `home`


def test_reception_type_by_angle_to_the_goal_60_and_120_degrees() -> None:
    at = Vec2(60.0, 34.0)  # but droit devant (angle 0)
    assert reception_type(math.radians(0.0), at, GOAL) == FACE
    assert reception_type(math.radians(59.0), at, GOAL) == FACE
    assert reception_type(math.radians(-61.0), at, GOAL) == PROFIL
    assert reception_type(math.radians(119.0), at, GOAL) == PROFIL
    assert reception_type(math.radians(121.0), at, GOAL) == DOS
    assert reception_type(math.pi, at, GOAL) == DOS


def test_the_receiver_aims_halfway_between_the_ball_and_the_goal() -> None:
    at, still = Vec2(60.0, 34.0), Vec2(0.0, 0.0)
    # ballon de côté (vers y décroissant) : à mi-chemin, 45° du but -> de face
    assert math.isclose(desired_facing(at, still, Vec2(60.0, 14.0), 0.0, goal=GOAL), -math.pi / 4)
    # ballon de face : vers le but
    assert math.isclose(desired_facing(at, still, Vec2(80.0, 34.0), 0.0, goal=GOAL), 0.0, abs_tol=1e-12)
    # ballon exactement derrière : la perpendiculaire au but la plus proche de son cap (ici, 100° -> +90°)
    assert math.isclose(desired_facing(at, still, Vec2(40.0, 34.0), math.radians(100.0), goal=GOAL), math.pi / 2)
    # sans passe pour lui (pas de but donné), il regarde le ballon comme au 07a
    assert math.isclose(abs(desired_facing(at, still, Vec2(40.0, 34.0), 0.0)), math.pi)


def _reception(passer_at: Vec2, speed: float, agility: int = 55, marker_at: Vec2 | None = None) -> str:
    """Passe de A (à `passer_at`) vers R, immobile en (60 ; 34), qui regarde le ballon au départ ; type de réception
    relevé au premier contact. `marker_at` : adversaire près de R."""
    seed_scene(21)
    r_at = Vec2(60.0, 34.0)
    to_ball = passer_at - r_at
    players = [player("A", "home", passer_at.x, passer_at.y),
               replace(player("R", "home", r_at.x, r_at.y, Agility=agility, First_Touch=99),
                       facing=math.atan2(to_ball.y, to_ball.x)),
               player("G", "away", 104.0, 34.0, poste="GK")]
    if marker_at is not None:
        players.append(player("M", "away", marker_at.x, marker_at.y, poste="DC"))
    direction = (r_at - passer_at).normalized()
    scene = Scene.full(players, ball_at=passer_at + direction * 0.5)
    ball = scene.ball
    ball.velocity, ball.receiver, ball.released_by = direction * speed, "R", "A"
    ball.pass_from, ball.last_pass_team, ball.receptions = passer_at, "home", []
    ball.receiver_marked = any(p.team == "away" and p.position.distance_to(r_at) < 2.0 for p in players)  # au départ
    run(scene, 3.0, until=lambda s: bool(s.ball.receptions))
    assert [e.player for e in ball.receptions] == ["R"]
    return ball.receptions[0].kind


def test_three_scenes_profile_from_behind_face_from_the_side_back_to_play_without_time() -> None:
    assert _reception(Vec2(40.0, 34.0), 10.0) == PROFIL  # de derrière, 2 s de vol : il a le temps de s'ouvrir
    assert _reception(Vec2(60.0, 14.0), 10.0) == FACE  # de côté : déjà ouvert à 45° du but
    assert _reception(Vec2(55.5, 34.0), 25.0, agility=11) == DOS  # de derrière, 0,2 s de vol : pas le temps



def test_a_marked_receiver_does_not_open_and_receives_back_to_play() -> None:
    """Décision du propriétaire du 12/11/2026 : adversaire à moins de 2 m (`possession.MARKED_RADIUS_M`) au départ de
    la passe, le receveur ne s'ouvre pas ; même passe de derrière qu'en scène « de profil », marqueur à 1,5 m dans son
    dos (puis à 3 m : il s'ouvre). La scène pose le drapeau comme `match._marked` au départ d'une passe."""
    assert _reception(Vec2(40.0, 34.0), 10.0, marker_at=Vec2(61.5, 34.0)) == DOS
    assert _reception(Vec2(40.0, 34.0), 10.0, marker_at=Vec2(63.0, 34.0)) == PROFIL  # à 3 m : il s'ouvre


def test_marked_at_the_pass_means_an_opponent_within_two_metres() -> None:
    from v2engine.match import _marked
    receiver = player("R", "home", 60.0, 34.0)
    assert _marked(receiver, [player("M", "away", 61.9, 34.0)])
    assert not _marked(receiver, [player("M", "away", 62.1, 34.0)])
    assert not _marked(receiver, [])

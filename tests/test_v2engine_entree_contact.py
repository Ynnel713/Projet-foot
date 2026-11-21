"""Instant d'entrée du ballon dans la portée d'un joueur (ticket v2-realisme/29c) : calculé sur la droite du pas, depuis le
pied de la perpendiculaire. Avant, quand le point le plus proche était rabattu sur la fin du pas, l'entrée était avancée,
d'autant plus que la portée est grande : le receveur (1 m) passait devant le défenseur collé qui le précédait."""

from __future__ import annotations

import math

from v2engine import possession
from v2engine.ball_state import BallState
from v2engine.geometry import Vec2
from v2engine.match import RECEIVER_REACH_M, _ball_contacts, _contacts, _step_ball
from v2engine.movement import PlayerState


def _player(name: str, team: str, position: Vec2, facing: Vec2 = Vec2(-1.0, 0.0),
            velocity: Vec2 = Vec2(0.0, 0.0)) -> PlayerState:
    return PlayerState(name=name, team=team, poste="DC", position=position, velocity=velocity, pace=60,
                       acceleration=60, stamina=99, home_target=position, facing=facing)


def _true_entry(start: Vec2, end: Vec2, player: Vec2, radius: float) -> float:
    """Fraction du pas où le ballon entre dans le cercle, par la géométrie exacte (droite du pas)."""
    seg = end - start
    length = seg.length()
    u = seg * (1.0 / length)
    rel = player - start
    along = rel.x * u.x + rel.y * u.y
    perp = abs(rel.x * u.y - rel.y * u.x)
    return max(0.0, (along - math.sqrt(radius**2 - perp**2)) / length)


def test_entry_is_exact_when_the_closest_point_is_the_end_of_the_step() -> None:
    """Pas de (40,47 ; 34) à (41,16 ; 34) ; joueur à (42 ; 34), portée 1 m : le ballon entre à x = 41, fraction 0,77
    (l'ancien calcul donnait 0,21)."""
    start, end = Vec2(40.47, 34.0), Vec2(41.16, 34.0)
    receiver = _player("R", "home", Vec2(42.0, 34.0))
    (entry, gap, _), = _contacts(start, end, 0.1, [receiver], None, RECEIVER_REACH_M)
    assert math.isclose(entry, (41.0 - 40.47) / 0.69, abs_tol=1e-9)
    assert math.isclose(gap, 0.84, abs_tol=1e-9)  # distance la plus proche, au bout du pas : inchangée


def test_entry_matches_the_exact_geometry_across_offsets() -> None:
    start, end = Vec2(10.0, 0.0), Vec2(11.0, 0.0)
    for x, y, radius in ((11.3, 0.2, 0.8), (11.6, 0.5, 0.8), (10.5, 0.3, 0.41), (11.9, 0.0, 1.0), (11.2, 0.7, 1.0)):
        hits = _contacts(start, end, 0.1, [_player("P", "away", Vec2(x, y))], None, radius)
        assert len(hits) == 1
        assert math.isclose(hits[0][0], _true_entry(start, end, Vec2(x, y), radius), abs_tol=1e-9)


def test_entry_unchanged_when_the_foot_is_inside_the_step() -> None:
    """Pied de la perpendiculaire dans le pas : même valeur qu'avant (s - sqrt(r² - d²) / L)."""
    start, end = Vec2(0.0, 0.0), Vec2(2.0, 0.0)
    (entry, gap, _), = _contacts(start, end, 0.1, [_player("P", "away", Vec2(1.0, 0.3))], None, 0.8)
    assert math.isclose(gap, 0.3, abs_tol=1e-9)
    assert math.isclose(entry, 0.5 - math.sqrt(0.64 - 0.09) / 2.0, abs_tol=1e-9)


def test_marker_in_front_and_off_the_line_now_comes_before_the_receiver() -> None:
    """Défenseur 0,5 m devant le receveur et 0,5 m à côté de la ligne, tourné vers le ballon : il entre dans sa portée
    (0,8 m) à x = 40,88, le receveur (1 m) à x = 41. Avant : receveur d'abord (0,21 contre 0,24)."""
    receiver = _player("R", "home", Vec2(42.0, 34.0))
    marker = _player("M", "away", Vec2(41.5, 34.5))
    ball = BallState(position=Vec2(40.47, 34.0), velocity=Vec2(6.9, 0.0), receiver="R", readers={},
                     last_pass_team="home", pass_started_s=0.0)
    hits = _ball_contacts(Vec2(40.47, 34.0), Vec2(41.16, 34.0), 0.1, [receiver, marker], ball, 1.1)
    assert [h[2].name for h in hits] == ["M", "R"]


def test_marked_receiver_scene_marker_wins_the_ball(monkeypatch) -> None:
    """Passe de 12 m au sol, défenseur décalé 0,5 m devant le receveur et 0,5 m à côté : il touche le premier."""
    monkeypatch.setattr("v2engine.match.attempt_control", lambda *a, **k: True)
    receiver = _player("R", "home", Vec2(42.0, 34.0))
    marker = _player("M", "away", Vec2(41.5, 34.5))
    ball = BallState(position=Vec2(30.0, 34.0), velocity=Vec2(possession._launch_speed(12.0), 0.0), receiver="R",
                     readers={}, last_pass_team="home", pass_started_s=0.0, released_by="passeur")
    for i in range(40):
        _step_ball(ball, 0.1, [receiver, marker], i * 0.1)
        if ball.holder is not None:
            break
    assert ball.holder == "M"


def test_receiver_beside_his_marker_still_takes_the_ball(monkeypatch) -> None:
    """Défenseur à côté du receveur (0,7 m, à sa hauteur) : le receveur, visé, touche le premier."""
    monkeypatch.setattr("v2engine.match.attempt_control", lambda *a, **k: True)
    receiver = _player("R", "home", Vec2(42.0, 34.0))
    marker = _player("M", "away", Vec2(42.0, 34.7))
    ball = BallState(position=Vec2(30.0, 34.0), velocity=Vec2(possession._launch_speed(12.0), 0.0), receiver="R",
                     readers={}, last_pass_team="home", pass_started_s=0.0, released_by="passeur")
    for i in range(40):
        _step_ball(ball, 0.1, [receiver, marker], i * 0.1)
        if ball.holder is not None:
            break
    assert ball.holder == "R"

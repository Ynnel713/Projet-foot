"""Couverture de la profondeur (ticket v2-realisme/10c) : quand une passe en profondeur est possible (porteur adverse
non pressé, dernière ligne à 25 m au moins de son but, personne au-delà de la ligne), le défenseur de la dernière ligne
le plus éloigné du ballon dans la largeur se place 3 m plus bas que la ligne."""

from __future__ import annotations

import math
import random

from v2engine.ball_state import BallState
from v2engine.bloc import DEPTH_DROP_M, DEPTH_SPACE_M, Bloc
from v2engine.geometry import Vec2
from v2engine.movement import PlayerState
from v2engine.situation import DEFENSE_PLACEE, POSSESSION_INSTALLEE


def _p(name: str, x: float, y: float, poste: str = "MC", team: str = "home") -> PlayerState:
    return PlayerState(name=name, team=team, poste=poste, position=Vec2(x, y), velocity=Vec2(0.0, 0.0), pace=60,
                       acceleration=60, stamina=60, home_target=Vec2(x, y))


def _scene(ball: Vec2, striker_x: float = 100.0, presser: bool = False) -> tuple[Bloc, list[PlayerState]]:
    """4-4-2 domicile (défend x = 0) : défense à x = 18 (y = 16, 28, 40, 52), milieu à 32, attaque à 45 ; porteur
    adverse au ballon, avant-centre adverse en `striker_x` ; `presser` : un milieu à 2 m du porteur."""
    team = ([_p("GK", 5, 34, poste="GK")] + [_p(f"D{i}", 18, y, poste="DC") for i, y in enumerate((16, 28, 40, 52))]
            + [_p(f"M{i}", 32, y) for i, y in enumerate((16, 28, 40, 52))]
            + [_p(f"A{i}", 45, y, poste="BU") for i, y in enumerate((28, 40))])
    if presser:
        team[5].position = ball + Vec2(-2.0, 0.0)
    players = [*team, _p("H", ball.x, ball.y, team="away"), _p("S", striker_x, 34.0, poste="BU", team="away")]
    bloc = Bloc.from_players(players)
    bloc.update(players, BallState(position=ball, velocity=Vec2(0.0, 0.0), holder="H"))
    return bloc, team


def _x(bloc: Bloc, team: list[PlayerState], name: str, ball: Vec2, situation: str = DEFENSE_PLACEE) -> float:
    return bloc.reference(next(p for p in team if p.name == name), ball, situation).x


def test_the_far_side_defender_drops_below_the_line() -> None:
    # ballon à droite (y = 60), porteur libre, ligne à 30 m de son but, avant-centre loin : le défenseur gauche (D0)
    # se place 3 m plus bas que ses partenaires de ligne
    ball = Vec2(52.5, 60.0)
    bloc, team = _scene(ball)
    assert bloc.lines["home"] >= DEPTH_SPACE_M and bloc.depth_cover == {"home": "D0"}
    assert math.isclose(_x(bloc, team, "D0", ball), _x(bloc, team, "D1", ball) - DEPTH_DROP_M)
    assert math.isclose(_x(bloc, team, "D3", ball), _x(bloc, team, "D1", ball))


def test_the_far_side_follows_the_ball() -> None:
    ball = Vec2(52.5, 8.0)  # ballon à gauche : le défenseur droit (D3) couvre
    bloc, team = _scene(ball)
    assert bloc.depth_cover == {"home": "D3"}
    assert math.isclose(_x(bloc, team, "D3", ball), _x(bloc, team, "D0", ball) - DEPTH_DROP_M)


def test_no_drop_when_the_holder_is_pressed() -> None:
    bloc, _ = _scene(Vec2(52.5, 60.0), presser=True)
    assert bloc.depth_cover == {}


def test_no_drop_when_an_attacker_is_beyond_the_line() -> None:
    # avant-centre à 20 m du but : la ligne tient à 25 m (piège), il est au-delà ; reculer le remettrait en jeu
    bloc, _ = _scene(Vec2(52.5, 60.0), striker_x=20.0)
    assert bloc.lines["home"] >= DEPTH_SPACE_M - 1e-9 and bloc.depth_cover == {}


def test_no_drop_without_space_behind_the_line() -> None:
    bloc, _ = _scene(Vec2(30.0, 60.0))  # ballon dans notre moitié : ligne sous 25 m
    assert bloc.lines["home"] < DEPTH_SPACE_M and bloc.depth_cover == {}


def test_no_drop_with_the_ball() -> None:
    ball = Vec2(52.5, 60.0)
    bloc, team = _scene(ball)
    assert math.isclose(_x(bloc, team, "D0", ball, POSSESSION_INSTALLEE), _x(bloc, team, "D1", ball, POSSESSION_INSTALLEE))


def test_depth_covers_are_traced_and_deterministic() -> None:
    from ligue1sim.clubs import load_clubs
    from ligue1sim.season import CLUBS_PATH
    from v2engine.match import simulate_match
    clubs = load_clubs(CLUBS_PATH, "Ligue 1")
    traces = []
    for _ in range(2):
        random.seed(20261119)
        traces.append(simulate_match(clubs[4], clubs[5], duration_minutes=3.0))
    records = traces[0].depth_covers
    assert records and records == traces[1].depth_covers
    assert {r.team for r in records} <= {"home", "away"}

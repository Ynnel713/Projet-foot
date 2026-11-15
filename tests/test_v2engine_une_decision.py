"""Une seule décision par ballon (ticket v2-realisme/11g) : sur un ballon libre, un seul chasseur par équipe (le plus
proche), les autres se replacent ; le joueur sorti du bloc couvre derrière le presseur affecté (voir
`test_v2engine_defense.py`)."""

from __future__ import annotations

from v2engine import cerveau
from v2engine.ball_state import BallState
from v2engine.geometry import Vec2
from tests.scenes import player


def _loose(ball_at: Vec2):
    return BallState(position=ball_at, velocity=Vec2(0.0, 0.0), holder=None)


def test_only_the_nearest_teammate_chases_a_loose_ball() -> None:
    ball = _loose(Vec2(50.0, 34.0))
    near, mid, far = player("N", "home", 52.0, 34.0), player("M", "home", 55.0, 36.0), player("F", "home", 60.0, 30.0)
    rival = player("R", "away", 47.0, 34.0)  # l'adversaire le plus proche de son équipe y va aussi
    players = [near, mid, far, rival]
    roles = {p.name: cerveau.think(p, ball, players, 1.0, None).role for p in players}
    assert roles == {"N": cerveau.BALLON_LIBRE, "M": cerveau.REPLACEMENT, "F": cerveau.REPLACEMENT,
                     "R": cerveau.BALLON_LIBRE}


def test_the_chaser_changes_when_another_teammate_becomes_nearest() -> None:
    ball = _loose(Vec2(50.0, 34.0))
    a, b = player("A", "home", 53.0, 34.0), player("B", "home", 51.0, 34.0)
    players = [a, b]
    assert cerveau.think(a, ball, players, 1.0, None).role == cerveau.REPLACEMENT
    assert cerveau.think(b, ball, players, 1.0, None).role == cerveau.BALLON_LIBRE


def test_keeper_who_does_not_come_out_does_not_take_the_loose_ball_from_the_defender() -> None:
    """Rejet A1 de l'expert : gardien à 3 m qui ne sort pas (l'attaquant, à 2 m, arrive avant lui), défenseur à 4 m :
    le défenseur reste le chasseur désigné de son équipe (avant la correction, personne n'y allait)."""
    from tests.scenes import Scene

    ball_at = Vec2(10.0, 34.0)
    keeper = player("G", "home", 7.0, 34.0, "GK")
    defender = player("D", "home", 10.0, 30.0, "DC")
    attacker = player("A", "away", 12.0, 34.0, "BU")
    scene = Scene.full([keeper, defender, attacker], ball_at=ball_at)
    intentions = {p.name: cerveau.think(p, scene.ball, scene.players, 1.0, None, None, scene.bloc, scene.defense,
                                        scene.transition) for p in scene.players}
    assert intentions["G"].action != "aller au ballon"  # il ne sort pas
    assert intentions["D"].role == cerveau.BALLON_LIBRE
    assert intentions["A"].role == cerveau.BALLON_LIBRE


def test_keeper_coming_out_leaves_a_single_field_chaser() -> None:
    """Gardien qui sort (attaquant loin) : il va au ballon ; un seul joueur de champ de son équipe est désigné."""
    from tests.scenes import Scene

    keeper = player("G", "home", 4.0, 34.0, "GK")
    d1, d2 = player("D1", "home", 18.0, 30.0, "DC"), player("D2", "home", 20.0, 38.0, "DC")
    scene = Scene.full([keeper, d1, d2, player("A", "away", 40.0, 34.0, "BU")], ball_at=Vec2(12.0, 34.0))
    intentions = {p.name: cerveau.think(p, scene.ball, scene.players, 1.0, None, None, scene.bloc, scene.defense,
                                        scene.transition) for p in scene.players}
    assert intentions["G"].action == "aller au ballon"
    assert [n for n in ("D1", "D2") if intentions[n].role == cerveau.BALLON_LIBRE] == ["D1"]

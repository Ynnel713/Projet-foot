"""Ticket v2-realisme/18i : portée de jambe d'un joueur qui attend le ballon (receveur visé, lecteurs de la passe)."""

from __future__ import annotations

from scenes import Scene, player, run, seed_scene
from v2engine.geometry import Vec2
from v2engine.match import CONTROL_RADIUS_M, LEG_REACH_M, _contacts


def _still(name: str, team: str, x: float, y: float):
    return player(name, team, x, y)


def test_a_ball_passing_at_70_cm_is_reached_only_by_a_player_who_expects_it() -> None:
    # ballon de (40 ; 34) à (44 ; 34) en un pas ; joueurs immobiles à 0,7 m de sa course
    start, end = Vec2(40.0, 34.0), Vec2(44.0, 34.0)
    receiver, reader, other = _still("R", "home", 42.0, 34.7), _still("L", "away", 42.5, 33.3), _still("O", "away", 41.0, 34.7)
    assert CONTROL_RADIUS_M < 0.7 < LEG_REACH_M
    hits = _contacts(start, end, 0.1, [receiver, reader, other], expecting=frozenset({"R", "L"}))
    assert [h[2].name for h in hits] == ["R", "L"]  # dans l'ordre d'arrivée du ballon ; O, qui ne l'attend pas, non
    assert _contacts(start, end, 0.1, [receiver, reader, other]) == []  # sans attente : le corps seul ne suffit pas


def test_the_body_still_counts_for_everyone_and_the_reach_stops_at_one_metre() -> None:
    start, end = Vec2(40.0, 34.0), Vec2(44.0, 34.0)
    body = _still("O", "away", 42.0, 34.3)  # à 0,3 m : touché par le corps, attendu ou non
    far = _still("R", "home", 43.0, 35.1)  # à 1,1 m : hors de portée même pour le receveur visé
    hits = _contacts(start, end, 0.1, [body, far], expecting=frozenset({"R"}))
    assert [h[2].name for h in hits] == ["O"]


def test_in_play_the_receiver_reaches_a_fast_pass_that_brushes_past_him() -> None:
    """Scène : passe rapide (20 m/s) de A vers R, à l'arrêt à 8 m et à 0,8 m de la trajectoire : il n'a pas le temps de
    venir dessus et la touche jambe tendue (avant le 18i, avec le corps seul, le ballon lui passait devant ; vérifié en
    ramenant `LEG_REACH_M` à `CONTROL_RADIUS_M` : personne ne la touche)."""
    seed_scene(5)
    players = [player("A", "home", 40.0, 34.0), player("R", "home", 48.0, 34.8, First_Touch=99),
               player("G", "away", 104.0, 34.0, poste="GK")]
    scene = Scene.full(players, ball_at=Vec2(40.5, 34.0))
    scene.ball.velocity = Vec2(20.0, 0.0)  # passe en vol vers R, qui l'attend
    scene.ball.receiver = "R"
    scene.ball.released_by = "A"
    run(scene, 2.0, until=lambda s: s.ball.last_toucher is not None)
    assert scene.ball.last_toucher == "R"

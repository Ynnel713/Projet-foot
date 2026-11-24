"""Qui attaque un ballon aérien (ticket v2-realisme/15a) : scènes fixes de la sélection des joueurs désignés."""

from __future__ import annotations

import v2engine.match as match
import v2engine.occasion as occasion
from v2engine.atteinte import reach_m
from v2engine.ball_state import BallState
from v2engine.cerveau import BALLON_LIBRE, RECEVEUR, decide, interpret, perceive
from v2engine.geometry import Vec2
from v2engine.jeu_aerien import (AERIAL_ATTACKERS, ATTACKER_HOLD_S, BALLON_AERIEN, HORIZON_S, SECOND_ATTACKER_GAP_S,
                                 STEP_S, TOUCH_M, ball_path, contact_point, is_aerial_ball, select_attackers)
from v2engine.movement import PlayerState
from v2engine.trace import AerialRecord
from v2engine.vol import height_at, launch_vz

SPEED = 26.0  # dégagement long : 26 m/s vers +x, qui retombe à 45 m (x = 65)


def _p(name: str, x: float, y: float, team: str, poste: str = "MC", pace: int = 60, height: float = 1.80,
       jumping: int = 50) -> PlayerState:
    return PlayerState(name=name, team=team, poste=poste, position=Vec2(x, y), velocity=Vec2(0.0, 0.0), pace=pace,
                       acceleration=60, stamina=60, home_target=Vec2(x, y), attributes={"Jumping Reach": jumping},
                       height_m=height)


def _clearance(receiver: str | None = None) -> BallState:
    ball = BallState(position=Vec2(20.0, 34.0), velocity=Vec2(SPEED, 0.0))
    ball.z, ball.vz = 0.0, launch_vz(45.0, SPEED, 0.1)
    ball.receiver = receiver
    ball.last_pass_team = "home"
    return ball


def _scene() -> list[PlayerState]:
    """Autour de la zone de chute (x ≈ 60 à 65) : trois joueurs de chaque équipe à des distances croissantes, plus loin
    un joueur de chaque équipe et les gardiens."""
    return [
        _p("h1", 60.0, 36.0, "home"), _p("h2", 58.0, 40.0, "home"), _p("h3", 52.0, 46.0, "home"),
        _p("h_loin", 30.0, 10.0, "home"),
        _p("a1", 63.0, 32.0, "away"), _p("a2", 66.0, 28.0, "away"), _p("a3", 72.0, 22.0, "away"),
        _p("a_loin", 95.0, 60.0, "away"),
        _p("h_gk", 5.0, 34.0, "home", "GK"), _p("a_gk", 100.0, 34.0, "away", "GK"),
    ]


def test_constants_validated_by_the_owner() -> None:
    assert (AERIAL_ATTACKERS, SECOND_ATTACKER_GAP_S, ATTACKER_HOLD_S) == (2, 1.0, 0.3)
    # recherche du point de contact : les valeurs de la lecture d'occasion et du rayon de contrôle du moteur
    assert (STEP_S, HORIZON_S, TOUCH_M) == (occasion.REACH_STEP_S, occasion.REACH_HORIZON_S, match.CONTROL_RADIUS_M)


def test_on_a_long_clearance_the_two_best_of_each_team_attack_the_ball_the_others_do_not() -> None:
    players = _scene()
    ball = _clearance()
    chosen = select_attackers(ball, players)
    assert set(chosen) == {"h1", "h2", "a1", "a2"}
    assert [chosen[n].rank for n in ("h1", "h2", "a1", "a2")] == [0, 1, 0, 1]
    for p in players:
        seen = perceive(p, ball, players)
        ball.aerial_attackers = chosen
        role = interpret(p, ball, seen, False, players)
        if p.name in chosen:
            assert role == BALLON_AERIEN
            intention = decide(p, role, ball, seen, players, 10.0, None)
            assert intention.action == "attaquer le ballon" and intention.target == chosen[p.name].point
        elif p.poste != "GK":
            assert role not in (BALLON_AERIEN, BALLON_LIBRE)  # ni désigné, ni chasseur du ballon libre (11g)


def test_the_contact_point_is_where_the_ball_passes_within_his_reach() -> None:
    ball = _clearance()
    under_the_apex = _p("h1", 42.0, 34.0, "home")  # sous le sommet du vol, il ne le touche pas là
    t, point, on_time, _ = contact_point(under_the_apex, ball_path(ball))
    assert on_time
    assert height_at(ball.z, ball.vz, t) <= reach_m(under_the_apex)
    assert point.x > 55.0  # il va plus loin, là où le ballon redescend à sa portée


def test_the_second_does_not_go_if_he_arrives_more_than_one_second_after_the_first() -> None:
    players = [_p("h1", 60.0, 36.0, "home"), _p("h_loin", 30.0, 10.0, "home"), _p("a1", 63.0, 32.0, "away")]
    chosen = select_attackers(_clearance(), players)
    assert set(chosen) == {"h1", "a1"}


def test_a_designated_player_keeps_his_place_unless_a_mate_is_clearly_earlier() -> None:
    ball = _clearance()
    path = ball_path(ball)
    held = _p("h1", 60.0, 40.0, "home")
    contact_s, _, _, held_arrival_s = contact_point(held, path)
    # coéquipier qui touche au même instant et arrive 0,2 s plus tôt : le désigné garde sa place ; 0,4 s : il la perd
    for lead_s, kept in ((0.2, True), (0.4, False)):
        other = next(o for o in (_p("h2", 60.0 + d * 0.05, 36.5, "home") for d in range(200))
                     if contact_point(o, path)[0] == contact_s
                     and abs(held_arrival_s - contact_point(o, path)[3] - lead_s) < 0.02)
        previous = select_attackers(ball, [held])
        chosen = select_attackers(ball, [held, other], previous)
        first = next(n for n, a in chosen.items() if a.rank == 0)
        assert (first == "h1") is kept
        assert first in select_attackers(ball, [held, other], chosen)  # stable au pas suivant


def test_the_intended_receiver_is_always_one_of_his_team() -> None:
    players = _scene()
    ball = _clearance(receiver="h3")
    chosen = select_attackers(ball, players)
    assert "h3" in chosen and chosen["h3"].rank == 0
    assert sum(1 for a in chosen.values() if a.team == "home") == 2
    ball.aerial_attackers = chosen
    h3 = next(p for p in players if p.name == "h3")
    seen = perceive(h3, ball, players)
    assert interpret(h3, ball, seen, True, players) == RECEVEUR
    assert decide(h3, RECEVEUR, ball, seen, players, 10.0, None).target == chosen["h3"].point


def test_a_player_flagged_offside_does_not_attack_the_ball() -> None:
    players = _scene()
    ball = _clearance()
    ball.offside_watch = {"h1"}
    assert "h1" not in select_attackers(ball, players)


def test_the_passer_does_not_attack_the_ball_he_releases() -> None:
    passer = _p("h0", 20.0, 34.0, "home")  # au point de départ : il « toucherait » le ballon à 0 s
    ball = _clearance()
    assert "h0" in select_attackers(ball, _scene() + [passer])
    ball.released_by = "h0"
    assert "h0" not in select_attackers(ball, _scene() + [passer])


def test_no_selection_on_a_ground_ball_a_held_ball_or_a_shot() -> None:
    players = _scene()
    ground = BallState(position=Vec2(20.0, 34.0), velocity=Vec2(SPEED, 0.0))
    assert not is_aerial_ball(ground) and select_attackers(ground, players) == {}
    held = _clearance()
    held.holder = "h1"
    assert select_attackers(held, players) == {}
    shot = _clearance()
    shot.shot_wide = True
    assert select_attackers(shot, players) == {}


def test_selection_is_traced_on_each_change() -> None:
    players = _scene()
    records: list[AerialRecord] = []
    last: dict[str, tuple[str, ...]] = {}
    chosen = select_attackers(_clearance(), players)
    match._record_aerial(chosen, 1.0, last, records)
    match._record_aerial(chosen, 1.1, last, records)  # inchangé : rien de plus
    match._record_aerial({}, 1.2, last, records)  # le ballon retombe : plus personne
    assert [(r.minute, r.team, r.players) for r in records] == [
        (1.0, "home", ("h1", "h2")), (1.0, "away", ("a1", "a2")), (1.2, "home", ()), (1.2, "away", ())]
    assert all(len(r.points) == len(r.contact_s) == len(r.on_time) == len(r.players) for r in records)


def test_a_taller_jumper_is_preferred_to_a_closer_shorter_mate() -> None:
    # ballon tendu au sommet de sa courbe à 2,8 m (un centre) : le grand l'atteint plus tôt dans sa descente
    ball = BallState(position=Vec2(55.0, 34.0), velocity=Vec2(15.0, 0.0), z=2.8, vz=0.0)
    short = _p("h1", 61.0, 34.5, "home", height=1.68, jumping=10)
    tall = _p("h2", 59.0, 35.5, "home", height=1.95, jumping=90)
    path = ball_path(ball)
    assert contact_point(tall, path)[0] < contact_point(short, path)[0]  # il touche plus tôt le ballon qui descend
    assert contact_point(short, path)[3] < contact_point(tall, path)[3]  # alors que le petit arrive avant
    chosen = select_attackers(ball, [short, tall])
    assert chosen["h2"].rank == 0 and chosen["h1"].rank == 1


def test_a_second_already_on_his_way_keeps_going_within_the_hold_margin() -> None:
    ball = _clearance()
    path = ball_path(ball)
    first = _p("h1", 63.0, 34.5, "home")
    first_arrival_s = contact_point(first, path)[3]
    # second qui arrive 1,15 s après le premier : écarté s'il n'était pas désigné, gardé s'il était déjà en route
    second = next(o for o in (_p("h2", 63.0, 34.5 + d * 0.05, "home") for d in range(400))
                  if abs(contact_point(o, path)[3] - first_arrival_s - 1.15) < 0.02)
    assert "h2" not in select_attackers(ball, [first, second])
    previous = {"h2": select_attackers(ball, [second])["h2"]}
    assert "h2" in select_attackers(ball, [first, second], previous)

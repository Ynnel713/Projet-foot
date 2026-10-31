"""Pressing coordonné (ticket v2-collectif/08) : course orientée, distance d'arrêt, effort par à-coups et relais,
déclencheurs collectifs suivis selon Teamwork."""

from __future__ import annotations

import random

from scripts.v2_indicators import open_options
from v2engine import cerveau
from v2engine.ball_state import BallState
from v2engine.defense import (MARQUAGE, PRESS_BURST_S, PRESSEUR, SHADOW_M, DefensiveRoles, follow_probability,
                              good_lane_probability, press_intensity, press_point, press_rest_s, stop_distance_m)
from v2engine.geometry import Vec2
from v2engine.match import _resolve_player_collisions, _step_ball, _step_player
from v2engine.movement import PlayerState


def _p(name: str, team: str = "home", x: float = 50.0, y: float = 34.0, poste: str = "MC", **attributes: int) -> PlayerState:
    return PlayerState(name=name, team=team, poste=poste, position=Vec2(x, y), velocity=Vec2(0.0, 0.0), pace=60,
                       acceleration=60, stamina=60, home_target=Vec2(x, y),
                       attributes={k.replace("_", " "): v for k, v in attributes.items()} or None)


def _at(values) -> list[float]:
    return [round(v, 2) for v in values]


def test_validated_curves() -> None:
    notes = (99, 55, 11)
    assert _at(press_intensity(_p("W", Work_Rate=n)) for n in notes) == [1.0, 0.8, 0.55]
    assert _at(press_rest_s(_p("W", Work_Rate=n)) for n in notes) == [5.0, 10.0, 20.0]
    assert _at(good_lane_probability(_p("A", Anticipation=n)) for n in notes) == [0.85, 0.65, 0.4]
    assert _at(stop_distance_m(_p("G", Aggression=n)) for n in notes) == [0.8, 1.2, 1.6]
    assert _at(follow_probability(_p("T", Teamwork=n)) for n in notes) == [0.95, 0.8, 0.55]


def test_presser_stops_at_his_aggression_distance_on_the_side_of_the_lane() -> None:
    holder = _p("H", team="away", x=40, y=34)
    receiver = _p("R", team="away", x=30, y=20)
    for note in (99, 11):
        presser = _p("P", x=46, y=34, Aggression=note)
        spot = press_point(presser, holder, receiver)
        assert abs(spot.distance_to(holder.position) - stop_distance_m(presser)) < 1e-9
        direct = Vec2(40 + stop_distance_m(presser), 34)
        assert 0.0 < spot.distance_to(direct) <= SHADOW_M + 1e-9
        assert spot.y < 34  # du côté de la passe vers R


def test_presser_relieved_after_his_burst_and_rests_by_work_rate() -> None:
    holder = _p("H", team="away", x=40)
    first, second = _p("Premier", x=43, Work_Rate=55), _p("Second", x=47, Work_Rate=55)
    ball = BallState(position=holder.position, velocity=Vec2(0.0, 0.0), holder="H")
    defense = DefensiveRoles()
    for k in range(int(PRESS_BURST_S * 10)):
        defense.update([holder, first, second], ball, None, k * 0.1)
        assert defense.assignments["Premier"].role == PRESSEUR
    defense.update([holder, first, second], ball, None, PRESS_BURST_S)
    assert defense.assignments["Second"].role == PRESSEUR  # relais
    assert abs(defense.rest_until["Premier"] - (PRESS_BURST_S + 10.0)) < 1e-9
    assert defense.resting(first, PRESS_BURST_S + 9.0) and not defense.resting(first, PRESS_BURST_S + 10.1)


# Marking 99 : marqueur à 1 m, nettement sous `possession._MARKED_RADIUS_M` (3 m), pour un test peu bruité.
def _scene(teamwork: int) -> list[PlayerState]:
    return [_p("H", team="away", x=40, y=34), _p("Ancien", team="away", x=32, y=34),
            _p("R1", team="away", x=31, y=23), _p("R2", team="away", x=31, y=45),
            _p("P", x=44, y=34), _p("D1", x=27, y=19, Teamwork=teamwork, Marking=99), _p("D2", x=27, y=49, Teamwork=teamwork, Marking=99),
            _p("C", x=28, y=34)]


def _back_pass(defense: DefensiveRoles, players: list[PlayerState]) -> BallState:
    """« Ancien », plus avancé (l'extérieur attaque vers x = 0), donne en retrait à H."""
    ball = BallState(position=players[1].position, velocity=Vec2(0.0, 0.0), holder="Ancien")
    defense.update(players, ball, None, 0.0)
    ball.holder, ball.position = "H", players[0].position
    return ball


def test_back_pass_triggers_a_team_press_followed_by_teamwork() -> None:
    random.seed(3)
    players = _scene(99)
    defense = DefensiveRoles()
    ball = BallState(position=players[0].position, velocity=Vec2(0.0, 0.0), holder="H")
    defense.update(players, ball, None, 0.0)  # sans déclencheur : personne ne suit R1 et R2
    assert not {"R1", "R2"} & {a.mate for a in defense.assignments.values() if a.role == MARQUAGE}
    defense = DefensiveRoles()
    ball = _back_pass(defense, players)
    defense.update(players, ball, None, 0.1)
    assert len({"Ancien", "R1", "R2"} & {a.mate for a in defense.assignments.values() if a.role == MARQUAGE}) >= 2
    counts = {}
    for note in (99, 11):
        random.seed(5)
        followed = 0
        for _ in range(200):
            defense = DefensiveRoles()
            defense.update(_scene(note), _back_pass(defense, _scene(note)), None, 0.1)
            followed += sum(defense.follows[n] for n in ("D1", "D2"))
        counts[note] = followed / 400
    assert counts[99] > counts[11] + 0.25  # 95 % contre 55 %, probabiliste


def _options_after(seconds: float, trigger: bool, seed: int) -> int:
    random.seed(seed)
    players = _scene(99)
    defense = DefensiveRoles()
    ball = _back_pass(defense, players) if trigger else BallState(position=players[0].position,
                                                                 velocity=Vec2(0.0, 0.0), holder="H")
    for k in range(int(seconds * 10)):
        defense.update(players, ball, None, 0.1 + k * 0.1)
        moved = [_step_player(p, ball, 0.1, (0.1 + k * 0.1) / 60.0, players, None, None, None, None, defense)
                 if p.team == "home" else p for p in players]
        players = moved
    holder = players[0]
    return open_options(holder, [p for p in players if p.team == "away"], [p for p in players if p.team == "home"])


def test_coordinated_press_closes_more_options_than_an_individual_press() -> None:
    individual = sum(_options_after(3.0, False, s) for s in range(10)) / 10
    coordinated = sum(_options_after(3.0, True, s) for s in range(10)) / 10
    assert coordinated <= individual - 0.5


def test_coordinated_press_does_not_make_recoveries_automatic() -> None:
    regained = 0
    for seed in range(30):
        random.seed(seed)
        players = _scene(99) + [_p("GK", team="away", x=100, y=34, poste="GK"), _p("GKh", x=3, y=34, poste="GK")]
        defense = DefensiveRoles()
        ball = _back_pass(defense, players)
        for k in range(60):  # 6 s
            now = 0.1 + k * 0.1
            defense.update(players, ball, None, now)
            players = [_step_player(p, ball, 0.1, now / 60.0, players, None, None, None, None, defense) for p in players]
            _resolve_player_collisions(players)
            _step_ball(ball, 0.1, players, now)
            if ball.holder is not None and next(p for p in players if p.name == ball.holder).team == "home":
                regained += 1
                break
    assert regained < 15  # moins de la moitié des cas


def test_resting_presser_does_not_go_back_to_the_ball_out_of_indiscipline() -> None:
    holder = _p("H", team="away", x=40)
    tired = _p("Las", x=42, Teamwork=11)
    players = [holder, _p("P", x=41), _p("C", x=34), tired]
    defense = DefensiveRoles()
    ball = BallState(position=holder.position, velocity=Vec2(0.0, 0.0), holder="H")
    defense.update(players, ball, None, 0.0)
    defense.rest_until["Las"], defense.leaving["Las"] = 100.0, (True, 1e9)
    assert cerveau.think(tired, ball, players, 1.0 / 60.0, None, defense=defense).role == cerveau.REPLACEMENT

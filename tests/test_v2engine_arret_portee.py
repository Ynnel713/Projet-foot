"""Arrêt par portée (ticket v2-realisme/05b) : quand le tir en vol passe au plus près du gardien, il l'atteint si l'écart
tient dans sa portée à cet instant (réaction, puis plongeon) ; sinon le ballon continue. Allumé en match au 05h."""

from __future__ import annotations

import math

from v2engine import match
from v2engine.ball_state import BallState, ShotFlight
from v2engine.decision import Action
from v2engine.geometry import PITCH_LENGTH_M, Vec2
from v2engine.match import GOAL_CENTER_Y, _step_ball
from v2engine.movement import PlayerState
from v2engine.occasion import ChanceTracker
from v2engine.shooting import (FLYING, HELD, KEEPER_DIVE_REACH_M, KEEPER_REACTION_S, KEEPER_STANDING_REACH_M, PARRIED,
                               TIPPED, keeper_reach_m)
from v2engine.trace import ShotEvent

SAVES = (HELD, PARRIED, TIPPED)


def _player(name: str, team: str, poste: str, position: Vec2) -> PlayerState:
    return PlayerState(name=name, team=team, poste=poste, position=position, velocity=Vec2(0.0, 0.0), pace=60,
                       acceleration=60, stamina=60, home_target=position, attributes=None)


def _shoot(monkeypatch, distance_m: float, lateral_m: float, keeper_y: float = 0.0, keeper_depth_m: float = 1.0,
           speed_mps: float | None = None):
    """Tir face au but depuis `distance_m`, réglé pour arriver sur la ligne à `lateral_m` du centre (à 1 m du sol) ;
    gardien à `keeper_depth_m` devant sa ligne, décalé de `keeper_y`. Retourne (issue tracée, tir tracé, équipe qui marque)."""
    shooter = _player("Buteur", "home", "BU", Vec2(PITCH_LENGTH_M - distance_m, GOAL_CENTER_Y))
    keeper = _player("Gardien", "away", "GK", Vec2(PITCH_LENGTH_M - keeper_depth_m, GOAL_CENTER_Y + keeper_y))
    ball = BallState(position=shooter.position, velocity=Vec2(0.0, 0.0), holder="Buteur")
    monkeypatch.setattr(match, "should_attempt_tackle", lambda aggression, dt: False)
    monkeypatch.setattr(match, "choose_action", lambda *args: Action("shot", 1.0))
    monkeypatch.setattr(match, "draw_blocker", lambda *args: None)
    monkeypatch.setattr(match, "draw_shot_error", lambda *args: (math.atan2(lateral_m, distance_m), 0.0))
    if speed_mps is not None:
        monkeypatch.setattr(match, "SHOT_SPEED_MPS", speed_mps)
    shots, scored = [], None
    for tick in range(40):
        scored = _step_ball(ball, 0.1, [shooter, keeper], tick * 0.1, shots=shots)
        if scored is not None or not ball.shot_in_flight:
            break
    _shoot.last = (ball, shooter, keeper)  # pour les tests qui regardent la scène après l'arrêt
    return shots[0], scored


def test_the_reach_grows_after_the_reaction_time_up_to_a_full_dive() -> None:
    assert keeper_reach_m(0.0) == keeper_reach_m(KEEPER_REACTION_S) == KEEPER_STANDING_REACH_M
    assert KEEPER_STANDING_REACH_M < keeper_reach_m(KEEPER_REACTION_S + 0.2) < KEEPER_DIVE_REACH_M
    assert keeper_reach_m(5.0) == KEEPER_DIVE_REACH_M


def test_a_central_shot_from_20_m_is_saved_and_the_time_and_gap_are_traced(monkeypatch) -> None:
    shot, scored = _shoot(monkeypatch, 20.0, 0.5)
    assert scored is None and shot.outcome in SAVES
    assert shot.keeper_time_s is not None and 0.5 < shot.keeper_time_s < 1.0  # 19 m de vol, ballon freiné
    assert shot.keeper_gap_m is not None and shot.keeper_gap_m < 1.0


def test_a_shot_from_8_m_into_the_side_netting_is_not_reached(monkeypatch) -> None:
    shot, scored = _shoot(monkeypatch, 8.0, 3.4)
    assert scored == "home" and shot.outcome == "but"
    assert shot.keeper_time_s < KEEPER_REACTION_S + 0.1 and shot.keeper_gap_m > keeper_reach_m(shot.keeper_time_s)


def test_the_closer_the_shot_the_fewer_saves(monkeypatch) -> None:
    # même point d'arrivée, à 2,5 m du centre : arrêté de loin, but de près
    saved = [_shoot(monkeypatch, d, 2.5)[0].outcome in SAVES for d in (28.0, 22.0, 16.0, 11.0, 6.0)]
    assert saved == sorted(saved, reverse=True) and saved[0] and not saved[-1]


def test_a_faster_shot_beats_the_keeper_where_a_slower_one_is_saved(monkeypatch) -> None:
    # 1,8 m du centre (réglage du gardien au 05h : plongeon plus lent)
    assert _shoot(monkeypatch, 14.0, 1.8, speed_mps=25.0)[0].outcome in SAVES
    assert _shoot(monkeypatch, 14.0, 1.8, speed_mps=60.0)[0].outcome == "but"


def test_a_badly_placed_keeper_concedes_where_a_well_placed_one_saves(monkeypatch) -> None:
    assert _shoot(monkeypatch, 20.0, 2.0, keeper_y=0.0)[0].outcome in SAVES  # 2 m du centre (réglage du 05h)
    assert _shoot(monkeypatch, 20.0, 2.0, keeper_y=-2.5)[0].outcome == "but"


def test_a_big_chance_ended_by_a_flying_shot_takes_the_shot_final_outcome() -> None:
    chances = []
    tracker = ChanceTracker(chances)
    ball = BallState(position=Vec2(PITCH_LENGTH_M - 8.0, GOAL_CENTER_Y), velocity=Vec2(25.0, 0.0), holder=None)
    # ballon en vol : aucun danger de jeu, seule la qualité du tir ouvre la séquence
    ball.shot_flight = ShotFlight("home", Vec2(PITCH_LENGTH_M - 8.0, GOAL_CENTER_Y), 0.0, 0)
    shots = [ShotEvent(10.0, "home", "Buteur", PITCH_LENGTH_M - 8.0, GOAL_CENTER_Y, 0.4, FLYING, "passe au sol")]
    tracker.update(10.0, ball, [], shots, lambda p: "")
    tracker.update(10.01, ball, [], shots, lambda p: "")
    assert chances == []  # issue pas encore connue : l'occasion reste ouverte
    shots[0] = ShotEvent(10.0, "home", "Buteur", PITCH_LENGTH_M - 8.0, GOAL_CENTER_Y, 0.4, "but", "passe au sol")
    tracker.update(10.02, ball, [], shots, lambda p: "")
    assert len(chances) == 1 and chances[0].outcome == "tir : but" and chances[0].shot


def test_a_flying_shot_cut_by_the_whistle_closes_its_big_chance_at_the_next_step() -> None:
    # réserve A3 du 05b : un tir en vol sans issue (sifflet, ballon mort avant la ligne) ne laisse pas l'occasion ouverte
    chances = []
    tracker = ChanceTracker(chances)
    ball = BallState(position=Vec2(PITCH_LENGTH_M - 8.0, GOAL_CENTER_Y), velocity=Vec2(25.0, 0.0), holder=None)
    ball.shot_flight = ShotFlight("home", Vec2(PITCH_LENGTH_M - 8.0, GOAL_CENTER_Y), 0.0, 0)
    shots = [ShotEvent(10.0, "home", "Buteur", PITCH_LENGTH_M - 8.0, GOAL_CENTER_Y, 0.4, FLYING, "passe au sol")]
    tracker.update(10.0, ball, [], shots, lambda p: "")
    ball.shot_flight = None  # sifflet pendant le vol : l'issue reste « en vol »
    tracker.update(10.01, ball, [], shots, lambda p: "")
    assert len(chances) == 1 and chances[0].outcome == "tir : " + FLYING and tracker.flying == {}


def test_after_a_save_the_ball_leaves_from_the_contact_point(monkeypatch) -> None:
    # réserve A2 du 05b : le ballon ne saute plus du point de contact au corps du gardien
    for outcome in SAVES:
        monkeypatch.setattr(match, "save_outcome", lambda *args, _o=outcome: _o)
        shot, _ = _shoot(monkeypatch, 20.0, 0.0, keeper_y=0.8)
        ball, shooter, keeper = _shoot.last
        assert shot.outcome == outcome
        contact = Vec2(PITCH_LENGTH_M - 1.0, GOAL_CENTER_Y)  # passage du tir au plus près du gardien, à 0,8 m de lui
        assert ball.position.distance_to(contact) <= match.CONTROL_RADIUS_M + 1e-9
        assert outcome != HELD or (keeper.position == contact and ball.holder == "Gardien")

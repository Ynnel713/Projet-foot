"""Choix du geste de la tête (ticket v2-realisme/15c1) : au contact de la tête, un joueur de champ choisit en une touche
remise, tir, dégagement ou amorti par l'évaluation tactique existante ; exécution provisoire neutre."""

from __future__ import annotations

from collections import Counter
from dataclasses import replace

import pytest

from v2engine.ball_state import BallState
from v2engine.danger import danger, loss_cost
import v2engine.decision as decision
from v2engine.decision import (CLEARANCE_DISTANCE_M, CLEARANCE_KEEP_SHARE, HEADER_NEUTRAL_ATTRIBUTES,
                               HEADER_NEUTRAL_NOTE, HEADER_PASS_RANGE_M, HEADER_SHOT_RANGE_M, Action, anticipation_share,
                               choose_action, clearance_point, dribble_options, header_cushion, header_gesture,
                               header_options, header_twin, in_own_half, option_value)
from v2engine.geometry import Vec2
from v2engine.match import _step_ball
from v2engine.movement import PlayerState
from v2engine.possession import control_probability, pressure
from v2engine.trace import (DEGAGEMENT, TETE_AMORTI, TETE_DEGAGEMENT, TETE_REMISE, TETE_TIR, EventLog, HeaderRecord,
                            ShotEvent)
from tests.scenes import seed_scene

EAST = Vec2(1.0, 0.0)
GOAL = Vec2(105.0, 34.0)


def _p(name: str, team: str, x: float, y: float, poste: str = "BU", height: float = 1.85, **attributes: int
       ) -> PlayerState:
    return PlayerState(name=name, team=team, poste=poste, position=Vec2(x, y), velocity=Vec2(0.0, 0.0), pace=60,
                       acceleration=60, stamina=60, home_target=Vec2(x, y), facing=EAST, height_m=height,
                       attributes={"First Touch": 60, "Passing": 60, "Finishing": 60, "Decisions": 60, "Vision": 60,
                                   **{k.replace("_", " "): v for k, v in attributes.items()}})


def test_constants_validated_by_the_owner() -> None:
    assert (HEADER_PASS_RANGE_M, HEADER_SHOT_RANGE_M, CLEARANCE_DISTANCE_M, CLEARANCE_KEEP_SHARE) == (20.0, 16.0, 30.0,
                                                                                                        0.4)
    assert HEADER_NEUTRAL_NOTE == 50
    assert set(HEADER_NEUTRAL_ATTRIBUTES) == {"Passing", "Technique", "Crossing", "Finishing", "Long Shots"}


def test_header_twin_neutralises_only_the_gesture_notes() -> None:
    player = _p("A", "home", 50.0, 34.0, Passing=95, Finishing=10, Decisions=90, Vision=80, Heading=77)
    twin = header_twin(player)
    assert all(twin.attributes[a] == 50 for a in HEADER_NEUTRAL_ATTRIBUTES)
    for a in ("Decisions", "Vision", "First Touch", "Heading"):
        assert twin.attributes[a] == player.attributes[a]
    assert player.attributes["Passing"] == 95  # l'original ne change pas
    bare = replace(player, attributes=None)  # joueur sans fiche (scènes synthétiques) : notes par défaut
    assert all(header_twin(bare).attributes[a] == 50 for a in HEADER_NEUTRAL_ATTRIBUTES)


def test_clearance_point_and_own_half() -> None:
    home = _p("D", "home", 10.0, 20.0)
    assert clearance_point(home) == Vec2(10.0 + CLEARANCE_DISTANCE_M, 20.0)
    away = _p("D", "away", 95.0, 50.0)
    assert clearance_point(away) == Vec2(95.0 - CLEARANCE_DISTANCE_M, 50.0)
    assert clearance_point(_p("D", "home", 90.0, 34.0)).x == 105.0  # dans le terrain
    assert in_own_half(home) and in_own_half(away)
    assert not in_own_half(_p("D", "home", 60.0, 34.0)) and not in_own_half(_p("D", "away", 40.0, 34.0))


def test_header_options_filter_ranges_add_clearance_and_cushion_by_control() -> None:
    near_goal = _p("A", "home", 92.0, 34.0)  # 13 m du but
    far = _p("A", "home", 85.0, 34.0)  # 20 m du but
    mate_near = _p("M", "home", 100.0, 34.0)  # à 8 m de near_goal
    mate_far = _p("M", "home", 60.0, 34.0)  # à 32 m
    options = [Action("shot", 0.10), Action("pass", 0.05, mate_near, one_touch=True),
               Action("pass", 0.04, mate_far, one_touch=True), Action("dribble", 0.03, point=Vec2(93.0, 34.0)),
               Action("pass", 0.02, mate_near)]
    kept = header_options(near_goal, options, GOAL, None, [near_goal], Vec2(10.0, 0.0))
    kinds = Counter((o.kind, o.one_touch) for o in kept)
    assert kinds == Counter({("shot", False): 1, ("pass", True): 1, ("dribble", False): 1, ("pass", False): 1})
    assert all(o.kind != "clearance" for o in kept)  # moitié adverse : pas de dégagement
    assert [o.kind for o in header_options(far, options[:1], GOAL, None, [far], Vec2(10.0, 0.0))] == []  # 20 m : pas de tir
    # amorti : valeur pondérée par la chance de contrôle, contrôle raté = perte sur place
    control = control_probability(near_goal, Vec2(10.0, 0.0), [])
    dribble = next(o for o in kept if o.kind == "dribble")
    expected = control * 0.03 - (1.0 - control) * loss_cost(near_goal.position, "home")
    assert dribble.value == pytest.approx(expected)
    shot = next(o for o in kept if o.kind == "shot")
    assert shot.value == 0.10  # geste de la tête : valeur inchangée
    # dégagement dans sa moitié, valeur dans la monnaie commune
    defender = _p("D", "home", 12.0, 34.0)
    [clear] = [o for o in header_options(defender, [], GOAL, None, [defender], Vec2(10.0, 0.0)) if o.kind == "clearance"]
    point = clearance_point(defender)
    assert clear.point == point
    assert clear.value == pytest.approx(option_value(defender, None, CLEARANCE_KEEP_SHARE, danger(point, "home"),
                                                     point))
    assert header_gesture(clear) and header_gesture(shot) and not header_gesture(dribble)


def _ball(z: float, x: float, y: float = 34.0, speed: float = 10.0, team: str = "away") -> BallState:
    ball = BallState(position=Vec2(x - 0.5, y), velocity=Vec2(speed, 0.0))
    ball.z, ball.vz = z, 0.0
    ball.last_pass_team = team
    ball.log = EventLog([])
    return ball


def _contact(players: list[PlayerState], z: float, x: float, seed: int, speed: float = 10.0, y: float = 34.0):
    ball = _ball(z, x, y, speed)
    headers: list[HeaderRecord] = []
    shots: list[ShotEvent] = []
    seed_scene(seed)
    _step_ball(ball, 0.1, [replace(p) for p in players], 10.0, shots=shots, headers=headers)
    return ball, headers, shots


def test_scene_free_header_in_front_of_goal_is_a_shot() -> None:
    striker = _p("Attaquant", "home", 96.0, 34.0)
    keeper = _p("Gardien", "away", 104.0, 34.0, poste="GK")
    gestures = Counter()
    for seed in range(40):
        ball, [record], shots = _contact([striker, keeper], 1.9, 96.0, seed)
        gestures[record.gesture] += 1
        if record.gesture == TETE_TIR:
            assert len(shots) == 1 and shots[0].player == "Attaquant" and ball.holder is None
    assert gestures[TETE_TIR] >= 30  # seul à 9 m, sans coéquipier : il tire de la tête


def test_scene_pressed_defender_on_a_hard_ball_in_his_box_clears() -> None:
    defender = _p("Defenseur", "home", 8.0, 34.0, poste="DC", First_Touch=1)
    attackers = [_p("Att1", "away", 8.8, 34.6), _p("Att2", "away", 7.2, 33.3)]
    gestures = Counter()
    for seed in range(40):
        ball, [record], _ = _contact([defender, *attackers], 1.9, 8.0, seed, speed=25.0)
        gestures[record.gesture] += 1
        if record.gesture == TETE_DEGAGEMENT:
            assert ball.holder is None and ball.vz > 0.0 and ball.velocity.x > 0.0  # en l'air, loin de son but
            assert ball.log.last_event().kind == DEGAGEMENT
    assert gestures[TETE_DEGAGEMENT] >= 20


def test_scene_header_pass_to_a_free_mate() -> None:
    passer = _p("Passeur", "home", 60.0, 34.0)
    mate = _p("Libre", "home", 72.0, 34.0)
    gestures = Counter()
    for seed in range(40):
        ball, [record], _ = _contact([passer, mate], 1.9, 60.0, seed)
        gestures[record.gesture] += 1
        if record.gesture == TETE_REMISE:
            assert record.target == "Libre" and ball.receiver == "Libre" and ball.holder is None
    assert gestures[TETE_REMISE] + gestures[TETE_AMORTI] == 40 and gestures[TETE_REMISE] > 0


def test_no_header_gesture_for_keeper_or_ball_below_the_head() -> None:
    keeper = _p("Gardien", "home", 30.0, 34.0, poste="GK")  # hors de sa surface : tête, mais gardien
    _, headers, _ = _contact([keeper], 1.9, 30.0, 1)
    assert headers == []
    field = _p("Joueur", "home", 50.0, 34.0)
    _, headers, _ = _contact([field], 1.0, 50.0, 1)  # ballon au corps : pas de tête
    assert headers == []


def test_determinism_at_fixed_seed() -> None:
    defender = _p("Defenseur", "home", 8.0, 34.0, poste="DC", First_Touch=1)
    attackers = [_p("Att1", "away", 8.8, 34.6), _p("Att2", "away", 7.2, 33.3)]
    first = [_contact([defender, *attackers], 1.9, 8.0, s, speed=25.0)[1] for s in range(20)]
    again = [_contact([defender, *attackers], 1.9, 8.0, s, speed=25.0)[1] for s in range(20)]
    assert first == again


def test_clearance_flags_a_mate_offside_at_departure() -> None:
    defender = _p("Defenseur", "home", 8.0, 34.0, poste="DC", First_Touch=1)
    lurker = _p("Avant", "home", 90.0, 34.0)  # au-delà de l'avant-dernier adversaire
    opponents = [_p("Att1", "away", 8.8, 34.6), _p("Att2", "away", 7.2, 33.3), _p("Def", "away", 70.0, 34.0),
                 _p("Gardien", "away", 104.0, 34.0, poste="GK")]
    flagged = 0
    for seed in range(30):
        ball, headers, _ = _contact([defender, lurker, *opponents], 1.9, 8.0, seed, speed=25.0)
        if headers and headers[0].gesture == TETE_DEGAGEMENT:  # sans faute aérienne ni duel perdu
            assert ball.offside_watch == {"Avant"}
            flagged += 1
    assert flagged > 0


def test_choice_weighs_the_perceived_carry_after_cushion_by_control(monkeypatch: pytest.MonkeyPatch) -> None:
    """Réserve A1 de l'expert : au moment du choix, la conduite perçue après amorti est pondérée par la chance de
    contrôle comme la valeur réelle ; sinon elle battrait ici le dégagement. Perception sans bruit."""
    monkeypatch.setattr(decision, "perception_error", lambda holder, gene: 0.0)
    holder = header_twin(_p("Defenseur", "home", 8.0, 34.0, poste="DC", First_Touch=30))
    opponents = [_p("Att", "away", 12.0, 36.0), _p("Gardien", "away", 104.0, 34.0, poste="GK")]
    players, incoming = [holder, *opponents], Vec2(12.0, 0.0)
    carry = max(o.value for o in dribble_options(holder, opponents, pressure(holder, opponents[:1]), None,
                                                 anticipation_share(holder)))
    [clear] = [o for o in header_options(holder, [], GOAL, None, players, incoming) if o.kind == "clearance"]
    assert carry > clear.value > header_cushion(holder, players, None, incoming)(carry)  # le cas que A1 faussait
    action = choose_action(holder, players, GOAL, opponents[1], None, None, {}, False, opponents, one_touch=True,
                           header=True, ball_velocity=incoming)
    assert action.kind == "clearance"


def test_no_backheel_from_a_header() -> None:
    """Réserve A3 de l'expert : une talonnade n'est pas un geste de la tête."""
    holder = _p("A", "home", 60.0, 34.0)
    mate = _p("M", "home", 55.0, 34.0)
    heel = Action("pass", 0.5, mate, one_touch=True, backheel=True)
    assert header_options(holder, [heel], GOAL, None, [holder, mate], Vec2(10.0, 0.0)) == []


def test_header_shot_keeps_its_origin() -> None:
    """Réserve A2 de l'expert : un tir de la tête après un centre a pour origine « centre »."""
    striker = _p("Attaquant", "home", 96.0, 34.0)
    keeper = _p("Gardien", "away", 104.0, 34.0, poste="GK")
    origins = set()
    for seed in range(20):
        ball = _ball(1.9, 96.0, team="home")
        ball.pass_from = Vec2(80.0, 5.0)  # centre du côté
        shots: list[ShotEvent] = []
        seed_scene(seed)
        _step_ball(ball, 0.1, [replace(striker), replace(keeper)], 10.0, shots=shots, headers=[])
        origins.update(e.origin for e in shots)
    assert origins == {"centre"}


"""Centre (ticket v2-attributs-restants/01) : le porteur dans les 35 derniers mètres, hors de la largeur de la surface,
envisage un centre vers un coéquipier de champ dans la surface adverse ; passe en l'air dont Crossing règle la précision
et le dosage à la place de Passing ; la retombée se joue au premier qui l'atteint."""

from __future__ import annotations

import random

import pytest

from tests.scenes import player
from v2engine import match
from v2engine.ball_state import BallState
from v2engine.decision import CROSS_ZONE_DEPTH_M, Action, evaluate_options, in_cross_zone
from v2engine.flux import seed_streams
from v2engine.geometry import Vec2
from v2engine.match import _step_ball
from v2engine.possession import dosage_quality, pass_accuracy_probability, pass_launch
from v2engine.trace import EventLog

GOAL = Vec2(105.0, 34.0)


def test_constant_validated_by_the_owner() -> None:
    assert CROSS_ZONE_DEPTH_M == 35.0


def test_cross_zone_is_the_last_35_m_outside_the_box_width() -> None:
    assert in_cross_zone(Vec2(96.0, 7.0), GOAL)  # aile droite près de la surface
    assert in_cross_zone(Vec2(70.5, 60.0), GOAL)  # 34,5 m de la ligne, aile gauche
    assert not in_cross_zone(Vec2(69.0, 7.0), GOAL)  # trop loin de la ligne
    assert not in_cross_zone(Vec2(96.0, 20.0), GOAL)  # dans la largeur de la surface (13,84 à 54,16)
    assert in_cross_zone(Vec2(9.0, 60.0), Vec2(0.0, 34.0))  # vers l'autre but


def _scene(lane_closed: bool, crossing: int = 80):
    ailier = player("Ailier", "home", 96.0, 7.0, "AD", Crossing=crossing, Passing=60)
    buteur = player("Buteur", "home", 94.0, 33.0, "BU")
    keeper = player("Gardien", "away", 103.5, 34.0, "GK")
    others = [player("DC", "away", 99.0, 38.0, "DC")]
    if lane_closed:  # deux défenseurs ferment la passe au sol vers le buteur
        others += [player("C1", "away", 95.0, 15.0, "DC"), player("C2", "away", 94.5, 24.0, "DC")]
    return ailier, buteur, keeper, [ailier, buteur, keeper, *others]


def test_a_winger_crosses_to_a_free_striker_when_the_ground_lane_is_closed() -> None:
    random.seed(1)
    seed_streams(1)
    ailier, buteur, keeper, players = _scene(lane_closed=True)
    best = evaluate_options(ailier, players, GOAL, keeper)[0]
    assert best.kind == "pass" and best.cross and best.lofted and best.target is buteur


def test_with_an_open_ground_lane_the_ground_pass_is_preferred() -> None:
    random.seed(1)
    seed_streams(1)
    ailier, buteur, keeper, players = _scene(lane_closed=False)
    options = evaluate_options(ailier, players, GOAL, keeper)
    assert not options[0].cross and any(o.cross and o.target is buteur for o in options)


def test_no_cross_from_the_centre_or_to_a_mate_outside_the_box() -> None:
    random.seed(1)
    seed_streams(1)
    axe = player("Meneur", "home", 82.0, 34.0, "MOC")
    dehors = player("Ailier", "home", 85.0, 60.0, "AG")
    keeper = player("Gardien", "away", 103.5, 34.0, "GK")
    assert not any(o.cross for o in evaluate_options(axe, [axe, dehors, keeper], GOAL, keeper))


def test_crossing_not_passing_sets_the_accuracy_and_the_dosage_of_a_cross() -> None:
    ailier, buteur, _, players = _scene(lane_closed=False)
    opponents = [p for p in players if p.team == "away"]
    good = player("Bon", "home", 96.0, 7.0, "AD", Crossing=90, Passing=30)
    bad = player("Mauvais", "home", 96.0, 7.0, "AD", Crossing=30, Passing=90)
    good_cross = pass_accuracy_probability(good, buteur, opponents, lofted=True, cross=True)
    bad_cross = pass_accuracy_probability(bad, buteur, opponents, lofted=True, cross=True)
    assert 0.0 < bad_cross < good_cross < 1.0
    # sans centre, c'est Passing qui compte : l'ordre s'inverse
    assert pass_accuracy_probability(good, buteur, opponents, lofted=True) < \
        pass_accuracy_probability(bad, buteur, opponents, lofted=True)
    assert dosage_quality(good, cross=True) > dosage_quality(bad, cross=True)
    assert dosage_quality(good) < dosage_quality(bad)


def test_better_crossers_put_more_crosses_near_their_target() -> None:
    _, buteur, _, players = _scene(lane_closed=False)
    opponents = [p for p in players if p.team == "away"]

    def near(crossing: int) -> float:
        passer = player("Centreur", "home", 96.0, 7.0, "AD", Crossing=crossing)
        random.seed(7)
        seed_streams(7)
        hits = sum(pass_launch(passer, buteur, opponents, lofted=True, cross=True)[1].distance_to(buteur.position) < 3.0
                   for _ in range(400))
        return hits / 400

    low, high = near(30), near(90)
    assert 0.0 < low < high < 1.0


def test_a_cross_leaves_in_the_air_and_is_logged_as_a_cross(monkeypatch) -> None:
    random.seed(3)
    seed_streams(3)
    ailier, buteur, keeper, players = _scene(lane_closed=True)
    ball = BallState(position=ailier.position, velocity=Vec2(0.0, 0.0), holder="Ailier")
    ball.log = EventLog([])
    monkeypatch.setattr(match, "should_attempt_tackle", lambda *args: False)
    monkeypatch.setattr(match, "choose_action", lambda *args, **kwargs: Action("pass", 1.0, buteur, lofted=True, cross=True))
    _step_ball(ball, 0.1, players, 0.0)
    assert ball.holder is None and ball.vz > 0.0 and ball.receiver == "Buteur"
    passes = [e for e in ball.log.events if e.kind == "passe"]
    assert passes and passes[-1].detail == match.CENTRE

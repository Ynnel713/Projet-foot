"""Notes du gardien sur l'arrêt (ticket v2-attributs-restants/03b1) : Reflexes règle son temps de réaction sur tir,
One on Ones sa portée debout en face-à-face ; la note mélangée A8 a disparu. Gardien moyen : médiane des gardiens de
Ligue 1 de la base (75), et un gardien sans note vaut le gardien moyen."""

from __future__ import annotations

import math

import pytest

from tests.scenes import player
from v2engine import match, shooting
from v2engine.ball_state import BallState
from v2engine.decision import Action
from v2engine.geometry import PITCH_LENGTH_M, Vec2
from v2engine.match import GOAL_CENTER_Y, _step_ball
from v2engine.shooting import (HELD, KEEPER_REACTION_S, KEEPER_STANDING_REACH_M, NEUTRAL_ATTRIBUTES, PARRIED, TIPPED,
                               keeper_profile, neutral_xg, physical_shot_chance)

SAVES = (HELD, PARRIED, TIPPED)
GOAL = Vec2(PITCH_LENGTH_M, GOAL_CENTER_Y)


def _keeper(reflexes: int = 75, one_on_ones: int = 75, x: float = PITCH_LENGTH_M - 1.0):
    return player("Gardien", "away", x, GOAL_CENTER_Y, "GK", Reflexes=reflexes, One_on_Ones=one_on_ones)


def _shooter(distance_m: float):
    return player("Buteur", "home", PITCH_LENGTH_M - distance_m, GOAL_CENTER_Y, "BU")


def test_the_average_keeper_is_the_engine_keeper_and_a_keeper_without_ratings_is_average() -> None:
    reference = (KEEPER_REACTION_S, KEEPER_STANDING_REACH_M)
    assert keeper_profile(_keeper(), True) == pytest.approx(reference)
    assert keeper_profile(None, True) == reference
    assert keeper_profile(player("G", "away", 104, 34, "GK"), True) == reference  # sans notes : effectif synthétique
    neutral = player("G", "away", 104, 34, "GK", Reflexes=99)
    assert keeper_profile(neutral.__class__(**{**neutral.__dict__, "attributes": NEUTRAL_ATTRIBUTES}), True) == reference


def test_reflexes_set_the_reaction_and_one_on_ones_the_standing_reach_in_a_face_to_face_only() -> None:
    assert keeper_profile(_keeper(reflexes=99), False)[0] == pytest.approx(0.204)
    assert keeper_profile(_keeper(reflexes=40), False)[0] == pytest.approx(0.44)
    assert keeper_profile(_keeper(reflexes=1), False)[0] == shooting.KEEPER_REACTION_BOUNDS_S[1]  # borné
    assert keeper_profile(_keeper(one_on_ones=99), True)[1] == pytest.approx(1.204)
    assert keeper_profile(_keeper(one_on_ones=40), True)[1] == pytest.approx(0.7025)
    assert keeper_profile(_keeper(one_on_ones=99), False)[1] == KEEPER_STANDING_REACH_M  # hors face-à-face : rien


def test_better_reflexes_concede_less_and_matter_from_close() -> None:
    # tireur seul face au but, One on Ones à la référence : seul Reflexes change
    def chance(distance_m: float, reflexes: int) -> float:
        keeper = _keeper(reflexes=reflexes)
        return physical_shot_chance(_shooter(distance_m), GOAL, keeper, [keeper])

    for distance in (10.0, 12.0, 16.0):
        assert chance(distance, 99) < chance(distance, 75) < chance(distance, 40)
    # à 8 m (0,24 s de vol jusqu'à lui), seul un très bon réflexe plonge encore ; à 6 m, personne
    assert chance(8.0, 99) < chance(8.0, 75) == pytest.approx(chance(8.0, 40))
    assert chance(6.0, 99) == pytest.approx(chance(6.0, 40))
    # de loin, le vol laisse à tout gardien le temps de plonger au plus loin : Reflexes ne joue presque plus
    assert chance(12.0, 40) - chance(12.0, 99) > 10.0 * (chance(20.0, 40) - chance(20.0, 99))
    assert chance(28.0, 40) == pytest.approx(chance(28.0, 99))


def test_one_on_ones_matter_in_a_face_to_face_and_not_with_a_defender_in_the_shot_line() -> None:
    shooter = _shooter(10.0)
    chances = []
    for note in (99, 75, 40):
        keeper = _keeper(one_on_ones=note)
        chances.append(physical_shot_chance(shooter, GOAL, keeper, [keeper]))
    assert chances[0] < chances[1] < chances[2]
    covered = []
    for note in (99, 40):  # défenseur sur la ligne de tir : plus un face-à-face, One on Ones ne joue pas
        keeper = _keeper(one_on_ones=note)
        defender = player("Def", "away", PITCH_LENGTH_M - 6.0, GOAL_CENTER_Y + 0.3, "DC")
        assert not shooting.one_on_one(shooter, GOAL, [keeper, defender])
        covered.append(physical_shot_chance(shooter, GOAL, keeper, [keeper, defender]))
    assert covered[0] == pytest.approx(covered[1])


def test_the_neutral_xg_ignores_the_keeper_ratings() -> None:
    shooter = _shooter(9.0)
    low, high = _keeper(reflexes=40, one_on_ones=40), _keeper(reflexes=99, one_on_ones=99)
    assert neutral_xg(shooter, GOAL, low, [low]) == pytest.approx(neutral_xg(shooter, GOAL, high, [high]))


def _shoot(monkeypatch, keeper, distance_m: float, lateral_m: float):
    shooter = _shooter(distance_m)
    ball = BallState(position=shooter.position, velocity=Vec2(0.0, 0.0), holder="Buteur")
    monkeypatch.setattr(match, "should_attempt_tackle", lambda aggression, dt: False)
    monkeypatch.setattr(match, "choose_action", lambda *args: Action("shot", 1.0))
    monkeypatch.setattr(match, "BLOCK_CHANCE", 0.0)
    monkeypatch.setattr(match, "draw_shot_error", lambda *args: (math.atan2(lateral_m, distance_m), 0.0))
    shots, scored = [], None
    for tick in range(40):
        scored = _step_ball(ball, 0.1, [shooter, keeper], tick * 0.1, shots=shots)
        if scored is not None or not ball.shot_in_flight:
            break
    return shots[0], scored


def test_in_the_match_loop_the_same_shot_is_saved_by_good_reflexes_and_not_by_poor_ones(monkeypatch) -> None:
    # tir de 12 m à environ 1,9 m du gardien : réflexes à 99 (0,20 s), arrêté ; à 40 (0,44 s), but
    good, scored_good = _shoot(monkeypatch, _keeper(reflexes=99), 12.0, 1.9)
    poor, scored_poor = _shoot(monkeypatch, _keeper(reflexes=40), 12.0, 1.9)
    assert good.outcome in SAVES and scored_good is None
    assert poor.outcome == "but" and scored_poor == "home"
    assert good.keeper_gap_m == pytest.approx(poor.keeper_gap_m)  # même tir, même écart

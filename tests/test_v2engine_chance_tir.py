"""La valeur du tir dans la décision suit la résolution physique (ticket v2-realisme/05e) : la chance évaluée
(`shooting.physical_shot_chance`) est celle que donne la vraie trajectoire, scène par scène."""

from __future__ import annotations

import pytest

from v2engine import match, shooting
from v2engine.geometry import PITCH_LENGTH_M, Vec2
from v2engine.match import GOAL_CENTER_Y

from scripts.shot_calibration import block_scene, scene_rate, wilson
from tests.scenes import player

GOAL = Vec2(PITCH_LENGTH_M, GOAL_CENTER_Y)
SHOTS = 1500


def test_the_estimator_steps_the_ball_like_the_match_loop() -> None:
    assert shooting._ENGINE_TICK_S == match.TICK_SECONDS


@pytest.mark.parametrize("from_line, offset", [(6.0, 0.0), (11.0, 10.0), (20.0, 0.0), (16.0, 15.0)])
def test_evaluated_chance_matches_the_goal_rate_of_the_real_trajectory(from_line: float, offset: float) -> None:
    # tireur et gardien neutres, sans défenseur : chance évaluée dans l'intervalle à 95 % du taux de buts observé sur
    # 1 500 tirs résolus par la trajectoire (grille complète de 20 positions : `scripts/shot_calibration.py scenes`)
    evaluated, rate = scene_rate(from_line, offset, SHOTS, seed=7)
    low, high = wilson(round(rate * SHOTS), SHOTS)
    assert low <= evaluated <= high, (evaluated, rate)


# défenseurs : (distance à la ligne, écart à l'axe du but, vitesse en x, vitesse en y) ; un défenseur dans l'axe, deux qui
# se cachent, un au contact du tireur, un qui coupe la trajectoire en courant, un à 2 m du tireur (jambe au pas suivant)
DEFENDED = [(20.0, 0.0, ((14.0, 0.0, 0.0, 0.0),)), (25.0, 0.0, ((15.0, 0.0, 0.0, 0.0), (10.0, 1.0, 0.0, 0.0))),
            (12.0, 0.0, ((11.7, 0.2, 0.0, 0.0),)), (16.0, 0.0, ((7.0, 2.0, 0.0, -4.0),)),
            (20.0, 0.0, ((18.0, 1.0, 0.0, 0.0),))]


@pytest.mark.parametrize("from_line, offset, defenders", DEFENDED)
def test_evaluated_block_chance_matches_the_blocks_of_the_real_trajectory(from_line, offset, defenders) -> None:
    evaluated, rate = block_scene(from_line, offset, SHOTS, 5, defenders)
    low, high = wilson(round(rate * SHOTS), SHOTS)
    assert low <= evaluated <= high, (evaluated, rate)


@pytest.mark.parametrize("from_line, offset, defenders", DEFENDED[:4])
def test_goal_and_block_are_judged_together_shot_direction_by_shot_direction(from_line, offset, defenders) -> None:
    # un défenseur dans l'axe contre surtout des tirs qui allaient au but : la chance de but n'est pas le produit
    evaluated, rate = scene_rate(from_line, offset, SHOTS, 6, defenders)
    low, high = wilson(round(rate * SHOTS), SHOTS)
    assert low <= evaluated <= high, (evaluated, rate)


def test_the_keeper_keeps_the_cone_rule_to_know_whether_the_shot_line_is_free() -> None:
    # `gardien.py` lit `block_probability == 0` : la chance physique, jamais exactement nulle, ne la remplace pas
    shooter = player("Buteur", x=PITCH_LENGTH_M - 14.0, y=GOAL_CENTER_Y, poste="BU")
    beside = player("Def", "away", x=PITCH_LENGTH_M - 8.0, y=GOAL_CENTER_Y + 6.0, poste="DC")
    assert shooting.block_probability(shooter, GOAL, [beside]) == 0.0
    assert shooting.physical_block_probability(shooter, GOAL, [beside]) > 0.0


def test_note_pressure_and_keeper_position_move_the_chance_the_way_the_resolution_does() -> None:
    at = dict(x=PITCH_LENGTH_M - 12.0, y=GOAL_CENTER_Y + 4.0, poste="BU")
    keeper = player("Gardien", "away", x=PITCH_LENGTH_M - 1.0, y=GOAL_CENTER_Y + 1.0, poste="GK")

    def chance(shooter, k=keeper, rivals=()):
        return shooting.physical_shot_chance(shooter, GOAL, k, [k, *rivals])

    average = chance(player("Buteur", **at))
    assert chance(player("Buteur", Finishing=95, **at)) > average > chance(player("Buteur", Finishing=20, **at))
    marker = player("Marqueur", "away", x=at["x"] + 1.0, y=at["y"], poste="DC")
    assert chance(player("Buteur", **at), rivals=[marker]) < average  # la pression élargit l'écart du ballon
    off_line = player("Gardien", "away", x=PITCH_LENGTH_M - 1.0, y=GOAL_CENTER_Y - 6.0, poste="GK")
    assert chance(player("Buteur", **at), k=off_line) > average  # gardien hors de position
    on_top = player("Gardien", "away", x=at["x"] + 0.5, y=at["y"], poste="GK")
    assert chance(player("Buteur", **at), k=on_top) == 0.0  # tireur dans la portée du gardien


def test_without_a_keeper_the_neutral_fallback_is_a_well_placed_keeper() -> None:
    shooter = player("Buteur", x=PITCH_LENGTH_M - 11.0, y=GOAL_CENTER_Y, poste="BU")
    placed = player("Gardien", "away", x=PITCH_LENGTH_M - shooting.KEEPER_REFERENCE_M, y=GOAL_CENTER_Y, poste="GK")
    assert shooting.physical_shot_chance(shooter, GOAL, None, []) == pytest.approx(
        shooting.physical_shot_chance(shooter, GOAL, placed, [placed]))

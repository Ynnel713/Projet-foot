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
# Tolérance de l'estimateur (ticket v2-realisme/05l) : l'intervalle à 95 % de l'observé est élargi de 5 % en relatif.
# Avec la visée à l'intérieur d'un poteau et le plongeon du 05l, l'estimateur s'écarte de quelques pour cent de la
# trajectoire, mesuré sur 7 500 à 9 000 tirs : scène 6 m face au but 0,421 évalué contre 0,403 observé (+ 4,5 %) ;
# 11 m / 10 m 0,062 contre 0,058 ; défenseur en course, but 0,095 contre 0,090, contre 0,250 contre 0,255.
ESTIMATOR_TOLERANCE = 0.05


def _agrees(evaluated: float, rate: float) -> bool:
    low, high = wilson(round(rate * SHOTS), SHOTS)
    return low * (1.0 - ESTIMATOR_TOLERANCE) <= evaluated <= high * (1.0 + ESTIMATOR_TOLERANCE)


def test_the_estimator_steps_the_ball_like_the_match_loop() -> None:
    assert shooting._ENGINE_TICK_S == match.TICK_SECONDS


@pytest.mark.parametrize("from_line, offset", [(6.0, 0.0), (11.0, 10.0), (20.0, 0.0), (16.0, 15.0)])
def test_evaluated_chance_matches_the_goal_rate_of_the_real_trajectory(from_line: float, offset: float) -> None:
    # tireur et gardien neutres, sans défenseur : chance évaluée dans l'intervalle à 95 % du taux de buts observé sur
    # 1 500 tirs résolus par la trajectoire (grille complète de 20 positions : `scripts/shot_calibration.py scenes`)
    evaluated, rate = scene_rate(from_line, offset, SHOTS, seed=7)
    assert _agrees(evaluated, rate), (evaluated, rate)


# défenseurs : (distance à la ligne, écart à l'axe du but, vitesse en x, vitesse en y) ; un défenseur dans l'axe, deux qui
# se cachent, un au contact du tireur, un qui coupe la trajectoire en courant, un à 2 m du tireur (jambe au pas suivant)
DEFENDED = [(20.0, 0.0, ((14.0, 0.0, 0.0, 0.0),)), (25.0, 0.0, ((15.0, 0.0, 0.0, 0.0), (10.0, 1.0, 0.0, 0.0))),
            (12.0, 0.0, ((11.7, 0.2, 0.0, 0.0),)), (16.0, 0.0, ((7.0, 2.0, 0.0, -4.0),)),
            (20.0, 0.0, ((18.0, 1.0, 0.0, 0.0),))]


@pytest.mark.parametrize("from_line, offset, defenders", DEFENDED)
def test_evaluated_block_chance_matches_the_blocks_of_the_real_trajectory(from_line, offset, defenders) -> None:
    evaluated, rate = block_scene(from_line, offset, SHOTS, 5, defenders)
    assert _agrees(evaluated, rate), (evaluated, rate)


@pytest.mark.parametrize("from_line, offset, defenders", DEFENDED[:4])
def test_goal_and_block_are_judged_together_shot_direction_by_shot_direction(from_line, offset, defenders) -> None:
    # un défenseur dans l'axe contre surtout des tirs qui allaient au but : la chance de but n'est pas le produit
    evaluated, rate = scene_rate(from_line, offset, SHOTS, 6, defenders)
    assert _agrees(evaluated, rate), (evaluated, rate)


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


# Défenseur en course (ticket v2-realisme/05j) : la scène évalue le tir à l'instant de la frappe, après le pas où la
# boucle avance les défenseurs (avant le ticket, à leur place de départ : écart attribué à tort à l'estimateur).
# Graines 5 à 9, `BLOCK_CHANCE` validée (0,6) et relevée (0,75, valeur mesurée au 18e).
RUNNING = (16.0, 0.0, ((7.0, 2.0, 0.0, -4.0),))


@pytest.mark.parametrize("block_chance", [0.6, 0.75])
@pytest.mark.parametrize("seed", [5, 6, 7, 8, 9])
def test_a_running_defender_is_judged_like_the_real_trajectory(monkeypatch, seed: int, block_chance: float) -> None:
    monkeypatch.setattr(shooting, "BLOCK_CHANCE", block_chance)
    monkeypatch.setattr(match, "BLOCK_CHANCE", block_chance)
    from_line, offset, defenders = RUNNING
    for evaluated, rate in (block_scene(from_line, offset, SHOTS, seed, defenders),
                            scene_rate(from_line, offset, SHOTS, seed, defenders)):
        assert _agrees(evaluated, rate), (evaluated, rate)


def test_the_scene_judges_the_shot_where_the_defenders_are_when_it_is_struck() -> None:
    # même défenseur, évalué à sa place de départ : hors de l'intervalle du contre observé (graine 5), ce que le ticket
    # 05j avait pris pour une erreur de l'estimateur
    from_line, offset, defenders = RUNNING
    shooter = player("Buteur", x=PITCH_LENGTH_M - from_line, y=GOAL_CENTER_Y + offset, poste="BU")
    d, y, vx, vy = defenders[0]
    at_start = player("D0", "away", x=PITCH_LENGTH_M - d, y=GOAL_CENTER_Y + y, poste="DC")
    at_start.velocity = Vec2(vx, vy)
    stale = shooting.physical_block_probability(shooter, GOAL, [at_start])
    evaluated, rate = block_scene(from_line, offset, SHOTS, 5, defenders)
    assert abs(evaluated - stale) > 0.01 and evaluated > stale

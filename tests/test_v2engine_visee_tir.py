"""Tests du moteur V2, ticket v2-realisme/05l (chance d'un tir propre ramenée sur la table cible) : plongeon du gardien
recalé, visée du tireur (centre ou intérieur d'un poteau), même loi à l'évaluation et au départ du tir. Voir
.scratch/v2-realisme/issues/05l-chance-du-tir-propre-sur-la-table-cible.md, critères d'acceptation."""

from __future__ import annotations

import math
import statistics

from tests.scenes import player
from v2engine import shooting
from v2engine.flux import seed_streams
from v2engine.geometry import PITCH_LENGTH_M, Vec2
from v2engine.match import GOAL_CENTER_Y

GOAL = Vec2(PITCH_LENGTH_M, GOAL_CENTER_Y)


def _keeper(dy: float = 0.0):
    return player("Gardien", "away", x=PITCH_LENGTH_M - 1.0, y=GOAL_CENTER_Y + dy, poste="GK")


def _shooter(depth: float, offset: float = 0.0, note: int | None = None):
    notes = {} if note is None else {"Finishing": note, "Long_Shots": note}
    return player("Buteur", x=PITCH_LENGTH_M - depth, y=GOAL_CENTER_Y + offset, poste="BU", **notes)


def test_validated_values() -> None:
    assert shooting.KEEPER_DIVE_MPS == 6.0
    assert shooting.AIM_INSIDE_POST_M == 2.5
    # portée, réaction et plafond du 05b inchangés
    assert (shooting.KEEPER_REACTION_S, shooting.KEEPER_STANDING_REACH_M, shooting.KEEPER_DIVE_REACH_M) == (0.30, 1.0, 2.8)


def test_a_better_shooter_always_has_a_better_chance() -> None:
    # sans visée, avec le plongeon du 05l, Finishing 95 valait moins que 60 face au but (tir sur le gardien)
    for depth, offset in ((6.0, 0.0), (11.0, 0.0), (11.0, 8.0), (16.0, 0.0), (20.0, 0.0), (25.0, 0.0)):
        keeper = _keeper()
        good, average, poor = (shooting.occasion_quality(_shooter(depth, offset, n), GOAL, keeper, [keeper])
                               for n in (95, 60, 20))
        assert good > average > poor, (depth, offset, good, average, poor)


def test_he_aims_inside_one_post_or_the_other_without_reading_the_keeper() -> None:
    shooter = _shooter(16.0)
    low, high = shooting.aim_angles(shooter, GOAL)
    inner = shooting.GOAL_WIDTH_M / 2.0 - shooting.AIM_INSIDE_POST_M
    assert abs(low + high) < 1e-12 and abs(high - math.atan2(inner, 16.0)) < 1e-12
    # même visées quel que soit le gardien : sa lecture du tireur viendra au 03l
    assert shooting._aimed(shooter, GOAL, _keeper(-1.5), [])[2] == shooting._aimed(shooter, GOAL, _keeper(1.5), [])[2]


def test_the_chance_is_the_mean_of_the_two_sides_and_the_shot_draws_one() -> None:
    shooter, keeper = _shooter(16.0, note=95), _keeper(-1.5)
    sides = shooting.aim_angles(shooter, GOAL)
    per_side = [(1.0 - shooting._shank_share(shooter, GOAL, [keeper], a)) * shares[2]
                for a, shares in zip(sides, shooting._flight_shares(shooter, GOAL, keeper, [keeper], sides))]
    assert abs(shooting.occasion_quality(shooter, GOAL, keeper, [keeper]) - sum(per_side) / 2.0) < 1e-12
    assert per_side[1] > per_side[0]  # gardien décalé vers y négatif : le côté y positif est le plus ouvert
    seed_streams(3)
    draws = [shooting.draw_shot_error(shooter, GOAL, [keeper], keeper) for _ in range(4000)]
    widths = [d[0] for d in draws if d is not None]
    # mélange de deux gaussiennes d'écart-type σ autour de ± la visée, à parts égales : moyenne nulle, variance σ² + a²
    sigma = shooting.shot_error_sigma(shooter, GOAL, [keeper])
    assert abs(statistics.fmean(widths)) < 0.01
    assert abs(statistics.pvariance(widths) / (sigma ** 2 + sides[1] ** 2) - 1.0) < 0.06


def test_a_clean_shot_from_16_to_20_m_follows_the_target_table() -> None:
    # tireur et gardien neutres, gardien bien placé, sans défenseur (scène du banc `scripts/shot_calibration.py`) :
    # avant le 05l, 0,204 à 16 m et 0,118 à 20 m contre 0,088 et 0,059 dans la table cible (`_XG_LOGIT`)
    for depth in (16.0, 20.0):
        at = Vec2(PITCH_LENGTH_M - depth, GOAL_CENTER_Y)
        shooter = _shooter(depth)
        keeper = player("Gardien", "away", x=GOAL.x + (at - GOAL).normalized().x * shooting.KEEPER_REFERENCE_M,
                        y=GOAL_CENTER_Y, poste="GK")
        ratio = shooting.physical_shot_chance(shooter, GOAL, keeper, [keeper]) / shooting.base_chance(at, GOAL)
        assert 0.8 <= ratio <= 1.3, (depth, ratio)

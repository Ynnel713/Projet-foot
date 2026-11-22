"""Style du gardien (ticket v2-attributs-restants/03b3a) : Rushing Out, tendance, règle sa hauteur quand le ballon est
loin et ses sorties sur ballon libre (marge sur l'adversaire, distance maximale de son but). Référence : 55, médiane des
gardiens notés de Ligue 1 de la base ; un gardien sans note vaut la référence et garde le comportement d'avant."""

from __future__ import annotations

from dataclasses import replace

import pytest

from tests.scenes import player
from v2engine import cerveau, gardien
from v2engine.ball_state import BallState
from v2engine.geometry import PENALTY_AREA_DEPTH_M, Vec2
from v2engine.movement import max_speed_mps

RUSHING_OUT = "Rushing Out (Tendency)"


def _keeper(note: int | None = None, x: float = 5.0, team: str = "home"):
    keeper = player("G", team, x, 34.0, "GK")
    return keeper if note is None else replace(keeper, attributes={RUSHING_OUT: note})


def _loose(at: Vec2, note: int | None, rival_x: float | None, keeper_x: float = 5.0):
    keeper = _keeper(note, keeper_x)
    players = [keeper] + ([player("A", "away", rival_x, 34.0, "BU")] if rival_x is not None else [])
    return keeper, BallState(position=at, velocity=Vec2(0.0, 0.0)), players


def test_a_keeper_without_ratings_or_at_the_reference_keeps_the_former_style() -> None:
    assert gardien.rushing_out(None) == gardien.RUSHING_OUT_REFERENCE_NOTE == 55.0
    assert gardien.rushing_out(_keeper()) == 55.0  # sans notes
    assert gardien.rushing_out(replace(_keeper(), attributes={})) == 55.0  # copie neutre de l'xG
    assert gardien.rushing_out(_keeper(90)) == 90.0
    assert gardien.rushing_out(replace(_keeper(), attributes={"Decisions": 70})) == 55.0  # colonne absente : référence
    assert gardien.depth_factor() == 1.0
    assert gardien.rush_margin_s() == gardien.RUSH_MARGIN_S == 0.5
    assert gardien.rush_max_from_goal_m() == gardien.RUSH_MAX_FROM_GOAL_M == 35.0
    for ball in (Vec2(10.0, 34.0), Vec2(30.0, 20.0), Vec2(60.0, 34.0)):
        for line in (None, 40.0):
            assert gardien.bisector_point(_keeper(55), ball, line) == gardien.bisector_point(_keeper(), ball, line)


def test_the_constants_at_both_ends_of_the_base() -> None:
    far = gardien.BALL_DISTANCE_M[1]
    assert gardien.depth_for_ball(far, None, gardien.depth_factor(25)) == pytest.approx(6.05)
    assert gardien.depth_for_ball(far, None, gardien.depth_factor(90)) == pytest.approx(10.275)
    assert gardien.rush_margin_s(25) == pytest.approx(0.80) and gardien.rush_margin_s(90) == pytest.approx(0.15)
    assert gardien.rush_max_from_goal_m(25) == pytest.approx(26.0) and gardien.rush_max_from_goal_m(90) == 45.0
    assert gardien.depth_factor(1) == gardien.RUSH_DEPTH_BOUNDS[0] and gardien.depth_factor(200) == gardien.RUSH_DEPTH_BOUNDS[1]
    assert gardien.rush_margin_s(200) == gardien.RUSH_MARGIN_BOUNDS_S[0]
    assert gardien.rush_max_from_goal_m(1) == gardien.RUSH_MAX_BOUNDS_M[0]


def test_a_sweeper_stands_higher_when_the_ball_is_far_and_nothing_changes_near_the_ball() -> None:
    far = Vec2(60.0, 34.0)
    low, mid, high = (gardien.bisector_point(_keeper(n), far).x for n in (25, 55, 90))
    assert low < mid < high
    assert high - low == pytest.approx(10.275 - 6.05)
    # avec une ligne haute, le libéro va jusqu'au bord de sa surface, jamais au-delà
    assert gardien.bisector_point(_keeper(90), far, 40.0).x == pytest.approx(PENALTY_AREA_DEPTH_M)
    assert gardien.bisector_point(_keeper(25), far, 40.0).x < gardien.bisector_point(_keeper(55), far, 40.0).x
    # ballon à `BALL_DISTANCE_M[0]` (12 m) ou moins de son but (tir) : même place pour tous
    for near in (Vec2(10.0, 34.0), Vec2(8.0, 28.0), Vec2(3.0, 10.0)):
        assert gardien.bisector_point(_keeper(25), near) == gardien.bisector_point(_keeper(90), near)
    # le cerveau vise ce point : intention de placement
    targets = [cerveau.think(_keeper(n), BallState(position=far, velocity=Vec2(0.0, 0.0), holder="A"),
                             [_keeper(n), player("A", "away", far.x, far.y, "MC")], 1.0, {}).target.x for n in (25, 90)]
    assert targets[0] < targets[1]


@pytest.mark.parametrize("gap_s, rushes", [(0.3, {25: False, 55: False, 90: True}),
                                           (0.65, {25: False, 55: True, 90: True}),
                                           (0.9, {25: True, 55: True, 90: True})])
def test_a_sweeper_rushes_with_a_shorter_lead_on_the_attacker(gap_s: float, rushes: dict[int, bool]) -> None:
    speed = max_speed_mps(60)
    for note, expected in rushes.items():  # même vitesse et même montée : l'écart de départ fait l'avance
        keeper, ball, players = _loose(Vec2(25.0, 34.0), note, rival_x=25.0 + 20.0 + gap_s * speed)
        assert gardien.race(keeper, ball, players).rush is expected, (gap_s, note)


def test_a_sweeper_rushes_farther_from_his_goal_and_the_reason_follows_his_cap() -> None:
    for at, rushes in ((40.0, {55: False, 90: True}), (30.0, {25: False, 55: True})):
        for note, expected in rushes.items():
            keeper, ball, players = _loose(Vec2(at, 34.0), note, rival_x=None, keeper_x=20.0)
            assert gardien.race(keeper, ball, players).rush is expected, (at, note)
    keeper, ball, players = _loose(Vec2(30.0, 34.0), 25, rival_x=None, keeper_x=20.0)
    assert "trop loin de son but" in cerveau.think(keeper, ball, players, 1.0, {}).reason
    keeper, ball, players = _loose(Vec2(40.0, 34.0), 90, rival_x=None, keeper_x=20.0)
    assert cerveau.think(keeper, ball, players, 1.0, {}).reason.startswith("sortie")


def test_the_style_is_mirrored_for_the_away_keeper() -> None:
    from v2engine.geometry import PITCH_LENGTH_M
    far = Vec2(PITCH_LENGTH_M - 60.0, 34.0)
    low, high = (gardien.bisector_point(_keeper(n, PITCH_LENGTH_M - 5.0, "away"), far).x for n in (25, 90))
    assert PITCH_LENGTH_M - low == pytest.approx(6.05) and PITCH_LENGTH_M - high == pytest.approx(10.275)

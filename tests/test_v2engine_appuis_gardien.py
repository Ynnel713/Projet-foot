"""Appuis du gardien au moment du tir (ticket v2-realisme/03f) : pendant sa réaction, le gardien garde son élan de la
frappe ; déjà lancé vers le ballon, il en atteint plus ; à contre-pied, il en atteint moins."""

from __future__ import annotations

import math

import pytest

from v2engine import match, shooting
from v2engine.ball_state import BallState
from v2engine.decision import Action
from v2engine.geometry import PITCH_LENGTH_M, Vec2
from v2engine.match import GOAL_CENTER_Y, _step_ball
from v2engine.movement import PlayerState
from v2engine.shooting import (HELD, KEEPER_REACTION_S, PARRIED, TIPPED, keeper_reach_m, keeper_toward_mps,
                               physical_shot_chance, post_shot_xg)

SAVES = (HELD, PARRIED, TIPPED)
GOAL = Vec2(PITCH_LENGTH_M, GOAL_CENTER_Y)


def _player(name: str, team: str, poste: str, position: Vec2, velocity: Vec2 = Vec2(0.0, 0.0)) -> PlayerState:
    return PlayerState(name=name, team=team, poste=poste, position=position, velocity=velocity, pace=60,
                       acceleration=60, stamina=60, home_target=position, attributes=None)


def _shoot(monkeypatch, distance_m: float, lateral_m: float, keeper_vy: float, drift: bool = False):
    """Tir face au but depuis `distance_m`, arrivant sur la ligne à `lateral_m` du centre (côté y croissant) ; gardien
    centré à 1 m de sa ligne, lancé à `keeper_vy` m/s en travers (positif : du côté du tir). Retourne (tir, marqueur)."""
    shooter = _player("Buteur", "home", "BU", Vec2(PITCH_LENGTH_M - distance_m, GOAL_CENTER_Y))
    keeper = _player("Gardien", "away", "GK", Vec2(PITCH_LENGTH_M - 1.0, GOAL_CENTER_Y), Vec2(0.0, keeper_vy))
    ball = BallState(position=shooter.position, velocity=Vec2(0.0, 0.0), holder="Buteur")
    monkeypatch.setattr(match, "should_attempt_tackle", lambda aggression, dt: False)
    monkeypatch.setattr(match, "choose_action", lambda *args: Action("shot", 1.0))
    monkeypatch.setattr(match, "BLOCK_CHANCE", 0.0)
    monkeypatch.setattr(match, "draw_shot_error", lambda *args: (math.atan2(lateral_m, distance_m), 0.0))
    shots, scored = [], None
    for tick in range(40):
        scored = _step_ball(ball, 0.1, [shooter, keeper], tick * 0.1, shots=shots)
        if drift:  # il glisse sur son élan pendant le vol (inertie du mouvement), sans plus de portée
            keeper.position = keeper.position + keeper.velocity * 0.1
        if scored is not None or not ball.shot_in_flight:
            break
    return shots[0], scored


def test_the_reach_shifts_by_the_keeper_momentum_during_his_reaction() -> None:
    assert keeper_reach_m(0.0, 2.0) == keeper_reach_m(0.0)  # à la frappe même, pas encore d'élan
    assert keeper_reach_m(0.2, 2.0) == pytest.approx(keeper_reach_m(0.2) + 0.4)
    # au-delà de la réaction, l'élan gardé ne grandit plus : décalage de vitesse fois `KEEPER_REACTION_S`
    for elapsed in (0.5, 1.0, 3.0):
        assert keeper_reach_m(elapsed, 2.0) - keeper_reach_m(elapsed) == pytest.approx(2.0 * KEEPER_REACTION_S)
        assert keeper_reach_m(elapsed) - keeper_reach_m(elapsed, -2.0) == pytest.approx(2.0 * KEEPER_REACTION_S)
    assert keeper_reach_m(0.3, -10.0) == 0.0  # jamais négative


def test_the_momentum_toward_the_ball_is_the_velocity_projected_on_the_gap() -> None:
    keeper = Vec2(104.0, 34.0)
    assert keeper_toward_mps(Vec2(0.0, 2.0), keeper, Vec2(104.0, 36.0)) == pytest.approx(2.0)
    assert keeper_toward_mps(Vec2(0.0, 2.0), keeper, Vec2(104.0, 32.0)) == pytest.approx(-2.0)
    assert keeper_toward_mps(Vec2(3.0, 0.0), keeper, Vec2(104.0, 36.0)) == pytest.approx(0.0)  # en profondeur : rien
    assert keeper_toward_mps(Vec2(0.0, 2.0), keeper, keeper) == 0.0  # ballon sur lui


@pytest.mark.parametrize("lateral_m, saved_by", [(1.1, (2.0, 0.0)), (1.6, (2.0,))])
def test_same_shot_still_keeper_moving_toward_and_wrong_footed(monkeypatch, lateral_m, saved_by) -> None:
    # tir de 11 m : lancé du bon côté, il arrête les deux ; immobile, le plus proche ; à contre-pied, aucun
    for vy in (2.0, 0.0, -2.0):
        shot, scored = _shoot(monkeypatch, 11.0, lateral_m, vy)
        assert (shot.outcome in SAVES) == (vy in saved_by), (lateral_m, vy, shot.outcome)
        assert (scored == "home") == (vy not in saved_by)
        assert shot.keeper_toward_mps == pytest.approx(vy, abs=0.05)  # élan tracé, signé vers le ballon


@pytest.mark.parametrize("lateral_m", [1.1, 1.6])
def test_the_drift_during_the_flight_is_not_counted_on_top_of_the_momentum(monkeypatch, lateral_m) -> None:
    # réserve A1 de l'expert : l'écart se prend depuis ses appuis de la frappe ; sa dérive pendant le vol ne change ni
    # l'écart tracé ni l'issue (l'élan la remplace déjà)
    for vy in (2.0, -2.0):
        still, _ = _shoot(monkeypatch, 11.0, lateral_m, vy)
        drifting, _ = _shoot(monkeypatch, 11.0, lateral_m, vy, drift=True)
        assert drifting.keeper_gap_m == pytest.approx(still.keeper_gap_m)
        assert (drifting.outcome in SAVES) == (still.outcome in SAVES)


def test_the_post_shot_xg_follows_the_momentum(monkeypatch) -> None:
    xg = [_shoot(monkeypatch, 11.0, 1.6, vy)[0].post_shot_xg for vy in (2.0, 0.0, -2.0)]
    assert xg[0] < xg[1] < xg[2]
    assert post_shot_xg(1.6, 0.5, 2.0) < post_shot_xg(1.6, 0.5) < post_shot_xg(1.6, 0.5, -2.0)


@pytest.mark.parametrize("distance_m", [11.0, 18.0])
def test_the_evaluated_cover_follows_the_keeper_momentum(distance_m) -> None:
    # évaluation du tir (décision, xG) : le gardien lancé vers +y (gauche du tireur, angles croissants) couvre plus de ce
    # côté et moins de l'autre ; à contre-pied, l'inverse
    origin = Vec2(PITCH_LENGTH_M - distance_m, GOAL_CENTER_Y)
    axis = (GOAL - origin).normalized()
    keeper_at = Vec2(PITCH_LENGTH_M - 1.0, GOAL_CENTER_Y)
    still, left, right = (shooting._keeper_cover(origin, GOAL, axis, keeper_at, Vec2(0.0, vy)) for vy in (0.0, 2.0, -2.0))
    assert left[1] > still[1] > right[1]
    assert left[0] > still[0] > right[0]
    assert still[0] == pytest.approx(-still[1])  # immobile : couverture symétrique


def test_a_moving_keeper_changes_the_evaluated_chance_of_a_shot_from_the_side() -> None:
    # tireur décalé vers +y : seul le poteau opposé (-y) est ouvert ; gardien lancé vers -y : moins de buts
    shooter = _player("Buteur", "home", "BU", Vec2(PITCH_LENGTH_M - 14.0, GOAL_CENTER_Y + 6.0))
    chances = []
    for vy in (-2.0, 0.0, 2.0):
        keeper = _player("Gardien", "away", "GK", Vec2(PITCH_LENGTH_M - 1.0, GOAL_CENTER_Y + 1.0), Vec2(0.0, vy))
        chances.append(physical_shot_chance(shooter, GOAL, keeper, [keeper]))
    assert chances[0] < chances[1] < chances[2]

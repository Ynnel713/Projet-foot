"""Courbe des tirs (ticket v2-hauteur-ballon/02a2) : le tir part du sol avec la vitesse verticale qui lui fait passer
la ligne à la hauteur qui fixe son issue (visée + pente, tickets v2-collectif/28b et v2-realisme/05a) ; rasant si cette
hauteur est nulle ou négative ; l'issue et la trajectoire au sol ne changent pas ; arrêté ou contré, le ballon repart du
sol."""

from __future__ import annotations

import math

import pytest

from v2engine import match
from v2engine.ball_state import BallState
from v2engine.decision import Action
from v2engine.geometry import PITCH_LENGTH_M, Vec2
from v2engine.match import GOAL_CENTER_Y, GOAL_HEIGHT_M, _step_ball
from v2engine.movement import PlayerState
from v2engine.possession import BALL_FRICTION_PER_S
from v2engine.restart import AERIEN, SOL
from v2engine.shooting import OVER, PARRIED, SHOT_AIM_HEIGHT_M
from v2engine.atteinte import reach_m
from v2engine.vol import GRAVITY_MPS2, height_at, line_crossing_s, shot_launch_vz

DT = 0.1


def _player(name: str, team: str, poste: str, position: Vec2) -> PlayerState:
    return PlayerState(name=name, team=team, poste=poste, position=position, velocity=Vec2(0.0, 0.0), pace=60,
                       acceleration=60, stamina=60, home_target=position, attributes=None)


def _shoot(monkeypatch, distance_m: float, line_height_m: float, lateral_m: float = 0.0,
           extra: list[PlayerState] | None = None, flat: bool = False):
    """Tir face au but depuis `distance_m`, réglé pour passer la ligne à `lateral_m` du centre et à `line_height_m`
    (pente de la visée) ; `flat` : sans hauteur (le code d'avant le 02a2). Retourne (tir tracé, équipe qui marque,
    ballon, relevé (position, z, mode) à chaque pas)."""
    shooter = _player("Buteur", "home", "BU", Vec2(PITCH_LENGTH_M - distance_m, GOAL_CENTER_Y))
    ball = BallState(position=shooter.position, velocity=Vec2(0.0, 0.0), holder="Buteur")
    monkeypatch.setattr(match, "should_attempt_tackle", lambda aggression, dt: False)
    monkeypatch.setattr(match, "choose_action", lambda *args: Action("shot", 1.0))
    width = math.atan2(lateral_m, distance_m)
    along = math.hypot(distance_m, lateral_m)
    monkeypatch.setattr(match, "draw_shot_error",
                        lambda *args: (width, math.atan((line_height_m - SHOT_AIM_HEIGHT_M) / along)))
    if flat:
        monkeypatch.setattr(match, "shot_launch_vz", lambda *args: 0.0)
    shots, scored, steps = [], None, []
    players = [shooter] + (extra or [])
    for tick in range(60):
        scored = _step_ball(ball, DT, players, tick * DT, shots=shots)
        steps.append((ball.position, ball.z, ball.mode))
        if scored is not None or not ball.shot_in_flight:
            break
    return shots[0], scored, ball, steps


def test_line_crossing_follows_the_engine_step_by_step_advance() -> None:
    q = BALL_FRICTION_PER_S ** DT
    for distance, speed in ((5.0, 30.0), (18.0, 30.0), (33.3, 30.0), (12.0, 9.0)):
        travelled, v, k = 0.0, speed, 0
        while travelled + v * DT < distance:
            travelled, v, k = travelled + v * DT, v * q, k + 1
        expected = (k + (distance - travelled) / (v * DT)) * DT
        assert line_crossing_s(distance, speed, DT) == pytest.approx(expected, abs=1e-12)
    assert line_crossing_s(80.0, 30.0, DT) is None  # le ballon s'arrête avant (environ 57 m à 30 m/s)
    assert line_crossing_s(0.0, 30.0, DT) == 0.0


def test_launch_puts_the_ball_at_the_line_height_without_touching_the_ground_before() -> None:
    for distance, height in ((20.0, 0.3), (20.0, 2.3), (25.0, 4.0), (8.0, 1.5)):
        vz = shot_launch_vz(distance, 30.0, height, DT)
        t = line_crossing_s(distance, 30.0, DT)
        assert height_at(0.0, vz, t) == pytest.approx(height, abs=1e-9)
        assert vz * vz / (2.0 * GRAVITY_MPS2) >= height  # sommet au moins à la hauteur de la ligne
        assert t <= 2.0 * vz / GRAVITY_MPS2  # pas de retour au sol avant la ligne
    assert shot_launch_vz(20.0, 30.0, 0.0, DT) == 0.0  # hauteur nulle : rasant
    assert shot_launch_vz(20.0, 30.0, -1.2, DT) == 0.0  # visée sous le sol : rasant
    assert shot_launch_vz(80.0, 30.0, 1.0, DT) == 0.0  # ligne jamais atteinte : rasant


def test_a_shot_over_the_bar_crosses_the_line_above_it(monkeypatch) -> None:
    shot, scored, _, steps = _shoot(monkeypatch, 20.0, 3.6)
    assert scored is None and shot.outcome == OVER
    assert shot.line_z_m == pytest.approx(3.6, abs=1e-6)
    assert steps[0][1] == 0.0 and min(z for _, z, _ in steps[1:-1]) > 0.0  # frappé du sol, en l'air jusqu'à la ligne
    assert any(mode == AERIEN for _, _, mode in steps)  # au-dessus de 2,5 m : tracé « aérien »


def test_an_on_target_shot_crosses_the_line_under_the_bar(monkeypatch) -> None:
    monkeypatch.setattr(match, "_goalkeeper", lambda *args: None)
    shot, scored, _, steps = _shoot(monkeypatch, 22.0, 2.3)
    assert scored == "home" and shot.outcome == "but"
    assert shot.line_z_m == pytest.approx(2.3, abs=1e-6) and shot.line_z_m < GOAL_HEIGHT_M
    assert all(z >= 0.0 for _, z, _ in steps)


def test_a_shot_aimed_under_the_ground_is_a_rolling_shot(monkeypatch) -> None:
    shot, scored, _, steps = _shoot(monkeypatch, 22.0, -0.8)
    assert scored == "home" and shot.line_z_m == 0.0
    assert all(z == 0.0 and mode == SOL for _, z, mode in steps)


@pytest.mark.parametrize("height", [-0.8, 0.4, 2.3, 3.6])
@pytest.mark.parametrize("lateral", [0.0, 2.5, 6.0])
def test_the_height_changes_neither_the_outcome_nor_the_ground_path(monkeypatch, height: float, lateral: float) -> None:
    flat_shot, flat_scored, _, flat_steps = _shoot(monkeypatch, 20.0, height, lateral, flat=True)
    monkeypatch.undo()
    shot, scored, _, steps = _shoot(monkeypatch, 20.0, height, lateral)
    assert (shot.outcome, scored) == (flat_shot.outcome, flat_scored)
    assert [p for p, _, _ in steps] == [p for p, _, _ in flat_steps]  # même trajet au sol, pas à pas


def test_a_saved_shot_leaves_the_keeper_on_the_ground(monkeypatch) -> None:
    monkeypatch.setattr(match, "save_outcome", lambda *args: PARRIED)
    keeper = _player("Gardien", "away", "GK", Vec2(PITCH_LENGTH_M - 1.0, GOAL_CENTER_Y + 0.5))
    shot, _, ball, _ = _shoot(monkeypatch, 20.0, 2.0, extra=[keeper])
    assert shot.outcome == PARRIED and shot.keeper_z_m is not None and shot.keeper_z_m > 1.0
    assert (ball.z, ball.vz, ball.mode) == (0.0, 0.0, SOL)


def test_a_blocked_shot_leaves_the_defender_on_the_ground(monkeypatch) -> None:
    monkeypatch.setattr(match, "BLOCK_CHANCE", 1.0)
    defender = _player("Défenseur", "away", "DC", Vec2(PITCH_LENGTH_M - 14.0, GOAL_CENTER_Y))
    shot, _, ball, _ = _shoot(monkeypatch, 20.0, 2.0, extra=[defender])
    assert shot.outcome == "contré" and shot.block_z_m is not None and shot.block_z_m > 0.0
    assert (ball.z, ball.vz, ball.mode) == (0.0, 0.0, SOL)


# --- Atteinte sur les tirs (ticket v2-hauteur-ballon/03b) ---------------------------------------------------------------

def test_a_shot_over_the_defender_reach_is_not_blocked(monkeypatch) -> None:
    monkeypatch.setattr(match, "BLOCK_CHANCE", 1.0)
    defender = _player("Défenseur", "away", "DC", Vec2(PITCH_LENGTH_M - 4.0, GOAL_CENTER_Y))
    shot, _, ball, steps = _shoot(monkeypatch, 20.0, 6.0, extra=[defender])
    assert shot.outcome == OVER and shot.block_z_m is None  # passé au-dessus de lui, jusqu'à la ligne
    assert max(z for _, z, _ in steps) > reach_m(defender)


def test_a_shot_within_the_defender_reach_is_still_blocked(monkeypatch) -> None:
    monkeypatch.setattr(match, "BLOCK_CHANCE", 1.0)
    defender = _player("Défenseur", "away", "DC", Vec2(PITCH_LENGTH_M - 4.0, GOAL_CENTER_Y))
    shot, _, _, _ = _shoot(monkeypatch, 20.0, 1.0, extra=[defender])
    assert shot.outcome == "contré" and shot.block_z_m <= reach_m(defender)


def _keeper_out(monkeypatch, height: float):
    """Gardien sorti hors de sa surface (17 m de sa ligne), sans mains, portée au sol illimitée : seule la hauteur juge."""
    monkeypatch.setattr(match, "save_outcome", lambda *args: PARRIED)
    monkeypatch.setattr(match, "keeper_reach_m", lambda *args: 99.0)
    keeper = _player("Gardien", "away", "GK", Vec2(PITCH_LENGTH_M - 17.0, GOAL_CENTER_Y + 0.5))
    shot, scored, _, _ = _shoot(monkeypatch, 30.0, height, extra=[keeper])
    return shot, scored, keeper


def test_the_keeper_does_not_save_a_shot_above_his_reach(monkeypatch) -> None:
    shot, scored, keeper = _keeper_out(monkeypatch, 2.4)
    assert shot.keeper_z_m > reach_m(keeper)  # 1,82 m + 0,53 m de détente, hors de sa surface
    assert shot.outcome == "but" and scored == "home"


def test_the_keeper_saves_a_shot_within_his_reach(monkeypatch) -> None:
    shot, _, keeper = _keeper_out(monkeypatch, 0.5)
    assert shot.keeper_z_m <= reach_m(keeper) and shot.outcome == PARRIED


def test_the_estimator_reads_the_same_curve_as_the_shot() -> None:
    # écart vertical seuil d'un défenseur (ticket 03b) : un tir lancé avec cet écart passe exactement à son atteinte
    from v2engine import shooting
    to_goal, elapsed, reach = 20.0, 0.4, 2.3
    angle = shooting._under_reach_angle(to_goal, elapsed, reach)
    line = SHOT_AIM_HEIGHT_M + to_goal * math.tan(angle)
    total = shooting._flight_time_s(to_goal)
    assert line * elapsed / total + GRAVITY_MPS2 * elapsed * (total - elapsed) / 2.0 == pytest.approx(reach)
    assert shooting._under_reach_angle(to_goal, total + 0.1, reach) == math.inf  # après la ligne : sans objet


def test_the_estimator_keeps_the_old_block_rule_when_every_shot_is_within_reach() -> None:
    from v2engine import shooting
    sigma = 0.2
    assert shooting._height_pass([math.inf, math.inf], math.inf, sigma) == pytest.approx((1 - shooting.BLOCK_CHANCE) ** 2)
    assert shooting._height_pass([], 0.1, sigma) == pytest.approx(0.5 * (1 + math.erf(0.1 / (sigma * math.sqrt(2)))))
    # un seul défenseur, seuil à 0 : la moitié basse des tirs peut être contrée
    assert shooting._height_pass([0.0], math.inf, sigma) == pytest.approx(0.5 * (1 - shooting.BLOCK_CHANCE) + 0.5)

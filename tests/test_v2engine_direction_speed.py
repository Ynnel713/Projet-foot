"""Se déplacer de face, de côté ou à reculons (ticket v2-realisme/07b) : la vitesse max dépend de l'angle entre la
direction voulue et le cap ; le joueur recule face au ballon pour une cible proche, se retourne et court pour une cible
lointaine ; bandes d'hystérésis sur les seuils (réserve A1 de l'expert au 07a)."""

from __future__ import annotations

import math
from dataclasses import replace

import pytest

from v2engine.geometry import Vec2
from v2engine.movement import (BACK_TO_BALL_DISTANCE_M, FACING_RUN_BAND_MPS, FACING_RUN_SPEED_MPS,
                               TURN_TO_RUN_DISTANCE_M, direction_speed_factor, faces_run, max_speed_mps,
                               step)
from tests.scenes import player

DT = 0.1
EAST = Vec2(1.0, 0.0)


def _dir(deg: float) -> Vec2:
    return Vec2(math.cos(math.radians(deg)), math.sin(math.radians(deg)))


def _angle(v: Vec2) -> float:
    return math.degrees(math.atan2(v.y, v.x))


@pytest.mark.parametrize("deg, part", [(0.0, 1.0), (30.0, 1.0), (45.0, 1.0), (90.0, 0.80), (-90.0, 0.80),
                                       (135.0, 0.725), (180.0, 0.65)])
def test_speed_part_by_angle_to_the_body(deg: float, part: float) -> None:
    assert direction_speed_factor(EAST, _dir(deg)) == pytest.approx(part)


def test_speed_part_is_full_without_a_direction() -> None:
    assert direction_speed_factor(EAST, Vec2(0.0, 0.0)) == 1.0


def _defender_facing_play(**changes) -> object:
    """Défenseur arrêté au milieu, face au jeu (ballon à l'est), Pace 99 pour que le plafond se lise."""
    d = player("D", x=50.0, y=34.0, Pace=99, Acceleration=99)
    return replace(d, facing=EAST, **changes)


def test_defender_backpedals_three_metres_facing_the_ball() -> None:
    d = _defender_facing_play()
    ball, target = Vec2(70.0, 34.0), Vec2(47.0, 34.0)
    top = 0.0
    for _ in range(30):
        d = step(d, DT, target, 0.0, look_at=ball)
        top = max(top, d.velocity.length())
        assert abs(_angle(d.facing)) < 1.0  # il ne se retourne jamais
        assert not d.facing_run
    assert d.position.distance_to(target) < 0.2
    assert top <= 0.65 * max_speed_mps(99) + 1e-9


def test_defender_turns_and_runs_for_twenty_metres() -> None:
    d = _defender_facing_play()
    ball, target = Vec2(70.0, 34.0), Vec2(30.0, 34.0)
    d = step(d, DT, target, 0.0, look_at=ball)
    assert d.facing_run
    for _ in range(15):
        d = step(d, DT, target, 0.0, look_at=ball)
    assert abs(abs(_angle(d.facing)) - 180.0) < 1.0  # dos au ballon, face à sa course
    assert d.velocity.length() > 0.65 * max_speed_mps(99)  # plus vite qu'à reculons


def test_turning_reaches_twenty_metres_sooner_than_backpedalling() -> None:
    """Le choix vaut la peine : se retourner arrive plus tôt que reculer, sur 20 m."""
    ball, target = Vec2(70.0, 34.0), Vec2(30.0, 34.0)

    def ticks(look_at_ball_always: bool) -> int:
        d = _defender_facing_play()
        for n in range(1, 200):
            d = step(d, DT, target, 0.0, look_at=ball)
            if look_at_ball_always:  # corps forcé face au ballon : il recule tout le long
                d = replace(d, facing=EAST, facing_run=False)
            if d.position.distance_to(target) < 0.5:
                return n
        return 200

    assert ticks(False) < ticks(True)


def test_ball_in_the_run_direction_keeps_the_body_on_the_ball() -> None:
    """Cible lointaine mais ballon devant lui (à moins de 45° de sa course) : rien à gagner à se retourner."""
    assert not faces_run(False, 3.0, Vec2(20.0, 0.0), Vec2(70.0, 44.0), Vec2(50.0, 34.0))


def test_distance_hysteresis() -> None:
    at, ball = Vec2(50.0, 34.0), Vec2(70.0, 34.0)
    between = Vec2(-(TURN_TO_RUN_DISTANCE_M + BACK_TO_BALL_DISTANCE_M) / 2.0, 0.0)  # 7 m, entre les deux seuils
    assert not faces_run(False, 3.0, between, ball, at)  # il reculait : il continue
    assert faces_run(True, 3.0, between, ball, at)  # il courait : il continue
    assert not faces_run(True, 3.0, Vec2(-BACK_TO_BALL_DISTANCE_M + 0.1, 0.0), ball, at)
    assert faces_run(False, 3.0, Vec2(-TURN_TO_RUN_DISTANCE_M, 0.0), ball, at)


def test_speed_oscillating_around_the_fast_run_threshold_keeps_the_choice() -> None:
    """Réserve A1 de l'expert au 07a : vitesse de ± 0,1 m/s autour de 19,8 km/h, le choix ne bascule pas."""
    at, ball, near = Vec2(50.0, 34.0), Vec2(50.0, 44.0), Vec2(2.0, 0.0)
    for start in (False, True):
        state = start
        for k in range(20):
            state = faces_run(state, FACING_RUN_SPEED_MPS + (0.1 if k % 2 else -0.1), near, ball, at)
            assert state == start
    assert faces_run(False, FACING_RUN_SPEED_MPS + FACING_RUN_BAND_MPS, near, ball, at)
    assert not faces_run(True, FACING_RUN_SPEED_MPS - FACING_RUN_BAND_MPS - 0.01, near, ball, at)


def test_side_steps_are_capped_at_eighty_percent() -> None:
    """Corps tenu face à l'est (forcé à chaque pas), course vers le nord : plafond de 80 % en pas chassés."""
    d = _defender_facing_play()
    target = Vec2(50.0, 64.0)
    top = 0.0
    for _ in range(40):
        d = replace(step(d, DT, target, 0.0, look_at=Vec2(150.0, 34.0)), facing=EAST)
        top = max(top, d.velocity.length())
    assert top <= 0.80 * max_speed_mps(99) + 1e-9
    assert top > 0.75 * max_speed_mps(99)


def _chase(follow_target_speed: bool) -> tuple[object, Vec2, int | None]:
    """Défenseur face au jeu (ballon à l'est), attaquant à 2 m dans son dos qui part à 8 m/s vers l'ouest (son but) ;
    le défenseur le suit au marquage, avec ou sans la vitesse de sa cible (`target_velocity`). Rend l'état à 2 s et le
    nombre de pas avant d'avoir le dos au ballon (cap à plus de 170°)."""
    d = _defender_facing_play()
    ball = Vec2(70.0, 34.0)
    attacker = Vec2(48.0, 34.0)
    run = Vec2(-8.0, 0.0)
    turned = None
    for n in range(1, 21):
        attacker = attacker + run * DT
        d = step(d, DT, attacker, 0.0, target_velocity=run if follow_target_speed else Vec2(0.0, 0.0), look_at=ball)
        if turned is None and abs(_angle(d.facing)) > 170.0:
            turned = n
    return d, attacker, turned


def test_defender_opens_his_hips_when_the_runner_leaves_faster_than_he_can_backpedal() -> None:
    """Réserve A1 de l'expert : l'appel dans le dos du marqueur. Il pivote en 0,5 s environ (demi-tour 0,48 s à
    Agility 60, plus un pas) et reste plus près de l'attaquant à 2 s que s'il ignorait sa vitesse."""
    d, attacker, turned = _chase(True)
    assert turned is not None and turned * DT <= 0.6
    d_blind, attacker_blind, _ = _chase(False)
    assert d.position.distance_to(attacker) < d_blind.position.distance_to(attacker_blind)


def test_slow_target_behind_keeps_the_body_on_the_ball() -> None:
    """Cible proche qui recule lentement (sous la vitesse à reculons) : il recule face au ballon."""
    at, ball = Vec2(50.0, 34.0), Vec2(70.0, 34.0)
    assert not faces_run(False, 2.0, Vec2(-3.0, 0.0), ball, at, Vec2(-2.0, 0.0), 0.65 * max_speed_mps(60))
    assert faces_run(False, 2.0, Vec2(-3.0, 0.0), ball, at, Vec2(-6.0, 0.0), 0.65 * max_speed_mps(60))


def test_ball_cone_hysteresis() -> None:
    """Réserve A2 : retourné, il ne revient au ballon que sous 40° ; face au ballon, il se retourne au-delà de 45°."""
    at, far = Vec2(50.0, 34.0), Vec2(-20.0, 0.0)  # course vers l'ouest, cible lointaine

    def ball_at(deg: float) -> Vec2:  # ballon à `deg` de la course
        return at + _dir(180.0 - deg) * 10.0

    assert not faces_run(False, 3.0, far, ball_at(43.0), at)
    assert faces_run(True, 3.0, far, ball_at(43.0), at)
    assert not faces_run(True, 3.0, far, ball_at(38.0), at)
    assert faces_run(False, 3.0, far, ball_at(47.0), at)

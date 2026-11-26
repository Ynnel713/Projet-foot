"""Hauteur du ballon, physique pure (ticket v2-hauteur-ballon/02a1, phase 1) : sommet, durée de vol, chute exacte sur le
pas, rebond (rapport 0,49), arrêt des rebonds, ballon qui n'arrive pas, mode « aérien »."""

from __future__ import annotations

import math

import pytest

from v2engine.hauteur import (AERIAL_THRESHOLD_M, GRAVITY_M_S2, GROUND_HORIZONTAL_KEEP, MAX_FLIGHT_S, REBOUND_MIN_APEX_M, apex_m,
                              flight_time_s, is_aerial, launch_vz, step_height, time_to_ground)
from v2engine.possession import BALL_FRICTION_PER_S

TICK = 0.1  # pas du moteur (`match.TICK_SECONDS`)


def _fly(z: float, vz: float, seconds: float, dt: float = TICK):
    """Rejoue `seconds` de vol au pas `dt` : liste des (instant, z, vz, rebonds cumulés, facteur horizontal cumulé)."""
    out, t, bounces, keep = [(0.0, z, vz, 0, 1.0)], 0.0, 0, 1.0
    for _ in range(round(seconds / dt)):
        step = step_height(z, vz, dt)
        z, vz, t = step.z, step.vz, t + dt
        bounces += step.bounces
        keep *= step.horizontal_keep
        out.append((t, z, vz, bounces, keep))
    return out


@pytest.mark.parametrize("vz0", [3.0, 7.5, 10.0, 14.0])
def test_sommet_au_pas_du_moteur(vz0: float) -> None:
    """Point le plus haut mesuré au pas de 0,1 s = vz0² / 2g, écart < 2 %."""
    expected = vz0 * vz0 / (2.0 * GRAVITY_M_S2)
    peak = max(z for _, z, _, b, _ in _fly(0.0, vz0, 2.0 * vz0 / GRAVITY_M_S2) if b == 0)
    assert apex_m(0.0, vz0) == pytest.approx(expected)
    assert abs(peak - expected) / expected < 0.02


@pytest.mark.parametrize("vz0", [3.0, 7.5, 10.0, 14.0])
def test_duree_de_vol_exacte(vz0: float) -> None:
    """Premier contact au sol à 2·vz0 / g, à moins d'un pas ; instant exact dans le pas (pas d'arrondi au tick)."""
    expected = 2.0 * vz0 / GRAVITY_M_S2
    z, vz, t = 0.0, vz0, 0.0
    while True:
        step = step_height(z, vz, TICK)
        if step.first_contact_s is not None:
            contact = t + step.first_contact_s
            break
        z, vz, t = step.z, step.vz, t + TICK
    assert abs(contact - expected) < TICK
    assert contact == pytest.approx(expected, abs=1e-9)
    assert time_to_ground(0.0, vz0) == pytest.approx(expected)


def test_chute_exacte_independante_du_pas() -> None:
    """Même hauteur après 1 s quel que soit le pas (0,1, 0,05, 0,02 s) : la chute est exacte, pas intégrée."""
    ref = _fly(0.0, 10.0, 1.0, dt=1.0)[-1][1]
    for dt in (0.1, 0.05, 0.02):
        assert _fly(0.0, 10.0, 1.0, dt=dt)[-1][1] == pytest.approx(ref, abs=1e-9)
    assert ref == pytest.approx(10.0 - 0.5 * GRAVITY_M_S2)


def test_rebond_hauteur_suivante_049() -> None:
    """Chaque rebond monte à 0,49 × la hauteur du précédent (± 5 %), horizontale × 0,85 par rebond."""
    track = _fly(0.0, 12.0, 8.0, dt=0.001)
    peaks: dict[int, float] = {}
    for _, z, _, bounces, _ in track:
        peaks[bounces] = max(peaks.get(bounces, 0.0), z)
    assert len(peaks) >= 4
    for k in range(1, len(peaks) - 1):
        assert peaks[k] / peaks[k - 1] == pytest.approx(0.49, rel=0.05)
    last_bounces, last_keep = track[-1][3], track[-1][4]
    assert last_keep == pytest.approx(GROUND_HORIZONTAL_KEEP ** last_bounces)


def test_le_ballon_finit_par_rouler() -> None:
    """Les rebonds s'arrêtent : le dernier rebond dépasse 0,15 m, le suivant aurait été plus bas ; ballon à z = 0, vz = 0."""
    track = _fly(0.0, 12.0, 10.0)
    _, z, vz, bounces, _ = track[-1]
    assert (z, vz) == (0.0, 0.0)
    assert bounces >= 1
    last_apex = 12.0 ** 2 / (2.0 * GRAVITY_M_S2) * 0.49 ** bounces
    assert last_apex >= REBOUND_MIN_APEX_M * 0.99
    assert last_apex * 0.49 < REBOUND_MIN_APEX_M


def test_z_jamais_negatif() -> None:
    for vz0 in (0.5, 2.0, 9.0, 20.0):
        assert all(z >= 0.0 for _, z, _, _, _ in _fly(0.0, vz0, 10.0))
    assert step_height(0.0, 0.0, TICK).z == 0.0
    assert step_height(0.0, -1.0, TICK).vz == 0.0


def test_ballon_au_repos_inchange() -> None:
    """Phase 1 : un ballon lancé à vz0 = 0 reste au sol, sans rebond ni freinage horizontal (jeu inchangé)."""
    step = step_height(0.0, 0.0, TICK)
    assert (step.z, step.vz, step.horizontal_keep, step.bounces, step.first_contact_s) == (0.0, 0.0, 1.0, 0, None)


def test_point_de_chute_a_la_cible() -> None:
    """Passe aérienne de 35 m à 20 m/s : durée de vol tirée du freinage exponentiel, point de chute à ± 1 m de la cible."""
    distance, v0 = 35.0, 20.0
    flight = flight_time_s(distance, v0, BALL_FRICTION_PER_S)
    assert flight is not None
    lam = -math.log(BALL_FRICTION_PER_S)
    vz0 = launch_vz(flight)
    landing_t = time_to_ground(0.0, vz0)
    travelled = v0 * (1.0 - math.exp(-lam * landing_t)) / lam
    assert abs(travelled - distance) < 1.0


def test_ballon_qui_n_arrive_pas() -> None:
    """Freinage plus fort que la vitesse : pas de durée de vol (ni division par zéro, ni logarithme d'un négatif)."""
    lam = -math.log(BALL_FRICTION_PER_S)
    assert flight_time_s(10.0 * 1.01, 10.0 * lam, BALL_FRICTION_PER_S) is None
    assert flight_time_s(10.0, 10.0 * lam, BALL_FRICTION_PER_S) is None  # limite exacte
    assert flight_time_s(10.0, 0.0, BALL_FRICTION_PER_S) is None
    assert flight_time_s(0.0, 5.0, BALL_FRICTION_PER_S) == 0.0
    assert launch_vz(0.0) == 0.0
    assert launch_vz(None) == pytest.approx(0.5 * GRAVITY_M_S2 * MAX_FLIGHT_S)  # vol plafonné


def test_mode_aerien_au_dessus_du_genou() -> None:
    assert not is_aerial(0.0)
    assert not is_aerial(AERIAL_THRESHOLD_M)
    assert is_aerial(AERIAL_THRESHOLD_M + 0.01)


def test_vol_plafonne() -> None:
    """Ballon long freiné (56 m à 30 m/s : 6,2 s de vol sans plafond) : vol plafonné à `MAX_FLIGHT_S`, sommet sous 25 m,
    il retombe avant sa cible et à moins de 5 m d'elle."""
    distance, v0 = 56.3, 30.0
    flight = flight_time_s(distance, v0, BALL_FRICTION_PER_S)
    assert flight is not None and flight > MAX_FLIGHT_S
    vz0 = launch_vz(flight)
    assert apex_m(0.0, vz0) < 25.0
    lam = -math.log(BALL_FRICTION_PER_S)
    landing = v0 * (1.0 - math.exp(-lam * time_to_ground(0.0, vz0))) / lam
    assert distance - 5.0 < landing < distance


@pytest.mark.parametrize("distance, speed", [(25.0, 20.0), (35.0, 25.0), (45.0, 30.0)])
def test_point_de_chute_dans_le_moteur(distance: float, speed: float) -> None:
    """Réserve A1 de l'expert (02a1) : lancé par le moteur (`_launch_aerial` puis `_step_ball` au pas du produit, sans
    joueur), le ballon touche le sol pour la première fois à ± 1 m de sa cible."""
    from v2engine.ball_state import BallState
    from v2engine.geometry import Vec2
    from v2engine.match import TICK_SECONDS, _launch_aerial, _step_ball

    start = Vec2(10.0, 34.0)
    ball = BallState(position=start, velocity=Vec2(speed, 0.0))
    _launch_aerial(ball, distance)
    assert ball.vz > 0.0
    for i in range(200):
        before, z0, vz0 = ball.position, ball.z, ball.vz
        _step_ball(ball, TICK_SECONDS, [], i * TICK_SECONDS)
        contact = step_height(z0, vz0, TICK_SECONDS).first_contact_s
        if contact is not None:
            landing = before.x + (ball.position.x - before.x) * contact / TICK_SECONDS
            assert abs(landing - start.x - distance) < 1.0
            return
    pytest.fail("le ballon n'est jamais retombé")

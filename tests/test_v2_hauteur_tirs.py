"""Hauteur des tirs (ticket v2-hauteur-ballon/02a2) : le tir en vol part du sol avec la vitesse verticale qui l'amène, à
la ligne de but, à la hauteur tirée par la loi du 35b, conditionnée à l'issue : cadré, haut du ballon sous la barre ;
au-dessus, bas du ballon au-dessus de la barre. Bande 2,22–2,44 m (ballon sur la barre) jamais produite (poteaux et barre :
ticket v2-collectif/35c)."""

from __future__ import annotations

import math
import random
from statistics import NormalDist

import pytest

from ligue1sim.pitch_geometry import GOAL_HEIGHT_M

from v2engine import hauteur, match
from v2engine.ball_state import BallState
from v2engine.decision import Action
from v2engine.geometry import PITCH_LENGTH_M, Vec2
from v2engine.match import BALL_RADIUS_M, GOAL_CENTER_Y, SHOT_SPEED_MPS, TICK_SECONDS, _step_ball
from v2engine.movement import PlayerState
from v2engine.possession import BALL_FRICTION_PER_S
from v2engine.shooting import FLYING, OVER, SHOT_AIM_HEIGHT_M, ground_strike_m, line_height_m

DIAMETER_M = 2.0 * BALL_RADIUS_M
SIGMA = 0.18


def _player(name: str, team: str, poste: str, position: Vec2) -> PlayerState:
    return PlayerState(name=name, team=team, poste=poste, position=position, velocity=Vec2(0.0, 0.0), pace=60,
                       acceleration=60, stamina=60, home_target=position, attributes=None)


def _slope(distance_m: float, height_m: float) -> float:
    return (height_m - SHOT_AIM_HEIGHT_M) / distance_m


# --- loi de la hauteur à la ligne (`shooting.line_height_m`) ---

@pytest.mark.parametrize("height", [GOAL_HEIGHT_M, GOAL_HEIGHT_M + 0.01, 3.0, 8.0])
def test_a_shot_over_the_bar_keeps_its_drawn_height_as_the_bottom_of_the_ball(height) -> None:
    assert line_height_m(_slope(20.0, height), SIGMA, 20.0, DIAMETER_M) == pytest.approx(height)


@pytest.mark.parametrize("distance", [6.0, 11.0, 20.0, 30.0])
def test_a_shot_under_the_bar_passes_with_the_top_of_the_ball_under_the_bar(distance) -> None:
    for height in (GOAL_HEIGHT_M - 1e-6, 2.3, 2.2, 1.5, 1.0, 0.3):
        z = line_height_m(_slope(distance, height), SIGMA, distance, DIAMETER_M)
        assert z + DIAMETER_M <= GOAL_HEIGHT_M + 1e-12
        assert (z < 0.0) == (height < 0.0) or height >= 0.0  # négatif seulement si la droite visée passe sous le sol


def test_the_mapping_keeps_the_order_of_heights_and_never_reaches_the_band_on_the_bar() -> None:
    heights = [GOAL_HEIGHT_M * k / 200.0 for k in range(200)]
    mapped = [line_height_m(_slope(16.0, h), SIGMA, 16.0, DIAMETER_M) for h in heights]
    assert mapped == sorted(mapped)
    assert not any(GOAL_HEIGHT_M - DIAMETER_M < z <= GOAL_HEIGHT_M for z in mapped)


def test_the_height_under_the_bar_follows_the_same_law_conditioned_on_the_top_under_the_bar() -> None:
    # écart gaussien tiré comme en match ; sous la barre, la hauteur ramenée suit la loi conditionnée à « haut du ballon
    # sous la barre » : sa fonction de répartition est celle de la loi tronquée (Kolmogorov, écart < 0,02 sur 20 000)
    rng, distance, normal = random.Random(7), 16.0, NormalDist()
    top = math.atan2(GOAL_HEIGHT_M - DIAMETER_M - SHOT_AIM_HEIGHT_M, distance)
    samples = []
    while len(samples) < 20000:
        slope = math.tan(rng.gauss(0.0, SIGMA))
        if SHOT_AIM_HEIGHT_M + distance * slope < GOAL_HEIGHT_M:
            samples.append(line_height_m(slope, SIGMA, distance, DIAMETER_M))
    samples.sort()
    worst = 0.0
    for z in (0.0, 0.5, 1.0, 1.5, 2.0, 2.2):
        expected = (normal.cdf(math.atan2(z - SHOT_AIM_HEIGHT_M, distance) / SIGMA) / normal.cdf(top / SIGMA)
                    if z < GOAL_HEIGHT_M - DIAMETER_M else 1.0)
        seen = sum(1 for s in samples if s <= z) / len(samples)
        worst = max(worst, abs(seen - expected))
    assert worst < 0.02


def test_a_shot_aimed_into_the_ground_strikes_it_where_the_aimed_line_meets_it() -> None:
    z = line_height_m(_slope(16.0, -0.5), SIGMA, 16.0, DIAMETER_M)
    assert z < 0.0
    strike = ground_strike_m(z, 16.0)
    assert 0.0 < strike < 16.0 and SHOT_AIM_HEIGHT_M + strike * (z - SHOT_AIM_HEIGHT_M) / 16.0 == pytest.approx(0.0)
    assert ground_strike_m(1.2, 16.0) == 16.0 and ground_strike_m(0.0, 16.0) == 16.0
    extreme = line_height_m(math.tan(-1.5), SIGMA, 16.0, DIAMETER_M)  # écart extrême : quantile nul, pas d'erreur
    assert extreme < 0.0 and 0.0 < ground_strike_m(extreme, 16.0) < 1.0
    assert line_height_m(0.3, SIGMA, 0.0, DIAMETER_M) == 0.0  # tir depuis la ligne


# --- trajectoire (`hauteur.stepped_travel_time_s`, `hauteur.launch_vz_to`) ---

@pytest.mark.parametrize("distance", [0.5, 6.0, 16.0, 29.7])
def test_the_travel_time_is_that_of_the_engine_steps(distance) -> None:
    t = hauteur.stepped_travel_time_s(distance, SHOT_SPEED_MPS, BALL_FRICTION_PER_S, TICK_SECONDS)
    done, speed, elapsed = 0.0, SHOT_SPEED_MPS, 0.0
    while done + speed * TICK_SECONDS < distance:
        done, speed, elapsed = done + speed * TICK_SECONDS, speed * BALL_FRICTION_PER_S**TICK_SECONDS, elapsed + TICK_SECONDS
    assert t == pytest.approx(elapsed + (distance - done) / speed)


def test_a_ball_that_stops_before_the_point_has_no_travel_time() -> None:
    assert hauteur.stepped_travel_time_s(1000.0, 5.0, BALL_FRICTION_PER_S, TICK_SECONDS) is None
    assert hauteur.stepped_travel_time_s(0.0, 5.0, BALL_FRICTION_PER_S, TICK_SECONDS) == 0.0
    assert hauteur.launch_vz_to(1.0, None) == 0.0 and hauteur.launch_vz_to(1.0, 0.0) == 0.0


@pytest.mark.parametrize("target", [0.0, 1.0, 2.2, 6.0])
def test_the_launch_speed_brings_the_bottom_of_the_ball_to_the_target_height(target) -> None:
    flight = 0.8
    z = 0.0
    vz = hauteur.launch_vz_to(target, flight)
    step = hauteur.step_height(z, vz, flight - 1e-9)
    assert step.bounces == 0 and step.z == pytest.approx(target, abs=1e-6)


# --- dans le moteur ---

def _shoot(monkeypatch, height_m: float, defender: PlayerState | None = None, distance: float = 20.0,
           until_touched: bool = False):
    """Tir face au but depuis `distance`, réglé pour arriver au centre du but à `height_m` (loi du 35b, avant ramenée) ;
    gardien hors de portée. Retourne (tirs, ballon, hauteurs du ballon pendant le vol, but). `until_touched` : arrêt au
    pas où le tir cesse d'être en vol (contre, arrêt)."""
    shooter = _player("Buteur", "home", "BU", Vec2(PITCH_LENGTH_M - distance, GOAL_CENTER_Y))
    keeper = _player("Gardien", "away", "GK", Vec2(PITCH_LENGTH_M - 1.0, GOAL_CENTER_Y + 10.0))
    players = [shooter, keeper] + ([defender] if defender is not None else [])
    monkeypatch.setattr(match, "should_attempt_tackle", lambda aggression, dt: False)
    monkeypatch.setattr(match, "choose_action", lambda *args: Action("shot", 1.0))
    if defender is None:
        monkeypatch.setattr(match, "BLOCK_CHANCE", 0.0)
    error = (0.0, math.atan2(height_m - SHOT_AIM_HEIGHT_M, distance))
    monkeypatch.setattr(match, "draw_shot_error", lambda *args: error)
    ball = BallState(position=shooter.position, velocity=Vec2(0.0, 0.0), holder="Buteur")
    shots, heights, scored = [], [], None
    for tick in range(60):
        scored = _step_ball(ball, TICK_SECONDS, players, tick * TICK_SECONDS, shots=shots)
        heights.append((ball.z, ball.vz, ball.shot_in_flight))
        if scored is not None or ball.restart is not None or (until_touched and tick > 0 and not ball.shot_in_flight):
            break
    return shots, ball, heights, scored


def test_a_goal_arcs_from_the_ground_and_crosses_with_the_top_of_the_ball_under_the_bar(monkeypatch) -> None:
    shots, ball, heights, scored = _shoot(monkeypatch, 2.3)  # sous la barre avant ramenée
    assert scored == "home" and shots[0].outcome == "but"
    assert shots[0].line_z_m + DIAMETER_M < GOAL_HEIGHT_M and shots[0].line_z_m > 1.0
    in_flight = [(z, vz) for z, vz, flying in heights if flying]
    assert in_flight[0] == (0.0, pytest.approx(in_flight[0][1])) and in_flight[0][1] > 0.0  # frappe : au pied, il monte
    assert all(z > 0.0 for z, _ in in_flight[1:])  # en l'air dès le pas suivant
    assert ball.z == 0.0 and ball.vz == 0.0  # ballon mort posé pour l'engagement


def test_a_shot_over_the_bar_crosses_with_the_bottom_of_the_ball_above_the_bar(monkeypatch) -> None:
    shots, ball, _, scored = _shoot(monkeypatch, GOAL_HEIGHT_M + 0.3)
    assert scored is None and shots[0].outcome == OVER
    assert shots[0].line_z_m == pytest.approx(GOAL_HEIGHT_M + 0.3, abs=1e-9)
    assert ball.z == 0.0 and ball.vz == 0.0  # sortie de but : ballon posé


def test_the_line_height_of_the_engine_is_the_drawn_one(monkeypatch) -> None:
    drawn = []
    real = match.line_height_m
    monkeypatch.setattr(match, "line_height_m", lambda *a: drawn.append(real(*a)) or drawn[-1])
    for height in (0.4, 1.0, 1.9, 2.4):  # au-dessus du sol après ramenée (sinon : rebond, test plus bas)
        shots, _, _, _ = _shoot(monkeypatch, height, distance=14.0)
        assert shots[0].line_z_m == pytest.approx(drawn[-1], abs=1e-9)


def test_a_blocked_shot_restarts_from_the_ground_and_gets_no_line_height(monkeypatch) -> None:
    # tir haut (sommet au-dessus du défenseur, contre encore jugé à plat jusqu'au ticket 03) : contré, le ballon repart
    # du sol comme tout ballon touché ; il n'est plus un tir, sa hauteur à la ligne n'est pas recalculée ni tracée
    monkeypatch.setattr(match, "BLOCK_CHANCE", 1.0)
    defender = _player("Defenseur", "away", "DC", Vec2(PITCH_LENGTH_M - 12.0, GOAL_CENTER_Y + 0.6))
    shots, ball, heights, _ = _shoot(monkeypatch, 2.2, defender=defender)
    assert shots[0].outcome == "contré" and shots[0].line_z_m is None
    blocked_at = next(k for k, (_, _, flying) in enumerate(heights) if not flying)
    assert heights[blocked_at - 1][0] > 0.0  # il était en l'air au pas d'avant
    assert all(z == 0.0 and vz == 0.0 for z, vz, _ in heights[blocked_at:])  # au sol ensuite, sans nouveau vol
    assert ball.z == 0.0


def test_a_blocked_shot_is_a_loose_ball_that_rolls_on_with_the_engine(monkeypatch) -> None:
    # le ballon contré n'est pas figé : libre, sans porteur, il roule et freine comme tout ballon libre (pas du ballon du
    # 02a1, `BALL_FRICTION_PER_S`), au mode « sol »
    monkeypatch.setattr(match, "BLOCK_CHANCE", 1.0)
    defender = _player("Defenseur", "away", "DC", Vec2(PITCH_LENGTH_M - 12.0, GOAL_CENTER_Y + 0.6))
    shots, ball, heights, _ = _shoot(monkeypatch, 2.2, defender=defender, until_touched=True)
    assert shots[0].outcome == "contré"
    blocked_at = len(heights) - 1
    monkeypatch.setattr(match, "_ball_contacts", lambda *args, **kwargs: [])  # personne ne le reprend : on suit son trajet
    # le même ballon, juste après le contre, continue sous le pas du ballon libre (pas de remise en jeu tant qu'il est
    # dans le terrain)
    far = _player("Loin", "home", "BU", Vec2(5.0, 5.0))
    positions, speeds = [ball.position], [ball.velocity.length()]
    assert ball.holder is None and ball.restart is None and speeds[0] > 1.0
    for tick in range(4):
        _step_ball(ball, TICK_SECONDS, [far], (blocked_at + 1 + tick) * TICK_SECONDS)
        if ball.restart is not None:
            break
        positions.append(ball.position)
        speeds.append(ball.velocity.length())
        assert ball.holder is None and ball.z == 0.0 and ball.vz == 0.0 and ball.mode == match.SOL
    assert len(positions) >= 3 and all(a.distance_to(b) > 0.05 for a, b in zip(positions, positions[1:]))  # il roule
    for before, after in zip(speeds, speeds[1:]):
        assert after == pytest.approx(before * BALL_FRICTION_PER_S**TICK_SECONDS)  # il freine comme un ballon libre


def test_a_parried_shot_restarts_from_the_ground(monkeypatch) -> None:
    # gardien dans l'axe, repoussé imposé : le ballon repart du sol (vraie parade en hauteur : tickets v2-realisme/03a, 03f)
    monkeypatch.setattr(match, "save_outcome", lambda *args: match.PARRIED)
    shooter = _player("Buteur", "home", "BU", Vec2(PITCH_LENGTH_M - 20.0, GOAL_CENTER_Y))
    keeper = _player("Gardien", "away", "GK", Vec2(PITCH_LENGTH_M - 1.0, GOAL_CENTER_Y))
    monkeypatch.setattr(match, "should_attempt_tackle", lambda aggression, dt: False)
    monkeypatch.setattr(match, "choose_action", lambda *args: Action("shot", 1.0))
    monkeypatch.setattr(match, "BLOCK_CHANCE", 0.0)
    monkeypatch.setattr(match, "draw_shot_error", lambda *args: (0.0, math.atan2(0.8, 20.0)))
    ball = BallState(position=shooter.position, velocity=Vec2(0.0, 0.0), holder="Buteur")
    shots = []
    for tick in range(15):
        _step_ball(ball, TICK_SECONDS, [shooter, keeper], tick * TICK_SECONDS, shots=shots)
        if shots[0].outcome != FLYING:
            break
    assert shots[0].outcome == match.PARRIED and shots[0].line_z_m is None
    assert ball.z == 0.0 and ball.vz == 0.0 and ball.holder is None


@pytest.mark.parametrize("height,distance", [(-0.5, 20.0), (-3.0, 25.0), (-1.0, 8.0)])
def test_a_shot_aimed_into_the_ground_bounces_or_rolls_before_the_line_under_the_engine(monkeypatch, height,
                                                                                        distance) -> None:
    # pas de hauteur imposée à la ligne : il retombe où la droite visée touche le sol, puis le pas du 02a1 décide (rebond à
    # 0,70, vitesse horizontale × 0,85, il roule sous 0,15 m de sommet) ; il entre quand même (sous la barre)
    trace = []
    real = hauteur.step_height
    monkeypatch.setattr(hauteur, "step_height", lambda z, vz, dt: trace.append(real(z, vz, dt)) or trace[-1])
    shots, _, heights, scored = _shoot(monkeypatch, height, distance=distance)
    assert scored == "home" and shots[0].outcome == "but"
    assert any(step.first_contact_s is not None for step in trace)  # il a touché le sol avant la ligne
    assert 0.0 <= shots[0].line_z_m < 0.5  # au ras du sol à la ligne : rebond bas ou roulé
    assert all(z >= 0.0 for z, _, _ in heights)

"""Socle cinématique et contact du ballon (ticket v2-collectif/25) : montée en vitesse exponentielle, freinage
borné, loi d'arrivée, contact sur le trajet du ballon, contrôle raté qui coûte vraiment -- indépendants du pas."""

from __future__ import annotations

import math
import random

import pytest

from v2engine.ball_state import BallState
from v2engine.geometry import Vec2
from v2engine.match import CONTROL_RADIUS_M, _step_ball
from v2engine.movement import DECEL_MAX_MPS2, PlayerState, accel_tau_s, max_speed_mps, step
from v2engine.possession import MISS_DEVIATION_MAX_DEG, MISS_RETRY_S, MISS_SPEED_SHARE

STEPS = (0.05, 0.1, 0.15)


def _player(name: str = "P", team: str = "home", pace: float = 60, acceleration: float = 60,
            position: Vec2 = Vec2(10.0, 34.0), attributes: dict[str, int] | None = None) -> PlayerState:
    return PlayerState(name=name, team=team, poste="MC", position=position, velocity=Vec2(0.0, 0.0), pace=pace,
                       acceleration=acceleration, stamina=99, home_target=position, attributes=attributes)


def _run(state: PlayerState, dt: float, seconds: float, target: Vec2, factor=lambda t: 1.0):
    """Trajectoire (instant, position, vitesse) d'un joueur dirigé vers `target` pendant `seconds`."""
    out = [(0.0, state.position, state.velocity)]
    for i in range(round(seconds / dt)):
        state = step(state, dt, target, 0.0, factor(i * dt))
        out.append(((i + 1) * dt, state.position, state.velocity))
    return out


# --- Arrivée -------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("dt", STEPS)
def test_arrival_at_fixed_target_without_overshoot_or_oscillation(dt) -> None:
    start, target = Vec2(10.0, 34.0), Vec2(30.0, 34.0)
    traj = _run(_player(position=start), dt, 30.0, target)
    xs = [p.x for _, p, _ in traj]
    assert max(xs) - target.x <= 0.5  # dépassement
    stopped = next(t for t, p, v in traj if v.length() < 0.2 and p.distance_to(target) < 0.5)
    assert stopped < 6.0
    last = [p.x for t, p, _ in traj if t >= 20.0]
    assert max(last) - min(last) < 0.3  # amplitude sur les 10 dernières secondes


def test_final_position_independent_of_step() -> None:
    finals = [_run(_player(), dt, 30.0, Vec2(30.0, 34.0))[-1][1] for dt in STEPS]
    assert max(a.distance_to(b) for a in finals for b in finals) <= 0.1


# --- Freinage borné ------------------------------------------------------------------------------------------

def _max_decel(traj) -> float:
    worst = 0.0
    for (t0, _, v0), (t1, _, v1) in zip(traj, traj[1:]):
        worst = max(worst, (v0.length() - v1.length()) / (t1 - t0))
    return worst


@pytest.mark.parametrize("dt", STEPS)
def test_deceleration_never_exceeds_cap(dt) -> None:
    limit = DECEL_MAX_MPS2 * 1.01
    # baisse d'intensité d'un coup (sprint puis 40 %), arrivée, demi-tour
    drop = _run(_player(pace=99, acceleration=99), dt, 8.0, Vec2(100.0, 34.0), lambda t: 1.0 if t < 4.0 else 0.4)
    arrival = _run(_player(pace=99, acceleration=99), dt, 12.0, Vec2(40.0, 34.0))
    sprint = _run(_player(pace=99, acceleration=99), dt, 4.0, Vec2(100.0, 34.0))
    flying = _player(pace=99, acceleration=99, position=sprint[-1][1])
    flying.velocity = sprint[-1][2]
    u_turn = _run(flying, dt, 5.0, Vec2(0.0, 34.0))
    for traj in (drop, arrival, u_turn):
        assert _max_decel(traj) <= limit


# --- Montée en vitesse ---------------------------------------------------------------------------------------

def test_initial_acceleration_follows_vmax_over_tau() -> None:
    dt = 0.01
    s = step(_player(acceleration=55), dt, Vec2(100.0, 34.0), 0.0)
    expected = max_speed_mps(60) / accel_tau_s(55)
    assert s.velocity.length() / dt == pytest.approx(expected, rel=0.02)


def test_acceleration_tau_points_validated() -> None:
    assert accel_tau_s(99) == pytest.approx(1.0)
    assert accel_tau_s(55) == pytest.approx(1.2)
    assert accel_tau_s(11) == pytest.approx(1.5)


def _time_to(distance: float, acceleration: float, dt: float = 0.1) -> float:
    for t, p, _ in _run(_player(acceleration=acceleration), dt, 10.0, Vec2(100.0, 34.0)):
        if p.x - 10.0 >= distance:
            return t
    raise AssertionError("jamais atteint")


def test_higher_acceleration_wins_the_first_ten_metres() -> None:  # TEST-V01
    assert _time_to(10.0, 11) - _time_to(10.0, 99) >= 0.2


# --- Contact sur le trajet -----------------------------------------------------------------------------------

@pytest.mark.parametrize("dt", STEPS)
@pytest.mark.parametrize("speed", (6.0, 10.0, 16.0, 21.0, 30.0))
def test_ball_crossing_a_still_player_always_makes_contact(monkeypatch, dt, speed) -> None:
    monkeypatch.setattr("v2engine.match.attempt_control", lambda *a, **k: True)
    for k in range(100):
        player = _player(position=Vec2(50.0, 34.0))
        offset = speed * dt * k / 100.0  # 100 positions de départ décalées sur un pas
        ball = BallState(position=Vec2(50.0 - 3.0 - offset, 34.0), velocity=Vec2(speed, 0.0))
        for i in range(int(2.0 / dt)):
            _step_ball(ball, dt, [player], i * dt)
            if ball.holder is not None:
                break
        assert ball.holder == "P", (speed, dt, k)


@pytest.mark.parametrize("first_team", ("home", "away"))
def test_first_player_reached_tries_first_whatever_his_team(monkeypatch, first_team) -> None:
    tried: list[str] = []
    monkeypatch.setattr("v2engine.match.attempt_control", lambda player, *a, **k: tried.append(player.name) or True)
    other = "away" if first_team == "home" else "home"
    # les deux joueurs sont atteints pendant le même pas ; l'autre est en tête de liste
    near = _player(name="premier", team=first_team, position=Vec2(50.0, 34.0))
    far = _player(name="second", team=other, position=Vec2(51.5, 34.0))
    ball = BallState(position=Vec2(49.0, 34.0), velocity=Vec2(30.0, 0.0))
    _step_ball(ball, 0.15, [far, near])
    assert tried[0] == "premier" and ball.holder == "premier"


# --- Contrôle raté -------------------------------------------------------------------------------------------

def test_missed_control_deflects_within_bounds_and_blocks_retry(monkeypatch) -> None:
    monkeypatch.setattr("v2engine.match.attempt_control", lambda *a, **k: False)
    random.seed(7)
    for _ in range(200):
        player = _player(position=Vec2(50.0, 34.0))
        incoming = Vec2(12.0, 0.0)
        ball = BallState(position=Vec2(49.5, 34.0), velocity=incoming, readers={"X": Vec2(0.0, 0.0)})
        _step_ball(ball, 0.1, [player], 3.0)
        angle = math.degrees(math.atan2(ball.velocity.y, ball.velocity.x))
        assert abs(angle) <= MISS_DEVIATION_MAX_DEG + 1e-9
        assert ball.velocity.length() == pytest.approx(MISS_SPEED_SHARE * incoming.length() * 0.6 ** 0.1, rel=0.05)
        assert ball.readers == {}
        assert ball.control_ban_until_s["P"] == pytest.approx(3.0 + MISS_RETRY_S)


def test_same_player_does_not_retry_before_delay(monkeypatch) -> None:
    calls: list[float] = []
    monkeypatch.setattr("v2engine.match.attempt_control", lambda *a, **k: calls.append(1) or False)
    player = _player(position=Vec2(50.0, 34.0))
    ball = BallState(position=Vec2(50.0, 34.0), velocity=Vec2(0.0, 0.0))
    t = 0.0
    while t < MISS_RETRY_S - 1e-9:
        ball.position, ball.velocity = Vec2(50.0, 34.0), Vec2(0.0, 0.0)  # ballon replacé au contact à chaque pas
        _step_ball(ball, 0.1, [player], t)
        t += 0.1
    assert len(calls) == 1


def test_dead_pass_forgets_readers() -> None:
    ball = BallState(position=Vec2(50.0, 34.0), velocity=Vec2(0.52, 0.0), receiver="R", readers={"X": Vec2(0.0, 0.0)})
    _step_ball(ball, 0.1, [_player(position=Vec2(5.0, 5.0))])
    assert ball.readers == {}


def test_better_first_touch_keeps_the_ball_more_often() -> None:
    random.seed(20260923)

    def kept(first_touch: int) -> float:
        n = 0
        for _ in range(400):
            player = _player(position=Vec2(50.0, 34.0), attributes={"First Touch": first_touch})
            ball = BallState(position=Vec2(49.0, 34.0), velocity=Vec2(18.0, 0.0))
            _step_ball(ball, 0.1, [player])
            n += ball.holder == "P"
        return n / 400

    assert kept(99) - kept(11) >= 0.2


def test_ball_never_left_overlapping_after_miss(monkeypatch) -> None:
    monkeypatch.setattr("v2engine.match.attempt_control", lambda *a, **k: False)
    player = _player(position=Vec2(50.0, 34.0))
    player.velocity = Vec2(5.0, 0.0)
    ball = BallState(position=Vec2(50.0, 34.0), velocity=Vec2(0.0, 0.0))
    _step_ball(ball, 0.1, [player])
    assert ball.position.distance_to(player.position) >= CONTROL_RADIUS_M - 1e-6


def test_product_and_bench_use_the_same_step() -> None:
    from api.routers import v2 as api_v2
    from scripts import measure_v2

    assert api_v2._TICK_SECONDS == measure_v2.TICK_S == 0.1
    assert api_v2._TICK_SECONDS * api_v2._RECORD_EVERY == pytest.approx(1.0)  # une image par seconde


def test_passer_does_not_touch_his_own_pass_as_it_leaves(monkeypatch) -> None:
    tried: list[str] = []
    monkeypatch.setattr("v2engine.match.attempt_control", lambda player, *a, **k: tried.append(player.name) or True)
    passer = _player(name="passeur", position=Vec2(50.0, 34.0))
    ball = BallState(position=Vec2(50.0, 34.0), velocity=Vec2(15.0, 0.0), released_by="passeur")  # passe qui part de ses pieds
    _step_ball(ball, 0.1, [passer])
    assert tried == [] and ball.holder is None



@pytest.mark.parametrize("dt", STEPS)
@pytest.mark.parametrize("pass_deg", range(0, 360, 45))
@pytest.mark.parametrize("run_deg", range(0, 360, 90))
def test_moving_passer_does_not_touch_his_own_pass_as_it_leaves(monkeypatch, dt, pass_deg, run_deg) -> None:
    """Ticket v2-collectif/26 : il a bougé pendant le pas où il passe, en freinant (sa vitesse a baissé de 5 à
    4 m/s) : l'estimation de sa position de début de pas est décalée de quelques centimètres, et le ballon, parti
    de ses pieds, s'éloigne quand même de lui."""
    tried: list[str] = []
    monkeypatch.setattr("v2engine.match.attempt_control", lambda player, *a, **k: tried.append(player.name) or True)
    release = Vec2(50.0, 34.0)
    run = Vec2(math.cos(math.radians(run_deg)), math.sin(math.radians(run_deg)))
    passer = _player(name="passeur", position=release + run * (4.5 * dt))  # 5 m/s au départ, 4 m/s à la fin
    passer.velocity = run * 4.0
    pass_dir = Vec2(math.cos(math.radians(pass_deg)), math.sin(math.radians(pass_deg)))
    ball = BallState(position=release, velocity=pass_dir * 12.0, released_by="passeur")
    _step_ball(ball, dt, [passer])
    assert tried == [] and ball.holder is None


def test_passer_can_take_back_a_pass_coming_back_to_him(monkeypatch) -> None:
    monkeypatch.setattr("v2engine.match.attempt_control", lambda *a, **k: True)
    passer = _player(name="passeur", position=Vec2(50.0, 34.0))
    ball = BallState(position=Vec2(51.0, 34.0), velocity=Vec2(-8.0, 0.0), released_by="passeur")  # elle revient
    _step_ball(ball, 0.1, [passer])
    assert ball.holder == "passeur"

# --- Cible mobile (revue expert du 29/10/2026, A1) ------------------------------------------------------------

def _chase(dt: float, chaser_pace: float, seconds: float = 12.0) -> list[float]:
    """Écart entre un poursuivant parti 10 m derrière et un porteur qui conduit en ligne droite à 7,4 m/s. La cible
    du poursuivant a un pas de retard, comme dans `simulate_match` (ballon mis à jour après les joueurs)."""
    u = 7.4
    carrier = Vec2(10.0, 34.0)  # 10 + 7,4 × 12 < 105 m : la course reste sur le terrain
    chaser = _player(pace=chaser_pace, acceleration=99, position=Vec2(0.0, 34.0))
    chaser.velocity = Vec2(u, 0.0)
    gaps = []
    for _ in range(round(seconds / dt)):
        chaser = step(chaser, dt, carrier, 0.0, 1.0, target_velocity=Vec2(u, 0.0))
        carrier = carrier + Vec2(u * dt, 0.0)
        gaps.append(carrier.x - chaser.position.x)
    return gaps


@pytest.mark.parametrize("dt", STEPS)
def test_faster_chaser_catches_a_dribbling_carrier(dt) -> None:
    gaps = _chase(dt, chaser_pace=99)
    assert min(gaps) < 1.5  # il entre dans le rayon de tacle
    assert min(gaps) > -0.5  # sans le dépasser franchement


@pytest.mark.parametrize("dt", STEPS)
def test_equal_speed_chaser_keeps_his_gap(dt) -> None:
    gaps = _chase(dt, chaser_pace=23)  # 7,4 m/s : sa vitesse max vaut celle du porteur
    assert max(gaps) - gaps[0] < 1.0  # pas de recul de plusieurs mètres


def test_pressers_follow_the_carrier_velocity() -> None:
    from v2engine.cerveau import think

    carrier = _player(name="C", team="away", position=Vec2(50.0, 34.0))
    carrier.velocity = Vec2(-6.0, 0.0)
    presser = _player(name="D", team="home", position=Vec2(56.0, 34.0))
    ball = BallState(position=carrier.position, velocity=Vec2(0.0, 0.0), holder="C")
    intention = think(presser, ball, [carrier, presser], 10.0, None)
    assert intention.target_velocity == carrier.velocity


def test_released_by_is_forgotten_once_someone_controls(monkeypatch) -> None:
    monkeypatch.setattr("v2engine.match.attempt_control", lambda *a, **k: True)
    receiver = _player(name="R", position=Vec2(50.0, 34.0))
    ball = BallState(position=Vec2(49.0, 34.0), velocity=Vec2(10.0, 0.0), released_by="passeur")
    _step_ball(ball, 0.1, [receiver])
    assert ball.holder == "R" and ball.released_by is None


def test_tie_at_contact_goes_to_the_closest_whatever_the_order(monkeypatch) -> None:
    tried: list[str] = []
    monkeypatch.setattr("v2engine.match.attempt_control", lambda player, *a, **k: tried.append(player.name) or True)
    near = _player(name="près", team="away", position=Vec2(50.05, 34.0))
    far = _player(name="loin", team="home", position=Vec2(50.3, 34.0))
    ball = BallState(position=Vec2(50.0, 34.0), velocity=Vec2(0.0, 0.0))  # dans les deux rayons dès le départ
    _step_ball(ball, 0.1, [far, near])
    assert tried[0] == "près"

"""Tests du moteur V2, Phase 1 (déplacement) -- voir docs/PLAN_V2.md, critères d'acceptation.
Lecture seule de la V1 (`ligue1sim.clubs`/`ligue1sim.players`) : aucun fichier protégé importé."""

from __future__ import annotations

from ligue1sim.clubs import load_clubs
from ligue1sim.players import Player
from ligue1sim.season import CLUBS_PATH

from v2engine.attributes import player_attribute
from v2engine.geometry import PITCH_LENGTH_M, PITCH_WIDTH_M, Vec2
from v2engine.match import BALL_RADIUS_M, PLAYER_RADIUS_M, _resolve_player_collisions, _step_ball, simulate_match
from v2engine.movement import PlayerState, accel_time_s, stamina_factor, step


def _player_state(name: str = "P", pace: float = 60, acceleration: float = 60, stamina: float = 60,
                   position: Vec2 = Vec2(0.0, 0.0)) -> PlayerState:
    return PlayerState(
        name=name, team="home", poste="BU", position=position, velocity=Vec2(0.0, 0.0),
        pace=pace, acceleration=acceleration, stamina=stamina, home_target=position,
    )


def _run_toward_target(state: PlayerState, target: Vec2, *, dt: float = 0.1, n_ticks: int = 50, minute: float = 0.0) -> PlayerState:
    for _ in range(n_ticks):
        state = step(state, dt, target, minute)
    return state


def test_higher_pace_covers_more_distance_in_same_time() -> None:
    target = Vec2(100.0, 0.0)
    slow = _run_toward_target(_player_state(pace=10), target)
    fast = _run_toward_target(_player_state(pace=99), target)

    assert fast.position.distance_to(Vec2(0.0, 0.0)) > slow.position.distance_to(Vec2(0.0, 0.0))


def test_higher_acceleration_reaches_max_speed_sooner() -> None:
    assert accel_time_s(99) < accel_time_s(5)


def test_stamina_reduces_speed_late_in_match() -> None:
    late_minute = 85.0
    assert stamina_factor(10, late_minute) < stamina_factor(95, late_minute)
    # En début de match, la fatigue ne joue pas encore, quelle que soit la Stamina.
    assert stamina_factor(10, 10.0) == 1.0


def test_missing_attributes_fall_back_to_neutral_default() -> None:
    no_attributes = Player(prenom="A", nom="N", nationalite="FRA", age=25, poste="BU", note=65.0,
                            club="C", championnat="Ligue 1", attributes=None)
    assert player_attribute(no_attributes, "Pace") == 60

    partial_attributes = Player(prenom="B", nom="N", nationalite="FRA", age=25, poste="BU", note=65.0,
                                 club="C", championnat="Ligue 1", attributes={"Finishing": 80})
    assert player_attribute(partial_attributes, "Pace") == 60
    assert player_attribute(partial_attributes, "Finishing") == 80


def test_overlapping_players_are_pushed_apart() -> None:
    a = _player_state(name="A", position=Vec2(50.0, 34.0))
    b = _player_state(name="B", position=Vec2(50.1, 34.0))  # chevauchement (rayon 0.3 m chacun)
    players = [a, b]

    _resolve_player_collisions(players)

    assert players[0].position.distance_to(players[1].position) >= 2 * PLAYER_RADIUS_M - 1e-6


def test_ball_bounces_off_player_instead_of_passing_through() -> None:
    runner = _player_state(position=Vec2(50.0, 34.0))
    runner.velocity = Vec2(5.0, 0.0)
    ball_position = Vec2(50.0, 34.0)  # superposé au joueur
    ball_velocity = Vec2(0.0, 0.0)

    new_position, new_velocity = _step_ball(ball_position, ball_velocity, 0.1, [runner])

    assert new_velocity.length() > 0.0  # a reçu une vitesse de l'interaction, pas resté immobile
    assert new_position.distance_to(runner.position) >= BALL_RADIUS_M + PLAYER_RADIUS_M - 1e-6


def test_full_short_match_runs_without_crashing() -> None:
    clubs = load_clubs(CLUBS_PATH, "Ligue 1")
    trace = simulate_match(clubs[0], clubs[1], duration_minutes=2.0, tick_seconds=0.2, record_every=5)

    assert len(trace.ticks) > 0
    first_tick = trace.ticks[0]
    assert len(first_tick.players) == 22
    for snapshot in first_tick.players:
        assert 0.0 <= snapshot.position.x <= PITCH_LENGTH_M
        assert 0.0 <= snapshot.position.y <= PITCH_WIDTH_M
    assert 0.0 <= first_tick.ball.position.x <= PITCH_LENGTH_M

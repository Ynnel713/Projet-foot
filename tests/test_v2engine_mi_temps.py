"""Mi-temps dans le moteur V2 (ticket v2-coach-et-gestion-de-match/07) : arrêt à la moitié du match, replacement de
chacun à sa place de départ, engagement par l'équipe qui n'a pas engagé la 1re période, tirée au sort."""

from __future__ import annotations

import random

from ligue1sim.clubs import load_clubs
from ligue1sim.lineup import pick_best_formation
from ligue1sim.season import CLUBS_PATH
from v2engine.formation import initial_positions
from v2engine.geometry import PITCH_LENGTH_M, PITCH_WIDTH_M, Vec2
from v2engine.match import simulate_match
from v2engine.restart import KICKOFF


def _clubs():
    clubs = load_clubs(CLUBS_PATH, "Ligue 1")
    return clubs[4], clubs[5]


def test_half_time_resets_everyone_and_the_other_team_kicks_off() -> None:
    home, away = _clubs()
    # graine sans coup de pied arrêté en attente à la pause (sinon la période se prolonge, ticket coach/03) ; changée
    # au ticket v2-realisme/01a, dont les flux aléatoires modifient les tirages (20260925 donnait un corner à 0,72)
    random.seed(20260927)
    trace = simulate_match(home, away, duration_minutes=2.0, record_every=1)
    assert trace.second_half_start_minute == 1.0

    kickoffs = [r for r in trace.restarts if r.kind == KICKOFF]
    first, second = kickoffs[0], next(r for r in kickoffs if r.minute == 1.0)
    assert first.minute == 0.0 and first.team != second.team

    # première image de la 2e période (un pas de 0,1 s après le replacement) : chacun à sa place de départ
    start = {**initial_positions(pick_best_formation(home), attacking_right=True),
             **initial_positions(pick_best_formation(away), attacking_right=False)}
    center = Vec2(PITCH_LENGTH_M / 2, PITCH_WIDTH_M / 2)
    tick = next(t for t in trace.ticks if t.minute >= 1.0)
    moved = [p.name for p in tick.players if p.position.distance_to(start[p.name]) >= 1.0]
    assert len(moved) == 1  # seul l'engageur, posé sur le point central
    assert next(p for p in tick.players if p.name == moved[0]).position.distance_to(center) < 1.0
    assert tick.ball.position.distance_to(center) < 5.0


def test_half_time_is_deterministic_for_a_given_seed() -> None:
    home, away = _clubs()
    runs = []
    for _ in range(2):
        random.seed(20260925)
        trace = simulate_match(home, away, duration_minutes=2.0)
        runs.append((trace.second_half_start_minute,
                     [(p.name, round(p.position.x, 6), round(p.position.y, 6)) for t in trace.ticks for p in t.players]))
    assert runs[0] == runs[1]


def test_first_kickoff_is_drawn_by_lot() -> None:
    home, away = _clubs()
    teams = set()
    for seed in range(10):
        random.seed(seed)
        trace = simulate_match(home, away, duration_minutes=0.05)
        teams.add(next(r.team for r in trace.restarts if r.kind == KICKOFF))
    assert teams == {"home", "away"}

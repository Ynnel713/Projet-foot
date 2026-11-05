"""Temps additionnel (ticket v2-coach-et-gestion-de-match/03) : annonce par période croissante avec les arrêts de jeu,
tirage reproductible, minute affichée 45+N' / 90+N', fin de période retardée par un coup de pied arrêté accordé."""

from __future__ import annotations

import random
from types import SimpleNamespace

from ligue1sim.clubs import load_clubs
from ligue1sim.season import CLUBS_PATH
from v2engine.added_time import GRACE_S, added_minutes, display_minute, played_minute
from v2engine.ball_state import BallState
from v2engine.geometry import Vec2
from v2engine.match import LateSetPiece, simulate_match
from v2engine.restart import CORNER, PENALTY, THROW_IN, Restart

_KEY = "Club A|Club B"


def test_added_time_grows_with_goals_and_penalties() -> None:
    for period in (1, 2):
        by_goals = [added_minutes(period, 45.0, g, 0, _KEY) for g in range(6)]
        assert by_goals[5] - by_goals[0] >= 4  # environ une minute par but
        assert added_minutes(period, 45.0, 0, 2, _KEY) >= by_goals[0] + 1


def test_second_half_has_more_added_time_than_the_first_on_average() -> None:
    first = [added_minutes(1, 45.0, 1, 0, f"{k}") for k in range(200)]
    second = [added_minutes(2, 45.0, 1, 0, f"{k}") for k in range(200)]
    assert 2.0 <= sum(first) / 200 <= 4.0
    assert 4.0 <= sum(second) / 200 <= 7.0


def test_added_time_draw_is_reproducible_and_scaled_to_short_matches() -> None:
    assert added_minutes(2, 45.0, 2, 1, _KEY) == added_minutes(2, 45.0, 2, 1, _KEY)
    assert added_minutes(2, 1.0, 0, 0, _KEY) == 0  # match de test d'une minute par période : pas 4 min d'arrêts


def test_background_varies_between_replays_of_the_same_fixture() -> None:
    # même affiche, mêmes buts : les fautes et remises de la période font varier le fond (réserve A1)
    values = {added_minutes(1, 45.0, 0, 0, _KEY, fouls=f, restarts=40 + f) for f in range(10)}
    assert len(values) >= 2


def test_display_minute() -> None:
    assert display_minute(12.4, None) == "12'"
    assert display_minute(45.3, None) == "45+1'"
    assert display_minute(48.9, 49.0) == "45+4'"
    assert display_minute(60.0, 49.0) == "56'"
    assert display_minute(94.0, 49.0) == "90+1'"
    assert display_minute(100.5, 49.0) == "90+7'"


def _ball(restart=None, holder=None) -> BallState:
    ball = BallState(position=Vec2(50.0, 30.0), velocity=Vec2(0.0, 0.0))
    ball.restart, ball.holder = restart, holder
    return ball


_PLAYERS = [SimpleNamespace(name="h1", team="home"), SimpleNamespace(name="a1", team="away")]


def _restart(kind: str) -> Restart:
    return Restart(kind, "home", Vec2(105.0, 0.0), "h1", 10.0, 0.0)


def test_period_waits_for_an_awarded_set_piece_then_lets_the_action_finish() -> None:
    late = LateSetPiece()
    assert not late.whistle(_ball(_restart(CORNER)), _PLAYERS, 0.0)  # corner accordé : on attend qu'il soit tiré
    assert not late.whistle(_ball(holder="h1"), _PLAYERS, 30.0)  # tiré, l'équipe qui l'a obtenu garde le ballon
    assert late.whistle(_ball(holder="h1"), _PLAYERS, 30.0 + GRACE_S)  # action à son terme, 30 s au plus
    late = LateSetPiece()
    late.whistle(_ball(_restart(PENALTY)), _PLAYERS, 0.0)
    assert late.whistle(_ball(holder="a1"), _PLAYERS, 61.0)  # l'adversaire récupère : fin
    late = LateSetPiece()
    late.whistle(_ball(_restart(CORNER)), _PLAYERS, 0.0)
    assert late.whistle(_ball(_restart(THROW_IN)), _PLAYERS, 35.0)  # ballon mort ordinaire : fin


def test_no_set_piece_pending_ends_at_once_and_hard_stop_wins() -> None:
    assert LateSetPiece().whistle(_ball(_restart(THROW_IN)), _PLAYERS, 0.0)  # une touche n'est pas rattrapée
    assert LateSetPiece(hard_stop_s=100.0).whistle(_ball(_restart(CORNER)), _PLAYERS, 100.0)


def test_match_announces_added_time_for_each_period_reproducibly() -> None:
    clubs = load_clubs(CLUBS_PATH, "Ligue 1")
    runs = []
    for _ in range(2):
        random.seed(20261104)
        trace = simulate_match(clubs[4], clubs[5], duration_minutes=2.0)
        runs.append((trace.added_minutes, trace.second_half_start_minute, trace.ticks[-1].minute,
                     [(p.name, round(p.position.x, 6)) for t in trace.ticks for p in t.players]))
    assert runs[0] == runs[1]
    added, half, _end, _ = runs[0]
    assert len(added) == 2
    assert half >= 1.0 + added[0]



def test_fatigue_follows_played_time_not_the_engine_clock() -> None:
    # réserve A1 (passage 2) : en 2e période, la fatigue ne compte pas le temps additionnel de la 1re ; à la 80e
    # affichée, même temps de jeu quel que soit ce temps additionnel
    assert played_minute(30.0, None, 45.0) == 30.0
    assert played_minute(47.0, None, 45.0) == 47.0  # temps additionnel de la 1re : on joue, on fatigue
    for start in (45.0, 48.0, 52.0):
        assert played_minute(start + 35.0, start, 45.0) == 80.0

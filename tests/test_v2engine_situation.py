"""Tests de la situation de jeu V2 (ticket v2-collectif/03) : reconnaissance par équipe et délai de perception par
joueur (Anticipation)."""

from __future__ import annotations

import math
import random

from v2engine.anticipation import reaction_delay_s
from v2engine.ball_state import BallState
from v2engine.geometry import Vec2
from v2engine.movement import PlayerState
from v2engine.situation import (
    DEFENSE_PLACEE, DERNIER_TIERS, POSSESSION_INSTALLEE, TRANSITION_DEFENSIVE, TRANSITION_OFFENSIVE,
    TRANSITION_WINDOW_S, SituationTracker,
)


def _p(name: str, team: str, x: float = 50.0, anticipation: int = 55) -> PlayerState:
    return PlayerState(name=name, team=team, poste="MC", position=Vec2(x, 34.0), velocity=Vec2(0.0, 0.0), pace=60,
                       acceleration=60, stamina=60, home_target=Vec2(x, 34.0), attributes={"Anticipation": anticipation})


HOME, AWAY = _p("H", "home"), _p("A", "away")
PLAYERS = [HOME, AWAY]


def _ball(holder: str | None, x: float = 50.0) -> BallState:
    return BallState(position=Vec2(x, 34.0), velocity=Vec2(0.0, 0.0), holder=holder)


def test_reaction_delay_follows_anticipation_validated_points() -> None:
    for note, expected in ((99, 0.4), (55, 0.7), (11, 1.0)):
        assert math.isclose(reaction_delay_s(_p("X", "home", anticipation=note)), expected)


def test_a_turnover_starts_both_transitions_then_they_settle() -> None:
    t = SituationTracker()
    assert t.update(0.0, _ball("H"), PLAYERS) == {"home": POSSESSION_INSTALLEE, "away": DEFENSE_PLACEE}  # 1re touche
    assert t.update(10.0, _ball("A"), PLAYERS) == {"home": TRANSITION_DEFENSIVE, "away": TRANSITION_OFFENSIVE}
    assert t.update(10.0 + TRANSITION_WINDOW_S, _ball("A"), PLAYERS) == {"home": DEFENSE_PLACEE, "away": POSSESSION_INSTALLEE}


def test_a_pass_in_flight_keeps_the_possession() -> None:
    t = SituationTracker()
    t.update(0.0, _ball("H"), PLAYERS)
    assert t.update(1.0, _ball(None), PLAYERS)["home"] == POSSESSION_INSTALLEE


def test_regaining_the_ball_ends_the_transition_early() -> None:
    t = SituationTracker()
    t.update(0.0, _ball("H"), PLAYERS)
    t.update(10.0, _ball("A"), PLAYERS)  # home perd
    assert t.update(12.0, _ball("H"), PLAYERS) == {"home": TRANSITION_OFFENSIVE, "away": TRANSITION_DEFENSIVE}


def test_final_third_overrides_the_offensive_transition() -> None:
    t = SituationTracker()
    t.update(0.0, _ball("A"), PLAYERS)
    assert t.update(1.0, _ball("H", x=80.0), PLAYERS)["home"] == DERNIER_TIERS  # récupération haute, à 80 m de son but
    assert t.update(2.0, _ball("A", x=80.0), PLAYERS)["away"] == TRANSITION_OFFENSIVE  # à 25 m de son but pour away


def test_kick_off_after_a_goal_is_not_a_transition() -> None:
    t = SituationTracker()
    t.update(0.0, _ball("H"), PLAYERS)
    assert t.update(5.0, _ball(None, x=52.5), PLAYERS, scored="home") == {"home": DEFENSE_PLACEE, "away": POSSESSION_INSTALLEE}


def test_each_player_perceives_the_change_after_his_reaction_delay() -> None:
    t = SituationTracker()
    t.update(0.0, _ball("H"), PLAYERS)
    t.update(10.0, _ball("A"), PLAYERS)  # perte de home
    sharp, average, slow = (_p(n, "home", anticipation=a) for n, a in (("S", 99), ("M", 55), ("L", 11)))
    assert t.perceived(sharp, 10.3) == POSSESSION_INSTALLEE and t.perceived(sharp, 10.41) == TRANSITION_DEFENSIVE
    assert t.perceived(average, 10.6) == POSSESSION_INSTALLEE and t.perceived(average, 10.71) == TRANSITION_DEFENSIVE
    assert t.perceived(slow, 10.9) == POSSESSION_INSTALLEE and t.perceived(slow, 11.01) == TRANSITION_DEFENSIVE


def test_situations_and_reaction_delays_are_in_the_trace_and_the_api() -> None:
    from api.routers.v2 import intention_segments
    from ligue1sim.clubs import load_clubs
    from ligue1sim.season import CLUBS_PATH
    from v2engine.match import simulate_match
    clubs = load_clubs(CLUBS_PATH, "Ligue 1")
    random.seed(20260923)
    trace = simulate_match(clubs[0], clubs[1], duration_minutes=2.0)
    assert {s.team for s in trace.situations if s.minute == 0.0} == {"home", "away"}
    assert any(s.situation in (TRANSITION_DEFENSIVE, TRANSITION_OFFENSIVE) for s in trace.situations)
    assert all(p.intention.situation for tick in trace.ticks for p in tick.players)
    assert all(0.4 <= d <= 1.0 for d in trace.reaction_delays_s.values()) and len(trace.reaction_delays_s) == 22
    assert all(player.reaction_delay_s is not None for player in intention_segments(trace))


def test_the_scoring_team_retaking_the_ball_after_kick_off_is_not_a_transition() -> None:
    t = SituationTracker()
    t.update(0.0, _ball("H"), PLAYERS)
    t.update(5.0, _ball(None, x=52.5), PLAYERS, scored="home")
    assert t.update(6.0, _ball("H", x=52.5), PLAYERS) == {"home": POSSESSION_INSTALLEE, "away": DEFENSE_PLACEE}
    assert t.update(9.0, _ball("A"), PLAYERS)["away"] == TRANSITION_OFFENSIVE  # le jeu reprend : vraie récupération


def test_final_third_for_the_away_team_is_near_x_zero() -> None:
    t = SituationTracker()
    t.update(0.0, _ball("A", x=30.0), PLAYERS)  # away attaque vers x = 0 : à 75 m de son but
    assert t.update(0.1, _ball("A", x=30.0), PLAYERS)["away"] == DERNIER_TIERS
    assert t.update(0.2, _ball("A", x=40.0), PLAYERS)["away"] == POSSESSION_INSTALLEE  # à 65 m : pas encore


def test_trace_records_only_changes() -> None:
    from ligue1sim.clubs import load_clubs
    from ligue1sim.season import CLUBS_PATH
    from v2engine.match import simulate_match
    clubs = load_clubs(CLUBS_PATH, "Ligue 1")
    random.seed(20260924)
    trace = simulate_match(clubs[2], clubs[3], duration_minutes=2.0)
    for team in ("home", "away"):
        seq = [s.situation for s in trace.situations if s.team == team]
        assert all(a != b for a, b in zip(seq, seq[1:]))

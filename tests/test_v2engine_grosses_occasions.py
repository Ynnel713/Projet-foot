"""Danger de la situation et grosses occasions (ticket v2-collectif/28c) : scènes contrôlées, trace des séquences sans
tir, calcul en lecture seule (le jeu ne change pas)."""

from __future__ import annotations

import hashlib
import random

from v2engine import match, occasion
from v2engine.ball_state import BallState
from v2engine.geometry import Vec2
from v2engine.movement import PlayerState
from v2engine.occasion import BIG_CHANCE_DANGER, ChanceTracker, reach_probability, situation_danger
from v2engine.possession import BALL_FRICTION_PER_S
from v2engine.trace import ShotEvent

DT = 0.1


def _p(name: str, x: float, y: float = 34.0, team: str = "home", poste: str = "BU") -> PlayerState:
    return PlayerState(name=name, team=team, poste=poste, position=Vec2(x, y), velocity=Vec2(0.0, 0.0), pace=60,
                       acceleration=60, stamina=60, home_target=Vec2(x, y))


def _origin(_player: PlayerState) -> str:
    return "test"


def test_touch_reach_is_the_engine_control_radius() -> None:
    assert occasion.TOUCH_M == round(match.CONTROL_RADIUS_M, 2)


def test_a_cross_that_beats_everyone_past_an_attacker_at_the_empty_goal_is_a_big_chance_without_a_shot() -> None:
    # centre fort le long de la ligne de but, gardien sorti et battu ; l'attaquant reste à deux mètres de la trajectoire
    # (scène figée : il ne bouge pas), le ballon traverse et file, personne ne le reprend
    attacker, keeper = _p("A", 101.5, 36.0), _p("K", 97.0, 20.0, "away", "GK")
    defender, crosser = _p("D", 95.0, 40.0, "away", "DC"), _p("C", 100.0, 8.0)
    players = [attacker, keeper, defender, crosser]
    ball = BallState(position=Vec2(103.5, 14.0), velocity=Vec2(0.0, 22.0), last_toucher="C", last_pass_team="home")
    assert situation_danger("home", ball, players)[0] >= BIG_CHANCE_DANGER
    chances: list = []
    tracker = ChanceTracker(chances)
    for i in range(60):
        tracker.update(i * DT / 60.0, ball, players, [], _origin)
        ball.position = ball.position + ball.velocity * DT
        ball.velocity = ball.velocity * BALL_FRICTION_PER_S ** DT
    tracker.close_all(1.0)
    assert len(chances) == 1
    chance = chances[0]
    assert not chance.shot and chance.player == "A" and chance.danger >= BIG_CHANCE_DANGER
    assert chance.outcome == "ballon non repris" and chance.start <= chance.peak_minute < chance.end
    assert chance.x > 102.0  # pic lu au point de contact, sur la trajectoire, pas là où il se tient


def test_a_one_on_one_stopped_by_a_last_ditch_tackle_is_a_big_chance_without_a_shot() -> None:
    attacker, keeper = _p("A", 98.0), _p("K", 104.5, 34.0, "away", "GK")
    chaser = _p("D", 96.5, 34.5, "away", "DC")
    players = [attacker, keeper, chaser]
    ball = BallState(position=attacker.position, velocity=Vec2(0.0, 0.0), holder="A")
    chances: list = []
    tracker = ChanceTracker(chances)
    tracker.update(10.0, ball, players, [], _origin)
    ball.holder = "D"  # tacle gagné
    tracker.update(10.002, ball, players, [], _origin)
    assert [(c.outcome, c.shot, c.player) for c in chances] == [("tacle", False, "A")]
    assert chances[0].danger >= BIG_CHANCE_DANGER


def test_a_harmless_long_shot_is_not_a_big_chance() -> None:
    shooter, keeper, blocker = _p("A", 80.0), _p("K", 104.0, 34.0, "away", "GK"), _p("D", 90.0, 34.0, "away", "DC")
    players = [shooter, keeper, blocker]
    ball = BallState(position=shooter.position, velocity=Vec2(0.0, 0.0), holder="A")
    assert situation_danger("home", ball, players)[0] < BIG_CHANCE_DANGER / 2.0
    chances: list = []
    tracker = ChanceTracker(chances)
    tracker.update(10.0, ball, players, [], _origin)
    ball.holder = "K"
    shot = ShotEvent(10.002, "home", "A", 80.0, 34.0, 0.03, "capté", "passe au sol")
    tracker.update(10.002, ball, players, [shot], _origin)
    tracker.close_all(11.0)
    assert chances == []


def test_a_big_shot_closes_its_sequence_with_the_shot_outcome() -> None:
    attacker, keeper = _p("A", 99.0), _p("K", 104.0, 34.0, "away", "GK")
    players = [attacker, keeper]
    ball = BallState(position=attacker.position, velocity=Vec2(0.0, 0.0), holder="A")
    chances: list = []
    tracker = ChanceTracker(chances)
    tracker.update(10.0, ball, players, [], _origin)
    ball.holder, ball.shot_for = None, "home"
    tracker.update(10.002, ball, players, [ShotEvent(10.002, "home", "A", 99.0, 34.0, 0.37, "but", "dribble")], _origin)
    assert [(c.outcome, c.shot) for c in chances] == [("tir : but", True)]


def test_a_late_attacker_keeps_a_fading_chance_to_reach_a_free_ball() -> None:
    ball = BallState(position=Vec2(95.0, 34.0), velocity=Vec2(0.0, 0.0))
    defender = _p("D", 90.0, 34.0, "away", "DC")
    first = reach_probability(_p("A", 98.0, 34.0), ball, [defender])[0]
    late = reach_probability(_p("A", 101.0, 34.0), ball, [defender])[0]
    very_late = reach_probability(_p("A", 104.0, 34.0), ball, [defender])[0]
    assert first == 1.0 > late > very_late > 0.0


def test_only_an_attacker_who_read_the_opponent_pass_can_cut_it() -> None:
    # relance adverse dans sa surface : l'attaquant au contact de la trajectoire ne la dispute que s'il l'a lue
    attacker, keeper = _p("A", 100.0, 30.0), _p("K", 104.0, 34.0, "away", "GK")
    passer, receiver = _p("P", 101.0, 26.0, "away", "DC"), _p("R", 101.0, 42.0, "away", "DC")
    players = [attacker, keeper, passer, receiver]
    ball = BallState(position=Vec2(101.0, 27.0), velocity=Vec2(0.0, 12.0), last_toucher="P", last_pass_team="away",
                     receiver="R")
    assert situation_danger("home", ball, players) == (0.0, None)
    ball.readers = {"A": Vec2(101.0, 30.0)}
    assert situation_danger("home", ball, players)[0] >= BIG_CHANCE_DANGER


def test_danger_is_zero_for_the_defending_team_and_on_a_dead_ball() -> None:
    attacker, keeper = _p("A", 99.0), _p("K", 104.0, 34.0, "away", "GK")
    ball = BallState(position=attacker.position, velocity=Vec2(0.0, 0.0), holder="A")
    assert situation_danger("away", ball, [attacker, keeper]) == (0.0, None)
    ball.shot_for = "home"
    assert situation_danger("home", ball, [attacker, keeper]) == (0.0, None)


def _fingerprint(trace) -> str:
    h = hashlib.sha256()
    for name in ("ticks", "goals", "decisions", "offsides", "restarts", "fouls", "shots"):
        h.update(repr(getattr(trace, name)).encode())
    return h.hexdigest()


def test_the_danger_computation_does_not_change_the_game_and_is_reproducible(monkeypatch) -> None:
    from ligue1sim.clubs import load_clubs
    from ligue1sim.season import CLUBS_PATH

    clubs = load_clubs(CLUBS_PATH, "Ligue 1")

    def play():
        random.seed(20260923)
        return match.simulate_match(clubs[0], clubs[1], duration_minutes=10)

    first, second = play(), play()
    assert first.chances == second.chances
    monkeypatch.setattr(ChanceTracker, "update", lambda *a, **k: None)
    assert _fingerprint(play()) == _fingerprint(first)

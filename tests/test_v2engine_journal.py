"""Journal des événements et chaîne de causes (ticket v2-realisme/19b) : chaque événement a un identifiant et pour cause
le dernier événement du ballon ; seul l'engagement ouvre une chaîne. Le journal ne change rien au jeu."""

from __future__ import annotations

from api.routers.v2 import _events_out, _goals_out
from v2engine import match
from v2engine.ball_state import BallState
from v2engine.decision import Action
from v2engine.geometry import PITCH_LENGTH_M, Vec2
from v2engine.match import GOAL_CENTER_Y, _step_ball
from v2engine.movement import PlayerState
from v2engine.trace import EventLog, GoalEvent, MatchTrace, chain


def _player(name: str, team: str, poste: str, x: float, y: float) -> PlayerState:
    return PlayerState(name=name, team=team, poste=poste, position=Vec2(x, y), velocity=Vec2(0.0, 0.0), pace=60,
                       acceleration=60, stamina=60, home_target=Vec2(x, y), attributes=None)


def test_a_chain_opens_at_the_kickoff_and_links_each_event_to_the_previous_one() -> None:
    log = EventLog([])
    kickoff = log.add(0.0, "remise", "home", "A", "engagement", start=True)
    a_pass = log.add(0.1, "passe", "home", "A", other="B")
    shot = log.add(0.2, "tir", "home", "B")
    restart = log.add(0.3, "remise", "away", "C", "engagement", start=True)
    assert kickoff.cause is None and a_pass.cause == kickoff.id and shot.cause == a_pass.id and restart.cause is None
    assert [e.id for e in chain(log.events, shot.id)] == [kickoff.id, a_pass.id, shot.id]


def test_reference_scene_back_pass_missed_control_loss_shot_goal(monkeypatch) -> None:
    # Passe en retrait de l'arrière vers son gardien, contrôle raté du gardien, ballon pris par l'attaquant, tir, but :
    # la chaîne remontée depuis le but contient ces cinq maillons dans l'ordre.
    back = _player("Arriere", "away", "DC", PITCH_LENGTH_M - 15.0, GOAL_CENTER_Y)
    keeper = _player("Gardien", "away", "GK", PITCH_LENGTH_M - 2.0, GOAL_CENTER_Y)
    striker = _player("Buteur", "home", "BU", PITCH_LENGTH_M - 6.0, GOAL_CENTER_Y + 12.0)
    players = [back, keeper, striker]
    monkeypatch.setattr(match, "should_attempt_tackle", lambda aggression, dt: False)
    monkeypatch.setattr(match, "choose_action", lambda holder, *args: Action("pass", 1.0, target=keeper)
                        if holder.name == "Arriere" else Action("shot", 1.0))
    monkeypatch.setattr(match, "attempt_control", lambda player, *args: player.name == "Buteur")
    monkeypatch.setattr(match, "draw_shot_error", lambda *args: (0.0, 0.0))
    monkeypatch.setattr(match, "keeper_reach_m", lambda elapsed: 0.0)  # le gardien battu ne touche pas le tir
    ball = BallState(position=back.position, velocity=Vec2(0.0, 0.0), holder="Arriere")
    ball.log = EventLog([])
    scored = None
    for tick in range(300):
        if ball.holder is None and ball.log.last_event() is not None and ball.log.last_event().kind == "contrôle raté":
            striker.position = ball.position  # il a suivi l'action : il est sur le ballon échappé
        scored = _step_ball(ball, 0.1, players, tick * 0.1)
        if scored is not None:
            break
    assert scored == "home"
    goal = ball.log.events[-1]
    links = chain(ball.log.events, goal.id)
    assert [(e.kind, e.player) for e in links] == [("passe", "Arriere"), ("contrôle raté", "Gardien"),
                                                  ("perte", "Gardien"), ("tir", "Buteur"), ("but", "Buteur")]
    assert links[2].detail == "contrôle" and links[2].other == "Buteur" and links[0].other == "Gardien"
    assert ball.last_toucher == "Buteur"


def test_a_blocked_shot_is_traced_with_the_blocker_and_no_goal(monkeypatch) -> None:
    shooter = _player("Buteur", "home", "BU", PITCH_LENGTH_M - 20.0, GOAL_CENTER_Y)
    keeper = _player("Gardien", "away", "GK", PITCH_LENGTH_M - 1.0, GOAL_CENTER_Y)
    defender = _player("Defenseur", "away", "DC", PITCH_LENGTH_M - 12.0, GOAL_CENTER_Y + 0.6)
    monkeypatch.setattr(match, "should_attempt_tackle", lambda aggression, dt: False)
    monkeypatch.setattr(match, "choose_action", lambda *args: Action("shot", 1.0))
    monkeypatch.setattr(match, "draw_shot_error", lambda *args: (0.0, 0.0))
    monkeypatch.setattr(match, "BLOCK_CHANCE", 1.0)
    ball = BallState(position=shooter.position, velocity=Vec2(0.0, 0.0), holder="Buteur")
    ball.log = EventLog([])
    for tick in range(15):
        assert _step_ball(ball, 0.1, [shooter, keeper, defender], tick * 0.1) is None
        if any(e.kind == "contre" for e in ball.log.events):
            break
    shot, block = ball.log.events[:2]
    assert (shot.kind, shot.player, block.kind, block.player, block.team) == ("tir", "Buteur", "contre", "Defenseur", "away")
    assert block.cause == shot.id and not any(e.kind == "but" for e in ball.log.events)


def test_no_log_no_event_and_no_change(monkeypatch) -> None:
    # Hors match tracé (scènes de test, bancs), le ballon n'a pas de journal : rien n'est écrit.
    shooter = _player("Buteur", "home", "BU", PITCH_LENGTH_M - 20.0, GOAL_CENTER_Y)
    monkeypatch.setattr(match, "should_attempt_tackle", lambda aggression, dt: False)
    monkeypatch.setattr(match, "choose_action", lambda *args: Action("shot", 1.0))
    ball = BallState(position=shooter.position, velocity=Vec2(0.0, 0.0), holder="Buteur")
    _step_ball(ball, 0.1, [shooter], 0.0)
    assert ball.log is None


def test_each_goal_has_its_scorer_and_the_own_goal_flag() -> None:
    trace = MatchTrace(home="A", away="B", tick_seconds=1.0)
    trace.record_goal("home", 12.5, "Buteur")
    trace.record_goal("away", 80.0, "Defenseur", own_goal=True)
    assert trace.goals == [GoalEvent(12.5, "home", "Buteur", "Buteur", False),
                           GoalEvent(80.0, "away", "Defenseur", "Defenseur", True)]
    out = _goals_out(trace)
    assert (out[1].scorer, out[1].last_toucher, out[1].own_goal) == ("Defenseur", "Defenseur", True)


def test_the_api_serializes_the_log() -> None:
    trace = MatchTrace(home="A", away="B", tick_seconds=1.0)
    log = EventLog(trace.events)
    log.add(0.0, "remise", "home", "A", "engagement", "B", start=True)
    log.add(0.1, "passe", "home", "B", other="C")
    out = _events_out(trace)
    assert [(e.id, e.kind, e.cause, e.detail, e.other) for e in out] == [(0, "remise", None, "engagement", "B"),
                                                                       (1, "passe", 0, None, "C")]


def test_the_log_covers_both_halves_and_every_goal() -> None:
    # Match court à graine fixée : le journal continue après la mi-temps (le ballon y est recréé) et chaque but tracé a
    # son événement « but », son buteur et une chaîne qui remonte à un engagement.
    import random

    from ligue1sim.clubs import load_clubs
    from ligue1sim.season import CLUBS_PATH

    clubs = load_clubs(CLUBS_PATH, "Ligue 1")
    random.seed(20260923 + 4)  # 13 buts sur 90 minutes à cette graine (banc du 19b)
    trace = match.simulate_match(clubs[8], clubs[9], duration_minutes=20.0)
    assert trace.second_half_start_minute is not None
    assert any(e.minute >= trace.second_half_start_minute for e in trace.events)
    kickoffs = [e for e in trace.events if e.kind == "remise" and e.detail == "engagement"]
    assert any(e.minute >= trace.second_half_start_minute for e in kickoffs)
    goals = [e for e in trace.events if e.kind == "but"]
    assert len(goals) == len(trace.goals) and all(g.scorer for g in trace.goals)
    assert all(chain(trace.events, e.id)[0].detail == "engagement" for e in goals)

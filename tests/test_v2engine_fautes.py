"""Fautes sifflées, avantage et coups francs simples (ticket v2-collectif/30) : coup de sifflet ou avantage selon la
zone, retour à la faute si l'avantage tourne court, penalty provisoire dans la surface, coup franc frappé ou passé."""

from __future__ import annotations

import random

from v2engine import match
from v2engine.ball_state import BallState
from v2engine.decision import Action
from v2engine.duel import CARELESS, EXCESSIVE, RECKLESS, foul_severity
from v2engine.geometry import PITCH_LENGTH_M, PITCH_WIDTH_M, Vec2
from v2engine.match import ADVANTAGE_S, _step_ball
from v2engine.movement import PlayerState
from v2engine.restart import DEAD_S, FREE_KICK, PENALTY, foul_restart
from v2engine.trace import FoulEvent, RestartEvent

DT = 0.1


def _p(name: str, x: float, y: float, team: str = "home", poste: str = "MC") -> PlayerState:
    return PlayerState(name=name, team=team, poste=poste, position=Vec2(x, y), velocity=Vec2(0.0, 0.0), pace=60,
                       acceleration=60, stamina=60, home_target=Vec2(x, y))


class _Foul:
    won, foul = False, True


def _foul_once(monkeypatch) -> None:
    calls = iter([True])
    monkeypatch.setattr("v2engine.match.should_attempt_tackle", lambda aggression, dt: next(calls, False))
    monkeypatch.setattr("v2engine.match.resolve_tackle", lambda tackler, holder: _Foul())
    monkeypatch.setattr("v2engine.match.choose_action", lambda *a, **k: Action("dribble", 0.0, point=Vec2(60, 34)))
    monkeypatch.setattr("v2engine.match.dribble_lost", lambda *args, **kwargs: False)  # ticket 04a : pas de perte tirée ici


def _scene(x: float, y: float = 34.0) -> tuple[BallState, list[PlayerState]]:
    holder, fouler = _p("Porteur", x, y), _p("Fautif", x + 0.5, y, team="away")
    keeper = _p("GK", PITCH_LENGTH_M - 1.0, 34.0, team="away", poste="GK")
    return BallState(position=Vec2(x, y), velocity=Vec2(0, 0), holder="Porteur"), [holder, fouler, keeper]


def test_foul_in_own_half_is_whistled_at_once_for_a_free_kick_to_the_victim(monkeypatch) -> None:
    _foul_once(monkeypatch)
    ball, players = _scene(30.0)
    fouls: list[FoulEvent] = []
    _step_ball(ball, DT, players, 10.0, fouls=fouls)
    assert ball.restart is not None and ball.restart.kind == FREE_KICK and ball.restart.team == "home"
    assert ball.restart.spot == Vec2(30.0, 34.0) and ball.restart.until_s == 10.0 + DEAD_S[FREE_KICK]
    assert ball.holder is None
    assert [(f.player, f.victim, f.team, f.outcome) for f in fouls] == [("Fautif", "Porteur", "away", FREE_KICK)]


def test_advantage_is_played_when_the_victim_keeps_the_ball_in_a_dangerous_zone(monkeypatch) -> None:
    _foul_once(monkeypatch)
    ball, players = _scene(80.0)
    fouls: list[FoulEvent] = []
    for i in range(int(ADVANTAGE_S / DT) + 2):
        _step_ball(ball, DT, players, 10.0 + i * DT, fouls=fouls)
    assert ball.restart is None and ball.holder == "Porteur" and ball.advantage is None
    assert [f.outcome for f in fouls] == ["avantage"]


def test_advantage_is_called_back_when_the_victim_loses_the_ball(monkeypatch) -> None:
    _foul_once(monkeypatch)
    ball, players = _scene(80.0)
    fouls: list[FoulEvent] = []
    _step_ball(ball, DT, players, 10.0, fouls=fouls)
    assert ball.advantage is not None and not fouls
    ball.holder = "Fautif"  # ballon perdu dans la fenêtre
    _step_ball(ball, DT, players, 11.0, fouls=fouls)
    assert ball.restart is not None and ball.restart.team == "home" and ball.restart.spot == Vec2(80.0, 34.0)
    assert [f.outcome for f in fouls] == [FREE_KICK]


def test_foul_in_the_box_gives_a_penalty_on_the_spot() -> None:
    restart = foul_restart("home", Vec2(95.0, 40.0), [_p("H", 90, 34)], 0.0)
    assert restart.kind == PENALTY and restart.spot == Vec2(PITCH_LENGTH_M - 11.0, PITCH_WIDTH_M / 2.0)
    away = foul_restart("away", Vec2(8.0, 30.0), [_p("A", 20, 34, team="away")], 0.0)
    assert away.kind == PENALTY and away.spot == Vec2(11.0, PITCH_WIDTH_M / 2.0)


def test_keeper_takes_a_free_kick_in_his_own_box() -> None:
    players = [_p("GK", 2.0, 34.0, poste="GK"), _p("DC", 10.0, 34.0)]
    assert foul_restart("home", Vec2(10.0, 30.0), players, 0.0).taker == "GK"  # dans sa surface : pas un penalty
    assert foul_restart("home", Vec2(40.0, 30.0), players, 0.0).taker == "DC"


def _penalty(monkeypatch, conversion: float) -> BallState:
    monkeypatch.setattr(match, "PENALTY_CONVERSION", conversion)
    taker, keeper = _p("Tireur", 90.0, 30.0), _p("GK", 104.0, 34.0, team="away", poste="GK")
    players = [taker, keeper]
    ball = BallState(position=Vec2(94.0, 34.0), velocity=Vec2(0, 0))
    ball.restart = foul_restart("home", Vec2(95.0, 34.0), players, 0.0)
    _step_ball(ball, DT, players, DEAD_S[PENALTY])
    return ball


def test_penalty_scored_or_kept_by_the_keeper(monkeypatch) -> None:
    scored = _penalty(monkeypatch, 1.0)
    assert scored.shot_for == "home" and scored.velocity.x > 0
    missed = _penalty(monkeypatch, 0.0)
    assert missed.shot_for is None and missed.holder == "GK"


def test_free_kick_taker_shoots_or_passes_never_dribbles(monkeypatch) -> None:
    taker, mate = _p("Preneur", 40.0, 34.0), _p("Partenaire", 50.0, 20.0)
    opponent = _p("Adv", 60.0, 50.0, team="away")
    players = [taker, mate, opponent]
    ball = BallState(position=Vec2(40.0, 34.0), velocity=Vec2(0, 0))
    ball.restart = foul_restart("home", Vec2(40.0, 34.0), players, 0.0)
    events: list[RestartEvent] = []
    random.seed(30)
    _step_ball(ball, DT, players, DEAD_S[FREE_KICK], restarts=events)
    assert ball.holder == "Preneur" and not events  # il a le ballon, il décide au tick suivant
    _step_ball(ball, DT, players, DEAD_S[FREE_KICK] + DT, restarts=events)
    assert ball.holder is None and ball.receiver == "Partenaire"
    assert len(events) == 1 and events[0].kind == FREE_KICK and events[0].target == "Partenaire" and not events[0].shot


def test_severity_shares_follow_the_validated_constants() -> None:
    random.seed(30)
    draws = [foul_severity() for _ in range(20000)]
    assert abs(draws.count(RECKLESS) / 20000 - 0.12) < 0.01
    assert 0.002 < draws.count(EXCESSIVE) / 20000 < 0.009
    assert draws.count(CARELESS) > 0.85 * 20000


def _free_kick_decision(x: float) -> RestartEvent:
    attrs = {"Finishing": 90, "Long Shots": 90, "Composure": 90, "Decisions": 90, "Technique": 90}
    taker = _p("Preneur", x, 34.0)
    taker.attributes = attrs
    mate = _p("Partenaire", x - 8.0, 20.0)
    keeper = _p("GK", PITCH_LENGTH_M - 1.0, 34.0, team="away", poste="GK")
    wall = _p("Adv", x + 9.15, 40.0, team="away")
    players = [taker, mate, keeper, wall]
    ball = BallState(position=Vec2(x, 34.0), velocity=Vec2(0, 0))
    ball.restart = foul_restart("home", Vec2(x, 34.0), players, 0.0)
    events: list[RestartEvent] = []
    random.seed(30)
    for i in range(3):
        _step_ball(ball, DT, players, DEAD_S[FREE_KICK] + i * DT, restarts=events)
    return events[0]


def test_free_kick_is_shot_close_to_goal_and_passed_far_from_it() -> None:
    # même preneur, même décision qu'en jeu (ticket 33) : à 20 m face au but il frappe, à 60 m il joue court
    assert _free_kick_decision(PITCH_LENGTH_M - 20.0).shot
    assert not _free_kick_decision(PITCH_LENGTH_M - 60.0).shot


def test_choose_action_on_a_set_piece_never_dribbles() -> None:
    from v2engine.decision import choose_action

    taker, mate = _p("Preneur", 40.0, 34.0), _p("Partenaire", 50.0, 20.0)
    players = [taker, mate, _p("Adv", 60.0, 50.0, team="away")]
    goal = Vec2(PITCH_LENGTH_M, PITCH_WIDTH_M / 2.0)
    random.seed(30)
    kinds = {choose_action(taker, players, goal, None, set_piece=True).kind for _ in range(200)}
    assert "dribble" not in kinds and kinds
    assert "dribble" in {choose_action(taker, players, goal, None).kind for _ in range(200)}  # en jeu, il conduit


def test_a_shot_during_the_advantage_settles_it_even_when_saved(monkeypatch) -> None:
    # réserve A1 de l'expert : l'équipe fautée a tiré, l'avantage est réalisé ; un arrêt ne ramène pas à la faute
    _foul_once(monkeypatch)
    ball, players = _scene(80.0)
    fouls: list[FoulEvent] = []
    _step_ball(ball, DT, players, 10.0, fouls=fouls)
    assert ball.advantage is not None
    monkeypatch.setattr("v2engine.match.choose_action", lambda *a, **k: Action("shot", 0.1))
    monkeypatch.setattr("v2engine.match.draw_blocker", lambda *a, **k: None)
    monkeypatch.setattr("v2engine.match.attempt_shot", lambda *a, **k: False)
    monkeypatch.setattr("v2engine.match.classify_unscored", lambda *args: "cadré")  # cadré : le gardien capte
    monkeypatch.setattr("v2engine.match.save_outcome", lambda *args: "capté")  # capté, sans dépendre du tirage
    ball.next_decision_s = 0.0
    _step_ball(ball, DT, players, 10.5, fouls=fouls)
    assert ball.holder == "GK"
    _step_ball(ball, DT, players, 10.6, fouls=fouls)
    assert ball.restart is None and [f.outcome for f in fouls] == ["avantage"]

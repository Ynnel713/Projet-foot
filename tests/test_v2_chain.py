"""Lecture de la chaîne d'un but et origine des buts (ticket v2-realisme/19e), et faute avec avantage écrite au journal
au moment où l'avantage est accordé (réserve A1 de l'expert sur le 19b)."""

from __future__ import annotations

from scripts import v2_chain as vc
from v2engine import match
from v2engine.ball_state import BallState
from v2engine.geometry import PITCH_LENGTH_M, Vec2
from v2engine.match import GOAL_CENTER_Y
from v2engine.movement import PlayerState
from v2engine.trace import EventLog, MatchTrace, chain


def _goal(log: EventLog, minute: float, team: str = "home", player: str = "B"):
    return log.add(minute, "but", team, player)


def _kickoff(log: EventLog, team: str = "away", minute: float = 0.0):
    return log.add(minute, "remise", team, "K", "engagement", start=True)


def test_corner_header_goal_is_a_set_piece() -> None:
    log = EventLog([])
    _kickoff(log)
    log.add(1.0, "passe", "away", "K", other="L")
    log.add(1.1, "remise", "home", "C", "corner", "B")  # l'adversaire a sorti le ballon : corner
    log.add(1.15, "tir", "home", "B", "but")
    goal = _goal(log, 1.16)
    origin = vc.goal_origin(log.events, goal)
    assert (origin.family, origin.detail) == (vc.CPA, "corner")
    assert round(origin.delay_s, 1) == 3.6


def test_tackle_pass_goal_is_a_recovery() -> None:
    log = EventLog([])
    _kickoff(log)
    log.add(2.0, "passe", "away", "K", other="L")
    log.add(2.1, "perte", "away", "L", "tacle", "A")  # A tacle L : le ballon change d'équipe
    log.add(2.2, "passe", "home", "A", other="B")
    log.add(2.3, "tir", "home", "B", "but")
    goal = _goal(log, 2.31)
    assert (vc.goal_origin(log.events, goal).family, vc.goal_origin(log.events, goal).detail) == (vc.RECUPERATION, "tacle")


def test_missed_control_shot_goal_is_an_error_and_a_long_touch_too() -> None:
    log = EventLog([])
    _kickoff(log)
    log.add(3.0, "passe", "away", "K", other="G")
    log.add(3.05, "contrôle raté", "away", "G")
    log.add(3.06, "perte", "away", "G", "contrôle", "B")
    log.add(3.1, "tir", "home", "B", "but")
    goal = _goal(log, 3.11)
    assert vc.goal_origin(log.events, goal).detail == "contrôle raté"
    log2 = EventLog([])
    _kickoff(log2)
    log2.add(4.0, "touche longue", "away", "K")
    log2.add(4.01, "perte", "away", "K", "conduite", "B")  # perte qui suit une touche trop longue
    log2.add(4.1, "tir", "home", "B", "but")
    origin = vc.goal_origin(log2.events, _goal(log2, 4.11))
    assert (origin.family, origin.detail) == (vc.ERREUR, "touche trop longue")


def test_a_saved_shot_rebound_and_a_foul_with_advantage_keep_the_attack_going() -> None:
    log = EventLog([])
    _kickoff(log, "home")  # engagement de l'équipe qui marquera : jeu placé
    log.add(0.1, "passe", "home", "K", other="B")
    log.add(0.2, "faute", "away", "D", "avantage", "B")  # avantage : l'attaque continue
    log.add(0.3, "tir", "home", "B", "repoussé")
    log.add(0.31, "arrêt", "away", "G", "repoussé")  # rebond repris par B
    log.add(0.35, "tir", "home", "B", "but")
    origin = vc.goal_origin(log.events, _goal(log, 0.36))
    assert (origin.family, origin.detail) == (vc.JEU_PLACE, "engagement")


def test_offside_free_kick_and_the_time_window() -> None:
    log = EventLog([])
    _kickoff(log)
    log.add(5.0, "hors-jeu", "away", "L")  # coup franc indirect pour l'équipe qui marquera, sans remise tracée
    log.add(5.05, "passe", "home", "A", other="B")
    log.add(5.1, "tir", "home", "B", "but")
    assert vc.goal_origin(log.events, _goal(log, 5.11)).detail == "coup franc (hors-jeu)"
    log2 = EventLog([])
    _kickoff(log2)
    log2.add(6.0, "remise", "home", "T", "touche", "B")
    log2.add(6.5, "tir", "home", "B", "but")  # 30 s après la touche : elle n'en est plus l'origine
    origin = vc.goal_origin(log2.events, _goal(log2, 6.5))
    assert (origin.family, origin.detail) == (vc.JEU_PLACE, "après touche")
    log3 = EventLog([])
    _kickoff(log3)
    log3.add(7.0, "remise", "home", "T", "touche", "B")
    log3.add(7.1, "tir", "home", "B", "but")
    assert vc.goal_origin(log3.events, _goal(log3, 7.1)).family == vc.TOUCHE


def test_a_goal_without_an_event_giving_the_ball_is_explained() -> None:
    log = EventLog([])
    _kickoff(log)
    log.add(8.0, "passe", "away", "K", other="L")  # passe adverse, puis tir sans perte tracée
    log.add(8.1, "tir", "home", "B", "but")
    origin = vc.goal_origin(log.events, _goal(log, 8.11))
    assert origin.family == vc.INCLASSABLE and "passe" in origin.detail


def test_format_chain_marks_the_origin_and_shares_add_up() -> None:
    log = EventLog([])
    _kickoff(log)
    log.add(1.1, "remise", "home", "C", "corner", "B")
    goal = _goal(log, 1.15)
    text = vc.format_chain(log.events, goal)
    assert "<- origine" in text and text.splitlines()[-1].startswith("origine : coup de pied arrêté (corner")
    shares = vc.origin_shares([vc.goal_origin(log.events, goal)])
    assert shares["buts"] == 1 and shares["par famille"][vc.CPA] == 1.0 and sum(
        v for v in shares["par famille"].values() if v) == 1.0


def _player(name: str, team: str, x: float, y: float) -> PlayerState:
    return PlayerState(name=name, team=team, poste="MC", position=Vec2(x, y), velocity=Vec2(0.0, 0.0), pace=60,
                       acceleration=60, stamina=60, home_target=Vec2(x, y), attributes=None)


def test_a_foul_with_advantage_is_logged_when_granted_and_not_when_settled() -> None:
    """Réserve A1 de l'expert (19b) : la faute laissée en avantage est écrite à sa minute, quand l'avantage est accordé ;
    son règlement n'écrit rien. Les minutes du journal restent croissantes."""
    victim = _player("Victime", "home", PITCH_LENGTH_M - 18.0, GOAL_CENTER_Y)  # près du but adverse : avantage
    fouler = _player("Fautif", "away", PITCH_LENGTH_M - 17.0, GOAL_CENTER_Y)
    ball = BallState(position=victim.position, velocity=Vec2(0.0, 0.0), holder="Victime")
    ball.log = EventLog([])
    ball.log.add(10.0, "passe", "home", "X", other="Victime")
    fouls: list = []
    match._foul(ball, fouler, victim, [victim, fouler], 610.0, fouls)
    assert ball.advantage is not None
    last = ball.log.events[-1]
    assert (last.kind, last.detail, last.player, last.other, last.minute) == ("faute", "avantage", "Fautif", "Victime",
                                                                              610.0 / 60.0)
    match._settle_advantage(ball, fouls)
    assert len(ball.log.events) == 2 and len(fouls) == 1  # rien de plus au journal ; la faute reste comptée


def test_a_foul_whistled_back_after_advantage_is_logged_at_the_whistle() -> None:
    victim = _player("Victime", "home", PITCH_LENGTH_M - 18.0, GOAL_CENTER_Y)
    fouler = _player("Fautif", "away", PITCH_LENGTH_M - 17.0, GOAL_CENTER_Y)
    ball = BallState(position=victim.position, velocity=Vec2(0.0, 0.0), holder="Victime")
    ball.log = EventLog([])
    match._foul(ball, fouler, victim, [victim, fouler], 610.0, [])
    ball.holder = "Fautif"  # l'équipe fautée a perdu le ballon : l'arbitre revient à la faute
    assert match._check_advantage(ball, [victim, fouler], 611.0, [])
    granted, whistled = ball.log.events
    assert granted.detail == "avantage" and whistled.kind == "faute" and whistled.minute == 611.0 / 60.0
    assert whistled.detail.endswith("après avantage") and whistled.cause == granted.id


def test_v2_chain_reads_a_trace() -> None:
    trace = MatchTrace(home="A", away="B", tick_seconds=1.0)
    log = EventLog(trace.events)
    _kickoff(log, "home")
    goal = _goal(log, 0.5)
    assert vc.goals(trace.events) == [goal] and chain(trace.events, goal.id)[0].kind == "remise"

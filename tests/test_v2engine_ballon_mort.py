"""Ballon mort et remises en jeu (ticket v2-collectif/29) : sortie de balle, remise à l'adversaire du dernier toucheur,
temps mort, engagement après un but, ballon aérien, choix court ou long selon la situation."""

from __future__ import annotations

import random

from v2engine.anticipation import loose_ball_target, meeting_point
from v2engine.ball_state import BallState
from v2engine.cerveau import think
from v2engine.geometry import PITCH_LENGTH_M, PITCH_WIDTH_M, Vec2
from v2engine.match import _step_ball
from v2engine.movement import PlayerState
from v2engine.possession import BALL_FRICTION_PER_S
from v2engine.restart import (AERIEN, CORNER, DEAD_S, GOAL_KICK, KICKOFF, LONG_RESTART_M, RESTART_DISTANCE_M,
                              THROW_IN, Restart, award, exit_point, kickoff, place, restart_target)
from v2engine.trace import RestartEvent

DT = 0.1


def _p(name: str, x: float, y: float, team: str = "home", poste: str = "MC", **attributes: int) -> PlayerState:
    return PlayerState(name=name, team=team, poste=poste, position=Vec2(x, y), velocity=Vec2(0.0, 0.0), pace=60,
                       acceleration=60, stamina=60, home_target=Vec2(x, y),
                       attributes={k.replace("_", " "): v for k, v in attributes.items()} or None)


def _run_until_restart(ball: BallState, players: list[PlayerState], ticks: int = 100) -> None:
    for i in range(ticks):
        _step_ball(ball, DT, players, i * DT)
        if ball.restart is not None:
            return


def test_exit_point_names_the_line_crossed() -> None:
    assert exit_point(Vec2(50, 1), Vec2(51, -1)) == ("touche", Vec2(50.5, 0.0))
    assert exit_point(Vec2(104, 30), Vec2(106, 30))[0] == "but"
    assert exit_point(Vec2(50, 30), Vec2(51, 31)) is None


def test_side_line_gives_a_throw_in_to_the_last_toucher_opponent() -> None:
    home, away = _p("H", 50, 5), _p("A", 40, 30, team="away")
    ball = BallState(position=Vec2(50, 1), velocity=Vec2(0, -10), last_toucher="H")
    _run_until_restart(ball, [home, away])
    assert ball.restart is not None and ball.restart.kind == THROW_IN and ball.restart.team == "away"
    assert ball.restart.spot.y == 0.0 and ball.restart.taker == "A"


def test_goal_line_gives_a_corner_or_a_goal_kick() -> None:
    attacker, defender, keeper = _p("Att", 95, 30), _p("Def", 98, 34, team="away"), _p("GK", 103, 34, "away", "GK")
    players = [attacker, defender, keeper]
    corner = award("but", Vec2(PITCH_LENGTH_M, 40), defender, players, 0.0)
    assert corner.kind == CORNER and corner.team == "home" and corner.spot == Vec2(PITCH_LENGTH_M, PITCH_WIDTH_M)
    goal_kick = award("but", Vec2(PITCH_LENGTH_M, 20), attacker, players, 0.0)
    assert goal_kick.kind == GOAL_KICK and goal_kick.team == "away" and goal_kick.taker == "GK"
    assert goal_kick.spot.x == PITCH_LENGTH_M - 5.5 and goal_kick.spot.y < PITCH_WIDTH_M / 2.0
    assert goal_kick.until_s == DEAD_S[GOAL_KICK]


def test_ball_is_dead_then_played_without_offside() -> None:
    # touche pour l'extérieur ; un attaquant de l'extérieur est derrière la défense : pas de hors-jeu sur une touche
    taker, runner = _p("A", 40, 3, team="away"), _p("A2", 25, 10, team="away")
    defender = _p("H", 30, 20)
    ball = BallState(position=Vec2(40, 0), velocity=Vec2(0, 0))
    ball.restart = Restart(THROW_IN, "away", Vec2(40, 0), "A", until_s=1.0, minute=0.0, last_toucher="H")
    events: list[RestartEvent] = []
    players = [taker, runner, defender]
    _step_ball(ball, DT, players, 0.5, restarts=events)
    assert ball.restart is not None and ball.velocity == Vec2(0, 0) and not events  # mort jusqu'à 1 s
    _step_ball(ball, DT, players, 1.0, restarts=events)
    assert ball.restart is None and ball.receiver in ("A2",) and not ball.offside_watch
    assert events and events[0].kind == THROW_IN and events[0].dead_s == 1.0


def test_goal_gives_kickoff_to_the_conceding_team_everyone_in_own_half() -> None:
    scorer, keeper = _p("Bu", 100, 34), _p("GK", 104, 34, "away", "GK")
    away_fwd = _p("Fwd", 60, 34, team="away")
    ball = BallState(position=Vec2(104.5, 34), velocity=Vec2(30, 0), shot_for="home")
    assert _step_ball(ball, DT, [scorer, keeper, away_fwd], 10.0) == "home"
    restart = ball.restart
    assert restart.kind == KICKOFF and restart.team == "away" and restart.until_s == 10.0 + DEAD_S[KICKOFF]
    assert restart.taker == "Fwd"
    # pendant le ballon mort : chacun dans son camp, l'adversaire du preneur hors du rond central
    for player in (_p("H1", 70, 34), _p("H2", 52, 34), _p("A1", 40, 30, team="away")):
        target = think(player, ball, [player, scorer, keeper, away_fwd], 10.0 / 60.0, None).target
        own_half = target.x < PITCH_LENGTH_M / 2.0 if player.team == "home" else target.x > PITCH_LENGTH_M / 2.0
        assert own_half
        if player.team == "home":
            assert target.distance_to(restart.spot) >= RESTART_DISTANCE_M[KICKOFF] - 1e-6


def test_opponents_stand_at_the_regulation_distance() -> None:
    restart = Restart(CORNER, "home", Vec2(105, 68), "C", 30.0, 0.0)
    defender = _p("D", 101, 64, team="away")
    assert place(defender, restart, defender.position).distance_to(restart.spot) >= 9.15 - 1e-6
    mate = _p("M", 101, 64)
    assert place(mate, restart, mate.position) == mate.position


def test_ground_player_does_not_touch_an_aerial_ball_except_at_its_landing_point() -> None:
    under, catcher = _p("Sous", 20, 34.0, team="away"), _p("Cible", 40, 34.0)
    ball = BallState(position=Vec2(10, 34), velocity=Vec2(25, 0), mode=AERIEN, aerial_left_m=27.0)
    for i in range(30):
        _step_ball(ball, DT, [under, catcher], i * DT)
        if ball.holder is not None:
            break
    assert ball.holder != "Sous" and ball.position.x > 20.0


def test_loose_ball_targets_stay_on_the_pitch() -> None:
    player = _p("P", 50, 3, Anticipation=99)
    assert loose_ball_target(player, Vec2(50, 1), Vec2(0, -20), BALL_FRICTION_PER_S).y >= 0.0
    assert meeting_point(_p("Lent", 80, 60), Vec2(50, 1), Vec2(0, -20), BALL_FRICTION_PER_S).y >= 0.0


def _long_share(pressed: bool) -> float:
    """Sortie de but : deux solutions courtes et une longue ; `pressed` : chaque solution courte a un adversaire au
    contact (pressing haut). Part de remises jouées long sur 400 tirages."""
    keeper = _p("GK", 5.5, 24.84, poste="GK", Decisions=70)
    short = [_p("DC1", 14, 18), _p("DC2", 14, 32)]
    long_mate = _p("BU", 45, 20)
    # ticket v2-realisme/18g : l'avant-centre visé est marqué (défenseur à 2 m derrière lui) ; seul à 25 m de tout
    # adversaire, une remise longue n'était presque jamais perdue et valait mieux que la courte, pressing ou non
    opponents = [_p("Loin", 70, 34, team="away"), _p("DCadv", 47, 20, team="away")]
    if pressed:
        opponents += [_p("Pr1", 14.8, 18.3, team="away"), _p("Pr2", 14.8, 32.3, team="away")]
    players = [keeper, *short, long_mate, *opponents]
    random.seed(20260923)
    targets = [restart_target(keeper, GOAL_KICK, players) for _ in range(400)]
    return sum(keeper.position.distance_to(t.position) > LONG_RESTART_M for t in targets) / len(targets)


def test_long_restarts_more_often_under_high_press() -> None:
    assert _long_share(pressed=True) >= _long_share(pressed=False) + 0.10


def test_throw_in_reaches_only_mates_within_hand_range() -> None:
    taker, near, far = _p("T", 50, 0), _p("N", 55, 10), _p("F", 90, 30)
    for _ in range(50):
        assert restart_target(taker, THROW_IN, [taker, near, far]) is near


def test_match_start_is_a_kickoff_by_home() -> None:
    restart = kickoff("home", [_p("A", 45, 34), _p("B", 30, 34)], 0.0, dead_s=0.0)
    assert restart.kind == KICKOFF and restart.team == "home" and restart.taker == "A" and restart.until_s == 0.0

"""Issues du tir (ticket v2-collectif/28b) : contré, à côté, but, capté, repoussé, claqué ; trace des tirs."""

from __future__ import annotations

import math
import random

from ligue1sim.pitch_geometry import GOAL_WIDTH_M

from v2engine.ball_state import BallState
from v2engine.decision import Action
from v2engine.geometry import PITCH_LENGTH_M, Vec2
from v2engine.match import GOAL_CENTER_Y, _step_ball
from v2engine.movement import PlayerState
from v2engine.shooting import FLYING, HELD, PARRIED, TIPPED, parry_velocity, save_outcome, save_shares

GOAL = Vec2(PITCH_LENGTH_M, GOAL_CENTER_Y)
CENTRAL_FAR = Vec2(PITCH_LENGTH_M - 25.0, GOAL_CENTER_Y)  # tir central, lointain : chance faible
WIDE_CLOSE = Vec2(PITCH_LENGTH_M - 6.0, GOAL_CENTER_Y - 16.0)  # tir excentré, proche


def _player(name: str, team: str = "home", poste: str = "BU", position: Vec2 = Vec2(0.0, 0.0)) -> PlayerState:
    return PlayerState(name=name, team=team, poste=poste, position=position, velocity=Vec2(0.0, 0.0),
                       pace=60, acceleration=60, stamina=60, home_target=position)


def _freq(chance: float, origin: Vec2, n: int = 4000) -> dict[str, float]:
    random.seed(20260923)
    draws = [save_outcome(chance, origin, GOAL) for _ in range(n)]
    return {k: draws.count(k) / n for k in (HELD, PARRIED, TIPPED)}


def test_shares_sum_to_one_and_follow_the_constants() -> None:
    held, parried, tipped = save_shares(0.0, CENTRAL_FAR, GOAL)
    assert abs(held + parried + tipped - 1.0) < 1e-9
    assert abs(held - 0.70) < 1e-9 and abs(tipped - 0.30 * 0.25) < 1e-9
    held, parried, tipped = save_shares(0.5, WIDE_CLOSE, GOAL)
    assert abs(held - 0.25) < 1e-9 and abs(tipped - 0.75 * (0.25 + 0.35 * 0.8)) < 1e-9  # excentrement 16 / 20


def test_dangerous_wide_shot_is_tipped_more_and_held_less_than_a_weak_central_one() -> None:
    weak_central = _freq(0.03, CENTRAL_FAR)
    dangerous_wide = _freq(0.30, WIDE_CLOSE)
    assert dangerous_wide[TIPPED] > weak_central[TIPPED] + 0.25  # attendu : 0,40 contre 0,09
    assert weak_central[HELD] > dangerous_wide[HELD] + 0.30  # attendu : 0,66 contre 0,25


def test_parry_goes_into_the_pitch_on_the_side_the_shot_is_travelling() -> None:
    random.seed(1)
    keeper_at = Vec2(PITCH_LENGTH_M - 1.0, GOAL_CENTER_Y)
    from_left = Vec2(PITCH_LENGTH_M - 12.0, GOAL_CENTER_Y - 10.0)  # file vers les y croissants
    from_right = Vec2(PITCH_LENGTH_M - 12.0, GOAL_CENTER_Y + 10.0)
    for _ in range(200):
        v = parry_velocity(from_left, GOAL, keeper_at, PARRIED, 30.0)
        assert v.x < 0.0 and v.y > 0.0  # vers le terrain, côté où file le tir
        assert 7.5 - 1e-9 <= v.length() <= 15.0 + 1e-9
        assert parry_velocity(from_right, GOAL, keeper_at, PARRIED, 30.0).y < 0.0


def test_tipped_save_goes_behind_the_line_for_a_corner(monkeypatch) -> None:
    shooter = _player("Buteur", position=WIDE_CLOSE)
    keeper = _player("Gardien", team="away", poste="GK", position=Vec2(PITCH_LENGTH_M - 1.0, GOAL_CENTER_Y - 2.0))
    ball = BallState(position=shooter.position, velocity=Vec2(0.0, 0.0), holder="Buteur")
    monkeypatch.setattr("v2engine.match.should_attempt_tackle", lambda aggression, dt: False)
    monkeypatch.setattr("v2engine.match.choose_action", lambda *args: Action("shot", 1.0))
    monkeypatch.setattr("v2engine.match.draw_shot_error", lambda *args: (0.0, 0.0))  # tir en vol vers le centre du but
    monkeypatch.setattr("v2engine.match.save_outcome", lambda *args: TIPPED)
    shots = []
    for i in range(40):
        _step_ball(ball, 0.1, [shooter, keeper], i * 0.1, shots=shots)
        if ball.restart is not None:
            break
    assert ball.restart is not None and ball.restart.kind == "corner" and ball.restart.team == "home"
    assert [s.outcome for s in shots] == [TIPPED] and shots[0].player == "Buteur"


def test_parried_ball_stays_live_and_the_keeper_does_not_hold_it(monkeypatch) -> None:
    shooter = _player("Buteur", position=Vec2(PITCH_LENGTH_M - 10.0, GOAL_CENTER_Y - 6.0))
    keeper = _player("Gardien", team="away", poste="GK", position=Vec2(PITCH_LENGTH_M - 1.0, GOAL_CENTER_Y))
    ball = BallState(position=shooter.position, velocity=Vec2(0.0, 0.0), holder="Buteur")
    monkeypatch.setattr("v2engine.match.should_attempt_tackle", lambda aggression, dt: False)
    monkeypatch.setattr("v2engine.match.choose_action", lambda *args: Action("shot", 1.0))
    monkeypatch.setattr("v2engine.match.draw_shot_error", lambda *args: (0.0, 0.0))  # tir en vol vers le centre du but
    monkeypatch.setattr("v2engine.match.save_outcome", lambda *args: PARRIED)
    shots = []
    for i in range(20):  # jusqu'au gardien (arrêt par portée, 05b)
        _step_ball(ball, 0.1, [shooter, keeper], i * 0.1, shots=shots)
        if shots[0].outcome != FLYING:
            break
    assert ball.holder is None and ball.velocity.length() > 0.0 and ball.rebound
    assert ball.last_toucher == "Gardien" and ball.position.x < PITCH_LENGTH_M
    assert shots[0].outcome == PARRIED and 0.0 < shots[0].quality < 1.0


def test_shot_trace_is_reproducible_at_fixed_seed() -> None:
    from ligue1sim.clubs import load_clubs
    from ligue1sim.season import CLUBS_PATH
    from v2engine.match import simulate_match

    clubs = load_clubs(CLUBS_PATH, "Ligue 1")
    runs = []
    for _ in range(2):
        random.seed(20260923)
        runs.append(simulate_match(clubs[0], clubs[1], duration_minutes=10).shots)
    assert runs[0] == runs[1]
    assert all(s.outcome in {"but", "à côté", "au-dessus", "dévissé", "contré", FLYING, HELD, PARRIED, TIPPED} for s in runs[0])
    # garde du 05h, sans monkeypatch : en jeu, un tir cadré n'a d'issue que par sa trajectoire (le gardien l'a jugé)
    framed = [s for s in runs[0] if s.outcome in {"but", HELD, PARRIED, TIPPED} and s.origin != "penalty"]
    assert framed and all(s.keeper_time_s is not None for s in framed)


def test_a_keeper_outside_his_area_never_holds_the_ball_with_his_hands(monkeypatch) -> None:
    # ticket v2-realisme/03d : le tirage donne « capté », mais hors de sa surface le gardien repousse (au pied)
    def held_at(keeper_at: Vec2) -> tuple[str, str | None]:
        shooter = _player("Buteur", position=Vec2(PITCH_LENGTH_M - 30.0, GOAL_CENTER_Y))
        keeper = _player("Gardien", team="away", poste="GK", position=keeper_at)
        ball = BallState(position=shooter.position, velocity=Vec2(0.0, 0.0), holder="Buteur")
        monkeypatch.setattr("v2engine.match.should_attempt_tackle", lambda aggression, dt: False)
        monkeypatch.setattr("v2engine.match.choose_action", lambda *args: Action("shot", 1.0))
        monkeypatch.setattr("v2engine.match.draw_shot_error", lambda *args: (0.0, 0.0))  # tir en vol, droit sur lui
        monkeypatch.setattr("v2engine.match.save_outcome", lambda *args: HELD)
        shots = []
        for i in range(20):
            _step_ball(ball, 0.1, [shooter, keeper], i * 0.1, shots=shots)
            if shots[0].outcome != FLYING:
                break
        return shots[0].outcome, ball.holder

    assert held_at(Vec2(PITCH_LENGTH_M - 10.0, GOAL_CENTER_Y)) == (HELD, "Gardien")  # dans sa surface : capté
    assert held_at(Vec2(PITCH_LENGTH_M - 22.0, GOAL_CENTER_Y)) == (PARRIED, None)  # hors de sa surface : repoussé


# --- Tir en vol (ticket v2-realisme/03k) -----------------------------------------------------------------------------
def _wide_shot(monkeypatch):
    """Un tir tenté et tiré à côté : (ballon, joueurs) juste après la frappe."""
    shooter = _player("Buteur", position=Vec2(PITCH_LENGTH_M - 25.0, GOAL_CENTER_Y))
    keeper = _player("Gardien", team="away", poste="GK", position=Vec2(PITCH_LENGTH_M - 1.0, GOAL_CENTER_Y))
    ball = BallState(position=shooter.position, velocity=Vec2(0.0, 0.0), holder="Buteur")
    monkeypatch.setattr("v2engine.match.should_attempt_tackle", lambda aggression, dt: False)
    monkeypatch.setattr("v2engine.match.choose_action", lambda *args: Action("shot", 1.0))
    monkeypatch.setattr("v2engine.match.draw_shot_error", lambda *args: (math.atan2(GOAL_WIDTH_M / 2.0 + 2.0, 25.0), 0.0))
    monkeypatch.setattr("v2engine.match.draw_blocker", lambda *args: None)
    _step_ball(ball, 0.1, [shooter, keeper], 0.0, shots=[])
    return ball, [shooter, keeper]


def test_a_wide_shot_is_flagged_in_flight_and_a_saved_or_scoring_one_is_not_flagged_wide(monkeypatch) -> None:
    ball, _ = _wide_shot(monkeypatch)
    assert ball.shot_wide and ball.shot_in_flight and ball.shot_for is None
    assert not BallState(position=Vec2(0.0, 0.0), velocity=Vec2(0.0, 0.0)).shot_in_flight  # ballon libre ordinaire
    assert BallState(position=Vec2(0.0, 0.0), velocity=Vec2(0.0, 0.0), shot_for="home").shot_in_flight  # tir qui entre


def test_the_wide_shot_flag_is_cleared_when_a_player_touches_the_ball_or_it_leaves_the_pitch(monkeypatch) -> None:
    ball, players = _wide_shot(monkeypatch)
    for i in range(1, 80):  # la ligne de but dépassée : sortie de but, ballon mort
        _step_ball(ball, 0.1, players, i * 0.1)
        if ball.restart is not None:
            break
    assert ball.restart is not None and not ball.shot_wide
    ball, players = _wide_shot(monkeypatch)
    ball.position = Vec2(PITCH_LENGTH_M - 3.0, GOAL_CENTER_Y)  # un défenseur sur la trajectoire touche le ballon
    ball.shot_flight = None  # sorti de son vol (ballon mort avant la ligne ; contre physique au 05c)
    defender = _player("Defenseur", team="away", poste="DC", position=ball.position)
    _step_ball(ball, 0.1, [players[0], defender], 0.5)
    assert not ball.shot_wide


def test_a_new_action_by_a_holder_clears_the_flag(monkeypatch) -> None:
    ball, players = _wide_shot(monkeypatch)
    ball.holder = "Gardien"  # ramassé ailleurs : le ballon est tenu, sa prochaine action le décrit
    monkeypatch.setattr("v2engine.match.choose_action", lambda *args: Action("dribble", 1.0))  # il ne retire pas
    monkeypatch.setattr("v2engine.match.dribble_lost", lambda *args, **kwargs: False)  # ticket 04a : pas de perte tirée ici
    _step_ball(ball, 0.1, players, 0.5)
    assert not ball.shot_wide

"""Meilleur choix factuel et perception du porteur (ticket v2-collectif/33) : scènes fixes des critères d'acceptation."""

from __future__ import annotations

import math
import random
from dataclasses import replace

from v2engine.decision import BEST_CHOICE_TOLERANCE, choose_action, evaluate_options, perception_error
from v2engine.geometry import Vec2
from v2engine.movement import PlayerState

GOAL = Vec2(105.0, 34.0)
DRAWS = 1000


def _p(name: str, x: float, y: float = 34.0, team: str = "home", velocity: Vec2 = Vec2(0.0, 0.0),
       **attributes: int) -> PlayerState:
    return PlayerState(name=name, team=team, poste="MC", position=Vec2(x, y), velocity=velocity, pace=60,
                       acceleration=60, stamina=60, home_target=Vec2(x, y),
                       attributes={k.replace("_", " "): v for k, v in attributes.items()} or None)


def _best(players: list[PlayerState]):
    random.seed(1)
    return evaluate_options(players[0], players, GOAL, None)[0]


def _picks(players: list[PlayerState]) -> list:
    random.seed(20260923)
    return [choose_action(players[0], players, GOAL, None) for _ in range(DRAWS)]


def test_midfielder_with_open_field_ahead_drives_rather_than_plays_back() -> None:
    # le constat d'origine : champ libre devant, il jouait en retrait
    def scene(decisions: int) -> list[PlayerState]:
        return [_p("M", 45, Decisions=decisions), _p("Back", 35), _p("L", 45, 15),
                _p("D1", 80, 25, team="away"), _p("D2", 80, 43, team="away"), _p("D3", 75, team="away")]
    best = _best(scene(60))
    assert best.kind == "dribble" and best.point.x > 50.0  # droit devant

    def shares(decisions: int) -> tuple[float, float]:
        picks = _picks(scene(decisions))
        drive = sum(a.kind == "dribble" for a in picks) / DRAWS
        back = sum(a.kind == "pass" and a.target.name == "Back" for a in picks) / DRAWS
        return drive, back
    (low_drive, low_back), (high_drive, high_back) = shares(20), shares(95)
    assert low_drive > low_back and high_drive > high_back
    # « nettement plus à Decisions élevée » (revue de l'expert, A8 ; mesuré le 04/11/2026 : conduite 83 % -> 99 %,
    # retrait 9,5 % -> 0,7 %)
    assert high_drive >= low_drive + 0.1 and high_back <= low_back / 3


def test_at_the_box_edge_a_good_finisher_shoots_and_a_poor_one_finds_the_free_teammate() -> None:
    def scene(finishing: int) -> list[PlayerState]:
        return [_p("A", 90, Finishing=finishing), _p("Free", 94, 37), _p("Back", 82, 30),
                _p("D1", 97, 30, team="away"), _p("D2", 98, 42, team="away"), _p("D3", 93, 32.5, team="away")]  # D3 colle le porteur, hors de la ligne de tir
    assert _best(scene(90)).kind == "shot"
    poor = _best(scene(25))
    assert poor.kind == "pass" and poor.target.name == "Free"


def test_pressed_near_his_own_goal_the_back_pass_is_the_best_choice() -> None:
    players = [_p("C", 15), _p("Back", 8, 40), _p("Mid", 30, 30),
               _p("P1", 16.5, team="away"), _p("P2", 17, 30, team="away"), _p("P3", 28, 32, team="away")]
    best = _best(players)
    assert best.kind == "pass" and best.target.name == "Back"


def test_no_opponent_closes_a_point_faster_than_his_top_speed_allows() -> None:
    # invariant de la course des adversaires (revue de l'expert, 04/11/2026) : élan puis sprint, jamais plus vite que
    # sa vitesse max depuis t = 0, quelle que soit la part d'élan que le porteur prolonge
    from v2engine.decision import arrival_s
    from v2engine.movement import max_speed_mps
    rng = random.Random(20260923)
    for _ in range(2000):
        pace = rng.randint(1, 99)
        speed, heading = rng.uniform(0.0, max_speed_mps(pace)), rng.uniform(0.0, 2.0 * 3.141592653589793)
        opponent = _p("O", rng.uniform(30, 70), rng.uniform(14, 54), team="away",
                      velocity=Vec2(speed * math.cos(heading), speed * math.sin(heading)))
        opponent = replace(opponent, pace=pace)
        point = Vec2(rng.uniform(30, 70), rng.uniform(14, 54))
        floor = opponent.position.distance_to(point) / max_speed_mps(pace)
        assert all(arrival_s(opponent, point, share) >= floor - 1e-9 for share in (0.0, 0.3, 1.0))


def test_the_expert_scene_a_defender_running_across_does_not_close_the_lane_too_soon() -> None:
    # scène chiffrée de la revue (04/11/2026) : défenseur à (60, 46) lancé à 7 m/s vers la ligne du porteur ; à
    # vitesse max dès t = 0 il lui faut 1,45 s pour (56, 34), le porteur y est en 0,81 s : le point est libre
    from v2engine.decision import free_point
    runner = _p("Run", 60, 46, team="away", velocity=Vec2(0.0, -7.0))
    assert free_point(_p("M", 50), [runner], Vec2(1.0, 0.0), 1.0).x >= 56.0


def test_low_anticipation_drives_more_often_into_a_closing_space() -> None:
    # défenseur lancé vers la ligne du porteur : en réalité l'espace droit devant s'arrête à 56 m ; celui qui ne
    # prolonge pas l'élan du défenseur le croit libre jusqu'à 58 m et s'y engage
    def into_the_closing_space(anticipation: int) -> float:
        players = [_p("M", 50, Anticipation=anticipation, Decisions=99), _p("Back", 40),
                   _p("Run", 58, 45, team="away", velocity=Vec2(0.0, -7.0)), _p("D2", 85, team="away")]
        return sum(a.kind == "dribble" and a.point.x > 57.0 and abs(a.point.y - 34.0) < 1.0
                   for a in _picks(players)) / DRAWS
    assert into_the_closing_space(99) == 0.0
    assert into_the_closing_space(11) >= 0.05


def test_composure_changes_nothing_without_pressure_and_a_lot_at_contact() -> None:
    calm, nervous = _p("C", 50, Composure=99), _p("N", 50, Composure=11)
    assert perception_error(calm, 0.0) == perception_error(nervous, 0.0)
    assert perception_error(nervous, 1.0) / perception_error(nervous, 0.0) > 1.9
    assert 1.1 < perception_error(calm, 1.0) / perception_error(calm, 0.0) < 1.3


def test_errors_are_mostly_close_ones() -> None:
    # erreur plausible : quand il se trompe, il perd surtout peu de valeur, rarement la moitié
    players = [_p("H", 40, Decisions=30), _p("B", 40, 46), _p("A", 40, 22), _p("T", 55, 26),
               _p("Def", 75, 30, team="away"), _p("Def2", 75, 40, team="away")]
    wrong = [a.gap for a in _picks(players) if not a.best]
    assert wrong and sum(gap < 0.25 for gap in wrong) / len(wrong) >= 0.8


def test_best_choice_and_gap_reach_the_trace_and_the_api() -> None:
    from api.routers.v2 import _decisions_out
    from ligue1sim.clubs import load_clubs
    from ligue1sim.season import CLUBS_PATH
    from v2engine.match import simulate_match
    random.seed(20260923)
    clubs = load_clubs(CLUBS_PATH, "Ligue 1")
    trace = simulate_match(clubs[0], clubs[1], duration_minutes=1.0)
    assert trace.decisions and all(d.best_kind in ("shot", "pass", "dribble") and d.gap >= 0.0 for d in trace.decisions)
    assert all(d.best == (d.gap < BEST_CHOICE_TOLERANCE) for d in trace.decisions)
    out = _decisions_out(trace)
    assert [(o.best_kind, o.gap) for o in out] == [(d.best_kind, d.gap) for d in trace.decisions]


def test_a_defender_in_the_shot_line_blocks_shots_and_lowers_their_value() -> None:
    from v2engine.shooting import BLOCK_CHANCE, block_probability, draw_blocker
    shooter = _p("A", 85)
    in_line, beside, behind = _p("D", 92, team="away"), _p("E", 92, 37, team="away"), _p("F", 80, team="away")
    assert block_probability(shooter, GOAL, [in_line]) == BLOCK_CHANCE
    assert block_probability(shooter, GOAL, [beside, behind]) == 0.0
    assert block_probability(shooter, GOAL, [in_line, _p("G", 95, 34.5, team="away")]) > BLOCK_CHANCE
    random.seed(20260923)
    assert abs(sum(draw_blocker(shooter, GOAL, [in_line]) is in_line for _ in range(4000)) / 4000 - BLOCK_CHANCE) < 0.03

    def shot_value(opponents: list[PlayerState]) -> float:
        random.seed(1)
        return next(o.value for o in evaluate_options(shooter, [shooter, *opponents], GOAL, None) if o.kind == "shot")
    assert abs(shot_value([in_line]) - shot_value([beside]) * (1 - BLOCK_CHANCE)) < 1e-12


def test_a_blocked_shot_bounces_off_the_defender_and_is_a_loose_ball(monkeypatch) -> None:
    from v2engine.ball_state import BallState
    from v2engine.decision import Action
    from v2engine.match import _step_ball
    shooter, blocker = _p("A", 85), _p("D", 92, team="away")
    monkeypatch.setattr("v2engine.match.choose_action", lambda *args: Action("shot", 0.1))
    monkeypatch.setattr("v2engine.match.draw_blocker", lambda *args: blocker)
    monkeypatch.setattr("v2engine.match.attempt_shot", lambda *args: (_ for _ in ()).throw(AssertionError("tir passé")))
    monkeypatch.setattr("v2engine.match.should_attempt_tackle", lambda aggression, dt: False)
    ball = BallState(position=shooter.position, velocity=Vec2(0.0, 0.0), holder="A")
    assert _step_ball(ball, 0.1, [shooter, blocker]) is None
    assert ball.holder is None and ball.last_toucher == "D" and ball.shot_for is None
    assert ball.position.distance_to(blocker.position) < 0.5 and ball.velocity.length() > 0.0

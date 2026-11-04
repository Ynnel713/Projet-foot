"""Combinaisons collectives (ticket v2-collectif/14) : le passeur transmet au receveur la suite qu'il a prévue (plan
de passe). Le receveur l'adopte selon son Teamwork, la tient tant que la passe reste jouable, l'abandonne quand la
ligne se ferme ; le coéquipier prévu relance son appel vers un espace où le receveur le trouve."""

from __future__ import annotations

import random

from v2engine.ball_state import BallState
from v2engine.cerveau import APPEL, decide, perceive
from v2engine.decision import (CONTRE_ATTAQUE, PLAN_DROPPED, PLAN_HELD, PLAN_REFUSED, PLAN_UNSEEN, Action,
                               choose_action, evaluate_options)
from v2engine.geometry import Vec2
from v2engine.match import _step_ball
from v2engine.movement import PlayerState
from v2engine.off_ball import OPEN_LANE_PROBABILITY
from v2engine.possession import pass_success_probability

GOAL = Vec2(105.0, 34.0)
DRAWS = 2000


def _p(name: str, x: float, y: float, team: str = "home", **attributes: int) -> PlayerState:
    return PlayerState(name=name, team=team, poste="MC", position=Vec2(x, y), velocity=Vec2(0.0, 0.0), pace=60,
                       acceleration=60, stamina=60, home_target=Vec2(x, y),
                       attributes={k.replace("_", " "): v for k, v in attributes.items()} or None)


def _scene(closed: bool = False, **receiver_attributes: int) -> list[PlayerState]:
    """Le receveur R (porteur ici) et deux coéquipiers presque symétriques : Q, un peu plus avancé, est la meilleure
    passe sans plan ; P est la suite prévue par le passeur. `closed` : un défenseur se place sur la ligne R -> P.
    Decisions 99 (ticket v2-collectif/33) : à 55, l'erreur de perception calée sur la courbe validée noie l'effet du
    plan parmi neuf options proches (mesuré le 04/11/2026 : +10 points pour le plan, +4 pour Teamwork) ; à 99, il se
    lit nettement (+56 et +23 points)."""
    players = [_p("R", 50, 34, Decisions=99, **receiver_attributes), _p("Q", 61, 42), _p("P", 60, 26),
               _p("Def", 80, 30, team="away"), _p("Def2", 80, 40, team="away")]
    if closed:
        players += [_p("Ferme", 55, 30, team="away"), _p("Ferme2", 57, 28.4, team="away")]
    return players


def _share_to_p(players: list[PlayerState], planned: str | None, mode: str | None = None) -> float:
    random.seed(20260923)
    picks = [choose_action(players[0], players, GOAL, None, mode, planned) for _ in range(DRAWS)]
    return sum(a.kind == "pass" and a.target.name == "P" for a in picks) / DRAWS


def _pass(players: list[PlayerState], planned: str | None, mode: str | None = None):
    return next(o for o in evaluate_options(players[0], players, GOAL, None, mode, planned) if o.kind == "pass")


def test_a_held_plan_makes_the_planned_pass_chosen_far_more_often() -> None:
    players = _scene()
    assert _pass(players, None).target.name == "Q"  # sans plan, Q est la meilleure passe
    assert pass_success_probability(players[0], players[2], players[3:]) >= OPEN_LANE_PROBABILITY
    assert _share_to_p(players, "P") >= _share_to_p(players, None) + 0.15


def test_the_plan_is_dropped_when_a_defender_closes_the_line() -> None:
    players = _scene(closed=True)
    assert pass_success_probability(players[0], players[2], players[3:]) < OPEN_LANE_PROBABILITY
    assert abs(_share_to_p(players, "P") - _share_to_p(players, None)) <= 0.02
    random.seed(1)
    states = {o.plan for o in evaluate_options(players[0], players, GOAL, None, None, "P")}
    assert states <= {PLAN_DROPPED, PLAN_REFUSED}


def test_teamwork_sets_how_often_the_plan_is_adopted() -> None:
    def held(teamwork: int) -> float:
        players = _scene(Teamwork=teamwork)
        random.seed(20260923)
        return sum(next(iter(evaluate_options(players[0], players, GOAL, None, None, "P"))).plan == PLAN_HELD
                   for _ in range(DRAWS)) / DRAWS
    high, low = held(99), held(11)
    assert high >= 0.97 and 0.55 <= low <= 0.75  # courbe de tenir le bloc : 99 -> 100 %, 11 -> 65 %
    assert _share_to_p(_scene(Teamwork=99), "P") > _share_to_p(_scene(Teamwork=11), "P") + 0.1


def test_no_plan_in_a_counter_attack(monkeypatch) -> None:
    monkeypatch.setattr("v2engine.decision.random.random", lambda: 0.0)
    players = _scene()
    with_plan = _pass(players, "P", CONTRE_ATTAQUE)
    # ni bonus ni sort compté : en contre-attaque, le plan n'existe pas (pas « refusé » par le Teamwork)
    assert with_plan.plan is None and with_plan.value == _pass(players, None, CONTRE_ATTAQUE).value


def test_a_plan_whose_target_is_out_of_sight_is_counted_apart() -> None:
    players = _scene(Teamwork=99)
    random.seed(1)
    assert {o.plan for o in evaluate_options(players[0], players, GOAL, None, None, "Absent")} == {PLAN_UNSEEN}


def test_the_match_hands_the_plan_to_its_receiver_only_and_clears_it(monkeypatch) -> None:
    seen = []

    def fake_choose(holder, players, goal, keeper, mode, planned, *perception):
        seen.append((holder.name, planned))
        mate = next(p for p in players if p.name == "R")
        return Action("pass", 1.0, mate, follow="P") if holder.name == "H" else Action("dribble", 1.0)
    monkeypatch.setattr("v2engine.match.choose_action", fake_choose)
    players = [_p("H", 40, 34), *_scene()]

    ball = BallState(position=Vec2(40, 34), velocity=Vec2(0, 0), holder="H")
    _step_ball(ball, 0.1, players, now_s=5.0)
    assert ball.plan == ("R", "P", 5.0)  # passe avec une suite : le plan part avec le ballon

    # le receveur le lit ; tout autre porteur l'efface sans le lire ; une conduite n'en pose pas de nouveau
    for holder, read in (("R", "P"), ("Q", None)):
        ball = BallState(position=Vec2(50, 34), velocity=Vec2(0, 0), holder=holder, plan=("R", "P", 5.0))
        _step_ball(ball, 0.1, players, now_s=6.0)
        assert seen[-1] == (holder, read) and ball.plan is None


def _no_depth_run(monkeypatch) -> None:
    # La relance passe d'abord par l'appel dans le dos (ticket 16) : neutralisé ici, la scène ne dépend plus de la graine.
    monkeypatch.setattr("v2engine.cerveau.depth_run", lambda *args, **kwargs: None)


def test_the_planned_mate_relaunches_only_once(monkeypatch) -> None:
    _no_depth_run(monkeypatch)
    receiver, mate = _p("R", 50, 34), _p("P", 62, 30)
    opponents = [_p("Coupe", 55, 32.3, team="away"), _p("Coupe2", 58, 31.3, team="away"),
                 _p("Def", 70, 30, team="away"), _p("Def2", 70, 40, team="away")]
    players = [_p("H", 40, 34), receiver, mate, *opponents]
    ball = BallState(position=Vec2(42, 34), velocity=Vec2(8, 0), receiver="R", last_pass_team="home",
                     plan=("R", "P", 9.5))
    runs = {"P": (Vec2(66.0, 30.0), 12.0)}
    random.seed(20260923)
    decide(mate, APPEL, ball, perceive(mate, ball, players), players, 10.0 / 60.0, runs)
    relaunched = runs["P"]
    decide(mate, APPEL, ball, perceive(mate, ball, players), players, 10.1 / 60.0, runs)
    assert runs["P"] == relaunched  # au tick suivant, l'appel relancé tient


def test_the_passer_transmits_the_follow_up_he_counted() -> None:
    # le porteur H sert A, qui a une meilleure suite vers T (scène du ticket 13) : T est le plan transmis
    players = [_p("H", 40, 34), _p("B", 40, 46), _p("A", 40, 22), _p("T", 55, 26),
               _p("Coupe", 47.5, 36, team="away"), _p("Direct", 47.5, 30, team="away"),
               _p("Def", 75, 30, team="away"), _p("Def2", 75, 40, team="away")]
    option = _pass(players, None)
    assert option.target.name == "A" and option.follow == "T"
    assert _pass([_p("H", 40, 34), _p("M", 40, 22)], None).follow is None  # sans meilleure suite, pas de plan


def test_the_planned_mate_relaunches_his_run_where_the_receiver_finds_him(monkeypatch) -> None:
    _no_depth_run(monkeypatch)
    receiver, mate = _p("R", 50, 34), _p("P", 62, 30)
    opponents = [_p("Coupe", 55, 32.3, team="away"), _p("Coupe2", 58, 31.3, team="away"),
                 _p("Def", 70, 30, team="away"), _p("Def2", 70, 40, team="away")]
    players = [_p("H", 40, 34), receiver, mate, *opponents]
    old = Vec2(66.0, 30.0)  # espace choisi avant la passe, pas encore atteint, ligne R -> P fermée par Coupe et Coupe2
    assert pass_success_probability(receiver, mate, opponents) < OPEN_LANE_PROBABILITY

    def run(plan):
        ball = BallState(position=Vec2(42, 34), velocity=Vec2(8, 0), receiver="R", last_pass_team="home", plan=plan)
        runs = {"P": (old, 10.0 + 2.0)}  # choisi à 9 s, gardé jusqu'à 12 s
        random.seed(20260923)
        decide(mate, APPEL, ball, perceive(mate, ball, players), players, 10.0 / 60.0, runs)
        return runs["P"][0]
    assert run(None) == old  # sans plan, il garde son espace
    target = run(("R", "P", 9.5))  # passe partie à 9,5 s, après son choix : il relance son appel
    assert target != old
    assert pass_success_probability(receiver, mate.__class__(**{**mate.__dict__, "position": target}),
                                    opponents) >= OPEN_LANE_PROBABILITY


def test_a_depth_run_takes_precedence_over_the_planned_space(monkeypatch) -> None:
    # Réserve A3 de la clôture 10-14-16 : à la relance, l'appel dans le dos (ticket 16) passe avant l'espace où le
    # receveur le trouve ; il est alors tenu pour le receveur, devenu le passeur pris en compte.
    receiver, mate = _p("R", 50, 34), _p("P", 62, 30)
    opponents = [_p("Coupe", 55, 32.3, team="away"), _p("Coupe2", 58, 31.3, team="away"),
                 _p("Def", 70, 30, team="away"), _p("Def2", 70, 40, team="away")]
    players = [_p("H", 40, 34), receiver, mate, *opponents]
    monkeypatch.setattr("v2engine.cerveau.depth_run", lambda *args, **kwargs: Vec2(68.0, 30.0))
    ball = BallState(position=Vec2(42, 34), velocity=Vec2(8, 0), receiver="R", last_pass_team="home",
                     plan=("R", "P", 9.5))
    runs = {"P": (Vec2(66.0, 30.0), 12.0)}
    decide(mate, APPEL, ball, perceive(mate, ball, players), players, 10.0 / 60.0, runs)
    assert len(runs["P"]) == 3 and runs["P"][2] == "R"

"""Tests du moteur V2, ticket v2-collectif/15a (court ou long selon le pressing, depuis la zone de construction). Voir
.scratch/v2-collectif/issues/15a-court-ou-long-selon-le-pressing.md, critères d'acceptation."""

from __future__ import annotations

import random

import pytest

from v2engine.ball_state import BallState
from v2engine.bloc import builds_up
from v2engine.decision import LONG_BALL_WON, choose_action, evaluate_options
from v2engine.geometry import PITCH_LENGTH_M, Vec2
from v2engine.match import GOAL_CENTER_Y, RELANCE_LONGUE, _execute, _record_decision
from v2engine.movement import PlayerState
from v2engine.possession import (LONG_PASS_M, max_pass_reach_m, pass_accuracy_probability, pass_success_probability)
from v2engine.restart import AERIAL_LANDING_M, AERIEN, LONG_RESTART_M
from v2engine.trace import PASSE, EventLog

GOAL = Vec2(PITCH_LENGTH_M, GOAL_CENTER_Y)


def _player(name: str, team: str = "home", poste: str = "DC", position: Vec2 = Vec2(50.0, 34.0),
            attributes: dict[str, int] | None = None) -> PlayerState:
    return PlayerState(name=name, team=team, poste=poste, position=position, velocity=Vec2(0.0, 0.0),
                       pace=60, acceleration=60, stamina=60, home_target=position, attributes=attributes)


def _scene(pressed: bool, keeper_attributes: dict[str, int] | None = None) -> tuple[PlayerState, list[PlayerState]]:
    """Gardien porteur, deux centraux écartés, une sentinelle, l'avant-centre à 47 m marqué ; adversaires loin, ou
    quatre dans ses 35 m sur ses solutions courtes (pressing haut)."""
    keeper = _player("GK", poste="GK", position=Vec2(5.0, 34.0), attributes=keeper_attributes)
    mates = [_player("DCg", position=Vec2(14.0, 18.0)), _player("DCd", position=Vec2(14.0, 50.0)),
             _player("MDC", poste="MDC", position=Vec2(22.0, 34.0)), _player("BU", poste="BU", position=Vec2(52.0, 34.0))]
    marker = _player("Def", team="away", position=Vec2(56.0, 34.0))
    if pressed:
        rivals = [_player("A0", "away", "BU", Vec2(15.5, 19.5)), _player("A1", "away", "BU", Vec2(15.5, 48.5)),
                  _player("A2", "away", "MOC", Vec2(20.5, 34.0)), _player("A3", "away", "BU", Vec2(8.0, 34.0))]
    else:
        rivals = [_player(f"A{i}", "away", "BU", Vec2(70.0, 10.0 + 15.0 * i)) for i in range(4)]
    return keeper, [keeper, *mates, marker, *rivals]


def _long_share(pressed: bool, draws: int = 1000) -> float:
    keeper, players = _scene(pressed)
    random.seed(20260923)
    return sum(choose_action(keeper, players, GOAL, None, build_up=True).lofted for _ in range(draws)) / draws


def test_lofted_accuracy_matches_validated_points() -> None:
    # constante validée le 17/11/2026 (0,8 point de difficulté par mètre au-delà de 10 m : à 50 m, 47 / 69 / 87 % à Passing
    # 40 / 55 / 70) ; loi d'écart continue depuis le ticket v2-realisme/23a : même écart angulaire qu'au sol, tolérance
    # d'arrivée `LOFTED_ON_TARGET_M` (2,5 m) réglée sur les 69 % de Passing 55 : 52 / 66 / 75 %
    target = _player("Cible", position=Vec2(60.0, 34.0))
    for passing, expected in ((40, 0.52), (55, 0.66), (70, 0.75)):
        passer = _player("Passeur", position=Vec2(10.0, 34.0), attributes={"Passing": passing})
        assert pass_accuracy_probability(passer, target, [], lofted=True) == pytest.approx(expected, abs=0.01)
        assert pass_accuracy_probability(passer, target, []) < expected - 0.15  # au sol, bien plus dure (0,3 avant le 23a)


def test_lofted_pass_is_not_cut_in_flight() -> None:
    passer = _player("Passeur", position=Vec2(10.0, 34.0))
    target = _player("Cible", position=Vec2(50.0, 34.0))
    on_path = [_player("Coupeur", "away", position=Vec2(30.0, 34.3))]
    assert pass_success_probability(passer, target, on_path) < pass_success_probability(passer, target, []) - 0.3
    assert pass_success_probability(passer, target, on_path, lofted=True) == \
        pytest.approx(pass_success_probability(passer, target, [], lofted=True))


def test_long_pass_threshold_is_shared_with_restarts_and_reach_is_about_58_m() -> None:
    assert LONG_RESTART_M == LONG_PASS_M == 25.0
    assert max_pass_reach_m() == pytest.approx(57.8, abs=0.1)


def test_builds_up_matches_the_build_up_phase() -> None:
    assert builds_up(_player("GK", poste="GK", position=Vec2(5.0, 34.0)))
    assert builds_up(_player("DC", position=Vec2(34.0, 20.0)))
    assert not builds_up(_player("DC", position=Vec2(36.0, 20.0)))  # au-delà de ses 35 m
    assert not builds_up(_player("MDC", poste="MDC", position=Vec2(20.0, 34.0)))  # pas un bâtisseur
    assert builds_up(_player("DC", team="away", position=Vec2(PITCH_LENGTH_M - 20.0, 20.0)))  # en miroir


def test_long_option_only_in_build_up_towards_high_postes_beyond_25_m_even_out_of_vision() -> None:
    # Vision 11 : portée 10 m ; la relance longue reste envisagée (schéma d'équipe, pas une passe à repérer)
    keeper, players = _scene(False, {"Vision": 11})
    random.seed(1)
    lofted = [o for o in evaluate_options(keeper, players, GOAL, None, build_up=True) if o.lofted]
    assert {o.target.name for o in lofted} == {"BU"}  # pas les centraux ni la sentinelle
    assert not any(o.lofted for o in evaluate_options(keeper, players, GOAL, None))  # hors zone de construction
    near = [p if p.name != "BU" else _player("BU", poste="BU", position=Vec2(5.0 + LONG_PASS_M - 1.0, 34.0))
            for p in players]
    assert not any(o.lofted for o in evaluate_options(keeper, near, GOAL, None, build_up=True))  # à moins de 25 m
    far = [p if p.name != "BU" else _player("BU", poste="BU", position=Vec2(5.0 + max_pass_reach_m() + 2.0, 34.0))
           for p in players]
    assert not any(o.lofted for o in evaluate_options(keeper, far, GOAL, None, build_up=True))  # hors de portée
    assert not any(o.lofted for o in evaluate_options(keeper, players, GOAL, None, build_up=True, one_touch=True))


def test_long_value_counts_the_contested_landing() -> None:
    keeper, players = _scene(False)
    random.seed(1)
    option = next(o for o in evaluate_options(keeper, players, GOAL, None, build_up=True) if o.lofted)
    target = option.target
    alone = [p for p in players if p.name != "Def"]
    random.seed(1)
    free = next(o for o in evaluate_options(keeper, alone, GOAL, None, build_up=True) if o.lofted)
    assert 0.0 < LONG_BALL_WON < 1.0 and target.name == "BU"
    assert free.value > option.value  # un avant-centre marqué vaut moins (gêne du receveur, comme au sol)


def test_keeper_plays_short_without_pressing_and_long_under_high_pressing() -> None:
    # critère : part de jeu long nettement plus forte face au pressing haut, à situation égale (mesuré le 17/11/2026 :
    # 0 % sans pressing, 100 % avec quatre adversaires sur ses solutions courtes)
    free, pressed = _long_share(False), _long_share(True)
    assert free <= 0.05
    assert pressed >= 0.8 and pressed >= free + 0.5


def _defender_passes(pressed: bool, draws: int = 1000) -> tuple[float, float]:
    """Central porteur à 25 m de son but, avant-centre à 46 m marqué, gardien adverse sur sa ligne ; adversaires loin, ou
    quatre dans ses 35 m sur ses solutions courtes et sur lui (pressing haut). Part de relances longues parmi ses passes,
    et parmi toutes ses décisions (revue de l'expert, A1)."""
    holder = _player("DCg", position=Vec2(25.0, 20.0))
    mates = [_player("GK", poste="GK", position=Vec2(5.0, 34.0)), _player("DCd", position=Vec2(25.0, 48.0)),
             _player("MDC", poste="MDC", position=Vec2(32.0, 30.0)), _player("LB", poste="LB", position=Vec2(30.0, 5.0)),
             _player("BU", poste="BU", position=Vec2(70.0, 30.0))]
    rivals = [_player("Def", "away", position=Vec2(74.0, 30.0)), _player("GKa", "away", "GK", Vec2(103.0, 34.0))]
    if pressed:
        rivals += [_player("A0", "away", "BU", Vec2(26.5, 47.0)), _player("A1", "away", "MOC", Vec2(33.0, 31.5)),
                   _player("A2", "away", "AG", Vec2(31.0, 6.5)), _player("A3", "away", "BU", Vec2(27.0, 21.5))]
    else:
        rivals += [_player(f"A{i}", "away", "BU", Vec2(85.0, 10.0 + 15.0 * i)) for i in range(4)]
    players = [holder, *mates, *rivals]
    random.seed(20260923)
    actions = [choose_action(holder, players, GOAL, rivals[1], build_up=True) for _ in range(draws)]
    passes = [a for a in actions if a.kind == "pass"]
    return sum(a.lofted for a in passes) / len(passes), sum(a.lofted for a in actions) / draws


def test_defender_plays_long_more_often_under_high_pressing() -> None:
    # mesuré le 17/11/2026 : parmi ses passes, 0,9 % de relances longues sans pressing, 45,5 % sous pressing ; parmi toutes
    # ses décisions, 0,6 % et 10,1 % (sous pressing, il conduit surtout : risque de conduite du ticket v2-realisme/04a)
    # Ticket v2-realisme/23a (erreur d'exécution continue) : 0,4 % et 6,2 % parmi ses passes, 0,3 % et 3,2 % parmi ses
    # décisions ; remesuré après le réajustement de la clôture (20/11/2026) : 0,3 % et 5,7 % parmi ses passes, 0,2 % et
    # 3,7 % parmi ses décisions. Une passe au sol imprécise reste presque toujours chez son équipe : la passe courte sous
    # pressing est plus sûre qu'avec l'ancienne passe ratée (25 à 50 % de sa longueur), le 45 % du 15a en dépendait.
    # Nouvelle référence décidée par le propriétaire le 20/11/2026 (réserve A3 de l'expert, option 1) ; valeur de la passe
    # longue sous pressing renvoyée au duel aérien (v2-realisme/15b). Le gardien sous pressing joue toujours long.
    free_passes, free_all = _defender_passes(False)
    pressed_passes, pressed_all = _defender_passes(True)
    assert free_passes <= 0.05 and pressed_passes >= 0.04 and pressed_passes >= 10 * free_passes
    assert pressed_all >= free_all + 0.02


def test_lofted_pass_flies_like_a_long_restart_and_is_traced() -> None:
    keeper, players = _scene(True)
    random.seed(20260923)
    action = choose_action(keeper, players, GOAL, None, build_up=True)
    assert action.lofted and action.target.name == "BU"
    ball = BallState(position=keeper.position, velocity=Vec2(0.0, 0.0), holder=keeper.name)
    events: list = []
    ball.log = EventLog(events)
    rivals = [p for p in players if p.team != keeper.team]
    _execute(ball, keeper, action, players, rivals, GOAL, None, 0.0, False, None, None, lost=False)
    assert ball.mode == AERIEN and ball.readers == {} and ball.receiver == "BU"
    assert ball.aerial_left_m == pytest.approx(keeper.position.distance_to(action.target.position) - AERIAL_LANDING_M)
    event = events[-1]
    assert event.kind == PASSE and event.detail == RELANCE_LONGUE
    decisions: list = []
    _record_decision(decisions, None, keeper, rivals, action, 0.0, False)
    record = decisions[0]
    short, long = action.short_long
    assert record.lofted and record.best_long_value == long and record.best_short_value == short and long > short


def test_short_choice_is_traced_with_its_reason_and_ground_passes_untouched() -> None:
    keeper, players = _scene(False)
    random.seed(20260923)
    action = choose_action(keeper, players, GOAL, None, build_up=True)
    assert not action.lofted and action.short_long is not None and action.short_long[0] > action.short_long[1]
    decisions: list = []
    _record_decision(decisions, None, keeper, [p for p in players if p.team != "home"], action, 0.0, False)
    assert not decisions[0].lofted and decisions[0].best_long_value is not None
    random.seed(20260923)
    outside = choose_action(keeper, players, GOAL, None)
    assert outside.short_long is None

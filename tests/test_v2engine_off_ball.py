"""Tests du moteur V2, Phase 5, ticket v2-cerveau-joueurs/03 (Off the Ball : appels et démarquage). Voir
.scratch/v2-cerveau-joueurs/issues/03-off-the-ball-appels.md, critères d'acceptation."""

from __future__ import annotations

import random

from v2engine.ball_state import BallState
from v2engine.geometry import Vec2
from v2engine.match import _step_player
from v2engine.movement import PlayerState
from v2engine.off_ball import (DEPTH_LANE_M, best_space_probability, choose_space, depth_run, depth_run_probability,
                               search_radius_m)


def _player(name: str = "P", team: str = "home", poste: str = "MC", position: Vec2 = Vec2(50.0, 34.0),
            attributes: dict[str, int] | None = None) -> PlayerState:
    return PlayerState(
        name=name, team=team, poste=poste, position=position, velocity=Vec2(0.0, 0.0),
        pace=60, acceleration=60, stamina=60, home_target=position, attributes=attributes,
    )


def test_off_the_ball_curves_match_validated_points() -> None:
    assert [round(search_radius_m(v), 6) for v in (99, 55, 11)] == [15.0, 8.0, 2.0]
    assert [round(best_space_probability(v), 6) for v in (99, 55, 11)] == [0.95, 0.70, 0.45]


def test_space_stays_within_search_radius_mostly_forward() -> None:
    runner = _player(attributes={"Off the Ball": 99})
    random.seed(20260923)
    for _ in range(200):
        target = choose_space(runner, [_player("Adv", team="away", position=Vec2(52.0, 34.0))], forward=1.0)
        assert target.distance_to(runner.home_target) <= 15.0 * 1.2 + 1e-9  # diagonale de la grille
        assert -5.0 - 1e-9 <= target.x - runner.home_target.x <= 10.0 + 1e-9  # 1/3 en arrière, 2/3 en avant


def test_teammates_of_the_holder_no_longer_chase_the_ball() -> None:
    holder = _player("Porteur", position=Vec2(50.0, 34.0))
    mate = _player("Coequipier", position=Vec2(55.0, 34.0))
    opponent = _player("Adv", team="away", position=Vec2(56.0, 34.0))
    ball = BallState(position=holder.position, velocity=Vec2(0.0, 0.0), holder="Porteur")
    runs: dict = {}
    players = [holder, mate, opponent]
    random.seed(1)
    _step_player(mate, ball, 0.1, 0.0, players, runs)
    assert runs["Coequipier"][0] != ball.position  # il vise un espace, pas le ballon


def test_high_off_the_ball_finds_more_space_than_low() -> None:
    opponents = [_player(f"Adv{i}", team="away", position=Vec2(50.0 + dx, 34.0 + dy))
                 for i, (dx, dy) in enumerate([(2, 0), (-2, 3), (0, -3), (5, 5), (6, -4)])]

    def mean_space(note: int) -> float:
        runner = _player(attributes={"Off the Ball": note})
        random.seed(20260923)
        targets = [choose_space(runner, opponents, forward=1.0) for _ in range(500)]
        return sum(min(t.distance_to(o.position) for o in opponents) for t in targets) / len(targets)

    assert mean_space(90) >= 1.3 * mean_space(30)


# --- Ticket v2-collectif/06 : soutien du porteur ------------------------------------------------------------------
def test_space_reachable_by_the_holder_comes_first() -> None:
    from dataclasses import replace
    from unittest import mock

    from v2engine.off_ball import OPEN_LANE_PROBABILITY
    from v2engine.possession import pass_success_probability

    runner = _player(attributes={"Off the Ball": 99})
    holder = _player("Porteur", position=Vec2(30.0, 34.0))
    opponents = [_player("Adv", team="away", position=Vec2(40.0, 45.0))]

    def reach(target: Vec2) -> float:
        return pass_success_probability(holder, replace(runner, position=target), opponents)

    with mock.patch("random.random", return_value=0.0):  # meilleur espace
        alone = choose_space(runner, opponents, forward=1.0)
        supported = choose_space(runner, opponents, forward=1.0, holder=holder)
    assert reach(alone) < OPEN_LANE_PROBABILITY  # le plus libre est trop loin du porteur
    assert reach(supported) >= OPEN_LANE_PROBABILITY


def test_space_keeps_its_distance_from_teammates() -> None:
    from v2engine.off_ball import SPACING_MIN_M

    runner = _player(attributes={"Off the Ball": 99})
    opponents = [_player("Adv", team="away", position=Vec2(52.0, 34.0))]
    mates = [Vec2(60.0, 26.5), Vec2(60.0, 41.5), Vec2(55.0, 34.0)]
    random.seed(20260923)
    for _ in range(200):
        target = choose_space(runner, opponents, forward=1.0, mates=mates)
        assert min(target.distance_to(m) for m in mates) >= SPACING_MIN_M


def test_crowded_teammates_fall_back_to_the_usual_choice() -> None:
    runner = _player(attributes={"Off the Ball": 99})
    opponents = [_player("Adv", team="away", position=Vec2(52.0, 34.0))]
    random.seed(1)
    target = choose_space(runner, opponents, forward=1.0, mates=[runner.home_target])  # aucun espace à 8 m : pas bloqué
    assert target.distance_to(runner.home_target) <= 15.0 * 1.2 + 1e-9


# Appel dans le dos (ticket v2-collectif/16). Ligne du hors-jeu à 80 m de son but, ballon à 50 m, place à 70 m.
LINE = 80.0
ANCHOR = Vec2(70.0, 34.0)


def _depth_runner(off_the_ball: int = 99) -> PlayerState:
    return _player("Coureur", poste="BU", position=Vec2(68.0, 34.0), attributes={"Off the Ball": off_the_ball})


def _holder(vision: int = 99, passing: int = 99) -> PlayerState:
    return _player("Porteur", position=Vec2(50.0, 34.0), attributes={"Vision": vision, "Passing": passing})


def _depth_share(runner: PlayerState, holder: PlayerState, mates: list[Vec2] | None = None, n: int = 2000) -> float:
    random.seed(20260923)
    return sum(depth_run(runner, ANCHOR, holder.position, LINE, holder, 1.0, mates or []) is not None
               for _ in range(n)) / n


def test_depth_run_curves_match_validated_points() -> None:
    exploit_99 = depth_run_probability(_depth_runner(55), _holder()) / 0.35
    assert [round(depth_run_probability(_depth_runner(v), _holder()) / exploit_99, 3) for v in (99, 55, 11)]         == [0.6, 0.35, 0.1]
    exploit = [depth_run_probability(_depth_runner(55), _holder(v, v)) / 0.35 for v in (99, 55, 11)]
    assert [round(e, 2) for e in exploit] == [0.95, 0.70, 0.47]


def test_depth_run_targets_the_line_at_the_width_of_his_place() -> None:
    random.seed(1)
    target = next(t for t in (depth_run(_depth_runner(), ANCHOR, Vec2(50.0, 34.0), LINE, _holder(), 1.0, [])
                              for _ in range(50)) if t is not None)
    assert target == Vec2(LINE, ANCHOR.y)
    away = _player("Coureur", team="away", position=Vec2(105.0 - 68.0, 34.0), attributes={"Off the Ball": 99})
    random.seed(1)
    target = next(t for t in (depth_run(away, Vec2(105.0 - 70.0, 34.0), Vec2(105.0 - 50.0, 34.0), LINE, _holder(),
                                        -1.0, []) for _ in range(50)) if t is not None)
    assert target.x == 105.0 - LINE


def test_no_depth_run_behind_the_ball_far_from_the_line_or_without_holder() -> None:
    runner = _depth_runner()
    random.seed(1)
    for _ in range(200):
        assert depth_run(runner, ANCHOR, Vec2(75.0, 34.0), LINE, _holder(), 1.0, []) is None  # derrière le ballon
        assert depth_run(runner, Vec2(55.0, 34.0), Vec2(50.0, 34.0), LINE, _holder(), 1.0, []) is None  # 25 m
        assert depth_run(runner, ANCHOR, Vec2(50.0, 34.0), LINE, None, 1.0, []) is None  # passe en l'air


def test_two_depth_runs_never_share_a_lane() -> None:
    same_lane = [Vec2(LINE - 1.0, ANCHOR.y + DEPTH_LANE_M - 1.0)]
    other_lane = [Vec2(LINE - 1.0, ANCHOR.y + DEPTH_LANE_M + 1.0)]
    assert _depth_share(_depth_runner(), _holder(), same_lane) == 0.0
    assert _depth_share(_depth_runner(), _holder(), other_lane) > 0.4


def test_high_off_the_ball_runs_in_behind_more_often() -> None:
    assert _depth_share(_depth_runner(99), _holder()) >= 2.0 * _depth_share(_depth_runner(11), _holder())


def test_a_weak_holder_makes_the_runner_give_up() -> None:
    strong, weak = _depth_share(_depth_runner(), _holder(99, 99)), _depth_share(_depth_runner(), _holder(11, 11))
    assert strong >= 2.0 * weak > 0.0  # jamais binaire : un porteur faible n'annule pas tout


def test_a_launched_depth_run_is_held_without_a_new_draw() -> None:
    runner, holder = _depth_runner(11), _holder(11, 11)  # tirage quasi perdu d'avance
    other = _player("Autre", position=Vec2(55.0, 30.0), attributes={"Vision": 11, "Passing": 11})
    random.seed(1)
    for _ in range(100):
        assert depth_run(runner, ANCHOR, holder.position, LINE, holder, 1.0, [], "Porteur") == Vec2(LINE, ANCHOR.y)
        assert depth_run(runner, ANCHOR, holder.position, LINE, None, 1.0, [], "Porteur") == Vec2(LINE, ANCHOR.y)
        assert depth_run(runner, ANCHOR, Vec2(75.0, 34.0), LINE, holder, 1.0, [], "Porteur") is None  # passé derrière
    assert sum(depth_run(runner, ANCHOR, other.position, LINE, other, 1.0, [], "Porteur") is not None
               for _ in range(500)) < 100  # nouveau porteur : il retire au sort
    lane = [Vec2(LINE - 1.0, ANCHOR.y)]
    assert depth_run(runner, ANCHOR, holder.position, LINE, holder, 1.0, lane, "Porteur") is None  # couloir pris

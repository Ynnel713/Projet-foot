"""Qualité de l'occasion et décision de tirer (ticket v2-collectif/28a) : scènes contrôlées. Chance de base tirée de
deux modèles publiés (angle entre les poteaux, distance), défenseurs dans le cône, position du gardien, pression
amortie par Composure seulement, frontière Finishing / Long Shots à la surface de réparation."""

from __future__ import annotations

import random

from v2engine.decision import choose_action
from v2engine.geometry import Vec2
from v2engine.movement import PlayerState
from v2engine.shooting import (BLOCK_CHANCE, KEEPER_OPEN_GOAL_MAX, base_chance, block_probability, occasion_quality,
                               shot_pressure, shot_probability, shooting_note)

GOAL = Vec2(105.0, 34.0)


def _p(name: str, x: float, y: float = 34.0, team: str = "home", poste: str = "BU", **attributes: int) -> PlayerState:
    return PlayerState(name=name, team=team, poste=poste, position=Vec2(x, y), velocity=Vec2(0.0, 0.0), pace=60,
                       acceleration=60, stamina=60, home_target=Vec2(x, y), attributes=attributes or None)


def _keeper(x: float = 104.0, y: float = 34.0) -> PlayerState:
    return _p("K", x, y, team="away", poste="GK")


def test_base_chance_stays_in_the_owner_target_table() -> None:
    # table cible du propriétaire (05/11/2026), face au but puis angle très fermé à 8-10 m
    table = ((6.0, 0.33, 0.40), (11.0, 0.15, 0.20), (16.0, 0.08, 0.11), (20.0, 0.04, 0.06), (25.0, 0.025, 0.04),
             (30.0, 0.015, 0.025))
    for distance, low, high in table:
        assert low <= base_chance(Vec2(105.0 - distance, 34.0), GOAL) <= high
    for closed in (Vec2(103.0, 26.0), Vec2(104.0, 25.0)):
        assert 0.03 <= base_chance(closed, GOAL) <= 0.08


def test_a_defender_in_the_shooting_cone_lowers_the_occasion_and_one_beside_it_does_not() -> None:
    shooter, keeper = _p("A", 89.0), _keeper()
    alone = occasion_quality(shooter, GOAL, keeper, [])
    in_cone = occasion_quality(shooter, GOAL, keeper, [_p("D", 97.0, 35.0, team="away")])
    beside = occasion_quality(shooter, GOAL, keeper, [_p("D", 97.0, 41.0, team="away")])
    assert in_cone < 0.85 * alone and beside == alone
    # plus il est près du tireur, plus il cache de but ; au contact du cône entier : `BLOCK_CHANCE`
    near, far = _p("N", 92.0, team="away"), _p("F", 102.0, team="away")
    assert block_probability(shooter, GOAL, [near]) == BLOCK_CHANCE > block_probability(shooter, GOAL, [far]) > 0.0


def test_the_keeper_position_changes_the_occasion() -> None:
    shooter = _p("A", 94.0)
    placed = shot_probability(shooter, GOAL, _keeper(), [])
    assert abs(placed - base_chance(shooter.position, GOAL)) < 0.01  # bien placé : la chance publiée
    assert shot_probability(shooter, GOAL, _keeper(100.0), []) < 0.75 * placed  # avancé, il ferme l'angle
    assert shot_probability(shooter, GOAL, _keeper(104.0, 30.0), []) > 1.2 * placed  # décalé, but ouvert
    assert shot_probability(_p("A", 103.0, 26.0), GOAL, _keeper(60.0), []) <= 0.9  # jamais garanti
    # but vide : jamais plus de 2 à 3 fois la chance de base, même en angle fermé (propriétaire)
    for spot in (Vec2(103.0, 26.0), Vec2(94.0, 34.0), Vec2(84.0, 30.0)):
        empty = shot_probability(_p("A", spot.x, spot.y), GOAL, _keeper(60.0), [])
        assert 1.0 < empty / base_chance(spot, GOAL) <= KEEPER_OPEN_GOAL_MAX + 1e-9


def test_shot_pressure_tiers_follow_the_nearest_defender_within_the_statsbomb_radius() -> None:
    shooter = _p("A", 89.0)  # 16 m : rayon 0,15 x 16 + 0,85 = 3,25 m
    def loss(x: float, y: float = 34.0, poste: str = "DC") -> float:
        return shot_pressure(shooter, GOAL, [_p("D", x, y, team="away", poste=poste)])
    assert loss(89.0, 34.5) == 0.40 and loss(89.0, 35.5) == 0.25 and loss(89.0, 36.5) == 0.10
    assert loss(89.0, 37.5) == 0.0  # 3,5 m : hors du rayon
    assert loss(87.5) == 0.25 * 0.5  # dans le dos : moitié
    assert loss(89.0, 34.5, poste="GK") == 0.0  # le gardien compte par sa position, pas par la pression
    close = _p("A", 99.0)  # 6 m : rayon 1,75 m
    assert shot_pressure(close, GOAL, [_p("D", 99.0, 36.5, team="away")]) == 0.0
    # paliers sans dépendre de l'axe du tir (déjà compté dans le contre)
    assert loss(89.5, 34.0) == loss(89.0, 34.5)


def test_composure_acts_only_under_pressure() -> None:
    calm, nervous = _p("A", 94.0, Composure=99), _p("A", 94.0, Composure=11)
    keeper, marker = _keeper(), _p("D", 94.5, 34.5, team="away")
    assert shot_probability(calm, GOAL, keeper, []) == shot_probability(nervous, GOAL, keeper, [])
    pressed_calm = shot_probability(calm, GOAL, keeper, [marker])
    pressed_nervous = shot_probability(nervous, GOAL, keeper, [marker])
    free = shot_probability(calm, GOAL, keeper, [])
    assert pressed_nervous < pressed_calm < free
    # Composure 99 récupère un tiers de la pénalité, pas plus
    assert abs((free - pressed_calm) / (free - pressed_nervous) - 2.0 / 3.0) < 0.05


def test_execution_ratio_between_an_elite_and_an_average_shooter_is_about_1_3() -> None:
    keeper = _keeper()
    def chance(note: int) -> float:
        return shot_probability(_p("A", 94.0, Finishing=note), GOAL, keeper, [])
    assert 1.15 <= chance(99) / chance(57) <= 1.45


def test_finishing_inside_the_box_and_long_shots_outside_never_both() -> None:
    inside, outside = Vec2(92.0, 34.0), Vec2(86.0, 34.0)
    assert shooting_note(_p("A", inside.x, Finishing=90, **{"Long Shots": 20})) == 90
    assert shooting_note(_p("A", outside.x, Finishing=90, **{"Long Shots": 20})) == 20
    keeper = _keeper()

    def chance(position: Vec2, **notes: int) -> float:
        return shot_probability(_p("A", position.x, position.y, **notes), GOAL, keeper, [])
    assert chance(inside, Finishing=90, **{"Long Shots": 10}) == chance(inside, Finishing=90, **{"Long Shots": 95})
    assert chance(outside, Finishing=10, **{"Long Shots": 90}) == chance(outside, Finishing=95, **{"Long Shots": 90})
    assert chance(outside, **{"Long Shots": 90}) > chance(outside, **{"Long Shots": 20})


def test_low_decisions_shoots_more_often_on_a_mediocre_chance() -> None:
    # 25 m, un partenaire démarqué dans la surface : le tir est un choix médiocre (moins que la passe)
    def shot_share(decisions: int) -> float:
        players = [_p("A", 80.0, Decisions=decisions), _p("Free", 93.0, 30.0), _p("Back", 70.0, 40.0),
                   _p("D1", 85.0, 40.0, team="away"), _p("D2", 98.0, 42.0, team="away"), _keeper()]
        random.seed(20260923)
        picks = [choose_action(players[0], players, GOAL, players[-1]) for _ in range(1000)]
        assert picks[0].best_kind != "shot"
        return sum(a.kind == "shot" for a in picks) / len(picks)
    low, high = shot_share(15), shot_share(95)
    assert low > high + 0.05

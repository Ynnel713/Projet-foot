"""Relance à la main du gardien (ticket v2-attributs-restants/03c2) : ballon en main (capté, ou pris dans sa surface sur
un ballon qui ne vient pas de son équipe), une passe au sol à portée de bras se joue à la main, Throwing règle sa
précision et sa portée. Référence : 55, médiane des gardiens notés de Ligue 1 de la base ; un gardien sans note vaut la
référence. Ballon au pied (sortie de but, passe en retrait) : Passing, comme avant."""

from __future__ import annotations

from dataclasses import replace

import pytest

from tests.scenes import player
from v2engine import possession
from v2engine.ball_state import BallState
from v2engine.geometry import Vec2
from v2engine.match import _keeper_save, _step_ball
from v2engine.shooting import HELD


def _keeper(throwing: int | None = None, passing: int = 50, in_hands: bool = True):
    keeper = replace(player("G", "home", 5.0, 34.0, "GK", Passing=passing), in_hands=in_hands)
    return keeper if throwing is None else replace(keeper, attributes={**keeper.attributes, "Throwing": throwing})


def test_the_reference_and_the_constants() -> None:
    assert possession.throwing(player("G", poste="GK")) == possession.THROWING_REFERENCE_NOTE == 55.0
    assert possession.throwing(_keeper(80)) == 80.0
    assert possession.throw_range_m() == possession.THROW_RANGE_M == 30.0
    assert possession.throw_range_m(25) == pytest.approx(21.0) and possession.throw_range_m(80) == pytest.approx(37.5)
    assert possession.throw_range_m(1) == possession.THROW_RANGE_BOUNDS_M[0]
    assert possession.throw_range_m(200) == possession.THROW_RANGE_BOUNDS_M[1]


def test_throwing_sets_the_accuracy_of_a_throw_and_passing_the_rest() -> None:
    mate = player("A", "home", 30.0, 34.0, "DC")  # à 25 m : à portée de bras à 55
    acc = {n: possession.pass_accuracy_probability(_keeper(n), mate, []) for n in (30, 55, 80)}
    assert acc[30] < acc[55] < acc[80]
    assert possession.pass_accuracy_probability(_keeper(55, passing=20), mate, []) == acc[55]  # Passing n'y joue pas
    # ballon au pied : Passing, Throwing sans effet
    feet = {n: possession.pass_accuracy_probability(_keeper(n, in_hands=False), mate, []) for n in (30, 80)}
    assert feet[30] == feet[80]
    # hors de portée de bras (à 34 m : au-delà de 30 m à 55, en deçà de 37,5 m à 80) : à 55, il passe au pied
    far = player("B", "home", 39.0, 34.0, "MC")
    assert possession.keeper_throw(_keeper(80), far, False) and not possession.keeper_throw(_keeper(55), far, False)
    assert possession.pass_accuracy_probability(_keeper(55, passing=20), far, []) == \
        possession.pass_accuracy_probability(_keeper(99, passing=20, in_hands=False), far, [])
    # un long ballon en l'air depuis la main reste un dégagement (Kicking, ticket 03c1)
    assert not possession.keeper_throw(_keeper(80), mate, True)
    # un joueur de champ ne lance jamais
    assert not possession.keeper_throw(replace(player("D", "home", 5.0, 34.0, "DC"), in_hands=True), mate, False)


def test_a_caught_shot_puts_the_ball_in_his_hands() -> None:
    keeper = _keeper(in_hands=False)
    rival = player("A", "away", 20.0, 34.0, "BU")
    ball = BallState(position=Vec2(6.0, 34.0), velocity=Vec2(-10.0, 0.0))
    _keeper_save(ball, keeper, HELD, Vec2(20.0, 34.0), Vec2(0.0, 34.0), "away", [keeper, rival], 10.0, Vec2(5.0, 34.0))
    assert keeper.in_hands and ball.holder == "G"


def test_a_ball_from_the_opponent_taken_in_his_area_is_in_hand_a_back_pass_is_not() -> None:
    for last, expected in (("away", True), ("home", False)):
        keeper = _keeper(in_hands=False)
        ball = BallState(position=Vec2(5.4, 34.0), velocity=Vec2(-2.0, 0.0), last_pass_team=last)
        for _ in range(5):
            _step_ball(ball, 0.1, [keeper], 0.0)
            if ball.holder == "G":
                break
        assert ball.holder == "G"
        assert keeper.in_hands is expected, last


def test_the_ball_stays_in_his_hands_from_one_step_to_the_next_and_leaves_with_the_ball() -> None:
    import random

    from ligue1sim.clubs import load_clubs
    from ligue1sim.season import CLUBS_PATH
    from v2engine import movement
    from v2engine.match import simulate_match
    keeper = _keeper()
    assert movement.step(keeper, 0.1, Vec2(6.0, 34.0), 1.0).in_hands  # tenu d'un pas à l'autre
    # en match : jamais en main sans avoir le ballon ; en main au moins une fois sur 15 minutes
    clubs = load_clubs(CLUBS_PATH, "Ligue 1")
    seen = []

    def observer(now_s, players, ball, scoring_team):
        for p in players:
            if p.in_hands:
                assert ball.holder == p.name and p.poste == "GK"
                seen.append(p.name)
    random.seed(20261123)
    simulate_match(clubs[0], clubs[1], duration_minutes=15.0, tick_seconds=0.1, observer=observer)
    assert seen

"""Atteinte selon la hauteur (ticket v2-hauteur-ballon/03a) : un joueur ne joue le ballon que s'il l'atteint avec son
corps (taille, détente selon Jumping Reach) ; le gardien va plus haut avec les mains dans sa surface."""

from __future__ import annotations

import random

import pytest

import v2engine.match as match
from v2engine.atteinte import (BODY_SHARE, CORPS, FOOT_SHARE, HANDS_SHARE, JUMP_M, MAINS, NEUTRAL_HEIGHT_M, PIED, TETE,
                               body_part, height_of, jump_m, reach_m)
from v2engine.ball_state import BallState
from v2engine.geometry import Vec2
from v2engine.match import _step_ball
from v2engine.movement import PlayerState
from v2engine.occasion import reach_probability

DT = 0.1


def _p(name: str, x: float, y: float, height: float, jumping: int, team: str = "away", poste: str = "DC") -> PlayerState:
    return PlayerState(name=name, team=team, poste=poste, position=Vec2(x, y), velocity=Vec2(0.0, 0.0), pace=60,
                       acceleration=60, stamina=60, home_target=Vec2(x, y), attributes={"Jumping Reach": jumping},
                       height_m=height)


def test_constants_validated_by_the_owner() -> None:
    assert (FOOT_SHARE, BODY_SHARE, HANDS_SHARE, JUMP_M) == (0.53, 0.82, 1.30, (0.35, 0.65))


def test_height_falls_back_to_the_position_median() -> None:
    assert height_of(178, "DC") == pytest.approx(1.78)
    assert height_of(None, "DC") == NEUTRAL_HEIGHT_M["DC"] == 1.87
    assert height_of(None, "GK") == 1.89 and height_of(None, "??") == 1.82


def test_jump_follows_jumping_reach() -> None:
    assert jump_m(_p("a", 0, 0, 1.8, 1)) == pytest.approx(0.35)
    assert jump_m(_p("a", 0, 0, 1.8, 99)) == pytest.approx(0.65)
    assert jump_m(_p("a", 0, 0, 1.8, 50)) == pytest.approx(0.35 + 0.30 * 49 / 98)


def test_body_part_bands() -> None:
    player = _p("a", 50.0, 34.0, 1.80, 50)
    assert body_part(player, 0.0) == PIED and body_part(player, 0.95) == PIED  # hanche 0,954 m
    assert body_part(player, 1.2) == CORPS and body_part(player, 1.47) == CORPS  # épaule 1,476 m
    assert body_part(player, 1.9) == TETE and body_part(player, reach_m(player)) == TETE
    assert body_part(player, reach_m(player) + 0.01) is None


def test_a_ball_at_half_a_metre_is_played_with_the_foot_by_everyone() -> None:
    smallest = _p("Petit", 50.0, 34.0, 1.67, 1)
    assert body_part(smallest, 0.5) == PIED


def test_keeper_hands_only_in_his_own_box() -> None:
    keeper = _p("Gardien", 3.0, 34.0, 1.89, 60, team="home", poste="GK")  # « home » défend le but en x = 0
    assert reach_m(keeper) == pytest.approx(1.30 * 1.89 + jump_m(keeper))
    assert body_part(keeper, 2.7) == MAINS
    keeper.position = Vec2(30.0, 34.0)  # hors de sa surface : pas de mains
    assert reach_m(keeper) == pytest.approx(1.89 + jump_m(keeper)) and body_part(keeper, 2.7) is None


def _cross(players: list[PlayerState], z: float, monkeypatch) -> BallState:
    """Ballon à `z` au sommet de sa course (vitesse verticale nulle), filant vers x croissant le long de y = 34."""
    monkeypatch.setattr(match, "attempt_control", lambda *args, **kwargs: True)
    ball = BallState(position=Vec2(40.0, 34.0), velocity=Vec2(12.0, 0.0), z=z, vz=0.0, last_pass_team="home")
    random.seed(20261123)
    for i in range(6):
        _step_ball(ball, DT, players, i * DT)
        if ball.last_toucher is not None:
            break
    return ball


def test_a_ball_at_25_m_passes_over_a_short_defender_and_a_tall_jumper_takes_it(monkeypatch) -> None:
    short = _p("Petit", 40.6, 34.0, 1.70, 20)  # atteinte 2,11 m
    tall = _p("Grand", 41.4, 34.0, 1.90, 90, team="home")  # atteinte 2,52 m
    ball = _cross([short, tall], 2.5, monkeypatch)
    assert ball.last_toucher == "Grand" and ball.holder == "Grand"


def test_alone_the_short_defender_cannot_reach_the_ball(monkeypatch) -> None:
    short = _p("Petit", 40.6, 34.0, 1.70, 20)
    ball = _cross([short], 2.5, monkeypatch)
    assert ball.last_toucher is None


def test_the_keeper_catches_in_his_box_a_ball_out_of_the_field_players_reach(monkeypatch) -> None:
    tall = _p("Grand", 98.6, 34.0, 1.90, 90)  # atteinte 2,52 m
    keeper = _p("Gardien", 99.4, 34.0, 1.89, 60, poste="GK")  # « away » défend le but en x = 105
    ball = BallState(position=Vec2(98.0, 34.0), velocity=Vec2(12.0, 0.0), z=2.7, vz=0.0, last_pass_team="home")
    monkeypatch.setattr(match, "attempt_control", lambda *args, **kwargs: True)
    random.seed(20261123)
    _step_ball(ball, DT, [tall, keeper], 0.0)
    assert ball.last_toucher == "Gardien" and ball.holder == "Gardien" and keeper.in_hands


def test_reach_probability_reads_each_player_reach() -> None:
    ball = BallState(position=Vec2(40.0, 34.0), velocity=Vec2(1e-6, 0.0), z=2.4, vz=0.0)  # ballon quasi arrêté à 2,4 m
    short = _p("Petit", 41.0, 34.0, 1.70, 20, team="home")
    tall = _p("Grand", 41.0, 34.0, 1.90, 90, team="home")
    assert reach_probability(short, ball, [])[0] == 0.0  # trop haut pour lui
    assert reach_probability(tall, ball, [])[0] == 1.0


def test_height_after_no_time_is_the_current_height() -> None:
    # défaut trouvé au 03a : `height_at(z, vz, 0)` valait 0, un ballon au contact dès le début du pas était lu au sol
    from v2engine.vol import height_at, step_height
    assert height_at(2.4, 0.0, 0.0) == 2.4
    assert step_height(1.0, 3.0, 0.0) == (1.0, 3.0, 0)
    assert height_at(0.0, 0.0, 0.0) == 0.0

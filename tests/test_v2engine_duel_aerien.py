"""Duel aérien loyal et retombée (ticket v2-realisme/15b1) : hauteur effective (taille, détente avec ou sans élan,
placement au contact par Strength), chance de gagner sur une courbe en S bornée, scènes de duel, retombée."""

from __future__ import annotations

from dataclasses import replace

import pytest

from v2engine.atteinte import jump_m, reach_m
from v2engine.ball_state import BallState
from v2engine.duel import after_contact_delay_s, contact_share
from v2engine.duel_aerien import (DUEL_MAX, DUEL_MIN, DUEL_RADIUS_M, DUEL_SCALE_M, LANDING_S, PLACEMENT_M, RUN_UP_MPS,
                                  STANDING_JUMP_SHARE, effective_height_m, rival, win_probability)
from v2engine.geometry import Vec2
from v2engine.match import _step_ball
from v2engine.movement import PlayerState
from v2engine.trace import AerialDuelRecord
from tests.scenes import seed_scene

RUN = Vec2(5.0, 0.0)


def _p(name: str, team: str, height: float, jumping: int = 50, strength: int = 50, y: float = 34.0,
       x: float = 50.0, velocity: Vec2 = RUN, poste: str = "BU", balance: int = 50) -> PlayerState:
    return PlayerState(name=name, team=team, poste=poste, position=Vec2(x, y), velocity=velocity, pace=60,
                       acceleration=60, stamina=60, home_target=Vec2(x, y),
                       attributes={"Jumping Reach": jumping, "Strength": strength, "Balance": balance},
                       height_m=height)


def test_constants_validated_by_the_owner() -> None:
    assert (DUEL_RADIUS_M, RUN_UP_MPS, STANDING_JUMP_SHARE, PLACEMENT_M) == (1.0, 3.0, 0.85, 0.06)
    assert (DUEL_SCALE_M, DUEL_MIN, DUEL_MAX, LANDING_S) == (0.18, 0.10, 0.90, 0.2)


def test_effective_height_is_height_plus_jump_reduced_without_run_up_plus_placement() -> None:
    runner = _p("A", "home", 1.80)
    assert effective_height_m(runner, 0.5) == pytest.approx(1.80 + jump_m(runner))
    standing = replace(runner, velocity=Vec2(2.9, 0.0))
    assert effective_height_m(standing, 0.5) == pytest.approx(1.80 + 0.85 * jump_m(runner))
    assert effective_height_m(runner, 0.75) - effective_height_m(runner, 0.5) == pytest.approx(PLACEMENT_M)
    assert effective_height_m(runner, 0.25) - effective_height_m(runner, 0.5) == pytest.approx(-PLACEMENT_M)
    strong, weak = _p("F", "home", 1.80, strength=99), _p("f", "away", 1.80, strength=1)
    share = contact_share(strong, weak)
    assert share == pytest.approx(0.75)  # part du contact du 11b, bornée : placement entier
    assert effective_height_m(strong, share) - effective_height_m(weak, 1.0 - share) == pytest.approx(2 * PLACEMENT_M)


def test_win_probability_landmarks_bounds_and_symmetry() -> None:
    assert win_probability(_p("G", "home", 1.95), _p("p", "away", 1.70)) == pytest.approx(0.80, abs=0.01)
    assert win_probability(_p("G", "home", 1.85), _p("p", "away", 1.75)) == pytest.approx(0.64, abs=0.01)
    assert win_probability(_p("p", "home", 1.70, jumping=99), _p("G", "away", 1.95)) == pytest.approx(0.36, abs=0.02)
    assert win_probability(_p("G", "home", 2.10, jumping=99), _p("p", "away", 1.60, jumping=1)) == DUEL_MAX
    assert win_probability(_p("p", "home", 1.60, jumping=1), _p("G", "away", 2.10, jumping=99)) == DUEL_MIN
    for a, b in ((_p("A", "home", 1.83, 70, 30), _p("B", "away", 1.78, 40, 80)),
                 (_p("A", "home", 1.90, velocity=Vec2(0.0, 0.0)), _p("B", "away", 1.80))):
        assert win_probability(a, b) + win_probability(b, a) == pytest.approx(1.0)
    same = win_probability(_p("A", "home", 1.80), _p("B", "away", 1.80))
    assert same == pytest.approx(0.5)


def _ball(z: float = 2.1) -> BallState:
    """Ballon qui arrive à 10 m/s vers +x et commence à descendre, à `z` mètres au-dessus des joueurs (x = 50)."""
    ball = BallState(position=Vec2(49.5, 34.0), velocity=Vec2(10.0, 0.0))
    ball.z, ball.vz = z, 0.0
    ball.last_pass_team = "home"
    return ball


def _duel(home: PlayerState, away: PlayerState, seed: int, z: float = 2.1) -> tuple[BallState, list[AerialDuelRecord]]:
    """Un pas de 0,1 s : le ballon passe entre les deux joueurs (0,3 m de part et d'autre de sa ligne)."""
    players = [replace(home, position=Vec2(50.0, 33.7 if seed % 2 else 34.3)),
               replace(away, position=Vec2(50.0, 34.3 if seed % 2 else 33.7))]
    ball, records = _ball(z), []
    seed_scene(seed)
    _step_ball(ball, 0.1, players, 10.0, aerial_duels=records)
    return ball, records


def _wins(home: PlayerState, away: PlayerState, n: int = 400) -> float:
    won = 0
    for seed in range(n):
        ball, [record] = _duel(home, away, seed)
        assert ball.last_toucher == record.winner  # le gagnant joue le ballon
        won += record.winner == home.name
    return won / n


def test_scene_the_taller_wins_four_duels_in_five_and_jumping_reach_reduces_the_gap() -> None:
    tall, short = _p("Grand", "home", 1.95), _p("Petit", "away", 1.70)
    assert _wins(tall, short) == pytest.approx(0.80, abs=0.05)
    jumper = _p("Petit", "away", 1.70, jumping=99)
    assert _wins(tall, jumper) == pytest.approx(0.64, abs=0.05)  # 36 % pour le petit à grande détente


def test_no_duel_outside_the_trigger() -> None:
    tall, short = _p("Grand", "home", 1.95), _p("Petit", "away", 1.70)
    z = 2.1
    assert rival(tall, [tall, replace(short, position=Vec2(50.0, 35.05))], z, lambda p: False) is None  # 1,05 m
    assert rival(tall, [tall, short], reach_m(short) + 0.01, lambda p: False) is None  # il n'y atteint pas
    assert rival(tall, [tall, replace(short, poste="GK")], z, lambda p: False) is None  # gardien : 03a
    assert rival(tall, [tall, replace(short, team="home")], z, lambda p: False) is None  # coéquipier
    assert rival(tall, [tall, short], z, lambda p: True) is None  # déséquilibré, hors-jeu à la passe...
    assert rival(tall, [tall, short], z, lambda p: False) is short
    keeper = replace(tall, poste="GK", position=Vec2(5.0, 34.0))  # gardien dans sa surface : ballon à la main
    assert rival(keeper, [keeper, replace(short, position=Vec2(5.5, 34.0))], z, lambda p: False) is None
    _, records = _duel(tall, short, 1, z=1.2)  # ballon sous la tête : pas de duel aérien
    assert records == []


def test_offside_flagged_opponent_does_not_contest() -> None:
    tall, short = _p("Grand", "home", 1.95), _p("Petit", "away", 1.70)
    players = [replace(tall, position=Vec2(50.0, 33.7)), replace(short, position=Vec2(50.0, 34.3))]
    ball, records = _ball(), []
    ball.offside_watch = {"Petit"}
    ball.last_pass_team = "away"
    seed_scene(1)
    _step_ball(ball, 0.1, players, 10.0, aerial_duels=records)
    assert records == [] or records[0].winner != "Petit"
    assert all(r.loser != "Petit" and r.winner != "Petit" for r in records)


def test_landing_jumpers_and_loser_wait_contact_loser_is_unsettled_by_balance() -> None:
    tall = _p("Grand", "home", 1.95, strength=90, balance=20)
    short = _p("Petit", "away", 1.70, strength=20, balance=20)
    for seed in range(40):
        ball, [record] = _duel(tall, short, seed)
        winner, loser = record.winner, record.loser
        # le perdant ne peut plus jouer le ballon pendant au moins la retombée
        assert ball.unsettled_until_s[loser] >= 10.0 + LANDING_S - 1e-9
        # le petit a sauté (2,1 m > 1,70 m) et perdu le contact (Strength 20 contre 90) : Balance (12c) par-dessus
        expected = 10.0 + max(LANDING_S, after_contact_delay_s(short))
        if ball.holder == "Petit":  # il a gagné et contrôlé : sa décision attend (réception comprise)
            assert ball.next_decision_s >= expected - 1e-9
        else:
            assert ball.unsettled_until_s["Petit"] == pytest.approx(expected)
        if winner == "Grand":  # 2,1 m > 1,95 m : il a sauté lui aussi
            waits = ball.next_decision_s if ball.holder == "Grand" else ball.unsettled_until_s["Grand"]
            assert waits >= 10.0 + LANDING_S - 1e-9


def test_record_and_determinism() -> None:
    tall, short = _p("Grand", "home", 1.95), _p("Petit", "away", 1.70)
    _, [a] = _duel(tall, short, 7)
    _, [b] = _duel(tall, short, 7)
    assert a == b
    assert {a.winner, a.loser} == {"Grand", "Petit"} and a.first in ("Grand", "Petit")
    assert (a.winner_height_m, a.loser_height_m) in ((1.95, 1.70), (1.70, 1.95))
    assert a.ball_z_m == pytest.approx(2.1, abs=0.1) and 0.10 <= a.probability <= 0.90

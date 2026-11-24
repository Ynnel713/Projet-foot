"""Fautes du duel aérien (ticket v2-realisme/15b2) : situation et fautif possible (épaule contre épaule : gagnant du
contact ; par derrière : celui de derrière ; bascule : celui qui reste sous le sauteur), chance de faute = facteur x
faute d'un tacle (Aggression seule) x prudence de surface, coup franc sifflé tout de suite, gravité propre."""

from __future__ import annotations

from collections import Counter
from dataclasses import replace

import pytest

from v2engine.atteinte import reach_m
from v2engine.ball_state import BallState
from v2engine.duel import CARELESS, EXCESSIVE, RECKLESS, box_prudence, foul_probability, foul_severity
from v2engine.duel_aerien import (BASCULE, BEHIND, BEHIND_ANGLE_DEG, EXCESSIVE_SHARE, FOUL_FACTOR, RECKLESS_SHARE,
                                  SIDE, AerialChallenge, challenge, foul_chance, from_behind, under)
from v2engine.geometry import Vec2
from v2engine.match import _step_ball
from v2engine.movement import PlayerState
from v2engine.restart import FREE_KICK, PENALTY
from v2engine.trace import AerialChallengeRecord, AerialDuelRecord, FoulEvent
from tests.scenes import seed_scene

RUN = Vec2(5.0, 0.0)
EAST = Vec2(1.0, 0.0)


def _p(name: str, team: str, height: float, x: float = 50.0, y: float = 34.0, aggression: int = 50,
       strength: int = 50, jumping: int = 50, decisions: int = 55, facing: Vec2 = EAST,
       poste: str = "BU") -> PlayerState:
    return PlayerState(name=name, team=team, poste=poste, position=Vec2(x, y), velocity=RUN, pace=60,
                       acceleration=60, stamina=60, home_target=Vec2(x, y), facing=facing, height_m=height,
                       attributes={"Aggression": aggression, "Strength": strength, "Jumping Reach": jumping,
                                   "Decisions": decisions, "Balance": 50})


def test_constants_validated_by_the_owner() -> None:
    assert FOUL_FACTOR == {SIDE: 0.10, BEHIND: 0.50, BASCULE: 0.80}
    assert BEHIND_ANGLE_DEG == 120.0
    assert (RECKLESS_SHARE, EXCESSIVE_SHARE) == (0.20, 0.01)


def test_foul_chance_is_factor_times_tackle_foul_and_aggression_alone_sets_it() -> None:
    victim = _p("V", "home", 1.80)
    for aggression in (1, 50, 99):
        fouler = _p("F", "away", 1.80, x=49.3, aggression=aggression)
        for situation, factor in FOUL_FACTOR.items():
            expected = factor * foul_probability(aggression)
            assert foul_chance(AerialChallenge(situation, fouler, victim)) == pytest.approx(expected)
    base = foul_chance(AerialChallenge(BEHIND, _p("F", "away", 1.80), victim))
    for other in ({"strength": 99}, {"jumping": 99}, {"decisions": 99}):  # hors surface : Aggression seule
        assert foul_chance(AerialChallenge(BEHIND, _p("F", "away", 1.80, **other), victim)) == pytest.approx(base)
    assert foul_chance(AerialChallenge(BEHIND, _p("F", "away", 1.80, aggression=99), victim)) > base


def test_box_prudence_in_the_fouler_own_box_only() -> None:
    fouler = _p("F", "away", 1.80, x=99.3, decisions=99)
    in_box = _p("V", "home", 1.80, x=100.0)  # surface que « home » attaque, que défend « away »
    out_box = _p("V", "home", 1.80, x=80.0)
    c_in, c_out = AerialChallenge(SIDE, fouler, in_box), AerialChallenge(SIDE, fouler, out_box)
    assert foul_chance(c_in) == pytest.approx(foul_chance(c_out) * box_prudence(fouler))
    assert box_prudence(fouler) == pytest.approx(0.35)
    attacker_fouls = AerialChallenge(SIDE, replace(out_box, position=Vec2(100.0, 34.0)),
                                     replace(fouler, position=Vec2(99.3, 34.0)))
    assert foul_chance(attacker_fouls) == pytest.approx(0.10 * foul_probability(50))  # surface adverse : pas de prudence


def test_situation_and_possible_fouler() -> None:
    front = _p("Devant", "home", 1.80, strength=90)  # regarde vers +x
    behind = _p("Derriere", "away", 1.80, x=49.3, strength=10)
    assert from_behind(behind, front) and not from_behind(front, behind)
    for a, b in ((front, behind), (behind, front)):
        c = challenge(a, b)  # celui de derrière, même plus faible au contact
        assert (c.situation, c.fouler.name, c.victim.name) == (BEHIND, "Derriere", "Devant")
    side = _p("Cote", "away", 1.80, y=34.7, strength=10)  # à 90° : de côté
    c = challenge(front, side)
    assert (c.situation, c.fouler.name, c.victim.name) == (SIDE, "Devant", "Cote")  # gagnant du contact (Strength)
    c = challenge(side, front)
    assert (c.situation, c.fouler.name) == (SIDE, "Devant")
    # juste au-delà et en deçà du seuil de 120°
    beyond = replace(behind, position=Vec2(50.0 - 0.7 * 0.5, 34.0 + 0.7 * 0.8))  # ~122°
    short = replace(behind, position=Vec2(50.0 - 0.7 * 0.45, 34.0 + 0.7 * 0.9))  # ~117°
    assert from_behind(beyond, front) and not from_behind(short, front)
    # dos à dos : par derrière, fautif = gagnant du contact
    back = replace(behind, facing=Vec2(-1.0, 0.0))
    c = challenge(front, back)
    assert (c.situation, c.fouler.name) == (BEHIND, "Devant")
    # égalité au contact : tiré, les deux possibles
    seed_scene(3)
    names = Counter(challenge(_p("A", "home", 1.8), _p("B", "away", 1.8, y=34.7)).fouler.name for _ in range(200))
    assert set(names) == {"A", "B"} and abs(names["A"] - 100) < 30


def test_under_finds_the_opponent_who_cannot_reach_beneath_a_jumper() -> None:
    jumper = _p("Sauteur", "home", 1.95, jumping=99)
    low = _p("Bas", "away", 1.60, y=34.6, jumping=1)
    z = reach_m(low) + 0.05
    assert jumper.height_m < z <= reach_m(jumper)
    assert under(jumper, [jumper, low], z, lambda p: False) is low
    assert under(jumper, [jumper, replace(low, position=Vec2(50.0, 35.05))], z, lambda p: False) is None  # 1,05 m
    assert under(jumper, [jumper, low], z, lambda p: True) is None  # exclu (déséquilibré, hors-jeu...)
    assert under(jumper, [jumper, replace(low, poste="GK")], z, lambda p: False) is None
    assert under(jumper, [jumper, replace(low, team="home")], z, lambda p: False) is None
    assert under(jumper, [jumper, low], 1.90, lambda p: False) is None  # ballon sous sa taille : il n'a pas sauté


def test_aerial_severity_shares() -> None:
    seed_scene(7)
    n = 20000
    tally = Counter(foul_severity(RECKLESS_SHARE, EXCESSIVE_SHARE) for _ in range(n))
    assert tally[RECKLESS] / n == pytest.approx(0.20, abs=0.01)
    assert tally[EXCESSIVE] / n == pytest.approx(0.01, abs=0.003)
    assert tally[CARELESS] / n == pytest.approx(0.79, abs=0.01)


def _ball(z: float, x: float = 49.5) -> BallState:
    ball = BallState(position=Vec2(x, 34.0), velocity=Vec2(10.0, 0.0))
    ball.z, ball.vz = z, 0.0
    ball.last_pass_team = "home"
    return ball


def _step(players: list[PlayerState], z: float, seed: int, x: float = 49.5):
    ball = _ball(z, x)
    fouls: list[FoulEvent] = []
    duels: list[AerialDuelRecord] = []
    challenges: list[AerialChallengeRecord] = []
    seed_scene(seed)
    _step_ball(ball, 0.1, [replace(p) for p in players], 10.0, fouls=fouls, aerial_duels=duels,
               aerial_challenges=challenges)
    return ball, fouls, duels, challenges


def _rate(players: list[PlayerState], z: float, situation: str, n: int = 400, x: float = 49.5):
    fouled, probability = 0, None
    for seed in range(n):
        ball, fouls, duels, [record] = _step(players, z, seed, x)
        assert record.situation == situation
        probability = record.probability
        if record.foul:
            fouled += 1
            [event] = fouls
            assert (event.player, event.victim, event.severity) == (record.fouler, record.victim, record.severity)
            assert record.victim == players[0].name and ball.restart.team == players[0].team  # équipe fautée
            assert duels == [] and ball.holder is None  # sifflé tout de suite : pas de duel joué, pas d'avantage
        else:
            assert fouls == [] and record.severity == ""
    return fouled / n, probability


def test_scene_side_behind_and_bascule_rates_follow_the_factors() -> None:
    victim = _p("Attaquant", "home", 1.95, jumping=99)
    side = _p("Defenseur", "away", 1.90, y=34.3, aggression=99, strength=90)  # gagnant du contact : fautif possible
    victim_side = replace(victim, position=Vec2(50.0, 33.7), attributes={**victim.attributes, "Strength": 10})
    rate, probability = _rate([victim_side, side], 2.1, SIDE)
    assert probability == pytest.approx(0.10 * foul_probability(99))
    assert rate == pytest.approx(probability, abs=0.04)

    behind = _p("Defenseur", "away", 1.90, x=49.3, aggression=99)
    rate, probability = _rate([victim, behind], 2.1, BEHIND)
    assert probability == pytest.approx(0.50 * foul_probability(99))
    assert rate == pytest.approx(probability, abs=0.06)

    low = _p("Defenseur", "away", 1.60, y=34.4, aggression=50, jumping=1)
    z = reach_m(low) + 0.05
    rate, probability = _rate([replace(victim, position=Vec2(50.0, 33.8)), low], z, BASCULE)
    assert probability == pytest.approx(0.80 * foul_probability(50))
    assert rate == pytest.approx(probability, abs=0.06)


def test_without_foul_the_jumper_wins_the_bascule() -> None:
    jumper = _p("Attaquant", "home", 1.95, x=50.0, y=33.8, jumping=99)
    low = _p("Defenseur", "away", 1.60, y=34.4, jumping=1, aggression=1)
    z = reach_m(low) + 0.05
    plays = 0
    for seed in range(60):
        ball, _fouls, duels, [record] = _step([jumper, low], z, seed)
        if not record.foul:
            assert duels == [] and ball.last_toucher == "Attaquant"  # pas de duel : le sauteur joue le ballon
            plays += 1
    assert plays > 40


def test_foul_in_the_fouler_box_is_a_penalty() -> None:
    victim = _p("Attaquant", "home", 1.95, x=100.0, jumping=99)
    behind = _p("Defenseur", "away", 1.90, x=99.3, aggression=99, decisions=55)
    penalties = 0
    for seed in range(200):
        ball, fouls, _, [record] = _step([victim, behind], 2.1, seed, x=99.5)
        assert record.probability == pytest.approx(0.50 * foul_probability(99) * 0.5)  # prudence de surface (55)
        if record.foul:
            assert ball.restart.kind == PENALTY and fouls[0].outcome == PENALTY
            penalties += 1
    assert penalties > 0
    ball, fouls, _, [record] = next(r for r in (_step([replace(victim, position=Vec2(80.0, 34.0)),
                                                         replace(behind, position=Vec2(79.3, 34.0))], 2.1, s, x=79.5)
                                                   for s in range(200)) if r[3][0].foul)
    assert ball.restart.kind == FREE_KICK


def test_determinism_at_fixed_seed() -> None:
    victim = _p("Attaquant", "home", 1.95, jumping=99)
    behind = _p("Defenseur", "away", 1.90, x=49.3, aggression=99)
    first = [_step([victim, behind], 2.1, s)[3] for s in range(30)]
    again = [_step([victim, behind], 2.1, s)[3] for s in range(30)]
    assert first == again

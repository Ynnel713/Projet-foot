"""Relance au pied du gardien (ticket v2-attributs-restants/03c1) : Kicking, exécution, règle la précision et la portée
d'un long ballon du gardien en l'air (relance longue en jeu, sortie de but jouée long). Référence : 60, médiane des
gardiens notés de Ligue 1 de la base ; un gardien sans note vaut la référence. Les passes courtes au sol et les longs
ballons des joueurs de champ restent sur Passing."""

from __future__ import annotations

from dataclasses import replace

import pytest

from tests.scenes import player
from v2engine import possession
from v2engine.decision import evaluate_options
from v2engine.geometry import Vec2
from v2engine.restart import GOAL_KICK, restart_target


def _keeper(kicking: int | None = None, passing: int = 50):
    keeper = player("G", "home", 5.0, 34.0, "GK", Passing=passing)
    return keeper if kicking is None else replace(keeper, attributes={**keeper.attributes, "Kicking": kicking})


def test_the_reference_and_the_constants() -> None:
    assert possession.kicking(player("G", poste="GK")) == possession.KICKING_REFERENCE_NOTE == 60.0
    assert possession.kicking(replace(player("G", poste="GK"), attributes={})) == 60.0
    assert possession.kicking(_keeper(80)) == 80.0
    assert possession.kick_speed_cap_mps() == possession.MAX_PASS_MPS
    assert possession.kick_speed_cap_mps(80) == pytest.approx(32.0)
    assert possession.kick_speed_cap_mps(35) == pytest.approx(27.5)
    assert possession.kick_speed_cap_mps(1) == possession.KICK_SPEED_BOUNDS_MPS[0]
    assert possession.kick_speed_cap_mps(200) == possession.KICK_SPEED_BOUNDS_MPS[1]
    assert possession.keeper_kick_reach_m(_keeper()) == pytest.approx(possession.max_pass_reach_m())
    reach = {n: possession.keeper_kick_reach_m(_keeper(n)) for n in (35, 60, 80, 99)}
    assert reach[35] == pytest.approx(52.9, abs=0.1) and reach[60] == pytest.approx(57.8, abs=0.1)
    assert reach[80] == pytest.approx(61.7, abs=0.1) and reach[99] == pytest.approx(65.4, abs=0.1)


def test_kicking_sets_the_accuracy_of_the_keeper_long_ball_only() -> None:
    mate = player("A", "home", 55.0, 34.0, "BU")
    acc = {n: possession.pass_accuracy_probability(_keeper(n), mate, [], lofted=True) for n in (40, 60, 80)}
    assert acc[40] < acc[60] < acc[80]
    # Passing n'y joue plus pour le gardien ; il règle encore ses passes au sol
    assert possession.pass_accuracy_probability(_keeper(60, passing=20), mate, [], lofted=True) == acc[60]
    short = player("B", "home", 20.0, 34.0, "DC")
    assert possession.pass_accuracy_probability(_keeper(99, passing=20), short, []) == \
        possession.pass_accuracy_probability(_keeper(20, passing=20), short, [])
    # un joueur de champ garde Passing sur un long ballon
    field = player("D", "home", 5.0, 34.0, "DC", Passing=50, Kicking=99)
    assert possession.pass_accuracy_probability(field, mate, [], lofted=True) == \
        possession.pass_accuracy_probability(replace(field, attributes={"Passing": 50}), mate, [], lofted=True)


def test_a_strong_kicker_reaches_farther_and_the_decision_follows() -> None:
    far = player("A", "home", 5.0 + 61.0, 34.0, "BU")  # à 61 m : hors de portée à 60, à portée à 80
    for note, expected in ((60, False), (80, True)):
        keeper = _keeper(note)
        options = evaluate_options(keeper, [keeper, far], Vec2(105.0, 34.0), None, build_up=True)
        assert any(o.kind == "pass" and getattr(o, "lofted", False) for o in options) is expected, note
    # la frappe arrive : ballon lancé au-delà de 30 m/s par le gardien de Kicking 80
    speeds = [possession.pass_velocity(_keeper(80), far, [], lofted=True).length() for _ in range(50)]
    assert max(speeds) > possession.MAX_PASS_MPS and max(speeds) <= possession.kick_speed_cap_mps(80) + 1e-9
    assert max(possession.pass_velocity(_keeper(60), far, [], lofted=True).length() for _ in range(50)) \
        <= possession.MAX_PASS_MPS + 1e-9


def test_a_long_goal_kick_flies_and_its_accuracy_follows_kicking(monkeypatch) -> None:
    # sortie de but jouée long : passe en l'air (Kicking), le choix du receveur reste celui d'avant (ADR 0002 : Kicking ne
    # règle que le geste) ; un attaquant seul à 50 m, aucun autre receveur
    from v2engine import flux, match
    from v2engine.ball_state import BallState
    from v2engine.restart import Restart
    seen = []
    original = match.pass_launch

    def spy(passer, target, opponents=(), backheel=False, one_touch=False, lofted=False):
        seen.append(lofted)
        return original(passer, target, opponents, backheel, one_touch, lofted)
    monkeypatch.setattr(match, "pass_launch", spy)
    keeper, mate = _keeper(80), player("A", "home", 55.0, 34.0, "BU")
    ball = BallState(position=keeper.position, velocity=Vec2(0.0, 0.0))
    ball.restart = Restart(GOAL_KICK, "home", keeper.position, keeper.name, 0.0, 0.0)
    flux.seed_streams(3)
    match._play_restart(ball, [keeper, mate], 1.0, None)
    assert seen == [True] and ball.vz > 0.0 and ball.receiver == "A"  # part en l'air (ticket v2-hauteur-ballon/02a1)
    assert restart_target(keeper, GOAL_KICK, [keeper, mate]).name == "A"

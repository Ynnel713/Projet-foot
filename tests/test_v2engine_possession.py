"""Tests du moteur V2, Phase 2 (contact ballon et passes) -- voir docs/PLAN_V2.md, critères
d'acceptation. Lecture seule de la V1 : aucun fichier protégé importé."""

from __future__ import annotations

from v2engine.attributes import player_attribute, success_probability
from v2engine.ball_state import BallState
from v2engine.geometry import Vec2
from v2engine.match import _step_ball
from v2engine.movement import PlayerState


def _player(name: str = "P", team: str = "home", position: Vec2 = Vec2(0.0, 0.0),
            attributes: dict[str, int] | None = None) -> PlayerState:
    return PlayerState(
        name=name, team=team, poste="MC", position=position, velocity=Vec2(0.0, 0.0),
        pace=60, acceleration=60, stamina=60, home_target=position, attributes=attributes,
    )


def test_success_probability_never_binary() -> None:
    """Règle "jamais binaire" du guide : même à note extrême, jamais 0 % ni 100 %."""
    assert 0.0 < success_probability(5) < 1.0
    assert 0.0 < success_probability(99) < 1.0


def test_low_first_touch_controls_worse_than_high_first_touch() -> None:
    poor = _player(attributes={"First Touch": 20})
    gifted = _player(attributes={"First Touch": 95})

    assert success_probability(player_attribute(poor, "First Touch")) < success_probability(
        player_attribute(gifted, "First Touch")
    )


def test_low_passing_and_technique_produce_less_accurate_passes_than_high() -> None:
    poor = _player(attributes={"Passing": 15, "Technique": 15})
    gifted = _player(attributes={"Passing": 95, "Technique": 95})

    def _accuracy(player: PlayerState) -> float:
        return (
            success_probability(player_attribute(player, "Passing"))
            + success_probability(player_attribute(player, "Technique"))
        ) / 2.0

    assert _accuracy(poor) < _accuracy(gifted)


def test_player_receives_controls_and_passes_to_nearest_teammate(monkeypatch) -> None:
    receiver = _player("Receveur", position=Vec2(50.0, 34.0))
    near_teammate = _player("Proche", position=Vec2(55.0, 34.0))
    far_teammate = _player("Loin", position=Vec2(90.0, 34.0))
    opponent = _player("Adversaire", team="away", position=Vec2(51.0, 34.0))
    players = [receiver, near_teammate, far_teammate, opponent]
    ball = BallState(position=Vec2(50.0, 34.0), velocity=Vec2(0.0, 0.0))

    monkeypatch.setattr("v2engine.match.attempt_control", lambda player, *args: True)
    # L'adversaire est volontairement à portée de tacle (Phase 3) : neutralisé ici pour ne tester
    # que la passe (Phase 2) -- voir tests/test_v2engine_duel.py pour les tacles eux-mêmes.
    monkeypatch.setattr("v2engine.match.should_attempt_tackle", lambda aggression, dt: False)
    _step_ball(ball, 0.1, players)
    assert ball.holder == "Receveur"
    assert ball.velocity == Vec2(0.0, 0.0)

    monkeypatch.setattr("v2engine.flux.PASSE.random", lambda: 0.0)  # force une passe précise
    _step_ball(ball, 0.1, players, now_s=ball.next_decision_s)  # après son temps de réception (v2-socle/06)

    assert ball.holder is None
    assert ball.velocity.length() > 0.0
    expected_direction = (near_teammate.position - receiver.position).normalized()
    actual_direction = ball.velocity.normalized()
    assert abs(actual_direction.x - expected_direction.x) < 1e-6
    assert abs(actual_direction.y - expected_direction.y) < 1e-6


def test_failed_control_deflects_ball_instead_of_receiving_it(monkeypatch) -> None:
    defender = _player("Defenseur", position=Vec2(30.0, 34.0))
    defender.velocity = Vec2(3.0, 1.0)
    ball = BallState(position=Vec2(30.0, 34.0), velocity=Vec2(0.0, 0.0))

    monkeypatch.setattr("v2engine.match.attempt_control", lambda player, *args: False)
    _step_ball(ball, 0.1, [defender])

    assert ball.holder is None
    assert ball.velocity.length() > 0.0


def test_holder_without_available_teammate_keeps_the_ball() -> None:
    lone_player = _player("Seul", position=Vec2(60.0, 34.0))
    ball = BallState(position=Vec2(60.0, 34.0), velocity=Vec2(0.0, 0.0), holder="Seul")

    _step_ball(ball, 0.1, [lone_player])

    assert ball.holder == "Seul"
    assert ball.velocity == Vec2(0.0, 0.0)

"""Tests du moteur V2, Phase 3 (duels et tacles) -- voir docs/PLAN_V2.md, critères d'acceptation.
Lecture seule de la V1 : aucun fichier protégé importé."""

from __future__ import annotations

from v2engine.ball_state import BallState
from v2engine.duel import attempt_tackle_probability, foul_probability, tackle_success_probability
from v2engine.geometry import Vec2
from v2engine.decision import Action
from v2engine.match import TACKLE_RADIUS_M, _step_ball
from v2engine.movement import PlayerState


def _player(name: str = "P", team: str = "home", position: Vec2 = Vec2(0.0, 0.0),
            attributes: dict[str, int] | None = None) -> PlayerState:
    return PlayerState(
        name=name, team=team, poste="MDC", position=position, velocity=Vec2(0.0, 0.0),
        pace=60, acceleration=60, stamina=60, home_target=position, attributes=attributes,
    )


def test_tackle_outcome_never_binary_even_at_extreme_attribute_gap() -> None:
    dominant = _player("Dominant", attributes={"Tackling": 99, "Aggression": 99})
    helpless = _player("Faible", attributes={"Strength": 5, "Balance": 5})

    probability = tackle_success_probability(dominant, helpless)

    assert 0.0 < probability < 1.0


def test_higher_tackling_strength_balance_favor_the_tackler() -> None:
    strong_tackler = _player("Costaud", attributes={"Tackling": 90, "Aggression": 60})
    weak_holder = _player("Fragile", attributes={"Strength": 20, "Balance": 20})

    weak_tackler = _player("Maladroit", attributes={"Tackling": 20, "Aggression": 60})
    strong_holder = _player("Robuste", attributes={"Strength": 90, "Balance": 90})

    assert tackle_success_probability(strong_tackler, weak_holder) > tackle_success_probability(
        weak_tackler, strong_holder
    )


def test_higher_aggression_increases_foul_risk_independently_of_tackling() -> None:
    assert foul_probability(aggression=90) > foul_probability(aggression=15)


def test_higher_aggression_increases_tackle_attempt_rate() -> None:
    assert attempt_tackle_probability(aggression=90) > attempt_tackle_probability(aggression=15)


def test_won_tackle_transfers_possession(monkeypatch) -> None:
    holder = _player("Porteur", position=Vec2(50.0, 34.0))
    challenger = _player("Adversaire", team="away", position=Vec2(50.5, 34.0))
    ball = BallState(position=Vec2(50.0, 34.0), velocity=Vec2(0.0, 0.0), holder="Porteur")

    monkeypatch.setattr("v2engine.match.should_attempt_tackle", lambda aggression: True)
    monkeypatch.setattr("v2engine.match.resolve_tackle", lambda tackler, holder: _WonTackle())

    _step_ball(ball, 0.1, [holder, challenger])

    assert ball.holder == "Adversaire"
    assert ball.velocity == Vec2(0.0, 0.0)


def test_failed_tackle_keeps_possession_without_falling_through_to_a_pass(monkeypatch) -> None:
    holder = _player("Porteur", position=Vec2(50.0, 34.0))
    challenger = _player("Adversaire", team="away", position=Vec2(50.5, 34.0))
    teammate = _player("Coequipier", position=Vec2(60.0, 34.0))
    ball = BallState(position=Vec2(50.0, 34.0), velocity=Vec2(0.0, 0.0), holder="Porteur")

    monkeypatch.setattr("v2engine.match.should_attempt_tackle", lambda aggression: True)
    monkeypatch.setattr("v2engine.match.resolve_tackle", lambda tackler, holder: _LostTackle())

    _step_ball(ball, 0.1, [holder, challenger, teammate])

    assert ball.holder == "Porteur"  # ni transfert au tacleur, ni passe exécutée ce tick


def test_no_opponent_in_range_falls_through_to_normal_pass(monkeypatch) -> None:
    holder = _player("Porteur", position=Vec2(50.0, 34.0))
    distant_opponent = _player("Loin", team="away", position=Vec2(50.0, 34.0 + TACKLE_RADIUS_M + 5.0))
    teammate = _player("Coequipier", position=Vec2(60.0, 34.0))
    ball = BallState(position=Vec2(50.0, 34.0), velocity=Vec2(0.0, 0.0), holder="Porteur")

    monkeypatch.setattr("v2engine.match.choose_action", lambda *args: Action("pass", 1.0, teammate))  # choix testé ailleurs
    _step_ball(ball, 0.1, [holder, distant_opponent, teammate])

    assert ball.holder is None  # la passe (Phase 2) s'est bien exécutée, faute d'adversaire à portée


class _WonTackle:
    won = True
    foul = False


class _LostTackle:
    won = False
    foul = False

"""Tests du moteur V2, Phase 3 (duels et tacles) -- voir docs/PLAN_V2.md, critères d'acceptation.
Lecture seule de la V1 : aucun fichier protégé importé."""

from __future__ import annotations

from scenes import player, with_attribute
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
    # Fabrique de scènes partagée (ticket v2-realisme/01f) : un profil de base, une note qui varie.
    tackler, holder = player("Tacleur", poste="MDC", Aggression=60), player("Porteur", "away", poste="MDC")
    strong_tackler = with_attribute([tackler], "Tackling", 90)[0]
    weak_holder = with_attribute(with_attribute([holder], "Strength", 20), "Balance", 20)[0]

    weak_tackler = with_attribute([tackler], "Tackling", 20)[0]
    strong_holder = with_attribute(with_attribute([holder], "Strength", 90), "Balance", 90)[0]

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

    monkeypatch.setattr("v2engine.match.should_attempt_tackle", lambda aggression, dt: True)
    monkeypatch.setattr("v2engine.match.resolve_tackle", lambda tackler, holder: _WonTackle())

    _step_ball(ball, 0.1, [holder, challenger])

    assert ball.holder == "Adversaire"
    assert ball.velocity == Vec2(0.0, 0.0)


def test_failed_tackle_keeps_possession_without_falling_through_to_a_pass(monkeypatch) -> None:
    holder = _player("Porteur", position=Vec2(50.0, 34.0))
    challenger = _player("Adversaire", team="away", position=Vec2(50.5, 34.0))
    teammate = _player("Coequipier", position=Vec2(60.0, 34.0))
    ball = BallState(position=Vec2(50.0, 34.0), velocity=Vec2(0.0, 0.0), holder="Porteur")

    monkeypatch.setattr("v2engine.match.should_attempt_tackle", lambda aggression, dt: True)
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


# --- v2-socle/03 : un duel par confrontation ---------------------------------------------------------------------
def _count_attempts(monkeypatch) -> list[str]:
    attempts: list[str] = []
    monkeypatch.setattr("v2engine.match.should_attempt_tackle", lambda aggression, dt: True)
    monkeypatch.setattr("v2engine.match.resolve_tackle",
                        lambda tackler, holder: attempts.append(tackler.name) or _LostTackle())
    monkeypatch.setattr("v2engine.match.choose_action", lambda *args: type("A", (), {"kind": "dribble"})())
    monkeypatch.setattr("v2engine.match.dribble_lost", lambda *args, **kwargs: False)  # ticket 04a : pas de perte tirée ici
    return attempts


def test_beaten_defender_still_close_retries_only_once_recovered(monkeypatch) -> None:
    # ticket v2-collectif/08 (réserve A4 du ticket 25) : un tacle par confrontation, puis un nouveau une fois relevé
    from v2engine.match import FAILED_TACKLE_RECOVERY_S

    holder = _player("Porteur", position=Vec2(50.0, 34.0))
    challenger = _player("Adversaire", team="away", position=Vec2(50.5, 34.0))
    ball = BallState(position=holder.position, velocity=Vec2(0.0, 0.0), holder="Porteur")
    attempts = _count_attempts(monkeypatch)
    times = []
    for i in range(50):  # 5 s au contact
        before = len(attempts)
        _step_ball(ball, 0.1, [holder, challenger], now_s=i * 0.1)
        if len(attempts) > before:
            times.append(i * 0.1)
    assert len(times) == 4  # 0 s, puis à chaque fin d'élimination (1,5 s)
    assert all(b - a >= FAILED_TACKLE_RECOVERY_S - 1e-9 for a, b in zip(times, times[1:]))


def test_failed_tackler_cannot_retry_before_recovery_even_in_a_new_confrontation(monkeypatch) -> None:
    from v2engine.match import FAILED_TACKLE_RECOVERY_S

    holder = _player("Porteur", position=Vec2(50.0, 34.0))
    near, far = Vec2(50.5, 34.0), Vec2(55.0, 34.0)
    ball = BallState(position=holder.position, velocity=Vec2(0.0, 0.0), holder="Porteur")
    attempts = _count_attempts(monkeypatch)
    _step_ball(ball, 0.1, [holder, _player("Adversaire", team="away", position=near)], now_s=0.0)
    _step_ball(ball, 0.1, [holder, _player("Adversaire", team="away", position=far)], now_s=0.1)  # confrontation finie
    _step_ball(ball, 0.1, [holder, _player("Adversaire", team="away", position=near)], now_s=1.0)  # encore éliminé
    assert attempts == ["Adversaire"]
    _step_ball(ball, 0.1, [holder, _player("Adversaire", team="away", position=near)], now_s=FAILED_TACKLE_RECOVERY_S)
    assert attempts == ["Adversaire", "Adversaire"]


def test_other_defender_can_still_tackle_while_the_first_is_engaged(monkeypatch) -> None:
    holder = _player("Porteur", position=Vec2(50.0, 34.0))
    first = _player("Premier", team="away", position=Vec2(50.3, 34.0))
    second = _player("Second", team="away", position=Vec2(50.0, 35.0))
    ball = BallState(position=holder.position, velocity=Vec2(0.0, 0.0), holder="Porteur")
    attempts = _count_attempts(monkeypatch)
    for i in range(3):
        _step_ball(ball, 0.1, [holder, first, second], now_s=i * 0.1)
    assert attempts == ["Premier", "Second"]


def test_confrontation_ends_when_the_ball_goes_loose(monkeypatch) -> None:
    holder = _player("Porteur", position=Vec2(50.0, 34.0))
    defender = _player("Adversaire", team="away", position=Vec2(50.5, 34.0))
    ball = BallState(position=holder.position, velocity=Vec2(0.0, 0.0), holder="Porteur")
    attempts = _count_attempts(monkeypatch)
    _step_ball(ball, 0.1, [holder, defender], now_s=0.0)
    ball.holder = None  # ballon relâché (contrôle raté...), puis repris par le même porteur
    ball.position = Vec2(30.0, 34.0)
    _step_ball(ball, 0.1, [holder, defender], now_s=0.1)
    ball.holder = "Porteur"
    _step_ball(ball, 0.1, [holder, defender], now_s=2.0)  # élimination finie : nouvelle confrontation
    assert attempts == ["Adversaire", "Adversaire"]


def test_aggression_does_not_change_tackle_success() -> None:
    # Aggression règle la fréquence des tentatives et la faute, pas la réussite (règle R1, ticket v2-collectif/18)
    holder = _player("Porteur", attributes={"Strength": 60, "Balance": 60})
    calm = _player("Calme", attributes={"Tackling": 70, "Aggression": 10})
    fierce = _player("Agressif", attributes={"Tackling": 70, "Aggression": 99})
    assert tackle_success_probability(calm, holder) == tackle_success_probability(fierce, holder)

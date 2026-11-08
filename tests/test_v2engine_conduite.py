"""Tests du moteur V2, ticket v2-realisme/04a : le risque de perdre le ballon en conduisant est le même à l'évaluation
(`decision.keep_ball_probability`) et à la résolution (`decision.dribble_lost`, un tirage par intervalle de décision).
Voir .scratch/v2-realisme/issues/04a-conduite-risque-unifie.md."""

from __future__ import annotations

from dataclasses import replace

from v2engine import decision
from v2engine.ball_state import BallState
from v2engine.decision import (DECISION_INTERVAL_S, DRIBBLE_REFERENCE_S, Action, dribble_loss_probability, dribble_lost,
                               evaluate_options, keep_ball_probability)
from v2engine.flux import DUEL
from v2engine.geometry import PITCH_LENGTH_M, Vec2
from v2engine.match import GOAL_CENTER_Y, _step_ball
from v2engine.movement import PlayerState
from v2engine.possession import pressure

GOAL = Vec2(PITCH_LENGTH_M, GOAL_CENTER_Y)


def _player(name: str = "P", team: str = "home", position: Vec2 = Vec2(50.0, 34.0),
            attributes: dict[str, int] | None = None) -> PlayerState:
    return PlayerState(name=name, team=team, poste="MC", position=position, velocity=Vec2(0.0, 0.0), pace=60,
                       acceleration=60, stamina=60, home_target=position, attributes=attributes)


def _marked(dribbling: int, **extra: int) -> tuple[PlayerState, list[PlayerState]]:
    """Porteur de Dribbling donné, un adversaire à 0,5 m (gêne 0,9)."""
    holder = _player(attributes={"Dribbling": dribbling, **extra})
    return holder, [_player("Adv", "away", holder.position + Vec2(0.5, 0.0))]


def _observed_loss(holder: PlayerState, opponents: list[PlayerState], seconds: float, trials: int = 10000) -> float:
    DUEL.seed(20260908)
    intervals = round(seconds / DECISION_INTERVAL_S)
    return sum(any(dribble_lost(holder, opponents) for _ in range(intervals)) for _ in range(trials)) / trials


def test_observed_loss_matches_the_estimate_within_a_point_for_two_seconds_at_contact() -> None:
    holder, opponents = _marked(55)
    estimated = dribble_loss_probability(holder, pressure(holder, opponents), 2.0)
    assert 0.15 < estimated < 0.35  # Dribbling 55 au contact : une conduite sur trois n'est pas perdue sur deux secondes
    assert abs(_observed_loss(holder, opponents, 2.0) - estimated) < 0.01


def test_dribbling_acts_on_the_real_outcome() -> None:
    high, opponents = _marked(99)
    low, _ = _marked(11)
    assert _observed_loss(high, opponents, 2.0) < 0.5 * _observed_loss(low, opponents, 2.0)


def test_strength_and_balance_do_not_enter_the_loss_of_a_carry() -> None:
    # point de vigilance du ticket : Strength et Balance restent au tacle (règle R1 de la carte des attributs)
    weak, opponents = _marked(55, Strength=11, Balance=11)
    strong, _ = _marked(55, Strength=99, Balance=99)
    gene = pressure(weak, opponents)
    assert dribble_loss_probability(weak, gene, 2.0) == dribble_loss_probability(strong, gene, 2.0)


def test_a_free_carry_rarely_loses_the_ball_and_the_loss_scales_with_time() -> None:
    holder = _player(attributes={"Dribbling": 55})
    assert dribble_loss_probability(holder, 0.0, 2.0) < 0.03
    gene = 0.9
    one = dribble_loss_probability(holder, gene, 1.0)
    two = dribble_loss_probability(holder, gene, 2.0)
    assert abs((1.0 - one) ** 2 - (1.0 - two)) < 1e-12  # événement par unité de temps : les survies se multiplient
    assert abs(dribble_loss_probability(holder, gene, DRIBBLE_REFERENCE_S) - (1.0 - keep_ball_probability(holder, gene))) < 1e-12


def test_one_function_serves_the_evaluation_and_the_resolution(monkeypatch) -> None:
    # test de garde : changer la chance de garder change l'évaluation de l'option ET le tirage de la perte
    holder, opponents = _marked(55)
    gene = pressure(holder, opponents)
    best = lambda: max(o.value for o in evaluate_options(holder, [holder, *opponents], GOAL, None) if o.kind == "dribble")
    monkeypatch.setattr(decision, "keep_ball_probability", lambda holder, gene: 1.0)
    sure_value = best()
    assert dribble_loss_probability(holder, gene, 0.5) == 0.0 and not any(dribble_lost(holder, opponents) for _ in range(200))
    monkeypatch.setattr(decision, "keep_ball_probability", lambda holder, gene: 0.0)
    assert best() < sure_value
    assert dribble_loss_probability(holder, gene, 0.5) == 1.0 and all(dribble_lost(holder, opponents) for _ in range(200))


def _carry(monkeypatch, lost: bool) -> tuple[BallState, PlayerState]:
    holder = _player("Porteur", attributes={"Dribbling": 55})
    other = _player("Adv", "away", Vec2(55.0, 34.0))
    holder = replace(holder, velocity=Vec2(5.0, 0.0))
    ball = BallState(position=holder.position, velocity=Vec2(0.0, 0.0), holder="Porteur")
    monkeypatch.setattr("v2engine.match.choose_action", lambda *args: Action("dribble", 1.0, point=Vec2(58.0, 34.0)))
    monkeypatch.setattr("v2engine.match.dribble_lost", lambda *args, **kwargs: lost)
    _step_ball(ball, 0.1, [holder, other], now_s=1.0)
    return ball, holder


def test_a_lost_carry_frees_the_ball_and_bans_the_carrier_for_a_moment(monkeypatch) -> None:
    ball, holder = _carry(monkeypatch, lost=True)
    assert ball.holder is None and ball.dribble is None
    assert ball.velocity.length() >= 1.0  # jamais collé au pied
    assert ball.position.distance_to(holder.position) < 1.0
    assert ball.control_ban_until_s["Porteur"] > 1.0 and ball.last_toucher == "Porteur"


def test_a_kept_carry_goes_on_as_before(monkeypatch) -> None:
    ball, _ = _carry(monkeypatch, lost=False)
    assert ball.holder == "Porteur" and ball.dribble == ("Porteur", Vec2(58.0, 34.0))


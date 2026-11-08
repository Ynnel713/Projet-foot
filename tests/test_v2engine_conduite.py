"""Tests du moteur V2, tickets v2-realisme/04a et 04b : le risque de perdre le ballon en conduisant est le même à l'évaluation
(`decision.keep_ball_probability`) et à la résolution (`decision.dribble_lost`, un tirage par intervalle de décision).
Voir .scratch/v2-realisme/issues/04a-conduite-risque-unifie.md. Ticket 04b : où va le ballon perdu (dépossession
au contact, sinon touche trop longue), `decision.lost_carry_outcome`."""

from __future__ import annotations

import math
from dataclasses import replace

from v2engine import decision
from v2engine.ball_state import BallState
from v2engine.decision import (DECISION_INTERVAL_S, DISPOSSESSION_RADIUS_M, DRIBBLE_REFERENCE_S, LONG_TOUCH_DEG, LONG_TOUCH_M,
                               Action, dribble_loss_probability, dribble_lost, evaluate_options, keep_ball_probability,
                               lost_carry_outcome)
from v2engine.flux import DUEL, PASSE
from v2engine.geometry import PITCH_LENGTH_M, Vec2
from v2engine.match import GOAL_CENTER_Y, TACKLE_RADIUS_M, _step_ball
from v2engine.movement import PlayerState
from v2engine.possession import BALL_FRICTION_PER_S, BALL_STOPPED_MPS, pressure

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



# --- Ticket v2-realisme/04b : où va le ballon perdu ---------------------------------------------------------------

HEADING = Vec2(1.0, 0.0)


def _outcomes(holder: PlayerState, opponents: list[PlayerState], trials: int = 2000) -> list[tuple[PlayerState | None, Vec2 | None]]:
    DUEL.seed(20261108)
    return [lost_carry_outcome(holder, opponents, HEADING) for _ in range(trials)]


def _rest_distance(velocity: Vec2) -> float:
    """Distance à laquelle un ballon lancé à `velocity` s'arrête (freinage du moteur, arrêt sous `BALL_STOPPED_MPS`)."""
    return (velocity.length() - BALL_STOPPED_MPS) / -math.log(BALL_FRICTION_PER_S)


def test_the_dispossession_reach_is_the_tackle_reach() -> None:
    assert DISPOSSESSION_RADIUS_M == TACKLE_RADIUS_M


def test_without_an_opponent_in_contact_the_ball_is_never_taken_and_runs_ahead_within_the_bounds() -> None:
    holder = _player(attributes={"Dribbling": 55})
    for rivals in ([], [_player("Adv", "away", holder.position + Vec2(1.6, 0.0))], [_player("Adv", "away", holder.position + Vec2(3.0, 0.0))]):
        for taker, velocity in _outcomes(holder, rivals):
            assert taker is None and velocity is not None
            assert LONG_TOUCH_M[0] - 1e-9 <= _rest_distance(velocity) <= LONG_TOUCH_M[1] + 1e-9
            assert abs(math.degrees(math.atan2(velocity.y, velocity.x))) <= LONG_TOUCH_DEG + 1e-9


def test_in_contact_both_outcomes_happen_and_the_share_follows_the_pressure() -> None:
    holder = _player(attributes={"Dribbling": 55})
    for gap in (0.5, 1.4):
        rival = _player("Adv", "away", holder.position + Vec2(gap, 0.0))
        outcomes = _outcomes(holder, [rival], trials=5000)
        taken = sum(taker is rival for taker, _ in outcomes) / len(outcomes)
        assert 0.0 < taken < 1.0
        assert abs(taken - pressure(holder, [rival])) < 0.03  # 0,90 à 0,5 m, 0,72 à 1,4 m
        assert all((taker is None) == (velocity is not None) for taker, velocity in outcomes)


def test_the_nearest_opponent_in_contact_takes_the_ball() -> None:
    holder = _player()
    near, far = _player("Proche", "away", holder.position + Vec2(0.4, 0.0)), _player("Loin", "away", holder.position + Vec2(1.2, 0.0))
    takers = {taker.name for taker, _ in _outcomes(holder, [far, near]) if taker is not None}
    assert takers == {"Proche"}


def test_the_lost_ball_reads_no_attribute_and_no_other_stream() -> None:
    # point de vigilance du 04a (réserve A4) : ni Composure, ni First Touch, ni vitesse de course, ni le flux PASSE
    rival = lambda: [_player("Adv", "away", Vec2(50.8, 34.0))]
    weak = _player(attributes={"Composure": 11, "First Touch": 11, "Dribbling": 55})
    strong = replace(_player(attributes={"Composure": 99, "First Touch": 99, "Dribbling": 55}), velocity=Vec2(7.0, 0.0))
    passe_before = PASSE.getstate()
    summary = lambda holder: [(taker is not None, velocity) for taker, velocity in _outcomes(holder, rival(), 200)]
    assert summary(weak) == summary(strong) and {kept for kept, _ in summary(weak)} == {True, False}
    assert PASSE.getstate() == passe_before


def _lost_carry_with_rival_at(gap: float, monkeypatch) -> tuple[BallState, PlayerState, PlayerState]:
    holder = replace(_player("Porteur", attributes={"Dribbling": 55}), velocity=Vec2(5.0, 0.0))
    rival = _player("Adv", "away", holder.position + Vec2(gap, 0.0))
    ball = BallState(position=holder.position, velocity=Vec2(0.0, 0.0), holder="Porteur")
    monkeypatch.setattr("v2engine.match.choose_action", lambda *args: Action("dribble", 1.0, point=Vec2(58.0, 34.0)))
    monkeypatch.setattr("v2engine.match.dribble_lost", lambda *args, **kwargs: True)
    DUEL.seed(1)
    _step_ball(ball, 0.1, [holder, rival], now_s=1.0)
    return ball, holder, rival


def test_a_dispossession_hands_the_ball_to_the_opponent_like_a_won_tackle(monkeypatch) -> None:
    monkeypatch.setattr("v2engine.match.lost_carry_outcome", lambda holder, rivals, heading: (rivals[0], None))
    ball, _, _ = _lost_carry_with_rival_at(0.3, monkeypatch)
    assert ball.holder == "Adv" and ball.receiving and ball.dribble is None
    assert ball.velocity == Vec2(0.0, 0.0) and ball.next_decision_s > 1.0


def test_a_long_touch_leaves_the_ball_free_ahead_of_the_carrier(monkeypatch) -> None:
    ball, holder, _ = _lost_carry_with_rival_at(6.0, monkeypatch)
    assert ball.holder is None and ball.control_ban_until_s["Porteur"] > 1.0
    assert ball.velocity.x > 0.0 and ball.position.x > holder.position.x  # devant lui, vers l'avant

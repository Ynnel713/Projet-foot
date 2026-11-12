"""Tests du moteur V2, Phase 5, ticket v2-cerveau-joueurs/01 (décision du porteur). Voir
.scratch/v2-cerveau-joueurs/issues/01-decision-du-porteur.md, critères d'acceptation."""

from __future__ import annotations

import random

from v2engine.ball_state import BallState
from v2engine.decision import (
    DECISION_INTERVAL_S,
    key_pass_spot_probability,
    vision_range_m,
    visible_teammates,
    best_choice_probability,
    choose_action,
    evaluate_options,
)
from v2engine.geometry import PITCH_LENGTH_M, Vec2
from v2engine.match import GOAL_CENTER_Y, _step_ball, _step_player
from v2engine.movement import PlayerState, max_speed_mps
from v2engine.possession import reception_delay_s

GOAL = Vec2(PITCH_LENGTH_M, GOAL_CENTER_Y)


def _player(name: str = "P", team: str = "home", poste: str = "BU", position: Vec2 = Vec2(50.0, 34.0),
            attributes: dict[str, int] | None = None) -> PlayerState:
    return PlayerState(
        name=name, team=team, poste=poste, position=position, velocity=Vec2(0.0, 0.0),
        pace=60, acceleration=60, stamina=60, home_target=position, attributes=attributes,
    )


def _kinds(options) -> set[str]:
    return {o.kind for o in options}


def test_decisions_curve_matches_validated_points() -> None:
    assert abs(best_choice_probability(99) - 0.95) < 1e-9
    assert abs(best_choice_probability(55) - 0.70) < 1e-9
    assert abs(best_choice_probability(11) - 0.45) < 1e-9


def test_shot_option_exists_up_to_30_m_and_not_beyond() -> None:
    at_25 = _player(position=Vec2(PITCH_LENGTH_M - 25.0, GOAL_CENTER_Y))
    at_32 = _player(position=Vec2(PITCH_LENGTH_M - 32.0, GOAL_CENTER_Y))
    assert "shot" in _kinds(evaluate_options(at_25, [at_25], GOAL, None))
    assert "shot" not in _kinds(evaluate_options(at_32, [at_32], GOAL, None))


def test_pressure_lowers_shot_and_dribble_values() -> None:
    holder = _player(position=Vec2(PITCH_LENGTH_M - 15.0, GOAL_CENTER_Y))
    marker = _player("Marqueur", team="away", position=holder.position + Vec2(0.5, 0.0))
    def best(options) -> dict:  # la meilleure conduite (un dict par genre garderait la dernière direction, de côté)
        values = {}
        for o in options:
            values[o.kind] = max(o.value, values.get(o.kind, o.value))
        return values
    free = best(evaluate_options(holder, [holder], GOAL, None))
    pressed = best(evaluate_options(holder, [holder, marker], GOAL, None))
    assert pressed["shot"] < free["shot"]
    assert pressed["dribble"] < free["dribble"]


def test_pass_prefers_open_teammate_closer_to_goal_over_nearest_marked_one(monkeypatch) -> None:
    monkeypatch.setattr("v2engine.flux.PERCEPTION.random", lambda: 0.0)  # la passe clé est repérée (Vision, ticket 02)
    holder = _player(position=Vec2(40.0, 34.0))
    near_marked = _player("Proche", position=Vec2(43.0, 34.0))
    marker = _player("Marqueur", team="away", position=Vec2(43.5, 34.0))
    far_open = _player("Demarque", position=Vec2(60.0, 20.0))
    options = evaluate_options(holder, [holder, near_marked, marker, far_open], GOAL, None)
    assert next(o for o in options if o.kind == "pass").target.name == "Demarque"


def test_high_decisions_picks_best_option_more_often_than_low() -> None:
    def best_rate(decisions: int) -> float:
        holder = _player(position=Vec2(PITCH_LENGTH_M - 9.0, GOAL_CENTER_Y), attributes={"Decisions": decisions})
        mate = _player("Coequipier", position=Vec2(60.0, 20.0))
        keeper = _player("Gardien", "away", "GK", Vec2(PITCH_LENGTH_M - 1.0, GOAL_CENTER_Y))
        players = [holder, mate, keeper]
        best = max(evaluate_options(holder, players, GOAL, keeper), key=lambda o: o.value).kind
        random.seed(20260923)
        return sum(choose_action(holder, players, GOAL, keeper).kind == best for _ in range(2000)) / 2000

    # un choix nettement meilleur (tir à 9 m face à un gardien sur sa ligne, environ 1,6 fois la meilleure conduite ;
    # à 6 m sans gardien jusqu'au ticket v2-realisme/05e, où la chance physique d'un but vide écrasait les autres
    # options) : vu par presque tous les bons décideurs ; un très mauvais décideur s'en écarte souvent, l'erreur étant
    # calée pour que la courbe validée tienne en moyenne sur un match (ticket v2-collectif/33 ; mesuré le 10/11/2026 sur
    # cette scène seule : 99,4 % à 95, 57 % à 20)
    assert best_rate(95) >= 0.95 and best_rate(95) >= best_rate(20) + 0.4


def test_close_options_split_low_decisions_far_more_than_high() -> None:
    # deux passes latérales proches (ticket 33) : le très bon joueur prend presque toujours la meilleure, le faible hésite
    def best_rate(decisions: int) -> float:
        holder = _player(position=Vec2(40.0, 34.0), attributes={"Decisions": decisions})
        players = [holder, _player("B", position=Vec2(40.0, 46.0)), _player("A", position=Vec2(40.0, 22.0)),
                   _player("T", position=Vec2(55.0, 26.0)), _player("Def", team="away", position=Vec2(75.0, 30.0))]
        random.seed(20260923)
        picks = [choose_action(holder, players, GOAL, None) for _ in range(2000)]
        return sum(a.best for a in picks) / 2000

    assert best_rate(95) > best_rate(20) + 0.2


def test_lone_holder_dribbles_toward_goal_at_reduced_speed(monkeypatch) -> None:
    monkeypatch.setattr("v2engine.flux.PERCEPTION.gauss", lambda mu, sigma: 0.0)  # perception exacte : droit au but
    holder = _player("Seul", position=Vec2(30.0, 34.0), attributes={"Decisions": 99})  # droit au but, le meilleur choix
    ball = BallState(position=holder.position, velocity=Vec2(0.0, 0.0), holder="Seul")
    _step_ball(ball, 0.1, [holder], now_s=0.0)
    assert ball.holder == "Seul"

    for _ in range(60):  # 6 s : vitesse de croisière atteinte
        holder = _step_player(holder, ball, 0.1, 0.0)
    assert holder.position.x > 30.0
    assert holder.velocity.length() <= 0.85 * max_speed_mps(60) + 1e-9


def test_holder_keeps_his_choice_until_next_decision(monkeypatch) -> None:
    holder = _player("Porteur")
    mate = _player("Coequipier", position=Vec2(70.0, 34.0))
    ball = BallState(position=holder.position, velocity=Vec2(0.0, 0.0), holder="Porteur",
                     next_decision_s=DECISION_INTERVAL_S)
    monkeypatch.setattr("v2engine.match.choose_action", lambda *args: (_ for _ in ()).throw(AssertionError("décision trop tôt")))
    _step_ball(ball, 0.1, [holder, mate], now_s=DECISION_INTERVAL_S - 0.1)
    assert ball.holder == "Porteur"


def test_heavily_pressed_holder_at_15_m_prefers_open_pass_over_shot() -> None:
    holder = _player(position=Vec2(PITCH_LENGTH_M - 15.0, GOAL_CENTER_Y + 10.0))
    # ticket v2-realisme/18g : marqueur à 0,8 m (gêne 0,84), et non plus 0,3 m, physiquement impossible (deux joueurs de
    # 0,3 m de rayon se touchent à 0,6 m) : là, il était sur la ligne de toute passe (coupe mesurée 0,75)
    marker = _player("Marqueur", team="away", position=holder.position + Vec2(0.8, 0.0))
    open_mate = _player("Demarque", position=Vec2(PITCH_LENGTH_M - 8.0, GOAL_CENTER_Y))
    options = {o.kind: o.value for o in evaluate_options(holder, [holder, marker, open_mate], GOAL, None)}
    assert options["pass"] > options["shot"]


def test_new_holder_decides_after_his_reception_time_when_winning_the_ball(monkeypatch) -> None:
    holder = _player("Porteur")
    tackler = _player("Tacleur", team="away", position=holder.position + Vec2(0.5, 0.0))
    ball = BallState(position=holder.position, velocity=Vec2(0.0, 0.0), holder="Porteur", next_decision_s=10.0)
    monkeypatch.setattr("v2engine.match.should_attempt_tackle", lambda aggression, dt: True)
    monkeypatch.setattr("v2engine.match.resolve_tackle", lambda tackler, holder: type("W", (), {"won": True})())
    _step_ball(ball, 0.1, [holder, tackler], now_s=3.0)
    # v2-socle/06 : il contrôle et lève la tête avant de décider (temps de réception selon First Touch et pression)
    assert ball.holder == "Tacleur"
    assert ball.next_decision_s == 3.0 + reception_delay_s(tackler, [holder])


# --- Ticket 02 : Vision -----------------------------------------------------------------------------------------


def test_vision_curves_match_validated_points() -> None:
    assert [round(vision_range_m(v), 6) for v in (99, 55, 11)] == [50.0, 30.0, 10.0]
    assert [round(key_pass_spot_probability(v), 6) for v in (99, 55, 11)] == [0.9, 0.5, 0.1]


def test_teammate_beyond_vision_range_is_not_considered_but_nearest_always_is() -> None:
    holder = _player(position=Vec2(20.0, 34.0), attributes={"Vision": 11})  # portée 10 m
    nearest = _player("Proche", position=Vec2(20.0, 50.0))  # 16 m : hors portée, mais le plus proche
    far = _player("Loin", position=Vec2(20.0, 60.0))
    assert [p.name for p in visible_teammates(holder, [nearest, far], GOAL)] == ["Proche"]


def test_high_vision_plays_long_passes_at_least_twice_as_often_as_low() -> None:
    def long_pass_rate(vision: int) -> float:
        holder = _player(position=Vec2(30.0, 34.0), attributes={"Vision": vision})
        short = _player("Court", position=Vec2(34.0, 30.0))
        long_ = _player("Long", position=Vec2(60.0, 20.0))  # 33 m, gagne ~25 m vers le but
        random.seed(20260923)
        picks = [next(o for o in evaluate_options(holder, [holder, short, long_], GOAL, None) if o.kind == "pass").target.name
                 for _ in range(2000)]
        return picks.count("Long") / len(picks)

    assert long_pass_rate(90) >= 2 * long_pass_rate(30)

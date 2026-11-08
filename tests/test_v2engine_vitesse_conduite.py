"""Tests du moteur V2, ticket v2-realisme/04d : la vitesse balle au pied dépend de Dribbling et baisse au contact d'un adversaire ;
la même fonction (`decision.dribble_speed_factor`) sert à l'évaluation de l'espace atteint et au déplacement du porteur.
Voir .scratch/v2-realisme/issues/04d-vitesse-de-conduite.md."""

from __future__ import annotations

from v2engine import cerveau
from v2engine.ball_state import BallState
from v2engine.decision import CONTACT_SLOWDOWN, dribble_speed_factor, free_point
from v2engine.geometry import Vec2
from v2engine.movement import PlayerState, max_speed_mps, step
from v2engine.possession import pressure


def _p(name: str, team: str = "home", x: float = 50.0, y: float = 34.0, dribbling: int | None = None) -> PlayerState:
    attributes = None if dribbling is None else {"Dribbling": dribbling}
    return PlayerState(name=name, team=team, poste="MC", position=Vec2(x, y), velocity=Vec2(0.0, 0.0), pace=60,
                       acceleration=60, stamina=60, home_target=Vec2(x, y), attributes=attributes)


def test_free_speed_grows_with_dribbling_and_keeps_the_old_value_at_55() -> None:
    low, mid, high = (dribble_speed_factor(_p("H", dribbling=d), 0.0) for d in (11, 55, 99))
    assert low < mid < high
    assert abs(mid - 0.85) < 1e-12  # valeur d'avant le ticket pour un joueur moyen sans adversaire
    assert abs(high - 0.90) < 1e-9 and abs(low - 0.80) < 1e-9


def test_contact_slows_the_carry_in_proportion_to_the_marking() -> None:
    holder = _p("H", dribbling=55)
    free, half, contact = (dribble_speed_factor(holder, g) for g in (0.0, 0.5, 1.0))
    assert free > half > contact
    assert abs(contact - free * (1.0 - CONTACT_SLOWDOWN)) < 1e-12


def test_evaluation_and_movement_use_the_same_speed() -> None:
    holder = _p("H", dribbling=90)
    rival = _p("R", team="away", x=51.0)
    gene = pressure(holder, [rival])
    assert gene > 0.0
    intention = cerveau.think(holder, BallState(position=holder.position, velocity=Vec2(0.0, 0.0), holder="H"),
                              [holder, rival], 1.0, {})
    assert intention.action == "conduire" and intention.intensity == dribble_speed_factor(holder, gene)
    assert intention.intensity < dribble_speed_factor(holder, 0.0)


def test_a_slower_carry_reaches_less_free_space() -> None:
    holder, rival = _p("H"), _p("R", team="away", x=70.0)
    heading = Vec2(1.0, 0.0)
    fast = free_point(holder, [rival], heading, 1.0, 0.95)
    slow = free_point(holder, [rival], heading, 1.0, 0.6)
    assert fast is not None and (slow is None or slow.x <= fast.x)


def _distance_after(holder: PlayerState, seconds: float, factor: float) -> float:
    state, target = holder, Vec2(100.0, 34.0)
    for _ in range(int(seconds / 0.1)):
        state = step(state, 0.1, target, 1.0, speed_factor=factor)
    return state.position.x - holder.position.x


def test_high_dribbling_covers_more_ground_than_low_at_the_same_pace() -> None:
    high, low = _p("A", dribbling=99), _p("B", dribbling=11)
    assert high.pace == low.pace
    assert _distance_after(high, 5.0, dribble_speed_factor(high, 0.0)) > _distance_after(low, 5.0, dribble_speed_factor(low, 0.0))
    assert dribble_speed_factor(high, 0.0) * max_speed_mps(high.pace) <= max_speed_mps(high.pace)  # Pace reste le plafond

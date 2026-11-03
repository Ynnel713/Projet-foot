"""Tests du moteur V2, Phase 4 (tirs et gardien -- jalon : match complet jouable). Voir
docs/PLAN_V2.md, critères d'acceptation. Lecture seule de la V1 : aucun fichier protégé importé."""

from __future__ import annotations

from ligue1sim.clubs import load_clubs
from ligue1sim.season import CLUBS_PATH

from v2engine.ball_state import BallState
from v2engine.geometry import PITCH_LENGTH_M, PITCH_WIDTH_M, Vec2
from v2engine.decision import Action
from v2engine.match import GOAL_CENTER_Y, _step_ball, simulate_match
from v2engine.movement import PlayerState
from v2engine.shooting import shot_probability


def _player(name: str = "P", team: str = "home", poste: str = "BU", position: Vec2 = Vec2(0.0, 0.0),
            attributes: dict[str, int] | None = None) -> PlayerState:
    return PlayerState(
        name=name, team=team, poste=poste, position=position, velocity=Vec2(0.0, 0.0),
        pace=60, acceleration=60, stamina=60, home_target=position, attributes=attributes,
    )


def test_shot_probability_never_binary_even_at_extreme_attribute_gap() -> None:
    lethal_shooter = _player(attributes={"Finishing": 99, "Composure": 99})
    no_keeper_probability = shot_probability(lethal_shooter, keeper=None, distance_m=8.0, goal_center_y=GOAL_CENTER_Y)
    assert 0.0 < no_keeper_probability < 1.0

    helpless_keeper = _player("Gardien", poste="GK", team="away", attributes={"Reflexes": 5, "One on Ones": 5, "Handling": 5})
    assert 0.0 < shot_probability(lethal_shooter, helpless_keeper, distance_m=8.0, goal_center_y=GOAL_CENTER_Y) < 1.0


def test_higher_finishing_and_composure_increase_conversion_at_equal_distance() -> None:
    sharp_shooter = _player(attributes={"Finishing": 90, "Composure": 85})
    poor_shooter = _player(attributes={"Finishing": 20, "Composure": 25})
    keeper = _player("Gardien", poste="GK", team="away", attributes={"Reflexes": 60, "One on Ones": 60, "Handling": 60})

    assert shot_probability(sharp_shooter, keeper, distance_m=10.0, goal_center_y=GOAL_CENTER_Y) > shot_probability(
        poor_shooter, keeper, distance_m=10.0, goal_center_y=GOAL_CENTER_Y
    )


def test_higher_keeper_reflexes_and_one_on_ones_reduce_conversion_at_equal_shot() -> None:
    shooter = _player(attributes={"Finishing": 70, "Composure": 65})
    great_keeper = _player("Costaud", poste="GK", team="away", attributes={"Reflexes": 90, "One on Ones": 90, "Handling": 85})
    poor_keeper = _player("Fragile", poste="GK", team="away", attributes={"Reflexes": 20, "One on Ones": 20, "Handling": 25})

    assert shot_probability(shooter, great_keeper, distance_m=10.0, goal_center_y=GOAL_CENTER_Y) < shot_probability(
        shooter, poor_keeper, distance_m=10.0, goal_center_y=GOAL_CENTER_Y
    )


def test_scored_shot_counts_only_when_the_ball_reaches_the_goal_line(monkeypatch) -> None:
    # Un tir ne compte pas au départ : le ballon part vers le but et le but est sifflé à son arrivée, jamais avant.
    shooter = _player("Buteur", position=Vec2(PITCH_LENGTH_M - 8.0, GOAL_CENTER_Y))
    keeper = _player("Gardien", poste="GK", team="away", position=Vec2(PITCH_LENGTH_M, GOAL_CENTER_Y))
    ball = BallState(position=shooter.position, velocity=Vec2(0.0, 0.0), holder="Buteur")

    monkeypatch.setattr("v2engine.match.should_attempt_tackle", lambda aggression, dt: False)
    monkeypatch.setattr("v2engine.match.choose_action", lambda *args: Action("shot", 1.0))  # issue du tir seule testée ici
    monkeypatch.setattr("v2engine.match.attempt_shot", lambda shooter, keeper, distance_m, goal_center_y: True)
    assert _step_ball(ball, 0.1, [shooter, keeper]) is None  # départ du tir : pas encore de but
    assert ball.holder is None
    assert ball.position == shooter.position

    results, positions = [], []
    for _ in range(20):  # 8 m à 30 m/s : trois pas de 0,1 s
        results.append(_step_ball(ball, 0.1, [shooter, keeper]))
        positions.append(ball.position)
        if results[-1] is not None:
            break
    assert results[-1] == "home"
    assert results[:-1] == [None] * (len(results) - 1)
    assert 2 <= len(results) <= 4  # ni instantané, ni interminable
    assert all(a.x < b.x for a, b in zip(positions, positions[1:-1]))  # le ballon avance vers le but adverse
    assert positions[-2].x > shooter.position.x
    assert ball.position == Vec2(PITCH_LENGTH_M / 2.0, PITCH_WIDTH_M / 2.0)  # le jeu repart du centre


def test_ball_snapshot_names_the_holder() -> None:
    from v2engine.trace import BallSnapshot

    assert BallSnapshot(position=Vec2(1.0, 2.0)).holder is None
    assert BallSnapshot(position=Vec2(1.0, 2.0), holder="Buteur").holder == "Buteur"


def test_missed_shot_gives_ball_to_the_opposing_keeper(monkeypatch) -> None:
    shooter = _player("Buteur", position=Vec2(PITCH_LENGTH_M - 8.0, GOAL_CENTER_Y))
    keeper = _player("Gardien", poste="GK", team="away", position=Vec2(PITCH_LENGTH_M, GOAL_CENTER_Y))
    ball = BallState(position=shooter.position, velocity=Vec2(0.0, 0.0), holder="Buteur")

    monkeypatch.setattr("v2engine.match.should_attempt_tackle", lambda aggression, dt: False)
    monkeypatch.setattr("v2engine.match.choose_action", lambda *args: Action("shot", 1.0))  # issue du tir seule testée ici
    monkeypatch.setattr("v2engine.match.attempt_shot", lambda shooter, keeper, distance_m, goal_center_y: False)
    scoring_team = _step_ball(ball, 0.1, [shooter, keeper])

    assert scoring_team is None
    assert ball.holder == "Gardien"


def test_full_short_match_exposes_a_score() -> None:
    clubs = load_clubs(CLUBS_PATH, "Ligue 1")
    trace = simulate_match(clubs[2], clubs[3], duration_minutes=5.0, tick_seconds=0.2, record_every=10)

    assert trace.home_goals >= 0
    assert trace.away_goals >= 0

"""Tests du moteur V2, Phase 5, ticket v2-cerveau-joueurs/03 (Off the Ball : appels et démarquage). Voir
.scratch/v2-cerveau-joueurs/issues/03-off-the-ball-appels.md, critères d'acceptation."""

from __future__ import annotations

import random

from v2engine.ball_state import BallState
from v2engine.geometry import Vec2
from v2engine.match import _step_player
from v2engine.movement import PlayerState
from v2engine.off_ball import best_space_probability, choose_space, search_radius_m


def _player(name: str = "P", team: str = "home", poste: str = "MC", position: Vec2 = Vec2(50.0, 34.0),
            attributes: dict[str, int] | None = None) -> PlayerState:
    return PlayerState(
        name=name, team=team, poste=poste, position=position, velocity=Vec2(0.0, 0.0),
        pace=60, acceleration=60, stamina=60, home_target=position, attributes=attributes,
    )


def test_off_the_ball_curves_match_validated_points() -> None:
    assert [round(search_radius_m(v), 6) for v in (99, 55, 11)] == [15.0, 8.0, 2.0]
    assert [round(best_space_probability(v), 6) for v in (99, 55, 11)] == [0.95, 0.70, 0.45]


def test_space_stays_within_search_radius_mostly_forward() -> None:
    runner = _player(attributes={"Off the Ball": 99})
    random.seed(20260923)
    for _ in range(200):
        target = choose_space(runner, [_player("Adv", team="away", position=Vec2(52.0, 34.0))], forward=1.0)
        assert target.distance_to(runner.home_target) <= 15.0 * 1.2 + 1e-9  # diagonale de la grille
        assert -5.0 - 1e-9 <= target.x - runner.home_target.x <= 10.0 + 1e-9  # 1/3 en arrière, 2/3 en avant


def test_teammates_of_the_holder_no_longer_chase_the_ball() -> None:
    holder = _player("Porteur", position=Vec2(50.0, 34.0))
    mate = _player("Coequipier", position=Vec2(55.0, 34.0))
    opponent = _player("Adv", team="away", position=Vec2(56.0, 34.0))
    ball = BallState(position=holder.position, velocity=Vec2(0.0, 0.0), holder="Porteur")
    runs: dict = {}
    players = [holder, mate, opponent]
    random.seed(1)
    _step_player(mate, ball, 0.1, 0.0, players, runs)
    assert runs["Coequipier"][0] != ball.position  # il vise un espace, pas le ballon


def test_high_off_the_ball_finds_more_space_than_low() -> None:
    opponents = [_player(f"Adv{i}", team="away", position=Vec2(50.0 + dx, 34.0 + dy))
                 for i, (dx, dy) in enumerate([(2, 0), (-2, 3), (0, -3), (5, 5), (6, -4)])]

    def mean_space(note: int) -> float:
        runner = _player(attributes={"Off the Ball": note})
        random.seed(20260923)
        targets = [choose_space(runner, opponents, forward=1.0) for _ in range(500)]
        return sum(min(t.distance_to(o.position) for o in opponents) for t in targets) / len(targets)

    assert mean_space(90) >= 1.3 * mean_space(30)

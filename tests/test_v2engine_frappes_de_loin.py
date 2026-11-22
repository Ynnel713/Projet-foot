"""Tests du moteur V2, ticket v2-realisme/18m (sélection des frappes de loin). Voir
.scratch/v2-realisme/issues/18m-selection-des-frappes-de-loin.md, critères d'acceptation."""

from __future__ import annotations

import random

from v2engine.decision import LONG_SHOT_MARGIN, choose_action, evaluate_options
from v2engine.geometry import PITCH_LENGTH_M, Vec2
from v2engine.match import GOAL_CENTER_Y
from v2engine.movement import PlayerState

GOAL = Vec2(PITCH_LENGTH_M, GOAL_CENTER_Y)


def _player(name: str, team: str = "home", poste: str = "BU", position: Vec2 = Vec2(50.0, 34.0)) -> PlayerState:
    return PlayerState(name=name, team=team, poste=poste, position=position, velocity=Vec2(0.0, 0.0), pace=60,
                       acceleration=60, stamina=60, home_target=position, attributes={"Decisions": 99})


def _scene(depth_m: float, free_mate: bool) -> tuple[PlayerState, list[PlayerState], PlayerState]:
    """Porteur dans l'axe à `depth_m` de la ligne de but, un presseur sur le côté, deux centraux écartés (ligne de tir
    libre), le gardien ; avec ou sans un coéquipier libre au point de penalty décalé (en jeu)."""
    holder = _player("Porteur", position=Vec2(PITCH_LENGTH_M - depth_m, GOAL_CENTER_Y))
    keeper = _player("Gardien", "away", "GK", Vec2(PITCH_LENGTH_M - 1.0, GOAL_CENTER_Y))
    rivals = [keeper, _player("Presseur", "away", position=holder.position + Vec2(2.0, 2.5)),
              _player("DC1", "away", position=Vec2(PITCH_LENGTH_M - 11.0, GOAL_CENTER_Y + 5.0)),
              _player("DC2", "away", position=Vec2(PITCH_LENGTH_M - 11.0, GOAL_CENTER_Y - 4.0))]
    mates = [_player("Libre", position=Vec2(PITCH_LENGTH_M - 11.5, GOAL_CENTER_Y - 8.0))] if free_mate else []
    return holder, [holder, *rivals, *mates], keeper


def _exact(monkeypatch) -> None:
    monkeypatch.setattr("v2engine.flux.PERCEPTION.gauss", lambda mu, sigma: 0.0)  # perception exacte


def _best(holder, players, keeper) -> dict[str, float]:
    values: dict[str, float] = {}
    for o in evaluate_options(holder, players, GOAL, keeper):
        values[o.kind] = max(o.value, values.get(o.kind, o.value))
    return values


def _ring(mate: bool) -> tuple[PlayerState, list[PlayerState], PlayerState]:
    """Porteur dans l'axe à 20 m, entouré à 3 m (dans son dos, sur les côtés, en biais devant) : la conduite ne mène à
    rien, la ligne de tir reste libre ; avec ou sans un coéquipier démarqué loin (passe qui vaut moins que la frappe)."""
    holder = _player("Porteur", position=Vec2(PITCH_LENGTH_M - 20.0, GOAL_CENTER_Y))
    keeper = _player("Gardien", "away", "GK", Vec2(PITCH_LENGTH_M - 1.0, GOAL_CENTER_Y))
    ring = [_player(f"R{i}", "away", position=holder.position + Vec2(dx, dy))
            for i, (dx, dy) in enumerate(((-3.0, 0.0), (0.0, 3.0), (0.0, -3.0), (2.1, 2.1), (2.1, -2.1)))]
    mates = [_player("Libre", position=Vec2(PITCH_LENGTH_M - 18.0, GOAL_CENTER_Y - 14.0))] if mate else []
    return holder, [holder, keeper, *ring, *mates], keeper


def test_margin_is_the_validated_value() -> None:
    # 0,05 au 18m, ramenée à 0 au 05l : elle compensait une frappe surévaluée (chance d'un tir propre deux fois la table)
    assert LONG_SHOT_MARGIN == 0.0


def test_a_long_shot_slightly_better_than_continuing_is_taken_only_without_margin(monkeypatch) -> None:
    _exact(monkeypatch)
    holder, players, keeper = _ring(mate=True)
    values = _best(holder, players, keeper)
    gap = values["shot"] - max(values["pass"], values["dribble"])
    assert 0.0 < gap < 0.01  # la frappe vaut un peu plus que la passe et la conduite, pas nettement plus
    assert choose_action(holder, players, GOAL, keeper).kind == "shot"
    monkeypatch.setattr("v2engine.decision.LONG_SHOT_MARGIN", 0.01)
    action = choose_action(holder, players, GOAL, keeper)
    assert action.kind != "shot"
    assert action.best and action.best_kind == action.kind  # le meilleur choix se juge avec la même règle


def test_at_20_m_without_a_better_option_he_still_shoots(monkeypatch) -> None:
    _exact(monkeypatch)
    holder, players, keeper = _ring(mate=False)
    values = _best(holder, players, keeper)
    assert values["shot"] - values["dribble"] > LONG_SHOT_MARGIN
    action = choose_action(holder, players, GOAL, keeper)
    assert action.kind == "shot" and action.best


def test_margin_does_not_apply_inside_the_box(monkeypatch) -> None:
    _exact(monkeypatch)
    holder, players, keeper = _scene(15.0, free_mate=False)
    monkeypatch.setattr("v2engine.decision.LONG_SHOT_MARGIN", 1.0)  # marge absurde : sans effet dans la surface
    assert choose_action(holder, players, GOAL, keeper).kind == "shot"


def test_margin_does_not_apply_to_a_direct_free_kick(monkeypatch) -> None:
    _exact(monkeypatch)
    holder, players, keeper = _ring(mate=True)
    monkeypatch.setattr("v2engine.decision.LONG_SHOT_MARGIN", 0.01)
    assert choose_action(holder, players, GOAL, keeper, set_piece=True).kind == "shot"


def test_long_shots_are_rarer_with_a_margin_under_noisy_perception(monkeypatch) -> None:
    # perception brouillée (Decisions 62) : une marge positive baisse la part des frappes, sans les supprimer
    holder, players, keeper = _ring(mate=True)
    holder.attributes["Decisions"] = 62

    def shot_rate(margin: float) -> float:
        monkeypatch.setattr("v2engine.decision.LONG_SHOT_MARGIN", margin)
        random.seed(20260923)
        return sum(choose_action(holder, players, GOAL, keeper).kind == "shot" for _ in range(1000)) / 1000

    without, with_margin = shot_rate(0.0), shot_rate(0.02)
    assert with_margin < without - 0.15 and with_margin > 0.0

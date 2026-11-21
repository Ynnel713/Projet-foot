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


def test_margin_is_the_validated_value() -> None:
    assert LONG_SHOT_MARGIN == 0.05


def test_at_20_m_with_a_free_teammate_in_the_box_he_passes_instead_of_shooting(monkeypatch) -> None:
    _exact(monkeypatch)
    holder, players, keeper = _scene(20.0, free_mate=True)
    values = _best(holder, players, keeper)
    # la frappe vaut un peu plus que la passe (avant le ticket, il frappait), mais pas nettement plus
    assert 0.0 < values["shot"] - max(values["pass"], values["dribble"]) < LONG_SHOT_MARGIN
    monkeypatch.setattr("v2engine.decision.LONG_SHOT_MARGIN", 0.0)
    assert choose_action(holder, players, GOAL, keeper).kind == "shot"
    monkeypatch.setattr("v2engine.decision.LONG_SHOT_MARGIN", 0.05)
    action = choose_action(holder, players, GOAL, keeper)
    assert action.kind == "pass" and action.target.name == "Libre"
    assert action.best and action.best_kind == "pass"  # le meilleur choix se juge avec la même règle


def test_at_20_m_without_a_better_option_he_still_shoots(monkeypatch) -> None:
    _exact(monkeypatch)
    # porteur entouré à 3 m (dans son dos, sur les côtés, en biais devant), sans coéquipier : la conduite ne mène à rien,
    # la ligne de tir reste libre
    holder = _player("Porteur", position=Vec2(PITCH_LENGTH_M - 20.0, GOAL_CENTER_Y))
    keeper = _player("Gardien", "away", "GK", Vec2(PITCH_LENGTH_M - 1.0, GOAL_CENTER_Y))
    ring = [_player(f"R{i}", "away", position=holder.position + Vec2(dx, dy))
            for i, (dx, dy) in enumerate(((-3.0, 0.0), (0.0, 3.0), (0.0, -3.0), (2.1, 2.1), (2.1, -2.1)))]
    players = [holder, keeper, *ring]
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
    holder, players, keeper = _scene(20.0, free_mate=True)
    assert choose_action(holder, players, GOAL, keeper, set_piece=True).kind == "shot"


def test_long_shots_are_rarer_with_the_margin_under_noisy_perception(monkeypatch) -> None:
    # perception brouillée (Decisions 62) : la marge baisse nettement la part des frappes, sans les supprimer
    holder, players, keeper = _scene(20.0, free_mate=True)
    holder.attributes["Decisions"] = 62

    def shot_rate(margin: float) -> float:
        monkeypatch.setattr("v2engine.decision.LONG_SHOT_MARGIN", margin)
        random.seed(20260923)
        return sum(choose_action(holder, players, GOAL, keeper).kind == "shot" for _ in range(1000)) / 1000

    before, after = shot_rate(0.0), shot_rate(LONG_SHOT_MARGIN)
    # mesuré le 21/11/2026 sur cette scène : 54 % sans marge, 19 % à 0,05 (36 % au premier essai à 0,03)
    assert after < before - 0.15 and after > 0.0

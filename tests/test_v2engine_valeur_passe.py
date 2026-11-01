"""Valeur future d'une passe (ticket v2-collectif/13) : le porteur compte aussi la meilleure passe suivante du
receveur, vers un coéquipier qu'il voit lui-même ; jamais le retour vers lui ; pas en contre-attaque."""

from __future__ import annotations

import random

from v2engine.decision import CONSERVATION, CONTRE_ATTAQUE, PASS_WEIGHT, choose_action, evaluate_options
from v2engine.geometry import Vec2
from v2engine.movement import PlayerState
from v2engine.possession import pass_success_probability

GOAL = Vec2(105.0, 34.0)


def _p(name: str, x: float, y: float, team: str = "home", **attributes: int) -> PlayerState:
    return PlayerState(name=name, team=team, poste="MC", position=Vec2(x, y), velocity=Vec2(0.0, 0.0), pace=60,
                       acceleration=60, stamina=60, home_target=Vec2(x, y),
                       attributes={k.replace("_", " "): v for k, v in attributes.items()} or None)


def _scene(**holder_attributes: int) -> list[PlayerState]:
    """Deux receveurs latéraux symétriques (A, B ; à égalité, B passe en premier) ; un coéquipier entre les lignes
    (T, à 15,6 m du porteur et 14 m plus près du but : pas une passe clé, il le voit toujours à Vision moyenne), servi
    librement depuis A ; un adversaire coupe la passe directe du porteur vers T, un autre celle de B vers T."""
    holder = _p("H", 40, 34, **holder_attributes)
    return [holder, _p("B", 40, 46), _p("A", 40, 22), _p("T", 55, 26),
            _p("Coupe", 47.5, 36, team="away"), _p("Direct", 47.5, 30, team="away"),
            _p("Def", 75, 30, team="away"), _p("Def2", 75, 40, team="away")]


def _pass(players: list[PlayerState], mode: str | None = None):
    return next(o for o in evaluate_options(players[0], players, GOAL, None, mode) if o.kind == "pass")


def test_lateral_pass_that_opens_a_next_pass_is_chosen_far_more_often() -> None:
    assert _pass(_scene()).target.name == "A"
    players = _scene(Decisions=55)
    random.seed(20260923)
    picks = [choose_action(players[0], players, GOAL, None) for _ in range(2000)]
    to = {name: sum(a.kind == "pass" and a.target.name == name for a in picks) / 2000 for name in ("A", "B")}
    # critère C1 ; seul le meilleur receveur est une option, d'où B à 0 : la discrimination vient de l'assertion du
    # début (sans la suite, A et B sont symétriques et l'égalité désigne B, premier de la liste)
    assert to["A"] >= 0.65 and to["B"] <= 0.35


def test_without_a_better_next_pass_the_value_is_the_one_before_the_ticket() -> None:
    # le receveur n'a que le porteur comme suite, exclu (pas d'aller-retour) : la suite vaut la position atteinte,
    # dans l'échelle du mode -- hors transition comme en conservation (sûreté d'abord, ticket 11)
    holder, mate = _p("H", 40, 34), _p("M", 40, 22)
    gain = holder.position.distance_to(GOAL) - mate.position.distance_to(GOAL)
    for mode, (fixed, progressive) in ((None, (0.3, 0.7)), (CONSERVATION, (0.7, 0.3))):
        expected = PASS_WEIGHT * pass_success_probability(holder, mate, []) * (fixed + progressive * (0.5 + gain / 40.0))
        assert abs(_pass([holder, mate], mode).value - expected) < 1e-12
    assert _pass([holder, mate, _p("T", 60, 26)]).value > _pass([holder, mate]).value


def test_low_vision_holder_does_not_read_the_next_pass_of_the_receiver() -> None:
    def option(vision: int, with_t: bool):
        return _pass([p for p in _scene(Vision=vision) if with_t or p.name != "T"])
    assert option(11, True).value == option(11, False).value  # T à 15,6 m, au-delà des 10 m de sa portée
    assert option(99, True).target.name == "A" and option(99, True).value > option(99, False).value


def test_the_next_pass_is_judged_on_the_receiver_passing() -> None:
    def value(passing: int) -> float:
        players = _scene()
        players[2] = _p("A", 40, 22, Passing=passing)
        return _pass(players).value
    assert value(99) > value(11)


def test_no_follow_up_in_a_counter_attack(monkeypatch) -> None:
    monkeypatch.setattr("v2engine.decision.random.random", lambda: 0.0)
    base = [_p("H", 40, 34), _p("F", 50, 24)]
    marked_t = [_p("T", 62, 26), _p("Marqueur", 62.3, 26, team="away")]  # T, marqué de près : jamais servi direct

    def value(players, mode):
        option = _pass(players, mode)
        assert option.target.name == "F"
        return option.value
    assert value(base + marked_t, CONTRE_ATTAQUE) == value(base, CONTRE_ATTAQUE)  # progression seule (ticket 11)
    assert value(base + marked_t, None) != value(base, None)

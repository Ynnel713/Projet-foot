"""Registre des contextes d'attributs (ADR 0002, ticket v2-attributs-contextes/01) : poids sommant à 1, lecture par la
façade, et reprise à l'identique des deux cumuls existants (porteur tête haute 08c, idée de jouer de première 31a)."""

from __future__ import annotations

import itertools

import pytest

import v2engine.contextes as contextes
from v2engine.condition import effective_rating
from v2engine.contextes import (CONTEXTES, IDEE_DE_PREMIERE, PORTEUR_TETE_HAUTE, TEMPS, Contexte,
                                contextual_rating)
from v2engine.decision import _ONE_TOUCH_IDEA_POINTS, one_touch_idea_probability
from v2engine.scan import _HEAD_UP_BY_TOUCH, _interpolate, head_up_share
from tests.scenes import player

NOTES = (1, 11, 23, 37, 55, 64, 78, 91, 99, 100)


@pytest.mark.parametrize("contexte", list(CONTEXTES.values()), ids=lambda c: c.nom)
def test_every_context_has_weights_summing_to_one_and_a_brain_time(contexte: Contexte) -> None:
    assert sum(weight for _, weight in contexte.poids) == pytest.approx(1.0, abs=1e-12)
    assert all(weight > 0.0 for _, weight in contexte.poids)
    assert contexte.temps in TEMPS and len(contexte.attributs) == len(set(contexte.attributs)) >= 2
    assert contexte.ticket and CONTEXTES[contexte.nom] is contexte
    module, function = contexte.effet.split(".")
    assert callable(getattr(__import__(f"v2engine.{module}", fromlist=[function]), function))  # effet = fonction réelle


def test_the_registry_is_read_only() -> None:
    with pytest.raises(TypeError):
        CONTEXTES["bidon"] = PORTEUR_TETE_HAUTE  # type: ignore[index]


def test_the_registry_holds_the_two_existing_cumuls_with_their_weights() -> None:
    assert set(CONTEXTES) == {"porteur tête haute", "idée de jouer de première"}
    assert PORTEUR_TETE_HAUTE.poids == (("Dribbling", 0.6), ("Technique", 0.4))
    assert PORTEUR_TETE_HAUTE.temps == contextes.PERCEPTION
    assert IDEE_DE_PREMIERE.poids == (("First Touch", 0.5), ("Technique", 0.5))
    assert IDEE_DE_PREMIERE.temps == contextes.DECISION


@pytest.mark.parametrize("poids, temps", [
    ((("Dribbling", 0.6), ("Technique", 0.3)), contextes.PERCEPTION),  # somme 0,9
    ((("Dribbling", 1.0),), contextes.PERCEPTION),  # un seul attribut : pas un contexte
    ((("Dribbling", 0.5), ("Dribbling", 0.5)), contextes.PERCEPTION),  # attribut répété
    ((("Dribbling", 1.2), ("Technique", -0.2)), contextes.PERCEPTION),  # poids négatif
    ((("Dribbling", 0.5), ("Technique", 0.5)), "intuition"),  # temps inconnu
])
def test_an_ill_formed_context_is_refused(poids, temps) -> None:
    with pytest.raises(ValueError):
        Contexte("bidon", temps, poids, "v2-x/1", "bidon.effet")


def test_contextual_rating_reads_each_note_through_the_facade(monkeypatch) -> None:
    calls = []

    def spy(p, attribute, context=None):
        calls.append(attribute)
        return effective_rating(p, attribute, context)

    monkeypatch.setattr(contextes, "effective_rating", spy)
    me = player("P", Dribbling=80, Technique=40)
    assert contextual_rating(me, PORTEUR_TETE_HAUTE) == pytest.approx(0.6 * 80 + 0.4 * 40, abs=1e-12)
    assert calls == ["Dribbling", "Technique"]
    assert contextual_rating(me, "porteur tête haute") == contextual_rating(me, PORTEUR_TETE_HAUTE)


def _old_one_touch_idea(first_touch: float, technique: float, gain: float) -> float:
    """Formule d'avant le registre (31a), recopiée telle quelle, sans pression."""
    note = 0.5 * (first_touch + technique)
    note = min(max(note, _ONE_TOUCH_IDEA_POINTS[0][0]), _ONE_TOUCH_IDEA_POINTS[-1][0])
    base = _ONE_TOUCH_IDEA_POINTS[-1][1]
    for (n0, v0), (n1, v1) in zip(_ONE_TOUCH_IDEA_POINTS, _ONE_TOUCH_IDEA_POINTS[1:]):
        if note <= n1:
            base = v0 + (note - n0) / (n1 - n0) * (v1 - v0)
            break
    return min(1.0, base * (1.0 + gain))


@pytest.mark.parametrize("a, b", list(itertools.product(NOTES, repeat=2)))
def test_the_migrated_cumuls_give_the_same_values_as_before(a: int, b: int) -> None:
    # porteur tête haute (08c) : 0,6 Dribbling + 0,4 Technique
    carrier = player("P", Dribbling=a, Technique=b)
    old = 0.6 * a + 0.4 * b
    assert abs(contextual_rating(carrier, PORTEUR_TETE_HAUTE) - old) <= 1e-12
    assert abs(head_up_share(carrier) - _interpolate(_HEAD_UP_BY_TOUCH, old)) <= 1e-12
    # idée de jouer de première (31a) : moyenne de First Touch et Technique
    receiver = player("R", First_Touch=a, Technique=b)
    assert abs(contextual_rating(receiver, IDEE_DE_PREMIERE) - 0.5 * (a + b)) <= 1e-12
    assert abs(one_touch_idea_probability(receiver, []) - _old_one_touch_idea(a, b, 0.0)) <= 1e-12

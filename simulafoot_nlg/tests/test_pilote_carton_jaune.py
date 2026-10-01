"""Invariants du pilote CARTON_JAUNE (pilotes_v2/carton_jaune.py). Meme
esprit que test_pilote_tir_non_cadre.py ; la collision de 4 mots est couverte
par test_pilotes_v2_garde_fous.py (decouverte automatique)."""

from __future__ import annotations

import re
from collections import defaultdict

import pytest

from pilotes_v2 import carton_jaune
from scripts.audit_structure_phrases import audit

TOUTES = carton_jaune.DEFAUT + carton_jaune.SURNOM
SLOTS_AUTORISES = {"joueur", "adversaire", "club", "minute"}
ATTRIBUTS_AUTORISES = {
    "Aggression", "Tackling", "Composure", "Decisions", "Anticipation", "Determination",
    "Flair", "Leadership", "age", "minute", "preferred_moves",
}
CONTEXTE = {"minute", "score_context"}
# "Argues With Officials" (propose par le plan) : 18 joueurs sur 7563 = fantome.
MOVES_AUTORISES = {"Dives Into Tackles", "Winds Up Opponents"}


def _mots(texte: str) -> list[str]:
    return re.findall(r"\{\w+\}|[\w'-]+", texte.lower().replace("’", "'"))


def test_volume_et_nombre_de_surnoms():
    assert 25 <= len(TOUTES) <= 30
    assert len(carton_jaune.SURNOM) == 6


def test_slots_connus_uniquement_et_surnom_sans_nom_propre():
    for texte, _ in TOUTES:
        assert set(re.findall(r"\{(\w+)\}", texte)) <= SLOTS_AUTORISES, texte
    for texte, _ in carton_jaune.SURNOM:
        assert "{joueur}" not in texte
    for texte, _ in carton_jaune.DEFAUT:
        assert "{joueur}" in texte


def test_conditions_bien_formees_sans_height_cm_ni_move_fantome():
    for texte, conditions in TOUTES:
        for attribut, operateur, valeur in conditions:
            assert attribut in ATTRIBUTS_AUTORISES, (attribut, texte)
            if attribut == "preferred_moves":
                assert operateur == "contient" and valeur in MOVES_AUTORISES, texte
            else:
                assert operateur in {">=", "<="}
                float(valeur)


def test_registre_jaune_ni_rouge_ni_suspense_de_deuxieme_avertissement():
    """Le jaune est un evenement leger : pas de vocabulaire du rouge, pas de
    "premier"/"second" avertissement (gestion du 2e jaune = V3)."""
    interdits = re.compile(r"\brouge\b|\bpremier\b|\bsecond\b|\bdeuxi[eè]me\b|exclu|vestiaires", re.IGNORECASE)
    for texte, _ in TOUTES:
        assert not interdits.search(texte), texte


def test_aucune_chute_de_phrase_repetee():
    chutes: dict[str, list[int]] = defaultdict(list)
    for i, (texte, _) in enumerate(TOUTES, 1):
        chutes[" ".join(_mots(texte)[-2:])].append(i)
        chutes[_mots(texte)[-1]].append(i)
    assert {c: sorted(set(p)) for c, p in chutes.items() if len(set(p)) > 1} == {}


def test_zero_doublon_structurel():
    assert audit("CARTON_JAUNE", [t for t, _ in TOUTES], nb_surnoms=len(carton_jaune.SURNOM)) == []


@pytest.fixture(scope="module")
def base_joueurs():
    from scripts.audit_conditions_pilote import BASE, charger_joueurs

    if not BASE.exists():
        pytest.skip("base locale absente")
    return charger_joueurs()


def test_aucune_condition_joueur_dominante_et_aucun_surnom_fantome(base_joueurs):
    from scripts.audit_conditions_pilote import SEUIL_FANTOME, audit as audit_jouabilite, joueurs_matchant

    rapport = audit_jouabilite("CARTON_JAUNE", TOUTES, base_joueurs)
    assert rapport["dominantes"] == []
    assert rapport["fantomes"] == []
    for texte, conditions in carton_jaune.SURNOM:
        assert len(joueurs_matchant(base_joueurs, conditions)) >= SEUIL_FANTOME, texte

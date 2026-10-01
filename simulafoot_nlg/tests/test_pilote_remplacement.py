"""Invariants du pilote REMPLACEMENT (pilotes_v2/remplacement.py). Meme
esprit que test_pilote_tir_non_cadre.py : chaque test echoue si on degrade
le pilote. Conditions evaluees sur l'ENTRANT (convention du pilote)."""

from __future__ import annotations

import re
from collections import defaultdict

import pytest

from pilotes_v2 import remplacement
from scripts.audit_structure_phrases import audit

TOUTES = remplacement.DEFAUT + remplacement.SURNOM
SLOTS_AUTORISES = {"sortant", "entrant", "club", "minute"}
ATTRIBUTS_AUTORISES = {"age", "fm_rating", "Pace", "Stamina", "Technique", "Work Rate", "minute"}
OPERATEURS_AUTORISES = {">=", "<="}
CONTEXTE = {"minute", "score_context"}


def _mots(texte: str) -> list[str]:
    return re.findall(r"\{\w+\}|[\w'-]+", texte.lower().replace("’", "'"))


def test_volume_et_nombre_de_surnoms():
    assert 15 <= len(TOUTES) <= 25
    assert 4 <= len(remplacement.SURNOM) <= 5


def test_defaut_nomme_l_entrant_et_surnom_designe_l_entrant_sans_le_nommer():
    for texte, _ in remplacement.DEFAUT:
        assert "{entrant}" in texte, texte
    for texte, _ in remplacement.SURNOM:
        assert "{sortant}" in texte and "{entrant}" not in texte, texte


def test_slots_connus_uniquement():
    for texte, _ in TOUTES:
        assert set(re.findall(r"\{(\w+)\}", texte)) <= SLOTS_AUTORISES, texte


def test_conditions_bien_formees_sans_height_cm_ni_score_context():
    for texte, conditions in TOUTES:
        for attribut, operateur, valeur in conditions:
            assert attribut in ATTRIBUTS_AUTORISES, (attribut, texte)
            assert operateur in OPERATEURS_AUTORISES, (operateur, texte)
            float(valeur)


def test_zero_collision_de_quatre_mots():
    positions: dict[tuple[str, ...], list[int]] = defaultdict(list)
    for i, (texte, _) in enumerate(TOUTES, 1):
        mots = _mots(texte)
        for k in range(len(mots) - 3):
            positions[tuple(mots[k:k + 4])].append(i)
    assert {" ".join(g): p for g, p in positions.items() if len(p) > 1} == {}


def test_aucune_chute_de_phrase_repetee():
    chutes: dict[str, list[int]] = defaultdict(list)
    for i, (texte, _) in enumerate(TOUTES, 1):
        chutes[" ".join(_mots(texte)[-2:])].append(i)
    assert {c: p for c, p in chutes.items() if len(p) > 1} == {}


def test_zero_doublon_structurel():
    assert audit("REMPLACEMENT", [t for t, _ in TOUTES], nb_surnoms=len(remplacement.SURNOM)) == []


@pytest.fixture(scope="module")
def base_joueurs():
    from scripts.audit_conditions_pilote import BASE, charger_joueurs

    if not BASE.exists():
        pytest.skip("base locale absente")
    return charger_joueurs()


def test_aucune_condition_joueur_dominante_et_aucun_surnom_fantome(base_joueurs):
    from scripts.audit_conditions_pilote import SEUIL_FANTOME, audit as audit_jouabilite, joueurs_matchant

    rapport = audit_jouabilite("REMPLACEMENT", TOUTES, base_joueurs)
    dominantes_joueur = [
        i for i in rapport["dominantes"]
        if any(c[0] not in CONTEXTE for c in TOUTES[i - 1][1])
    ]
    assert dominantes_joueur == []
    for texte, conditions in remplacement.SURNOM:
        assert len(joueurs_matchant(base_joueurs, conditions)) >= SEUIL_FANTOME, texte


def test_aucune_elision_collee_a_un_slot_nom_de_joueur():
    """"d'{entrant}" donnerait "d'Mbappé" : le nom est inconnu a l'ecriture, on
    ne l'elide jamais (non-regression de la relecture a voix haute)."""
    for texte, _ in TOUTES:
        assert not re.search(r"\b(?:d|l|qu|n|j|s|c)['’]\{", texte), texte

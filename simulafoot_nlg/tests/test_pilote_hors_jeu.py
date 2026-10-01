"""Invariants du pilote HORS-JEU (pilotes_v2/hors_jeu.py). Collisions de 4 mots,
jouabilite et regle des 70 % sont aussi couvertes par test_pilotes_v2_garde_fous.py."""

from __future__ import annotations

import re
from collections import defaultdict

import pytest

from pilotes_v2 import hors_jeu
from scripts.audit_structure_phrases import audit

TOUTES = hors_jeu.DEFAUT + hors_jeu.SURNOM
SLOTS_AUTORISES = {"joueur", "adversaire", "minute"}
ATTRIBUTS_AUTORISES = {
    "Off the Ball", "Pace", "Concentration", "Anticipation", "Finishing", "fm_rating",
    "position", "age", "minute",
}
POSITIONS = {"BU", "SA", "AG", "AD", "MOC", "MC", "MDC", "RB", "LB"}  # jamais GK ni DC
TIC_MAX = 0.30


def _mots(texte: str) -> list[str]:
    return re.findall(r"\{\w+\}|[\w'-]+", texte.lower().replace("’", "'"))


def test_volume_et_surnoms():
    assert 20 <= len(TOUTES) <= 25
    assert len(hors_jeu.SURNOM) == 5


def test_slots_connus_surnom_sans_slot_joueur():
    for texte, _ in TOUTES:
        assert set(re.findall(r"\{(\w+)\}", texte)) <= SLOTS_AUTORISES, texte
    for texte, _ in hors_jeu.SURNOM:
        assert "{joueur}" not in texte


def test_conditions_bien_formees_et_positions_valides():
    for texte, conditions in TOUTES:
        for attribut, operateur, valeur in conditions:
            assert attribut in ATTRIBUTS_AUTORISES, (attribut, texte)
            if operateur == "in":
                assert attribut == "position"
                assert {v.strip() for v in valeur.split(",")} <= POSITIONS, texte
            else:
                assert operateur in {">=", "<="}
                float(valeur)


def test_surnom_age_est_restreint_aux_postes_offensifs():
    """Un gardien de 36 ans ne peut pas etre hors-jeu : les SURNOM lies a l'age
    portent aussi une condition de poste (sans quoi 'vetéran' matcherait un GK)."""
    for texte, conditions in hors_jeu.SURNOM:
        if any(a == "age" for a, _, _ in conditions):
            assert any(a == "position" for a, _, _ in conditions), texte


def test_au_moins_six_phrases_sans_condition_pour_le_repli_alpha():
    """Regle alpha (SPEC_ANTI_REPEAT.md section 6) : le repli sans condition ne
    doit pas etre sous-dimensionne."""
    assert sum(not c for _, c in hors_jeu.DEFAUT) >= 6


def test_aucune_phrase_ne_dit_un_but_annule_ni_un_resultat():
    interdits = re.compile(r"annul|\bbut annul|var\b|score|menant|marqu", re.I)
    for texte, _ in TOUTES:
        assert not interdits.search(texte), texte


def test_aucune_chute_repetee_et_pas_de_tic_lexical():
    chutes: dict[str, list[int]] = defaultdict(list)
    for i, (texte, _) in enumerate(TOUTES, 1):
        chutes[_mots(texte)[-1]].append(i)
    assert {c: p for c, p in chutes.items() if len(p) > 1} == {}
    for mot in ("hors-jeu", "drapeau", "assistant", "ligne", "piège", "{adversaire}", "trop tôt"):
        part = sum(mot in texte.lower() for texte, _ in TOUTES) / len(TOUTES)
        assert part <= TIC_MAX, (mot, part)


def test_zero_doublon_structurel():
    assert audit("HORS_JEU", [t for t, _ in TOUTES], nb_surnoms=len(hors_jeu.SURNOM)) == []


@pytest.fixture(scope="module")
def base_joueurs():
    from scripts.audit_conditions_pilote import BASE, charger_joueurs

    if not BASE.exists():
        pytest.skip("base locale absente")
    return charger_joueurs()


def test_zero_dominante_zero_surnom_fantome(base_joueurs):
    from scripts.audit_conditions_pilote import SEUIL_FANTOME, audit as audit_jouabilite, joueurs_matchant

    rapport = audit_jouabilite("HORS_JEU", TOUTES, base_joueurs)
    assert rapport["dominantes"] == []
    for texte, conditions in hors_jeu.SURNOM:
        assert len(joueurs_matchant(base_joueurs, conditions)) >= SEUIL_FANTOME, texte

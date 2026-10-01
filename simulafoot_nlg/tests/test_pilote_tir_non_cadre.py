"""Invariants du pilote TIR_NON_CADRE (pilotes_v2/tir_non_cadre.py) :
volume, slots, conditions bien formees, 0 collision de 4 mots, 0 doublon
structurel, pas de tic d'ecriture, pas de height_cm tant que les
sentinelles 152/154 ne sont pas purgees. Chaque test echoue si on degrade
le pilote (phrase dupliquee, slot inconnu, condition mal formee)."""

from __future__ import annotations

import re
from collections import defaultdict

import pytest

from pilotes_v2 import corner, defense, faute_simple, tir_non_cadre
from scripts.audit_structure_phrases import audit

TOUTES = tir_non_cadre.DEFAUT + tir_non_cadre.SURNOM
ATTRIBUTS_AUTORISES = {
    "Finishing", "Technique", "Vision", "Pace", "Composure", "First Touch", "Long Shots",
    "minute", "preferred_moves",
}
OPERATEURS_AUTORISES = {">=", "<=", "contient"}
SLOTS_AUTORISES = {"joueur", "adversaire"}


def _mots(texte: str) -> list[str]:
    return re.findall(r"\{\w+\}|[\w'-]+", texte.lower().replace("’", "'"))


def _quadrigrammes(texte: str) -> set[tuple[str, ...]]:
    mots = _mots(texte)
    return {tuple(mots[i:i + 4]) for i in range(len(mots) - 3)}


def test_volume_dans_la_fourchette_du_plan_v2():
    assert 25 <= len(TOUTES) <= 30
    assert len(tir_non_cadre.SURNOM) == 6


def test_slots_limites_a_joueur_et_adversaire():
    for texte, _ in TOUTES:
        assert set(re.findall(r"\{(\w+)\}", texte)) <= SLOTS_AUTORISES, texte


def test_surnom_sans_nom_propre_defaut_avec_joueur():
    for texte, _ in tir_non_cadre.SURNOM:
        assert "{joueur}" not in texte
    for texte, _ in tir_non_cadre.DEFAUT:
        assert "{joueur}" in texte


def test_conditions_bien_formees_et_sans_height_cm():
    for texte, conditions in TOUTES:
        for attribut, operateur, valeur in conditions:
            assert attribut in ATTRIBUTS_AUTORISES, (attribut, texte)
            assert operateur in OPERATEURS_AUTORISES, (operateur, texte)
            if operateur != "contient":
                float(valeur)


def test_aucune_phrase_dupliquee():
    textes = [t for t, _ in TOUTES]
    assert len(set(textes)) == len(textes)


def test_zero_collision_de_quatre_mots_dans_le_pilote():
    positions: dict[tuple[str, ...], list[int]] = defaultdict(list)
    for i, (texte, _) in enumerate(TOUTES, 1):
        for gramme in _quadrigrammes(texte):
            positions[gramme].append(i)
    collisions = {" ".join(g): p for g, p in positions.items() if len(p) > 1}
    assert not collisions


def test_zero_doublon_structurel(capsys):
    assert audit("TIR_NON_CADRE", [t for t, _ in TOUTES]) == []


@pytest.mark.parametrize("tic", ["tout le monde", "le gardien de {adversaire}"])
def test_pas_de_tic_decriture_sur_les_quatre_pilotes(tic):
    pilotes = (defense, faute_simple, corner, tir_non_cadre)
    occurrences = sum(
        tic in texte.lower() for module in pilotes for texte, _ in module.DEFAUT + module.SURNOM
    )
    assert occurrences <= 4


def test_aucune_chute_de_phrase_repetee():
    """Echo de fin de phrase : deux phrases ne finissent jamais par les deux
    memes derniers mots (au-dessus du bruit des 7 % sur 28 phrases)."""
    chutes: dict[str, list[int]] = defaultdict(list)
    for i, (texte, _) in enumerate(TOUTES, 1):
        chutes[" ".join(_mots(texte)[-2:])].append(i)
    assert {c: p for c, p in chutes.items() if len(p) > 1} == {}


def test_canonnier_condition_exacte_et_non_fantome_sur_la_base_reelle(base_joueurs):
    """Pin de la condition (une version "Long Shots >= 90" ne matcherait que
    3 joueurs) : move Shoots With Power ET Finishing <= 70 (frappe de mule
    ratee), 24 joueurs sur 7563 a la date du 01/10/2026."""
    from scripts.audit_conditions_pilote import SEUIL_FANTOME, joueurs_matchant

    conditions = next(c for t, c in tir_non_cadre.SURNOM if t.startswith("Le canonnier"))
    assert conditions == [
        ("preferred_moves", "contient", "Shoots With Power"),
        ("Finishing", "<=", "70"),
    ]
    assert len(joueurs_matchant(base_joueurs, conditions)) >= SEUIL_FANTOME


# --- jouabilite contre la vraie base (non versionnee : ignores si absente) ---
# Lecon de GESTE_SIGNATURE : 32 phrases sur 37 etaient injouables sur 95 % des
# joueurs. Une condition qui matche >50 % des joueurs de champ ecrase le
# tirage ; un SURNOM qui matche <20 joueurs est un fantome.

@pytest.fixture(scope="module")
def base_joueurs():
    from scripts.audit_conditions_pilote import BASE, charger_joueurs

    if not BASE.exists():
        pytest.skip("base locale absente")
    return charger_joueurs()


def test_au_plus_trois_conditions_dominantes_sur_les_joueurs_de_champ(base_joueurs):
    from scripts.audit_conditions_pilote import audit

    rapport = audit("TIR_NON_CADRE", TOUTES, base_joueurs)
    # minute (contexte de match) est ignoree par l'audit : une phrase dont la
    # seule condition est contextuelle apparait "dominante" sans l'etre.
    dominantes_joueur = [
        i for i in rapport["dominantes"]
        if any(c[0] not in {"minute", "score_context"} for c in TOUTES[i - 1][1])
    ]
    assert len(dominantes_joueur) <= 3
    assert dominantes_joueur == []


def test_aucun_surnom_fantome_sur_la_base_reelle(base_joueurs):
    from scripts.audit_conditions_pilote import SEUIL_FANTOME, joueurs_matchant

    for texte, conditions in tir_non_cadre.SURNOM:
        assert len(joueurs_matchant(base_joueurs, conditions)) >= SEUIL_FANTOME, texte

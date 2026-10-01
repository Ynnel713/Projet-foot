"""Invariants du pilote AMBIANCE (pilotes_v2/ambiance.py). Scenario sans joueur :
conditions limitees a is_home et minute ; 4 types d'ambiance equilibres ;
phrases neutres vraies a domicile comme a l'exterieur."""

from __future__ import annotations

import re
from collections import Counter, defaultdict

from pilotes_v2 import ambiance
from scripts.audit_structure_phrases import audit

TOUTES = ambiance.DEFAUT
SLOTS_AUTORISES = {"club", "adversaire"}
CONDITIONS_AUTORISEES = {"is_home", "minute"}
# Un mot de COTE (maison / visiteur) ne peut pas figurer dans une phrase sans
# condition is_home : elle serait fausse dans un des deux cas.
MOTS_DE_COTE = re.compile(r"domicile|d[ée]placement|hostile|locaux|visiteurs|chaudron|\bchez\b|acquis", re.I)
TIC_MAX = 0.30
MOTS_SURVEILLES = ("tribunes", "stade", "public", "gradins", "enceinte", "supporters", "ballon")
PLAFOND_STADE = 3


def _mots(texte: str) -> list[str]:
    return re.findall(r"\{\w+\}|[\w'-]+", texte.lower().replace("’", "'"))


def test_volume_sans_surnom():
    assert 20 <= len(TOUTES) <= 25
    assert ambiance.SURNOM == []
    assert len(ambiance.TYPES) == len(TOUTES)


def test_quatre_types_distincts_et_equilibres():
    comptes = Counter(ambiance.TYPES)
    assert set(comptes) == {"fete", "tension", "silence", "pression"}
    assert min(comptes.values()) >= 4
    assert max(comptes.values()) / len(TOUTES) <= 0.40


def test_aucun_joueur_slots_et_conditions_limites_au_contexte():
    for texte, conditions in TOUTES:
        assert set(re.findall(r"\{(\w+)\}", texte)) <= SLOTS_AUTORISES, texte
        for attribut, operateur, valeur in conditions:
            assert attribut in CONDITIONS_AUTORISEES, (attribut, texte)
            if attribut == "is_home":
                assert operateur == "==" and valeur in {"true", "false"}


def test_phrase_neutre_ne_nomme_ni_club_ni_cote():
    """Sans condition is_home, {club} peut etre la maison OU le visiteur :
    on n'y met ni le club ni un mot de cote."""
    for texte, conditions in TOUTES:
        if any(a == "is_home" for a, _, _ in conditions):
            continue
        assert "{club}" not in texte and "{adversaire}" not in texte, texte
        assert not MOTS_DE_COTE.search(texte), texte


def test_couverture_domicile_et_exterieur_comparable():
    domicile = sum(("is_home", "==", "true") in c for _, c in TOUTES)
    exterieur = sum(("is_home", "==", "false") in c for _, c in TOUTES)
    assert domicile >= 3 and exterieur >= 3 and abs(domicile - exterieur) <= 1


def test_aucune_phrase_ne_dit_un_resultat_ni_un_derby():
    interdits = re.compile(r"\bbut\b|marqu|menant|m[eè]ne\b|derby|classement|leader|finale", re.I)
    for texte, _ in TOUTES:
        assert not interdits.search(texte), texte


def test_aucune_chute_repetee_ni_tic_lexical():
    chutes: dict[str, list[int]] = defaultdict(list)
    for i, (texte, _) in enumerate(TOUTES, 1):
        chutes[_mots(texte)[-1]].append(i)
    assert {c: p for c, p in chutes.items() if len(p) > 1} == {}
    for mot in MOTS_SURVEILLES:
        part = sum(mot in texte.lower() for texte, _ in TOUTES) / len(TOUTES)
        assert part <= TIC_MAX, (mot, part)


def test_zero_doublon_structurel():
    assert audit("AMBIANCE", [t for t, _ in TOUTES]) == []


def test_stade_sous_le_plafond_de_trois_phrases():
    """"stade" est le mot de domaine d'AMBIANCE : plafonne a 3/24 (12 %), le
    reste du vocabulaire varie (travees, temple, enceinte, tribunes...)."""
    assert sum("stade" in texte.lower() for texte, _ in TOUTES) <= PLAFOND_STADE

"""engine/fm26.py : source unique des attributs FM26 (D16, R11)."""

from __future__ import annotations

import importlib

from engine.fm26 import ATTRIBUTE_TO_CATEGORY, FM26_ATTRIBUTES, FM26_ATTRIBUTES_KNOWN


def test_les_47_attributs_sont_connus_et_aplatis():
    noms_par_categorie = [nom for noms in FM26_ATTRIBUTES.values() for nom in noms]
    assert len(noms_par_categorie) == 47
    assert FM26_ATTRIBUTES_KNOWN == frozenset(noms_par_categorie)


def test_aucun_attribut_n_appartient_a_deux_categories():
    noms_par_categorie = [nom for noms in FM26_ATTRIBUTES.values() for nom in noms]
    assert len(noms_par_categorie) == len(set(noms_par_categorie))
    assert set(ATTRIBUTE_TO_CATEGORY) == FM26_ATTRIBUTES_KNOWN


def test_une_faute_de_frappe_n_est_pas_connue():
    assert "Aggression" in FM26_ATTRIBUTES_KNOWN
    assert "Aggresion" not in FM26_ATTRIBUTES_KNOWN


def test_import_players_utilise_la_source_unique_et_non_une_copie():
    # "data.import.import_players" n'est pas importable statiquement
    # ("import" est un mot-cle Python), voir cli.py.
    import_players = importlib.import_module("data.import.import_players")
    assert import_players.FM26_ATTRIBUTES is FM26_ATTRIBUTES
    assert import_players.ATTRIBUTE_TO_CATEGORY is ATTRIBUTE_TO_CATEGORY

"""L'outil de jouabilite (scripts/audit_conditions_pilote.py) doit calculer
l'INTERSECTION des conditions "ET", jamais leur maximum ni leur union. Un
jeu de 4 joueurs synthetiques dont le resultat attendu se lit a la main."""

from __future__ import annotations

from scripts.audit_conditions_pilote import condition_vraie, joueurs_matchant

JOUEURS = [
    {"id": 1, "Tackling": 50, "Vision": 50},  # matche les deux conditions
    {"id": 2, "Tackling": 50, "Vision": 90},  # matche Tackling seul
    {"id": 3, "Tackling": 90, "Vision": 50},  # matche Vision seul
    {"id": 4, "Tackling": 90, "Vision": 90},  # ne matche rien
]
TACKLING_BAS = ("Tackling", "<=", "60")
VISION_BASSE = ("Vision", "<=", "60")


def test_conditions_seules_comptent_chacune_deux_joueurs():
    assert len(joueurs_matchant(JOUEURS, [TACKLING_BAS])) == 2
    assert len(joueurs_matchant(JOUEURS, [VISION_BASSE])) == 2


def test_deux_conditions_et_donnent_l_intersection_pas_le_maximum_ni_l_union():
    matchants = joueurs_matchant(JOUEURS, [TACKLING_BAS, VISION_BASSE])
    assert [j["id"] for j in matchants] == [1]


def test_valeur_absente_ne_matche_jamais_meme_en_inferieur_ou_egal():
    assert condition_vraie({"id": 5}, TACKLING_BAS) is False


def test_operateur_in_matche_la_liste_de_valeurs_et_pas_le_reste():
    joueurs = [{"id": 1, "position": "BU"}, {"id": 2, "position": "DC"}, {"id": 3, "position": "AG"}]
    condition = ("position", "in", "BU, AG, AD")
    assert [j["id"] for j in joueurs_matchant(joueurs, [condition])] == [1, 3]

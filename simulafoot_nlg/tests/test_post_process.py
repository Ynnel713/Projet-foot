"""post_process.apply est un SQUELETTE (voir engine/post_process.py) --
même raisonnement que test_phrase_selector.py : les 4 cas du brief (élision,
majuscule, ponctuation, double espace) décrivent l'algorithme FUTUR. Seul le
contrat "échoue explicitement" est vérifié ici, un test par cas pour que
l'implémentation future les remplace un par un sans devoir redécouvrir la
liste."""

from __future__ import annotations

import pytest

from engine.post_process import (
    INITIALE_ASPIREE,
    apply,
    ecraser_espaces,
    elision,
    majuscule_initiale,
    ponctuation_finale,
)


def test_apply_raises_not_implemented_error_on_plain_text():
    with pytest.raises(NotImplementedError):
        apply("quelle frappe")


def test_apply_raises_not_implemented_error_on_elision_case():
    # Futur : "le Ailier" -> "l'Ailier"
    with pytest.raises(NotImplementedError):
        apply("le Ailier a marqué")


def test_apply_raises_not_implemented_error_on_capitalisation_case():
    # Futur : "mbappé marque" -> "Mbappé marque"
    with pytest.raises(NotImplementedError):
        apply("mbappé marque")


def test_apply_raises_not_implemented_error_on_punctuation_case():
    # Futur : "Quel but !." -> "Quel but !"
    with pytest.raises(NotImplementedError):
        apply("Quel but !.")


def test_apply_raises_not_implemented_error_on_double_space_case():
    # Futur : "Quel  but" -> "Quel but"
    with pytest.raises(NotImplementedError):
        apply("Quel  but")


# --- Regle 1 : espaces multiples (fonctions pures, apply les enchainera) -----

@pytest.mark.parametrize(
    ("brut", "attendu"),
    [
        ("Quel  but", "Quel but"),  # slot vide au milieu du gabarit
        ("a   b    c", "a b c"),
        ("  Quel but", "Quel but"),  # slot vide en tete
        ("Quel but  ", "Quel but"),
        ("Quel\t\tbut", "Quel but"),
        ("Quel but", "Quel but"),  # deja propre : inchange
        ("", ""),
    ],
)
def test_ecraser_espaces(brut, attendu):
    assert ecraser_espaces(brut) == attendu


def test_ecraser_espaces_respecte_l_espace_insecable_et_les_retours_a_la_ligne():
    assert ecraser_espaces("Quel but !") == "Quel but !"
    assert ecraser_espaces("une\n\nligne") == "une\n\nligne"


def test_ecraser_espaces_est_idempotente():
    assert ecraser_espaces(ecraser_espaces("a   b  ")) == "a b"


# --- Regle 2 : majuscule initiale --------------------------------------------


@pytest.mark.parametrize(
    ("brut", "attendu"),
    [
        ("mbappé marque", "Mbappé marque"),  # slot en minuscule en tete de gabarit
        ("Mbappé marque", "Mbappé marque"),  # deja en majuscule : inchange
        ("élan parfait", "Élan parfait"),  # lettre accentuee
        ("l'ailier file", "L'ailier file"),
        ("« quel but », dit-il", "« Quel but », dit-il"),  # signes d'ouverture sautes
        ("— quel but", "— Quel but"),
        ("3 joueurs, et mbappé", "3 joueurs, et mbappé"),  # chiffre en tete : rien
        ("!!!", "!!!"),
        ("", ""),
    ],
)
def test_majuscule_initiale(brut, attendu):
    assert majuscule_initiale(brut) == attendu


def test_majuscule_initiale_ne_touche_que_la_premiere_lettre():
    assert majuscule_initiale("mbappé et LUCAS ont marqué") == "Mbappé et LUCAS ont marqué"


# --- Regle 3 : une seule marque finale ---------------------------------------


@pytest.mark.parametrize(
    ("brut", "attendu"),
    [
        ("Quel but !.", "Quel but !"),  # slot "!" + gabarit "."
        ("Quel but ?.", "Quel but ?"),
        ("Quel but..", "Quel but."),
        ("Quel but !!", "Quel but !"),
        ("Quel but .!", "Quel but !"),
        ("Quoi !?!", "Quoi ?!"),  # les deux marques expressives restent
        ("Quel but.", "Quel but."),  # deja correct : inchange
        ("Quel but !", "Quel but !"),  # espace avant la marque : inchange
        ("Quel but...", "Quel but..."),  # points de suspension voulus
        ("Quel but…", "Quel but…"),
        ("Quoi ?!", "Quoi ?!"),
        ("Quoi !?", "Quoi !?"),
        ("Pas de ponctuation", "Pas de ponctuation"),  # rien n'est ajoute
        ("", ""),
    ],
)
def test_ponctuation_finale(brut, attendu):
    assert ponctuation_finale(brut) == attendu


def test_ponctuation_finale_ne_touche_que_la_fin_et_garde_les_espaces_apres():
    assert ponctuation_finale("Quel but ! Quel but !.  ") == "Quel but ! Quel but !  "
    assert ponctuation_finale("Oh... quel but !.") == "Oh... quel but !"


# --- Regle 4 : elision --------------------------------------------------------


@pytest.mark.parametrize(
    ("brut", "attendu"),
    [
        ("le Ailier a marqué", "l'Ailier a marqué"),
        ("la équipe", "l'équipe"),
        ("de Arsenal", "d'Arsenal"),
        ("que il marque", "qu'il marque"),
        ("ne a pas", "n'a pas"),
        ("se être", "s'être"),
        ("ce est", "c'est"),
        ("me envoie", "m'envoie"),
        ("te avoir", "t'avoir"),
        ("de Écosse", "d'Écosse"),  # voyelle accentuee
        ("de homme", "d'homme"),  # h muet
        ("de Henry", "d'Henry"),  # h muet : absent de la table
        ("Le Ailier", "L'Ailier"),  # casse de l'article conservee
        ("DE Arsenal", "D'Arsenal"),
    ],
)
def test_elision_devant_voyelle_ou_h_muet(brut, attendu):
    assert elision(brut) == attendu


@pytest.mark.parametrize(
    "texte",
    [
        "le Havre",
        "de Havre",
        "à la fois contre Le Havre",
        "de Hull City",
        "le Hamburger SV",
        "de Hannover 96",
        "de Hajduk Split",
        "le hors-jeu",
        "de hors-jeu",
        "le onze de départ",
        "la hargne",
        "le héros du match",
        "le huitième de finale",
        "de Haaland",
    ],
)
def test_pas_d_elision_devant_une_initiale_aspiree(texte):
    assert elision(texte) == texte


@pytest.mark.parametrize(
    "texte",
    [
        "le ballon",  # consonne
        "de Lyon",
        "l'ailier",  # deja elide
        "de l'équipe",
        "tele a",  # le n'est pas un mot seul
        "cela a marché",
    ],
)
def test_pas_d_elision_hors_des_articles_devant_voyelle(texte):
    assert elision(texte) == texte


def test_elision_n_agit_que_sur_les_mots_entiers_et_pas_devant_y():
    assert elision("de Yann") == "de Yann"
    assert elision("rôle a") == "rôle a"
    assert elision("pile à l'heure") == "pile à l'heure"


def test_elision_traite_plusieurs_occurrences_et_est_idempotente():
    brut = "le Ailier de Arsenal que il connaît"
    assert elision(brut) == "l'Ailier d'Arsenal qu'il connaît"
    assert elision(elision(brut)) == elision(brut)


def test_la_table_couvre_le_havre_et_les_clubs_en_h_de_la_base():
    # Clubs en "H" de players.club (01/10/2026), tous a h aspire en francais.
    for club in (
        "Le Havre AC", "Hull City", "Hamburger SV", "HNK Hajduk Split", "Hellas Verona", "Hapoel Tel Aviv",
        "Hannover 96", "Holstein Kiel", "Hertha BSC", "Hardrock Football Club", "Hammarby IF", "HNK Rijeka",
        "Huddersfield Town", "Hibernian FC", "Heracles Almelo", "Henan FC", "Heidenheim", "Hearts of Oak",
        "Heart of Midlothian FC", "Hafia FC", "HJK Helsinki",
    ):
        phrase = f"face à {club}" if club.startswith("Le ") else f"de {club}"
        assert elision(phrase) == phrase, club  # "Le Havre AC" : c'est le "Le" du club qui est juge


def test_la_table_est_en_forme_normalisee():
    # Comparaison faite en minuscules, sans accent, premier segment : une entree
    # en majuscule ou accentuee ne matcherait jamais.
    for mot in INITIALE_ASPIREE:
        assert mot == mot.lower() and "-" not in mot and mot.isascii(), mot

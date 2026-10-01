"""post_process.apply est un SQUELETTE (voir engine/post_process.py) --
même raisonnement que test_phrase_selector.py : les 4 cas du brief (élision,
majuscule, ponctuation, double espace) décrivent l'algorithme FUTUR. Seul le
contrat "échoue explicitement" est vérifié ici, un test par cas pour que
l'implémentation future les remplace un par un sans devoir redécouvrir la
liste."""

from __future__ import annotations

import pytest

from engine.post_process import apply, ecraser_espaces, majuscule_initiale, ponctuation_finale


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

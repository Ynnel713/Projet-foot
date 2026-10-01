"""post_process : les quatre regles sont des fonctions pures testees une a une (regles 1 a 4
ci-dessous), puis `apply` les enchaine (ordre et cas combines en fin de fichier)."""

from __future__ import annotations

import pytest

from engine.post_process import (
    INITIALE_ASPIREE,
    apply,
    contraction,
    ecraser_espaces,
    elision,
    majuscule_initiale,
    ponctuation_finale,
)


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


# --- Regle 5 : contractions de/a + Le/Les devant un nom propre -----------------


@pytest.mark.parametrize(
    ("brut", "attendu"),
    [
        ("le gardien de Le Havre AC", "le gardien du Havre AC"),
        ("face à Le Havre AC", "face au Havre AC"),
        ("les joueurs de Le Mans FC", "les joueurs du Mans FC"),
        ("de Les Herbiers", "des Herbiers"),
        ("à Les Herbiers", "aux Herbiers"),
        ("De Le Mans", "Du Mans"),  # casse de la preposition conservee
        ("À Le Mans", "Au Mans"),
    ],
)
def test_contraction_devant_un_nom_propre_a_article(brut, attendu):
    assert contraction(brut) == attendu


@pytest.mark.parametrize(
    "texte",
    [
        "décidé de le faire",  # pronom + infinitif : "de le" est correct
        "personne ne parvient à le reprendre",
        "sans que personne ne pense à le suivre",
        "de Lyon",
        "à Lens",
        "de Le ballon",  # le mot suivant n'est pas un nom propre
        "il a Le Havre dans son groupe",  # "a" sans accent : verbe, jamais contracte
        "Le Havre AC domine",  # pas de preposition devant
    ],
)
def test_pas_de_contraction_hors_nom_propre_a_article(texte):
    assert contraction(texte) == texte


def test_contraction_est_idempotente():
    assert contraction(contraction("de Le Havre et à Les Herbiers")) == "du Havre et aux Herbiers"


def test_aucun_gabarit_reel_ne_contient_de_pronom_modifie_par_la_contraction():
    """Les 4 gabarits reels ("de le jouer", "à le suivre", "à le reprendre"...) ne
    doivent pas bouger : c'est ce qui interdit de contracter un "le" en minuscule."""
    import glob

    import yaml
    from pathlib import Path

    racine = Path(__file__).resolve().parent.parent / "data" / "seed"
    for fichier in [racine / "scenarios.yml", *sorted((racine / "v2").glob("*.yml"))]:
        for scenario in yaml.safe_load(fichier.read_text(encoding="utf-8")):
            for variante in scenario["variants"]:
                for phrase in variante["phrases"]:
                    assert contraction(phrase["text"]) == phrase["text"], phrase["text"]


def test_apply_les_trois_exemples_du_havre_et_du_mans():
    assert apply("le gardien de Le Havre AC s'avance") == "Le gardien du Havre AC s'avance"
    assert apply("face à Le Havre AC") == "Face au Havre AC"
    assert apply("les joueurs de Le Mans FC") == "Les joueurs du Mans FC"


def test_la_banque_complete_rendue_avec_un_club_a_article_n_a_plus_de_de_le():
    """Les 494 gabarits rendus avec Le Havre AC / Le Mans FC : plus aucun "de Le", "à Le",
    "de Les" ni "à Les" apres apply (avant la regle : 94 phrases en "de/à {adversaire}")."""
    import re
    from pathlib import Path

    import yaml

    racine = Path(__file__).resolve().parent.parent / "data" / "seed"
    valeurs = {
        "joueur": "Kylian Mbappé", "club": "Le Mans FC", "adversaire": "Le Havre AC", "minute": "67",
        "passeur": "Alexandre Lacazette", "receveur": "Moussa Dembélé", "sortant": "Ousmane Dembélé",
        "entrant": "Rayan Cherki",
    }
    restants = []
    rendus = 0
    for fichier in [racine / "scenarios.yml", *sorted((racine / "v2").glob("*.yml"))]:
        for scenario in yaml.safe_load(fichier.read_text(encoding="utf-8")):
            for variante in scenario["variants"]:
                for phrase in variante["phrases"]:
                    rendu = apply(re.sub(r"\{(\w+)\}", lambda m: valeurs[m.group(1)], phrase["text"]))
                    rendus += 1
                    if re.search(r"(de|à|De|À) Les? [A-Z]", rendu):
                        restants.append(rendu)
    assert rendus == 494
    assert restants == []


# --- apply : les cinq regles dans l'ordre -----------------------------------


@pytest.mark.parametrize(
    ("brut", "attendu"),
    [
        ("quelle frappe", "Quelle frappe"),
        ("le Ailier a marqué", "L'Ailier a marqué"),
        ("mbappé marque", "Mbappé marque"),
        ("Quel but !.", "Quel but !"),
        ("Quel  but", "Quel but"),
        ("  de arsenal  gagne !!  ", "D'arsenal gagne !"),  # les quatre a la fois
    ],
)
def test_apply_cas_du_brief(brut, attendu):
    assert apply(brut) == attendu


def test_apply_ecrase_les_espaces_avant_l_elision():
    # Avec deux espaces entre l'article et le mot, l'elision ne reconnaitrait pas "le Ailier" :
    # elle ne fonctionne que parce que les espaces sont ecrases d'abord.
    assert apply("quel but : le  ailier  frappe") == "Quel but : l'ailier frappe"


def test_apply_enchaine_les_regles_dans_l_ordre_valide(monkeypatch):
    import engine.post_process as module

    appels: list[str] = []

    def espion(nom: str):
        original = getattr(module, nom)

        def enveloppe(texte: str) -> str:
            appels.append(nom)
            return original(texte)

        return enveloppe

    for nom in ("ecraser_espaces", "majuscule_initiale", "ponctuation_finale", "elision", "contraction"):
        monkeypatch.setattr(module, nom, espion(nom))

    module.apply("texte")
    assert appels == ["ecraser_espaces", "majuscule_initiale", "ponctuation_finale", "elision", "contraction"]


@pytest.mark.parametrize("brut", ["  de arsenal  gagne !!  ", "le  Ailier a marqué !.", "mbappé..", "Quoi ?!", ""])
def test_apply_est_idempotente(brut):
    assert apply(apply(brut)) == apply(brut)

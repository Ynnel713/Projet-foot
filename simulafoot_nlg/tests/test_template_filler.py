"""template_filler.render : slots a expression resolus sur les vrais objets (Player,
MatchContext), y compris sur la banque reelle (v1 + 8 pilotes)."""

from __future__ import annotations

import hashlib
import random
import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from engine.models import MatchContext, Phrase, PhraseSlot, Player
from engine.template_filler import SlotResolutionError, derive_rng
from engine.template_filler import render as render_phrase
from scripts.convert_commentary_xlsx_to_yaml import SLOT_EXPRESSIONS

SEED = Path(__file__).resolve().parent.parent / "data" / "seed"


def render(phrase, player, context, *, seed=1, scenario_code="BUT", variant_code="DEFAUT", **kwargs):
    """render avec une graine et des codes par defaut (les tests de rendu n'en dependent pas)."""
    return render_phrase(
        phrase, player, context, seed=seed, scenario_code=scenario_code, variant_code=variant_code, **kwargs
    )


def _joueur(prenom: str, nom: str) -> Player:
    return Player(id=1, first_name=prenom, last_name=nom)


JOUEUR = _joueur("Kylian", "Mbappé")
CONTEXTE = MatchContext(
    match_id="m1",
    minute=67,
    home_team="Lyon",
    away_team="Marseille",
    is_home=True,
    player_team="Lyon",
    passeur=_joueur("Alexandre", "Lacazette"),
    receveur=_joueur("Moussa", "Dembélé"),
    sortant=_joueur("Ousmane", "Dembélé"),
    entrant=_joueur("Rayan", "Cherki"),
)


def _phrase(texte: str, *noms_de_slots: str, **expressions: str) -> Phrase:
    """Phrase dont les slots portent l'expression de SLOT_EXPRESSIONS (ou une surcharge)."""
    slots = tuple(
        PhraseSlot(id=i, phrase_id=1, slot_name=nom, expression=expressions.get(nom, SLOT_EXPRESSIONS[nom]))
        for i, nom in enumerate(noms_de_slots)
    )
    return Phrase(id=1, variant_id=1, text=texte, slots=slots)


def test_les_8_slots_autorises_se_resolvent_sur_les_vrais_objets():
    phrase = _phrase(
        "{joueur} / {club} / {adversaire} / {minute} / {passeur} / {receveur} / {sortant} / {entrant}",
        "joueur", "club", "adversaire", "minute", "passeur", "receveur", "sortant", "entrant",
    )
    assert render(phrase, JOUEUR, CONTEXTE) == (
        "Kylian Mbappé / Lyon / Marseille / 67 / Alexandre Lacazette / Moussa Dembélé / "
        "Ousmane Dembélé / Rayan Cherki"
    )


def test_un_texte_sans_slot_est_rendu_tel_quel():
    assert render(Phrase(id=1, variant_id=1, text="Le match suit son cours."), JOUEUR, CONTEXTE) == (
        "Le match suit son cours."
    )


def test_un_slot_repete_est_rempli_partout():
    phrase = _phrase("{joueur} sert {joueur}", "joueur")
    assert render(phrase, JOUEUR, CONTEXTE) == "Kylian Mbappé sert Kylian Mbappé"


def test_nom_a_apostrophe_et_a_accolades_est_insere_sans_etre_redeveloppe():
    phrase = _phrase("{joueur} marque ! {club}", "joueur", "club")
    joueur = _joueur("Jake", "O'Brien {club}")
    # Une seule passe : "{club}" contenu dans le NOM n'est pas re-substitue.
    assert render(phrase, joueur, CONTEXTE) == "Jake O'Brien {club} marque ! Lyon"


def test_un_format_spec_dans_le_texte_ne_casse_pas_le_rendu():
    phrase = Phrase(id=1, variant_id=1, text="{score:d} reste tel quel, {joueur}")
    phrase = Phrase(
        id=1,
        variant_id=1,
        text=phrase.text,
        slots=(PhraseSlot(id=1, phrase_id=1, slot_name="joueur", expression="player.full_name"),),
    )
    assert render(phrase, JOUEUR, CONTEXTE) == "{score:d} reste tel quel, Kylian Mbappé"


def test_un_slot_du_texte_sans_valeur_leve_slot_resolution_error():
    phrase = Phrase(id=1, variant_id=1, text="{joueur} contre {adversaire}")
    with pytest.raises(SlotResolutionError, match="adversaire"):
        render(phrase, JOUEUR, CONTEXTE)


def test_une_valeur_absente_du_contexte_leve_slot_resolution_error():
    phrase = _phrase("{passeur} centre", "passeur")
    contexte = MatchContext(match_id="m1")
    with pytest.raises(SlotResolutionError, match="None"):
        render(phrase, JOUEUR, contexte)


def _phrases_reelles() -> list[Phrase]:
    phrases: list[Phrase] = []
    for fichier in [SEED / "scenarios.yml", *sorted((SEED / "v2").glob("*.yml"))]:
        for scenario in yaml.safe_load(fichier.read_text(encoding="utf-8")):
            for variante in scenario["variants"]:
                for rang, brute in enumerate(variante["phrases"]):
                    slots = tuple(
                        PhraseSlot(id=i, phrase_id=rang, slot_name=s["slot_name"], expression=s["expression"])
                        for i, s in enumerate(brute["slots"])
                    )
                    phrases.append(Phrase(id=rang, variant_id=1, text=brute["text"], slots=slots))
    return phrases


def test_les_494_phrases_reelles_se_rendent_sans_slot_ni_accolade_residuelle():
    phrases = _phrases_reelles()
    assert len(phrases) == 494
    for phrase in phrases:
        rendu = render(phrase, JOUEUR, CONTEXTE)
        assert not re.search(r"[{}]", rendu), (phrase.text, rendu)
        assert rendu.strip(), phrase.text


def test_une_phrase_reelle_donne_le_texte_attendu():
    phrase = next(p for p in _phrases_reelles() if p.text.startswith("{joueur} voit rouge"))
    assert render(phrase, JOUEUR, CONTEXTE) == "Kylian Mbappé voit rouge à la 67e minute, Lyon devra finir à dix."


# --- Branche dictionary_key (slots.yml SYNTHETIQUE : aucune donnee reelle) -----

SLOTS_SYNTHETIQUES = yaml.safe_load(
    """
exclamations_but:
  - value: "quelle frappe !"
    weight: 1.0
  - value: "magnifique !"
    weight: 0.5
  - value: "personne ne s'y attendait !"
adjectifs:
  - value: "exceptionnel"
  - value: "rare"
"""
)


def _phrase_a_dictionnaires() -> Phrase:
    return Phrase(
        id=1,
        variant_id=1,
        text="{joueur} frappe, {exclamation} Un geste {adjectif}.",
        slots=(
            PhraseSlot(id=1, phrase_id=1, slot_name="joueur", expression="player.full_name"),
            PhraseSlot(id=2, phrase_id=1, slot_name="exclamation", dictionary_key="exclamations_but"),
            PhraseSlot(id=3, phrase_id=1, slot_name="adjectif", dictionary_key="adjectifs"),
        ),
    )


def test_un_slot_a_dictionnaire_tire_une_valeur_du_dictionnaire():
    rendu = render(_phrase_a_dictionnaires(), JOUEUR, CONTEXTE, seed=1, dictionaries=SLOTS_SYNTHETIQUES)
    exclamations = [e["value"] for e in SLOTS_SYNTHETIQUES["exclamations_but"]]
    adjectifs = [e["value"] for e in SLOTS_SYNTHETIQUES["adjectifs"]]
    assert any(f"Kylian Mbappé frappe, {x} Un geste {a}." == rendu for x in exclamations for a in adjectifs)


def test_meme_graine_meme_rendu_et_les_tirages_suivent_l_ordre_des_slots():
    def rendre(graine: int) -> str:
        return render(
            _phrase_a_dictionnaires(), JOUEUR, CONTEXTE, seed=graine, dictionaries=SLOTS_SYNTHETIQUES
        )

    assert rendre(7) == rendre(7)
    # Consommation previsible : un tirage pondere par slot a dictionnaire, dans l'ordre de
    # phrase.slots, avec le rng derive de la phrase.
    rng = derive_rng(7, "BUT", "DEFAUT", _phrase_a_dictionnaires().text)
    exclamation = rng.choices(["quelle frappe !", "magnifique !", "personne ne s'y attendait !"], weights=[1.0, 0.5, 1.0])[0]
    adjectif = rng.choices(["exceptionnel", "rare"], weights=[1.0, 1.0])[0]
    assert rendre(7) == f"Kylian Mbappé frappe, {exclamation} Un geste {adjectif}."


def test_les_poids_sont_respectes():
    dictionnaire = {"k": [{"value": "A", "weight": 1.0}, {"value": "B", "weight": 0.0}]}
    phrase = Phrase(
        id=1, variant_id=1, text="{x}", slots=(PhraseSlot(id=1, phrase_id=1, slot_name="x", dictionary_key="k"),)
    )
    assert {render(phrase, JOUEUR, CONTEXTE, seed=graine, dictionaries=dictionnaire) for graine in range(50)} == {"A"}


def test_un_slot_a_dictionnaire_tire_une_seule_fois_meme_repete():
    phrase = Phrase(
        id=1,
        variant_id=1,
        text="{x} puis {x}",
        slots=(PhraseSlot(id=1, phrase_id=1, slot_name="x", dictionary_key="adjectifs"),),
    )
    for graine in range(20):
        gauche, droite = render(phrase, JOUEUR, CONTEXTE, seed=graine, dictionaries=SLOTS_SYNTHETIQUES).split(" puis ")
        assert gauche == droite


def test_dictionnaire_absent_ou_vide_leve_slot_resolution_error():
    phrase = _phrase_a_dictionnaires()
    with pytest.raises(SlotResolutionError, match="exclamations_but"):
        render(phrase, JOUEUR, CONTEXTE, dictionaries={"adjectifs": [{"value": "x"}]})
    with pytest.raises(SlotResolutionError, match="exclamations_but"):
        render(phrase, JOUEUR, CONTEXTE, dictionaries={"exclamations_but": [], "adjectifs": []})
    with pytest.raises(SlotResolutionError, match="exclamations_but"):
        render(phrase, JOUEUR, CONTEXTE)


# --- SlotResolutionError : slot inconnu, definition invalide ------------------


def _avec_slots(texte: str, *slots: PhraseSlot) -> Phrase:
    return Phrase(id=1, variant_id=1, text=texte, slots=slots)


def test_un_slot_du_texte_non_declare_est_nomme_dans_l_erreur():
    with pytest.raises(SlotResolutionError, match=r"\{adversaire\}"):
        render(_avec_slots("{joueur} contre {adversaire}"), JOUEUR, CONTEXTE)


@pytest.mark.parametrize(
    "expression",
    ["player.full_name()", "joueur.full_name", "player.__class__", "player.nope", "context.receveur.nope"],
)
def test_une_expression_invalide_ou_inconnue_leve_slot_resolution_error_en_nommant_le_slot(expression):
    phrase = _avec_slots("{x} marque", PhraseSlot(id=1, phrase_id=1, slot_name="x", expression=expression))
    with pytest.raises(SlotResolutionError, match=r"Slot \{x\}"):
        render(phrase, JOUEUR, CONTEXTE)


def test_un_slot_sans_expression_ni_dictionnaire_est_refuse():
    phrase = _avec_slots("{x}", PhraseSlot(id=1, phrase_id=1, slot_name="x"))
    with pytest.raises(SlotResolutionError, match="exactement un"):
        render(phrase, JOUEUR, CONTEXTE)


def test_un_slot_avec_expression_ET_dictionnaire_est_refuse():
    phrase = _avec_slots(
        "{x}",
        PhraseSlot(id=1, phrase_id=1, slot_name="x", expression="player.full_name", dictionary_key="k"),
    )
    with pytest.raises(SlotResolutionError, match="exactement un"):
        render(phrase, JOUEUR, CONTEXTE, dictionaries={"k": [{"value": "v"}]})


def test_un_slot_declare_deux_fois_avec_des_definitions_differentes_est_refuse():
    phrase = _avec_slots(
        "{x}",
        PhraseSlot(id=1, phrase_id=1, slot_name="x", expression="player.full_name"),
        PhraseSlot(id=2, phrase_id=1, slot_name="x", expression="player.last_name"),
    )
    with pytest.raises(SlotResolutionError, match="deux fois"):
        render(phrase, JOUEUR, CONTEXTE)


def test_un_slot_declare_deux_fois_a_l_identique_est_normal():
    # Le convertisseur declare un slot AUTANT de fois qu'il apparait dans le texte.
    phrase = _avec_slots(
        "{x} et {x}",
        PhraseSlot(id=1, phrase_id=1, slot_name="x", expression="player.last_name"),
        PhraseSlot(id=2, phrase_id=1, slot_name="x", expression="player.last_name"),
    )
    assert render(phrase, JOUEUR, CONTEXTE) == "Mbappé et Mbappé"


def test_un_slot_declare_mais_absent_du_texte_ne_consomme_ni_rng_ni_erreur():
    phrase = _avec_slots(
        "{joueur} marque",
        PhraseSlot(id=1, phrase_id=1, slot_name="joueur", expression="player.full_name"),
        PhraseSlot(id=2, phrase_id=1, slot_name="inutile", dictionary_key="absent"),
        PhraseSlot(id=3, phrase_id=1, slot_name="receveur", expression="context.receveur.full_name"),
    )
    assert render(phrase, JOUEUR, MatchContext(match_id="m1")) == "Kylian Mbappé marque"


@pytest.mark.parametrize(
    "dictionnaire",
    [
        [{"valeur": "x"}],  # cle "value" absente
        ["x"],  # entree non-mapping
        [{"value": "x", "weight": "lourd"}],  # poids non numerique
        [{"value": "x", "weight": -1}],  # poids negatif
        [{"value": "x", "weight": 0}],  # poids tous nuls
    ],
)
def test_un_dictionnaire_mal_forme_leve_slot_resolution_error(dictionnaire):
    phrase = _avec_slots("{x}", PhraseSlot(id=1, phrase_id=1, slot_name="x", dictionary_key="k"))
    with pytest.raises(SlotResolutionError, match=r"Slot \{x\}"):
        render(phrase, JOUEUR, CONTEXTE, dictionaries={"k": dictionnaire})


# --- rng derive par phrase : sha256(seed|code scenario|code variante|texte) -----


def test_derive_rng_suit_exactement_la_formule_sha256():
    cle = "42|BUT|SURNOM|{joueur} marque !"
    attendu = random.Random(int.from_bytes(hashlib.sha256(cle.encode("utf-8")).digest()[:8], "big"))
    obtenu = derive_rng(42, "BUT", "SURNOM", "{joueur} marque !")
    assert [obtenu.random() for _ in range(3)] == [attendu.random() for _ in range(3)]


@pytest.mark.parametrize(
    "autre",
    [
        (43, "BUT", "SURNOM", "t"),  # graine
        (42, "CORNER", "SURNOM", "t"),  # code scenario
        (42, "BUT", "DEFAUT", "t"),  # code variante
        (42, "BUT", "SURNOM", "autre texte"),  # texte
    ],
)
def test_chaque_composante_de_la_cle_change_le_rng(autre):
    reference = derive_rng(42, "BUT", "SURNOM", "t").random()
    assert derive_rng(*autre).random() != reference


@pytest.mark.parametrize(("scenario", "variante"), [("", "DEFAUT"), ("BUT", "")])
def test_un_code_vide_est_refuse(scenario, variante):
    with pytest.raises(ValueError, match="obligatoires"):
        derive_rng(1, scenario, variante, "t")
    with pytest.raises(ValueError, match="obligatoires"):
        render_phrase(
            Phrase(id=1, variant_id=1, text="t"), JOUEUR, CONTEXTE, seed=1, scenario_code=scenario, variant_code=variante
        )


def test_le_rendu_d_une_phrase_ne_depend_pas_des_autres_phrases_du_pool():
    """Ajouter ou retirer une phrase du pool ne change le rendu d'aucune autre (cle naturelle,
    pas d'etat partage) -- avec un rng global, retirer B decalerait les tirages de C."""
    adjectifs = {"adjectifs": [{"value": v} for v in ("a", "b", "c", "d", "e", "f", "g", "h")]}

    def phrase(texte: str) -> Phrase:
        return _avec_slots(texte, PhraseSlot(id=1, phrase_id=1, slot_name="x", dictionary_key="adjectifs"))

    pool = [phrase("A {x}"), phrase("B {x}"), phrase("C {x}")]
    complet = [render(p, JOUEUR, CONTEXTE, seed=5, dictionaries=adjectifs) for p in pool]
    sans_b = [render(p, JOUEUR, CONTEXTE, seed=5, dictionaries=adjectifs) for p in (pool[0], pool[2])]
    assert sans_b == [complet[0], complet[2]]


def test_la_graine_fait_varier_le_rendu():
    phrase = _avec_slots("{x}", PhraseSlot(id=1, phrase_id=1, slot_name="x", dictionary_key="k"))
    dictionnaire = {"k": [{"value": str(i)} for i in range(10)]}
    rendus = {render(phrase, JOUEUR, CONTEXTE, seed=graine, dictionaries=dictionnaire) for graine in range(30)}
    assert len(rendus) > 3


def test_meme_entree_meme_rendu_quelle_que_soit_la_graine_de_hachage_de_python():
    """sha256, pas hash() : le rendu ne depend pas de PYTHONHASHSEED."""
    code = (
        "from engine.template_filler import derive_rng;"
        "print(derive_rng(7, 'BUT', 'DEFAUT', 'texte').random())"
    )
    resultats = set()
    for graine_de_hachage in ("1", "2", "random"):
        sortie = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            check=True,
            env={**__import__("os").environ, "PYTHONHASHSEED": graine_de_hachage},
            cwd=str(Path(__file__).resolve().parent.parent),
        )
        resultats.add(sortie.stdout.strip())
    assert len(resultats) == 1

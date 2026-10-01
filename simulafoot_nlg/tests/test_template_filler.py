"""template_filler.render : slots a expression resolus sur les vrais objets (Player,
MatchContext), y compris sur la banque reelle (v1 + 8 pilotes)."""

from __future__ import annotations

import random
import re
from pathlib import Path

import pytest
import yaml

from engine.models import MatchContext, Phrase, PhraseSlot, Player
from engine.template_filler import SlotResolutionError, render
from scripts.convert_commentary_xlsx_to_yaml import SLOT_EXPRESSIONS

SEED = Path(__file__).resolve().parent.parent / "data" / "seed"


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
    rendu = render(_phrase_a_dictionnaires(), JOUEUR, CONTEXTE, rng=random.Random(1), dictionaries=SLOTS_SYNTHETIQUES)
    exclamations = [e["value"] for e in SLOTS_SYNTHETIQUES["exclamations_but"]]
    adjectifs = [e["value"] for e in SLOTS_SYNTHETIQUES["adjectifs"]]
    assert any(f"Kylian Mbappé frappe, {x} Un geste {a}." == rendu for x in exclamations for a in adjectifs)


def test_meme_graine_meme_rendu_et_les_tirages_suivent_l_ordre_des_slots():
    def rendre(graine: int) -> str:
        return render(
            _phrase_a_dictionnaires(), JOUEUR, CONTEXTE, rng=random.Random(graine), dictionaries=SLOTS_SYNTHETIQUES
        )

    assert rendre(7) == rendre(7)
    # Consommation previsible : un tirage pondere par slot a dictionnaire, dans l'ordre de phrase.slots.
    rng = random.Random(7)
    exclamation = rng.choices(["quelle frappe !", "magnifique !", "personne ne s'y attendait !"], weights=[1.0, 0.5, 1.0])[0]
    adjectif = rng.choices(["exceptionnel", "rare"], weights=[1.0, 1.0])[0]
    assert rendre(7) == f"Kylian Mbappé frappe, {exclamation} Un geste {adjectif}."


def test_les_poids_sont_respectes():
    dictionnaire = {"k": [{"value": "A", "weight": 1.0}, {"value": "B", "weight": 0.0}]}
    phrase = Phrase(
        id=1, variant_id=1, text="{x}", slots=(PhraseSlot(id=1, phrase_id=1, slot_name="x", dictionary_key="k"),)
    )
    rng = random.Random(0)
    assert {render(phrase, JOUEUR, CONTEXTE, rng=rng, dictionaries=dictionnaire) for _ in range(50)} == {"A"}


def test_un_slot_a_dictionnaire_tire_une_seule_fois_meme_repete():
    phrase = Phrase(
        id=1,
        variant_id=1,
        text="{x} puis {x}",
        slots=(PhraseSlot(id=1, phrase_id=1, slot_name="x", dictionary_key="adjectifs"),),
    )
    for graine in range(20):
        gauche, droite = render(phrase, JOUEUR, CONTEXTE, rng=random.Random(graine), dictionaries=SLOTS_SYNTHETIQUES).split(" puis ")
        assert gauche == droite


def test_dictionnaire_absent_ou_vide_leve_slot_resolution_error():
    phrase = _phrase_a_dictionnaires()
    with pytest.raises(SlotResolutionError, match="exclamations_but"):
        render(phrase, JOUEUR, CONTEXTE, rng=random.Random(1), dictionaries={"adjectifs": [{"value": "x"}]})
    with pytest.raises(SlotResolutionError, match="exclamations_but"):
        render(phrase, JOUEUR, CONTEXTE, rng=random.Random(1), dictionaries={"exclamations_but": [], "adjectifs": []})
    with pytest.raises(SlotResolutionError, match="exclamations_but"):
        render(phrase, JOUEUR, CONTEXTE, rng=random.Random(1))


def test_un_slot_a_dictionnaire_sans_rng_est_refuse():
    with pytest.raises(ValueError, match="rng obligatoire"):
        render(_phrase_a_dictionnaires(), JOUEUR, CONTEXTE, dictionaries=SLOTS_SYNTHETIQUES)

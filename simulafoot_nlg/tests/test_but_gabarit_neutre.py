"""B2 n°6 : la racine emet un but sans passeur (corner / coup_franc / construction_placee) avec le gabarit
`percee_individuelle`, pour que `event_to_scenario` renvoie BUT (engine/nlg_ingestion.py, cote racine).
Garde-fou cote NLG : aucune phrase de BUT ne conditionne ce gabarit, ni positivement ni par exclusion --
sinon le gabarit neutre changerait la selection du texte."""

from __future__ import annotations

from pathlib import Path

import yaml

from engine.narrative_adapter import event_to_scenario

SEED = Path(__file__).resolve().parent.parent / "data" / "seed"
GABARIT_NEUTRE = "percee_individuelle"


def _phrases_but() -> list[dict]:
    phrases: list[dict] = []
    for fichier in sorted(SEED.rglob("*.yml")):
        contenu = yaml.safe_load(fichier.read_text(encoding="utf-8"))
        if not isinstance(contenu, list):
            continue
        for scenario in contenu:
            if isinstance(scenario, dict) and scenario.get("code") == "BUT":
                for variante in scenario["variants"]:
                    phrases.extend(variante["phrases"])
    return phrases


def test_le_gabarit_neutre_mene_a_but():
    base = {"event_type": "but", "gabarit": GABARIT_NEUTRE}
    assert event_to_scenario(base) == "BUT"


def test_banque_but_non_vide():
    assert len(_phrases_but()) >= 50  # garde-fou : la banque est bien lue (v1 : 281 phrases, tous scenarios)


def test_aucune_phrase_de_but_ne_conditionne_le_gabarit_neutre():
    for phrase in _phrases_but():
        for condition in phrase["conditions"]:
            if condition["attribute"] == "gabarit":
                # seul `== "penalty"` existe : percee_individuelle ne l'active pas
                assert (condition["operator"], condition["value"]) == ("==", '"penalty"'), phrase["text"]
        assert GABARIT_NEUTRE not in str(phrase), phrase["text"]


def test_les_conditions_de_gabarit_de_but_sont_toutes_penalty():
    valeurs = {
        c["value"]
        for p in _phrases_but()
        for c in p["conditions"]
        if c["attribute"] == "gabarit"
    }
    assert valeurs <= {'"penalty"'}

"""engine/narrative_adapter.py : (event_type, gabarit, outcome) -> scenario_code (D12)."""

from __future__ import annotations

from itertools import product
from pathlib import Path
from typing import get_args

import pytest
import yaml

from engine.event_contract import GABARITS, OutcomeCarton, OutcomeOccasion
from engine.narrative_adapter import (
    OUTCOMES_NON_COMMENTES,
    SCENARIOS_ATTEIGNABLES,
    SCENARIOS_DIFFERES,
    SCENARIOS_STRUCTURELS,
    event_to_scenario,
)
from scripts.convert_commentary_xlsx_to_yaml import PILOTES_METADATA

V1_PATH = Path(__file__).resolve().parent.parent / "data" / "seed" / "scenarios.yml"
OUTCOMES_OCCASION: tuple[str, ...] = get_args(OutcomeOccasion)
OUTCOMES_CARTON: tuple[str, ...] = get_args(OutcomeCarton)


def _but(gabarit: str) -> dict:
    return {"event_type": "but", "gabarit": gabarit}


def _occasion(gabarit: str, outcome: str) -> dict:
    return {"event_type": "occasion", "gabarit": gabarit, "outcome": outcome}


@pytest.mark.parametrize(
    ("evenement", "attendu"),
    [
        # buts : gabarits a scenario propre, tout le reste -> BUT (penalty compris : variante PENALTY)
        (_but("coup_franc"), "COUP_FRANC"),
        (_but("construction_placee"), "CONSTRUCTION"),
        (_but("corner"), "CORNER"),
        (_but("penalty"), "BUT"),
        (_but("contre_attaque"), "BUT"),
        (_but("but_gag"), "BUT"),
        # occasions : arret -> ARRET_GARDIEN quel que soit le gabarit (decision D12 pour penalty)
        (_occasion("penalty", "arret"), "ARRET_GARDIEN"),
        (_occasion("corner", "arret"), "ARRET_GARDIEN"),
        (_occasion("une_deux", "arret"), "ARRET_GARDIEN"),
        # penalty rate hors cadre
        (_occasion("penalty", "hors_cadre"), "PENALTY_RATE"),
        # occasions ordinaires, y compris sur gabarit corner / coup_franc
        (_occasion("une_deux", "hors_cadre"), "TIR_NON_CADRE"),
        (_occasion("corner", "hors_cadre"), "TIR_NON_CADRE"),
        (_occasion("coup_franc", "tacle"), "DEFENSE"),
        (_occasion("contre_attaque", "degagement"), "DEFENSE"),
        # cartons et remplacements
        ({"event_type": "carton", "outcome": "yellow"}, "CARTON_JAUNE"),
        ({"event_type": "carton", "outcome": "direct"}, "CARTON_ROUGE"),
        ({"event_type": "carton", "outcome": "second_yellow"}, "CARTON_ROUGE"),
        ({"event_type": "remplacement"}, "REMPLACEMENT"),
    ],
)
def test_table_de_correspondance(evenement, attendu):
    assert event_to_scenario(evenement) == attendu


@pytest.mark.parametrize("gabarit", GABARITS)
@pytest.mark.parametrize("outcome", sorted(OUTCOMES_NON_COMMENTES))
def test_poteau_et_barre_ne_sont_pas_commentes_en_v2_1_quel_que_soit_le_gabarit(gabarit, outcome):
    assert event_to_scenario(_occasion(gabarit, outcome)) is None


def test_poteau_et_barre_sont_les_seuls_outcomes_non_commentes():
    assert OUTCOMES_NON_COMMENTES == {"poteau", "barre"}


@pytest.mark.parametrize("outcome", ["tacle", "degagement"])
def test_un_penalty_ne_peut_etre_ni_tacle_ni_degage(outcome):
    with pytest.raises(ValueError, match="hors domaine"):
        event_to_scenario(_occasion("penalty", outcome))


@pytest.mark.parametrize("evenement", [_occasion("une_deux", "but"), {"event_type": "carton", "outcome": "rouge"}])
def test_un_outcome_inconnu_est_refuse(evenement):
    with pytest.raises(ValueError, match="hors domaine"):
        event_to_scenario(evenement)


def test_un_event_type_inconnu_est_refuse():
    with pytest.raises(ValueError, match="event_type inconnu"):
        event_to_scenario({"event_type": "corner"})  # corner est un gabarit


def _domaine_complet() -> list[dict]:
    evenements = [_but(g) for g in GABARITS]
    evenements += [_occasion(g, o) for g, o in product(GABARITS, OUTCOMES_OCCASION)]
    evenements += [{"event_type": "carton", "outcome": o} for o in OUTCOMES_CARTON]
    evenements.append({"event_type": "remplacement"})
    return evenements


def test_scenarios_atteignables_est_exactement_l_image_du_domaine():
    images = set()
    for evenement in _domaine_complet():
        try:
            code = event_to_scenario(evenement)
        except ValueError:  # penalty + tacle/degagement : hors domaine du moteur
            continue
        if code is not None:
            images.add(code)
    assert images == SCENARIOS_ATTEIGNABLES


def _codes_importes() -> set[str]:
    banque = yaml.safe_load(V1_PATH.read_text(encoding="utf-8"))
    return {s["code"] for s in banque} | set(PILOTES_METADATA)


def test_mappes_union_inatteignables_egale_les_scenarios_importes_et_les_ensembles_sont_disjoints():
    mappes, structurels, differes = set(SCENARIOS_ATTEIGNABLES), set(SCENARIOS_STRUCTURELS), set(SCENARIOS_DIFFERES)
    assert mappes | structurels | differes == _codes_importes()
    assert not mappes & structurels
    assert not mappes & differes
    assert not structurels & differes
    assert len(_codes_importes()) == 17


def test_chaque_scenario_inatteignable_a_une_raison():
    for raisons in (SCENARIOS_STRUCTURELS, SCENARIOS_DIFFERES):
        assert all(raison.strip() for raison in raisons.values())


def test_les_trois_pilotes_sans_source_sont_differes_a_v2_2_et_les_traits_et_contextes_sont_structurels():
    assert set(SCENARIOS_DIFFERES) == {"FAUTE_SIMPLE", "HORS_JEU", "AMBIANCE"}  # D13
    assert set(SCENARIOS_STRUCTURELS) == {"DEBUT_MATCH", "SITUATION_MATCH", "GESTE_SIGNATURE"}

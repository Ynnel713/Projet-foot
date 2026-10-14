"""B6-e (ticket 23) : le NLG recoit `strike_type` (contrat, contexte, conditions) et la banque ne decrit que la frappe vue a l'ecran."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pytest
import yaml

from engine.conditions import evaluate_condition, parse_condition_atoms
from engine.event_contract import STRIKE_TYPES, validate_event
from engine.models import PhraseCondition
from engine.profile_engine import normalize_match_context
from tests.test_conditions import _context, _player
from tests.test_event_contract import but, carton, occasion

SEED = Path(__file__).resolve().parent.parent / "data" / "seed"
NEUF_TYPES = (
    "shot_tendu", "shot_enroule_leger", "shot_enroule_fort", "shot_exterieur_pied", "reprise_vollee", "tete",
    "penalty_fort", "penalty_place", "penalty_contre_pied",
)
CURVE = {"shot_enroule_leger", "shot_enroule_fort"}


def test_le_contrat_admet_les_neuf_types():
    assert STRIKE_TYPES == NEUF_TYPES


@pytest.mark.parametrize("fabrique", [but, occasion])
@pytest.mark.parametrize("valeur", [*NEUF_TYPES, None])
def test_un_but_ou_une_occasion_accepte_chaque_type_ou_none(fabrique, valeur):
    validate_event(fabrique(strike_type=valeur))


@pytest.mark.parametrize("fabrique", [but, occasion])
def test_la_cle_est_optionnelle(fabrique):
    validate_event(fabrique())  # anciens flux et dicts ecrits a la main


@pytest.mark.parametrize("fabrique", [but, occasion])
@pytest.mark.parametrize("valeur", ["lob", "", 3, True])
def test_un_type_hors_contrat_est_refuse(fabrique, valeur):
    with pytest.raises(ValueError, match="strike_type"):
        validate_event(fabrique(strike_type=valeur))


def test_un_carton_refuse_la_cle():
    with pytest.raises(ValueError, match="cles inconnues"):
        validate_event(carton(strike_type="tete"))


def test_le_contexte_porte_le_type():
    assert normalize_match_context({"match_id": "m", "strike_type": "tete"}).strike_type == "tete"
    assert normalize_match_context({"match_id": "m"}).strike_type is None


class TestConditionStrikeType:
    @staticmethod
    def _condition() -> PhraseCondition:
        (atome,) = parse_condition_atoms("strike_type in [shot_enroule_leger, shot_enroule_fort]")
        return PhraseCondition(id=1, phrase_id=1, attribute=atome.attribute, operator=atome.operator, value=atome.value)

    @pytest.mark.parametrize("type_", sorted(CURVE))
    def test_matche_un_type_de_la_liste(self, type_):
        assert evaluate_condition(self._condition(), _player(), _context(strike_type=type_)) is True

    @pytest.mark.parametrize("type_", ["shot_tendu", "tete", "penalty_fort", None])
    def test_ne_matche_ni_un_autre_type_ni_un_type_absent(self, type_):
        assert evaluate_condition(self._condition(), _player(), _context(strike_type=type_)) is False


# --- Garde-fou de banque : un style n'est decrit que pour le(s) type(s) qui le portent ------------------------------------
_SCENARIOS = {"BUT", "ARRET_GARDIEN", "TIR_NON_CADRE", "PENALTY_RATE"}  # les seuls atteignables avec une frappe (narrative_adapter)
_PENALTY_SEULEMENT = {("BUT", "PENALTY"), ("PENALTY_RATE", "DEFAUT")}  # gabarit penalty : types penalty_*, jamais de tete
_NON_FRAPPES = {  # mots de frappe qui n'en decrivent pas une (dribble, idiome, surnom, centre-tir)
    ("BUT", "DEFAUT", 8), ("BUT", "SURNOM", 13), ("ARRET_GARDIEN", "DEFAUT", 18), ("ARRET_GARDIEN", "DEFAUT", 23),
    ("ARRET_GARDIEN", "DEFAUT", 24),  # le gardien devance l'attaquant "avant qu'il ne puisse frapper" : aucune frappe
}
_MOT_ENROULE = re.compile(r"enroul", re.I)
_MOT_VOLEE = re.compile(r"volée|retournée", re.I)
_MOT_EXTERIEUR = re.compile(r"extérieur du pied", re.I)
_MOT_TETE = re.compile(r"\b(de la tête|une tête|cette tête|tête (rageuse|surpuissante|plongeante|dangereuse))", re.I)
_MOT_PIED = re.compile(r"\b(frappe|frappes|frappé|frapper|tir|tirs|tire|tirer|missile|bombe|du pied|d'un pied)\b", re.I)


def _phrases():
    for fichier in (SEED / "scenarios.yml", SEED / "v2" / "tir_non_cadre.yml"):
        for scenario in yaml.safe_load(fichier.read_text(encoding="utf-8")):
            if scenario["code"] not in _SCENARIOS:
                continue
            for variante in scenario["variants"]:
                for rang, phrase in enumerate(variante["phrases"]):
                    admis: set[str] | None = None
                    for c in phrase.get("conditions", []):
                        if c["attribute"] == "strike_type":
                            admis = {v.strip() for v in c["value"].split(",")}
                    yield scenario["code"], variante["code"], rang, " ".join(phrase["text"].split()), admis


@pytest.mark.parametrize(
    ("motif", "types"),
    [(_MOT_ENROULE, CURVE), (_MOT_VOLEE, {"reprise_vollee"}), (_MOT_EXTERIEUR, {"shot_exterieur_pied"}), (_MOT_TETE, {"tete"})],
    ids=["enroule", "volee", "exterieur", "tete"],
)
def test_une_phrase_qui_nomme_un_style_est_reservee_aux_types_de_ce_style(motif, types):
    fautives = [(s, v, r, t[:60]) for s, v, r, t, admis in _phrases() if motif.search(t) and (admis is None or not admis <= types)]
    assert fautives == []


def test_une_phrase_de_frappe_au_pied_exclut_la_tete():
    fautives = [
        (s, v, r, t[:60])
        for s, v, r, t, admis in _phrases()
        if _MOT_PIED.search(t) and not _MOT_TETE.search(t) and (s, v) not in _PENALTY_SEULEMENT
        and (s, v, r) not in _NON_FRAPPES and (admis is None or "tete" in admis)
    ]
    assert fautives == []


def test_les_phrases_de_penalty_ne_citent_que_des_types_de_penalty():
    fautives = [
        (s, v, r) for s, v, r, _t, admis in _phrases()
        if admis and (s, v) in _PENALTY_SEULEMENT and not admis <= {"penalty_fort", "penalty_place", "penalty_contre_pied"}
    ]
    assert fautives == []

"""PILOTES_METADATA (scripts/convert_commentary_xlsx_to_yaml.py) face aux modules
pilotes_v2/*.py : bijection module <-> code et egalite STRICTE des slots."""

from __future__ import annotations

import re
from pathlib import Path
from types import ModuleType

import pytest
import yaml

from scripts.convert_commentary_xlsx_to_yaml import PILOTES_METADATA
from tests.test_pilotes_v2_garde_fous import _pilotes

V1_SCENARIOS_PATH = Path(__file__).resolve().parent.parent / "data" / "seed" / "scenarios.yml"


def _nom(module: ModuleType) -> str:
    return module.__name__.rsplit(".", 1)[-1]


def _slots_utilises(module: ModuleType) -> set[str]:
    textes = [texte for texte, _ in module.DEFAUT + getattr(module, "SURNOM", [])]
    return {slot for texte in textes for slot in re.findall(r"\{(\w+)\}", texte)}


def test_bijection_module_code():
    modules = {_nom(m).upper() for m in _pilotes()}
    assert modules == set(PILOTES_METADATA)


@pytest.mark.parametrize("pilote", _pilotes(), ids=_nom)
def test_slots_utilises_egalent_slots_declares(pilote):
    declares = set(PILOTES_METADATA[_nom(pilote).upper()].slots)
    assert _slots_utilises(pilote) == declares


def test_aucun_code_pilote_n_entre_en_collision_avec_la_banque_v1():
    codes_v1 = {s["code"] for s in yaml.safe_load(V1_SCENARIOS_PATH.read_text(encoding="utf-8"))}
    assert not codes_v1 & set(PILOTES_METADATA)


@pytest.mark.parametrize("code", sorted(PILOTES_METADATA))
def test_code_en_majuscules_sans_accent_ni_tiret(code):
    assert re.fullmatch(r"[A-Z]+(_[A-Z]+)*", code)

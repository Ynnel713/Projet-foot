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


# --- Derivation dans le convertisseur et couverture des expressions de slots ---

from scripts.convert_commentary_xlsx_to_yaml import (  # noqa: E402
    DEFAULT_COOLDOWN_MATCHES_BY_SCENARIO,
    SLOT_EXPRESSIONS,
    SLOTS_AUTORISES,
)


def test_slots_et_cooldowns_derives_couvrent_exactement_v1_et_v2_avec_les_bonnes_valeurs():
    codes_v1 = {s["code"] for s in yaml.safe_load(V1_SCENARIOS_PATH.read_text(encoding="utf-8"))}
    assert set(SLOTS_AUTORISES) == codes_v1 | set(PILOTES_METADATA)
    assert set(DEFAULT_COOLDOWN_MATCHES_BY_SCENARIO) == set(SLOTS_AUTORISES)
    for code, meta in PILOTES_METADATA.items():
        assert SLOTS_AUTORISES[code] == meta.slots
        assert DEFAULT_COOLDOWN_MATCHES_BY_SCENARIO[code] == meta.cooldown_matches


def _contexte_et_joueurs():
    from engine.models import MatchContext, Player

    def joueur(prenom: str, nom: str) -> Player:
        return Player(id=1, first_name=prenom, last_name=nom)

    context = MatchContext(
        match_id="m1",
        minute=67,
        home_team="Lyon",
        away_team="Marseille",
        is_home=True,
        player_team="Lyon",
        passeur=joueur("Alexandre", "Lacazette"),
        receveur=joueur("Moussa", "Tagliafico"),
        sortant=joueur("Ousmane", "Dembélé"),
        entrant=joueur("Rayan", "Cherki"),
    )
    return joueur("Kylian", "Mbappé"), context


def _resoudre(expression: str, player, context):
    racine, *chemin = expression.split(".")
    valeur = {"player": player, "context": context}[racine]
    for attribut in chemin:
        valeur = getattr(valeur, attribut)
    return valeur


@pytest.mark.parametrize("slot", sorted({s for slots in SLOTS_AUTORISES.values() for s in slots}))
def test_tout_slot_autorise_a_une_expression_qui_se_resout_sur_les_vrais_objets(slot):
    player, context = _contexte_et_joueurs()
    assert slot in SLOT_EXPRESSIONS
    assert _resoudre(SLOT_EXPRESSIONS[slot], player, context) not in (None, "")


def test_sortant_et_entrant_se_resolvent_sur_leur_propre_joueur():
    player, context = _contexte_et_joueurs()
    assert _resoudre(SLOT_EXPRESSIONS["sortant"], player, context) == "Ousmane Dembélé"
    assert _resoudre(SLOT_EXPRESSIONS["entrant"], player, context) == "Rayan Cherki"

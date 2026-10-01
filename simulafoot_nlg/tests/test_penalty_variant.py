"""penalty-variant (SPEC_ANTI_REPEAT.md section 10) : la variante BUT/PENALTY ne
sort que pour un vrai penalty. Sans condition `gabarit == "penalty"`, ses 15 phrases
(sans autre condition) seraient toujours candidates et, essayees avant SURNOM et
DEFAUT, commenteraient tout BUT comme un penalty."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from engine.conditions import evaluate_condition
from engine.models import MatchContext, PhraseCondition, Player

SCENARIOS_PATH = Path(__file__).resolve().parent.parent / "data" / "seed" / "scenarios.yml"


def _variantes_de_but() -> dict[str, list[dict]]:
    banque = yaml.safe_load(SCENARIOS_PATH.read_text(encoding="utf-8"))
    but = next(s for s in banque if s["code"] == "BUT")
    return {v["code"]: v["phrases"] for v in but["variants"]}


def _conditions(phrase: dict) -> list[PhraseCondition]:
    return [
        PhraseCondition(
            id=i,
            phrase_id=0,
            attribute=c["attribute"],
            operator=c["operator"],
            value=str(c["value"]),
            mandatory=c.get("mandatory", True),
        )
        for i, c in enumerate(phrase["conditions"])
    ]


def _candidates(phrases: list[dict], gabarit: str | None) -> int:
    """Phrases dont TOUTES les conditions mandatory matchent (joueur sans attribut)."""
    joueur = Player(id=1, first_name="Kylian", last_name="Mbappé")
    contexte = MatchContext(match_id="m1", gabarit=gabarit)
    return sum(
        all(evaluate_condition(c, joueur, contexte) for c in _conditions(p) if c.mandatory) for p in phrases
    )


def test_la_variante_penalty_existe_et_compte_15_phrases():
    assert len(_variantes_de_but()["PENALTY"]) == 15


def test_chaque_phrase_penalty_porte_la_condition_mandatory_gabarit_penalty():
    for phrase in _variantes_de_but()["PENALTY"]:
        assert {
            "attribute": "gabarit",
            "operator": "==",
            "value": '"penalty"',
            "mandatory": True,
        } in phrase["conditions"], phrase["text"]


def test_aucune_autre_phrase_de_la_banque_ne_conditionne_sur_gabarit():
    banque = yaml.safe_load(SCENARIOS_PATH.read_text(encoding="utf-8"))
    hors_penalty = [
        (s["code"], v["code"])
        for s in banque
        for v in s["variants"]
        for p in v["phrases"]
        if any(c["attribute"] == "gabarit" for c in p["conditions"]) and (s["code"], v["code"]) != ("BUT", "PENALTY")
    ]
    assert hors_penalty == []


@pytest.mark.parametrize("gabarit", ["contre_attaque", "construction_placee", "corner", "coup_franc", "but_gag", None])
def test_un_but_ordinaire_n_a_aucune_phrase_penalty_candidate(gabarit):
    assert _candidates(_variantes_de_but()["PENALTY"], gabarit) == 0


def test_un_vrai_penalty_a_ses_15_phrases_candidates():
    assert _candidates(_variantes_de_but()["PENALTY"], "penalty") == 15


@pytest.mark.parametrize("gabarit", ["contre_attaque", "penalty"])
def test_defaut_et_surnom_ne_dependent_pas_du_gabarit(gabarit):
    variantes = _variantes_de_but()
    sans_condition_de_gabarit = [p for p in variantes["DEFAUT"] if not p["conditions"]]
    assert _candidates(sans_condition_de_gabarit, gabarit) == len(sans_condition_de_gabarit) > 0

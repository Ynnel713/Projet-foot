"""data/seed/fallback/*.yml (D10) : une phrase de secours par scenario, sobre, sans slot,
et importable avec la banque v1 + les 8 pilotes."""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

import yaml

from scripts.convert_commentary_xlsx_to_yaml import PILOTES_METADATA
from scripts.convert_pilotes_to_yaml import convertir_pilotes
from scripts.import_seed import (
    DEFAULT_FALLBACK_DIR,
    DEFAULT_SCENARIOS_PATH,
    DEFAULT_SLOTS_PATH,
    import_seed,
)
from scripts.init_db import init_db

LONGUEUR_MAX = 80  # une courte phrase : un fallback ne vole jamais la vedette


def _fallbacks() -> list[dict[str, str]]:
    return [
        entree
        for fichier in sorted(DEFAULT_FALLBACK_DIR.glob("*.yml"))
        for entree in yaml.safe_load(fichier.read_text(encoding="utf-8"))
    ]


def _codes_attendus() -> set[str]:
    banque = yaml.safe_load(DEFAULT_SCENARIOS_PATH.read_text(encoding="utf-8"))
    return {s["code"] for s in banque} | set(PILOTES_METADATA)


def test_exactement_un_fallback_par_scenario_des_17_scenarios():
    codes = [e["scenario"] for e in _fallbacks()]
    assert sorted(codes) == sorted(_codes_attendus())
    assert len(codes) == 17


def test_ton_sobre_sans_slot_sans_exclamation_et_court():
    for entree in _fallbacks():
        texte = entree["text"]
        assert not re.search(r"\{\w+\}", texte), texte
        assert "!" not in texte, texte
        assert texte.endswith("."), texte
        assert 0 < len(texte) <= LONGUEUR_MAX, texte


def test_les_17_textes_sont_distincts():
    textes = [e["text"] for e in _fallbacks()]
    assert len(textes) == len(set(textes))


def test_la_banque_complete_s_importe_avec_un_fallback_par_scenario(tmp_path):
    convertir_pilotes(tmp_path / "v2")
    db_path = tmp_path / "test.db"
    init_db(db_path=db_path)

    stats = import_seed(
        db_path,
        [DEFAULT_SCENARIOS_PATH, *sorted((tmp_path / "v2").glob("*.yml"))],
        DEFAULT_SLOTS_PATH,
        fallback_path=sorted(DEFAULT_FALLBACK_DIR.glob("*.yml")),
    )

    assert (stats.scenarios, stats.phrases, stats.fallbacks) == (17, 494, 17)
    conn = sqlite3.connect(db_path)
    try:
        par_scenario = conn.execute(
            """SELECT s.code, COUNT(p.id) FROM scenarios s
               LEFT JOIN variants v ON v.scenario_id = s.id
               LEFT JOIN phrases p ON p.variant_id = v.id AND p.is_fallback = 1
               GROUP BY s.code"""
        ).fetchall()
    finally:
        conn.close()
    assert len(par_scenario) == 17 and all(n == 1 for _, n in par_scenario)

"""Tests d'import_seed.import_seed -- en particulier la regle "cooldown
obligatoire" (voir README.md et AUDIT_EDITORIAL_2026-09-30.md) : toute phrase
importee doit produire une ligne dans phrase_cooldowns, jamais un
cooldown_matches NULL."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import pytest
import yaml

from scripts.import_seed import SeedValidationError, _validate_scenarios, import_seed

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "data" / "schema.sql"


def _init_db(tmp_path: Path) -> Path:
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    conn.commit()
    conn.close()
    return db_path


def _write_scenarios_yaml(
    tmp_path: Path, cooldown_matches: int | None, conditions: list[dict[str, Any]] | None = None
) -> Path:
    phrase: dict[str, Any] = {"text": "{joueur} marque !", "weight": 1.0}
    if cooldown_matches is not None:
        phrase["cooldown_matches"] = cooldown_matches
    if conditions is not None:
        phrase["conditions"] = conditions
    scenarios = [
        {
            "code": "BUT",
            "label": "But",
            "variants": [
                {"code": "DEFAUT", "label": "Défaut", "is_default": True, "phrases": [phrase]}
            ],
        }
    ]
    path = tmp_path / "scenarios.yml"
    path.write_text(yaml.safe_dump(scenarios, allow_unicode=True), encoding="utf-8")
    return path


def _write_empty_slots_yaml(tmp_path: Path) -> Path:
    path = tmp_path / "slots.yml"
    path.write_text("{}", encoding="utf-8")
    return path


class TestImportSeedCooldown:
    def test_phrase_with_cooldown_matches_is_inserted_into_phrase_cooldowns(self, tmp_path):
        db_path = _init_db(tmp_path)
        scenarios_path = _write_scenarios_yaml(tmp_path, cooldown_matches=3)
        slots_path = _write_empty_slots_yaml(tmp_path)

        stats = import_seed(db_path, scenarios_path, slots_path)
        assert stats.phrases == 1

        conn = sqlite3.connect(db_path)
        row = conn.execute(
            "SELECT p.id, pc.cooldown_matches FROM phrases p "
            "JOIN phrase_cooldowns pc ON pc.phrase_id = p.id"
        ).fetchone()
        conn.close()

        assert row is not None
        assert row[1] == 3

    def test_phrase_without_cooldown_matches_fails_the_whole_import(self, tmp_path):
        import pytest

        from scripts.import_seed import SeedValidationError

        db_path = _init_db(tmp_path)
        scenarios_path = _write_scenarios_yaml(tmp_path, cooldown_matches=None)
        slots_path = _write_empty_slots_yaml(tmp_path)

        with pytest.raises(SeedValidationError, match="cooldown_matches"):
            import_seed(db_path, scenarios_path, slots_path)

        # Import refuse "tout ou rien" (voir docstring du module) : aucune
        # ligne ne doit avoir ete ecrite, meme dans scenarios/variants.
        conn = sqlite3.connect(db_path)
        n_scenarios = conn.execute("SELECT COUNT(*) FROM scenarios").fetchone()[0]
        conn.close()
        assert n_scenarios == 0


class TestImportSeedConditionOperators:
    """Non-regression du bug trouve au 1er import reel des 281 phrases
    (30/09/2026) : le CHECK de phrase_conditions.operator n'incluait pas
    'contient' (56 occurrences dans la banque reelle) ni '=' -- pourtant
    tous deux acceptes par engine.conditions.evaluate_condition. Aucun test
    existant ne le detectait : ceux d'import_seed ne posaient jamais de
    condition, ceux de convert_commentary ne testaient que la validation
    structurelle (_validate_scenarios), jamais une vraie insertion SQLite."""

    def test_contient_operator_is_accepted_by_the_schema(self, tmp_path):
        db_path = _init_db(tmp_path)
        scenarios_path = _write_scenarios_yaml(
            tmp_path,
            cooldown_matches=3,
            conditions=[
                {"attribute": "preferred_moves", "operator": "contient", "value": "Shoots With Power"}
            ],
        )
        slots_path = _write_empty_slots_yaml(tmp_path)

        stats = import_seed(db_path, scenarios_path, slots_path)
        assert stats.phrases == 1

        conn = sqlite3.connect(db_path)
        row = conn.execute("SELECT operator FROM phrase_conditions").fetchone()
        conn.close()
        assert row[0] == "contient"


class TestImportSeedNomsDAttributs:
    """D16-fine : un nom d'attribut inconnu fait echouer l'import (tout ou rien) ;
    les noms valides (FM26, champ Player, champ de contexte, preferred_moves) passent,
    y compris ceux que certains joueurs n'ont pas (ecartes a l'execution, pas ici)."""

    @staticmethod
    def _importer(tmp_path: Path, attribute: str) -> Path:
        db_path = _init_db(tmp_path)
        scenarios_path = _write_scenarios_yaml(
            tmp_path,
            cooldown_matches=3,
            conditions=[{"attribute": attribute, "operator": ">=", "value": "70"}],
        )
        import_seed(db_path, scenarios_path, _write_empty_slots_yaml(tmp_path))
        return db_path

    def test_une_faute_de_frappe_fait_echouer_l_import_et_suggere_le_bon_nom(self, tmp_path):
        db_path = _init_db(tmp_path)
        scenarios_path = _write_scenarios_yaml(
            tmp_path,
            cooldown_matches=3,
            conditions=[{"attribute": "Aggresion", "operator": ">=", "value": "70"}],
        )
        with pytest.raises(SeedValidationError, match="Aggresion.*Aggression"):
            import_seed(db_path, scenarios_path, _write_empty_slots_yaml(tmp_path))

        conn = sqlite3.connect(db_path)
        assert conn.execute("SELECT COUNT(*) FROM scenarios").fetchone()[0] == 0
        conn.close()

    @pytest.mark.parametrize("attribute", ["Aggression", "age", "minute", "is_home", "fm_rating"])
    def test_un_nom_valide_est_accepte(self, tmp_path, attribute):
        db_path = self._importer(tmp_path, attribute)
        conn = sqlite3.connect(db_path)
        assert conn.execute("SELECT attribute FROM phrase_conditions").fetchone()[0] == attribute
        conn.close()

    def test_toutes_les_conditions_de_la_banque_v1_sont_reconnues(self):
        banque = yaml.safe_load(
            (SCHEMA_PATH.parent / "seed" / "scenarios.yml").read_text(encoding="utf-8")
        )
        _validate_scenarios(banque, known_slot_keys=set())

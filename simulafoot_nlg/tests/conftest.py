"""Fixtures partagees -- toutes en memoire (:memory: pour SQLite, DuckDB en
RAM), jamais de fichier sur disque dans les tests (sauf test_import_players,
qui a besoin d'un vrai classeur .xlsx -- ecrit dans tmp_path, nettoye par
pytest automatiquement)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import duckdb
import pytest

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "data" / "schema.sql"


@pytest.fixture
def sqlite_conn() -> sqlite3.Connection:
    """Connexion SQLite en memoire, schema deja applique (voir
    data/schema.sql) -- row_factory=Row, foreign_keys=ON."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    yield conn
    conn.close()


@pytest.fixture
def duckdb_conn() -> duckdb.DuckDBPyConnection:
    """Connexion DuckDB en RAM (":memory:")."""
    conn = duckdb.connect(":memory:")
    yield conn
    conn.close()


@pytest.fixture
def seeded_scenario(sqlite_conn: sqlite3.Connection) -> dict[str, int]:
    """Un scenario minimal (1 variante par defaut, 1 phrase) inséré
    directement en base (pas via import_seed -- ces IDs servent aux tests de
    scenario_engine/phrase_selector, pas aux tests d'import YAML). Retourne
    les IDs generes."""
    cur = sqlite_conn.execute(
        "INSERT INTO scenarios (code, label) VALUES ('BUT_TEST', 'But de test')"
    )
    scenario_id = cur.lastrowid
    cur = sqlite_conn.execute(
        "INSERT INTO variants (scenario_id, code, label, is_default) VALUES (?, 'DEFAUT', 'Défaut', 1)",
        (scenario_id,),
    )
    variant_id = cur.lastrowid
    cur = sqlite_conn.execute(
        "INSERT INTO phrases (variant_id, text) VALUES (?, '{player_name} marque !')",
        (variant_id,),
    )
    phrase_id = cur.lastrowid
    sqlite_conn.commit()
    return {"scenario_id": scenario_id, "variant_id": variant_id, "phrase_id": phrase_id}

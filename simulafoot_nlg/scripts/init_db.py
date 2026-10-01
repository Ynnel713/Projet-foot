"""Cree/met a jour data/simulafoot.db depuis data/schema.sql.

Idempotent : schema.sql n'utilise que des CREATE TABLE/INDEX IF NOT EXISTS,
donc executer ce script plusieurs fois sur une base existante ne casse rien
(aucune table n'est recreee ni videe). CREATE TABLE IF NOT EXISTS n'ajoute pas
une colonne a une table deja existante : les colonnes ajoutees apres coup sont
listees dans _COLONNES_AJOUTEES_APRES_COUP et creees par ALTER TABLE si
absentes."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from engine.db import get_sqlite

DEFAULT_SCHEMA_PATH = Path(__file__).resolve().parent.parent / "data" / "schema.sql"
DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "simulafoot.db"

# (table, colonne, definition SQL) -- la definition doit rester identique a
# celle de data/schema.sql (verrouille par tests/test_init_db.py).
_COLONNES_AJOUTEES_APRES_COUP: tuple[tuple[str, str, str], ...] = (
    ("phrase_history", "match_sequence", "INTEGER CHECK (match_sequence >= 0)"),
    ("phrases", "is_fallback", "INTEGER NOT NULL DEFAULT 0 CHECK (is_fallback IN (0, 1))"),
)


def _ajouter_colonnes_manquantes(conn: sqlite3.Connection) -> None:
    """A appeler AVANT schema.sql : certains index du schema portent sur une
    colonne ajoutee apres coup (idx_phrases_one_fallback_per_variant) et
    echoueraient sur une base ancienne. Table absente (base neuve) : rien a
    faire, CREATE TABLE creera la colonne."""
    for table, colonne, definition in _COLONNES_AJOUTEES_APRES_COUP:
        existantes = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
        if existantes and colonne not in existantes:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {colonne} {definition}")


def init_db(db_path: str | Path = DEFAULT_DB_PATH, schema_path: str | Path = DEFAULT_SCHEMA_PATH) -> None:
    schema_path = Path(schema_path)
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema introuvable : {schema_path}")

    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    sql = schema_path.read_text(encoding="utf-8")
    conn = get_sqlite(db_path)
    try:
        _ajouter_colonnes_manquantes(conn)
        conn.executescript(sql)
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
    print(f"Base initialisee : {DEFAULT_DB_PATH}")

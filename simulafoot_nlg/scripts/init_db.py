"""Cree/met a jour data/simulafoot.db depuis data/schema.sql.

Idempotent : schema.sql n'utilise que des CREATE TABLE/INDEX IF NOT EXISTS,
donc executer ce script plusieurs fois sur une base existante ne casse rien
(aucune table n'est recreee ni videe)."""

from __future__ import annotations

from pathlib import Path

from engine.db import get_sqlite

DEFAULT_SCHEMA_PATH = Path(__file__).resolve().parent.parent / "data" / "schema.sql"
DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "simulafoot.db"


def init_db(db_path: str | Path = DEFAULT_DB_PATH, schema_path: str | Path = DEFAULT_SCHEMA_PATH) -> None:
    schema_path = Path(schema_path)
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema introuvable : {schema_path}")

    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    sql = schema_path.read_text(encoding="utf-8")
    conn = get_sqlite(db_path)
    try:
        conn.executescript(sql)
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
    print(f"Base initialisee : {DEFAULT_DB_PATH}")

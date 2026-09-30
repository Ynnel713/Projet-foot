"""Connexions aux deux bases du projet.

SQLite (`get_sqlite`) : runtime, seule source de verite (voir data/schema.sql).
Toujours ouvert avec journal_mode=WAL (lectures concurrentes pendant une
ecriture) et foreign_keys=ON (les CASCADE du schema ne s'appliquent pas sinon).

DuckDB (`get_duckdb`) : zone d'ETL/staging + analytics (voir
data/import/import_players.py et scripts/export_analytics.py) -- jamais lu
par le moteur de generation lui-meme, uniquement par l'import et les scripts
d'analyse.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import duckdb


def get_sqlite(path: str | Path) -> sqlite3.Connection:
    """Connexion SQLite configuree pour le runtime : WAL, FK ON, lignes
    accessibles par nom de colonne (`row["player_id"]` plutot que `row[2]`).

    `path` peut etre ":memory:" (tests) -- WAL est alors ignore par SQLite
    lui-meme (pas de fichier a verrouiller), sans erreur."""
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn


def get_duckdb(path: str | Path) -> duckdb.DuckDBPyConnection:
    """Connexion DuckDB pour l'ETL/analytics. `path` peut etre ":memory:"
    (tests, ou etapes d'ETL purement transitoires)."""
    return duckdb.connect(str(path))


@contextmanager
def sqlite_transaction(conn: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    """Transaction explicite : commit si le bloc `with` se termine sans
    exception, rollback sinon. sqlite3 ouvre deja une transaction implicite
    des la premiere ecriture, mais un rollback explicite en cas d'erreur
    evite de laisser une transaction a moitie ecrite si l'appelant oublie de
    gerer l'exception lui-meme (voir tests/test_db.py, cas rollback)."""
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise


@contextmanager
def duckdb_transaction(conn: duckdb.DuckDBPyConnection) -> Iterator[duckdb.DuckDBPyConnection]:
    """Equivalent de `sqlite_transaction` pour DuckDB (BEGIN/COMMIT/ROLLBACK
    explicites -- DuckDB est autocommit par defaut hors bloc de transaction)."""
    conn.execute("BEGIN TRANSACTION;")
    try:
        yield conn
        conn.execute("COMMIT;")
    except Exception:
        conn.execute("ROLLBACK;")
        raise

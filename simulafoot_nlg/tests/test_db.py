"""Cas minimum du brief : WAL activé, FK activées, transaction rollback."""

from __future__ import annotations

import sqlite3

import pytest

from engine.db import duckdb_transaction, get_duckdb, get_sqlite, sqlite_transaction


def test_get_sqlite_enables_wal_and_foreign_keys(tmp_path):
    # WAL n'a d'effet observable que sur un vrai fichier (":memory:" l'ignore
    # silencieusement) -- fichier temporaire dédié pour ce test précis.
    db_path = tmp_path / "test.db"
    conn = get_sqlite(db_path)
    try:
        assert conn.execute("PRAGMA journal_mode;").fetchone()[0] == "wal"
        assert conn.execute("PRAGMA foreign_keys;").fetchone()[0] == 1
    finally:
        conn.close()


def test_get_sqlite_row_factory_allows_column_access_by_name():
    conn = get_sqlite(":memory:")
    try:
        conn.execute("CREATE TABLE t (id INTEGER, name TEXT)")
        conn.execute("INSERT INTO t VALUES (1, 'a')")
        row = conn.execute("SELECT * FROM t").fetchone()
        assert row["name"] == "a"
    finally:
        conn.close()


def test_foreign_keys_are_enforced():
    conn = get_sqlite(":memory:")
    try:
        conn.execute("CREATE TABLE parent (id INTEGER PRIMARY KEY)")
        conn.execute("CREATE TABLE child (id INTEGER PRIMARY KEY, parent_id INTEGER REFERENCES parent(id))")
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("INSERT INTO child (id, parent_id) VALUES (1, 999)")
    finally:
        conn.close()


def test_sqlite_transaction_commits_on_success():
    conn = get_sqlite(":memory:")
    try:
        conn.execute("CREATE TABLE t (id INTEGER)")
        conn.commit()
        with sqlite_transaction(conn):
            conn.execute("INSERT INTO t VALUES (1)")
        # Nouvelle connexion impossible sur :memory: -- on relit sur la même,
        # mais l'essentiel est que commit() ait bien été appelé sans lever.
        assert conn.execute("SELECT COUNT(*) FROM t").fetchone()[0] == 1
    finally:
        conn.close()


def test_sqlite_transaction_rolls_back_on_error():
    conn = get_sqlite(":memory:")
    try:
        conn.execute("CREATE TABLE t (id INTEGER)")
        conn.commit()
        with pytest.raises(ValueError), sqlite_transaction(conn):
            conn.execute("INSERT INTO t VALUES (1)")
            raise ValueError("boom")
        assert conn.execute("SELECT COUNT(*) FROM t").fetchone()[0] == 0
    finally:
        conn.close()


def test_get_duckdb_returns_working_connection():
    conn = get_duckdb(":memory:")
    try:
        assert conn.execute("SELECT 1").fetchone() == (1,)
    finally:
        conn.close()


def test_duckdb_transaction_rolls_back_on_error():
    conn = get_duckdb(":memory:")
    try:
        conn.execute("CREATE TABLE t (id INTEGER)")
        with pytest.raises(ValueError), duckdb_transaction(conn):
            conn.execute("INSERT INTO t VALUES (1)")
            raise ValueError("boom")
        assert conn.execute("SELECT COUNT(*) FROM t").fetchone() == (0,)
    finally:
        conn.close()

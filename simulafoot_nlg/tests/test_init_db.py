"""Colonne phrase_history.match_sequence (decision B du plan V2.1) : presente
quand la base est creee depuis schema.sql ET quand elle existait deja sans la
colonne (ALTER TABLE idempotent, voir scripts/init_db.py)."""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

import pytest

from scripts.init_db import DEFAULT_SCHEMA_PATH, init_db


def _colonnes(db_path: Path, table: str) -> dict[str, str]:
    conn = sqlite3.connect(db_path)
    try:
        return {row[1]: row[2] for row in conn.execute(f"PRAGMA table_info({table})")}
    finally:
        conn.close()


def _base_anterieure_a_la_colonne(db_path: Path) -> None:
    """Schema actuel prive de toute ligne mentionnant match_sequence (colonne +
    commentaire) : etat d'une base creee avant la decision B."""
    sql = Path(DEFAULT_SCHEMA_PATH).read_text(encoding="utf-8")
    ancien = re.sub(r"^.*match_sequence.*\n", "", sql, flags=re.MULTILINE)
    assert ancien != sql, "schema.sql ne mentionne plus match_sequence : le test ne prouve plus rien"
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(ancien)
        conn.execute("INSERT INTO scenarios (code, label) VALUES ('BUT', 'But')")
        conn.execute("INSERT INTO variants (scenario_id, code, label, is_default) VALUES (1, 'DEFAUT', 'd', 1)")
        conn.execute("INSERT INTO phrases (variant_id, text) VALUES (1, 'x')")
        conn.execute("INSERT INTO phrase_history (phrase_id, match_id, rendered_text) VALUES (1, 'm0', 'x')")
        conn.commit()
    finally:
        conn.close()
    assert "match_sequence" not in _colonnes(db_path, "phrase_history")


def test_match_sequence_existe_a_la_creation(tmp_path):
    db_path = tmp_path / "neuve.db"
    init_db(db_path=db_path)
    assert _colonnes(db_path, "phrase_history")["match_sequence"] == "INTEGER"


def test_match_sequence_ajoutee_a_une_base_existante_sans_perdre_les_lignes(tmp_path):
    db_path = tmp_path / "ancienne.db"
    _base_anterieure_a_la_colonne(db_path)

    init_db(db_path=db_path)

    assert _colonnes(db_path, "phrase_history")["match_sequence"] == "INTEGER"
    conn = sqlite3.connect(db_path)
    try:
        assert conn.execute("SELECT match_id, match_sequence FROM phrase_history").fetchall() == [("m0", None)]
    finally:
        conn.close()


def test_init_db_est_idempotent_avec_la_colonne(tmp_path):
    db_path = tmp_path / "deux_fois.db"
    init_db(db_path=db_path)
    init_db(db_path=db_path)
    assert list(_colonnes(db_path, "phrase_history")).count("match_sequence") == 1


@pytest.mark.parametrize("origine", ["creation", "alter"])
def test_la_contrainte_refuse_un_rang_negatif_dans_les_deux_chemins(tmp_path, origine):
    db_path = tmp_path / f"{origine}.db"
    if origine == "alter":
        _base_anterieure_a_la_colonne(db_path)
    init_db(db_path=db_path)

    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA foreign_keys = OFF")
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO phrase_history (phrase_id, match_id, match_sequence, rendered_text) "
                "VALUES (1, 'm1', -1, 'x')"
            )
    finally:
        conn.close()


def test_l_index_d_unicite_est_ajoute_a_une_base_existante_qui_ne_l_avait_pas(tmp_path):
    db_path = tmp_path / "sans_index.db"
    init_db(db_path=db_path)
    conn = sqlite3.connect(db_path)
    conn.execute("DROP INDEX idx_phrases_variant_text_unique")
    conn.commit()
    conn.close()

    init_db(db_path=db_path)
    init_db(db_path=db_path)  # idempotent

    conn = sqlite3.connect(db_path)
    try:
        noms = {row[1] for row in conn.execute("PRAGMA index_list(phrases)")}
    finally:
        conn.close()
    assert "idx_phrases_variant_text_unique" in noms

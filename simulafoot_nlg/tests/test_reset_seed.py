"""reset_seed (D7bis) : vide les 11 tables seed et leurs compteurs, preserve les joueurs."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from scripts.init_db import init_db
from scripts.reset_seed import SEED_TABLES_DELETION_ORDER, reset_seed

PRESERVED_TABLES = {"players", "player_attributes"}


def _remplir(db_path: Path) -> None:
    """Une ligne dans chacune des tables du schema (joueurs compris)."""
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("INSERT INTO players (id, first_name, last_name) VALUES (7, 'Ousmane', 'Dembélé')")
        conn.execute(
            "INSERT INTO player_attributes (player_id, attribute, category, value) "
            "VALUES (7, 'Pace', 'physique', 90)"
        )
        conn.execute("INSERT INTO scenarios (code, label) VALUES ('BUT', 'But')")
        conn.execute("INSERT INTO variants (scenario_id, code, label, is_default) VALUES (1, 'DEFAUT', 'd', 1)")
        conn.execute("INSERT INTO phrases (variant_id, text) VALUES (1, 'x')")
        conn.execute(
            "INSERT INTO phrase_conditions (phrase_id, attribute, operator, value) VALUES (1, 'minute', '>=', '5')"
        )
        conn.execute(
            "INSERT INTO phrase_slots (phrase_id, slot_name, expression) VALUES (1, 'joueur', 'player.full_name')"
        )
        conn.execute("INSERT INTO slot_dictionaries (dictionary_key, value) VALUES ('k', 'v')")
        conn.execute("INSERT INTO phrase_cooldowns (phrase_id, cooldown_matches) VALUES (1, 3)")
        conn.execute("INSERT INTO tags (name) VALUES ('humour')")
        conn.execute("INSERT INTO phrase_tags (phrase_id, tag_id) VALUES (1, 1)")
        conn.execute(
            "INSERT INTO phrase_history (phrase_id, player_id, match_id, rendered_text) VALUES (1, 7, 'm1', 'x')"
        )
        conn.execute("INSERT INTO similarity_signatures (history_id, signature) VALUES (1, '[]')")
        conn.commit()
    finally:
        conn.close()


def _compte(db_path: Path, table: str) -> int:
    conn = sqlite3.connect(db_path)
    try:
        return int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
    finally:
        conn.close()


def _sequences(db_path: Path) -> dict[str, int]:
    conn = sqlite3.connect(db_path)
    try:
        return dict(conn.execute("SELECT name, seq FROM sqlite_sequence").fetchall())
    finally:
        conn.close()


@pytest.fixture
def base_remplie(tmp_path: Path) -> Path:
    db_path = tmp_path / "reset.db"
    init_db(db_path=db_path)
    _remplir(db_path)
    return db_path


def test_la_liste_de_reset_couvre_exactement_les_tables_hors_joueurs(tmp_path):
    db_path = tmp_path / "schema.db"
    init_db(db_path=db_path)
    conn = sqlite3.connect(db_path)
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    conn.close()
    assert set(SEED_TABLES_DELETION_ORDER) == tables - PRESERVED_TABLES - {"sqlite_sequence"}
    assert len(SEED_TABLES_DELETION_ORDER) == 11


def test_reset_vide_les_11_tables_seed_et_garde_les_joueurs(base_remplie):
    deleted = reset_seed(base_remplie, yes=True)

    assert set(deleted) == set(SEED_TABLES_DELETION_ORDER)
    assert all(n >= 1 for n in deleted.values())
    for table in SEED_TABLES_DELETION_ORDER:
        assert _compte(base_remplie, table) == 0, table
    assert _compte(base_remplie, "players") == 1
    assert _compte(base_remplie, "player_attributes") == 1


def test_les_compteurs_seed_repartent_de_1_et_celui_des_joueurs_est_intact(base_remplie):
    sequences_avant = _sequences(base_remplie)
    assert "player_attributes" in sequences_avant and "scenarios" in sequences_avant

    reset_seed(base_remplie, yes=True)

    sequences = _sequences(base_remplie)
    assert sequences["player_attributes"] == sequences_avant["player_attributes"]
    assert not set(SEED_TABLES_DELETION_ORDER) & set(sequences)

    conn = sqlite3.connect(base_remplie)
    cur = conn.execute("INSERT INTO scenarios (code, label) VALUES ('BUT', 'But')")
    conn.close()
    assert cur.lastrowid == 1


def test_sans_confirmation_rien_n_est_supprime_et_le_message_recommande_l_export(base_remplie):
    with pytest.raises(ValueError, match="export-analytics"):
        reset_seed(base_remplie, yes=False)
    assert _compte(base_remplie, "phrases") == 1
    assert _compte(base_remplie, "phrase_history") == 1


def test_la_commande_cli_exige_yes(base_remplie):
    import cli

    with pytest.raises(SystemExit) as refus:
        cli.main(["--db", str(base_remplie), "reset-seed"])
    assert refus.value.code == 1
    assert _compte(base_remplie, "phrases") == 1

    cli.main(["--db", str(base_remplie), "reset-seed", "--yes"])
    assert _compte(base_remplie, "phrases") == 0

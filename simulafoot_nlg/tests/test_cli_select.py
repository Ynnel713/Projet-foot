"""cli.py select : commande de developpement branchee sur phrase_selector.select."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

import cli
from scripts.init_db import init_db


@pytest.fixture
def base(tmp_path: Path) -> Path:
    db_path = tmp_path / "cli.db"
    init_db(db_path=db_path)
    conn = sqlite3.connect(db_path)
    conn.execute("INSERT INTO players (id, first_name, last_name, position) VALUES (7, 'Kylian', 'Mbappé', 'BU')")
    conn.execute("INSERT INTO players (id, first_name, last_name, position) VALUES (8, 'Gardien', 'Test', 'GK')")
    conn.execute("INSERT INTO scenarios (code, label) VALUES ('BUT_TEST', 'But')")
    conn.execute("INSERT INTO variants (scenario_id, code, label, is_default) VALUES (1, 'DEFAUT', 'd', 1)")
    conn.execute("INSERT INTO phrases (variant_id, text) VALUES (1, 'Quel but !')")
    conn.execute("INSERT INTO phrase_cooldowns (phrase_id, cooldown_matches) VALUES (1, 3)")  # cooldown obligatoire
    conn.commit()
    conn.close()
    return db_path


def test_select_affiche_la_phrase_choisie(base, capsys):
    cli.main(["--db", str(base), "select", "--scenario", "BUT_TEST", "--player-id", "7", "--seed", "3", "--match-sequence", "5"])
    assert capsys.readouterr().out.strip() == "Quel but !"


def test_scenario_introuvable_sort_en_erreur(base, capsys):
    with pytest.raises(SystemExit) as sortie:
        cli.main(["--db", str(base), "select", "--scenario", "NOPE", "--player-id", "7", "--match-sequence", "5"])
    assert sortie.value.code == 1
    assert "introuvable" in capsys.readouterr().err


def test_scenario_a_sec_sort_avec_le_code_2(base, capsys):
    conn = sqlite3.connect(base)
    conn.execute("UPDATE phrases SET is_active = 0")
    conn.commit()
    conn.close()
    with pytest.raises(SystemExit) as sortie:
        cli.main(["--db", str(base), "select", "--scenario", "BUT_TEST", "--player-id", "7", "--match-sequence", "5"])
    assert sortie.value.code == 2
    assert "BUT_TEST" in capsys.readouterr().err

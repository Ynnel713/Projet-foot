"""engine/player_resolver.py : player_id -> Player par lookup (D14)."""

from __future__ import annotations

import sqlite3

import pytest

from engine.models import Player
from engine.player_resolver import resolve
from scripts.init_db import init_db


@pytest.fixture
def base_joueurs(sqlite_conn):
    sqlite_conn.execute(
        """INSERT INTO players (id, first_name, last_name, nationality, age, position, secondary_positions,
                                club, height_cm, foot, fm_rating, preferred_moves)
           VALUES (7, 'Kylian', 'Mbappé', 'France', 26, 'BU', 'AG / AD', 'Real Madrid', 178, 'Right', 91.0,
                   'Cuts Inside ; Runs With Ball Often')"""
    )
    sqlite_conn.execute("INSERT INTO players (id, first_name, last_name) VALUES (8, 'Sans', 'Attributs')")
    sqlite_conn.executemany(
        "INSERT INTO player_attributes (player_id, attribute, category, value) VALUES (?, ?, ?, ?)",
        [(7, "Pace", "physique", 95), (7, "Finishing", "technique", 90)],
    )
    sqlite_conn.commit()
    return sqlite_conn


def test_un_identifiant_connu_donne_le_joueur_complet(base_joueurs):
    joueur = resolve(7, base_joueurs)
    assert isinstance(joueur, Player)
    assert (joueur.id, joueur.full_name, joueur.position, joueur.age, joueur.club) == (7, "Kylian Mbappé", "BU", 26, "Real Madrid")
    assert joueur.secondary_positions == ("AG", "AD")
    assert joueur.preferred_moves == ("Cuts Inside", "Runs With Ball Often")
    assert joueur.fm_rating == 91.0


def test_les_attributs_fm26_sont_attaches(base_joueurs):
    assert resolve(7, base_joueurs).attributes == {"Pace": 95, "Finishing": 90}


def test_un_joueur_sans_attributs_importes_a_un_dict_vide_sans_erreur(base_joueurs):
    joueur = resolve(8, base_joueurs)
    assert joueur.attributes == {}
    assert joueur.full_name == "Sans Attributs"


def test_les_attributs_d_un_autre_joueur_ne_fuient_pas(base_joueurs):
    assert resolve(8, base_joueurs).attributes == {}


def test_un_identifiant_inconnu_leve_key_error(base_joueurs):
    with pytest.raises(KeyError, match="999"):
        resolve(999, base_joueurs)


@pytest.mark.parametrize("identifiant", [True, "7", 7.0, None])
def test_un_identifiant_non_entier_est_refuse(base_joueurs, identifiant):
    with pytest.raises(TypeError, match="player_id"):
        resolve(identifiant, base_joueurs)  # type: ignore[arg-type]


def test_fonctionne_avec_une_connexion_sans_row_factory(tmp_path):
    db_path = tmp_path / "plain.db"
    init_db(db_path=db_path)
    conn = sqlite3.connect(db_path)  # pas de row_factory : tuples
    conn.execute("INSERT INTO players (id, first_name, last_name) VALUES (1, 'A', 'B')")
    conn.execute("INSERT INTO player_attributes (player_id, attribute, category, value) VALUES (1, 'Pace', 'physique', 80)")
    conn.commit()
    try:
        assert resolve(1, conn).attributes == {"Pace": 80}
    finally:
        conn.close()

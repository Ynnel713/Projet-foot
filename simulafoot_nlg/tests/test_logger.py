"""logger.log_usage : ecrivain unique de phrase_history (D17), retourne l'id insere ;
refuse les phrases de secours (D10)."""

from __future__ import annotations

import pytest

from engine.logger import log_usage


@pytest.fixture
def joueur_id(sqlite_conn) -> int:
    sqlite_conn.execute("INSERT INTO players (id, first_name, last_name) VALUES (7, 'Kylian', 'Mbappé')")
    sqlite_conn.commit()
    return 7


def test_log_usage_retourne_l_id_insere_et_ecrit_la_ligne(sqlite_conn, seeded_scenario, joueur_id):
    history_id = log_usage(
        sqlite_conn, seeded_scenario["phrase_id"], joueur_id, "m1", "Quel but !", match_sequence=12
    )

    ligne = sqlite_conn.execute("SELECT * FROM phrase_history WHERE id = ?", (history_id,)).fetchone()
    assert isinstance(history_id, int)
    assert (ligne["phrase_id"], ligne["player_id"], ligne["match_id"]) == (seeded_scenario["phrase_id"], 7, "m1")
    assert (ligne["match_sequence"], ligne["rendered_text"]) == (12, "Quel but !")
    assert ligne["used_at"]  # pose par SQLite


def test_les_ids_retournes_se_suivent_et_designent_des_lignes_distinctes(sqlite_conn, seeded_scenario, joueur_id):
    premier = log_usage(sqlite_conn, seeded_scenario["phrase_id"], joueur_id, "m1", "a", match_sequence=1)
    second = log_usage(sqlite_conn, seeded_scenario["phrase_id"], joueur_id, "m2", "b", match_sequence=2)
    assert second == premier + 1
    textes = dict(sqlite_conn.execute("SELECT id, rendered_text FROM phrase_history").fetchall())
    assert textes == {premier: "a", second: "b"}


def test_un_joueur_inconnu_de_l_appelant_peut_etre_none(sqlite_conn, seeded_scenario):
    history_id = log_usage(sqlite_conn, seeded_scenario["phrase_id"], None, "m1", "x", match_sequence=0)
    assert sqlite_conn.execute("SELECT player_id FROM phrase_history WHERE id = ?", (history_id,)).fetchone()[0] is None


def test_log_usage_ne_commite_pas(sqlite_conn, seeded_scenario, joueur_id):
    log_usage(sqlite_conn, seeded_scenario["phrase_id"], joueur_id, "m1", "x", match_sequence=1)
    sqlite_conn.rollback()
    assert sqlite_conn.execute("SELECT COUNT(*) FROM phrase_history").fetchone()[0] == 0


def test_une_phrase_de_secours_est_refusee_et_rien_n_est_ecrit(sqlite_conn, seeded_scenario, joueur_id):
    fallback_id = sqlite_conn.execute(
        "INSERT INTO phrases (variant_id, text, is_fallback) VALUES (?, 'Le match suit son cours.', 1)",
        (seeded_scenario["variant_id"],),
    ).lastrowid
    with pytest.raises(ValueError, match="phrase de secours"):
        log_usage(sqlite_conn, fallback_id, joueur_id, "m1", "Le match suit son cours.", match_sequence=1)
    assert sqlite_conn.execute("SELECT COUNT(*) FROM phrase_history").fetchone()[0] == 0


def test_un_phrase_id_inconnu_est_refuse(sqlite_conn, joueur_id):
    with pytest.raises(ValueError, match="inconnu"):
        log_usage(sqlite_conn, 999, joueur_id, "m1", "x", match_sequence=1)


@pytest.mark.parametrize(("rang", "erreur"), [(None, ValueError), (-1, ValueError), (True, TypeError), ("3", TypeError)])
def test_match_sequence_invalide_est_refuse_sans_ecriture(sqlite_conn, seeded_scenario, joueur_id, rang, erreur):
    with pytest.raises(erreur, match="match_sequence"):
        log_usage(sqlite_conn, seeded_scenario["phrase_id"], joueur_id, "m1", "x", match_sequence=rang)
    assert sqlite_conn.execute("SELECT COUNT(*) FROM phrase_history").fetchone()[0] == 0


def test_match_sequence_est_obligatoire_et_par_mot_cle(sqlite_conn, seeded_scenario, joueur_id):
    with pytest.raises(TypeError):
        log_usage(sqlite_conn, seeded_scenario["phrase_id"], joueur_id, "m1", "x")  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        log_usage(sqlite_conn, seeded_scenario["phrase_id"], joueur_id, "m1", "x", 1)  # type: ignore[misc]

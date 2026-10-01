"""anti_repeat : recency_penalty est implemente (voir TestRecencyPenalty) ;
similarity_penalty et update_cooldown restent des SQUELETTES (contrat "echoue
explicitement" seulement) jusqu'a leurs commits."""

from __future__ import annotations

import pytest

from engine.anti_repeat import recency_penalty, similarity_penalty, update_cooldown
from engine.models import Phrase, Player
from engine.logger import log_usage


def _phrase() -> Phrase:
    return Phrase(id=1, variant_id=1, text="{player_name} marque !")


def _player() -> Player:
    return Player(id=1, first_name="A", last_name="B")


def test_similarity_penalty_raises_not_implemented_error(sqlite_conn):
    with pytest.raises(NotImplementedError):
        similarity_penalty(sqlite_conn, "Quel but !", _player())


def test_update_cooldown_raises_not_implemented_error(sqlite_conn):
    with pytest.raises(NotImplementedError):
        update_cooldown(sqlite_conn, _phrase(), _player(), "m1", "Quel but !")


# --- recency_penalty : en matchs, binaire, match_sequence obligatoire -----------


class TestRecencyPenalty:
    @pytest.fixture
    def phrase_en_base(self, sqlite_conn, seeded_scenario):
        sqlite_conn.execute("INSERT INTO players (id, first_name, last_name) VALUES (7, 'Kylian', 'Mbappé')")
        sqlite_conn.execute("INSERT INTO players (id, first_name, last_name) VALUES (8, 'Ousmane', 'Dembélé')")
        sqlite_conn.execute("INSERT INTO phrase_cooldowns (phrase_id, cooldown_matches) VALUES (?, 3)", (seeded_scenario["phrase_id"],))
        sqlite_conn.commit()
        return Phrase(id=seeded_scenario["phrase_id"], variant_id=seeded_scenario["variant_id"], text="x")

    @staticmethod
    def _joueur(identifiant: int = 7) -> Player:
        return Player(id=identifiant, first_name="A", last_name="B")

    @staticmethod
    def _usage(conn, phrase: Phrase, joueur: int, rang: int | None) -> None:
        if rang is None:
            conn.execute(
                "INSERT INTO phrase_history (phrase_id, player_id, match_id, rendered_text) VALUES (?, ?, 'm', 'x')",
                (phrase.id, joueur),
            )
        else:
            log_usage(conn, phrase.id, joueur, f"m{rang}", "x", match_sequence=rang)

    def test_jamais_utilisee_pas_de_penalite(self, sqlite_conn, phrase_en_base):
        assert recency_penalty(sqlite_conn, phrase_en_base, self._joueur(), match_sequence=10) == 0.0

    @pytest.mark.parametrize(
        ("rang", "attendu"),
        [(10, 1.0), (11, 1.0), (12, 1.0), (13, 0.0), (14, 0.0), (40, 0.0)],
    )
    def test_cooldown_de_3_matchs_bloque_trois_matchs_puis_libere(self, sqlite_conn, phrase_en_base, rang, attendu):
        self._usage(sqlite_conn, phrase_en_base, 7, 10)
        assert recency_penalty(sqlite_conn, phrase_en_base, self._joueur(), match_sequence=rang) == attendu

    def test_le_cooldown_est_par_joueur(self, sqlite_conn, phrase_en_base):
        self._usage(sqlite_conn, phrase_en_base, 8, 10)  # un AUTRE joueur
        assert recency_penalty(sqlite_conn, phrase_en_base, self._joueur(7), match_sequence=10) == 0.0
        assert recency_penalty(sqlite_conn, phrase_en_base, self._joueur(8), match_sequence=10) == 1.0

    def test_seul_le_dernier_usage_compte(self, sqlite_conn, phrase_en_base):
        self._usage(sqlite_conn, phrase_en_base, 7, 2)
        self._usage(sqlite_conn, phrase_en_base, 7, 10)
        assert recency_penalty(sqlite_conn, phrase_en_base, self._joueur(), match_sequence=12) == 1.0

    def test_un_usage_futur_compte_comme_non_ecoule(self, sqlite_conn, phrase_en_base):
        self._usage(sqlite_conn, phrase_en_base, 7, 20)
        assert recency_penalty(sqlite_conn, phrase_en_base, self._joueur(), match_sequence=5) == 1.0

    def test_les_lignes_sans_match_sequence_sont_ignorees(self, sqlite_conn, phrase_en_base):
        self._usage(sqlite_conn, phrase_en_base, 7, None)
        assert recency_penalty(sqlite_conn, phrase_en_base, self._joueur(), match_sequence=10) == 0.0

    def test_une_phrase_de_secours_n_a_jamais_de_penalite_meme_sans_cooldown(self, sqlite_conn, seeded_scenario):
        secours = Phrase(id=999, variant_id=seeded_scenario["variant_id"], text="x", is_fallback=True)
        assert recency_penalty(sqlite_conn, secours, self._joueur(), match_sequence=1) == 0.0

    def test_une_phrase_normale_sans_cooldown_est_refusee(self, sqlite_conn, seeded_scenario):
        sans_cooldown = Phrase(id=seeded_scenario["phrase_id"], variant_id=seeded_scenario["variant_id"], text="x")
        with pytest.raises(ValueError, match="sans cooldown"):
            recency_penalty(sqlite_conn, sans_cooldown, self._joueur(), match_sequence=1)

    @pytest.mark.parametrize(("rang", "erreur"), [(None, ValueError), (-1, ValueError), (True, TypeError), ("3", TypeError)])
    def test_match_sequence_invalide_est_refuse_sans_repli(self, sqlite_conn, phrase_en_base, rang, erreur):
        with pytest.raises(erreur, match="match_sequence"):
            recency_penalty(sqlite_conn, phrase_en_base, self._joueur(), match_sequence=rang)

    def test_match_sequence_est_obligatoire_et_par_mot_cle(self, sqlite_conn, phrase_en_base):
        with pytest.raises(TypeError):
            recency_penalty(sqlite_conn, phrase_en_base, self._joueur())  # type: ignore[call-arg]
        with pytest.raises(TypeError):
            recency_penalty(sqlite_conn, phrase_en_base, self._joueur(), 10)  # type: ignore[misc]

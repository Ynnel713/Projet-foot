"""anti_repeat : recency_penalty est implemente (voir TestRecencyPenalty) ;
similarity_penalty l'est aussi (TestSimilarityPenalty) ; update_cooldown reste un SQUELETTE
(contrat "echoue explicitement") jusqu'a son commit."""

from __future__ import annotations

import pytest

from engine.anti_repeat import recency_penalty, similarity_penalty, update_cooldown
from engine.models import Phrase, Player
from engine import minhash
from engine.logger import log_usage


def _phrase() -> Phrase:
    return Phrase(id=1, variant_id=1, text="{player_name} marque !")


def _player() -> Player:
    return Player(id=1, first_name="A", last_name="B")


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


# --- similarity_penalty : MinHash, fenetre en matchs ----------------------------

TEXTE = "Kylian Mbappé efface le gardien d'un crochet et pousse tranquillement le ballon au fond des filets !"


class TestSimilarityPenalty:
    @pytest.fixture
    def base(self, sqlite_conn, seeded_scenario):
        for identifiant in (7, 8):
            sqlite_conn.execute("INSERT INTO players (id, first_name, last_name) VALUES (?, 'A', 'B')", (identifiant,))
        sqlite_conn.commit()
        return sqlite_conn, seeded_scenario["phrase_id"]

    @staticmethod
    def _rendre(conn, phrase_id: int, joueur: int, rang: int | None, texte: str) -> None:
        """Une ligne d'historique + sa signature, ecrites a la main (update_cooldown arrive au commit 4)."""
        history_id = conn.execute(
            "INSERT INTO phrase_history (phrase_id, player_id, match_id, match_sequence, rendered_text) "
            "VALUES (?, ?, 'm', ?, ?)",
            (phrase_id, joueur, rang, texte),
        ).lastrowid
        conn.execute(
            "INSERT INTO similarity_signatures (history_id, signature) VALUES (?, ?)",
            (history_id, minhash.serialiser(minhash.signature(texte))),
        )

    @staticmethod
    def _joueur(identifiant: int = 7) -> Player:
        return Player(id=identifiant, first_name="A", last_name="B")

    def test_aucun_texte_recent_pas_de_penalite(self, base):
        conn, _ = base
        assert similarity_penalty(conn, TEXTE, self._joueur(), match_sequence=10) == 0.0

    def test_un_texte_identique_donne_1(self, base):
        conn, phrase_id = base
        self._rendre(conn, phrase_id, 7, 10, TEXTE)
        assert similarity_penalty(conn, TEXTE, self._joueur(), match_sequence=10) == 1.0

    def test_casse_et_ponctuation_ne_changent_pas_la_penalite(self, base):
        conn, phrase_id = base
        self._rendre(conn, phrase_id, 7, 10, TEXTE)
        autre = "kylian mbappé EFFACE le gardien d'un crochet, et pousse tranquillement le ballon au fond des filets."
        assert similarity_penalty(conn, autre, self._joueur(), match_sequence=10) == 1.0

    def test_un_texte_voisin_est_penalise_moins_qu_un_identique_et_plus_qu_un_texte_distinct(self, base):
        conn, phrase_id = base
        self._rendre(conn, phrase_id, 7, 10, TEXTE)
        voisin = TEXTE.replace("tranquillement", "calmement")
        distinct = "Le gardien repousse du bout des doigts une frappe lointaine puis capte le rebond sans trembler."
        penalite_voisin = similarity_penalty(conn, voisin, self._joueur(), match_sequence=10)
        penalite_distinct = similarity_penalty(conn, distinct, self._joueur(), match_sequence=10)
        assert 0.3 < penalite_voisin < 1.0
        assert penalite_distinct < 0.1

    def test_c_est_le_texte_le_plus_proche_qui_compte(self, base):
        conn, phrase_id = base
        self._rendre(conn, phrase_id, 7, 9, "Une tout autre phrase sans aucun rapport avec celle-ci.")
        self._rendre(conn, phrase_id, 7, 10, TEXTE)
        assert similarity_penalty(conn, TEXTE, self._joueur(), match_sequence=10) == 1.0

    @pytest.mark.parametrize(("rang_usage", "attendu"), [(10, 1.0), (7, 1.0), (6, 0.0), (11, 0.0)])
    def test_fenetre_en_matchs_match_courant_et_trois_precedents(self, base, rang_usage, attendu):
        conn, phrase_id = base
        self._rendre(conn, phrase_id, 7, rang_usage, TEXTE)
        # courant = 10, fenetre 3 -> [7, 10] ; 6 est trop ancien, 11 est dans le futur.
        assert similarity_penalty(conn, TEXTE, self._joueur(), match_sequence=10) == attendu

    def test_la_fenetre_est_configurable_en_matchs(self, base):
        conn, phrase_id = base
        self._rendre(conn, phrase_id, 7, 5, TEXTE)
        assert similarity_penalty(conn, TEXTE, self._joueur(), match_sequence=10) == 0.0
        assert similarity_penalty(conn, TEXTE, self._joueur(), match_sequence=10, fenetre_matchs=5) == 1.0
        assert similarity_penalty(conn, TEXTE, self._joueur(), match_sequence=10, fenetre_matchs=0) == 0.0

    def test_les_textes_d_un_autre_joueur_et_les_lignes_sans_rang_sont_ignores(self, base):
        conn, phrase_id = base
        self._rendre(conn, phrase_id, 8, 10, TEXTE)
        self._rendre(conn, phrase_id, 7, None, TEXTE)
        assert similarity_penalty(conn, TEXTE, self._joueur(7), match_sequence=10) == 0.0
        assert similarity_penalty(conn, TEXTE, self._joueur(8), match_sequence=10) == 1.0

    @pytest.mark.parametrize(("rang", "erreur"), [(None, ValueError), (-1, ValueError), (True, TypeError)])
    def test_match_sequence_invalide_est_refuse_sans_repli(self, base, rang, erreur):
        conn, _ = base
        with pytest.raises(erreur, match="match_sequence"):
            similarity_penalty(conn, TEXTE, self._joueur(), match_sequence=rang)

    @pytest.mark.parametrize("fenetre", [-1, True, 2.5, "3"])
    def test_fenetre_invalide_est_refusee(self, base, fenetre):
        conn, _ = base
        with pytest.raises(ValueError, match="fenetre_matchs"):
            similarity_penalty(conn, TEXTE, self._joueur(), match_sequence=10, fenetre_matchs=fenetre)

    def test_match_sequence_est_obligatoire_et_par_mot_cle(self, base):
        conn, _ = base
        with pytest.raises(TypeError):
            similarity_penalty(conn, TEXTE, self._joueur())  # type: ignore[call-arg]
        with pytest.raises(TypeError):
            similarity_penalty(conn, TEXTE, self._joueur(), 10)  # type: ignore[misc]

    def test_une_signature_de_longueur_differente_n_est_jamais_comparee_en_silence(self, base):
        conn, phrase_id = base
        history_id = conn.execute(
            "INSERT INTO phrase_history (phrase_id, player_id, match_id, match_sequence, rendered_text) "
            "VALUES (?, 7, 'm', 10, 'x')",
            (phrase_id,),
        ).lastrowid
        conn.execute(
            "INSERT INTO similarity_signatures (history_id, signature) VALUES (?, ?)",
            (history_id, minhash.serialiser(minhash.signature(TEXTE, permutations=16))),
        )
        with pytest.raises(ValueError, match="incomparables"):
            similarity_penalty(conn, TEXTE, self._joueur(), match_sequence=10)

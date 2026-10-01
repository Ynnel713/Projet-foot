"""phrase_selector : filtre mandatory, variantes de contexte prioritaires, tirage pondere DEFAUT/SURNOM, cooldown
joueur et global, similarite, rendu, phrase de secours, WARNING unique (decisions D1, D9, D10, D10-warn, revisees 02/10/2026)."""

from __future__ import annotations

import logging

import pytest

import engine.phrase_selector as module
from engine import minhash
from engine.anti_repeat import update_cooldown
from engine.logger import log_usage
from engine.models import MatchContext, Phrase, PhraseCondition, Player, SelectionResult, Variant
from engine.phrase_selector import (
    AucunCandidatError,
    candidats,
    select,
    variantes_de_contexte,
)
from engine.selectivity import Selectivite

RAPIDE = [("Pace", ">=", "8")]  # 30 % de la population : specifique


def _context() -> MatchContext:
    return MatchContext(match_id="m1")


def _joueur_rapide() -> Player:
    return Player(id=1, first_name="A", last_name="B", attributes={"Pace": 90, "Finishing": 40})


def _joueur_lent() -> Player:
    return Player(id=3, first_name="L", last_name="ent", attributes={"Pace": 2})


def _population_pace() -> Selectivite:
    """10 joueurs de champ, Pace 1..10."""
    return Selectivite([Player(id=i, first_name="J", last_name=str(i), attributes={"Pace": i}) for i in range(1, 11)])


def _cond(attribute: str, operator: str, value: str, mandatory: bool = True) -> PhraseCondition:
    return PhraseCondition(id=1, phrase_id=1, attribute=attribute, operator=operator, value=value, mandatory=mandatory)


def _p(identifiant: int, *conditions: PhraseCondition, **champs) -> Phrase:
    return Phrase(id=identifiant, variant_id=1, text=f"p{identifiant}", conditions=conditions, **champs)


def _v(identifiant: int, code: str, *, defaut: bool = False, poids: float = 1.0, active: bool = True) -> Variant:
    return Variant(id=identifiant, scenario_id=1, code=code, label=code, is_default=defaut, weight=poids, is_active=active)


# --- Filtre mandatory -----------------------------------------------------------


class TestFiltreMandatory:
    def test_une_phrase_sans_condition_passe(self):
        assert candidats([_p(1)], _joueur_rapide(), _context()) == [_p(1)]

    def test_une_condition_mandatory_qui_echoue_ecarte_la_phrase(self):
        pool = [_p(1, _cond("Pace", ">=", "80")), _p(2, _cond("Finishing", ">=", "80"))]
        assert [p.id for p in candidats(pool, _joueur_rapide(), _context())] == [1]

    def test_toutes_les_conditions_mandatory_doivent_etre_satisfaites(self):
        pool = [_p(1, _cond("Pace", ">=", "80"), _cond("Finishing", ">=", "80"))]
        assert candidats(pool, _joueur_rapide(), _context()) == []

    def test_une_condition_non_mandatory_ne_filtre_pas(self):
        pool = [_p(1, _cond("Finishing", ">=", "80", mandatory=False))]
        assert len(candidats(pool, _joueur_rapide(), _context())) == 1

    def test_les_conditions_de_contexte_filtrent_aussi(self):
        pool = [_p(1, _cond("minute", ">=", "85"))]
        assert candidats(pool, _joueur_rapide(), MatchContext(match_id="m", minute=90)) == pool
        assert candidats(pool, _joueur_rapide(), MatchContext(match_id="m", minute=10)) == []
        assert candidats(pool, _joueur_rapide(), MatchContext(match_id="m")) == []  # minute inconnue : ne matche jamais

    def test_attribut_fm_connu_mais_absent_ecarte_la_phrase_sans_lever(self):
        # D16 : un joueur sans attributs ecarte les phrases a condition FM, il ne fait pas planter select.
        sans_attributs = Player(id=2, first_name="C", last_name="D")
        assert candidats([_p(1, _cond("Pace", ">=", "10"))], sans_attributs, _context()) == []

    def test_une_faute_de_frappe_en_base_leve_toujours_value_error(self):
        with pytest.raises(ValueError, match="Aggresion"):
            candidats([_p(1, _cond("Aggresion", ">=", "10"))], _joueur_rapide(), _context())

    def test_fallback_et_phrases_inactives_ne_sont_jamais_dans_le_pool_normal(self):
        pool = [_p(1), _p(2, is_fallback=True), _p(3, is_active=False)]
        assert [p.id for p in candidats(pool, _joueur_rapide(), _context())] == [1]

    def test_l_ordre_du_pool_est_conserve(self):
        pool = [_p(3), _p(1), _p(2)]
        assert [p.id for p in candidats(pool, _joueur_rapide(), _context())] == [3, 1, 2]


# --- Variantes de contexte ------------------------------------------------------


class TestVariantesDeContexte:
    def test_ni_defaut_ni_surnom_par_poids_decroissant_puis_id_croissant(self):
        variantes = [
            _v(1, "DEFAUT", defaut=True),
            _v(2, "SURNOM", poids=1.0),
            _v(3, "PENALTY", poids=2.0),
            _v(4, "AUTRE", poids=1.0),
            _v(5, "ENCORE", poids=1.0),
        ]
        assert [v.code for v in variantes_de_contexte(variantes)] == ["PENALTY", "AUTRE", "ENCORE"]

    def test_les_variantes_inactives_sont_ignorees(self):
        variantes = [_v(1, "DEFAUT", defaut=True), _v(2, "PENALTY", active=False)]
        assert variantes_de_contexte(variantes) == []

    def test_l_ordre_ne_depend_pas_de_l_ordre_d_entree(self):
        variantes = [_v(1, "DEFAUT", defaut=True), _v(2, "PENALTY"), _v(3, "AUTRE")]
        assert variantes_de_contexte(variantes) == variantes_de_contexte(list(reversed(variantes)))


# --- Banque en base pour select -------------------------------------------------


def _banque(conn, variantes: dict[str, dict], *, cooldown: int | None = 2) -> None:
    """Scenario BUT_TEST ; `variantes` : code -> {defaut, poids, active, phrases: [(texte, [(attr, op, val)], poids?)]}.
    Les joueurs 1 et 3 existent (historique) ; chaque phrase recoit un cooldown (sauf cooldown=None)."""
    for identifiant in (1, 3):
        conn.execute("INSERT INTO players (id, first_name, last_name) VALUES (?, 'J', 'x')", (identifiant,))
    conn.execute("INSERT INTO scenarios (code, label) VALUES ('BUT_TEST', 'But')")
    for code, definition in variantes.items():
        variante_id = conn.execute(
            "INSERT INTO variants (scenario_id, code, label, is_default, weight, is_active) VALUES (1, ?, ?, ?, ?, ?)",
            (code, code, int(definition.get("defaut", False)), definition.get("poids", 1.0), int(definition.get("active", True))),
        ).lastrowid
        for texte, conditions, *poids in definition["phrases"]:
            phrase_id = conn.execute(
                "INSERT INTO phrases (variant_id, text, weight) VALUES (?, ?, ?)", (variante_id, texte, poids[0] if poids else 1.0)
            ).lastrowid
            if cooldown is not None:
                conn.execute("INSERT INTO phrase_cooldowns (phrase_id, cooldown_matches) VALUES (?, ?)", (phrase_id, cooldown))
            for attribut, operateur, valeur in conditions:
                conn.execute(
                    "INSERT INTO phrase_conditions (phrase_id, attribute, operator, value) VALUES (?, ?, ?, ?)",
                    (phrase_id, attribut, operateur, valeur),
                )
    conn.commit()


def _ajouter_slot(conn, texte: str, slot_name: str, expression: str) -> None:
    phrase_id = conn.execute("SELECT id FROM phrases WHERE text = ?", (texte,)).fetchone()[0]
    conn.execute(
        "INSERT INTO phrase_slots (phrase_id, slot_name, expression) VALUES (?, ?, ?)", (phrase_id, slot_name, expression)
    )
    conn.commit()


def _ajouter_secours(conn, texte: str = "Le match suit son cours.") -> int:
    variante_id = conn.execute("SELECT id FROM variants WHERE is_default = 1").fetchone()[0]
    phrase_id = conn.execute(
        "INSERT INTO phrases (variant_id, text, is_fallback) VALUES (?, ?, 1)", (variante_id, texte)
    ).lastrowid
    conn.commit()
    return phrase_id


def _usage(conn, texte: str, joueur: int, rang: int, texte_rendu: str | None = None) -> None:
    """Un usage enregistre comme update_cooldown le fait : ligne d'historique + signature MinHash."""
    phrase_id = conn.execute("SELECT id FROM phrases WHERE text = ?", (texte,)).fetchone()[0]
    # Par defaut le texte HISTORISE differe de la phrase (aucun lien de similarite avec elle) ; les
    # tests de similarite passent explicitement le texte identique.
    rendu = texte_rendu or f"historique du match {rang} sans rapport"
    history_id = log_usage(conn, phrase_id, joueur, f"m{rang}", rendu, match_sequence=rang)
    conn.execute(
        "INSERT INTO similarity_signatures (history_id, signature) VALUES (?, ?)",
        (history_id, minhash.serialiser(minhash.signature(rendu))),
    )
    conn.commit()


def _resultat(conn, joueur: Player | None = None, *, seed=1, match_sequence=10, **kwargs) -> SelectionResult:
    return select(
        conn,
        "BUT_TEST",
        joueur or _joueur_rapide(),
        kwargs.pop("contexte", _context()),
        seed=seed,
        match_sequence=match_sequence,
        selectivite=kwargs.pop("selectivite", _population_pace()),
        **kwargs,
    )


def _select(conn, joueur: Player | None = None, **kwargs) -> Phrase:
    """La phrase choisie (la plupart des tests ne regardent que elle)."""
    return _resultat(conn, joueur, **kwargs).phrase


# --- Cascade de variantes ----------------------------------------------------------


class TestSelectVariantes:
    def test_une_variante_de_contexte_garde_sa_priorite_sur_defaut(self, sqlite_conn):
        _banque(sqlite_conn, {
            "DEFAUT": {"defaut": True, "phrases": [("generique A", []), ("generique B", [])]},
            "PENALTY": {"phrases": [("sur penalty", [])]},
        })
        for graine in range(20):
            assert _select(sqlite_conn, seed=graine).text == "sur penalty"

    def test_surnom_et_defaut_partagent_un_tirage_pondere_defaut_en_tete(self, sqlite_conn):
        _banque(sqlite_conn, {
            "DEFAUT": {"defaut": True, "phrases": [("generique A", []), ("generique B", [])]},
            "SURNOM": {"phrases": [("Le sprinter file", RAPIDE)]},
        })
        tires = [_select(sqlite_conn, seed=graine).text for graine in range(300)]
        assert 0 < tires.count("Le sprinter file") < 300 / 6  # SURNOM (0.35) x ciblage large (0.4) face a deux generiques (1.0)

    def test_surnom_vide_defaut_sert(self, sqlite_conn):
        _banque(sqlite_conn, {
            "DEFAUT": {"defaut": True, "phrases": [("generique", [])]},
            "SURNOM": {"phrases": [("Le sprinter file", RAPIDE)]},
        })
        assert _select(sqlite_conn, _joueur_lent()).text == "generique"

    def test_une_variante_a_zero_candidat_laisse_la_place_a_la_suivante_une_seule_fois(self, sqlite_conn, monkeypatch):
        _banque(sqlite_conn, {
            "DEFAUT": {"defaut": True, "phrases": [("generique", [])]},
            "SURNOM": {"phrases": [("A", RAPIDE)]},
            "PENALTY": {"poids": 2.0, "phrases": [("B", RAPIDE)]},
        })
        charges: list[int] = []
        original = module.load_phrases
        monkeypatch.setattr(module, "load_phrases", lambda conn, variante_id: charges.append(variante_id) or original(conn, variante_id))

        assert _select(sqlite_conn, _joueur_lent()).text == "generique"
        assert len(charges) == 3 and len(set(charges)) == 3  # PENALTY, puis SURNOM et DEFAUT : une fois chacune

    def test_on_s_arrete_a_la_premiere_variante_de_contexte_qui_produit_un_candidat(self, sqlite_conn, monkeypatch):
        _banque(sqlite_conn, {
            "DEFAUT": {"defaut": True, "phrases": [("generique", [])]},
            "PENALTY": {"phrases": [("sur penalty", RAPIDE)]},
        })
        charges: list[int] = []
        original = module.load_phrases
        monkeypatch.setattr(module, "load_phrases", lambda conn, variante_id: charges.append(variante_id) or original(conn, variante_id))
        _select(sqlite_conn)
        assert len(charges) == 1  # DEFAUT n'a meme pas ete charge

    def test_la_variante_de_contexte_au_plus_grand_poids_passe_la_premiere(self, sqlite_conn):
        _banque(sqlite_conn, {
            "DEFAUT": {"defaut": True, "phrases": [("generique", [])]},
            "AUTRE": {"poids": 1.0, "phrases": [("autre", RAPIDE)]},
            "PENALTY": {"poids": 3.0, "phrases": [("penalty", RAPIDE)]},
        })
        assert _select(sqlite_conn).text == "penalty"

    def test_une_variante_inactive_n_est_jamais_essayee(self, sqlite_conn):
        _banque(sqlite_conn, {
            "DEFAUT": {"defaut": True, "phrases": [("generique", [])]},
            "SURNOM": {"active": False, "phrases": [("surnom", RAPIDE)]},
        })
        assert {_select(sqlite_conn, seed=g).text for g in range(30)} == {"generique"}

    def test_scenario_inconnu_leve_key_error(self, sqlite_conn):
        with pytest.raises(KeyError, match="INCONNU"):
            select(sqlite_conn, "INCONNU", _joueur_rapide(), _context(), seed=1, match_sequence=1, selectivite=_population_pace())


class TestPonderationDesCandidats:
    def test_une_phrase_a_condition_large_ne_ecrase_plus_les_generiques(self, sqlite_conn):
        large = [("Pace", ">=", "1")]  # 100 % de la population : ciblage 0.4
        _banque(sqlite_conn, {"DEFAUT": {"defaut": True, "phrases": [("large", large), ("sans condition", [])]}})
        tires = [_select(sqlite_conn, seed=g).text for g in range(400)]
        assert set(tires) == {"large", "sans condition"}
        assert tires.count("large") < tires.count("sans condition")  # 0.4 contre 1.0

    def test_une_condition_discriminante_ne_desavantage_pas_la_phrase(self, sqlite_conn):
        rare = [("Pace", ">=", "10")]  # 10 % de la population : ciblage 1.0
        _banque(sqlite_conn, {"DEFAUT": {"defaut": True, "phrases": [("rare", rare), ("sans condition", [])]}})
        tires = [_select(sqlite_conn, seed=g).text for g in range(400)]
        assert abs(tires.count("rare") - tires.count("sans condition")) < 80  # ~ moitie-moitie

    def test_zero_specifique_eligible_repli_sur_les_generiques(self, sqlite_conn):
        _banque(sqlite_conn, {"DEFAUT": {"defaut": True, "phrases": [("spec", RAPIDE), ("gen", [])]}})
        assert _select(sqlite_conn, _joueur_lent()).text == "gen"

    def test_un_fallback_n_est_jamais_tire_dans_le_pool_normal(self, sqlite_conn):
        _banque(sqlite_conn, {"DEFAUT": {"defaut": True, "phrases": [("normale", [])]}})
        _ajouter_secours(sqlite_conn)
        assert {_select(sqlite_conn, seed=g).text for g in range(30)} == {"normale"}


class TestTirage:
    def test_meme_graine_meme_phrase_et_la_graine_fait_varier_le_tirage(self, sqlite_conn):
        _banque(sqlite_conn, {"DEFAUT": {"defaut": True, "phrases": [(f"g{i}", []) for i in range(10)]}})
        assert _select(sqlite_conn, seed=7).text == _select(sqlite_conn, seed=7).text
        assert len({_select(sqlite_conn, seed=g).text for g in range(40)}) > 4

    def test_une_phrase_de_poids_nul_n_est_jamais_tiree(self, sqlite_conn):
        _banque(sqlite_conn, {"DEFAUT": {"defaut": True, "phrases": [("poids nul", [], 0.0), ("poids un", [], 1.0)]}})
        assert {_select(sqlite_conn, seed=g).text for g in range(40)} == {"poids un"}


# --- Cooldown (en matchs) ---------------------------------------------------------


class TestCooldown:
    def test_une_phrase_en_cooldown_est_ecartee_puis_redevient_disponible(self, sqlite_conn):
        _banque(sqlite_conn, {"DEFAUT": {"defaut": True, "phrases": [("A", []), ("B", [])]}})  # cooldown 2
        _usage(sqlite_conn, "A", 1, 10)
        assert {_select(sqlite_conn, seed=g, match_sequence=11).text for g in range(30)} == {"B"}
        assert {_select(sqlite_conn, seed=g, match_sequence=12).text for g in range(40)} == {"A", "B"}

    def test_une_phrase_en_cooldown_laisse_les_autres_servir_puis_revient(self, sqlite_conn):
        _banque(sqlite_conn, {"DEFAUT": {"defaut": True, "phrases": [("spec", RAPIDE), ("gen", [])]}})
        _usage(sqlite_conn, "spec", 1, 10)
        assert {_select(sqlite_conn, match_sequence=11, seed=g).text for g in range(30)} == {"gen"}  # au lieu de bloquer
        assert "spec" in {_select(sqlite_conn, match_sequence=12, seed=g).text for g in range(60)}  # cooldown ecoule

    def test_le_tirage_ne_contourne_jamais_le_cooldown(self, sqlite_conn):
        _banque(sqlite_conn, {
            "DEFAUT": {"defaut": True, "phrases": [("generique", [])]},
            "SURNOM": {"phrases": [("surnom", RAPIDE)]},
        })
        _usage(sqlite_conn, "surnom", 1, 10)
        assert {_select(sqlite_conn, match_sequence=11, seed=g).text for g in range(60)} == {"generique"}  # SURNOM en cooldown
        assert "surnom" in {_select(sqlite_conn, match_sequence=13, seed=g).text for g in range(200)}  # cooldown (2) et memoire globale ecoules

    def test_le_cooldown_joueur_ne_bloque_que_ce_joueur(self, sqlite_conn):
        _banque(sqlite_conn, {"DEFAUT": {"defaut": True, "phrases": [("A", []), ("B", [])]}})
        _usage(sqlite_conn, "A", 3, 10)  # un AUTRE joueur l'a eue : pas de blocage joueur, mais la memoire globale la bloque
        assert {_select(sqlite_conn, _joueur_rapide(), match_sequence=10, seed=g).text for g in range(40)} == {"B"}
        assert {_select(sqlite_conn, _joueur_rapide(), match_sequence=10, seed=g).text for g in range(40)} == {"B"}

    def test_une_phrase_sans_cooldown_est_refusee_avec_un_warning(self, sqlite_conn, caplog):
        _banque(sqlite_conn, {"DEFAUT": {"defaut": True, "phrases": [("avec", [])]}})
        sqlite_conn.execute("INSERT INTO phrases (variant_id, text) VALUES (1, 'sans cooldown')")
        sqlite_conn.commit()
        with caplog.at_level(logging.WARNING, logger="engine.phrase_selector"):
            assert {_select(sqlite_conn, seed=g).text for g in range(30)} == {"avec"}
        assert any("cooldown" in r.getMessage() for r in caplog.records)


# --- Similarite et rendu ------------------------------------------------------------


class TestSimilariteEtRendu:
    def test_un_texte_identique_a_un_usage_recent_est_ecarte_quand_une_alternative_existe(self, sqlite_conn):
        _banque(sqlite_conn, {"DEFAUT": {"defaut": True, "phrases": [("Il marque un but superbe ce soir", []), ("Une toute autre phrase sans rapport", [])]}}, cooldown=0)
        _usage(sqlite_conn, "Il marque un but superbe ce soir", 1, 10, "Il marque un but superbe ce soir")
        assert {_select(sqlite_conn, seed=g, match_sequence=10).text for g in range(40)} == {"Une toute autre phrase sans rapport"}

    def test_si_tous_les_candidats_sont_identiques_a_l_historique_le_pool_n_est_pas_vide(self, sqlite_conn):
        _banque(sqlite_conn, {"DEFAUT": {"defaut": True, "phrases": [("Il marque un but superbe ce soir", [])]}}, cooldown=0)
        _usage(sqlite_conn, "Il marque un but superbe ce soir", 1, 10, "Il marque un but superbe ce soir")
        assert _select(sqlite_conn, match_sequence=10).text == "Il marque un but superbe ce soir"

    def test_un_slot_irresolvable_ecarte_la_phrase_et_une_autre_sert(self, sqlite_conn):
        _banque(sqlite_conn, {"DEFAUT": {"defaut": True, "phrases": [("{passeur} centre", []), ("Il frappe", [])]}})
        _ajouter_slot(sqlite_conn, "{passeur} centre", "passeur", "context.passeur.full_name")
        # le contexte n'a pas de passeur : la premiere phrase ne se rend pas (SlotResolutionError)
        assert {_select(sqlite_conn, seed=g).text for g in range(30)} == {"Il frappe"}

    def test_si_la_phrase_a_condition_ne_se_rend_pas_les_generiques_servent(self, sqlite_conn):
        _banque(sqlite_conn, {"DEFAUT": {"defaut": True, "phrases": [("{passeur} lance", RAPIDE), ("gen", [])]}})
        _ajouter_slot(sqlite_conn, "{passeur} lance", "passeur", "context.passeur.full_name")
        assert _select(sqlite_conn).text == "gen"

    def test_render_recoit_la_graine_et_les_codes_de_scenario_et_de_variante(self, sqlite_conn, monkeypatch):
        _banque(sqlite_conn, {
            "DEFAUT": {"defaut": True, "phrases": [("generique", [])]},
            "SURNOM": {"phrases": [("surnom", RAPIDE)]},
        })
        appels = []
        original = module.render
        monkeypatch.setattr(module, "render", lambda *a, **kw: appels.append(kw) or original(*a, **kw))
        _select(sqlite_conn, seed=42)
        assert sorted((a["seed"], a["scenario_code"], a["variant_code"]) for a in appels) == [
            (42, "BUT_TEST", "DEFAUT"),
            (42, "BUT_TEST", "SURNOM"),
        ]


# --- Phrase de secours et WARNING unique ----------------------------------------------


class TestFallbackEtWarning:
    def test_cascade_epuisee_la_phrase_de_secours_sert(self, sqlite_conn):
        _banque(sqlite_conn, {
            "DEFAUT": {"defaut": True, "phrases": [("spec", RAPIDE)]},
            "SURNOM": {"phrases": [("surnom", RAPIDE)]},
        })
        secours_id = _ajouter_secours(sqlite_conn)
        phrase = _select(sqlite_conn, _joueur_lent())
        assert (phrase.id, phrase.text, phrase.is_fallback) == (secours_id, "Le match suit son cours.", True)

    def test_le_fallback_n_est_pas_soumis_au_cooldown(self, sqlite_conn):
        _banque(sqlite_conn, {"DEFAUT": {"defaut": True, "phrases": [("spec", RAPIDE)]}})
        secours_id = _ajouter_secours(sqlite_conn)
        for rang in (10, 11, 12):  # il peut se repeter : aucune ligne d'historique n'est jamais ecrite pour lui
            assert _select(sqlite_conn, _joueur_lent(), match_sequence=rang).id == secours_id

    def test_cascade_warning_only_when_default_empty(self, sqlite_conn, caplog):
        """D5/D10-warn : AUCUN log pour le passage normal SURNOM -> DEFAUT ; UN seul WARNING enrichi
        quand la variante par defaut est elle aussi a sec."""
        _banque(sqlite_conn, {
            "DEFAUT": {"defaut": True, "phrases": [("spec", RAPIDE), ("gen", [])]},
            "SURNOM": {"phrases": [("surnom", RAPIDE)]},
        })
        with caplog.at_level(logging.DEBUG, logger="engine.phrase_selector"):
            assert _select(sqlite_conn, _joueur_lent()).text == "gen"  # SURNOM vide, DEFAUT sert
        assert [r for r in caplog.records if r.levelno >= logging.WARNING] == []

        _usage(sqlite_conn, "gen", 3, 10)  # le seul candidat de DEFAUT passe en cooldown
        secours_id = _ajouter_secours(sqlite_conn)
        caplog.clear()
        with caplog.at_level(logging.DEBUG, logger="engine.phrase_selector"):
            assert _select(sqlite_conn, _joueur_lent(), match_sequence=11).id == secours_id
        avertissements = [r for r in caplog.records if r.levelno >= logging.WARNING]
        assert len(avertissements) == 1
        message = avertissements[0].getMessage()
        assert "BUT_TEST" in message and "SURNOM#2" in message and "DEFAUT#1" in message
        assert f"phrase de secours #{secours_id}" in message

    def test_sans_phrase_de_secours_un_seul_warning_puis_erreur(self, sqlite_conn, caplog):
        _banque(sqlite_conn, {
            "DEFAUT": {"defaut": True, "phrases": [("spec", RAPIDE)]},
            "SURNOM": {"phrases": [("surnom", RAPIDE)]},
        })
        with caplog.at_level(logging.WARNING, logger="engine.phrase_selector"):
            with pytest.raises(AucunCandidatError, match="BUT_TEST"):
                _select(sqlite_conn, _joueur_lent())
        avertissements = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert len(avertissements) == 1 and "repli = aucun" in avertissements[0].getMessage()


# --- match_sequence obligatoire --------------------------------------------------------


class TestMatchSequence:
    @pytest.mark.parametrize(("rang", "erreur"), [(None, ValueError), (-1, ValueError), (True, TypeError), ("3", TypeError)])
    def test_invalide_est_refuse_sans_repli_meme_si_le_scenario_est_inconnu(self, sqlite_conn, rang, erreur):
        with pytest.raises(erreur, match="match_sequence"):
            select(sqlite_conn, "INCONNU", _joueur_rapide(), _context(), seed=1, match_sequence=rang, selectivite=_population_pace())

    def test_obligatoire_et_par_mot_cle(self, sqlite_conn):
        with pytest.raises(TypeError):
            select(sqlite_conn, "X", _joueur_rapide(), _context(), seed=1, selectivite=_population_pace())  # type: ignore[call-arg]
        with pytest.raises(TypeError):
            select(sqlite_conn, "X", _joueur_rapide(), _context(), 1, 10, _population_pace())  # type: ignore[misc]


# --- SelectionResult (D11) : la phrase ET son texte rendu --------------------------------


class TestSelectionResult:
    def test_le_resultat_porte_la_phrase_et_le_texte_rendu_post_traite(self, sqlite_conn):
        _banque(sqlite_conn, {"DEFAUT": {"defaut": True, "phrases": [("{joueur} frappe  fort face à {adversaire}", [])]}})
        _ajouter_slot(sqlite_conn, "{joueur} frappe  fort face à {adversaire}", "joueur", "player.full_name")
        _ajouter_slot(sqlite_conn, "{joueur} frappe  fort face à {adversaire}", "adversaire", "context.opponent_team")
        joueur = Player(id=1, first_name="kylian", last_name="Mbappé")
        contexte = MatchContext(match_id="m1", home_team="Lyon", away_team="Le Havre AC", is_home=True, player_team="Lyon")

        resultat = _resultat(sqlite_conn, joueur, contexte=contexte)

        assert isinstance(resultat, SelectionResult)
        assert resultat.phrase.text == "{joueur} frappe  fort face à {adversaire}"  # le gabarit est intact
        # slots resolus, espaces ecrases, majuscule initiale, contraction "à Le" -> "au"
        assert resultat.rendered_text == "Kylian Mbappé frappe fort face au Havre AC"

    def test_le_texte_rendu_est_celui_que_update_cooldown_doit_enregistrer(self, sqlite_conn):
        from engine.anti_repeat import similarity_penalty, update_cooldown

        _banque(sqlite_conn, {"DEFAUT": {"defaut": True, "phrases": [("un but superbe de {joueur} ce soir", [])]}})
        _ajouter_slot(sqlite_conn, "un but superbe de {joueur} ce soir", "joueur", "player.full_name")
        joueur = Player(id=1, first_name="Ousmane", last_name="Dembélé")
        resultat = _resultat(sqlite_conn, joueur, match_sequence=10)
        update_cooldown(sqlite_conn, resultat.phrase, joueur, "m10", resultat.rendered_text, match_sequence=10)
        assert similarity_penalty(sqlite_conn, resultat.rendered_text, joueur, match_sequence=10) == 1.0
        assert sqlite_conn.execute("SELECT rendered_text FROM phrase_history").fetchone()[0] == "Un but superbe d'Ousmane Dembélé ce soir"

    def test_une_phrase_de_secours_est_aussi_rendue(self, sqlite_conn):
        _banque(sqlite_conn, {"DEFAUT": {"defaut": True, "phrases": [("spec", RAPIDE)]}})
        secours_id = _ajouter_secours(sqlite_conn, "le match suit son cours.")
        resultat = _resultat(sqlite_conn, _joueur_lent())
        assert (resultat.phrase.id, resultat.phrase.is_fallback) == (secours_id, True)
        assert resultat.rendered_text == "Le match suit son cours."  # post_process applique

    def test_le_resultat_est_immuable(self, sqlite_conn):
        _banque(sqlite_conn, {"DEFAUT": {"defaut": True, "phrases": [("x", [])]}})
        resultat = _resultat(sqlite_conn)
        with pytest.raises(AttributeError):
            resultat.rendered_text = "autre"  # type: ignore[misc]

    def test_le_rendu_est_reproductible_avec_la_meme_graine(self, sqlite_conn):
        _banque(sqlite_conn, {"DEFAUT": {"defaut": True, "phrases": [(f"phrase numero {i}", []) for i in range(10)]}})
        assert _resultat(sqlite_conn, seed=9) == _resultat(sqlite_conn, seed=9)


# --- Memoire INTER-JOUEURS (cooldown global) -----------------------------------------

MITRAILLEUR = "Le mitrailleur tire de partout et envoie encore celle-là dans les nuages !"
TIREUR = [("Pace", ">=", "9")]  # 20 % de la population de test : discriminante (ciblage 1.0)


def _banque_mitrailleur(conn, generiques: int = 2) -> None:
    """Un modele SANS slot de protagoniste (surnom seul, comme la phrase 489 de la vraie banque) et des generiques."""
    _banque(conn, {
        "DEFAUT": {"defaut": True, "phrases": [(f"Generique numero {i} sans rapport", []) for i in range(generiques)]},
        "SURNOM": {"phrases": [(MITRAILLEUR, TIREUR)]},
    })


class TestCooldownGlobal:
    def test_non_regression_global_cooldown(self, sqlite_conn):
        """Echantillon du 01/10/2026 : « Le mitrailleur… » (phrase 489) servi a Tolisso (M1 52') puis a Zaire-Emery
        (M2 20') -- puis a 5 autres joueurs. Le cooldown par joueur ne le voyait pas ; la memoire globale, si."""
        _banque_mitrailleur(sqlite_conn)
        tolisso, zaire_emery = _joueur_rapide(), Player(id=3, first_name="Warren", last_name="Zaire-Emery", attributes={"Pace": 80})
        _usage(sqlite_conn, MITRAILLEUR, tolisso.id, 1)
        # meme match : bloque pour un AUTRE joueur, quelle que soit la graine
        assert MITRAILLEUR not in {_select(sqlite_conn, zaire_emery, match_sequence=1, seed=g).text for g in range(200)}
        # match suivant : penalise (0.9 de penalite -> poids x 0.1), puis libre une fois la fenetre ecoulee
        suivant = [_select(sqlite_conn, zaire_emery, match_sequence=2, seed=g).text for g in range(800)].count(MITRAILLEUR)
        libre = [_select(sqlite_conn, zaire_emery, match_sequence=6, seed=g).text for g in range(800)].count(MITRAILLEUR)
        assert 0 < suivant < libre / 2

    def test_surnom_seul_global(self, sqlite_conn):
        """Un modele sans slot de joueur ne peut pas sortir deux fois dans le meme match, tant que le pool a une alternative :
        4 evenements de 4 joueurs differents -> les 4 modeles du pool (1 surnom seul + 3 generiques) sortent chacun une fois."""
        _banque_mitrailleur(sqlite_conn, generiques=3)
        tires = []
        for rang_evenement in range(4):
            joueur = Player(id=10 + rang_evenement, first_name="J", last_name=str(rang_evenement), attributes={"Pace": 90})
            sqlite_conn.execute("INSERT INTO players (id, first_name, last_name) VALUES (?, 'J', 'x')", (joueur.id,))
            sqlite_conn.commit()
            resultat = _resultat(sqlite_conn, joueur, match_sequence=5, seed=rang_evenement)
            update_cooldown(sqlite_conn, resultat.phrase, joueur, "m5", resultat.rendered_text, match_sequence=5)
            tires.append(resultat.phrase.text)
        assert len(set(tires)) == 4
        assert tires.count(MITRAILLEUR) <= 1

    def test_pool_epuise_la_memoire_globale_est_relachee_sans_secours(self, sqlite_conn):
        _banque(sqlite_conn, {"DEFAUT": {"defaut": True, "phrases": [("seule phrase", [])]}})
        _ajouter_secours(sqlite_conn)
        _usage(sqlite_conn, "seule phrase", 3, 10)  # un autre joueur, meme match : bloquee globalement
        assert _resultat(sqlite_conn, match_sequence=10).phrase.text == "seule phrase"  # et non le secours

    def test_le_cooldown_global_est_deterministe(self, sqlite_conn):
        _banque_mitrailleur(sqlite_conn)
        _usage(sqlite_conn, MITRAILLEUR, 3, 5)
        assert [_select(sqlite_conn, match_sequence=6, seed=g).text for g in range(30)] == [
            _select(sqlite_conn, match_sequence=6, seed=g).text for g in range(30)
        ]

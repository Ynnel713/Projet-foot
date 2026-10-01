"""phrase_selector : filtre mandatory et paliers (Bloc 2, commit 1), cascade de variantes
(commit 2). La classe TestCascadeDeVariantesSpec verrouille encore le DOCSTRING du module ; elle
sera remplacee par des tests de comportement au commit 3."""

from __future__ import annotations

import logging

import pytest

from engine.models import MatchContext, Phrase, PhraseCondition, Player, Variant
from engine.phrase_selector import (
    AucunCandidatError,
    candidats,
    ordonner_variantes,
    palier_retenu,
    paliers,
    select,
)
from engine.selectivity import Selectivite


def _player() -> Player:
    return Player(id=1, first_name="A", last_name="B")


def _context() -> MatchContext:
    return MatchContext(match_id="m1")


class TestCascadeDeVariantesSpec:
    """select() n'est pas implemente -- il n'y a donc pas de COMPORTEMENT a
    tester pour la cascade de variantes (decision du 01/10/2026, etape 7 de
    l'algorithme). Mais la DECISION elle-meme (pas juste une intention) doit
    survivre a une reecriture distraite du docstring -- sans ca, la
    formalisation n'est qu'un vœu pieux. Ces tests verrouillent chacune des
    garanties promises (ordre, garde-fou, logging) independamment, pour
    qu'un echec pointe precisement CE qui a disparu plutot qu'un diff vague
    sur tout le docstring."""

    @staticmethod
    def _doc() -> str:
        import engine.phrase_selector as module

        assert module.__doc__ is not None
        return module.__doc__

    def test_cascade_falls_back_to_other_active_variants_on_zero_candidates(self):
        doc = self._doc()
        assert "0 candidat" in doc
        assert "is_active=1" in doc or "variantes actives" in doc

    def test_cascade_order_is_deterministic_non_default_first_then_default_last(self):
        doc = self._doc()
        assert "weight" in doc and "decroissant" in doc
        assert "is_default" in doc and "dernier recours" in doc

    def test_cascade_reapplies_mandatory_conditions_and_cooldown_unchanged(self):
        doc = self._doc()
        assert "cooldown obligatoire" in doc
        assert "jamais contournes" in doc

    def test_cascade_has_an_anti_loop_guard(self):
        doc = self._doc()
        assert "anti-boucle" in doc
        assert "au plus une fois" in doc

    def test_cascade_activation_is_logged_as_warning(self):
        doc = self._doc()
        assert "LOGGING obligatoire" in doc
        assert "WARNING" in doc

    def test_cascade_exhaustion_falls_through_to_the_final_fallback(self):
        # L'etape 7 ne remplace pas le fallback final (toujours a definir) --
        # elle le retarde jusqu'a ce que TOUTES les variantes actives aient
        # ete tentees, pas une seule.
        doc = self._doc()
        assert "fallback final explicite" in doc
        assert "toujours a definir" in doc


# --- Bloc 2 (1/4) : filtre mandatory, partition specifiques / generiques --------


def _cond(attribute: str, operator: str, value: str, mandatory: bool = True) -> PhraseCondition:
    return PhraseCondition(id=1, phrase_id=1, attribute=attribute, operator=operator, value=value, mandatory=mandatory)


def _p(identifiant: int, *conditions: PhraseCondition, **champs) -> Phrase:
    return Phrase(id=identifiant, variant_id=1, text=f"p{identifiant}", conditions=conditions, **champs)


def _joueur_rapide() -> Player:
    return Player(id=1, first_name="A", last_name="B", attributes={"Pace": 90, "Finishing": 40})


def _population_pace() -> Selectivite:
    """10 joueurs de champ, Pace 1..10."""
    return Selectivite([Player(id=i, first_name="J", last_name=str(i), attributes={"Pace": i}) for i in range(1, 11)])


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


class TestPartitionEtPaliers:
    def test_partition_a_70_pour_cent(self):
        specifique = _p(1, _cond("Pace", ">=", "4"))  # 7/10 = 70 % : specifique
        large = _p(2, _cond("Pace", ">=", "3"))  # 8/10 : generique
        sans_condition = _p(3)
        specifiques, generiques = paliers([specifique, large, sans_condition], _population_pace())
        assert [p.id for p in specifiques] == [1]
        assert [p.id for p in generiques] == [2, 3]

    def test_un_specifique_eligible_l_emporte_et_les_generiques_sont_ecartes(self):
        pool = [_p(1, _cond("Pace", ">=", "8")), _p(2), _p(3, _cond("Pace", ">=", "1"))]
        assert [p.id for p in palier_retenu(pool, _population_pace())] == [1]

    def test_zero_specifique_repli_sur_les_generiques(self):
        pool = [_p(2), _p(3, _cond("Pace", ">=", "1"))]  # sans condition, et trop large (100 %)
        assert [p.id for p in palier_retenu(pool, _population_pace())] == [2, 3]

    def test_zero_generique_les_specifiques_servent(self):
        assert [p.id for p in palier_retenu([_p(1, _cond("Pace", ">=", "8"))], _population_pace())] == [1]

    def test_pool_vide_donne_une_liste_vide(self):
        assert palier_retenu([], _population_pace()) == []

    def test_repli_apres_filtre_conditions_et_cooldown(self):
        """Le pool arrive deja filtre (conditions, puis cooldown au commit 3) : si le seul specifique
        est ecarte (condition non satisfaite), les generiques prennent le relais."""
        joueur_lent = Player(id=3, first_name="L", last_name="ent", attributes={"Pace": 2})
        pool = candidats([_p(1, _cond("Pace", ">=", "8")), _p(2)], joueur_lent, _context())
        assert [p.id for p in palier_retenu(pool, _population_pace())] == [2]


# --- Bloc 2 (2/4) : cascade de variantes ----------------------------------------


def _v(identifiant: int, code: str, *, defaut: bool = False, poids: float = 1.0, active: bool = True) -> Variant:
    return Variant(id=identifiant, scenario_id=1, code=code, label=code, is_default=defaut, weight=poids, is_active=active)


class TestOrdreDeLaCascade:
    def test_non_defaut_par_poids_decroissant_puis_id_croissant_puis_defaut_en_dernier(self):
        variantes = [
            _v(1, "DEFAUT", defaut=True),
            _v(2, "SURNOM", poids=1.0),
            _v(3, "PENALTY", poids=2.0),
            _v(4, "AUTRE", poids=1.0),
        ]
        assert [v.code for v in ordonner_variantes(variantes)] == ["PENALTY", "SURNOM", "AUTRE", "DEFAUT"]

    def test_les_variantes_inactives_sont_ignorees(self):
        variantes = [_v(1, "DEFAUT", defaut=True), _v(2, "SURNOM", active=False)]
        assert [v.code for v in ordonner_variantes(variantes)] == ["DEFAUT"]

    def test_l_ordre_ne_depend_pas_de_l_ordre_d_entree(self):
        variantes = [_v(1, "DEFAUT", defaut=True), _v(2, "SURNOM"), _v(3, "PENALTY")]
        assert ordonner_variantes(variantes) == ordonner_variantes(list(reversed(variantes)))


def _banque(conn, variantes: dict[str, dict]) -> None:
    """Scenario BUT_TEST ; `variantes` : code -> {defaut, poids, active, phrases: [(texte, [(attr, op, val)], poids)]}."""
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
            for attribut, operateur, valeur in conditions:
                conn.execute(
                    "INSERT INTO phrase_conditions (phrase_id, attribute, operator, value) VALUES (?, ?, ?, ?)",
                    (phrase_id, attribut, operateur, valeur),
                )
    conn.commit()


RAPIDE = [("Pace", ">=", "8")]  # specifique pour _population_pace (30 %)


class TestSelectCascade:
    def test_surnom_dont_la_condition_est_satisfaite_bat_defaut_generique(self, sqlite_conn):
        _banque(sqlite_conn, {
            "DEFAUT": {"defaut": True, "phrases": [("generique A", []), ("generique B", [])]},
            "SURNOM": {"phrases": [("Le sprinter file", RAPIDE)]},
        })
        for graine in range(20):
            phrase = select(sqlite_conn, "BUT_TEST", _joueur_rapide(), _context(), seed=graine, selectivite=_population_pace())
            assert phrase.text == "Le sprinter file"

    def test_surnom_vide_defaut_sert(self, sqlite_conn):
        joueur_lent = Player(id=3, first_name="L", last_name="ent", attributes={"Pace": 2})
        _banque(sqlite_conn, {
            "DEFAUT": {"defaut": True, "phrases": [("generique", [])]},
            "SURNOM": {"phrases": [("Le sprinter file", RAPIDE)]},
        })
        phrase = select(sqlite_conn, "BUT_TEST", joueur_lent, _context(), seed=1, selectivite=_population_pace())
        assert phrase.text == "generique"

    def test_une_variante_a_zero_candidat_laisse_la_place_a_la_suivante_une_seule_fois(self, sqlite_conn, monkeypatch):
        import engine.phrase_selector as module

        joueur_lent = Player(id=3, first_name="L", last_name="ent", attributes={"Pace": 2})
        _banque(sqlite_conn, {
            "DEFAUT": {"defaut": True, "phrases": [("generique", [])]},
            "SURNOM": {"phrases": [("A", RAPIDE)]},
            "PENALTY": {"poids": 2.0, "phrases": [("B", RAPIDE)]},
        })
        charges: list[int] = []
        original = module.load_phrases
        monkeypatch.setattr(module, "load_phrases", lambda conn, variante_id: charges.append(variante_id) or original(conn, variante_id))

        phrase = select(sqlite_conn, "BUT_TEST", joueur_lent, _context(), seed=1, selectivite=_population_pace())

        assert phrase.text == "generique"
        assert len(charges) == 3 and len(set(charges)) == 3  # PENALTY, SURNOM, DEFAUT : une fois chacune

    def test_on_s_arrete_a_la_premiere_variante_qui_produit_un_candidat(self, sqlite_conn, monkeypatch):
        import engine.phrase_selector as module

        _banque(sqlite_conn, {
            "DEFAUT": {"defaut": True, "phrases": [("generique", [])]},
            "SURNOM": {"phrases": [("Le sprinter file", RAPIDE)]},
        })
        charges: list[int] = []
        original = module.load_phrases
        monkeypatch.setattr(module, "load_phrases", lambda conn, variante_id: charges.append(variante_id) or original(conn, variante_id))
        select(sqlite_conn, "BUT_TEST", _joueur_rapide(), _context(), seed=1, selectivite=_population_pace())
        assert len(charges) == 1  # DEFAUT n'a meme pas ete charge

    def test_la_variante_par_poids_decroissant_passe_la_premiere(self, sqlite_conn):
        _banque(sqlite_conn, {
            "DEFAUT": {"defaut": True, "phrases": [("generique", [])]},
            "SURNOM": {"poids": 1.0, "phrases": [("surnom", RAPIDE)]},
            "PENALTY": {"poids": 3.0, "phrases": [("penalty", RAPIDE)]},
        })
        assert select(sqlite_conn, "BUT_TEST", _joueur_rapide(), _context(), seed=1, selectivite=_population_pace()).text == "penalty"

    def test_une_variante_inactive_n_est_jamais_essayee(self, sqlite_conn):
        _banque(sqlite_conn, {
            "DEFAUT": {"defaut": True, "phrases": [("generique", [])]},
            "SURNOM": {"active": False, "phrases": [("surnom", RAPIDE)]},
        })
        assert select(sqlite_conn, "BUT_TEST", _joueur_rapide(), _context(), seed=1, selectivite=_population_pace()).text == "generique"

    def test_les_generiques_servent_quand_aucun_specifique_n_est_eligible_dans_la_variante(self, sqlite_conn):
        joueur_lent = Player(id=3, first_name="L", last_name="ent", attributes={"Pace": 2})
        _banque(sqlite_conn, {"DEFAUT": {"defaut": True, "phrases": [("spec", RAPIDE), ("gen", [])]}})
        assert select(sqlite_conn, "BUT_TEST", joueur_lent, _context(), seed=1, selectivite=_population_pace()).text == "gen"

    def test_un_fallback_n_est_jamais_tire_dans_le_pool_normal(self, sqlite_conn):
        _banque(sqlite_conn, {"DEFAUT": {"defaut": True, "phrases": [("normale", [])]}})
        sqlite_conn.execute("INSERT INTO phrases (variant_id, text, is_fallback) VALUES (1, 'secours', 1)")
        sqlite_conn.commit()
        textes = {select(sqlite_conn, "BUT_TEST", _joueur_rapide(), _context(), seed=g, selectivite=_population_pace()).text for g in range(30)}
        assert textes == {"normale"}

    def test_scenario_inconnu_leve_key_error(self, sqlite_conn):
        with pytest.raises(KeyError, match="INCONNU"):
            select(sqlite_conn, "INCONNU", _joueur_rapide(), _context(), seed=1, selectivite=_population_pace())


class TestTirage:
    def test_meme_graine_meme_phrase_et_la_graine_fait_varier_le_tirage(self, sqlite_conn):
        _banque(sqlite_conn, {"DEFAUT": {"defaut": True, "phrases": [(f"g{i}", []) for i in range(10)]}})
        def tirer(graine):
            return select(sqlite_conn, "BUT_TEST", _joueur_rapide(), _context(), seed=graine, selectivite=_population_pace()).text
        assert tirer(7) == tirer(7)
        assert len({tirer(g) for g in range(40)}) > 4

    def test_une_phrase_de_poids_nul_n_est_jamais_tiree(self, sqlite_conn):
        _banque(sqlite_conn, {"DEFAUT": {"defaut": True, "phrases": [("poids nul", [], 0.0), ("poids un", [], 1.0)]}})
        textes = {select(sqlite_conn, "BUT_TEST", _joueur_rapide(), _context(), seed=g, selectivite=_population_pace()).text for g in range(40)}
        assert textes == {"poids un"}


class TestWarningUnique:
    def test_defaut_a_zero_candidat_un_seul_warning_enrichi_puis_erreur(self, sqlite_conn, caplog):
        joueur_lent = Player(id=3, first_name="L", last_name="ent", attributes={"Pace": 2})
        _banque(sqlite_conn, {
            "DEFAUT": {"defaut": True, "phrases": [("spec", RAPIDE)]},
            "SURNOM": {"phrases": [("surnom", RAPIDE)]},
        })
        with caplog.at_level(logging.WARNING, logger="engine.phrase_selector"):
            with pytest.raises(AucunCandidatError, match="BUT_TEST"):
                select(sqlite_conn, "BUT_TEST", joueur_lent, _context(), seed=1, selectivite=_population_pace())
        avertissements = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert len(avertissements) == 1
        message = avertissements[0].getMessage()
        assert "BUT_TEST" in message and "SURNOM#2" in message and "DEFAUT#1" in message

    def test_le_passage_normal_surnom_vers_defaut_ne_logue_rien(self, sqlite_conn, caplog):
        joueur_lent = Player(id=3, first_name="L", last_name="ent", attributes={"Pace": 2})
        _banque(sqlite_conn, {
            "DEFAUT": {"defaut": True, "phrases": [("generique", [])]},
            "SURNOM": {"phrases": [("surnom", RAPIDE)]},
        })
        with caplog.at_level(logging.DEBUG, logger="engine.phrase_selector"):
            select(sqlite_conn, "BUT_TEST", joueur_lent, _context(), seed=1, selectivite=_population_pace())
        assert [r for r in caplog.records if r.levelno >= logging.WARNING] == []

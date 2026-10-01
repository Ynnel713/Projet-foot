"""phrase_selector.select est un SQUELETTE (voir engine/phrase_selector.py) :
tant que la banque de phrases n'est pas livrée, il n'existe aucun
comportement réel à tester (0 candidat -> fallback, tirage reproductible
avec seed, conditions mandatory -- voir le brief) puisqu'aucune phrase ne
doit être générée dans cette session. Le seul contrat vérifiable ici est que
l'appel échoue explicitement (NotImplementedError, jamais un texte inventé
ni un crash silencieux). Ces tests seront remplacés par les cas du brief
(0 candidat, seed, mandatory) à l'implémentation réelle."""

from __future__ import annotations

import pytest

from engine.models import MatchContext, Phrase, PhraseCondition, Player
from engine.phrase_selector import candidats, palier_retenu, paliers, select
from engine.selectivity import Selectivite


def _player() -> Player:
    return Player(id=1, first_name="A", last_name="B")


def _context() -> MatchContext:
    return MatchContext(match_id="m1")


def test_select_raises_not_implemented_error(sqlite_conn):
    with pytest.raises(NotImplementedError):
        select(sqlite_conn, "BUT_TEST", _player(), _context())


def test_select_error_message_names_the_module():
    with pytest.raises(NotImplementedError, match="phrase_selector.select"):
        select(None, "BUT_TEST", _player(), _context())  # type: ignore[arg-type]


def test_select_accepts_an_injectable_rng_without_using_it_yet():
    import random

    with pytest.raises(NotImplementedError):
        select(None, "BUT_TEST", _player(), _context(), rng=random.Random(42))  # type: ignore[arg-type]


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

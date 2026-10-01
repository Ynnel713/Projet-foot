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

from engine.models import MatchContext, Player
from engine.phrase_selector import select


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

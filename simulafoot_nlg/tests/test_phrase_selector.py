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

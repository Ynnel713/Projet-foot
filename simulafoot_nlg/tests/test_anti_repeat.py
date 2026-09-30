"""anti_repeat.* sont des SQUELETTES (voir engine/anti_repeat.py) -- même
raisonnement que test_phrase_selector.py : les cas du brief (cooldown
écoulé/non écoulé, récence, similarité Jaccard) décrivent l'algorithme
FUTUR, pas testable tant qu'aucune implémentation n'existe. Seul le contrat
"échoue explicitement" est vérifié ici."""

from __future__ import annotations

import pytest

from engine.anti_repeat import recency_penalty, similarity_penalty, update_cooldown
from engine.models import Phrase, Player


def _phrase() -> Phrase:
    return Phrase(id=1, variant_id=1, text="{player_name} marque !")


def _player() -> Player:
    return Player(id=1, first_name="A", last_name="B")


def test_recency_penalty_raises_not_implemented_error(sqlite_conn):
    with pytest.raises(NotImplementedError):
        recency_penalty(sqlite_conn, _phrase(), _player(), "m1")


def test_similarity_penalty_raises_not_implemented_error(sqlite_conn):
    with pytest.raises(NotImplementedError):
        similarity_penalty(sqlite_conn, "Quel but !", _player())


def test_update_cooldown_raises_not_implemented_error(sqlite_conn):
    with pytest.raises(NotImplementedError):
        update_cooldown(sqlite_conn, _phrase(), _player(), "m1", "Quel but !")

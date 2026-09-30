"""template_filler.render est un SQUELETTE (voir engine/template_filler.py)
-- même raisonnement que test_phrase_selector.py : les cas du brief (slot
manquant, caractères spéciaux, nom avec apostrophe) décrivent l'algorithme
FUTUR. Seul le contrat "échoue explicitement" est vérifié ici -- y compris
avec un joueur à nom à apostrophe, pour documenter que ce cas limite est
attendu dès l'implémentation (pas une régression future)."""

from __future__ import annotations

import pytest

from engine.models import MatchContext, Phrase, PhraseSlot, Player
from engine.template_filler import render


def test_render_raises_not_implemented_error(sqlite_conn):
    phrase = Phrase(id=1, variant_id=1, text="{player_name} marque !")
    player = Player(id=1, first_name="A", last_name="B")
    context = MatchContext(match_id="m1")

    with pytest.raises(NotImplementedError):
        render(phrase, player, context)


def test_render_with_apostrophe_name_also_raises_not_implemented_error():
    # Cas limite explicite du brief (nom avec apostrophe) : ne doit pas
    # planter AUTREMENT qu'avec NotImplementedError (pas d'UnicodeError, pas
    # de KeyError sur le nom lui-même).
    phrase = Phrase(
        id=1,
        variant_id=1,
        text="{player_name} marque !",
        slots=(PhraseSlot(id=1, phrase_id=1, slot_name="player_name", expression="player.full_name"),),
    )
    player = Player(id=1, first_name="Jake", last_name="O'Brien")
    context = MatchContext(match_id="m1")

    with pytest.raises(NotImplementedError):
        render(phrase, player, context)

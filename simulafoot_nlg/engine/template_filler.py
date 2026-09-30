"""SQUELETTE -- remplacement des emplacements `{slot_name}` d'une Phrase par
leur valeur resolue. Aucune implementation dans cette session.

Algorithme prevu :
    Pour chaque PhraseSlot de `phrase.slots` :
        - `expression` renseignee (ex. "player.full_name") -> evaluee contre
          `player`/`context` via un mini-interpreteur d'attributs a points
          restreint (PAS `eval()` -- surface d'attaque inacceptable pour du
          texte potentiellement issu d'un YAML edite a la main), produisant
          un SlotExpression avec resolved_value rempli.
        - `dictionary_key` renseignee -> tirage pondere dans
          slot_dictionaries (voir data/seed/slots.yml) parmi les entrees de
          cette cle ; `rng` injectable comme pour phrase_selector.select.
        - ni l'un ni l'autre, ou slot reference absent des deux -- cas
          limite explicite du brief ("Phrase referencant un slot
          inexistant") : NE DOIT PAS lever d'exception qui casse tout le
          match ; a la place, laisser une trace explicite (ex. lever une
          exception DEDIEE `SlotResolutionError`, que l'appelant (phrase_selector)
          pourra choisir de traiter comme "phrase invalide, en choisir une
          autre" plutot que de laisser planter la generation).
    Une fois tous les slots resolus, remplacer chaque "{slot_name}" du texte
    par sa valeur (`str.format_map` ou equivalent controle -- pas
    `str.format(**kwargs)` direct, pour eviter qu'un nom de slot avec un
    format-spec accidentel (ex. "{score:d}") ne casse le rendu).
"""

from __future__ import annotations

import random

from engine.models import MatchContext, Phrase, Player


def render(
    phrase: Phrase,
    player: Player,
    context: MatchContext,
    *,
    rng: random.Random | None = None,
) -> str:
    """Rend `phrase.text` avec tous ses slots resolus pour (`player`,
    `context`) -- voir algorithme prevu en tete de module. Leve
    NotImplementedError tant que la banque de phrases n'est pas livree."""
    raise NotImplementedError(
        "template_filler.render : squelette non implémenté -- voir la docstring "
        "de engine/template_filler.py pour l'algorithme prévu."
    )

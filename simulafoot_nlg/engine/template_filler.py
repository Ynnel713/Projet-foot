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
import re
from typing import Any

from engine.models import MatchContext, Phrase, Player


class SlotResolutionError(ValueError):
    """Un slot ne peut pas etre resolu (expression invalide, chemin inconnu ou a valeur
    absente...). Exception DEDIEE : phrase_selector peut la traiter comme "phrase
    invalide, en choisir une autre" au lieu de laisser planter tout un match."""


# "player" ou "context", puis un ou plusieurs segments en minuscules : un CHEMIN
# d'attributs, jamais autre chose (pas d'appel, d'indexation, d'operateur, d'espace).
_EXPRESSION_RE = re.compile(r"(player|context)(\.[a-z][a-z0-9_]*)+")


def resolve_expression(expression: str, player: Player, context: MatchContext) -> str:
    """Valeur (en texte) d'une expression de slot comme "player.full_name",
    "context.opponent_team" ou "context.passeur.full_name" : mini-interpreteur
    d'attributs a points, SANS eval() (le YAML est edite a la main). Grammaire :
    `player` | `context`, suivi de `.segment` (minuscules, chiffres, `_`, sans `_` initial).

    Leve SlotResolutionError si l'expression sort de cette grammaire, si un segment
    n'existe pas, si un segment est une methode (appel interdit) ou si une valeur du
    chemin est None (ex. `context.passeur` absent : un slot ne se rend jamais en "None")."""
    if not isinstance(expression, str) or _EXPRESSION_RE.fullmatch(expression) is None:
        raise SlotResolutionError(
            f"Expression de slot invalide : {expression!r} (attendu : player.<champ> ou "
            "context.<champ>[.<champ>...], en minuscules)."
        )
    racine, *chemin = expression.split(".")
    valeur: Any = player if racine == "player" else context
    parcouru = racine
    for segment in chemin:
        if valeur is None:
            raise SlotResolutionError(f"Expression {expression!r} : {parcouru} vaut None, {segment!r} introuvable.")
        if not hasattr(valeur, segment):
            raise SlotResolutionError(f"Expression {expression!r} : {parcouru} n'a pas d'attribut {segment!r}.")
        valeur = getattr(valeur, segment)
        parcouru = f"{parcouru}.{segment}"
        if callable(valeur):
            raise SlotResolutionError(f"Expression {expression!r} : {parcouru} est une methode (appel interdit).")
    if valeur is None:
        raise SlotResolutionError(f"Expression {expression!r} : valeur absente (None).")
    return str(valeur)


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

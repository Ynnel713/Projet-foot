"""Remplacement des emplacements `{slot_name}` d'une Phrase par leur valeur resolue.

Pour chaque PhraseSlot de `phrase.slots` :
    - `expression` (ex. "player.full_name") -> evaluee contre `player`/`context` par un
      mini-interpreteur d'attributs a points (resolve_expression) -- PAS `eval()` : le
      YAML est edite a la main ;
    - un slot du texte sans valeur resolue -> SlotResolutionError (jamais un "{slot}"
      affiche tel quel a l'ecran) ; l'appelant (phrase_selector) la traite comme "phrase
      invalide, en choisir une autre".
Le texte est rempli en UNE passe (regex), pas par `str.format` : un nom de slot a
format-spec accidentel ("{score:d}") ne casse pas le rendu, et une valeur qui contient
des accolades n'est jamais re-developpee. Le texte rendu est BRUT : le post-traitement
linguistique (post_process.apply) est une etape distincte, appliquee apres.
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


_SLOT_RE = re.compile(r"\{(\w+)\}")


def render(
    phrase: Phrase,
    player: Player,
    context: MatchContext,
    *,
    rng: random.Random | None = None,
) -> str:
    """Rend `phrase.text` avec tous ses slots resolus pour (`player`, `context`) -- voir
    docstring du module. Leve SlotResolutionError si un slot du texte n'a pas de valeur."""
    valeurs: dict[str, str] = {}
    for slot in phrase.slots:
        if slot.expression is not None:
            valeurs[slot.slot_name] = resolve_expression(slot.expression, player, context)

    def remplacer(correspondance: re.Match[str]) -> str:
        nom = correspondance.group(1)
        if nom not in valeurs:
            raise SlotResolutionError(f"Slot {{{nom}}} sans valeur resolue dans {phrase.text!r}.")
        return valeurs[nom]

    return _SLOT_RE.sub(remplacer, phrase.text)

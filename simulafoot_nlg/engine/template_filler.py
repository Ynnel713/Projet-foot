"""Remplacement des emplacements `{slot_name}` d'une Phrase par leur valeur resolue.

Pour chaque PhraseSlot de `phrase.slots` :
    - `expression` (ex. "player.full_name") -> evaluee contre `player`/`context` par un
      mini-interpreteur d'attributs a points (resolve_expression) -- PAS `eval()` : le
      YAML est edite a la main ;
    - `dictionary_key` -> tirage pondere dans `dictionaries[cle]` (meme forme que
      data/seed/slots.yml : liste de {value, weight?}) avec un rng DERIVE PAR PHRASE (voir
      derive_rng) ; un slot tire UNE fois par rendu, dans l'ordre de `phrase.slots`
      (consommation du rng previsible) ;
    - un slot du texte sans valeur resolue -> SlotResolutionError (jamais un "{slot}"
      affiche tel quel a l'ecran) ; l'appelant (phrase_selector) la traite comme "phrase
      invalide, en choisir une autre".
Le texte est rempli en UNE passe (regex), pas par `str.format` : un nom de slot a
format-spec accidentel ("{score:d}") ne casse pas le rendu, et une valeur qui contient
des accolades n'est jamais re-developpee. Le texte rendu est BRUT : le post-traitement
linguistique (post_process.apply) est une etape distincte, appliquee apres.
"""

from __future__ import annotations

import hashlib
import random
import re
from collections.abc import Mapping, Sequence
from typing import Any

from engine.models import MatchContext, Phrase, PhraseSlot, Player


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


def derive_rng(seed: int | str, scenario_code: str, variant_code: str, text: str) -> random.Random:
    """RNG propre a UNE phrase : graine = 8 premiers octets de
    sha256(f"{seed}|{scenario_code}|{variant_code}|{text}"). Cle NATURELLE (codes et texte,
    jamais les id autoincrement, instables apres un reset + reimport) : retirer ou ajouter une
    phrase du pool ne change le rendu d'aucune autre, et deux executions donnent le meme rendu
    (sha256, pas hash() : independant de PYTHONHASHSEED). `seed` est fourni par l'appelant
    (cli.py : derive de match_id, match_sequence et event_id)."""
    if not scenario_code or not variant_code:
        raise ValueError("derive_rng : scenario_code et variant_code sont obligatoires (cle de la graine).")
    cle = f"{seed}|{scenario_code}|{variant_code}|{text}"
    return random.Random(int.from_bytes(hashlib.sha256(cle.encode("utf-8")).digest()[:8], "big"))


def _tirer(
    slot: PhraseSlot, dictionaries: Mapping[str, Sequence[Mapping[str, Any]]] | None, rng: random.Random
) -> str:
    entrees = (dictionaries or {}).get(slot.dictionary_key or "")
    if not entrees:
        raise SlotResolutionError(f"Slot {{{slot.slot_name}}} : dictionnaire {slot.dictionary_key!r} absent ou vide.")
    valeurs: list[str] = []
    poids: list[float] = []
    for entree in entrees:
        try:
            valeur, poids_entree = entree["value"], float(entree.get("weight", 1.0))
        except (KeyError, TypeError, ValueError, AttributeError) as exc:
            raise SlotResolutionError(
                f"Slot {{{slot.slot_name}}} : entree invalide {entree!r} dans {slot.dictionary_key!r} "
                "(attendu : {value, weight?} avec un poids numerique)."
            ) from exc
        if poids_entree < 0:
            raise SlotResolutionError(f"Slot {{{slot.slot_name}}} : poids negatif dans {slot.dictionary_key!r}.")
        valeurs.append(str(valeur))
        poids.append(poids_entree)
    if not any(poids):
        raise SlotResolutionError(f"Slot {{{slot.slot_name}}} : poids tous nuls dans {slot.dictionary_key!r}.")
    return rng.choices(valeurs, weights=poids, k=1)[0]


def _resoudre(
    slot: PhraseSlot,
    player: Player,
    context: MatchContext,
    rng: random.Random,
    dictionaries: Mapping[str, Sequence[Mapping[str, Any]]] | None,
) -> str:
    if (slot.expression is None) == (slot.dictionary_key is None):
        raise SlotResolutionError(
            f"Slot {{{slot.slot_name}}} : exactement un de `expression` et `dictionary_key` est attendu "
            f"(recu expression={slot.expression!r}, dictionary_key={slot.dictionary_key!r})."
        )
    if slot.expression is not None:
        try:
            return resolve_expression(slot.expression, player, context)
        except SlotResolutionError as exc:
            raise SlotResolutionError(f"Slot {{{slot.slot_name}}} : {exc}") from exc
    return _tirer(slot, dictionaries, rng)


def render(
    phrase: Phrase,
    player: Player,
    context: MatchContext,
    *,
    seed: int | str,
    scenario_code: str,
    variant_code: str,
    dictionaries: Mapping[str, Sequence[Mapping[str, Any]]] | None = None,
) -> str:
    """Rend `phrase.text` avec tous ses slots resolus pour (`player`, `context`) -- voir
    docstring du module. Leve SlotResolutionError dans tous ces cas : slot du texte non declare ;
    slot declare sans (ou avec les deux de) expression/dictionary_key ; deux declarations
    differentes du meme slot ; expression invalide ou a valeur absente ; dictionnaire absent,
    vide ou mal forme. Seuls les slots PRESENTS dans le texte sont resolus (un slot declare
    mais inutilise ne consomme ni rng ni erreur).

    `seed`, `scenario_code` et `variant_code` sont OBLIGATOIRES : ils forment, avec le texte, la
    graine du rng de cette phrase (derive_rng) -- une `Phrase` n'a que `variant_id`, c'est donc au
    selecteur de fournir les deux codes. ValueError si un code est vide."""
    rng = derive_rng(seed, scenario_code, variant_code, phrase.text)
    utilises = set(_SLOT_RE.findall(phrase.text))
    declarations: dict[str, PhraseSlot] = {}
    valeurs: dict[str, str] = {}
    for slot in phrase.slots:
        if slot.slot_name not in utilises:
            continue
        precedente = declarations.get(slot.slot_name)
        if precedente is not None:
            # Un slot repete dans le texte est declare plusieurs fois par le convertisseur :
            # normal si c'est la meme definition, ambigu sinon.
            if (precedente.expression, precedente.dictionary_key) != (slot.expression, slot.dictionary_key):
                raise SlotResolutionError(
                    f"Slot {{{slot.slot_name}}} : declare deux fois avec des definitions differentes."
                )
            continue
        declarations[slot.slot_name] = slot
        valeurs[slot.slot_name] = _resoudre(slot, player, context, rng, dictionaries)

    def remplacer(correspondance: re.Match[str]) -> str:
        nom = correspondance.group(1)
        if nom not in valeurs:
            raise SlotResolutionError(f"Slot {{{nom}}} non declare dans {phrase.text!r}.")
        return valeurs[nom]

    return _SLOT_RE.sub(remplacer, phrase.text)

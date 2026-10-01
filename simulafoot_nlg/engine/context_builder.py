"""Construit le `MatchContext` d'un evenement valide : dict (event_contract) -> MatchContext.

Les identifiants de protagonistes (`passeur_id`, `receveur_id`, `sortant_id`, `entrant_id`) sont
resolus en `Player` par player_resolver (lookup en base, D14) ; les autres champs sont recopies tels
quels et normalises par profile_engine.normalize_match_context. `scenario_code` n'est PAS decide ici
(c'est narrative_adapter) : `select` le recoit en argument. L'ACTEUR (`player_id`) n'est pas dans le
contexte : c'est le `player` de `select`, resolu par l'appelant.
"""

from __future__ import annotations

from collections.abc import Mapping
from sqlite3 import Connection
from typing import Any

from engine.models import MatchContext
from engine.player_resolver import resolve
from engine.profile_engine import normalize_match_context

#: cle du dict d'evenement -> champ de MatchContext qui recoit le Player resolu.
_PROTAGONISTES = {
    "passeur_id": "passeur",
    "receveur_id": "receveur",
    "sortant_id": "sortant",
    "entrant_id": "entrant",
}

_CHAMPS_RECOPIES = (
    "match_id",
    "match_sequence",
    "minute",
    "home_team",
    "away_team",
    "player_team",
    "is_home",
    "competition",
    "journee",
    "score_context",
    "gabarit",
)


def dict_to_context(event: Mapping[str, Any], conn: Connection) -> MatchContext:
    """`MatchContext` complet de `event` (deja valide par event_contract.validate_event). Les
    protagonistes presents dans le dict sont resolus en base ; ceux qui ne s'appliquent pas a la
    famille d'evenement restent None (jamais remplis "au cas ou"). KeyError si un identifiant est
    inconnu de la table players."""
    brut: dict[str, Any] = {cle: event[cle] for cle in _CHAMPS_RECOPIES if cle in event}
    for cle, champ in _PROTAGONISTES.items():
        if cle in event:
            brut[champ] = resolve(event[cle], conn)
    return normalize_match_context(brut)

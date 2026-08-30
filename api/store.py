"""État des compétitions créées via l'API, en mémoire (process-local).

Suffisant pour un usage personnel hébergé en local : redémarrer le backend
perd les parties en cours. Si la persistance entre redémarrages devient
nécessaire, remplacer par SQLite/shelve sans toucher au moteur --
`CustomCompetition` reste l'unique source de vérité.
"""

from __future__ import annotations

import uuid

from ligue1sim.custom_competition import CustomCompetition

_COMPETITIONS: dict[str, CustomCompetition] = {}
_PREVIOUS_RANKS: dict[str, dict[str, int]] = {}


def create(competition: CustomCompetition) -> str:
    comp_id = str(uuid.uuid4())
    _COMPETITIONS[comp_id] = competition
    _PREVIOUS_RANKS[comp_id] = {}
    return comp_id


def get(comp_id: str) -> CustomCompetition:
    if comp_id not in _COMPETITIONS:
        raise KeyError(comp_id)
    return _COMPETITIONS[comp_id]


def previous_ranks(comp_id: str) -> dict[str, int]:
    return _PREVIOUS_RANKS.get(comp_id, {})


def update_ranks(comp_id: str, ranks: dict[str, int]) -> None:
    _PREVIOUS_RANKS[comp_id] = ranks

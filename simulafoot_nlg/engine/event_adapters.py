"""Adaptateurs des cartons et des remplacements du moteur vers les dicts du contrat (event_contract).

Les buts et occasions arrivent deja au format du contrat (NarrativeEvent -> dict cote racine) ; les
cartons (`CardEvent`) et remplacements (`SubstitutionEvent`) ont un autre vocabulaire (`club_name`,
`card_type`, `player_on` / `player_off`). Ces deux fonctions ne font que TRADUIRE ce vocabulaire :
elles produisent un `CartonDict` / `RemplacementDict` et ne decident JAMAIS du `scenario_code` (c'est
narrative_adapter.event_to_scenario, seul decideur).

Entrees : des dicts BRUTS dont les joueurs sont deja des IDENTIFIANTS (la racine resout les noms en
`players.id`, proprio-conversion hors V2.1) :
    carton        : match_id, match_sequence, event_id, home_team, away_team, minute, club_name,
                    player_id, card_type (yellow | second_yellow | direct) ; competition, journee,
                    score_context facultatifs (None par defaut).
    remplacement  : memes champs communs, club_name, player_on_id, player_off_id.
Aucune validation metier ici : le flux passe ensuite par validate_event / validate_event_stream.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, cast, get_args

from engine.event_contract import CartonDict, OutcomeCarton, RemplacementDict

_CARD_TYPES: tuple[str, ...] = get_args(OutcomeCarton)
_COMMUNS = ("match_id", "match_sequence", "event_id", "home_team", "away_team", "minute", "club_name")


def _exiger(brut: Mapping[str, Any], cles: tuple[str, ...], nature: str) -> None:
    manquantes = [cle for cle in cles if cle not in brut]
    if manquantes:
        raise ValueError(f"{nature} : cles manquantes {manquantes}.")


def _commun(brut: Mapping[str, Any], nature: str) -> dict[str, Any]:
    """Champs communs du contrat ; `is_home` se deduit de `club_name` (le club de l'acteur)."""
    club = brut["club_name"]
    if club not in (brut["home_team"], brut["away_team"]):
        raise ValueError(f"{nature} : club_name={club!r} n'est ni home_team ni away_team.")
    return {
        "match_id": brut["match_id"],
        "match_sequence": brut["match_sequence"],
        "event_id": brut["event_id"],
        "minute": brut["minute"],
        "player_team": club,
        "home_team": brut["home_team"],
        "away_team": brut["away_team"],
        "is_home": club == brut["home_team"],
        "competition": brut.get("competition"),
        "journee": brut.get("journee"),
        "score_context": brut.get("score_context"),
    }


def card_to_event(card: Mapping[str, Any]) -> CartonDict:
    """Carton brut -> `CartonDict` : `card_type` devient `outcome` (yellow / second_yellow / direct),
    `player_id` reste l'acteur (le sanctionne). ValueError si une cle manque, si `card_type` est
    inconnu ou si `club_name` n'est pas l'un des deux clubs."""
    _exiger(card, (*_COMMUNS, "player_id", "card_type"), "Carton")
    if card["card_type"] not in _CARD_TYPES:
        raise ValueError(f"Carton : card_type={card['card_type']!r} inconnu (attendu : {list(_CARD_TYPES)}).")
    evenement = {
        **_commun(card, "Carton"),
        "event_type": "carton",
        "outcome": card["card_type"],
        "player_id": card["player_id"],
    }
    return cast(CartonDict, evenement)


def substitution_to_event(sub: Mapping[str, Any]) -> RemplacementDict:
    """Remplacement brut -> `RemplacementDict` : `player_on_id` devient `entrant_id` ET `player_id`
    (l'acteur d'un remplacement est l'entrant), `player_off_id` devient `sortant_id`. ValueError si une
    cle manque ou si `club_name` n'est pas l'un des deux clubs."""
    _exiger(sub, (*_COMMUNS, "player_on_id", "player_off_id"), "Remplacement")
    evenement = {
        **_commun(sub, "Remplacement"),
        "event_type": "remplacement",
        "player_id": sub["player_on_id"],
        "entrant_id": sub["player_on_id"],
        "sortant_id": sub["player_off_id"],
    }
    return cast(RemplacementDict, evenement)

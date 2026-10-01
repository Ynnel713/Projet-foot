"""Ingestion NLG cote racine : `Timeline` (engine/narrative.py) -> liste de dicts d'evenements, au
contrat de `simulafoot_nlg/engine/event_contract.py` (voir simulafoot_nlg/SPEC_NLG_INGESTION.md).

Deux projets, aucun import croise : le NLG ne lit jamais ce module ni les types de la racine ; il
recoit des dicts (puis du JSON Lines, voir `write_jsonl`). Les formes sont donc REPLIQUEES ici, pas
importees.

Un dict par evenement commentable : buts et occasions (`NarrativeEvent`), cartons (`CardEvent`),
remplacements (`SubstitutionEvent`). Tri par minute (a minute egale : buts/occasions, puis cartons,
puis remplacements, puis ordre d'origine) ; `event_id` = rang dans ce tri, calcule AVANT tout rejet :
un evenement ecarte ne decale jamais l'`event_id` (donc la graine de rendu) des suivants -- unique et
stable, avec d'eventuels trous.

`match_sequence` est fourni par l'appelant (seul a connaitre l'ordre des matchs) ; `match_id` est celui
de la `Timeline` sauf surcharge. Un evenement qu'on ne sait pas convertir (joueur introuvable...) est
ECARTE, jamais devine : il est signale dans `skipped` si l'appelant le demande.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from ligue1sim.events import CardEvent, SubstitutionEvent
from ligue1sim.players import Player

from narrative import BUT, NarrativeEvent, Timeline

# Rang de tri a minute egale : ce qui se joue (but, occasion) avant la sanction, avant le changement.
_RANG_NARRATIF, _RANG_CARTON, _RANG_REMPLACEMENT = 0, 1, 2

_CARTON_OUTCOMES = {"yellow", "second_yellow", "direct"}


class EvenementEcarte(ValueError):
    """Un evenement du moteur ne peut pas devenir un dict du contrat ; le message dit pourquoi."""


def _resolve_id(name: str, squad: Sequence[Player]) -> int:
    for player in squad:
        if player.name == name and player.id is not None:
            return player.id
    raise EvenementEcarte(f"joueur {name!r} introuvable dans l'effectif")


def _commun(timeline: Timeline, match_id: str, match_sequence: int, event_id: int, minute: int, club: str,
            competition: str | None, journee: int | None) -> dict[str, Any]:
    return {
        "match_id": match_id,
        "match_sequence": match_sequence,
        "event_id": event_id,
        "minute": minute,
        "player_team": club,
        "home_team": timeline.home_team,
        "away_team": timeline.away_team,
        "is_home": club == timeline.home_team,
        "competition": competition,
        "journee": journee,
        "score_context": None,
    }


def _narratif_to_dict(event: NarrativeEvent, commun: dict[str, Any], squad: Sequence[Player]) -> dict[str, Any]:
    if event.event_type == BUT:
        dico = {**commun, "event_type": "but", "gabarit": event.gabarit, "player_id": _resolve_id(event.main_player, squad)}
        if len(event.involved_players) > 1:
            dico["passeur_id"] = _resolve_id(event.involved_players[1], squad)
        return dico
    if event.outcome in {"hors_cadre", "poteau", "barre"}:  # le tireur est l'acteur
        return {**commun, "event_type": "occasion", "gabarit": event.gabarit, "outcome": event.outcome,
                "player_id": _resolve_id(event.main_player, squad)}
    raise EvenementEcarte(f"occasion {event.outcome!r} : acteur defensif non resolu")


def _carton_to_dict(event: CardEvent, commun: dict[str, Any], squad: Sequence[Player]) -> dict[str, Any]:
    if event.card_type not in _CARTON_OUTCOMES:
        raise EvenementEcarte(f"type de carton inconnu : {event.card_type!r}")
    return {**commun, "event_type": "carton", "outcome": event.card_type, "player_id": _resolve_id(event.player, squad)}


def _remplacement_to_dict(event: SubstitutionEvent, commun: dict[str, Any], squad: Sequence[Player]) -> dict[str, Any]:
    entrant = _resolve_id(event.player_on, squad)
    return {**commun, "event_type": "remplacement", "player_id": entrant, "entrant_id": entrant,
            "sortant_id": _resolve_id(event.player_off, squad)}


def timeline_to_events(
    timeline: Timeline,
    *,
    match_sequence: int,
    home_squad: Sequence[Player],
    away_squad: Sequence[Player],
    competition: str | None = None,
    journee: int | None = None,
    match_id: str | None = None,
    skipped: list[tuple[int, str]] | None = None,
) -> list[dict[str, Any]]:
    """Dicts du contrat NLG pour un match, tries par minute, `event_id` = rang.

    `home_squad`/`away_squad` : effectifs complets (`Club.players`) -- les ids viennent de `Player.id`.
    `skipped` (optionnel) recoit `(event_id, raison)` pour chaque evenement ecarte."""
    match_id = match_id or timeline.match_id
    squads = {timeline.home_team: home_squad, timeline.away_team: away_squad}

    # (minute, rang, ordre d'origine, club, evenement du moteur, convertisseur)
    candidats: list[tuple[int, int, int, str, Any, Any]] = []
    for i, event in enumerate(timeline.events):
        candidats.append((event.minute, _RANG_NARRATIF, i, event.team, event, _narratif_to_dict))
    for i, event in enumerate(timeline.cards):
        candidats.append((event.minute, _RANG_CARTON, i, event.club_name, event, _carton_to_dict))
    for i, event in enumerate(timeline.substitutions):
        candidats.append((event.minute, _RANG_REMPLACEMENT, i, event.club_name, event, _remplacement_to_dict))
    candidats.sort(key=lambda c: c[:3])

    dicts: list[dict[str, Any]] = []
    for event_id, (minute, _rang, _ordre, club, event, convertir) in enumerate(candidats):
        commun = _commun(timeline, match_id, match_sequence, event_id, minute, club, competition, journee)
        try:
            dicts.append(convertir(event, commun, squads[club]))
        except EvenementEcarte as exc:
            if skipped is not None:
                skipped.append((event_id, str(exc)))
    return dicts

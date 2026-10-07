"""Sérialisation JSON d'un `Match` (score + `MatchEvents` complets + compos).

Format `format_version` 1 :
    {"format_version": 1, "home", "away", "home_goals", "away_goals",
     "events": <MatchEvents encodé par dataclass_codec> | null}

Lecture tolérante (voir `dataclass_codec`) : un document dont `events` n'a
pas les clés `home_lineup_snapshot`/`away_lineup_snapshot` (écrit avant leur
ajout) se relit sans erreur, avec snapshots à `None` -- le consommateur
passe alors par `lineup_snapshot.persisted_lineups` (None) ou
`require_persisted_lineups` (LineupNotPersistedError). Rien n'est recalculé.
"""

from __future__ import annotations

import json
from typing import Any

from ligue1sim import dataclass_codec
from ligue1sim.events import MatchEvents
from ligue1sim.schedule import Match

FORMAT_VERSION = 1


def match_to_dict(match: Match) -> dict[str, Any]:
    return {
        "format_version": FORMAT_VERSION,
        "home": match.home,
        "away": match.away,
        "home_goals": match.home_goals,
        "away_goals": match.away_goals,
        "events": None if match.events is None else dataclass_codec.encode(match.events),
    }


def match_from_dict(data: dict[str, Any]) -> Match:
    version = data.get("format_version", FORMAT_VERSION)
    if version > FORMAT_VERSION:
        raise ValueError(f"format_version {version} plus récent que {FORMAT_VERSION} : mise à jour du code requise")
    events = data.get("events")
    return Match(
        home=data["home"],
        away=data["away"],
        home_goals=data.get("home_goals"),
        away_goals=data.get("away_goals"),
        events=None if events is None else dataclass_codec.decode(MatchEvents, events),
    )


def match_to_json(match: Match) -> str:
    return json.dumps(match_to_dict(match), ensure_ascii=False, allow_nan=False)


def match_from_json(text: str) -> Match:
    return match_from_dict(json.loads(text))

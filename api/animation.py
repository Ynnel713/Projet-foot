"""Payload d'animation d'un match pour l'iframe `render/canvas.html` (section
2.11 de docs/canvas_integration_state.md, protocole `version` 1).

Source UNIQUE de la composition : le `LineupSnapshot` persisté dans
`Match.events` (voir `ligue1sim.lineup_snapshot`). Aucun appel à
`pick_best_formation`, aucune reconstruction depuis `PlayerMatchStat` : si le
match n'a pas de compo persistée, on répond `available=False` plutôt qu'un
payload partiel (comportement de la section 2.10).

Le calcul des clips (`engine.narrative` / `engine.narrative_player`) reste
côté Python : c'est le moteur de rendu, inchangé -- la PWA ne fait que
transporter le résultat jusqu'à l'iframe.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

# Convention du dépôt (apps/streamlit_preview.py, scripts/render_*.py, pytest
# `pythonpath`) : `engine/` est mis sur le chemin et ses modules s'importent
# en top-level (`narrative`, `narrative_player`, qui fait `from narrative
# import ...`). Importer `engine.narrative` ici créerait un 2e exemplaire du
# module (classes `Timeline`/`NarrativeEvent` dupliquées).
_ENGINE_DIR = str(Path(__file__).resolve().parent.parent / "engine")
if _ENGINE_DIR not in sys.path:
    sys.path.insert(0, _ENGINE_DIR)

from narrative import build_timeline, match_result_from  # noqa: E402
from narrative_player import build_clips, clips_to_json  # noqa: E402

from ligue1sim.lineup_snapshot import persisted_lineups
from ligue1sim.schedule import Match

PROTOCOL_VERSION = 1

REASON_LINEUP_NOT_PERSISTED = "lineup_not_persisted"
REASON_NO_HIGHLIGHTS = "no_highlights"
REASON_NOT_PLAYED = "not_played"


def unavailable(reason: str) -> dict[str, Any]:
    return {"version": PROTOCOL_VERSION, "available": False, "reason": reason}


def build_match_animation(match: Match, label: str = "") -> dict[str, Any]:
    """`{"version", "available": True, "match": {...}, "clips": [...]}` ou
    `{"version", "available": False, "reason": ...}`.

    `label` : suffixe stable du match (journée, poule, tour) -- passé comme
    `date` à `match_result_from`, qui s'en sert pour varier la graine des
    occasions d'un match à l'autre (même convention que le fil NLG)."""
    if not match.played or match.events is None:
        return unavailable(REASON_NOT_PLAYED)
    lineups = persisted_lineups(match)
    if lineups is None:
        return unavailable(REASON_LINEUP_NOT_PERSISTED)
    home_lineup, away_lineup = lineups

    result = match_result_from(match, match.events, home_lineup, away_lineup, date=label)
    timeline = build_timeline(result)
    clips = build_clips(timeline, max_occasions=None)
    if not clips:
        return unavailable(REASON_NO_HIGHLIGHTS)

    return {
        "version": PROTOCOL_VERSION,
        "available": True,
        "match": {
            "home": match.home,
            "away": match.away,
            "home_goals": match.home_goals,
            "away_goals": match.away_goals,
        },
        "clips": json.loads(clips_to_json(clips, timeline)),
    }

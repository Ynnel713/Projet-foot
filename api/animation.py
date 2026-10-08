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

import hashlib
import json
import sys
from collections import OrderedDict
from pathlib import Path
from threading import Lock
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


def _compact(obj: Any) -> str:
    return json.dumps(obj, separators=(",", ":"))


def _animation_json(match: Match, label: str) -> tuple[bytes, bool]:
    """(JSON UTF-8 du payload, `available`). Calcul complet, sans cache.

    Le JSON des clips est inséré tel quel dans l'enveloppe (aucun
    `json.loads` puis ré-`dumps` de ~14 Mo, voir docs/ticket4_latency_audit.md)."""
    if not match.played or match.events is None:
        return _compact(unavailable(REASON_NOT_PLAYED)).encode(), False
    lineups = persisted_lineups(match)
    if lineups is None:
        return _compact(unavailable(REASON_LINEUP_NOT_PERSISTED)).encode(), False
    home_lineup, away_lineup = lineups

    result = match_result_from(match, match.events, home_lineup, away_lineup, date=label)
    timeline = build_timeline(result)
    clips = build_clips(timeline, max_occasions=None)
    if not clips:
        return _compact(unavailable(REASON_NO_HIGHLIGHTS)).encode(), False

    head = {
        "version": PROTOCOL_VERSION,
        "available": True,
        "match": {
            "home": match.home,
            "away": match.away,
            "home_goals": match.home_goals,
            "away_goals": match.away_goals,
        },
    }
    text = f'{_compact(head)[:-1]},"clips":{clips_to_json(clips, timeline)}}}'
    return text.encode(), True


def build_match_animation(match: Match, label: str = "") -> dict[str, Any]:
    """`{"version", "available": True, "match": {...}, "clips": [...]}` ou
    `{"version", "available": False, "reason": ...}`. Toujours recalculé
    (jamais le cache) : c'est la référence que les tests comparent.

    `label` : suffixe stable du match (journée, poule, tour) -- passé comme
    `date` à `match_result_from`, qui s'en sert pour varier la graine des
    occasions d'un match à l'autre (même convention que le fil NLG)."""
    return json.loads(_animation_json(match, label)[0])


# --- Cache mémoire (ticket 4, optimisation 3) ---------------------------------
# LRU simple, sans expiration, perdu au redémarrage du serveur. On garde le JSON
# DÉCOMPRESSÉ (octets) : ~11 Mo par match après arrondi, soit ~55 Mo pour 5
# entrées. Choix assumé plutôt que de garder le gzip (~0,5 Mo par entrée) : le
# même octet-string sert tous les clients (avec ou sans `Accept-Encoding: gzip`)
# et le cache ne dépend pas du middleware ; la compression (une passe sur 11 Mo)
# est refaite par `GZipMiddleware` à chaque réponse.
CACHE_MAX_ENTRIES = 5
_cache: OrderedDict[tuple, bytes] = OrderedDict()
_cache_lock = Lock()


def _cache_key(match: Match, label: str) -> tuple:
    """Identifiant du match (équipes, libellé) + empreinte de ses `MatchEvents`,
    qui contiennent les `LineupSnapshot` persistés (les deux compos) : une compo
    ou un événement différent donne une autre clé, donc un recalcul."""
    digest = hashlib.sha256(repr(match.events).encode()).hexdigest()
    return (match.home, match.away, label, match.home_goals, match.away_goals, digest)


def build_match_animation_json(match: Match, label: str = "") -> bytes:
    """Comme `build_match_animation`, mais en JSON (octets) et avec cache LRU.
    Seuls les payloads `available=True` sont mis en cache (les autres sont
    instantanés)."""
    if not match.played or match.events is None:
        return _animation_json(match, label)[0]
    key = _cache_key(match, label)
    with _cache_lock:
        cached = _cache.get(key)
        if cached is not None:
            _cache.move_to_end(key)
            return cached
    payload, available = _animation_json(match, label)
    if available:
        with _cache_lock:
            _cache[key] = payload
            _cache.move_to_end(key)
            while len(_cache) > CACHE_MAX_ENTRIES:
                _cache.popitem(last=False)
    return payload


def clear_cache() -> None:
    with _cache_lock:
        _cache.clear()

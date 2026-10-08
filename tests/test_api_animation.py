"""Payload d'animation pour l'iframe canvas (api/animation.py + route
`/animation`, protocole version 1, docs/canvas_integration_state.md §2.11).
Appelle les fonctions de vue directement (pas de TestClient, voir
tests/test_competitions.py)."""

import dataclasses
import json
import time

import pytest
from fastapi import HTTPException

from ligue1sim import lineup as lineup_module
from ligue1sim import simulation
from ligue1sim.clubs import load_clubs
from ligue1sim.custom_competition import CustomCompetition
from ligue1sim.season import CLUBS_PATH

from api import animation as animation_module
from api import store
from api.animation import (
    PROTOCOL_VERSION,
    REASON_LINEUP_NOT_PERSISTED,
    REASON_NOT_PLAYED,
    build_match_animation,
    build_match_animation_json,
)
from api.routers.competitions import get_match_animation, simulate_current


@pytest.fixture
def played_competition():
    clubs = load_clubs(CLUBS_PATH, "Ligue 1")
    competition = CustomCompetition(format="LEAGUE", legs=2, clubs=clubs, label="Ligue 1")
    comp_id = store.create(competition)
    simulate_current(comp_id)
    return comp_id, competition, clubs


def _first_animable(competition):
    for match in competition.season.calendar[0].matches:
        out = build_match_animation(match, "j1")
        if out["available"]:
            return match, out
    pytest.skip("aucun match de la journée 1 n'a de temps forts animables avec cette simulation")


def test_animation_payload_shape_and_json_roundtrip(played_competition):
    _, competition, _ = played_competition
    match, out = _first_animable(competition)

    assert out["version"] == PROTOCOL_VERSION == 1
    assert out["match"] == {
        "home": match.home, "away": match.away, "home_goals": match.home_goals, "away_goals": match.away_goals
    }
    clips = out["clips"]
    assert clips and all({"duration", "frames", "metadata"} <= set(c) for c in clips)
    assert {"minute", "score_after", "home_team", "away_team", "teams", "interval_events"} <= set(clips[0]["metadata"])
    assert json.loads(json.dumps(out)) == out  # JSON pur, sans perte


def test_animation_uses_only_the_persisted_lineup_even_if_squads_change(played_competition, monkeypatch):
    comp_id, competition, clubs = played_competition
    match, before = _first_animable(competition)

    def forbidden(*_a, **_k):
        raise AssertionError("pick_best_formation appelé pendant la construction du payload")

    monkeypatch.setattr(lineup_module, "pick_best_formation", forbidden)
    monkeypatch.setattr(simulation, "pick_best_formation", forbidden)
    for club in clubs:  # l'effectif change entre-temps
        club.players[:] = [dataclasses.replace(p, note=1.0) for p in club.players[:15]]

    assert build_match_animation(match, "j1") == before  # identique, au bit près
    via_route = get_match_animation(comp_id, match.home, match.away, journee=1)
    assert json.loads(via_route.body) == before


def test_match_without_persisted_lineup_is_unavailable_not_partial(played_competition, monkeypatch):
    _, competition, _ = played_competition
    match, _ = _first_animable(competition)
    legacy_events = dataclasses.replace(match.events, home_lineup_snapshot=None, away_lineup_snapshot=None)
    legacy = dataclasses.replace(match, events=legacy_events)

    def forbidden(*_a, **_k):
        raise AssertionError("recalcul de composition interdit")

    monkeypatch.setattr(lineup_module, "pick_best_formation", forbidden)
    monkeypatch.setattr(simulation, "pick_best_formation", forbidden)

    assert build_match_animation(legacy, "j1") == {
        "version": 1, "available": False, "reason": REASON_LINEUP_NOT_PERSISTED
    }


def test_one_sided_snapshot_is_also_unavailable(played_competition):
    _, competition, _ = played_competition
    match, _ = _first_animable(competition)
    half = dataclasses.replace(match, events=dataclasses.replace(match.events, away_lineup_snapshot=None))
    assert build_match_animation(half)["reason"] == REASON_LINEUP_NOT_PERSISTED


def test_unplayed_match_is_unavailable(played_competition):
    _, competition, _ = played_competition
    upcoming = competition.season.calendar[1].matches[0]
    assert build_match_animation(upcoming) == {"version": 1, "available": False, "reason": REASON_NOT_PLAYED}


def test_route_serves_cached_identical_payload_and_second_call_is_fast(played_competition):
    comp_id, competition, _ = played_competition
    match, reference = _first_animable(competition)
    animation_module.clear_cache()

    started = time.perf_counter()
    first = get_match_animation(comp_id, match.home, match.away, journee=1)
    first_seconds = time.perf_counter() - started
    started = time.perf_counter()
    second = get_match_animation(comp_id, match.home, match.away, journee=1)
    second_seconds = time.perf_counter() - started

    assert first.body == second.body  # même payload, octet pour octet
    assert first.media_type == "application/json"
    assert json.loads(first.body) == reference  # le cache ne change pas le contenu
    assert second_seconds < 1.0
    assert second_seconds < first_seconds
    assert len(animation_module._cache) == 1


def test_cache_key_follows_lineup_snapshot_and_is_lru_bounded(played_competition, monkeypatch):
    _, competition, _ = played_competition
    match, _ = _first_animable(competition)
    animation_module.clear_cache()
    calls = []
    real = animation_module._animation_json
    monkeypatch.setattr(animation_module, "_animation_json", lambda m, label: calls.append(label) or real(m, label))

    build_match_animation_json(match, "j1")
    build_match_animation_json(match, "j1")
    assert calls == ["j1"]  # 2e appel servi par le cache

    # Une compo persistée différente invalide l'entrée (clé = empreinte des MatchEvents).
    home_snapshot = match.events.home_lineup_snapshot
    other_lineup = dataclasses.replace(home_snapshot.lineup, club_name=home_snapshot.lineup.club_name + " bis")
    other_snapshot = dataclasses.replace(home_snapshot, lineup=other_lineup)
    changed = dataclasses.replace(match, events=dataclasses.replace(match.events, home_lineup_snapshot=other_snapshot))
    assert animation_module._cache_key(changed, "j1") != animation_module._cache_key(match, "j1")

    # Au plus CACHE_MAX_ENTRIES entrées, la plus ancienne est évincée.
    animation_module.clear_cache()
    monkeypatch.setattr(animation_module, "_animation_json", lambda m, label: (b'{"available":true}', True))
    for index in range(animation_module.CACHE_MAX_ENTRIES + 2):
        build_match_animation_json(match, f"l{index}")
    assert len(animation_module._cache) == animation_module.CACHE_MAX_ENTRIES
    assert [key[2] for key in animation_module._cache] == [f"l{i}" for i in range(2, animation_module.CACHE_MAX_ENTRIES + 2)]


def test_unavailable_payloads_are_not_cached(played_competition):
    _, competition, _ = played_competition
    animation_module.clear_cache()
    upcoming = competition.season.calendar[1].matches[0]
    assert json.loads(build_match_animation_json(upcoming, "j2")) == {
        "version": 1, "available": False, "reason": REASON_NOT_PLAYED
    }
    assert not animation_module._cache


def test_animation_coordinates_are_rounded_to_four_decimals(played_competition):
    _, competition, _ = played_competition
    _, out = _first_animable(competition)
    for clip in out["clips"]:
        for frame in clip["frames"]:
            for player in frame["players"]:
                assert player["x"] == round(player["x"], 4) and player["y"] == round(player["y"], 4)
            ball = frame["ball"]
            assert all(ball[k] == round(ball[k], 4) for k in ("x", "y", "z", "spin"))


def _asgi_get(app, path: str) -> dict[str, str]:
    """Appel ASGI minimal (pas de TestClient : httpx absent, voir l'en-tête du
    module) avec `Accept-Encoding: gzip` ; renvoie les en-têtes de la réponse."""
    import asyncio

    headers: dict[str, str] = {}

    async def run() -> None:
        scope = {
            "type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1", "method": "GET", "scheme": "http",
            "path": path, "raw_path": path.encode(), "query_string": b"", "root_path": "",
            "headers": [(b"accept-encoding", b"gzip"), (b"host", b"test")],
            "client": ("127.0.0.1", 1), "server": ("test", 80),
        }

        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}

        async def send(message):
            if message["type"] == "http.response.start":
                headers.update({k.decode().lower(): v.decode() for k, v in message["headers"]})

        await app(scope, receive, send)

    asyncio.run(run())
    return headers


def test_app_gzips_large_responses_only():
    from fastapi.middleware.gzip import GZipMiddleware

    from api.main import app

    gzip_layers = [m for m in app.user_middleware if m.cls is GZipMiddleware]
    assert len(gzip_layers) == 1 and gzip_layers[0].kwargs["minimum_size"] == 1000
    assert _asgi_get(app, "/api/health").get("content-encoding") != "gzip"  # réponse < 1 000 octets
    assert _asgi_get(app, "/render/canvas.html").get("content-encoding") == "gzip"  # fichier > 1 000 octets


def test_route_404_for_unknown_match_and_422_without_locator(played_competition):
    comp_id, *_ = played_competition
    with pytest.raises(HTTPException) as unknown:
        get_match_animation(comp_id, "Nope FC", "Nada FC", journee=1)
    assert unknown.value.status_code == 404
    with pytest.raises(HTTPException) as bad:
        get_match_animation(comp_id, "A", "B")
    assert bad.value.status_code == 422

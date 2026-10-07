"""Payload d'animation pour l'iframe canvas (api/animation.py + route
`/animation`, protocole version 1, docs/canvas_integration_state.md §2.11).
Appelle les fonctions de vue directement (pas de TestClient, voir
tests/test_competitions.py)."""

import dataclasses
import json

import pytest
from fastapi import HTTPException

from ligue1sim import lineup as lineup_module
from ligue1sim import simulation
from ligue1sim.clubs import load_clubs
from ligue1sim.custom_competition import CustomCompetition
from ligue1sim.season import CLUBS_PATH

from api import store
from api.animation import (
    PROTOCOL_VERSION,
    REASON_LINEUP_NOT_PERSISTED,
    REASON_NOT_PLAYED,
    build_match_animation,
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
    assert via_route == before


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


def test_route_404_for_unknown_match_and_422_without_locator(played_competition):
    comp_id, *_ = played_competition
    with pytest.raises(HTTPException) as unknown:
        get_match_animation(comp_id, "Nope FC", "Nada FC", journee=1)
    assert unknown.value.status_code == 404
    with pytest.raises(HTTPException) as bad:
        get_match_animation(comp_id, "A", "B")
    assert bad.value.status_code == 422

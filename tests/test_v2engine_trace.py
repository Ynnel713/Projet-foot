"""Tests du lot rendu V2 (US-29, docs/PLAN_V2.md Phase 4) : buts horodatés dans la trace et route
API `/api/v2/matches`."""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from api.routers.v2 import SimulateV2Request, create_match
from v2engine.trace import GoalEvent, MatchTrace


def test_record_goal_keeps_score_and_minute_of_each_goal() -> None:
    trace = MatchTrace(home="A", away="B", tick_seconds=1.0)
    trace.record_goal("home", 12.5)
    trace.record_goal("away", 80.0)
    assert (trace.home_goals, trace.away_goals) == (1, 1)
    assert trace.goals == [GoalEvent(minute=12.5, team="home"), GoalEvent(minute=80.0, team="away")]


def test_v2_match_route_rejects_unknown_club() -> None:
    with pytest.raises(HTTPException) as error:
        create_match(SimulateV2Request(home="Club inexistant", away="Autre inexistant"))
    assert error.value.status_code == 404

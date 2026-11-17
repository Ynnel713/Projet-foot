"""Le tacleur le mieux placé tente (ticket v2-realisme/11p) : parmi les défenseurs à portée, seul celui au meilleur angle
d'approche (0° = de face) tente ; deux angles à moins de 10° l'un de l'autre : le plus proche l'emporte. Un seul tirage
par pas : deux défenseurs ne taclent jamais ensemble."""

from __future__ import annotations

import math
from dataclasses import replace

import pytest

from scenes import player
from scripts import bench_series as bs
from v2engine import match
from v2engine.ball_state import BallState
from v2engine.duel import TACKLER_ANGLE_TIE_DEG, TackleResult, best_placed_tackler, tackle_approach_angle_deg
from v2engine.geometry import Vec2
from v2engine.match import TACKLE_RADIUS_M, _step_ball


def _holder():
    return replace(player("Porteur", "home", 70.0, 34.0, "BU"), facing=Vec2(1.0, 0.0))  # face au but adverse (x = 105)


def _def(name: str, x: float, y: float = 34.0):
    return player(name, "away", x, y, "DC", Decisions=55, Aggression=60)


def test_the_tie_tolerance_is_the_validated_constant() -> None:
    assert TACKLER_ANGLE_TIE_DEG == 10.0


def test_the_front_defender_tackles_despite_a_closer_one_behind() -> None:
    holder, behind, front = _holder(), _def("Dos", 69.5), _def("Face", 71.2)  # 0,5 m dans le dos, 1,2 m de face
    assert best_placed_tackler(holder, [holder, behind, front], TACKLE_RADIUS_M) is front
    # règle d'avant (neutralisation 11p) : le plus proche
    assert best_placed_tackler(holder, [holder, behind, front], TACKLE_RADIUS_M, math.inf) is behind


def test_within_the_tolerance_the_closest_wins() -> None:
    holder = _holder()
    far = _def("Loin", 71.4)  # 0°, 1,4 m
    near = _def("Près", 70.0 + 1.0 * math.cos(math.radians(8.0)), 34.0 + 1.0 * math.sin(math.radians(8.0)))  # 8°, 1 m
    wide = _def("Écarté", 70.0 + 1.0 * math.cos(math.radians(12.0)), 34.0 + 1.0 * math.sin(math.radians(12.0)))
    assert tackle_approach_angle_deg(near, holder) == pytest.approx(8.0)
    assert best_placed_tackler(holder, [far, near], TACKLE_RADIUS_M) is near
    assert best_placed_tackler(holder, [far, wide], TACKLE_RADIUS_M) is far  # 12° d'écart : le meilleur angle


def test_teammates_and_defenders_out_of_range_are_ignored() -> None:
    holder = _holder()
    mate = player("Coéquipier", "home", 71.0, 34.0, "MC")
    out = _def("Hors portée", 70.0 + TACKLE_RADIUS_M + 0.1)
    assert best_placed_tackler(holder, [holder, mate, out], TACKLE_RADIUS_M) is None
    assert best_placed_tackler(holder, [holder, mate, out, _def("Dos", 69.0)], TACKLE_RADIUS_M).name == "Dos"


def test_one_tackle_per_step_by_the_best_placed(monkeypatch) -> None:
    holder, behind, front = _holder(), _def("Dos", 69.5), _def("Face", 71.2)
    cover = player("Couverture", "away", 95.0, 34.0, "DC")  # hors urgence : le dos serait prudent (facteur 0,15)
    ball = BallState(position=holder.position, velocity=Vec2(0.0, 0.0), holder="Porteur")
    tacklers: list[str] = []
    monkeypatch.setattr("v2engine.match.should_attempt_tackle", lambda aggression, dt: True)
    monkeypatch.setattr("v2engine.match.resolve_tackle",
                        lambda tackler, h: tacklers.append(tackler.name) or TackleResult(won=False, foul=False))

    _step_ball(ball, 0.1, [holder, behind, front, cover])

    assert tacklers == ["Face"]


def test_the_bench_can_neutralise_11p() -> None:
    holder, behind, front = _holder(), _def("Dos", 69.5), _def("Face", 71.2)
    real = match.best_placed_tackler
    with bs.neutralised(["11p"]):
        assert match.best_placed_tackler(holder, [holder, behind, front], TACKLE_RADIUS_M) is behind
    assert match.best_placed_tackler is real
    assert bs.parse_neutralised("11h,11p") == ("11h", "11p")

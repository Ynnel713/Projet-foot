"""Validation de l'orientation (ticket v2-realisme/07g) : indicateurs de mesure seulement, sans effet sur le jeu.
Type de réception par poste, délai moyen de rotation avant l'action (rotations nulles comprises), course à reculons des
défenseurs, contrôles à l'aveugle d'un joueur dont le corps est tourné vers sa course (facultatif A1 de l'expert au 07d),
changements du choix course / ballon du cap et ceux défaits en moins de 0,5 s (facultatif A2 de l'expert au 07b)."""

from __future__ import annotations

from dataclasses import replace

import pytest

from scripts import v2_indicators as ind
from scripts.measure_v2 import report
from v2engine.ball_state import BallState
from v2engine.geometry import Vec2
from v2engine.match import _step_ball
from v2engine.reception import DE_FACE, DOS_AU_JEU
from v2engine.trace import DecisionRecord, ReceptionEvent
from tests.scenes import player


def _reception(name: str, poste: str, kind: str, blind: bool = False, facing_run: bool = False,
               first_time: bool = False) -> ReceptionEvent:
    return ReceptionEvent(minute=1.0, team="home", player=name, poste=poste, kind=kind, facing_goal_deg=0.0,
                          ball_facing_deg=0.0, origin="passe", intended=True, first_time=first_time, blind=blind,
                          facing_run=facing_run)


def test_the_trace_records_whether_the_receiver_faced_his_run(monkeypatch) -> None:
    monkeypatch.setattr("v2engine.match.attempt_control", lambda *args: True)
    monkeypatch.setattr("v2engine.match.orients_control", lambda *args: False)
    monkeypatch.setattr("v2engine.match.thinks_one_touch", lambda *args: False)
    for facing_run in (False, True):
        receiver = replace(player("R", x=50.0, y=34.0), facing=Vec2(1.0, 0.0), facing_run=facing_run)
        ball = BallState(position=Vec2(49.6, 34.0), velocity=Vec2(6.0, 0.0), receiver="R", released_by="P")
        receptions: list[ReceptionEvent] = []
        _step_ball(ball, 0.1, [receiver, player("P", x=10.0, y=10.0)], 10.0, receptions=receptions)
        assert ball.holder == "R"
        assert receptions[0].facing_run is facing_run
        assert receptions[0].blind  # ballon dans le dos, joueur arrêté : à l'aveugle, quel que soit son cap de course


def test_reception_kinds_per_poste_and_blind_controls_facing_the_run() -> None:
    c = ind.Collector()
    c.on_receptions([
        _reception("D", "DC", DOS_AU_JEU, blind=True, facing_run=True),
        _reception("D", "DC", DE_FACE),
        _reception("A", "BU", DOS_AU_JEU, blind=True),
        _reception("A", "BU", DOS_AU_JEU, first_time=True),  # pense à jouer de première : hors contrôles
    ])
    out = report(c)
    assert out["réceptions dos au jeu, DC (part des contrôles du poste)"] == pytest.approx(0.5)
    assert out["réceptions de face, DC (part des contrôles du poste)"] == pytest.approx(0.5)
    assert out["réceptions dos au jeu, BU (part des contrôles du poste)"] == pytest.approx(1.0)
    assert out["contrôles à l'aveugle, corps vers sa course (part des contrôles à l'aveugle)"] == pytest.approx(0.5)
    assert out["contrôles corps vers sa course (part des contrôles)"] == pytest.approx(1 / 3)


def test_mean_rotation_delay_counts_actions_without_rotation() -> None:
    c = ind.Collector()
    def decision(action: str, rotation_s: float = 0.0) -> DecisionRecord:
        return DecisionRecord(minute=1.0, player="P", team="home", action=action, target=None, considered=3, best=True,
                              rotation_s=rotation_s)

    c.on_decisions([decision("pass", 0.4), decision("pass"), decision("dribble", 0.9)])
    out = report(c)
    assert out["rotation : passes, délai moyen avant l'action (s)"] == pytest.approx(0.2)
    assert out["rotation : passes, durée moyenne quand il y en a une (s)"] == pytest.approx(0.4)


def test_defenders_backpedalling_time_speed_and_distance() -> None:
    c = ind.Collector()
    north = Vec2(0.0, 1.0)
    back = replace(player("D", poste="DC"), facing=north, velocity=Vec2(0.0, -3.0))  # à reculons, 3 m/s
    side = replace(player("L", poste="LB"), facing=north, velocity=Vec2(3.0, 0.0))  # de côté : pas à reculons
    slow = replace(player("R", poste="RB"), facing=north, velocity=Vec2(0.0, -0.5))  # piétine : hors mesure
    mid = replace(player("M", poste="MC"), facing=north, velocity=Vec2(0.0, -3.0))  # milieu : hors mesure
    for _ in range(10):
        c._speeds([back, side, slow, mid], 1.0, 0.1)
    out = report(c)
    assert out["défenseurs (DC, LB, RB) : temps à reculons (part du temps en mouvement)"] == pytest.approx(0.5)
    assert out["défenseurs (DC, LB, RB) : vitesse moyenne à reculons (m/s)"] == pytest.approx(3.0)
    assert out["défenseurs (DC, LB, RB) : vitesse maximale à reculons (m/s)"] == pytest.approx(3.0)
    # 3 m parcourus à reculons en 3 s de présence de défenseurs (3 joueurs x 1 s) : 3 / (3 / 5400) = 5 400 m par 90 min
    assert out["défenseurs (DC, LB, RB) : distance à reculons par joueur et par 90 min (m)"] == pytest.approx(5400.0)


def test_facing_choice_changes_and_quick_reversals() -> None:
    c = ind.Collector()
    states = [False, True, False, False, False, False, False, False, True, True]  # changements à 0,1 s, 0,2 s, 0,8 s
    for i, run in enumerate(states):
        c.now = 0.1 * i
        c._speeds([replace(player("P", poste="MC"), facing_run=run)], c.now / 60.0, 0.1)
    out = report(c)
    assert out["cap : changements course / ballon par joueur et par minute, MC"] == pytest.approx(3 / (1.0 / 60.0))
    # 0,2 s : défait 0,1 s après ; 0,8 s : 0,6 s après le précédent, pas « défait » ; 0,1 s : premier, pas défait
    assert out["cap : changements course / ballon défaits en moins de 0.5 s (part des changements), MC"] == pytest.approx(1 / 3)


def test_series_merge_keeps_the_maxima_of_all_matches() -> None:
    """`bench_series` fusionne les maxima (vitesse à reculons, erreur de mémoire) par le maximum : avant le ticket 07g,
    ils valaient 0 dans l'agrégé d'une série."""
    from scripts import bench_series as bs
    merged = ind.Collector()
    for value in (4.0, 6.0, 5.0):
        bs._merge_into(merged, {"count": {}, "stats": {}, "km": {},
                                "peak": {"défenseurs : vitesse maximale à reculons (m/s)": value}})
    assert merged.peak["défenseurs : vitesse maximale à reculons (m/s)"] == 6.0

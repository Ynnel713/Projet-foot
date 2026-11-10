"""Rapport de validation des tirs (ticket v2-realisme/05g) : `scripts.shot_calibration.validation_report` range des tirs
relevés en match par distance, angle, note, cône et vitesse, et suit la sortie des contres."""

from __future__ import annotations

import pytest

from scripts.shot_calibration import validation_report


def _shot(match: int, issue: str, distance: float = 10.0, angle: float = 30.0, note: int = 60, surface: bool = True,
          cone: int = 0, speed: float | None = None, after: str | None = None, corners: int = 4) -> dict:
    return {"match": match, "issue": issue, "distance": distance, "angle": angle, "note": note, "surface": surface,
            "dans le cône": cone, "vitesse au gardien": speed, "après le contre": after, "corners du match": corners,
            "contre prévu": 0.2, "hors contre": 0.3, "écart au gardien": 1.5 if speed is not None else None}


def test_the_report_splits_outcomes_on_target_blocks_saves_and_corners() -> None:
    shots = [_shot(0, "but", distance=6.0, speed=25.0), _shot(0, "capté", distance=6.0, speed=25.0),
             _shot(0, "à côté", distance=22.0, angle=10.0, surface=False, note=80),
             _shot(0, "contré", distance=22.0, angle=10.0, surface=False, cone=2, after="corner"),
             _shot(1, "contré", cone=1, after="en jeu", corners=6), _shot(1, "claqué", speed=21.0, corners=6),
             _shot(1, "dévissé", note=30, corners=6)]
    out = validation_report(shots)
    assert out["matchs"] == 2 and out["tirs par match"] == pytest.approx(3.5) and out["buts par match"] == 0.5
    near = out["issues par distance (m)"]["[0 ; 8["]
    assert near["tirs"] == 2 and near["but"] == 0.5 and near["capté"] == 0.5
    assert list(out["issues par distance (m)"]) == ["[0 ; 8[", "[8 ; 12[", "[20 ; 25["]  # dans l'ordre des distances
    # cadrage : contrés et dévissés à part ; 60 dans la surface : but, capté, claqué cadrés
    assert out["cadrage par note, Finishing (surface)"]["[55 ; 70["]["cadrés"] == 1.0
    assert out["cadrage par note, Long Shots (dehors)"]["[70 ; 100["]["cadrés"] == 0.0
    assert out["contres par défenseurs dans le cône"]["0"]["contrés"] == 0.0
    assert out["contres par défenseurs dans le cône"]["1"]["contrés"] == 1.0
    assert out["arrêts par vitesse au gardien"]["[24 ; 27[ m/s"]["arrêtés"] == 0.5
    assert out["contres : suite directe (part)"] == {"corner": 0.5, "touche": 0.0, "sortie de but": 0.0, "en jeu": 0.5}
    assert out["corners par match"] == 5.0  # (4 + 6) / 2, compté une fois par match
    assert out["corners par match : après un contre"] == 0.5 and out["corners par match : après un tir claqué"] == 0.5


def test_on_target_rate_rises_with_the_shooting_note_at_a_fixed_spot() -> None:
    # scène de référence du 05g : en match, l'effet de la note sur le cadrage se perd dans le mélange des situations
    # (environ 3 points prévus entre tranches voisines sur 50 matchs) ; à position fixe, il est net (mesuré : 40 %, 56 %,
    # 69 % à 14 m pour 25, 60 et 95)
    from scripts.shot_calibration import on_target_scene, wilson

    rates = [on_target_scene(14.0, 0.0, 1500, 8, note) for note in (25, 60, 95)]
    bounds = [wilson(round(r * 1500), 1500) for r in rates]
    assert bounds[0][1] < bounds[1][0] and bounds[1][1] < bounds[2][0]

"""Indicateurs du jeu aérien (ticket v2-realisme/15a) : désignés sur ballon aérien, partie du corps des contrôles et du
premier contrôle après un centre (réserve A1 du ticket v2-attributs-restants/01). Le banc observe sans changer le jeu."""

from __future__ import annotations

from types import SimpleNamespace

import scripts.v2_indicators as ind
from v2engine.trace import AerialRecord


def _reception(minute: float, part: str) -> SimpleNamespace:
    return SimpleNamespace(minute=minute, body_part=part)


def test_body_part_of_controls_and_of_the_first_control_after_a_cross() -> None:
    c = ind.Collector(geometry_every_s=1e9)
    c.pass_log = [{"t": 10.0, "cross": True}, {"t": 20.0, "cross": False}, {"t": 30.0, "cross": True}]
    # centre à 10 s : tête à 11 s puis pied à 12 s (seul le premier compte) ; centre à 30 s : rien avant la fin
    c._body_parts([_reception(11.0 / 60, "tête"), _reception(12.0 / 60, "pied"), _reception(21.0 / 60, "corps")])
    assert c.count["contrôles par partie du corps : tête"] == 1
    assert c.count["contrôles par partie du corps : pied"] == 1
    assert c.count["contrôles par partie du corps : corps"] == 1
    assert c.count["premier contrôle après un centre : tête"] == 1
    assert c.count["premier contrôle après un centre : pied"] == 0


def test_aerial_designations_pairs_on_time_and_quick_changes() -> None:
    c = ind.Collector(geometry_every_s=1e9)
    c.on_aerial([
        AerialRecord(1.0, "home", ("a", "b"), ((0, 0), (1, 1)), (2.0, 2.1), (True, True)),
        AerialRecord(1.005, "home", ("b", "a"), ((0, 0), (1, 1)), (2.0, 2.1), (True, False)),  # 0,3 s après
        AerialRecord(1.05, "home", (), (), (), ()),
        AerialRecord(2.0, "away", ("x",), ((0, 0),), (3.0,), (False,)),
    ])
    assert c.count["ballon aérien : désignations"] == 3
    assert c.count["ballon aérien : deux désignés"] == 2
    assert c.count["ballon aérien : premier à temps"] == 2
    assert c.count["ballon aérien : changements rapides"] == 1
    assert c.count["ballon aérien : changements rapides du premier"] == 1

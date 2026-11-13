"""Le défenseur ne voit pas toujours l'appel dans son dos (ticket v2-realisme/08e) : le marqueur situe l'attaquant là où il le
perçoit, la ligne se cale sur l'attaquant que son défenseur le plus bas perçoit comme le plus avancé ; un défenseur qui
scanne ne suit plus le ballon le temps du scan (ticket v2-realisme/08c, réserve A1)."""

from __future__ import annotations

from dataclasses import replace

import pytest

import v2engine.flux as flux
from v2engine.ball_state import BallState
from v2engine.bloc import Bloc
from v2engine.cerveau import Intention, think
from v2engine.decision import anticipation_share
from v2engine.defense import MARQUAGE, DefensiveRoles, marking_distance_m
from v2engine.geometry import Vec2
from v2engine.perception_memory import PerceptionMemory
from v2engine.scan import ScanTracker
from tests.scenes import player


def _scene(markers: dict[str, tuple[float, float, float]]):
    """Attaquant A (équipe away) qui a couru dans le dos des marqueurs : vu à (30, 34) à 6 m/s vers son but, 2 s plus tard il
    est en (12, 34) ; chaque marqueur est donné par (x, y, cap vers l'est = 1 ou vers l'ouest = -1)."""
    striker = replace(player("A", "away", x=30.0, y=34.0, poste="BU"), velocity=Vec2(-6.0, 0.0))
    holder = player("H", "away", x=40.0, y=10.0, poste="MC")
    team = [replace(player(name, "home", x=x, y=y, poste="DC", Anticipation=11), facing=Vec2(face, 0.0))
            for name, (x, y, face) in markers.items()]
    team += [player("P", "home", x=38.0, y=10.0, poste="DC"), player("C", "home", x=33.0, y=14.0, poste="DC")]  # presseur et couverture
    start = [striker, holder, *team]
    memory = PerceptionMemory(start, 0.0)
    memory.update(start, 0.0)
    moved = [replace(striker, position=Vec2(12.0, 34.0)), holder, *team]
    memory.update(moved, 2.0)
    ball = BallState(position=holder.position, velocity=Vec2(0.0, 0.0), holder="H")
    return moved, ball, memory


def _marking(players, ball, memory):
    defense = DefensiveRoles()
    defense.update(players, ball, None, 2.0, memory=memory)
    return {name: a for name, a in defense.assignments.items() if a.role == MARQUAGE}


def test_a_marker_who_sees_the_attacker_marks_him_where_he_is() -> None:
    players, ball, memory = _scene({"M": (16.0, 34.0, -1.0)})  # il regarde vers son but : l'attaquant est devant lui
    assert _marking(players, ball, memory)["M"].target == _marking(players, ball, None)["M"].target


def test_a_run_in_the_back_of_a_marker_looking_at_the_ball_is_seen_late() -> None:
    players, ball, memory = _scene({"M": (16.0, 34.0, 1.0)})  # il regarde vers le ballon : l'attaquant est dans son dos
    seen = _marking(players, ball, memory)["M"]
    real = _marking(players, ball, None)["M"]
    perceived_x = 30.0 - anticipation_share(next(p for p in players if p.name == "M")) * 6.0 * 2.0
    assert seen.mate == "A" and real.mate == "A"
    assert seen.target.x - real.target.x == pytest.approx(perceived_x - 12.0, abs=1e-6)  # il vise l'endroit où il l'a vu
    assert seen.target.x > real.target.x + 8.0  # en retard de plus de 8 m
    assert seen.target_velocity == Vec2(-6.0, 0.0)  # et à la vitesse d'alors


def test_the_marker_is_the_one_nearest_to_the_attacker_as_each_perceives_him() -> None:
    players, ball, memory = _scene({"Dos": (16.0, 34.0, 1.0), "Face": (21.0, 34.0, -1.0)})
    assert list(_marking(players, ball, None)) == ["Dos"]  # en vrai le plus proche (4 m contre 9 m)
    assert list(_marking(players, ball, memory)) == ["Face"]  # mais « Dos » situe l'attaquant plus loin que « Face »


def test_without_memory_the_marking_is_unchanged() -> None:
    players, ball, _ = _scene({"M": (16.0, 34.0, 1.0)})
    mark = _marking(players, ball, None)["M"]
    assert mark.target.x == pytest.approx(12.0 - marking_distance_m(next(p for p in players if p.name == "M")))
    assert mark.target_velocity == Vec2(-6.0, 0.0)  # sa vraie vitesse


def _line(memory_on: bool):
    """Équipe domicile : défenseurs en x = 20, milieux en 35, attaquants en 50 ; le défenseur le plus bas regarde vers l'est.
    L'attaquant S, vu à 60 m de son but, a couru à 10 m : dans le dos de celui qui cale la ligne."""
    team = [replace(player(f"D{i}", "home", x=20.0, y=10.0 + 12.0 * i, poste="DC"), facing=Vec2(1.0, 0.0)) for i in range(4)]
    team += [player(f"M{i}", "home", x=35.0, y=14.0 + 12.0 * i, poste="MC") for i in range(4)]
    team += [player(f"B{i}", "home", x=50.0, y=24.0 + 20.0 * i, poste="BU") for i in range(2)]
    team.append(player("GK", "home", x=3.0, y=34.0, poste="GK"))
    striker = replace(player("S", "away", x=60.0, y=34.0, poste="BU", Pace=60), velocity=Vec2(-7.0, 0.0))
    start = [*team, striker]
    memory = PerceptionMemory(start, 0.0)
    memory.update(start, 0.0)
    moved = [*team, replace(striker, position=Vec2(10.0, 34.0))]
    memory.update(moved, 2.0)
    bloc = Bloc.from_players(moved)
    bloc.update(moved, BallState(position=Vec2(52.5, 34.0), velocity=Vec2(0.0, 0.0), holder=None), 2.0,
                memory if memory_on else None)
    return bloc.lines["home"]


def test_the_line_stays_high_when_the_run_behind_the_last_defender_is_not_seen() -> None:
    real, perceived = _line(False), _line(True)
    assert real <= 10.0 + 5.0 + 1e-6  # elle redescend derrière la course (piège de 5 m au plus)
    assert perceived > real + 5.0  # le défenseur le plus bas ne l'a pas vue : la ligne reste haute


def test_a_defender_who_scans_keeps_his_intention_and_stops_following_the_ball() -> None:
    defender = player("D", "home", x=30.0, y=34.0, poste="DC")
    holder = player("H", "away", x=40.0, y=34.0, poste="MC")
    ball = BallState(position=holder.position, velocity=Vec2(0.0, 0.0), holder="H")
    previous = Intention("pressing", "presser", Vec2(33.0, 12.0), 1.0, reason="il presse")
    followed = think(defender, ball, [defender, holder], 0.0, {}, None, None, None, None, previous, False)
    frozen = think(defender, ball, [defender, holder], 0.0, {}, None, None, None, None, previous, True)
    assert frozen is previous  # tête tournée : ce qu'il visait, il le garde
    assert followed is not previous  # sinon il suit le ballon


def test_a_goalkeeper_who_scans_keeps_following_the_ball() -> None:
    keeper = player("G", "home", x=3.0, y=34.0, poste="GK")
    holder = player("H", "away", x=14.0, y=34.0, poste="BU")
    ball = BallState(position=holder.position, velocity=Vec2(0.0, 0.0), holder="H")
    previous = Intention("sortie", "sortir", Vec2(5.0, 34.0), 1.0, reason="il attend")
    updated = think(keeper, ball, [keeper, holder], 0.0, {}, None, None, None, None, previous, True)
    assert updated is not previous  # le gardien en face-à-face ne garde pas son ancienne intention


def test_the_scan_costs_nothing_to_the_side_with_the_ball() -> None:
    carrier = player("H", "away", x=40.0, y=34.0, poste="MC")
    mate = player("T", "away", x=45.0, y=34.0, poste="MC")
    foe = player("D", "home", x=30.0, y=34.0, poste="DC")
    ball = BallState(position=carrier.position, velocity=Vec2(0.0, 0.0), holder="H")
    previous = Intention("soutien", "soutenir", Vec2(1.0, 1.0), 1.0, reason="soutien")
    kept = think(mate, ball, [carrier, mate, foe], 0.0, {}, None, None, None, None, previous, True)
    assert kept is not previous  # l'attaquant qui scanne n'est pas gelé


def test_scans_are_traced_as_defending_only_for_the_side_without_the_ball(monkeypatch) -> None:
    carrier = player("H", "away", x=40.0, y=34.0)
    mate = player("T", "away", x=45.0, y=34.0)
    foe = player("D", "home", x=30.0, y=34.0)
    monkeypatch.setattr(flux.REGARD, "random", lambda: 0.0)  # tout le monde scanne
    events: list = []
    ScanTracker().update([carrier, mate, foe], "H", 0.0, 0.1, events)
    assert {e.player: e.defending for e in events} == {"H": False, "T": False, "D": True}
    events.clear()
    ScanTracker().update([carrier, mate, foe], None, 0.0, 0.1, events)  # ballon libre : personne ne défend
    assert not any(e.defending for e in events)

"""Tests du moteur V2, ticket v2-realisme/10f (zones de la surface : premier poteau, point de penalty, second poteau,
retrait). Voir .scratch/v2-realisme/issues/10f-zones-de-la-surface.md, critères d'acceptation."""

from __future__ import annotations

from v2engine import cerveau
from v2engine.ball_state import BallState
from v2engine.defense import (BOX_ZONES, COUVERTURE, POST_ZONES_MAX_M, PRESSEUR, WIDE_LAST_THIRD_M,
                              ZONE_HOLD_MARGIN_M, ZONE_SURFACE, DefensiveRoles, box_zone_spots, own_goal)
from v2engine.geometry import PITCH_LENGTH_M, Vec2
from v2engine.movement import PlayerState


def _p(name: str, team: str = "home", x: float = 50.0, y: float = 34.0, poste: str = "DC") -> PlayerState:
    return PlayerState(name=name, team=team, poste=poste, position=Vec2(x, y), velocity=Vec2(0.0, 0.0), pace=60,
                       acceleration=60, stamina=60, home_target=Vec2(x, y))


def _roles(players: list[PlayerState], holder: str) -> DefensiveRoles:
    holding = next(p for p in players if p.name == holder)
    defense = DefensiveRoles()
    defense.update(players, BallState(position=holding.position, velocity=Vec2(0.0, 0.0), holder=holder), None, 0.0)
    return defense


def _wing_scene(free: int) -> list[PlayerState]:
    """Ailier adverse à 10 m de la ligne de but défendue par « home » (x = 0), sur l'aile ; un presseur, un couvreur
    (le premier arrivé à 6 m derrière le porteur), puis `free` défenseurs libres dans le camp de « home », aucun
    attaquant dans les 25 m."""
    holder = _p("Ailier", team="away", x=10.0, y=60.0, poste="AG")
    players = [holder, _p("Presseur", x=12.0, y=58.0), _p("Couverture", x=9.0, y=52.0)]
    players += [_p(f"D{i}", x=20.0 + 3.0 * i, y=30.0 + 2.0 * i) for i in range(free)]
    return players


def test_validated_constants() -> None:
    assert WIDE_LAST_THIRD_M == 35.0 and POST_ZONES_MAX_M == 20.0 and ZONE_HOLD_MARGIN_M == 2.0
    assert BOX_ZONES == (("premier poteau", 4.0, 3.0), ("point de penalty", 11.0, 0.0), ("second poteau", 5.0, -4.0),
                         ("retrait", 13.0, 6.0))


def test_zones_only_when_ball_is_wide_in_the_last_third() -> None:
    goal = own_goal("home")
    assert len(box_zone_spots(Vec2(10.0, 60.0), goal)) == 4  # aile, à 10 m
    assert box_zone_spots(Vec2(10.0, 40.0), goal) == []  # dans la largeur de la surface
    assert box_zone_spots(Vec2(WIDE_LAST_THIRD_M + 1.0, 60.0), goal) == []  # hors du dernier tiers
    # côté ballon : premier poteau et retrait du côté de l'aile, second poteau de l'autre ; but adverse symétrique
    spots = dict(box_zone_spots(Vec2(10.0, 60.0), goal))
    assert spots["premier poteau"] == Vec2(4.0, 37.0) and spots["second poteau"] == Vec2(5.0, 30.0)
    assert spots["point de penalty"] == Vec2(11.0, 34.0) and spots["retrait"] == Vec2(13.0, 40.0)
    away = dict(box_zone_spots(Vec2(PITCH_LENGTH_M - 10.0, 8.0), own_goal("away")))
    assert away["premier poteau"] == Vec2(PITCH_LENGTH_M - 4.0, 31.0)


def test_four_free_defenders_hold_the_four_zones() -> None:
    defense = _roles(_wing_scene(4), "Ailier")
    zones = {a.mate: n for n, a in defense.assignments.items() if a.role == ZONE_SURFACE}
    assert set(zones) == {name for name, _, _ in BOX_ZONES}
    assert defense.assignments["Presseur"].role == PRESSEUR  # presseur et couverture gardent leur rôle
    assert defense.assignments["Couverture"].role == COUVERTURE
    spots = dict(box_zone_spots(Vec2(10.0, 60.0), own_goal("home")))
    assert all(defense.assignments[n].target == spots[z] for z, n in zones.items())  # sans bloc : point exact


def test_fewer_free_defenders_hold_the_zones_by_priority() -> None:
    defense = _roles(_wing_scene(2), "Ailier")
    assert {a.mate for a in defense.assignments.values() if a.role == ZONE_SURFACE} == {"premier poteau",
                                                                                        "point de penalty"}


def test_no_zone_when_the_ball_is_central() -> None:
    players = _wing_scene(4)
    players[0] = _p("Ailier", team="away", x=10.0, y=40.0, poste="AG")
    defense = _roles(players, "Ailier")
    assert not any(a.role == ZONE_SURFACE for a in defense.assignments.values())


def test_defender_outside_his_own_half_does_not_take_a_zone() -> None:
    players = _wing_scene(0) + [_p("Avant", x=60.0, y=34.0, poste="BU")]
    defense = _roles(players, "Ailier")
    assert "Avant" not in defense.assignments


def test_zone_holder_intention_is_traced() -> None:
    players = _wing_scene(4)
    defense = _roles(players, "Ailier")
    name = next(n for n, a in defense.assignments.items() if a.mate == "premier poteau")
    holder = players[0]
    intention = cerveau.think(next(p for p in players if p.name == name),
                              BallState(position=holder.position, velocity=Vec2(0.0, 0.0), holder="Ailier"),
                              players, 1.0, None, defense=defense)
    assert intention.role == ZONE_SURFACE and intention.action == "tenir sa zone" and intention.mate == "premier poteau"


def test_posts_are_held_only_when_the_ball_is_close() -> None:
    # réserve A1 de l'expert : ailier à 30 m, personne ne descend aux poteaux (la ligne de hors-jeu ne tombe pas à 4 m)
    goal = own_goal("home")
    far = [zone for zone, _ in box_zone_spots(Vec2(30.0, 60.0), goal)]
    assert far == ["point de penalty", "retrait"]
    assert [zone for zone, _ in box_zone_spots(Vec2(POST_ZONES_MAX_M, 60.0), goal)] == [name for name, _, _ in BOX_ZONES]
    players = [_p("Ailier", team="away", x=30.0, y=60.0, poste="AG"), _p("Presseur", x=32.0, y=58.0),
               _p("Couverture", x=26.0, y=55.0)] + [_p(f"D{i}", x=20.0 + 3.0 * i, y=30.0 + 2.0 * i) for i in range(4)]
    targets = [a.target for a in _roles(players, "Ailier").assignments.values() if a.role == ZONE_SURFACE]
    assert len(targets) == 2 and min(t.x for t in targets) >= 11.0


def test_active_zones_stay_while_the_ball_wavers_at_the_threshold() -> None:
    # réserve A2 de l'expert : un porteur qui longe le bord de la largeur de surface garde les mêmes zones
    edge = 34.0 + 20.16
    players = _wing_scene(4)
    defense = DefensiveRoles()
    roles = []
    for step, y in enumerate((edge + 0.5, edge - 0.5, edge + 0.5, edge - 0.5)):
        players[0] = _p("Ailier", team="away", x=10.0, y=y, poste="AG")
        defense.update(players, BallState(position=players[0].position, velocity=Vec2(0.0, 0.0), holder="Ailier"),
                       None, 0.1 * step)
        roles.append({n: a.mate for n, a in defense.assignments.items() if a.role == ZONE_SURFACE})
    assert len(roles[0]) == 4 and all(r == roles[0] for r in roles)
    # au-delà de la marge, elles s'éteignent ; sans zone active, le seuil reste le bord de la surface
    players[0] = _p("Ailier", team="away", x=10.0, y=edge - ZONE_HOLD_MARGIN_M - 0.5, poste="AG")
    defense.update(players, BallState(position=players[0].position, velocity=Vec2(0.0, 0.0), holder="Ailier"), None, 1.0)
    assert not any(a.role == ZONE_SURFACE for a in defense.assignments.values())
    assert box_zone_spots(Vec2(10.0, edge - 0.5), own_goal("home")) == []

"""Presseur selon la zone (ticket v2-realisme/10a) : le presseur est choisi parmi les joueurs dont la zone de
responsabilité (rectangle autour de leur place de référence sans ballon) contient le porteur, sauf si aucun d'eux
n'arrive dans la marge validée ; à égalité de zone, le premier arrivé."""

from __future__ import annotations

import random

from v2engine.ball_state import BallState
from v2engine.defense import (PRESS_ZONE_MARGIN_S, PRESSEUR, ZONE_DEPTH_M, ZONE_WIDTH_M, DefensiveRoles, arrival_time_s,
                              in_zone, own_goal)
from v2engine.geometry import Vec2
from v2engine.movement import PlayerState

GOAL = own_goal("home")  # domicile défend x = 0


def _p(name: str, x: float, y: float = 34.0, poste: str = "DC", team: str = "home", pace: float = 60,
       place: Vec2 | None = None) -> PlayerState:
    """Joueur en (x, y) ; `place` : sa place de référence sans ballon (par défaut, là où il est)."""
    return PlayerState(name=name, team=team, poste=poste, position=Vec2(x, y), velocity=Vec2(0.0, 0.0), pace=pace,
                       acceleration=60, stamina=60, home_target=place or Vec2(x, y))


class _Bloc:
    """Bloc de scène : la place de référence de chacun est sa `home_target`, sans erreur de placement."""

    def reference(self, player: PlayerState, ball: Vec2, situation: str, now_s: float = 0.0) -> Vec2:
        return player.home_target

    def placement_error(self, player: PlayerState, now_s: float) -> Vec2:
        return Vec2(0.0, 0.0)


def _presser(players: list[PlayerState], holder: str, bloc: _Bloc | None = None) -> tuple[str, DefensiveRoles]:
    random.seed(0)
    holding = next(p for p in players if p.name == holder)
    defense = DefensiveRoles()
    defense.update(players, BallState(position=holding.position, velocity=Vec2(0.0, 0.0), holder=holder), bloc, 0.0)
    (name,) = [n for n, a in defense.assignments.items() if a.role == PRESSEUR]
    return name, defense


def _lines() -> dict[str, Vec2]:
    """Places d'une équipe en 4-4-2 simplifié : ligne de défense à 27,5 m, milieux à 40,5 m, attaquants à 55 m."""
    return {"LB": Vec2(27.5, 10.0), "DC1": Vec2(27.5, 28.0), "DC2": Vec2(27.5, 40.0), "RB": Vec2(27.5, 58.0),
            "LM": Vec2(40.5, 10.0), "MC1": Vec2(40.5, 28.0), "MC2": Vec2(40.5, 40.0), "RM": Vec2(40.5, 58.0),
            "BU1": Vec2(55.0, 28.0), "BU2": Vec2(55.0, 40.0)}


def test_validated_constants() -> None:
    assert (ZONE_DEPTH_M, ZONE_WIDTH_M, PRESS_ZONE_MARGIN_S) == (8.0, 10.0, 1.0)


def test_zone_is_a_rectangle_around_the_reference_place() -> None:
    places = _lines()
    assert in_zone("MC1", places, Vec2(40.5 + 7.9, 28.0 + 9.9), GOAL)
    assert not in_zone("MC1", places, Vec2(40.5 + 8.1, 28.0), GOAL)  # devant : une ligne devant lui
    assert not in_zone("MC1", places, Vec2(40.5 - 8.1, 28.0), GOAL)  # derrière : une ligne derrière lui
    assert not in_zone("MC1", places, Vec2(40.5, 28.0 + 10.1), GOAL)  # vers l'axe : MC2 plus excentré de ce côté
    assert not in_zone("MC1", places, Vec2(40.5, 28.0 - 10.1), GOAL)  # vers la touche : LM plus excentré


def test_open_edges_last_line_front_line_and_touchline() -> None:
    places = _lines()
    assert in_zone("DC1", places, Vec2(3.0, 28.0), GOAL)  # dernière ligne : ouverte jusqu'à son but
    assert in_zone("BU1", places, Vec2(90.0, 28.0), GOAL)  # ligne la plus avancée : ouverte vers l'avant
    assert in_zone("LB", places, Vec2(27.5, 0.5), GOAL) and in_zone("LM", places, Vec2(40.5, 0.5), GOAL)
    assert not in_zone("LB", places, Vec2(27.5, 10.0 + 10.1), GOAL)  # vers l'axe : DC1 plus excentré de ce côté


def test_away_team_zones_are_mirrored() -> None:
    places = {n: Vec2(105.0 - v.x, v.y) for n, v in _lines().items()}
    goal = own_goal("away")
    assert in_zone("DC1", places, Vec2(102.0, 28.0), goal)
    assert not in_zone("MC1", places, Vec2(105.0 - 40.5 - 8.1, 28.0), goal)


def test_holder_at_the_centre_circle_the_midfielder_presses_not_the_centre_back() -> None:
    # porteur au rond central ; le DC (25 m, rapide) arrive avant le milieu (18 m, lent), mais le porteur est dans la
    # zone du milieu (place à 6,5 m devant elle), pas dans celle du DC : le milieu presse
    holder = _p("H", 52.5, team="away", poste="MC")
    dc = _p("DC", 27.5, pace=99)
    mc = _p("MC", 34.5, poste="MC", pace=11, place=Vec2(46.0, 34.0))
    bu = _p("BU", 75.0, y=10.0, poste="BU", pace=11)
    assert arrival_time_s(dc, holder.position) < arrival_time_s(mc, holder.position)  # avant le ticket : le DC
    assert _presser([holder, dc, mc, bu], "H")[0] == "DC"  # sans bloc : le premier arrivé, comme avant
    name, defense = _presser([holder, dc, mc, bu], "H", _Bloc())
    assert name == "MC"
    assigned = defense.assignments["MC"]
    assert assigned.zone is True and assigned.reference == Vec2(46.0, 34.0)  # zone tracée avec le presseur


def test_holder_in_the_centre_back_zone_the_centre_back_presses() -> None:
    # porteur à 7,5 m devant le but par rapport au DC (zone du DC) ; le milieu, juste à côté, est hors de sa zone
    holder = _p("H", 20.0, team="away", poste="BU")
    dc = _p("DC", 27.5)
    mc = _p("MC", 22.0, poste="MC", place=Vec2(40.5, 34.0))
    assert arrival_time_s(mc, holder.position) < arrival_time_s(dc, holder.position)
    assert arrival_time_s(dc, holder.position) - arrival_time_s(mc, holder.position) <= PRESS_ZONE_MARGIN_S
    name, defense = _presser([holder, dc, mc], "H", _Bloc())
    assert name == "DC" and defense.assignments["DC"].zone is True


def test_nobody_of_the_zone_within_the_margin_the_first_to_arrive_presses() -> None:
    # le seul joueur dont la zone contient le porteur arrive plus d'une seconde après le plus rapide
    holder = _p("H", 20.0, team="away", poste="BU")
    dc = _p("DC", 50.0, pace=11, place=Vec2(27.5, 34.0))  # 30 m, lent
    mc = _p("MC", 22.0, poste="MC", place=Vec2(40.5, 34.0))
    assert arrival_time_s(dc, holder.position) - arrival_time_s(mc, holder.position) > PRESS_ZONE_MARGIN_S
    name, defense = _presser([holder, dc, mc], "H", _Bloc())
    assert name == "MC" and defense.assignments["MC"].zone is False


def test_same_zone_the_first_to_arrive() -> None:
    holder = _p("H", 30.0, team="away", poste="BU")
    slow, fast = _p("Lent", 22.0, y=30.0, pace=11), _p("Rapide", 20.0, y=38.0, pace=99)
    assert _presser([holder, slow, fast], "H", _Bloc())[0] == "Rapide"


def test_pressers_are_traced_and_deterministic() -> None:
    from ligue1sim.clubs import load_clubs
    from ligue1sim.season import CLUBS_PATH
    from v2engine.match import simulate_match
    clubs = load_clubs(CLUBS_PATH, "Ligue 1")
    traces = []
    for _ in range(2):
        random.seed(20261118)
        traces.append(simulate_match(clubs[4], clubs[5], duration_minutes=2.0))
    records = traces[0].pressers
    assert records and records == traces[1].pressers
    pressing = [r for r in records if r.player]
    assert pressing and all(r.in_zone in (True, False) and r.reference_distance_m is not None for r in pressing)
    assert all(r.in_zone is None and r.poste == "" for r in records if not r.player)


def test_the_incumbent_keeps_a_holder_who_crosses_into_the_next_zone() -> None:
    # le milieu presse le porteur dans sa zone ; le porteur passe dans la zone du DC, le milieu est encore le plus près :
    # il le garde (`HOLD_MARGIN_S`) au lieu de le céder puis de le reprendre (va-et-vient au bord des zones)
    defense = DefensiveRoles()
    dc = _p("DC", 27.5)
    for x_holder, x_mc in ((36.0, 37.0), (31.0, 32.0)):
        holder = _p("H", x_holder, team="away", poste="BU")
        mc = _p("MC", x_mc, poste="MC", place=Vec2(40.5, 34.0))
        defense.update([holder, dc, mc], BallState(position=holder.position, velocity=Vec2(0.0, 0.0), holder="H"),
                       _Bloc(), 0.0)
        assert [n for n, a in defense.assignments.items() if a.role == PRESSEUR] == ["MC"]
    assert defense.assignments["MC"].zone is False  # tracé : il presse hors de sa zone
    # sans titulaire, le DC, dont la zone contient le porteur, presse
    assert _presser([holder, dc, mc], "H", _Bloc())[0] == "DC"

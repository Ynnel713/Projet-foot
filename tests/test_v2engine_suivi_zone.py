"""Suiveur du pressing d'équipe et couvreur selon la zone (ticket v2-realisme/10k) : comme le presseur du 10a, ils
sont choisis parmi les joueurs dont la zone de responsabilité contient le receveur (ou le point de couverture) et qui
arrivent dans la marge validée ; aucun : tous, comme avant."""

from __future__ import annotations

import random

from v2engine.ball_state import BallState
from v2engine.defense import (COUVERTURE, MARQUAGE, PRESS_ZONE_MARGIN_S, PRESSEUR, DefensiveRoles, arrival_time_s)
from v2engine.geometry import Vec2
from v2engine.movement import PlayerState


def _p(name: str, x: float, y: float, poste: str, team: str = "home", pace: float = 60,
       place: Vec2 | None = None) -> PlayerState:
    return PlayerState(name=name, team=team, poste=poste, position=Vec2(x, y), velocity=Vec2(0.0, 0.0), pace=pace,
                       acceleration=60, stamina=60, home_target=place or Vec2(x, y))


class _Bloc:
    """Bloc de scène : la place de référence de chacun est sa `home_target`, sans erreur de placement."""

    def reference(self, player: PlayerState, ball: Vec2, situation: str, now_s: float = 0.0) -> Vec2:
        return player.home_target

    def placement_error(self, player: PlayerState, now_s: float) -> Vec2:
        return Vec2(0.0, 0.0)


def _roles(players: list[PlayerState], holder: str, bloc: _Bloc | None, team_press: bool = False) -> dict[str, str]:
    """Rôle de chacun après une mise à jour ; `team_press` : pressing d'équipe en cours, tous suivent (Teamwork)."""
    random.seed(0)
    holding = next(p for p in players if p.name == holder)
    defense = DefensiveRoles()
    if team_press:
        defense.trigger_until["home"] = 10.0
        defense.follows = {p.name: True for p in players if p.team == "home"}
    defense.update(players, BallState(position=holding.position, velocity=Vec2(0.0, 0.0), holder=holder), bloc, 0.0)
    return {n: (a.role, a.mate) for n, a in defense.assignments.items()}


def _press_scene(mc2_pace: float = 60, mc2_at: Vec2 = Vec2(44.0, 38.0)) -> list[PlayerState]:
    """Porteur adverse à 60 m (hors de la moitié défendue : pas de couverture), receveur central R ; le latéral gauche,
    rentré, est plus près de R que le milieu MC2 dont la zone contient R. Domicile défend x = 0."""
    return [_p("H", 60.0, 34.0, "MC", team="away"), _p("R", 48.0, 31.0, "MC", team="away"),
            _p("MC1", 58.0, 34.0, "MC"), _p("MC2", mc2_at.x, mc2_at.y, "MC", pace=mc2_pace, place=Vec2(44.0, 38.0)),
            _p("LB", 46.0, 26.0, "LB", place=Vec2(25.0, 12.0)),
            _p("DC1", 25.0, 28.0, "DC"), _p("DC2", 25.0, 40.0, "DC")]


def test_central_receiver_followed_by_the_midfielder_of_the_zone_not_the_fullback() -> None:
    players = _press_scene()
    by = {p.name: p for p in players}
    r = by["R"].position
    assert by["LB"].position.distance_to(r) < by["MC2"].position.distance_to(r)  # avant le ticket : le latéral
    assert arrival_time_s(by["MC2"], r) - arrival_time_s(by["LB"], r) <= PRESS_ZONE_MARGIN_S
    assert _roles(players, "H", None, team_press=True)["LB"] == (MARQUAGE, "R")  # sans bloc : comme avant
    roles = _roles(players, "H", _Bloc(), team_press=True)
    assert roles["MC1"] == (PRESSEUR, "H")
    assert roles["MC2"] == (MARQUAGE, "R")
    assert "LB" not in roles  # il garde son couloir


def test_a_slower_follower_of_the_zone_still_follows() -> None:
    # règle stricte (choix du propriétaire du 21/11/2026) : pas de marge, le milieu de la zone suit même s'il arrive
    # plus d'une seconde après le latéral
    players = _press_scene(mc2_pace=11, mc2_at=Vec2(44.0, 46.0))
    by = {p.name: p for p in players}
    r = by["R"].position
    assert arrival_time_s(by["MC2"], r) - arrival_time_s(by["LB"], r) > PRESS_ZONE_MARGIN_S
    roles = _roles(players, "H", _Bloc(), team_press=True)
    assert roles["MC2"] == (MARQUAGE, "R") and "LB" not in roles


def test_nobody_of_the_zone_the_receiver_is_not_followed() -> None:
    players = [p if p.name != "MC2" else _p("MC2", 44.0, 38.0, "MC", place=Vec2(44.0, 60.0)) for p in _press_scene()]
    roles = _roles(players, "H", _Bloc(), team_press=True)
    assert roles["MC1"] == (PRESSEUR, "H")
    assert not any(mate == "R" for _, mate in roles.values())  # personne de sa zone : il n'est pas suivi
    assert "LB" not in roles  # le latéral garde son couloir


def _cover_scene() -> list[PlayerState]:
    """Porteur adverse dans l'axe de la moitié défendue : point de couverture à 6 m derrière lui, (34, 34) ; le latéral
    rentré y arrive le premier, le milieu défensif dont la zone le contient juste après."""
    return [_p("H", 40.0, 34.0, "MC", team="away"),
            _p("MC1", 42.0, 34.0, "MC"), _p("MDC", 28.0, 42.0, "MDC", place=Vec2(32.0, 40.0)),
            _p("LB", 33.0, 26.0, "LB", place=Vec2(25.0, 12.0)),
            _p("DC1", 20.0, 28.0, "DC"), _p("DC2", 20.0, 40.0, "DC")]


def test_central_cover_taken_by_the_midfielder_of_the_zone_not_the_fullback() -> None:
    players = _cover_scene()
    by = {p.name: p for p in players}
    spot = Vec2(34.0, 34.0)
    assert arrival_time_s(by["LB"], spot) < arrival_time_s(by["MDC"], spot)  # avant le ticket : le latéral
    assert arrival_time_s(by["MDC"], spot) - arrival_time_s(by["LB"], spot) <= PRESS_ZONE_MARGIN_S
    assert _roles(players, "H", None)["LB"] == (COUVERTURE, "H")  # sans bloc : comme avant
    roles = _roles(players, "H", _Bloc())
    assert roles["MC1"] == (PRESSEUR, "H")
    assert roles["MDC"] == (COUVERTURE, "H")
    assert "LB" not in roles


def test_match_with_zone_followers_is_deterministic() -> None:
    from ligue1sim.clubs import load_clubs
    from ligue1sim.season import CLUBS_PATH
    from v2engine.match import simulate_match
    clubs = load_clubs(CLUBS_PATH, "Ligue 1")
    traces = []
    for _ in range(2):
        random.seed(20261121)
        traces.append(simulate_match(clubs[6], clubs[7], duration_minutes=2.0))
    assert traces[0].events == traces[1].events and traces[0].pressers == traces[1].pressers


def _follow_two_ticks(r_second: Vec2, mc2_place: Vec2 = Vec2(44.0, 38.0)) -> tuple[dict, dict]:
    """Pressing d'équipe sur deux ticks : le receveur R, d'abord dans le couloir du latéral (qui le prend), rentre
    ensuite vers l'axe, dans la zone du milieu MC2."""
    random.seed(0)
    defense = DefensiveRoles()
    defense.trigger_until["home"] = 10.0
    roles = []
    for now_s, r_at, lb_at in ((0.0, Vec2(44.0, 22.0), Vec2(42.0, 20.0)), (0.1, r_second, Vec2(44.0, 24.0))):
        players = [_p("H", 55.0, 30.0, "MC", team="away"), _p("R", r_at.x, r_at.y, "MC", team="away"),
                   _p("MC1", 57.0, 30.0, "MC", place=Vec2(58.0, 34.0)),
                   _p("MC2", 44.0, 38.0, "MC", place=mc2_place),
                   _p("LB", lb_at.x, lb_at.y, "LB", place=Vec2(40.0, 14.0)),
                   _p("DC1", 25.0, 28.0, "DC"), _p("DC2", 25.0, 40.0, "DC")]
        defense.follows = {p.name: True for p in players if p.team == "home"}
        defense.update(players, BallState(position=players[0].position, velocity=Vec2(0.0, 0.0), holder="H"),
                       _Bloc(), now_s)
        roles.append({n: (a.role, a.mate) for n, a in defense.assignments.items()})
    return roles[0], roles[1]


def test_follower_hands_over_a_receiver_who_cuts_inside() -> None:
    first, second = _follow_two_ticks(Vec2(48.0, 31.0))
    assert first["LB"] == (MARQUAGE, "R")  # dans son couloir : le latéral le prend
    assert second["MC2"] == (MARQUAGE, "R")  # rentré dans l'axe : le milieu de la zone le reprend
    assert "LB" not in second  # le latéral retourne à sa place


def test_follower_lets_go_a_receiver_who_leaves_his_zone_even_if_nobody_takes_him() -> None:
    first, second = _follow_two_ticks(Vec2(48.0, 31.0), mc2_place=Vec2(44.0, 60.0))
    assert first["LB"] == (MARQUAGE, "R")
    assert "LB" not in second and not any(mate == "R" for _, mate in second.values())

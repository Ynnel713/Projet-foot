"""Rôles défensifs (ticket v2-collectif/07) : un presseur, une couverture dans sa moitié, un marqueur par attaquant
dangereux ; les autres tiennent le bloc, sauf l'indiscipliné (Teamwork)."""

from __future__ import annotations

import math
import random

from v2engine import cerveau
from v2engine.ball_state import BallState
from v2engine.bloc import Bloc
from v2engine.defense import (COUVERTURE, COVER_DEPTH_M, DANGER_M, MARQUAGE, PRESSEUR, DefensiveRoles,
                              leave_probability, marking_distance_m, own_goal)
from v2engine.geometry import Vec2
from v2engine.movement import PlayerState


def _p(name: str, team: str = "home", x: float = 50.0, y: float = 34.0, poste: str = "DC", pace: float = 60,
       **attributes: int) -> PlayerState:
    return PlayerState(name=name, team=team, poste=poste, position=Vec2(x, y), velocity=Vec2(0.0, 0.0), pace=pace,
                       acceleration=60, stamina=60, home_target=Vec2(x, y),
                       attributes={k.replace("_", " "): v for k, v in attributes.items()} or None)


def _roles(players: list[PlayerState], holder: str, bloc: Bloc | None = None) -> DefensiveRoles:
    holding = next(p for p in players if p.name == holder)
    defense = DefensiveRoles()
    defense.update(players, BallState(position=holding.position, velocity=Vec2(0.0, 0.0), holder=holder), bloc, 0.0)
    return defense


def test_validated_curves() -> None:
    assert [round(marking_distance_m(_p("M", Marking=n)), 2) for n in (99, 55, 11)] == [1.0, 2.5, 4.0]
    assert [round(leave_probability(_p("T", Teamwork=n)), 2) for n in (99, 55, 11)] == [0.0, 0.15, 0.35]


def test_one_presser_the_first_to_arrive_not_the_nearest() -> None:
    holder = _p("H", team="away", x=40)
    slow_near = _p("Lent", x=28, pace=11)  # 12 m à 7,0 m/s
    fast_far = _p("Rapide", x=25, pace=99)  # 15 m à 10,1 m/s : arrive avant
    other = _p("Autre", x=38, y=60)
    defense = _roles([holder, slow_near, fast_far, other], "H")
    pressers = [n for n, a in defense.assignments.items() if a.role == PRESSEUR]
    assert pressers == ["Rapide"]


def test_cover_stands_between_holder_and_goal_in_own_half_only() -> None:
    holder = _p("H", team="away", x=40, y=30)
    presser, coverer = _p("P", x=38, y=30), _p("C", x=30, y=34)
    defense = _roles([holder, presser, coverer], "H")
    cover = defense.assignments["C"]
    assert cover.role == COUVERTURE and cover.mate == "H"
    assert math.isclose(cover.target.distance_to(holder.position), COVER_DEPTH_M)
    goal = own_goal("home")
    # sur la ligne porteur-but : il ferme l'axe
    assert math.isclose(holder.position.distance_to(cover.target) + cover.target.distance_to(goal),
                        holder.position.distance_to(goal))
    far = _roles([_p("H", team="away", x=70, y=30), _p("P", x=68, y=30), _p("C", x=60, y=34)], "H")
    assert all(a.role != COUVERTURE for a in far.assignments.values())


def test_cover_spot_carries_the_positioning_error() -> None:
    random.seed(1)
    players = [_p("H", team="away", x=40), _p("P", x=38), _p("C", x=30, Positioning=11)]
    bloc = Bloc.from_players(players)
    defense = _roles(players, "H", bloc)
    error = bloc.errors["C"][0]
    spot = Vec2(40.0 - COVER_DEPTH_M, 34.0)
    assert error.length() > 0.0 and defense.assignments["C"].target.distance_to(spot + error) < 1e-9
    assert bloc.placement_error(players[2], 1.0) == error  # une seule erreur par joueur, partagée avec le bloc


def test_no_cover_for_a_holder_on_the_goal_and_no_marker_for_an_offside_attacker() -> None:
    holder = _p("H", team="away", x=0.0, y=34.0)
    defense = _roles([holder, _p("P", x=3), _p("C", x=8)], "H")
    assert [a.role for a in defense.assignments.values()] == [PRESSEUR]
    players = [_p("H", team="away", x=40, y=10), _p("A", team="away", x=12), _p("P", x=38, y=10), _p("M", x=16)]
    roles = DefensiveRoles()
    roles.update(players, BallState(position=Vec2(40, 10), velocity=Vec2(0.0, 0.0), holder="H",
                                    offside_out_until={"A": 5.0}), None, 0.0)
    assert all(a.role != MARQUAGE for a in roles.assignments.values())


def test_goalkeeper_near_an_opposing_holder_neither_presses_nor_leaves_the_bloc() -> None:
    # ticket v2-realisme/03a : avant, le gardien à moins de 15 m du porteur adverse le pressait (règle générale)
    holder = _p("H", team="away", x=12)
    keeper = _p("GK", x=3, poste="GK")
    players = [holder, _p("P", x=10), keeper]
    defense = _roles(players, "H")
    ball = BallState(position=holder.position, velocity=Vec2(0.0, 0.0), holder="H")
    intention = cerveau.think(keeper, ball, players, 1.0, None, defense=defense)
    assert intention.role == cerveau.GARDIEN and intention.reason.startswith("placement")
    assert intention.action != "aller au ballon"


def test_dangerous_attacker_is_marked_goal_side_tighter_by_a_good_marker() -> None:
    def marked(note: int) -> float:
        holder = _p("H", team="away", x=40, y=10)
        striker = _p("A", team="away", x=12, y=34)
        far_attacker = _p("Loin", team="away", x=12 + DANGER_M + 5, y=34)
        defense = _roles([holder, striker, far_attacker, _p("P", x=38, y=10), _p("C", x=33, y=14),
                          _p("M", x=16, y=34, Marking=note)], "H")
        mark = defense.assignments["M"]
        assert mark.role == MARQUAGE and mark.mate == "A"
        assert mark.target.x < striker.position.x  # côté but
        assert "Loin" not in {a.mate for a in defense.assignments.values()}
        return mark.target.distance_to(striker.position)
    assert marked(11) - marked(99) >= 1.0


def test_unassigned_player_holds_the_bloc_unless_he_leaves_it() -> None:
    holder = _p("H", team="away", x=40)
    disciplined = _p("D", x=45, y=40, Teamwork=99)
    players = [holder, _p("P", x=39), _p("C", x=33), disciplined]
    defense = _roles(players, "H")
    ball = BallState(position=holder.position, velocity=Vec2(0.0, 0.0), holder="H")
    assert "D" not in defense.assignments
    assert cerveau.think(disciplined, ball, players, 1.0, None, defense=defense).role == cerveau.REPLACEMENT
    defense.leaving["D"] = (True, 1e9)  # tirage d'indiscipline forcé
    leaving = cerveau.think(disciplined, ball, players, 1.0, None, defense=defense)
    assert leaving.role == PRESSEUR and leaving.reason == "quitte le bloc pour aller au ballon"


def test_low_teamwork_leaves_the_bloc_more_often() -> None:
    random.seed(7)
    defense = DefensiveRoles()
    counts = {}
    for note in (99, 11):
        player = _p(f"T{note}", Teamwork=note)
        counts[note] = sum(defense.leaves_the_bloc(player, 5.0 * k) for k in range(400))
    assert counts[99] == 0 and 100 < counts[11] < 180  # 35 % de 400, à quelques écarts-types près


def test_think_follows_the_assigned_roles() -> None:
    holder = _p("H", team="away", x=40)
    players = [holder, _p("P", x=38), _p("C", x=30), _p("GK", x=5, poste="GK")]
    defense = _roles(players, "H")
    ball = BallState(position=holder.position, velocity=Vec2(0.0, 0.0), holder="H")
    roles = {p.name: cerveau.think(p, ball, players, 1.0, None, defense=defense) for p in players[1:]}
    assert roles["P"].role == PRESSEUR and roles["P"].reason == "presse le porteur adverse"
    assert (roles["C"].role, roles["C"].action) == (COUVERTURE, "couvrir")
    assert "GK" not in defense.assignments  # le gardien n'a pas de rôle défensif de champ


def test_roles_stay_with_their_holder_unless_another_arrives_clearly_sooner() -> None:
    """Réserve A1 de l'expert : sans mémoire, deux défenseurs à temps d'arrivée quasi égaux se passaient le rôle."""
    holder = _p("H", team="away", x=40)
    a, b = _p("A", x=35), _p("B", x=45.2)  # B arrive à peine plus tard que A
    defense = DefensiveRoles()
    ball = BallState(position=holder.position, velocity=Vec2(0.0, 0.0), holder="H")
    defense.update([holder, a, b], ball, None, 0.0)
    assert defense.assignments["A"].role == PRESSEUR
    b_closer = _p("B", x=44.6)  # B passe devant, mais de bien moins de 0,3 s : A garde le rôle
    defense.update([holder, a, b_closer], ball, None, 0.1)
    assert defense.assignments["A"].role == PRESSEUR
    a_beaten = _p("A", x=30)  # A éliminé, B nettement plus près : la relève passe
    defense.update([holder, a_beaten, b_closer], ball, None, 0.2)
    assert defense.assignments["B"].role == PRESSEUR

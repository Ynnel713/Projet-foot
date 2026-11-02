"""Compensations défensives (ticket v2-collectif/09) et rôles pendant une passe adverse en vol (réserve A2 du ticket
07). Scénario de référence : le latéral droit est monté, le ballon est perdu, l'adversaire lance son ailier gauche."""

from __future__ import annotations

import random
from dataclasses import replace

from v2engine import cerveau
from v2engine.anticipation import reaction_delay_s
from v2engine.ball_state import BallState
from v2engine.bloc import Bloc
from v2engine.defense import COMPENSATION, COUVERTURE, PRESSEUR, DefensiveRoles, arrival_time_s
from v2engine.geometry import Vec2
from v2engine.movement import PlayerState, accel_tau_s, max_speed_mps, step
from v2engine.situation import DEFENSE_PLACEE


def _p(name: str, team: str = "home", x: float = 50.0, y: float = 34.0, poste: str = "DC",
       **attributes: int) -> PlayerState:
    return PlayerState(name=name, team=team, poste=poste, position=Vec2(x, y), velocity=Vec2(0.0, 0.0), pace=60,
                       acceleration=60, stamina=60, home_target=Vec2(x, y),
                       attributes={k.replace("_", " "): v for k, v in attributes.items()} or None)


def _scene(mdc_offset: Vec2 = Vec2(9.0, -4.0), with_dcs: bool = True, **mdc_attributes: int):
    """Domicile défend x = 0. Le latéral droit (RB) est monté de 35 m ; l'ailier adverse est à 16 m de sa place,
    non marqué (à plus de 25 m du but) ; le porteur adverse est au-delà de la ligne médiane. Retourne
    (joueurs, bloc, place du latéral, ailier)."""
    home = [_p("LB", x=20, y=10, poste="LB"), _p("RB", x=20, y=58, poste="RB"), _p("MC", x=45, y=34, poste="MC"),
            _p("MDC", x=32, y=34, poste="MDC", **mdc_attributes)]
    if with_dcs:
        home += [_p("DC1", x=20, y=28), _p("DC2", x=20, y=40)]
    bloc = Bloc.from_players(home)
    holder = _p("H", team="away", x=60, y=30, poste="MC")
    rb = home[1]
    place = bloc.reference(rb, holder.position, DEFENSE_PLACEE, 0.0)
    home[1] = replace(rb, position=place + Vec2(35.0, 0.0))
    winger = _p("W", team="away", x=place.x + 16.0, y=place.y, poste="AG")
    home[3] = replace(home[3], position=place + mdc_offset)
    if with_dcs:  # le central voisin, décalé vers le latéral : à 6,4 m de sa place
        home[5] = replace(home[5], position=place + Vec2(4.0, -5.0))
    return home + [holder, winger], bloc, place, winger


def _update(players, bloc, holder="H", defense=None, now_s=0.0):
    defense = defense or DefensiveRoles()
    holding = next(p for p in players if p.name == holder)
    defense.update(players, BallState(position=holding.position, velocity=Vec2(0.0, 0.0), holder=holder), bloc, now_s)
    return defense


def _compensator(defense: DefensiveRoles) -> str | None:
    return next((n for n, a in defense.assignments.items() if a.role == COMPENSATION), None)


def _run(players, bloc, place, dt=0.1, max_s=6.0):
    """Fait courir l'ailier vers la place vide et chaque défenseur vers sa cible de compensation, tick après tick
    (`movement.step`, rôles recalculés à chaque tick). Retourne la distance du défenseur le plus proche à la place quand
    l'ailier y arrive (à 1,5 m), et les compensateurs vus."""
    defense, seen = DefensiveRoles(), set()
    for i in range(int(max_s / dt)):
        now_s = i * dt
        defense = _update(players, bloc, defense=defense, now_s=now_s)
        seen |= {n for n, a in defense.assignments.items() if a.role == COMPENSATION}
        moved = []
        for p in players:
            assignment = defense.assignments.get(p.name)
            if p.name == "W":
                p = step(p, dt, place, 0.0)
            elif assignment is not None and assignment.role == COMPENSATION:
                p = step(p, dt, assignment.target, 0.0)
            moved.append(p)
        players = moved
        winger = next(p for p in players if p.name == "W")
        if winger.position.distance_to(place) <= 1.5:
            break
    home = [p for p in players if p.team == "home" and p.name != "RB"]
    return min(p.position.distance_to(place) for p in home), seen


def test_reference_scenario_the_place_is_taken_before_the_winger_arrives() -> None:
    held = 0
    for seed in range(1000):  # critère C1, joueurs moyens (55 par défaut), déplacements réels
        random.seed(seed)
        players, bloc, place, _ = _scene()
        distance, seen = _run(players, bloc, place)
        held += distance < 5.0  # place occupée : même seuil que le trou
    assert held / 1000 >= 0.60
    random.seed(0)
    players, bloc, place, _ = _scene(with_dcs=False)
    players = [replace(p, position=place + Vec2(-20.0, -20.0)) if p.name == "MDC" else p for p in players]
    assert _run(players, bloc, place)[0] > 5.0  # sans compensateur à temps : la place reste vide (0 % avant)


def test_hierarchy_defensive_midfielder_first_then_centre_back() -> None:
    random.seed(0)
    players, bloc, _, _ = _scene(Teamwork=99)
    assert _compensator(_update(players, bloc)) == "MDC"
    far, bloc, _, _ = _scene(mdc_offset=Vec2(-5.0, -30.0))  # le milieu défensif n'arrive pas à temps : le central
    far = [replace(p, attributes={"Teamwork": 99}) if p.name == "DC2" else p for p in far]
    assert _compensator(_update(far, bloc)) == "DC2"


def test_nobody_goes_when_nobody_arrives_in_time_or_without_danger() -> None:
    late, bloc, _, _ = _scene(mdc_offset=Vec2(25.0, -25.0), with_dcs=False)
    assert _compensator(_update(late, bloc)) is None
    players, bloc, place, _ = _scene()
    far_winger = [replace(p, position=place + Vec2(30.0, 0.0)) if p.name == "W" else p for p in players]
    assert _compensator(_update(far_winger, bloc)) is None  # attaquant à plus de 20 m : pas de danger
    holder_behind = [replace(p, position=Vec2(place.x - 2.0, 30.0)) if p.name == "H" else p for p in players]
    assert _compensator(_update(holder_behind, bloc)) is None  # place pas entre le ballon et le but


def test_low_teamwork_compensates_less_often() -> None:
    def rate(teamwork: int) -> float:
        hits = 0
        for seed in range(1000):
            random.seed(seed)
            players, bloc, _, _ = _scene(with_dcs=False, Teamwork=teamwork)
            hits += _compensator(_update(players, bloc)) == "MDC"
        return hits / 1000
    high, low = rate(99), rate(11)
    assert high > 0.9 and low < 0.7 and high > low  # 95 % contre 55 % (courbe du ticket 08)


def test_anticipation_reaction_delay_decides_who_is_in_time() -> None:
    players, bloc, place, winger = _scene(with_dcs=False)
    mdc = next(p for p in players if p.name == "MDC")
    # milieu défensif placé pour arriver juste à temps avec 0,55 s de réaction (99 : 0,4 s ; 11 : 1,0 s)
    margin = arrival_time_s(winger, place) - accel_tau_s(mdc.acceleration) - 0.55
    offset = Vec2(margin * max_speed_mps(mdc.pace), 0.0)

    def compensates(anticipation: int) -> bool:
        random.seed(1)
        scene, bloc, _, _ = _scene(mdc_offset=offset, with_dcs=False, Anticipation=anticipation, Teamwork=99)
        return _compensator(_update(scene, bloc)) == "MDC"
    assert reaction_delay_s(replace(mdc, attributes={"Anticipation": 99})) < 0.55 < reaction_delay_s(
        replace(mdc, attributes={"Anticipation": 11}))
    assert compensates(99) and not compensates(11)


def test_positioning_sets_how_close_to_the_place_he_stands() -> None:
    def close(positioning: int) -> float:
        hits = 0
        for seed in range(500):
            random.seed(seed)
            players, bloc, place, _ = _scene(with_dcs=False, Positioning=positioning, Teamwork=99)
            defense = _update(players, bloc, now_s=5.0 * seed)  # nouvelle erreur de placement à chaque tirage
            assignment = defense.assignments.get("MDC")
            hits += assignment is not None and assignment.target.distance_to(place) < 2.0
        return hits / 500
    assert close(99) > 0.9 > 0.5 > close(11)


def test_the_compensator_keeps_the_place_until_the_owner_is_back_within_5_m() -> None:
    random.seed(0)
    players, bloc, place, _ = _scene(with_dcs=False, Teamwork=99)
    defense = _update(players, bloc)
    assert _compensator(defense) == "MDC"
    halfway = [replace(p, position=place + Vec2(7.0, 0.0)) if p.name == "RB" else p for p in players]
    assert _compensator(_update(halfway, bloc, defense=defense)) == "MDC"  # 7 m : il garde la place
    back = [replace(p, position=place + Vec2(4.0, 0.0)) if p.name == "RB" else p for p in players]
    assert _compensator(_update(back, bloc, defense=defense)) is None  # revenu à moins de 5 m : il la rend
    assert _compensator(_update(halfway, bloc, defense=defense)) is None  # 7 m sans titulaire : pas de trou (> 10 m)


def test_cascade_stops_after_two_levels() -> None:
    random.seed(0)
    players, bloc, place, _ = _scene(mdc_offset=Vec2(-5.0, -30.0), Teamwork=99)
    players = [replace(p, attributes={"Teamwork": 99}) if p.name == "DC2" else p for p in players]
    defense = _update(players, bloc)
    first = _compensator(defense)
    assert first == "DC2" and defense.levels == {first: 1}
    dc = next(p for p in players if p.name == first)
    dc_place = bloc.reference(dc, Vec2(60.0, 30.0), DEFENSE_PLACEE, 0.0)
    # il est parti combler la place du latéral ; un attaquant arrive dans la sienne
    moved = [replace(p, position=place) if p.name == first else p for p in players]
    moved.append(_p("W2", team="away", x=dc_place.x + 18.0, y=dc_place.y, poste="BU"))

    def fills_his_place(level: int) -> bool:
        state = DefensiveRoles(levels={first: level})
        state = _update(moved, bloc, defense=state)
        return any(a.mate == first for a in state.assignments.values() if a.role == COMPENSATION)
    assert fills_his_place(1)  # deuxième niveau : comblée
    assert not fills_his_place(2)  # troisième niveau : non


def test_a_pass_in_flight_keeps_the_defensive_roles() -> None:
    random.seed(0)
    receiver = _p("R", team="away", x=40, y=30, poste="MC")
    passer = _p("H", team="away", x=60, y=30, poste="MC")
    marker_target = _p("A", team="away", x=15, y=34, poste="BU")
    reader = _p("Lecteur", x=50, y=31)
    home = [_p("D", x=10, y=34), _p("D2", x=12, y=36), _p("P", x=35, y=30, poste="MC"), reader]
    players = home + [receiver, passer, marker_target]
    ball = BallState(position=Vec2(58.0, 30.0), velocity=Vec2(-15.0, 0.0), receiver="R", last_pass_team="away",
                     readers={"Lecteur": Vec2(50.0, 30.0)})
    defense = DefensiveRoles()
    defense.update(players, ball, None, 0.0)
    roles = {n: a.role for n, a in defense.assignments.items()}
    assert roles.get("P") == PRESSEUR and "D" in roles and "Lecteur" not in roles
    assert any(a.mate == "A" for a in defense.assignments.values())  # l'attaquant dangereux reste marqué
    seen = cerveau.perceive(home[0], ball, players)
    assert cerveau.interpret(home[0], ball, seen, True, players, defense) == roles["D"]
    seen = cerveau.perceive(reader, ball, players)
    assert cerveau.interpret(reader, ball, seen, True, players, defense) == cerveau.LECTURE
    # une passe de sa propre équipe ne donne pas de rôle défensif
    own = BallState(position=Vec2(58.0, 30.0), velocity=Vec2(-15.0, 0.0), receiver="P", last_pass_team="home")
    mine = DefensiveRoles()
    mine.update(players, own, None, 0.0)
    assert all(n not in {p.name for p in home} for n in mine.assignments)


def test_think_reports_the_compensation() -> None:
    random.seed(0)
    players, bloc, place, _ = _scene(with_dcs=False, Teamwork=99)
    defense = _update(players, bloc)
    mdc = next(p for p in players if p.name == "MDC")
    ball = BallState(position=Vec2(60.0, 30.0), velocity=Vec2(0.0, 0.0), holder="H")
    intention = cerveau.think(mdc, ball, players, 0.0, {}, DEFENSE_PLACEE, bloc, defense)
    assert intention.role == COMPENSATION and intention.mate == "RB"
    assert intention.target.distance_to(place) < 5.0


def test_an_incumbent_taken_by_another_role_no_longer_holds_the_place_open() -> None:
    random.seed(0)
    players, bloc, place, _ = _scene(Teamwork=99)
    defense = _update(players, bloc)
    assert _compensator(defense) == "MDC"
    on_place = [replace(p, position=place + Vec2(1.0, 0.0)) if p.name == "MDC" else p for p in players]
    # au tick suivant, le milieu défensif, arrivé sur la place, a un autre rôle (ici : il lit une passe)
    holding = next(p for p in on_place if p.name == "H")
    ball = BallState(position=holding.position, velocity=Vec2(0.0, 0.0), holder="H", readers={"MDC": place})
    defense.update(on_place, ball, bloc, 0.1)
    assert _compensator(defense) is None  # il est sur la place : pas de deuxième compensateur, pas de cascade


def test_one_teamwork_draw_per_hole_until_the_owner_is_back() -> None:
    random.seed(0)
    players, bloc, place, _ = _scene(with_dcs=False)
    defense = _update(players, bloc)
    drawn = dict(defense.willing)
    assert drawn
    calm = [replace(p, position=place + Vec2(30.0, 0.0)) if p.name == "W" else p for p in players]
    defense = _update(calm, bloc, defense=defense, now_s=0.1)  # le danger s'éloigne un instant
    defense = _update(players, bloc, defense=defense, now_s=0.2)  # il revient : même tirage
    assert {k: defense.willing[k] for k in drawn} == drawn
    back = [replace(p, position=place + Vec2(3.0, 0.0)) if p.name == "RB" else p for p in players]
    defense = _update(back, bloc, defense=defense, now_s=0.3)  # l'absent est revenu : trou fini
    assert not any(k[0] == "RB" for k in defense.willing)


def test_flight_keeps_the_real_holder_for_triggers_and_the_presser_effort() -> None:
    random.seed(0)
    passer, receiver = _p("H", team="away", x=60, y=30, poste="MC"), _p("R", team="away", x=40, y=30, poste="MC")
    presser = _p("P", x=35, y=30, poste="MC")
    players = [presser, _p("D", x=10, y=34), passer, receiver]
    defense = DefensiveRoles()
    defense.update(players, BallState(position=passer.position, velocity=Vec2(0.0, 0.0), holder="H"), None, 0.0)
    flight = BallState(position=Vec2(58.0, 30.0), velocity=Vec2(-15.0, 0.0), receiver="R", last_pass_team="away")
    defense.update(players, flight, None, 0.5)
    assert defense.last_holder[0] == "H"  # le porteur fictif ne déclenche pas le pressing d'équipe
    assert defense.burst["P"] == ("R", 0.5)  # effort sur le receveur, compté dès le départ de la passe
    defense.update(players, BallState(position=receiver.position, velocity=Vec2(0.0, 0.0), holder="R"), None, 1.0)
    assert defense.burst["P"] == ("R", 0.5)  # gardé à la réception (réserve A4 du ticket 08)


def test_the_compensator_holds_the_place_after_the_winger_arrives() -> None:
    # vérification V1 de l'expert (passage 1) : le latéral reste absent ; les joueurs sans rôle regagnent leur place
    kept = 0
    for seed in range(300):
        random.seed(seed)
        players, bloc, place, _ = _scene()
        holder = next(p for p in players if p.name == "H").position
        defense, arrived_at = DefensiveRoles(), None
        for i in range(80):
            now_s = i * 0.1
            defense = _update(players, bloc, defense=defense, now_s=now_s)
            if arrived_at is not None and now_s >= arrived_at + 2.0:
                break
            moved = []
            for p in players:
                assignment = defense.assignments.get(p.name)
                if p.name == "W":
                    p = step(p, 0.1, place, 0.0)
                elif p.team == "home" and p.name != "RB":
                    p = step(p, 0.1, assignment.target if assignment is not None
                             else bloc.reference(p, holder, DEFENSE_PLACEE, now_s), 0.0)
                moved.append(p)
            players = moved
            if arrived_at is None and next(p for p in players if p.name == "W").position.distance_to(place) <= 1.5:
                arrived_at = now_s
        kept += arrived_at is not None and any(a.role == COMPENSATION and a.mate == "RB"
                                               for a in defense.assignments.values())
    assert kept / 300 >= 0.95


def test_a_pressed_holder_still_threatens_the_empty_place() -> None:
    # réserve A2 de l'expert (passage 1) : le porteur pressé reste une menace, seul un attaquant marqué n'en est pas une.
    # Sans autre attaquant, la place n'est comblée que si le porteur compte.
    random.seed(0)
    players, bloc, _, _ = _scene(with_dcs=False, Teamwork=99)
    players = [p for p in players if p.name != "W"]
    rb = next(p for p in players if p.name == "RB")
    for x in range(60, 0, -1):  # la place du latéral suit le ballon : porteur à 20 m au plus, devant elle
        place = bloc.reference(rb, Vec2(float(x), 52.8), DEFENSE_PLACEE, 0.0)
        if Vec2(float(x), place.y).distance_to(place) <= 18.0:
            break
    holder_at = Vec2(float(x), place.y)
    scene = [replace(p, position=holder_at) if p.name == "H" else p for p in players]
    scene = [replace(p, position=place + Vec2(35.0, 0.0)) if p.name == "RB" else p for p in scene]
    scene = [replace(p, position=place + Vec2(4.0, -4.0)) if p.name == "MDC" else p for p in scene]
    scene = [replace(p, position=holder_at + Vec2(2.0, 0.0)) if p.name == "MC" else p for p in scene]  # presseur
    scene.append(_p("C", x=holder_at.x - 6.0, y=holder_at.y, poste="MC"))  # couverture
    defense = _update(scene, bloc)
    assert any(a.role == PRESSEUR and a.mate == "H" for a in defense.assignments.values())
    assert _compensator(defense) is not None


def test_the_served_winger_is_pressed_and_covered_with_a_real_line_height() -> None:
    # réserve A3 de l'expert (passage 2), comportement retenu par le propriétaire le 02/11/2026 (« Oui, ça suffit ») :
    # comme en match, `bloc.update` cale la ligne avant les rôles. L'ailier servi dans le couloir du latéral monté est
    # pressé (milieu défensif) et couvert (central voisin, entre lui et le but) ; la compensation est pour l'attaquant
    # qui court vers la place sans ballon.
    for seed in range(200):
        random.seed(seed)
        players, bloc, _, _ = _scene()
        players = [p for p in players if p.name not in ("H", "W")]
        rb = next(p for p in players if p.name == "RB")
        winger = _p("W", team="away", x=38.0, y=rb.home_target.y, poste="AG")
        players.append(winger)
        bloc.update(players, BallState(position=winger.position, velocity=Vec2(0.0, 0.0), holder="W"), 0.0)
        place = bloc.reference(rb, winger.position, DEFENSE_PLACEE, 0.0)
        assert winger.position.distance_to(place) <= 20.0  # dans le rayon de danger (sans ligne : plus de 20 m)
        scene = [replace(p, position=bloc.reference(p, winger.position, DEFENSE_PLACEE, 0.0))
                 if p.team == "home" else p for p in players]
        scene = [replace(p, position=place + Vec2(35.0, 0.0)) if p.name == "RB" else p for p in scene]
        scene = [replace(p, position=place + Vec2(9.0, -4.0)) if p.name == "MDC" else p for p in scene]
        roles = {n: (a.role, a.mate, a.target) for n, a in _update(scene, bloc, holder="W").assignments.items()}
        assert roles["MDC"][:2] == (PRESSEUR, "W")
        assert roles["DC2"][:2] == (COUVERTURE, "W") and roles["DC2"][2].x < winger.position.x


def test_cascade_levels_survive_a_loose_ball_tick() -> None:
    random.seed(0)
    players, bloc, _, _ = _scene(Teamwork=99)
    defense = _update(players, bloc)
    levels = dict(defense.levels)
    assert levels
    defense.update(players, BallState(position=Vec2(50.0, 34.0), velocity=Vec2(0.0, 0.0)), bloc, 0.1)  # ballon libre
    assert defense.levels == levels

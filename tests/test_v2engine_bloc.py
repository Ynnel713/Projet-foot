"""Tests du bloc de référence dynamique V2 (ticket v2-collectif/04) : le bloc suit le ballon, change de forme selon
la situation, Positioning règle l'erreur de placement et Teamwork l'écart toléré. Et la hauteur de la ligne défensive
sans ballon (ticket v2-collectif/05)."""

from __future__ import annotations

import dataclasses
import math
import random

from v2engine.ball_state import BallState
from v2engine.bloc import (
    BLOCK_SHIFT, LINE_HEIGHT_M, LINE_LAG_MAX_S, LINE_MAX_WITH_BALL_M, LINE_MIN_WITH_BALL_M, PRESSURE_STEP_M,
    GAP_DEF_MID_M, GAP_MID_ATT_M, SHAPE_WITH_BALL, SHAPE_WITHOUT_BALL, Bloc, line_lag_s, positioning_error_m,
    teamwork_tolerance_m, with_ball_line,
)
from v2engine.cerveau import REPLACEMENT, think
from v2engine.geometry import Vec2
from v2engine.movement import PlayerState
from v2engine.offside import TRAP_DEPTH_M
from v2engine.situation import DEFENSE_PLACEE, POSSESSION_INSTALLEE


def _p(name: str, x: float, y: float, poste: str = "MC", team: str = "home", **attrs: int) -> PlayerState:
    return PlayerState(name=name, team=team, poste=poste, position=Vec2(x, y), velocity=Vec2(0.0, 0.0), pace=60,
                       acceleration=60, stamina=60, home_target=Vec2(x, y), attributes=attrs or None)


# 4-4-2 simplifiée : défense à x = 18, milieu à 32, attaque à 45 ; largeur de 16 à 52 m.
TEAM = ([_p("GK", 5, 34, poste="GK")] + [_p(f"D{i}", 18, y, poste="DC") for i, y in enumerate((16, 28, 40, 52))]
        + [_p(f"M{i}", 32, y) for i, y in enumerate((16, 28, 40, 52))] + [_p(f"A{i}", 45, y, poste="BU") for i, y in enumerate((28, 40))])
CENTER_BALL = Vec2(52.5, 34.0)


def _dims(bloc: Bloc, ball: Vec2, situation: str) -> tuple[float, float, Vec2]:
    pts = [bloc.reference(p, ball, situation) for p in TEAM if p.poste != "GK"]
    xs, ys = [p.x for p in pts], [p.y for p in pts]
    return max(xs) - min(xs), max(ys) - min(ys), Vec2(sum(xs) / len(xs), sum(ys) / len(ys))


def test_the_shape_follows_the_situation() -> None:
    bloc = Bloc.from_players(TEAM)
    length, width, _ = _dims(bloc, CENTER_BALL, DEFENSE_PLACEE)
    assert math.isclose(length, SHAPE_WITHOUT_BALL[0]) and math.isclose(width, SHAPE_WITHOUT_BALL[1])
    length, width, _ = _dims(bloc, CENTER_BALL, POSSESSION_INSTALLEE)
    # avec ballon, 42 m avant le resserrement des écarts entre lignes (ticket v2-realisme/09e) : 14 m puis 13 m de départ,
    # x 42/27, soit 21,8 m ramenés à 15 m et 20,2 m ramenés à 20 m
    scale = SHAPE_WITH_BALL[0] / 27.0
    expected = SHAPE_WITH_BALL[0] - (14.0 * scale - GAP_DEF_MID_M[1]) - (13.0 * scale - GAP_MID_ATT_M[1])
    assert math.isclose(length, expected) and math.isclose(width, SHAPE_WITH_BALL[1])


def test_the_block_slides_with_the_ball_more_in_length_than_in_width() -> None:
    bloc = Bloc.from_players(TEAM)
    _, _, center = _dims(bloc, CENTER_BALL, DEFENSE_PLACEE)
    _, _, moved = _dims(bloc, CENTER_BALL + Vec2(10.0, 10.0), DEFENSE_PLACEE)
    assert math.isclose(moved.x - center.x, 10.0 * BLOCK_SHIFT[0]) and math.isclose(moved.y - center.y, 10.0 * BLOCK_SHIFT[1])


def test_the_far_side_tightens_but_stays_occupied() -> None:
    bloc = Bloc.from_players(TEAM)
    ys = [bloc.reference(p, Vec2(52.5, 0.0), DEFENSE_PLACEE).y for p in TEAM if p.poste != "GK"]
    assert max(ys) > 34.0  # ballon contre la touche du bas : il reste du monde au-delà de l'axe


def test_the_block_never_goes_behind_its_own_goal_line_and_the_keeper_keeps_his_place() -> None:
    bloc = Bloc.from_players(TEAM)
    assert min(bloc.reference(p, Vec2(0.0, 34.0), POSSESSION_INSTALLEE).x for p in TEAM if p.poste != "GK") >= 5.0 - 1e-9
    assert bloc.reference(TEAM[0], Vec2(80.0, 10.0), DEFENSE_PLACEE) == TEAM[0].home_target


def test_positioning_and_teamwork_follow_validated_points() -> None:
    # note médiane (62) -> valeur de base, 55 avant le ticket v2-realisme/24 ; extrêmes inchangés
    for note, error, tolerance in ((99, 0.5, 2.0), (62, 2.0, 5.0), (11, 4.0, 9.0)):
        player = _p("X", 30, 30, Positioning=note, Teamwork=note)
        assert math.isclose(positioning_error_m(player), error) and math.isclose(teamwork_tolerance_m(player), tolerance)


def test_positioning_error_is_redrawn_every_five_seconds_and_bounded() -> None:
    random.seed(1)
    bloc = Bloc.from_players(TEAM)
    player = _p("M0", 32, 16, Positioning=11)
    ref = bloc.reference(player, CENTER_BALL, DEFENSE_PLACEE)
    first = bloc.target(player, CENTER_BALL, DEFENSE_PLACEE, 0.0)
    assert bloc.target(player, CENTER_BALL, DEFENSE_PLACEE, 4.9) == first
    assert bloc.target(player, CENTER_BALL, DEFENSE_PLACEE, 5.0) != first
    assert all(bloc.target(player, CENTER_BALL, DEFENSE_PLACEE, 5.0 * k).distance_to(ref) <= 8.0 + 1e-9 for k in range(50))


def test_teamwork_decides_whether_he_holds_or_goes_back() -> None:
    random.seed(2)
    bloc = Bloc.from_players(TEAM)
    ball = BallState(position=Vec2(95.0, 34.0), velocity=Vec2(0.0, 0.0), holder=None)
    for teamwork, expected in ((99, "se replacer"), (11, "tenir sa place")):
        player = _p("M0", 32, 16, Positioning=99, Teamwork=teamwork)
        bloc.returning.clear()  # même joueur aux deux notes : il n'est pas déjà en train de revenir
        ref = bloc.reference(player, ball.position, DEFENSE_PLACEE)
        player.position = ref + Vec2(0.0, 5.0)  # 5 m de sa place : au-delà de 2 m, en deçà de 9 m
        others = [_p("Y", 90.0, 34.0, team="home"), _p("Z", 20.0, 34.0, team="away")]  # plus proches du ballon
        intention = think(player, ball, [player, *others], 1.0, None, DEFENSE_PLACEE, bloc)
        assert intention.role == REPLACEMENT and intention.action == expected


def test_positioning_only_acts_without_the_ball() -> None:  # placement défensif de zone (règle R3)
    bloc = Bloc.from_players(TEAM)
    player = _p("M0", 32, 16, Positioning=11)
    assert bloc.target(player, CENTER_BALL, POSSESSION_INSTALLEE, 0.0) == bloc.reference(player, CENTER_BALL, POSSESSION_INSTALLEE)


def test_the_block_moves_up_when_the_team_has_the_ball() -> None:
    bloc = Bloc.from_players(TEAM)
    _, _, without = _dims(bloc, CENTER_BALL, DEFENSE_PLACEE)
    _, _, with_ball = _dims(bloc, CENTER_BALL, POSSESSION_INSTALLEE)
    assert with_ball.x > without.x
    away = _p("B", 80, 30, team="away")
    away_bloc = Bloc.from_players([away, _p("B2", 70, 40, team="away")])
    assert away_bloc.reference(away, CENTER_BALL, POSSESSION_INSTALLEE).x < away_bloc.reference(away, CENTER_BALL, DEFENSE_PLACEE).x


def test_the_keeper_always_goes_back_to_his_place() -> None:
    bloc = Bloc.from_players(TEAM)
    keeper = _p("GK", 5, 34, poste="GK", Positioning=11, Teamwork=11)
    keeper.position = Vec2(8.0, 34.0)  # 3 m de sa place, bien en deçà de la tolérance de Teamwork 11
    assert bloc.replacement(keeper, CENTER_BALL, DEFENSE_PLACEE, 0.0) == keeper.home_target


def test_once_he_goes_back_he_goes_all_the_way_to_his_place() -> None:
    random.seed(3)
    bloc = Bloc.from_players(TEAM)
    player = _p("M0", 32, 16, Positioning=99, Teamwork=55)  # tolérance 5 m
    place = bloc.target(player, CENTER_BALL, DEFENSE_PLACEE, 0.0)
    player.position = place + Vec2(0.0, 7.0)
    assert bloc.replacement(player, CENTER_BALL, DEFENSE_PLACEE, 0.1) is not None  # au-delà de 5 m : il repart
    player.position = place + Vec2(0.0, 3.0)
    assert bloc.replacement(player, CENTER_BALL, DEFENSE_PLACEE, 0.2) is not None  # en route : il continue
    player.position = place + Vec2(0.0, 0.5)
    assert bloc.replacement(player, CENTER_BALL, DEFENSE_PLACEE, 0.3) is None  # arrivé : il tient sa place
    player.position = place + Vec2(0.0, 3.0)
    assert bloc.replacement(player, CENTER_BALL, DEFENSE_PLACEE, 0.4) is None  # écart toléré


def test_the_last_line_stays_five_metres_from_goal_whatever_the_shape() -> None:
    lopsided = [_p(f"D{i}", 18, y, poste="DC") for i, y in enumerate((20, 34, 48))] + [
        _p(f"M{i}", 32, y) for i, y in enumerate((16, 28, 40, 52))] + [_p(f"A{i}", 45, y, poste="BU") for i, y in enumerate((20, 34, 48))]
    bloc = Bloc.from_players(lopsided)
    for ball_x, situation in ((0.0, DEFENSE_PLACEE), (0.0, POSSESSION_INSTALLEE), (105.0, POSSESSION_INSTALLEE)):
        xs = [bloc.reference(p, Vec2(ball_x, 34.0), situation).x for p in lopsided]
        assert min(xs) >= 5.0 - 1e-9 and max(xs) <= 100.0 + 1e-9


def test_a_team_without_outfield_players_keeps_its_places() -> None:
    keeper = _p("GK", 5, 34, poste="GK")
    assert Bloc.from_players([keeper]).reference(keeper, CENTER_BALL, DEFENSE_PLACEE) == keeper.home_target


def test_runs_start_from_the_place_in_the_block() -> None:
    from v2engine.off_ball import choose_space
    random.seed(4)
    player = _p("M0", 32, 16, **{"Off the Ball": 99})
    anchor = Vec2(70.0, 40.0)
    assert choose_space(player, [_p("Z", 0.0, 0.0, team="away")], 1.0, anchor).distance_to(anchor) <= 16.0


def test_the_block_is_wired_in_the_match_and_stays_deterministic() -> None:
    from ligue1sim.clubs import load_clubs
    from ligue1sim.season import CLUBS_PATH
    from v2engine.match import simulate_match
    clubs = load_clubs(CLUBS_PATH, "Ligue 1")
    traces = []
    for _ in range(2):
        random.seed(20260925)
        traces.append(simulate_match(clubs[4], clubs[5], duration_minutes=2.0))
    actions = {p.intention.action for tick in traces[0].ticks for p in tick.players}
    assert "tenir sa place" in actions
    assert [[(p.position.x, p.position.y) for p in t.players] for t in traces[0].ticks] == \
        [[(p.position.x, p.position.y) for p in t.players] for t in traces[1].ticks]


# --- Hauteur de la ligne défensive sans ballon (ticket v2-collectif/05) ---------------------------------------------
def _line_case(holder_gap: float | None, striker_x: float = 100.0, defender_pace: int = 60, striker_pace: int = 60):
    """Domicile défend (TEAM, ballon au centre tenu par l'extérieur) ; `holder_gap` : distance du défenseur domicile le
    plus proche au porteur (None : ballon en vol)."""
    team = [_p(p.name, p.home_target.x, p.home_target.y, poste=p.poste) for p in TEAM]
    for p in team:
        if p.name.startswith("D"):
            p.pace = defender_pace
        p.position = Vec2(10.0, 5.0) if p.name != "M1" else Vec2(52.5 - (holder_gap or 30.0), 34.0)
    holder = _p("H", 52.5, 34.0, team="away")
    striker = _p("S", striker_x, 34.0, poste="BU", team="away")
    striker.pace = striker_pace
    players = [*team, holder, striker]
    bloc = Bloc.from_players(players)
    bloc.update(players, BallState(position=Vec2(52.5, 34.0), velocity=Vec2(0.0, 0.0), holder=None if holder_gap is None else "H"))
    return bloc, team


def test_line_height_at_the_centre_and_pressure_on_the_passer() -> None:
    assert math.isclose(_line_case(None)[0].lines["home"], LINE_HEIGHT_M)  # ballon en vol : ni pressé ni libre
    assert math.isclose(_line_case(6.0)[0].lines["home"], LINE_HEIGHT_M)  # entre 3 et 9 m : neutre
    assert math.isclose(_line_case(2.0)[0].lines["home"], LINE_HEIGHT_M + PRESSURE_STEP_M)  # pressé : la ligne monte
    assert math.isclose(_line_case(12.0)[0].lines["home"], LINE_HEIGHT_M - PRESSURE_STEP_M)  # libre : elle recule


def test_the_line_can_hold_above_an_isolated_attacker_up_to_the_trap_depth() -> None:
    """Ticket 23 : la ligne n'est plus tenue derrière l'attaquant le plus avancé (c'était le garde-fou du ticket
    05, faute de hors-jeu) ; elle peut se tenir jusqu'à TRAP_DEPTH_M au-dessus de lui."""
    even, _ = _line_case(None, striker_x=30.0)
    assert math.isclose(even.lines["home"], LINE_HEIGHT_M)  # 35 m : 5 m au-dessus de l'attaquant, dans le piège
    slow, _ = _line_case(None, striker_x=30.0, defender_pace=11, striker_pace=99)
    assert slow.lines["home"] < even.lines["home"] - 5.0  # trop lente : elle redescend derrière l'attaquant


def test_the_block_sits_on_its_line_for_both_teams() -> None:
    bloc, team = _line_case(None)
    xs = [bloc.reference(p, CENTER_BALL, DEFENSE_PLACEE).x for p in team if p.poste != "GK"]
    assert math.isclose(min(xs), LINE_HEIGHT_M)
    away = [_p(f"B{i}", 105.0 - p.home_target.x, p.home_target.y, poste=p.poste, team="away") for i, p in enumerate(TEAM)]
    rivals = [_p("R", 52.5, 34.0, team="home"), _p("R2", 5.0, 34.0, poste="BU", team="home")]
    bloc = Bloc.from_players([*away, *rivals])
    bloc.update([*away, *rivals], BallState(position=Vec2(52.5, 34.0), velocity=Vec2(0.0, 0.0), holder=None))
    xs = [bloc.reference(p, CENTER_BALL, DEFENSE_PLACEE).x for p in away if p.poste != "GK"]
    assert math.isclose(max(xs), 105.0 - LINE_HEIGHT_M)


def test_with_the_ball_the_line_rule_does_not_apply() -> None:
    bloc, team = _line_case(2.0)
    free = Bloc.from_players(team)
    player = next(p for p in team if p.name == "D0")
    assert bloc.reference(player, CENTER_BALL, POSSESSION_INSTALLEE) == free.reference(player, CENTER_BALL, POSSESSION_INSTALLEE)


def test_the_line_follows_an_off_centre_ball_for_both_teams() -> None:
    ball = BallState(position=Vec2(72.5, 34.0), velocity=Vec2(0.0, 0.0), holder=None)
    players = [*_line_case(None)[1], _p("H", 52.5, 34.0, team="away"), _p("S", 100.0, 34.0, poste="BU", team="away")]
    home = Bloc.from_players(players)
    home.update(players, ball)
    assert math.isclose(home.lines["home"], LINE_HEIGHT_M + 20.0 * BLOCK_SHIFT[0])  # ballon 20 m plus haut : la ligne monte
    away = [_p(f"B{i}", 105.0 - p.home_target.x, p.home_target.y, poste=p.poste, team="away") for i, p in enumerate(TEAM)]
    rivals = [_p("R", 72.5, 34.0, team="home"), _p("R2", 5.0, 34.0, poste="BU", team="home")]
    for p in away:
        p.position = Vec2(95.0, 5.0)
    bloc = Bloc.from_players([*away, *rivals])
    bloc.update([*away, *rivals], BallState(position=Vec2(72.5, 34.0), velocity=Vec2(0.0, 0.0), holder="R"))
    # extérieur : ballon 20 m plus près de son but, porteur libre (défenseur le plus proche à plus de 9 m)
    assert math.isclose(bloc.lines["away"], LINE_HEIGHT_M - 20.0 * BLOCK_SHIFT[0] - PRESSURE_STEP_M)
    rivals[1].position = Vec2(80.0, 34.0)  # attaquant à 25 m du but extérieur, même vitesse
    bloc.update([*away, *rivals], BallState(position=Vec2(52.5, 34.0), velocity=Vec2(0.0, 0.0), holder=None))
    assert math.isclose(bloc.lines["away"], 25.0 + TRAP_DEPTH_M)  # le piège la laisse monter au-dessus de lui


def test_the_margin_uses_the_slowest_defender_of_the_last_line_only() -> None:
    from v2engine.movement import max_speed_mps
    _, team = _line_case(None, striker_x=30.0)
    for p in team:  # un milieu très lent ne compte pas ; deux défenseurs de vitesses différentes : le plus lent compte
        p.pace = {"M0": 1, "D0": 40, "D1": 80}.get(p.name, 60)
    players = [*team, _p("H", 52.5, 34.0, team="away"), _p("S", 30.0, 34.0, poste="BU", team="away")]
    players[-1].pace = 90
    bloc = Bloc.from_players(players)
    bloc.update(players, BallState(position=Vec2(52.5, 34.0), velocity=Vec2(0.0, 0.0), holder=None))
    gain = (1.0 - max_speed_mps(40) / max_speed_mps(90)) * 30.0
    assert math.isclose(bloc.lines["home"], 30.0 + TRAP_DEPTH_M - gain)


def test_a_slow_line_follows_the_rise_with_a_delay() -> None:
    """Ticket 23, directive « piège collectif » : la ligne monte en bloc, mais un défenseur au Teamwork faible la
    suit avec du retard -- la faille qui laisse l'attaquant en jeu."""
    # note médiane (62) -> valeur de base, 55 avant le ticket v2-realisme/24 ; extrêmes inchangés
    for note, lag in ((99, 0.0), (62, 0.75), (11, 1.5)):
        assert math.isclose(line_lag_s(_p("D", 18, 20, Positioning=note, Teamwork=note)), lag, abs_tol=1e-9)
    assert math.isclose(line_lag_s(_p("D", 18, 20, Positioning=99, Teamwork=11)), LINE_LAG_MAX_S)  # le maillon faible
    bloc, team = _line_case(None)
    slow = next(p for p in team if p.name == "D0")
    for p in team:
        p.attributes = {"Positioning": 99, "Teamwork": 99}
    slow.attributes = {"Positioning": 11, "Teamwork": 11}
    low = BallState(position=Vec2(52.5, 34.0), velocity=Vec2(0.0, 0.0), holder=None)
    bloc.update([*team, _p("H", 52.5, 34.0, team="away"), _p("S", 40.0, 34.0, poste="BU", team="away")], low, 0.0)
    high = BallState(position=Vec2(85.0, 34.0), velocity=Vec2(0.0, 0.0), holder=None)
    bloc.update([*team, _p("H", 85.0, 34.0, team="away"), _p("S", 40.0, 34.0, poste="BU", team="away")], high, 1.0)
    lagging = bloc.reference(slow, high.position, DEFENSE_PLACEE, 1.0).x
    alert = bloc.reference(next(p for p in team if p.name == "D1"), high.position, DEFENSE_PLACEE, 1.0).x
    assert lagging < alert - 1.0  # le retardataire est resté plus près de son but : il joue l'attaquant en jeu


# --- Place avec ballon propre au rôle (ticket v2-realisme/02d) ---

def _with_roles(roles: dict[str, str], team: list[PlayerState] = TEAM) -> list[PlayerState]:
    return [dataclasses.replace(p, role=roles.get(p.name, p.role)) for p in team]


def test_every_role_has_a_place_with_the_ball() -> None:
    from v2engine.bloc import ROLE_PLACE_WITH_BALL
    from v2engine.roles import ROLES
    assert set(ROLES) == set(ROLE_PLACE_WITH_BALL)  # 0 explicite plutôt qu'oubli


def test_an_attacking_full_back_stands_higher_than_a_defensive_one_with_the_ball() -> None:
    team = _with_roles({"D0": "piston", "D3": "latéral défensif"})
    bloc = Bloc.from_players(team)
    high = bloc.reference(next(p for p in team if p.name == "D0"), CENTER_BALL, POSSESSION_INSTALLEE)
    low = bloc.reference(next(p for p in team if p.name == "D3"), CENTER_BALL, POSSESSION_INSTALLEE)
    assert high.x - low.x >= 12.0  # 15 m de décalage de départ, un peu comprimés par le bloc


def test_roles_redistribute_inside_the_block_without_moving_or_resizing_it() -> None:
    plain = Bloc.from_players(TEAM)
    team = _with_roles({"D0": "piston", "D3": "latéral défensif", "M1": "récupérateur", "M2": "box to box",
                        "A0": "pivot", "A1": "buteur axial"})
    bloc = Bloc.from_players(team)
    pts = [bloc.reference(p, CENTER_BALL, POSSESSION_INSTALLEE) for p in team if p.poste != "GK"]
    ref = [plain.reference(p, CENTER_BALL, POSSESSION_INSTALLEE) for p in TEAM if p.poste != "GK"]
    # depuis le ticket v2-realisme/09j, le bloc avec ballon se cale sur sa dernière ligne (et non plus sur son centre) :
    # les rôles ne déplacent pas cette ligne
    assert math.isclose(min(p.x for p in pts), min(p.x for p in ref), abs_tol=1e-6)
    assert math.isclose(min(p.x for p in pts), with_ball_line("home", CENTER_BALL.x), abs_tol=1e-6)
    assert math.isclose(max(p.x for p in pts) - min(p.x for p in pts), SHAPE_WITH_BALL[0], abs_tol=1e-6)
    assert math.isclose(max(p.y for p in pts) - min(p.y for p in pts), SHAPE_WITH_BALL[1], abs_tol=1e-6)


def test_an_inverted_winger_cuts_inside_and_a_touchline_winger_stays_wide() -> None:
    team = _with_roles({"M0": "ailier de couloir", "M3": "ailier intérieur"})
    bloc = Bloc.from_players(team)
    wide = bloc.reference(next(p for p in team if p.name == "M0"), CENTER_BALL, POSSESSION_INSTALLEE)
    inside = bloc.reference(next(p for p in team if p.name == "M3"), CENTER_BALL, POSSESSION_INSTALLEE)
    assert abs(wide.y - 34.0) > abs(inside.y - 34.0) + 8.0


def test_a_role_without_a_place_does_not_change_anything() -> None:
    # un rôle absent de la table, ou vide, garde la place d'avant 02d / 02e, avec ou sans ballon
    team = _with_roles({"D0": "rôle inconnu", "M1": ""})
    plain, roled = Bloc.from_players(TEAM), Bloc.from_players(team)
    for situation in (DEFENSE_PLACEE, POSSESSION_INSTALLEE):
        for p, q in zip(TEAM, team):
            assert roled.reference(q, CENTER_BALL, situation) == plain.reference(p, CENTER_BALL, situation)


def test_every_role_has_a_place_without_the_ball() -> None:
    from v2engine.bloc import ROLE_PLACE_WITHOUT_BALL
    from v2engine.roles import ROLES
    assert set(ROLES) == set(ROLE_PLACE_WITHOUT_BALL)


def test_a_touchline_winger_drops_and_a_centre_forward_stays_high_without_the_ball() -> None:
    # ticket 02e, critère 1 : même joueur, deux rôles, même scène
    def height(role: str) -> float:
        team = _with_roles({"M0": role})
        return Bloc.from_players(team).reference(next(p for p in team if p.name == "M0"), CENTER_BALL, DEFENSE_PLACEE).x
    assert height("avant-centre") - height("ailier de couloir") >= 8.0


def test_a_wing_back_tracks_back_to_the_defensive_line_without_the_ball() -> None:
    # critère 2 : piston placé au milieu contre latéral défensif ; il rejoint la ligne des défenseurs sans la dépasser
    team = _with_roles({"M0": "piston", "M3": "latéral défensif"})
    bloc = Bloc.from_players(team)
    xs = {p.name: bloc.reference(p, CENTER_BALL, DEFENSE_PLACEE).x for p in team}
    assert xs["M3"] - xs["M0"] >= 8.0
    assert xs["M0"] >= min(xs[f"D{i}"] for i in range(4)) - 1e-9  # jamais derrière la dernière ligne


def test_roles_redistribute_inside_the_low_block_without_moving_or_resizing_it() -> None:
    # critère 3 : 32 x 40 m, centre conservé
    plain = Bloc.from_players(TEAM)
    team = _with_roles({"D0": "piston", "D3": "latéral défensif", "M0": "ailier de couloir", "M1": "récupérateur",
                        "M2": "ailier intérieur", "A0": "pivot", "A1": "buteur axial"})
    bloc = Bloc.from_players(team)
    pts = [bloc.reference(p, CENTER_BALL, DEFENSE_PLACEE) for p in team if p.poste != "GK"]
    ref = [plain.reference(p, CENTER_BALL, DEFENSE_PLACEE) for p in TEAM if p.poste != "GK"]
    assert math.isclose(sum(p.x for p in pts), sum(p.x for p in ref), abs_tol=1e-6)
    assert math.isclose(sum(p.y for p in pts), sum(p.y for p in ref), abs_tol=1e-6)
    assert math.isclose(max(p.x for p in pts) - min(p.x for p in pts), SHAPE_WITHOUT_BALL[0], abs_tol=1e-6)
    assert math.isclose(max(p.y for p in pts) - min(p.y for p in pts), SHAPE_WITHOUT_BALL[1], abs_tol=1e-6)


def test_the_low_block_keeps_the_defensive_line_for_both_teams() -> None:
    # critère 4 : la dernière ligne sans ballon reste celle des défenseurs, équipe visiteuse en miroir
    roles = {"M0": "piston", "M1": "récupérateur", "M2": "ailier de couloir", "M3": "sentinelle"}
    home = _with_roles(roles)
    away = [dataclasses.replace(p, team="away", home_target=Vec2(105.0 - p.home_target.x, p.home_target.y),
                                position=Vec2(105.0 - p.position.x, p.position.y)) for p in home]
    for team, deep in ((home, min), (away, max)):
        bloc = Bloc.from_players(team)
        xs = {p.name: bloc.reference(p, CENTER_BALL, DEFENSE_PLACEE).x for p in team if p.poste != "GK"}
        defenders = [xs[f"D{i}"] for i in range(4)]
        assert math.isclose(deep(xs.values()), deep(defenders), abs_tol=1e-9)


def test_the_away_team_is_mirrored() -> None:
    away = [dataclasses.replace(p, team="away", role="piston" if p.name == "D0" else "",
                                home_target=Vec2(105.0 - p.home_target.x, p.home_target.y),
                                position=Vec2(105.0 - p.position.x, p.position.y)) for p in TEAM]
    bloc = Bloc.from_players(away)
    piston = next(p for p in away if p.name == "D0")
    plain = Bloc.from_players([dataclasses.replace(p, role="") for p in away])
    roleless = dataclasses.replace(piston, role="")
    assert bloc.reference(piston, CENTER_BALL, POSSESSION_INSTALLEE).x < plain.reference(roleless, CENTER_BALL, POSSESSION_INSTALLEE).x


def _last_line(bloc: Bloc, team: list[PlayerState], ball: Vec2, situation: str, now_s: float = 0.0) -> float:
    """Dernière ligne de référence (joueur de champ le plus bas), depuis le but de l'équipe."""
    xs = [bloc.reference(p, ball, situation, now_s).x for p in team if p.poste != "GK"]
    return min(xs) if team[0].team == "home" else 105.0 - max(xs)


def test_with_the_ball_the_block_sits_on_a_line_that_follows_the_ball() -> None:
    # Ticket v2-realisme/09j : H = 40 + 0,5 x (ballon - 52,5), depuis son but ; valeurs du ticket à 0,5 m près.
    away_team = [_p(p.name + "x", 105.0 - p.position.x, p.position.y, poste=p.poste, team="away") for p in TEAM]
    for ball_m, expected in ((17.0, 22.25), (47.0, 37.25), (76.0, 51.75), (92.0, 55.0)):
        for team, ball_x in ((TEAM, ball_m), (away_team, 105.0 - ball_m)):
            bloc = Bloc.from_players(team)
            holder = team[6]  # un milieu porteur, pas le gardien
            ball = BallState(position=Vec2(ball_x, 30.0), velocity=Vec2(0.0, 0.0), holder=holder.name)
            bloc.update(team, ball, 0.0)  # pas d'adversaire : la ligne sans ballon n'est pas calculée, celle avec ballon oui
            assert abs(_last_line(bloc, team, ball.position, POSSESSION_INSTALLEE) - expected) <= 0.5, (ball_m, team[0].team)


def test_the_line_with_the_ball_keeps_its_floor_and_ceiling() -> None:
    assert with_ball_line("home", 0.0) == LINE_MIN_WITH_BALL_M == 15.0  # ballon sur sa ligne de but : 13,75 -> 15
    assert with_ball_line("home", 105.0) == LINE_MAX_WITH_BALL_M == 55.0
    assert with_ball_line("away", 105.0) == 15.0 and with_ball_line("away", 0.0) == 55.0
    assert math.isclose(with_ball_line("home", 82.5), 55.0) and with_ball_line("home", 82.0) < 55.0
    bloc = Bloc.from_players(TEAM)
    assert abs(_last_line(bloc, TEAM, Vec2(2.0, 34.0), POSSESSION_INSTALLEE) - 15.0) <= 1e-9
    assert abs(_last_line(bloc, TEAM, Vec2(103.0, 34.0), POSSESSION_INSTALLEE) - 55.0) <= 1e-9


def test_with_the_ball_the_line_ignores_pressure_and_the_deepest_rival() -> None:
    # 09j : ni pression sur le porteur ni attaquant adverse le plus avancé ; la ligne sans ballon, elle, les lit encore
    rival = _p("R", 30.0, 34.0, poste="BU", team="away")  # attaquant adverse bas : il tirerait la ligne sans ballon vers lui
    players = TEAM + [rival]
    bloc = Bloc.from_players(players)
    ball = BallState(position=Vec2(60.0, 34.0), velocity=Vec2(0.0, 0.0), holder="M1")
    bloc.update(players, ball, 0.0)
    assert math.isclose(bloc.lines_ball["home"], 40.0 + 7.5 * 0.5)
    assert bloc.lines["home"] < bloc.lines_ball["home"]


def test_a_low_teamwork_player_follows_the_line_with_the_ball_late() -> None:
    bloc = Bloc.from_players(TEAM)
    slow = dataclasses.replace(TEAM[1], attributes={"Teamwork": 11})  # retard 1,5 s
    quick = dataclasses.replace(TEAM[1], attributes={"Teamwork": 99})
    for k in range(16):  # le ballon avance de 2 m par dixième de seconde pendant 1,5 s
        ball = BallState(position=Vec2(40.0 + 2.0 * k, 34.0), velocity=Vec2(0.0, 0.0), holder="M1")
        bloc.update(TEAM, ball, 0.1 * k)
    now, where = 1.5, ball.position
    assert math.isclose(bloc.reference(quick, where, POSSESSION_INSTALLEE, now).x, with_ball_line("home", where.x))
    assert bloc.reference(slow, where, POSSESSION_INSTALLEE, now).x < bloc.reference(quick, where, POSSESSION_INSTALLEE, now).x - 10.0


def _line_levels(team: list[PlayerState], ball: Vec2 = CENTER_BALL) -> tuple[float, float, float, float]:
    """Hauteurs des lignes avec ballon (centraux, milieux axiaux, avant-centres) et longueur du bloc (ticket 09e)."""
    bloc = Bloc.from_players(team)
    ref = {p.name: bloc.reference(p, ball, POSSESSION_INSTALLEE).x for p in team if p.poste != "GK"}
    mean = lambda postes: sum(ref[p.name] for p in team if p.poste in postes) / sum(1 for p in team if p.poste in postes)  # noqa: E731
    return mean({"DC"}), mean({"MDC", "MC", "MOC"}), mean({"BU"}), max(ref.values()) - min(ref.values())


def test_a_stretched_shape_brings_its_line_gaps_back_to_the_nearest_bound() -> None:
    # Ticket v2-realisme/09e : forme très étirée (30 m entre chaque ligne, 21 m après mise à l'échelle) : défense-milieu
    # ramené à 15 m, milieu-attaque à 20 m ; la dernière ligne reste sur H, le bloc raccourcit.
    team = ([_p("GK", 5, 34, poste="GK")] + [_p(f"D{i}", 10, y, poste="DC") for i, y in enumerate((16, 28, 40, 52))]
            + [_p(f"M{i}", 40, y) for i, y in enumerate((16, 28, 40, 52))] + [_p(f"A{i}", 70, y, poste="BU") for i, y in enumerate((28, 40))])
    d, m, a, length = _line_levels(team)
    assert math.isclose(d, with_ball_line("home", CENTER_BALL.x))
    assert math.isclose(m - d, GAP_DEF_MID_M[1]) and math.isclose(a - m, GAP_MID_ATT_M[1])
    assert math.isclose(length, 35.0)


def test_a_compact_shape_opens_its_gaps_to_the_lower_bound_and_a_gap_inside_the_bounds_does_not_move() -> None:
    team = ([_p("GK", 5, 34, poste="GK")] + [_p(f"D{i}", 18, y, poste="DC") for i, y in enumerate((16, 28, 40, 52))]
            + [_p(f"M{i}", 22, y) for i, y in enumerate((16, 28, 40, 52))] + [_p(f"A{i}", 45, y, poste="BU") for i, y in enumerate((28, 40))])
    d, m, a, _ = _line_levels(team)  # 4 m puis 23 m de départ, x 42/27 : 6,2 puis 35,8 m
    assert math.isclose(m - d, GAP_DEF_MID_M[0]) and math.isclose(a - m, GAP_MID_ATT_M[1])
    inside = ([_p("GK", 5, 34, poste="GK")] + [_p(f"D{i}", 18, y, poste="DC") for i, y in enumerate((16, 28, 40, 52))]
              + [_p(f"M{i}", 26, y) for i, y in enumerate((16, 28, 40, 52))] + [_p(f"A{i}", 45, y, poste="BU") for i, y in enumerate((28, 40))])
    d, m, a, length = _line_levels(inside)  # 8 m puis 19 m, x 42/27 : 12,4 m (dans 10-15) puis 29,6 m (ramené à 20)
    assert math.isclose(m - d, 8.0 * 42.0 / 27.0) and math.isclose(a - m, GAP_MID_ATT_M[1])


def test_players_between_two_lines_keep_their_order_and_the_away_team_is_mirrored() -> None:
    team = ([_p("GK", 5, 34, poste="GK")] + [_p(f"D{i}", 10, y, poste="DC") for i, y in enumerate((28, 40))]
            + [_p("LB", 25, 10, poste="LB"), _p("RB", 25, 58, poste="RB")]
            + [_p(f"M{i}", 40, y) for i, y in enumerate((16, 28, 40, 52))] + [_p(f"A{i}", 70, y, poste="BU") for i, y in enumerate((28, 40))])
    bloc = Bloc.from_players(team)
    x = {p.name: bloc.reference(p, CENTER_BALL, POSSESSION_INSTALLEE).x for p in team if p.poste != "GK"}
    assert x["D0"] < x["LB"] < x["M0"]  # latéral à mi-chemin des deux lignes : il y reste
    assert math.isclose(x["LB"] - x["D0"], (x["M0"] - x["D0"]) / 2.0)
    away = [_p(p.name, 105.0 - p.position.x, p.position.y, poste=p.poste, team="away") for p in team]
    away_bloc = Bloc.from_players(away)
    mirrored = {p.name: away_bloc.reference(p, Vec2(105.0 - CENTER_BALL.x, 34.0), POSSESSION_INSTALLEE).x for p in away if p.poste != "GK"}
    assert all(math.isclose(mirrored[n], 105.0 - x[n]) for n in x)


def test_a_team_without_a_centre_forward_only_constrains_defence_to_midfield() -> None:
    team = ([_p("GK", 5, 34, poste="GK")] + [_p(f"D{i}", 10, y, poste="DC") for i, y in enumerate((16, 28, 40, 52))]
            + [_p(f"M{i}", 40, y) for i, y in enumerate((16, 28, 40, 52))] + [_p(f"A{i}", 70, y, poste="AG") for i, y in enumerate((28, 40))])
    bloc = Bloc.from_players(team)
    x = {p.name: bloc.reference(p, CENTER_BALL, POSSESSION_INSTALLEE).x for p in team if p.poste != "GK"}
    assert math.isclose(x["M0"] - x["D0"], GAP_DEF_MID_M[1])
    assert math.isclose(x["A0"] - x["M0"], 30.0 * 42.0 / 60.0)  # pas d'avant-centre : l'attaque garde son écart


# --- Placement de construction (ticket v2-realisme/25b) -------------------------------------------------------------
# 4-3-3 avec rôles : centraux à 25 et 43 m (18 m d'écart, comme mesuré en match avant 25b), latéraux à 12 et 56 m, sentinelle dans l'axe, deux relayeurs.
def _r(name: str, x: float, y: float, poste: str, role: str, team: str = "home") -> PlayerState:
    return dataclasses.replace(_p(name, x, y, poste=poste, team=team), role=role)


BUILD_TEAM = [_r("GK", 5, 34, "GK", "gardien"), _r("CB1", 18, 25, "DC", "défenseur central"),
              _r("CB2", 18, 43, "DC", "défenseur central"), _r("LB", 20, 12, "LB", "latéral"),
              _r("RB", 20, 56, "RB", "latéral"), _r("DM", 28, 34, "MDC", "sentinelle"),
              _r("CM1", 34, 24, "MC", "milieu relayeur"), _r("CM2", 34, 44, "MC", "mezzala"),
              _r("LW", 46, 12, "AG", "ailier de couloir"), _r("RW", 46, 56, "AD", "ailier intérieur"),
              _r("ST", 50, 34, "BU", "avant-centre")]
_SPOT = Vec2(5.5, 34.0)


def _goal_kick(rivals: list[PlayerState] = ()) -> tuple[Bloc, list[PlayerState], BallState]:
    from v2engine.restart import GOAL_KICK, Restart
    players = BUILD_TEAM + list(rivals)
    bloc = Bloc.from_players(players)
    ball = BallState(position=_SPOT, velocity=Vec2(0.0, 0.0),
                     restart=Restart(GOAL_KICK, "home", _SPOT, "GK", 25.0, 0.0))
    bloc.update(players, ball, 0.0)
    return bloc, players, ball


def _ref(bloc: Bloc, name: str, ball: Vec2 = _SPOT, team: list[PlayerState] = BUILD_TEAM) -> Vec2:
    player = next(p for p in team if p.name == name)
    return bloc.reference(player, ball, POSSESSION_INSTALLEE)


def _cb_gap(bloc: Bloc) -> float:
    return abs(_ref(bloc, "CB2").y - _ref(bloc, "CB1").y)


def test_every_build_up_role_is_a_known_role() -> None:
    from v2engine.bloc import ROLE_PLACE_BUILD_UP
    from v2engine.roles import ROLES
    assert set(ROLE_PLACE_BUILD_UP) <= set(ROLES)


def test_on_a_goal_kick_without_pressing_the_centre_backs_split_and_the_holding_midfielder_drops() -> None:
    bloc, _, _ = _goal_kick()
    assert bloc.build_up == {"home": 1.0}
    plain = Bloc.from_players(BUILD_TEAM)  # même scène, sans phase de construction
    assert _cb_gap(bloc) >= 32.0 and math.isclose(_cb_gap(bloc), _cb_gap(plain) + 16.0)
    assert _ref(bloc, "DM").distance_to(BUILD_TEAM[0].position) <= 18.0
    assert math.isclose(_ref(bloc, "DM").x, _ref(plain, "DM").x - 6.0)
    for name in ("LB", "RB"):  # les latéraux montent de 6 m et s'ouvrent, jamais à moins de 2 m de la touche
        assert math.isclose(_ref(bloc, name).x, _ref(plain, name).x + 6.0)
        assert 2.0 - 1e-9 <= _ref(bloc, name).y <= 66.0 + 1e-9
        assert abs(_ref(bloc, name).y - 34.0) > abs(_ref(plain, name).y - 34.0)
    for name in ("CM1", "CM2"):  # demi-espaces : 4 m plus loin de l'axe
        assert math.isclose(abs(_ref(bloc, name).y - 34.0), abs(_ref(plain, name).y - 34.0) + 4.0)
    for name in ("LW", "RW", "ST"):  # rôles hors de la table : rien ne change
        assert _ref(bloc, name) == _ref(plain, name)


def test_under_a_high_press_the_same_players_stay_closer_to_the_holder() -> None:
    free, _, _ = _goal_kick()
    rivals = [_p(f"R{i}", 25.0, y, poste="BU", team="away") for i, y in enumerate((20, 30, 40, 50))]
    pressed, _, _ = _goal_kick(rivals)
    assert pressed.build_up == {"home": 0.5}
    assert _cb_gap(pressed) <= _cb_gap(free) - 6.0
    three, _, _ = _goal_kick(rivals[:3])  # entre 2 et 4 adversaires : écartement intermédiaire
    assert three.build_up == {"home": 0.75} and _cb_gap(pressed) < _cb_gap(three) < _cb_gap(free)


def test_the_build_up_phase_follows_the_holder_and_lasts_through_the_pass() -> None:
    bloc = Bloc.from_players(BUILD_TEAM)
    def tick(holder: str | None, x: float) -> None:  # le porteur est placé sur le ballon
        players = [dataclasses.replace(p, position=Vec2(x, 30.0)) if p.name == holder else p for p in BUILD_TEAM]
        bloc.update(players, BallState(position=Vec2(x, 30.0), velocity=Vec2(0.0, 0.0), holder=holder), 0.0)
    tick("CB1", 18.0)
    assert bloc.in_build_up("home")
    tick(None, 25.0)  # passe en vol : la phase continue jusqu'au contrôle suivant
    assert bloc.in_build_up("home")
    tick("CM1", 34.0)  # un milieu contrôle : fin de la construction
    assert not bloc.in_build_up("home")
    tick(None, 40.0)
    assert not bloc.in_build_up("home")
    tick("CB1", 36.0)  # défenseur au-delà de 35 m de son but : pas de construction
    assert not bloc.in_build_up("home")
    tick("GK", 5.0)
    assert bloc.in_build_up("home") and not bloc.in_build_up("away")


def test_the_build_up_place_only_applies_with_the_ball_and_is_mirrored_for_the_away_team() -> None:
    bloc, _, _ = _goal_kick()
    plain = Bloc.from_players(BUILD_TEAM)
    cb = BUILD_TEAM[1]
    assert bloc.reference(cb, _SPOT, DEFENSE_PLACEE) == plain.reference(cb, _SPOT, DEFENSE_PLACEE)
    from v2engine.restart import GOAL_KICK, Restart
    away = [dataclasses.replace(p, team="away", position=Vec2(105.0 - p.position.x, p.position.y),
                                home_target=Vec2(105.0 - p.home_target.x, p.home_target.y)) for p in BUILD_TEAM]
    spot = Vec2(105.0 - _SPOT.x, _SPOT.y)
    mirrored = Bloc.from_players(away)
    mirrored.update(away, BallState(position=spot, velocity=Vec2(0.0, 0.0),
                                    restart=Restart(GOAL_KICK, "away", spot, "GK", 25.0, 0.0)), 0.0)
    for name in ("CB1", "CB2", "LB", "DM", "CM2"):
        home_ref, away_ref = _ref(bloc, name), _ref(mirrored, name, spot, away)
        assert math.isclose(away_ref.x, 105.0 - home_ref.x) and math.isclose(away_ref.y, home_ref.y)


def test_the_build_up_phase_is_written_in_the_traced_reason() -> None:
    bloc, players, ball = _goal_kick()
    intention = think(BUILD_TEAM[1], ball, players, 0.0, {}, POSSESSION_INSTALLEE, bloc)
    assert intention.reason.endswith("(construction)") and intention.target == bloc.target(
        BUILD_TEAM[1], _SPOT, POSSESSION_INSTALLEE, 0.0)
    plain = Bloc.from_players(BUILD_TEAM)
    assert "construction" not in think(BUILD_TEAM[1], ball, players, 0.0, {}, POSSESSION_INSTALLEE, plain).reason

"""Tests du bloc de référence dynamique V2 (ticket v2-collectif/04) : le bloc suit le ballon, change de forme selon
la situation, Positioning règle l'erreur de placement et Teamwork l'écart toléré. Et la hauteur de la ligne défensive
sans ballon (ticket v2-collectif/05)."""

from __future__ import annotations

import math
import random

from v2engine.ball_state import BallState
from v2engine.bloc import (
    BLOCK_SHIFT, LINE_HEIGHT_M, LINE_LAG_MAX_S, POSSESSION_ADVANCE_M, PRESSURE_STEP_M, SHAPE_WITH_BALL, SHAPE_WITHOUT_BALL,
    Bloc, line_lag_s, positioning_error_m, teamwork_tolerance_m,
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
    assert math.isclose(length, SHAPE_WITH_BALL[0]) and math.isclose(width, SHAPE_WITH_BALL[1])


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
    for note, error, tolerance in ((99, 0.5, 2.0), (55, 2.0, 5.0), (11, 4.0, 9.0)):
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
    assert math.isclose(with_ball.x - without.x, POSSESSION_ADVANCE_M)
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
    for note, lag in ((99, 0.0), (55, 0.75), (11, 1.5)):
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

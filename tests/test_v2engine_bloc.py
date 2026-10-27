"""Tests du bloc de référence dynamique V2 (ticket v2-collectif/04) : le bloc suit le ballon, change de forme selon
la situation, Positioning règle l'erreur de placement et Teamwork l'écart toléré."""

from __future__ import annotations

import math
import random

from v2engine.ball_state import BallState
from v2engine.bloc import BLOCK_SHIFT, POSSESSION_ADVANCE_M, SHAPE_WITH_BALL, SHAPE_WITHOUT_BALL, Bloc, positioning_error_m, teamwork_tolerance_m
from v2engine.cerveau import REPLACEMENT, think
from v2engine.geometry import Vec2
from v2engine.movement import PlayerState
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

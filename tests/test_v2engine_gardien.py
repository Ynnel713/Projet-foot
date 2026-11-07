"""Gardien (tickets v2-realisme/03a, 03b et 03c) : placement sur la bissectrice de l'angle ballon-poteaux, plus avancé
quand la ligne défensive est haute et le ballon loin."""

from __future__ import annotations

import math
from dataclasses import replace

import pytest

from tests.scenes import Scene, player, run, seed_scene
from v2engine import cerveau, gardien, movement
from v2engine.ball_state import BallState
from v2engine.bloc import Bloc
from v2engine.geometry import PENALTY_AREA_DEPTH_M, PENALTY_AREA_WIDTH_M, PITCH_LENGTH_M, Vec2

GOAL_HOME, GOAL_AWAY = Vec2(0.0, 34.0), Vec2(PITCH_LENGTH_M, 34.0)


def _keeper(team: str = "home", x: float = 5.0):
    return player("G", team, x, 34.0, "GK")


def _angle(a: Vec2, b: Vec2, c: Vec2) -> float:
    """Angle (rad) en `a` entre les directions vers `b` et `c`."""
    u, v = (b - a).normalized(), (c - a).normalized()
    return math.acos(max(-1.0, min(1.0, u.x * v.x + u.y * v.y)))


def test_the_point_is_on_the_bisector_of_the_angle_between_the_posts() -> None:
    for ball in (Vec2(30, 34), Vec2(25, 12), Vec2(20, 50), Vec2(45, 30)):
        point = gardien.bisector_point(_keeper(), ball)
        post_low, post_high = Vec2(0.0, 34.0 - 3.66), Vec2(0.0, 34.0 + 3.66)
        assert _angle(ball, post_low, point) == pytest.approx(_angle(ball, point, post_high), abs=0.01)


def test_depth_grows_with_the_ball_distance_and_stays_in_the_area() -> None:
    depths = [gardien.bisector_point(_keeper(), Vec2(x, 34.0)).x for x in (4.0, 12.0, 20.0, 30.0, 40.0, 60.0)]
    assert depths[0] == pytest.approx(gardien.DEPTH_M[0])  # ballon à 4 m de sa ligne : près de sa ligne
    assert depths[1] == pytest.approx(gardien.DEPTH_M[0]) and depths[4] == pytest.approx(gardien.DEPTH_M[1])
    assert depths[5] == pytest.approx(gardien.DEPTH_M[1])
    assert depths[1] < depths[2] < depths[3] < depths[4]
    for ball in (Vec2(50, 2), Vec2(2, 2), Vec2(3, 66), Vec2(0.3, 34), Vec2(40, 34)):
        p = gardien.bisector_point(_keeper(), ball)
        assert 0.0 <= p.x <= PENALTY_AREA_DEPTH_M and abs(p.y - 34.0) <= PENALTY_AREA_WIDTH_M / 2.0


def test_the_keeper_follows_the_ball_side_symmetrically_and_for_both_teams() -> None:
    left, right = gardien.bisector_point(_keeper(), Vec2(25, 10)), gardien.bisector_point(_keeper(), Vec2(25, 58))
    assert left.y < 34.0 < right.y and left.x == pytest.approx(right.x)
    assert 34.0 - left.y == pytest.approx(right.y - 34.0)
    # l'équipe visiteuse défend x = 105 : image dans un miroir de l'équipe domicile
    away = gardien.bisector_point(_keeper("away", PITCH_LENGTH_M - 5.0), Vec2(PITCH_LENGTH_M - 25, 10))
    assert away.x == pytest.approx(PITCH_LENGTH_M - left.x) and away.y == pytest.approx(left.y)


def test_a_ball_beside_the_goal_line_puts_the_keeper_at_the_minimum_depth() -> None:
    near_post = gardien.bisector_point(_keeper(), Vec2(3.0, 10.0))
    assert near_post.x == pytest.approx(gardien.DEPTH_M[0])  # le ballon est plus près de la ligne que 4 m : profondeur minimale


def test_the_placement_state_targets_the_bisector_point() -> None:
    keeper, far = _keeper(), player("D", "home", 30.0, 34.0, "DC")
    ball = BallState(position=Vec2(40.0, 20.0), velocity=Vec2(0.0, 0.0))
    intention = cerveau.think(keeper, ball, [keeper, far], 1.0, {})
    assert intention.reason.startswith("placement") and intention.target == gardien.bisector_point(keeper, ball.position)


@pytest.mark.parametrize("ball_at", [Vec2(52.0, 34.0), Vec2(30.0, 12.0), Vec2(30.0, 56.0), Vec2(45.0, 20.0)])
def test_the_keeper_reaches_the_bisector_point_within_three_seconds(ball_at: Vec2) -> None:
    # ballon libre et immobile ; un coéquipier plus proche du ballon, qui ne peut pas le toucher, laisse le gardien en
    # état de placement (le plus proche de son équipe sortirait)
    keeper, mate = _keeper(), player("D", "home", ball_at.x - 3.0, ball_at.y, "DC")
    ball = BallState(position=ball_at, velocity=Vec2(0.0, 0.0))
    ball.control_ban_until_s[mate.name] = 99.0
    scene = Scene([keeper, mate], ball, runs={}, intentions={})
    run(scene, 3.0)
    assert scene.get("G").position.distance_to(gardien.bisector_point(keeper, ball_at)) < 0.5


def test_a_higher_line_pushes_the_keeper_forward_when_the_ball_is_far() -> None:
    far = Vec2(60.0, 34.0)
    low, high = gardien.bisector_point(_keeper(), far, 20.0).x, gardien.bisector_point(_keeper(), far, 40.0).x
    assert low == pytest.approx(gardien.DEPTH_M[1])  # ligne à 20 m : 0,4 x 20 = 8 m, pas plus loin que le 03b
    assert high == pytest.approx(gardien.DEPTH_LINE_MAX_M) and high > low + 5.0
    assert gardien.bisector_point(_keeper(), far, None).x == pytest.approx(low)  # sans ligne connue : le 03b


def test_the_depth_grows_with_the_line_and_stays_capped_inside_the_area() -> None:
    depths = [gardien.bisector_point(_keeper(), Vec2(60.0, 34.0), line).x for line in (5.0, 20.0, 25.0, 30.0, 35.0, 40.0, 55.0)]
    assert depths == sorted(depths) and depths[2] < depths[3] < depths[4]
    assert max(depths) == pytest.approx(gardien.DEPTH_LINE_MAX_M) and max(depths) < PENALTY_AREA_DEPTH_M


def test_the_line_counts_in_proportion_to_the_ball_distance_and_not_at_all_near_the_goal() -> None:
    near = Vec2(12.0, 34.0)  # ballon à 12 m : la ligne ne change rien (la bissectrice du 03b reste entière)
    assert gardien.bisector_point(_keeper(), near, 45.0) == gardien.bisector_point(_keeper(), near)
    middle = [gardien.bisector_point(_keeper(), Vec2(x, 34.0), 40.0).x for x in (12.0, 20.0, 30.0, 40.0)]
    assert middle == sorted(middle) and middle[0] == pytest.approx(gardien.DEPTH_M[0])


def test_the_point_stays_on_the_bisector_with_a_high_line() -> None:
    for ball in (Vec2(55, 34), Vec2(45, 12), Vec2(48, 60)):
        point = gardien.bisector_point(_keeper(), ball, 45.0)
        post_low, post_high = Vec2(0.0, 34.0 - 3.66), Vec2(0.0, 34.0 + 3.66)
        assert _angle(ball, post_low, point) == pytest.approx(_angle(ball, point, post_high), abs=0.01)


def test_the_brain_reads_the_line_of_the_bloc_of_its_own_team_at_that_instant() -> None:
    keeper, mate = _keeper(), player("D", "home", 40.0, 34.0, "DC")
    ball = BallState(position=Vec2(70.0, 34.0), velocity=Vec2(0.0, 0.0))
    bloc = Bloc(shapes={}, lines={"home": 40.0, "away": 10.0})
    with_line = cerveau.think(keeper, ball, [keeper, mate], 1.0, {}, bloc=bloc)
    assert with_line.target == gardien.bisector_point(keeper, ball.position, 40.0) and with_line.target.x > gardien.DEPTH_M[1]
    without = cerveau.think(keeper, ball, [keeper, mate], 1.0, {})
    assert without.target == gardien.bisector_point(keeper, ball.position)
    away = player("G2", "away", PITCH_LENGTH_M - 5.0, 34.0, "GK")  # l'équipe visiteuse lit sa propre ligne (10 m)
    other = cerveau.think(away, ball, [away, player("D2", "away", 80.0, 34.0, "DC")], 1.0, {}, bloc=bloc)
    assert other.target == gardien.bisector_point(away, ball.position, 10.0)


# --- Sortie sur un ballon libre (ticket v2-realisme/03d) -------------------------------------------------------------
def _loose_ball(at: Vec2, rival_x: float | None, keeper_x: float = 5.0):
    keeper = _keeper(x=keeper_x)
    players = [keeper]
    if rival_x is not None:
        players.append(player("A", "away", rival_x, 34.0, "BU"))
    return keeper, BallState(position=at, velocity=Vec2(0.0, 0.0)), players


def test_the_keeper_rushes_when_the_attacker_is_much_farther_and_stays_when_he_is_closer() -> None:
    keeper, ball, far = _loose_ball(Vec2(25.0, 34.0), rival_x=55.0)  # lui à 20 m du ballon, l'attaquant à 30 m
    assert gardien.race(keeper, ball, far).rush
    out = cerveau.think(keeper, ball, far, 1.0, {})
    assert out.reason.startswith("sortie") and "il arrive en" in out.reason  # décision tracée avec les deux temps
    keeper, ball, close = _loose_ball(Vec2(25.0, 34.0), rival_x=35.0)  # l'attaquant à 10 m
    assert not gardien.race(keeper, ball, close).rush
    stays = cerveau.think(keeper, ball, close, 1.0, {})
    assert stays.reason.startswith("placement") and "arrive avant lui" in stays.reason
    assert stays.target == gardien.bisector_point(keeper, ball.position)


def test_the_margin_decides_between_two_attackers_a_little_before_and_after() -> None:
    from v2engine.movement import max_speed_mps
    speed = max_speed_mps(60)
    for gap_s, expected in ((gardien.RUSH_MARGIN_S - 0.2, False), (gardien.RUSH_MARGIN_S + 0.2, True)):
        keeper, ball, players = _loose_ball(Vec2(25.0, 34.0), rival_x=25.0 + 20.0 + gap_s * speed)  # même vitesse et même montée
        assert gardien.race(keeper, ball, players).rush is expected


def test_no_rush_beyond_the_distance_cap_even_without_any_attacker() -> None:
    near = _loose_ball(Vec2(gardien.RUSH_MAX_FROM_GOAL_M - 3.0, 34.0), rival_x=None, keeper_x=20.0)
    far = _loose_ball(Vec2(gardien.RUSH_MAX_FROM_GOAL_M + 3.0, 34.0), rival_x=None, keeper_x=20.0)
    assert gardien.race(near[0], near[1], near[2]).rush and not gardien.race(far[0], far[1], far[2]).rush
    assert "trop loin de son but" in cerveau.think(far[0], far[1], far[2], 1.0, {}).reason


def test_the_rival_goalkeeper_does_not_count_as_a_rival_and_the_race_is_mirrored_for_the_away_team() -> None:
    keeper, ball, players = _loose_ball(Vec2(25.0, 34.0), rival_x=None)
    players.append(player("G2", "away", 24.0, 34.0, "GK"))  # le gardien adverse, tout près : ignoré
    assert gardien.race(keeper, ball, players).rush
    away = player("G", "away", PITCH_LENGTH_M - 5.0, 34.0, "GK")
    mirror = [away, player("A", "home", PITCH_LENGTH_M - 55.0, 34.0, "BU")]
    mirror_ball = BallState(position=Vec2(PITCH_LENGTH_M - 25.0, 34.0), velocity=Vec2(0.0, 0.0))
    assert gardien.race(away, mirror_ball, mirror).rush
    assert gardien.race(away, mirror_ball, [away, player("A", "home", PITCH_LENGTH_M - 35.0, 34.0, "BU")]).rush is False


def test_the_keeper_does_not_chase_a_pass_of_his_own_team_but_chases_the_same_ball_when_it_is_loose() -> None:
    keeper, ball, players = _loose_ball(Vec2(20.0, 34.0), rival_x=None, keeper_x=8.0)
    mate = player("D", "home", 30.0, 34.0, "DC")
    players.append(mate)
    ball.velocity, ball.receiver, ball.last_pass_team = Vec2(-5.0, 0.0), "D", "home"  # passe de son équipe, en vol
    assert cerveau.think(keeper, ball, players, 1.0, {}).reason.startswith("placement")
    ball.receiver = None  # la passe est ratée : ballon libre
    assert cerveau.think(keeper, ball, players, 1.0, {}).reason.startswith("sortie")



# --- Face-à-face (ticket v2-realisme/03e) ----------------------------------------------------------------------------
def _one_on_one(attacker_x: float = 16.0, attacker_y: float = 34.0, defender: tuple[float, float] | None = None):
    keeper, attacker = _keeper(), player("A", "away", attacker_x, attacker_y, "BU")
    players = [keeper, attacker]
    if defender is not None:
        players.append(player("D", "home", defender[0], defender[1], "DC"))
    return keeper, attacker, players, BallState(position=attacker.position, velocity=Vec2(0.0, 0.0), holder="A")


def test_a_lone_attacker_with_the_ball_in_front_of_goal_puts_the_keeper_in_face_to_face_and_he_comes_out() -> None:
    keeper, attacker, players, ball = _one_on_one()  # attaquant seul à 16 m dans l'axe
    assert gardien.face_to_face(keeper, attacker, players)
    out = cerveau.think(keeper, ball, players, 1.0, {})
    assert out.reason.startswith("face-à-face")  # état tracé
    assert out.target.x == pytest.approx(gardien.face_depth(16.0), abs=0.05) == pytest.approx(4.0, abs=0.05)
    assert out.target.x > gardien.placement(keeper, ball.position).x  # plus avancé que placé
    assert out.target.y == pytest.approx(34.0)  # dans l'axe : sur la bissectrice


def test_a_defender_of_his_team_on_the_shot_line_keeps_the_keeper_in_placement() -> None:
    keeper, attacker, players, ball = _one_on_one(defender=(10.0, 34.0))
    assert not gardien.face_to_face(keeper, attacker, players)
    out = cerveau.think(keeper, ball, players, 1.0, {})
    assert out.reason.startswith("placement") and out.target == gardien.bisector_point(keeper, ball.position)


def test_a_defender_who_stayed_behind_the_attacker_or_far_to_the_side_does_not_break_the_face_to_face() -> None:
    for spot in [(22.0, 34.0), (10.0, 50.0)]:  # derrière le porteur ; loin du cône de tir
        keeper, attacker, players, _ = _one_on_one(defender=spot)
        assert gardien.face_to_face(keeper, attacker, players)


def test_beyond_the_range_or_for_a_goalkeeper_or_a_teammate_there_is_no_face_to_face() -> None:
    keeper, far, players, _ = _one_on_one(gardien.FACE_RANGE_M + 2.0)
    assert not gardien.face_to_face(keeper, far, players)
    keeper, near, players, _ = _one_on_one(gardien.FACE_RANGE_M - 2.0)
    assert gardien.face_to_face(keeper, near, players)
    assert not gardien.face_to_face(keeper, replace(near, poste="GK"), players)  # le gardien adverse n'est pas un attaquant
    assert not gardien.face_to_face(keeper, replace(near, team="home"), players)  # un coéquipier non plus
    assert not gardien.face_to_face(keeper, None, players)


def test_the_face_to_face_is_mirrored_for_the_away_team() -> None:
    keeper = player("G", "away", PITCH_LENGTH_M - 5.0, 34.0, "GK")
    attacker = player("A", "home", PITCH_LENGTH_M - 16.0, 34.0, "BU")
    ball = BallState(position=attacker.position, velocity=Vec2(0.0, 0.0), holder="A")
    out = cerveau.think(keeper, ball, [keeper, attacker], 1.0, {})
    assert out.reason.startswith("face-à-face") and PITCH_LENGTH_M - out.target.x == pytest.approx(4.0, abs=0.05)


def test_the_depth_grows_with_the_attacker_distance_up_to_the_cap_and_is_never_below_the_placement() -> None:
    depths = [gardien.face_depth(d) for d in (8.0, 16.0, 24.0, 30.0)]
    assert depths == sorted(depths) and depths[-1] == gardien.FACE_DEPTH_MAX_M
    keeper = _keeper()
    for ball_at in [Vec2(4.0, 20.0), Vec2(10.0, 34.0), Vec2(20.0, 34.0)]:  # même près de sa ligne, jamais plus reculé
        assert (gardien.bisector_point(keeper, ball_at, depth_m=1.0).x
                >= gardien.bisector_point(keeper, ball_at).x - 1e-9)


def test_the_keeper_comes_out_then_creeps_before_the_shot() -> None:
    # attaquant hors de portée de tir (35 m), ballon aux pieds ; il progresse, le gardien avance puis s'arrête avant le tir
    seed_scene(1)
    keeper, attacker, players, _ = _one_on_one(35.0)
    scene = Scene.full(players, holder="A")
    seen: dict[str, float] = {}

    def shot(s: Scene) -> bool:
        if s.ball.holder != "A":
            seen["speed"], seen["depth"] = s.get("G").velocity.length(), s.get("G").position.x
            return True
        return False

    assert run(scene, 20.0, until=shot)
    assert seen["depth"] > 2.5  # il est sorti de sa ligne
    assert seen["speed"] < gardien.FACE_STOPPED_MPS  # et il est arrêté au moment du tir


def test_the_face_to_face_run_is_deterministic() -> None:
    logs = []
    for _ in range(2):
        seed_scene(1)
        keeper, attacker, players, _ = _one_on_one(35.0)
        scene = Scene.full(players, holder="A")
        run(scene, 6.0)
        logs.append(scene.log)
    assert logs[0] == logs[1]


def test_the_keeper_runs_while_the_attacker_is_far_then_creeps_below_the_stop_threshold() -> None:
    assert gardien.face_intensity(gardien.FACE_SET_DISTANCE_M + 1.0) == gardien.FACE_INTENSITY
    creeping = gardien.face_intensity(gardien.FACE_SET_DISTANCE_M)
    assert 0.0 < creeping < gardien.FACE_INTENSITY
    for pace in (10, 60, 99):  # quel que soit le gardien, les petits pas restent sous le seuil d'arrêt
        assert creeping * movement.max_speed_mps(pace) < gardien.FACE_STOPPED_MPS


# --- Scènes de référence et réserves des clôtures (ticket v2-realisme/03g) -----------------------------------------------
def _replay(others, ball_at: Vec2, holder: str | None = None, line: float | None = None):
    """Le gardien domicile (x = 5) pense dans cette scène ; rend (son intention, le ballon, les joueurs)."""
    keeper = _keeper()
    ball = BallState(position=ball_at, velocity=Vec2(0.0, 0.0), holder=holder)
    players = [keeper, *others]
    bloc = Bloc(shapes={}, lines={"home": line, "away": 10.0}) if line is not None else None
    return cerveau.think(keeper, ball, players, 1.0, {}, bloc=bloc), ball, players


def test_reference_scenes_replayed_give_the_traced_state_and_the_aimed_depth() -> None:
    attacker = lambda x: player("A", "away", x, 34.0, "BU")  # noqa: E731
    defender = player("D", "home", 10.0, 34.0, "DC")
    scenes = [  # (nom, scène, état tracé, profondeur visée)
        ("ballon loin, sans ligne", _replay([attacker(95.0)], Vec2(60.0, 34.0)), "placement", gardien.DEPTH_M[1]),
        ("ballon loin, ligne à 40 m", _replay([attacker(95.0)], Vec2(60.0, 34.0), line=40.0), "placement",
         gardien.DEPTH_LINE_MAX_M),
        ("ballon près du but, tenu par un défenseur", _replay([attacker(95.0), player("D", "home", 8.0, 34.0, "DC")],
                                                           Vec2(8.0, 34.0), holder="D"), "placement", gardien.DEPTH_M[0]),
        ("face-à-face à 16 m", _replay([attacker(16.0)], Vec2(16.0, 34.0), holder="A"), "face-à-face", 4.0),
        ("défenseur sur l'axe", _replay([attacker(16.0), defender], Vec2(16.0, 34.0), holder="A"), "placement",
         gardien.depth_for_ball(16.0)),
        ("ballon libre, attaquant loin", _replay([attacker(55.0)], Vec2(25.0, 34.0)), "sortie", None),
    ]
    for name, (out, _, _), state, depth in scenes:
        assert out.reason.startswith(state), name
        if depth is not None:  # en sortie, la cible est le point du ballon libre, pas une profondeur de placement
            assert out.target.x == pytest.approx(depth, abs=0.05), name


def test_with_a_defender_nearer_to_the_loose_ball_the_keeper_stays_and_the_defender_goes() -> None:
    # réserve A1 du 03d : ballon à 18 m du gardien, défenseur à 15 m du ballon, attaquant à 30 m. Le gardien gagnerait la
    # course, mais le défenseur est plus proche : le filtre de portée le laisse en placement et le défenseur y va.
    defender, attacker = player("D", "home", 8.0, 34.0, "DC"), player("A", "away", 53.0, 34.0, "BU")
    keeper_out, ball, players = _replay([defender, attacker], Vec2(23.0, 34.0))
    assert gardien.race(players[0], ball, players).rush  # il gagnerait la course
    assert keeper_out.reason.startswith("placement")
    mate_out = cerveau.think(defender, ball, players, 1.0, {})
    assert mate_out.target.distance_to(ball.position) < 3.0  # le défenseur va au ballon


def test_a_high_line_is_honoured_in_the_face_to_face_depth() -> None:
    # réserve A1 du 03e : ligne à 40 m, porteur seul à 22 m (profondeur de face-à-face 5,5 m, placement de la ligne 6,7 m)
    attacker = player("A", "away", 22.0, 34.0, "BU")
    out, ball, players = _replay([attacker], Vec2(22.0, 34.0), holder="A", line=40.0)
    assert out.reason.startswith("face-à-face")
    assert out.target.x >= gardien.placement(players[0], ball.position, 40.0).x - 1e-9
    low, _, _ = _replay([attacker], Vec2(22.0, 34.0), holder="A", line=10.0)  # ligne basse : la profondeur de face-à-face
    assert low.target.x == pytest.approx(gardien.face_depth(22.0), abs=0.05)

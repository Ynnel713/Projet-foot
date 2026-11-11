"""Intensité de course selon le rôle (ticket v2-realisme/12d) : trot pour rejoindre sa place en possession, course
sans ballon, course rapide pour un appel vers un espace libre, sprint dans la profondeur ; Work Rate et Off the Ball
modulent, pressing et repli inchangés."""

from __future__ import annotations

from v2engine import cerveau
from v2engine.ball_state import BallState
from v2engine.defense import press_intensity, replacement_intensity
from v2engine.geometry import Vec2
from v2engine.movement import PlayerState, max_speed_mps, step
from v2engine.off_ball import DEEP_RUN_INTENSITY, run_intensity

TROT_MAX_KMH, HIGH_SPEED_KMH = 14.4, 19.8  # classes de vitesse (Bradley 2009)


def _p(name: str, team: str = "home", x: float = 50.0, y: float = 34.0, home: Vec2 | None = None,
       attributes: dict[str, int] | None = None) -> PlayerState:
    return PlayerState(name=name, team=team, poste="MC", position=Vec2(x, y), velocity=Vec2(0.0, 0.0), pace=60,
                       acceleration=60, stamina=60, home_target=home or Vec2(x, y), attributes=attributes)


def _top_speed_kmh(player: PlayerState, intention: cerveau.Intention, seconds: float = 6.0) -> float:
    top = 0.0
    for _ in range(int(seconds / 0.1)):
        player = step(player, 0.1, intention.target, 10.0, intention.intensity)
        top = max(top, player.velocity.length() * 3.6)
    return top


def test_a_far_player_rejoins_his_place_running_not_sprinting() -> None:
    """Scène du ticket : loin du ballon, sans ballon, il rejoint sa place en course, sous la haute intensité."""
    far = _p("F", team="away", x=10.0, home=Vec2(40.0, 34.0))
    holder, near = _p("H", x=60.0), _p("N", team="away", x=58.0)
    intention = cerveau.think(far, BallState(position=Vec2(60.0, 34.0), velocity=Vec2(0.0, 0.0), holder="H"),
                              [far, holder, near], 1.0, None)
    assert (intention.role, intention.action) == (cerveau.REPLACEMENT, "se replacer")
    assert intention.intensity == replacement_intensity(far, False) < 1.0
    assert TROT_MAX_KMH < _top_speed_kmh(far, intention) < HIGH_SPEED_KMH


def test_in_possession_the_trot_is_slower_than_the_run_and_work_rate_modulates() -> None:
    lazy, keen = _p("L", attributes={"Work Rate": 20}), _p("K", attributes={"Work Rate": 95})
    for p in (lazy, keen):
        assert replacement_intensity(p, True) < replacement_intensity(p, False) < press_intensity(p)
    assert replacement_intensity(lazy, False) < replacement_intensity(keen, False)
    trot = cerveau.Intention(cerveau.TENIR, "se replacer", Vec2(90.0, 34.0), replacement_intensity(_p("M"), True))
    assert _top_speed_kmh(_p("M"), trot) < TROT_MAX_KMH  # trot : sous 14,4 km/h pour un joueur moyen (Pace 60)


def test_space_runs_are_fast_and_deep_runs_are_sprints() -> None:
    low, high = _p("L", attributes={"Off the Ball": 20}), _p("H", attributes={"Off the Ball": 95})
    assert run_intensity(low, False) < run_intensity(high, False) < DEEP_RUN_INTENSITY == run_intensity(low, True)
    average = _p("M")
    kmh = run_intensity(average, False) * max_speed_mps(average.pace) * 3.6
    assert HIGH_SPEED_KMH < kmh < 25.1  # course rapide, pas un sprint


def test_a_space_run_from_decide_carries_its_intensity() -> None:
    holder, mate, rival = _p("H"), _p("M", x=60.0), _p("R", team="away", x=70.0)
    intention = cerveau.think(mate, BallState(position=Vec2(50.0, 34.0), velocity=Vec2(0.0, 0.0), holder="H"),
                              [holder, mate, rival], 1.0, {})
    assert intention.role == cerveau.APPEL and intention.intensity in (run_intensity(mate, False), DEEP_RUN_INTENSITY)


def test_a_marker_follows_the_pace_of_his_man_not_a_sprint() -> None:
    """Ticket v2-realisme/18d : marquage et couverture à l'allure de l'adversaire suivi, plus une marge pour reprendre
    l'écart ; jamais sous la course sans ballon, au plus le sprint."""
    from v2engine.defense import FOLLOW_CATCH_UP, follow_intensity
    marker = _p("D", team="away")
    top = max_speed_mps(marker.pace)
    assert follow_intensity(marker, Vec2(0.0, 0.0)) == replacement_intensity(marker, False)  # homme arrêté : course
    jogging = Vec2(0.5 * top, 0.0)
    assert follow_intensity(marker, jogging) == 0.5 + FOLLOW_CATCH_UP
    assert follow_intensity(marker, Vec2(1.2 * top, 0.0)) == 1.0  # attaquant lancé plus vite que lui : sprint


def test_marking_from_decide_carries_the_followed_pace() -> None:
    from v2engine.defense import MARQUAGE, Assignment, DefensiveRoles, follow_intensity
    marker, holder = _p("D", team="away", x=40.0), _p("H", x=60.0)
    roles = DefensiveRoles()
    roles.assignments["D"] = Assignment(MARQUAGE, Vec2(42.0, 34.0), "H", Vec2(3.0, 0.0))
    intention = cerveau.decide(marker, MARQUAGE, BallState(position=Vec2(60.0, 34.0), velocity=Vec2(0.0, 0.0),
                                                           holder="H"),
                               cerveau.perceive(marker, BallState(position=Vec2(60.0, 34.0), velocity=Vec2(0.0, 0.0),
                                                                  holder="H"), [marker, holder]),
                               [marker, holder], 1.0, None, defense=roles)
    assert intention.action == "marquer" and intention.intensity == follow_intensity(marker, Vec2(3.0, 0.0)) < 1.0

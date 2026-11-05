"""Tests du cerveau du joueur V2 (ADR 0001, ticket v2-collectif/02) : rôles, intentions tracées, journal des
décisions, et séparation voir / choisir / réussir."""

from __future__ import annotations

import random

from v2engine import cerveau
from v2engine.anticipation import pass_readers
from v2engine.ball_state import BallState
from v2engine.decision import DRIBBLE_DIRECTIONS_DEG, choose_action
from v2engine.geometry import Vec2
from v2engine.movement import PlayerState
from v2engine.possession import pass_velocity
from v2engine.trace import DecisionRecord, MatchTrace, PlayerSnapshot


def _p(name: str, team: str = "home", x: float = 50.0, y: float = 34.0, poste: str = "MC",
       attributes: dict[str, int] | None = None) -> PlayerState:
    return PlayerState(name=name, team=team, poste=poste, position=Vec2(x, y), velocity=Vec2(0.0, 0.0),
                       pace=60, acceleration=60, stamina=60, home_target=Vec2(x, y), attributes=attributes)


def _ball(x: float = 50.0, y: float = 34.0, **kw) -> BallState:
    return BallState(position=Vec2(x, y), velocity=kw.pop("velocity", Vec2(0.0, 0.0)), **kw)


# --- Rôles et intentions ------------------------------------------------------------------------------------------
def test_holder_controls_then_drives() -> None:
    holder = _p("H")
    receiving = cerveau.think(holder, _ball(holder="H", receiving=True), [holder], 1.0, {})
    driving = cerveau.think(holder, _ball(holder="H", receiving=False), [holder], 1.0, {})
    assert (receiving.role, receiving.action) == (cerveau.PORTEUR, "contrôler")
    assert (driving.role, driving.action) == (cerveau.PORTEUR, "conduire")
    assert receiving.intensity < driving.intensity


def test_teammate_of_the_holder_makes_a_run_and_remembers_it() -> None:
    holder, mate, rival = _p("H"), _p("M", x=60), _p("R", team="away", x=70)
    runs: dict = {}
    intention = cerveau.think(mate, _ball(holder="H"), [holder, mate, rival], 1.0, runs)
    assert (intention.role, intention.mate) == (cerveau.APPEL, "H") and runs["M"][0] == intention.target


def test_receiver_reader_loose_ball_pressure_and_replacement_roles() -> None:
    receiver, reader, far = _p("R", x=60), _p("X", team="away", x=55), _p("F", team="away", x=10)
    passer = _p("P", x=45)
    in_flight = _ball(52, 34, velocity=Vec2(5.0, 0.0), receiver="R", readers={"X": Vec2(56, 34)})
    players = [receiver, reader, far, passer]
    assert cerveau.think(receiver, in_flight, players, 1.0, {}).role == cerveau.RECEVEUR
    lecture = cerveau.think(reader, in_flight, players, 1.0, {})
    assert lecture.role == cerveau.LECTURE and lecture.explain() == "passe lue, il court l'intercepter (1 m)"
    near_mate = _p("N", team="away", x=50)
    assert cerveau.think(far, in_flight, players + [near_mate], 1.0, {}).role == cerveau.REPLACEMENT
    loose = _ball(52, 34)
    assert cerveau.think(passer, loose, players, 1.0, {}).role == cerveau.BALLON_LIBRE
    held = _ball(60, 34, holder="R")
    pressing = cerveau.think(reader, held, players, 1.0, None)
    assert (pressing.role, pressing.mate) == (cerveau.PRESSEUR, "R")


def test_keeper_near_his_own_holder_supports_him_instead_of_pressing() -> None:
    holder, keeper = _p("H", x=12), _p("G", x=5, poste="GK")
    support = cerveau.think(keeper, _ball(12, 34, holder="H"), [holder, keeper], 1.0, {})
    assert (support.role, support.mate, support.reason) == (cerveau.SOUTIEN, "H", "soutien de son porteur")


def test_every_player_has_a_complete_intention_in_the_trace() -> None:
    from ligue1sim.clubs import load_clubs
    from ligue1sim.season import CLUBS_PATH
    from v2engine.match import simulate_match
    clubs = load_clubs(CLUBS_PATH, "Ligue 1")
    random.seed(20260923)
    trace = simulate_match(clubs[0], clubs[1], duration_minutes=1.0)
    for tick in trace.ticks:
        for p in tick.players:
            i = p.intention
            assert i is not None and i.role and i.action and i.target is not None and 0.0 < i.intensity <= 1.0
            assert i.explain()
    assert trace.decisions and all(isinstance(d, DecisionRecord) for d in trace.decisions)
    assert all(d.considered >= 1 for d in trace.decisions)


# --- Voir, choisir, réussir : trois tirages distincts --------------------------------------------------------------
def test_perception_alone_decides_whether_the_pass_is_read(monkeypatch) -> None:
    reader = _p("X", team="away", x=55, y=36)
    start, aim = Vec2(45, 34), Vec2(65, 34)
    monkeypatch.setattr("v2engine.flux.PERCEPTION.random", lambda: 0.0)
    assert "X" in pass_readers(start, Vec2(12.0, 0.0), aim, [reader])
    monkeypatch.setattr("v2engine.flux.PERCEPTION.random", lambda: 0.999)
    assert "X" not in pass_readers(start, Vec2(12.0, 0.0), aim, [reader])


def test_perception_alone_decides_whether_the_best_option_is_taken(monkeypatch) -> None:
    # ticket v2-collectif/33 : seule l'erreur de perception choisit -- une par direction de conduite (gardée pendant
    # la possession), puis une par option comparée (la conduite retenue, chaque passe, le tir)
    holder, mate = _p("H", x=30), _p("M", x=33, y=40)  # pas de passe décisive
    players = [holder, mate, _p("D", team="away", x=31)]
    goal = Vec2(105.0, 34.0)
    draws: list[float] = []
    monkeypatch.setattr("v2engine.flux.PERCEPTION.gauss", lambda mu, sigma: draws.append(sigma) or 0.0)
    best = choose_action(holder, players, goal, None)
    directions = len(DRIBBLE_DIRECTIONS_DEG)
    assert len(draws) == directions + (best.considered - directions + 1) and best.best and best.gap == 0.0
    # l'autre option comparée (conduite retenue, puis la passe) paraît bien meilleure qu'elle n'est
    slot = directions if best.kind == "pass" else directions + 1
    boosted = iter([0.0] * slot + [5.0])
    monkeypatch.setattr("v2engine.flux.PERCEPTION.gauss", lambda mu, sigma: next(boosted, 0.0))
    other = choose_action(holder, players, goal, None)
    assert not other.best and other.gap > 0.0 and other.best_kind == best.kind and best.considered == other.considered


def test_execution_alone_decides_the_quality_of_the_pass(monkeypatch) -> None:
    passer, target = _p("P", x=40, attributes={"Passing": 60}), _p("T", x=60)
    monkeypatch.setattr("v2engine.possession.random.random", lambda: 0.0)  # passe précise
    monkeypatch.setattr("v2engine.possession.random.uniform", lambda a, b: a)
    slow = pass_velocity(passer, target, [])
    monkeypatch.setattr("v2engine.possession.random.uniform", lambda a, b: b)
    fast = pass_velocity(passer, target, [])
    assert fast.length() > slow.length()  # même intention, même choix : seul le dosage (exécution) change


# --- Relecture : API ----------------------------------------------------------------------------------------------
def test_api_sends_intentions_only_when_role_or_action_changes() -> None:
    from api.routers.v2 import intention_segments
    trace = MatchTrace(home="A", away="B", tick_seconds=1.0)
    go = cerveau.Intention(cerveau.BALLON_LIBRE, "aller au ballon", Vec2(0, 0), reason="ballon libre", distance_m=4.2)
    nearer = cerveau.Intention(cerveau.BALLON_LIBRE, "aller au ballon", Vec2(0, 0), reason="ballon libre", distance_m=1.0)
    press_a = cerveau.Intention(cerveau.PRESSEUR, "aller au ballon", Vec2(0, 0), mate="A", reason="presse le porteur adverse")
    press_b = cerveau.Intention(cerveau.PRESSEUR, "aller au ballon", Vec2(0, 0), mate="B", reason="presse le porteur adverse")
    for minute, intention in ((0.0, go), (0.1, nearer), (0.2, press_a), (0.3, press_b)):
        trace.record(minute, [PlayerSnapshot("J", "home", "MC", Vec2(0, 0), intention)], None)
    [player] = intention_segments(trace)
    assert [(s.minute, s.role, s.mate, s.reason) for s in player.segments] == [
        (0.0, cerveau.BALLON_LIBRE, None, "ballon libre"),  # la distance change, pas le segment
        (0.2, cerveau.PRESSEUR, "A", "presse le porteur adverse"),
        (0.3, cerveau.PRESSEUR, "B", "presse le porteur adverse")]  # nouveau porteur pressé : nouveau segment


# --- Équilibre derrière le ballon (ticket v2-collectif/06) ----------------------------------------------------------
def _balance_ahead_share(teamwork: int, situation: str) -> float:
    """Part des appels du défenseur le plus reculé qui le mènent devant le ballon (x > 40)."""
    holder = _p("H", x=40.0)
    deep = _p("DC1", x=38.0, y=20.0, poste="DC", attributes={"Teamwork": teamwork, "Off the Ball": 99})
    other = _p("DC2", x=36.0, y=48.0, poste="DC")
    forward = _p("BU", x=60.0, poste="BU")
    players = [holder, deep, other, forward, _p("Adv", team="away", x=20.0, y=5.0)]
    random.seed(20260923)
    ahead = sum(cerveau.think(deep, _ball(40.0, 34.0, holder="H"), players, 1.0, {}, situation).target.x > 40.0
                for _ in range(400))
    return ahead / 400


def test_rest_defenders_stay_behind_the_ball_in_settled_possession() -> None:
    from v2engine.situation import POSSESSION_INSTALLEE, TRANSITION_OFFENSIVE

    assert _balance_ahead_share(99, POSSESSION_INSTALLEE) == 0.0  # discipliné : jamais devant le ballon
    free = _balance_ahead_share(99, TRANSITION_OFFENSIVE)  # hors possession installée : appel libre
    assert free > 0.3
    loose = _balance_ahead_share(11, POSSESSION_INSTALLEE)  # Teamwork 11 : monte 35 % du temps
    assert 0.2 * free < loose < 0.5 * free


def test_rest_defenders_are_the_two_deepest_outfield_players_except_the_holder() -> None:
    holder = _p("H", x=10.0, poste="DC")
    keeper = _p("GK", x=2.0, poste="GK")
    team = [holder, keeper, _p("A", x=20.0), _p("B", x=30.0), _p("C", x=40.0)]
    assert [p.name for p in cerveau._rest_defenders(team, holder, 1.0)] == ["A", "B"]
    assert [p.name for p in cerveau._rest_defenders(team, holder, -1.0)] == ["C", "B"]


def test_runner_keeps_his_space_until_he_reaches_it_or_three_seconds() -> None:
    holder = _p("H", x=40.0)
    far = _p("M", x=50.0, y=20.0)
    players = [holder, far, _p("Adv", team="away", x=20.0, y=5.0)]
    space = Vec2(65.0, 10.0)  # choisi à t = 10 s, loin du joueur

    def target(player, now_s: float) -> Vec2:
        runs = {"M": (space, 10.0 + cerveau.SPACE_HOLD_MAX_S)}
        return cerveau.think(player, _ball(40.0, 34.0, holder="H"), players, now_s / 60.0, runs).target

    random.seed(3)
    assert target(far, 12.9) == space  # pas encore atteint : il le garde
    assert target(far, 13.0) != space  # 3 s : il en cherche un autre
    there = _p("M", x=65.0, y=11.0)  # à 1 m de l'espace
    assert target(there, 10.5) == space  # atteint, mais moins de 1 s : il reste
    assert target(there, 11.0) != space  # atteint après 1 s : il en cherche un autre


def test_teammates_keep_their_run_while_their_pass_is_in_flight() -> None:
    passer, receiver, mate, rival = _p("P", x=45), _p("R", x=60), _p("M", x=53, y=30), _p("X", team="away", x=70)
    players = [passer, receiver, mate, rival]
    space = Vec2(70.0, 20.0)
    runs = {"M": (space, 60.0 + cerveau.SPACE_HOLD_MAX_S)}
    own_pass = _ball(52, 34, velocity=Vec2(5.0, 0.0), receiver="R", last_pass_team="home")
    run = cerveau.think(mate, own_pass, players, 1.0, runs)
    assert (run.role, run.target, run.mate) == (cerveau.APPEL, space, "R")  # il poursuit son appel, pas le ballon
    assert cerveau.think(receiver, own_pass, players, 1.0, runs).role == cerveau.RECEVEUR
    rival_pass = _ball(52, 34, velocity=Vec2(5.0, 0.0), receiver="Y", last_pass_team="away")
    assert cerveau.think(mate, rival_pass, players, 1.0, runs).role == cerveau.BALLON_LIBRE
    assert cerveau.think(mate, _ball(52, 34), players, 1.0, runs).role == cerveau.BALLON_LIBRE  # ballon perdu


def test_a_depth_run_is_remembered_and_held_at_the_next_search(monkeypatch) -> None:
    holder, mate = _p("H"), _p("M", x=70, poste="BU")
    defenders = [_p("D1", team="away", x=80, y=20), _p("D2", team="away", x=80, y=48), _p("G", team="away", x=104)]
    monkeypatch.setattr(cerveau.random, "random", lambda: 0.999)  # tout nouveau tirage serait perdu
    runs: dict = {"M": (Vec2(80.0, 34.0), 59.0, "H")}  # appel dans le dos lancé pour H, délai à peine écoulé
    intention = cerveau.think(mate, _ball(holder="H"), [holder, mate, *defenders], 1.0, runs)
    assert intention.target.x >= 79.0 and runs["M"][2] == "H"  # il tient la ligne, sans nouveau tirage


def test_a_held_depth_run_does_not_survive_a_loss_of_the_ball(monkeypatch) -> None:
    holder, mate = _p("H"), _p("M", x=70, poste="BU")
    defenders = [_p("D1", team="away", x=80, y=20), _p("D2", team="away", x=80, y=48), _p("G", team="away", x=104)]
    monkeypatch.setattr(cerveau.random, "random", lambda: 0.999)  # tout nouveau tirage serait perdu
    runs: dict = {"M": (Vec2(80.0, 34.0), 10.0, "H")}  # lancé pour H, il y a 50 s : la possession a changé depuis
    intention = cerveau.think(mate, _ball(holder="H"), [holder, mate, *defenders], 1.0, runs)
    assert intention.target.x < 79.0 and len(runs["M"]) == 2  # retiré au sort, perdu : espace ordinaire

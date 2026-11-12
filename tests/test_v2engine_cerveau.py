"""Tests du cerveau du joueur V2 (ADR 0001, ticket v2-collectif/02) : rôles, intentions tracées, journal des
décisions, et séparation voir / choisir / réussir."""

from __future__ import annotations

import random

from v2engine import cerveau, gardien
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


def test_keeper_near_his_own_holder_keeps_his_place_instead_of_supporting_him() -> None:
    # ticket v2-realisme/03a : avant, le gardien à moins de 15 m de son porteur venait en soutien (règle générale)
    holder, keeper = _p("H", x=12), _p("G", x=5, poste="GK")
    placed = cerveau.think(keeper, _ball(12, 34, holder="H"), [holder, keeper], 1.0, {})
    assert placed.role == cerveau.GARDIEN and placed.reason.startswith("placement") and placed.mate is None
    assert placed.action == "se replacer" and placed.target == gardien.placement(keeper, Vec2(12.0, 34.0))


def test_keeper_near_an_opposing_holder_does_not_press() -> None:
    keeper, striker = _p("G", x=5, poste="GK"), _p("S", team="away", x=15)
    # un défenseur sur la ligne de tir : pas de face-à-face (ticket v2-realisme/03e), le gardien reste en placement
    held = cerveau.think(keeper, _ball(15, 34, holder="S"), [keeper, striker, _p("D", x=10)], 1.0, {})
    assert held.role == cerveau.GARDIEN and held.reason.startswith("placement")
    assert held.action != "aller au ballon" and held.target == gardien.placement(keeper, Vec2(15.0, 34.0))
    alone = cerveau.think(keeper, _ball(15, 34, holder="S"), [keeper, striker], 1.0, {})  # seul face à lui : face-à-face
    assert alone.role == cerveau.GARDIEN and alone.reason.startswith("face-à-face") and alone.action != "aller au ballon"


def test_keeper_states_are_traced_in_the_reason() -> None:
    keeper = _p("G", x=5, poste="GK")
    holding = cerveau.think(keeper, _ball(5, 34, holder="G"), [keeper], 1.0, {})
    assert (holding.role, holding.action) == (cerveau.GARDIEN, "conduire") and holding.reason.startswith("relance")
    other = _p("A", team="away", x=40)
    incoming = _ball(15, 34, velocity=Vec2(-8.0, 0.0), receiver="G")  # passe en retrait pour lui
    receiving = cerveau.think(keeper, incoming, [keeper, other], 1.0, {})
    assert (receiving.role, receiving.action) == (cerveau.GARDIEN, "venir au ballon")
    assert receiving.reason.startswith("intervention")
    read = cerveau.think(keeper, _ball(15, 34, velocity=Vec2(5.0, 0.0), readers={"G": Vec2(20, 34)}, receiver="A"),
                         [keeper, other], 1.0, {})
    assert read.reason.startswith("intervention") and read.action == "couper la passe"


def test_keeper_still_comes_out_for_a_loose_ball_in_reach_only() -> None:
    keeper, mate = _p("G", x=5, poste="GK"), _p("D", x=30, poste="DC")
    near = cerveau.think(keeper, _ball(12, 34), [keeper, mate], 1.0, {})
    assert near.reason.startswith("sortie") and near.action == "aller au ballon"
    far_ball = _ball(60, 34)  # loin, et un défenseur est plus près : le gardien reste placé
    far = cerveau.think(keeper, far_ball, [keeper, mate], 1.0, {})
    assert far.reason.startswith("placement") and far.target == gardien.placement(keeper, far_ball.position)


def test_keeper_never_presses_or_supports_in_a_real_match() -> None:
    from ligue1sim.clubs import load_clubs
    from ligue1sim.season import CLUBS_PATH
    from v2engine.match import simulate_match
    clubs = load_clubs(CLUBS_PATH, "Ligue 1")
    random.seed(20260923)
    trace = simulate_match(clubs[0], clubs[1], duration_minutes=4.0)
    keepers = [p.intention for tick in trace.ticks for p in tick.players if p.poste == "GK"]
    # hors remises en jeu (ticket 29) et hors « play the whistle » (hors-jeu, ticket 23), qui change la raison de tous
    live = [i for i in keepers if i.role != cerveau.REMISE and not i.reason.startswith(("ballon mort", "il lève la main"))]
    assert live and all(i.role == cerveau.GARDIEN for i in live)
    # « face-à-face » (ticket 03e) est une raison légitime du gardien ; la graine du match la fait apparaître depuis le 04a
    assert {i.reason.split(" : ")[0] for i in live} <= {"placement", "sortie", "intervention", "relance", "face-à-face"}
    assert any(i.reason.startswith("placement") for i in live)
    assert not {i.role for i in keepers} & {cerveau.PRESSEUR, cerveau.SOUTIEN, cerveau.BALLON_LIBRE}


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
    # pas de passe décisive ; coéquipier à 14 m (y = 48) : conduite et passe séparées de plus de
    # `BEST_CHOICE_TOLERANCE` (à y = 40, quasi égales depuis le ticket v2-realisme/18i)
    holder, mate = _p("H", x=30), _p("M", x=33, y=48)
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
    monkeypatch.setattr("v2engine.flux.PASSE.random", lambda: 0.0)  # passe précise
    monkeypatch.setattr("v2engine.flux.PASSE.uniform", lambda a, b: a)
    slow = pass_velocity(passer, target, [])
    monkeypatch.setattr("v2engine.flux.PASSE.uniform", lambda a, b: b)
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
    """Part des appels du défenseur le plus reculé qui le mènent devant le ballon (x > 30). Le porteur est derrière
    lui (relance courte) : depuis le ticket v2-realisme/02f, un joueur derrière le ballon tient sa place, seul un
    joueur devant le ballon peut encore appeler. Depuis le 02g, un défenseur central n'appelle plus en possession : le
    joueur d'équilibre testé est ici un box to box, l'un des deux plus reculés de l'équipe."""
    holder = _p("H", x=30.0)
    deep = _p("DC1", x=38.0, y=20.0, poste="DC", attributes={"Teamwork": teamwork, "Off the Ball": 99})
    deep.role = "box to box"
    other = _p("DC2", x=36.0, y=48.0, poste="DC")
    forward = _p("BU", x=60.0, poste="BU")
    players = [holder, deep, other, forward, _p("Adv", team="away", x=20.0, y=5.0)]
    random.seed(20260923)
    ball = _ball(30.0, 34.0, holder="H")
    cerveau.think(deep, ball, players, 1.0 - 0.5 / 60.0, {}, situation)  # choisi : son délai (Off the Ball) court
    ahead = sum(cerveau.think(deep, ball, players, 1.0, {}, situation).target.x > 30.0 for _ in range(400))
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
    monkeypatch.setattr("v2engine.flux.PLACEMENT.random", lambda: 0.999)  # tout nouvel appel serait perdu
    monkeypatch.setattr("v2engine.flux.DEFENSE.random", lambda: 0.999)
    runs: dict = {"M": (Vec2(80.0, 34.0), 59.0, "H")}  # appel dans le dos lancé pour H, délai à peine écoulé
    intention = cerveau.think(mate, _ball(holder="H"), [holder, mate, *defenders], 1.0, runs)
    assert intention.target.x >= 79.0 and runs["M"][2] == "H"  # il tient la ligne, sans nouveau tirage


def test_a_held_depth_run_does_not_survive_a_loss_of_the_ball(monkeypatch) -> None:
    holder, mate = _p("H"), _p("M", x=70, poste="BU")
    defenders = [_p("D1", team="away", x=80, y=20), _p("D2", team="away", x=80, y=48), _p("G", team="away", x=104)]
    monkeypatch.setattr("v2engine.flux.PLACEMENT.random", lambda: 0.999)  # tout nouvel appel serait perdu
    monkeypatch.setattr("v2engine.flux.DEFENSE.random", lambda: 0.999)
    runs: dict = {"M": (Vec2(80.0, 34.0), 10.0, "H")}  # lancé pour H, il y a 50 s : la possession a changé depuis
    intention = cerveau.think(mate, _ball(holder="H"), [holder, mate, *defenders], 1.0, runs)
    assert intention.target.x < 79.0 and len(runs["M"]) == 2  # retiré au sort, perdu : espace ordinaire


# --- Tenir sa place en possession (02f), qui appelle (02g) -----------------------------------------------------------
_SCENE_ROLES = {"A0": "milieu relayeur", "A1": "avant-centre", "A2": "ailier de couloir", "A3": "défenseur central",
                "A4": "mezzala", "A5": "sentinelle", "A6": "défenseur central", "A7": "latéral défensif", "A8": "regista"}


def _settled_scene() -> tuple[list[PlayerState], PlayerState, BallState]:
    """Possession installée au milieu : porteur à x = 50, neuf coéquipiers de champ (cinq devant, quatre derrière), chacun
    avec son rôle (A1, A2, A4 : projection ; A0 : intermédiaire ; A3 : devant le ballon mais rôle qui n'appelle pas)."""
    holder = _p("H", x=50.0, y=34.0)
    mates = [_p(f"A{i}", x=x, y=y, poste="MC") for i, (x, y) in enumerate(
        ((55, 20), (58, 34), (62, 48), (70, 10), (75, 58), (40, 20), (35, 34), (30, 48), (25, 10)))]
    for mate in mates:
        mate.role = _SCENE_ROLES[mate.name]
    rival = _p("R", team="away", x=60.0, y=30.0)
    return [holder, *mates, _p("GK", x=3.0, poste="GK"), rival], holder, _ball(50.0, 34.0, holder="H")


_TICKS = tuple(1.0 + i * 0.15 / 60.0 for i in range(11))  # 1,5 s de match au pas de 0,15 s : plus que tout délai d'appel


def _roles(players: list[PlayerState], ball: BallState, situation: str | None, runs: dict | None = None,
           minutes: tuple[float, ...] = _TICKS) -> dict[str, str]:
    """Rôle de chaque coéquipier de champ du porteur aux instants `minutes` (le premier choisit les appelants, le
    dernier est après leur délai d'Off the Ball) ; renvoie ceux du dernier instant."""
    runs = {} if runs is None else runs
    roles: dict[str, str] = {}
    for minute in minutes:
        roles = {p.name: cerveau.think(p, ball, players, minute, runs, situation).role
                 for p in players if p.team == "home" and p.name not in ("H", "GK")}
    return roles


def _callers(roles: dict[str, str]) -> list[str]:
    return sorted(n for n, r in roles.items() if r == cerveau.APPEL)


def test_settled_possession_keeps_the_two_best_ranked_runners_and_the_others_hold() -> None:
    from v2engine.situation import POSSESSION_INSTALLEE

    players, _, ball = _settled_scene()
    roles = _roles(players, ball, POSSESSION_INSTALLEE)
    # rôles de projection d'abord (A1 à 8 m, A2 à 17 m, A4 à 29 m), l'intermédiaire A0 ensuite : A1 et A2
    assert _callers(roles) == ["A1", "A2"]
    assert all(r == cerveau.TENIR for n, r in roles.items() if n not in ("A1", "A2"))
    assert cerveau.think(players[0], ball, players, 1.0, {}, POSSESSION_INSTALLEE).role == cerveau.PORTEUR


def test_the_cap_depends_on_the_situation_and_without_situation_everyone_calls() -> None:
    from v2engine.situation import DEFENSE_PLACEE, DERNIER_TIERS, TRANSITION_DEFENSIVE, TRANSITION_OFFENSIVE

    players, _, ball = _settled_scene()
    # dernier tiers et transition offensive : 3 appelants (A4 rejoint A1 et A2). C'est aussi le cas d'une contre-attaque
    # qui arrive au dernier tiers (réserve A1 de l'expert au 02f) : elle garde 3 appelants au lieu de 2.
    for situation in (DERNIER_TIERS, TRANSITION_OFFENSIVE):
        assert _callers(_roles(players, ball, situation)) == ["A1", "A2", "A4"]
    # situation perçue avec retard (il croit encore défendre alors que son équipe a le ballon) : règle de la transition
    for situation in (DEFENSE_PLACEE, TRANSITION_DEFENSIVE):
        assert _callers(_roles(players, _ball(50.0, 34.0, holder="H"), situation)) == ["A1", "A2", "A4"]
    mates = [p for p in players if p.team == "home" and p.name not in ("H", "GK")]
    # tests sans situation : tous appellent comme avant
    assert {cerveau.think(p, ball, players, 1.0, {}, None).role for p in mates} == {cerveau.APPEL}


def test_roles_that_build_or_cover_never_call_even_when_nearest_to_the_ball() -> None:
    from v2engine.situation import POSSESSION_INSTALLEE

    players, _, ball = _settled_scene()
    ahead = next(p for p in players if p.name == "A3")
    ahead.position = Vec2(52.0, 34.0)  # devant le ballon, le plus proche
    for role in ("défenseur central", "sentinelle", "récupérateur", "regista", "latéral défensif"):
        ahead.role = role
        assert _roles(players, _ball(50.0, 34.0, holder="H"), POSSESSION_INSTALLEE)["A3"] == cerveau.TENIR
    ahead.role = "ailier de couloir"
    # même place, rôle de projection ; balle neuve : A1 et A2, déjà choisis sur l'autre balle, n'ont pas la priorité
    assert _roles(players, _ball(50.0, 34.0, holder="H"), POSSESSION_INSTALLEE)["A3"] == cerveau.APPEL


def test_a_full_back_calls_only_when_the_ball_is_on_the_other_side() -> None:
    from v2engine.situation import POSSESSION_INSTALLEE

    players, _, _ = _settled_scene()
    back = next(p for p in players if p.name == "A0")
    back.role, back.position = "latéral", Vec2(55.0, 60.0)  # côté y > 34
    for p in players:
        if p.name in ("A1", "A2", "A4"):
            p.role = "défenseur central"  # personne d'autre devant ne peut appeler
    same_side, other_side = _ball(50.0, 50.0, holder="H"), _ball(50.0, 10.0, holder="H")
    assert _roles(players, same_side, POSSESSION_INSTALLEE)["A0"] == cerveau.TENIR
    assert _roles(players, other_side, POSSESSION_INSTALLEE)["A0"] == cerveau.APPEL


def test_off_the_ball_sets_the_delay_before_the_run_starts() -> None:
    from v2engine.off_ball import call_delay_s
    from v2engine.situation import POSSESSION_INSTALLEE

    assert abs(call_delay_s(99) - 0.3) < 1e-9 and abs(call_delay_s(11) - 1.0) < 1e-9
    assert call_delay_s(99) < call_delay_s(70) < call_delay_s(55) < call_delay_s(30) < call_delay_s(11)
    for note in (99, 11):
        holder = _p("H")
        mate = _p("W", x=60.0, y=20.0, attributes={"Off the Ball": note})
        mate.role = "ailier de couloir"
        ball, players, delay = _ball(holder="H"), [holder, mate], call_delay_s(note)
        first = cerveau.think(mate, ball, players, 1.0, {}, POSSESSION_INSTALLEE)
        too_early = cerveau.think(mate, ball, players, (60.0 + delay - 0.1) / 60.0, {}, POSSESSION_INSTALLEE)
        in_time = cerveau.think(mate, ball, players, (60.0 + delay + 0.1) / 60.0, {}, POSSESSION_INSTALLEE)
        assert (first.role, too_early.role, in_time.role) == (cerveau.TENIR, cerveau.TENIR, cerveau.APPEL)


def test_a_runner_in_full_run_keeps_his_call_instead_of_alternating_with_a_nearer_mate() -> None:
    from v2engine.situation import POSSESSION_INSTALLEE

    players, _, ball = _settled_scene()
    runs = {"A4": (Vec2(85.0, 58.0), 70.0)}  # A4, le plus loin des projections, court vers un espace encore lointain
    assert _callers(_roles(players, ball, POSSESSION_INSTALLEE, runs)) == ["A1", "A4"]  # A2 cède, A4 ne lâche pas
    runs = {"A4": (Vec2(75.0, 58.0), 70.0)}  # espace atteint : candidat ordinaire, donc évincé (balle neuve)
    assert _callers(_roles(players, _ball(50.0, 34.0, holder="H"), POSSESSION_INSTALLEE, runs)) == ["A1", "A2"]
    runs = {"A4": (Vec2(85.0, 58.0), 50.0)}  # appel périmé : même chose
    assert _callers(_roles(players, _ball(50.0, 34.0, holder="H"), POSSESSION_INSTALLEE, runs)) == ["A1", "A2"]


def test_the_player_named_by_the_pass_plan_stays_a_caller() -> None:
    from v2engine.situation import POSSESSION_INSTALLEE

    players, _, ball = _settled_scene()
    a6 = next(p for p in players if p.name == "A6")  # défenseur central derrière le ballon
    ball.plan = ("H", "A6", 0.0)  # suite prévue de la passe du porteur : appelant sans délai
    assert cerveau.think(a6, ball, players, 1.0, {}, POSSESSION_INSTALLEE).role == cerveau.APPEL
    ball.plan = ("X", "A6", 0.0)  # plan d'un autre porteur : ignoré
    assert cerveau.think(a6, ball, players, 1.0, {}, POSSESSION_INSTALLEE).role == cerveau.TENIR


def test_the_receiver_and_the_runners_of_a_pass_in_flight_are_kept() -> None:
    from v2engine.situation import POSSESSION_INSTALLEE

    players, _, _ = _settled_scene()
    flight = _ball(53.0, 34.0, velocity=Vec2(10.0, 0.0), receiver="A1", last_pass_team="home")
    roles = _roles(players, flight, POSSESSION_INSTALLEE)
    assert roles["A1"] == cerveau.RECEVEUR
    assert _callers(roles) == ["A2", "A4"]  # le receveur ne prend pas de place d'appelant
    assert all(r in (cerveau.APPEL, cerveau.TENIR, cerveau.RECEVEUR) for r in roles.values())


def test_away_team_holds_in_mirror_and_the_intention_shows_the_role() -> None:
    from v2engine.situation import POSSESSION_INSTALLEE

    holder, ahead, behind = _p("H", team="away", x=50.0), _p("F", team="away", x=40.0), _p("B", team="away", x=60.0)
    ahead.role = behind.role = "avant-centre"
    players = [holder, ahead, behind, _p("R", x=30.0)]
    ball = _ball(50.0, 34.0, holder="H")
    cerveau.think(ahead, ball, players, 1.0, {}, POSSESSION_INSTALLEE)  # choisi : son délai (Off the Ball) court
    run = cerveau.think(ahead, ball, players, 1.0 + 1.0 / 60.0, {}, POSSESSION_INSTALLEE)
    hold = cerveau.think(behind, ball, players, 1.0 + 1.0 / 60.0, {}, POSSESSION_INSTALLEE)
    assert run.role == cerveau.APPEL and hold.role == cerveau.TENIR
    assert hold.action in ("se replacer", "tenir sa place") and "en possession" in hold.reason


def test_teamwork_decides_whether_a_holder_s_mate_returns_to_his_place_in_possession() -> None:
    from v2engine.bloc import Bloc
    from v2engine.situation import POSSESSION_INSTALLEE

    players, _, ball = _settled_scene()
    team = [p for p in players if p.team == "home"]
    bloc = Bloc.from_players(team)
    for teamwork, expected in ((99, "se replacer"), (11, "tenir sa place")):
        player = _p("T", x=30.0, y=48.0, attributes={"Positioning": 99, "Teamwork": teamwork})
        bloc.returning.clear()
        place = bloc.reference(player, ball.position, POSSESSION_INSTALLEE)
        player.position = place + Vec2(0.0, 5.0)  # 5 m de sa place : au-delà de 2 m, en deçà de 9 m
        intention = cerveau.think(player, ball, [*team, player], 1.0, {}, POSSESSION_INSTALLEE, bloc)
        assert intention.role == cerveau.TENIR and intention.action == expected


def test_a_player_holding_his_place_keeps_doing_so_until_he_has_seen_the_loss() -> None:
    from v2engine.situation import POSSESSION_INSTALLEE

    players, _, ball = _settled_scene()
    mate = next(p for p in players if p.name == "A6")
    held = cerveau.think(mate, ball, players, 1.0, {}, POSSESSION_INSTALLEE)
    assert held.role == cerveau.TENIR
    rival_ball = _ball(50.0, 34.0, holder="R")  # perte de balle, pas encore perçue : même intention
    assert cerveau.think(mate, rival_ball, players, 1.0, {}, POSSESSION_INSTALLEE, previous=held) is held


def test_a_chosen_caller_keeps_his_place_when_a_nearer_mate_appears_and_is_forgotten_once_gone() -> None:
    from v2engine.situation import POSSESSION_INSTALLEE

    players, _, ball = _settled_scene()
    assert _callers(_roles(players, ball, POSSESSION_INSTALLEE)) == ["A1", "A2"]
    a4 = next(p for p in players if p.name == "A4")
    a4.position = Vec2(52.0, 34.0)  # A4 devient le plus proche du ballon : il n'évince pas A2, déjà choisi
    assert _callers(_roles(players, ball, POSSESSION_INSTALLEE, minutes=(1.03, 1.032))) == ["A1", "A2"]
    a2 = next(p for p in players if p.name == "A2")
    a2.position = Vec2(45.0, 48.0)  # A2 passe derrière le ballon : il n'est plus éligible, A4 prend la place libre
    later = tuple(1.03 + i * 0.15 / 60.0 for i in range(11))  # A4 attend ensuite son propre délai
    assert _callers(_roles(players, ball, POSSESSION_INSTALLEE, minutes=later)) == ["A1", "A4"]
    # absent plus d'une seconde, un appelant est oublié : il repasse par la sélection et par son délai
    gone = _ball(50.0, 34.0, holder="H")
    gone.callers["A1"] = (10.0, 10.0)
    assert cerveau.think(next(p for p in players if p.name == "A1"), gone, players, 2.0, {}, POSSESSION_INSTALLEE).role         == cerveau.TENIR

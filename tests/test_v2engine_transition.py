"""Transition défense-attaque (ticket v2-collectif/11) : à la récupération, contre-attaque ou conservation selon le
nombre d'adversaires derrière le ballon et de coéquipiers devant lui (choix réglé par Decisions) ; en contre-attaque,
passes vers l'avant et appels dans la profondeur ; en conservation, d'abord une passe sûre."""

from __future__ import annotations

import random

from v2engine import cerveau
from v2engine.ball_state import BallState
from v2engine.decision import (CONSERVATION, CONTRE_ATTAQUE, COUNTER_MAX_EXCESS,
                               choose_transition, counter_is_favorable, evaluate_options)
from v2engine.geometry import Vec2
from v2engine.movement import PlayerState
from v2engine.off_ball import COUNTER_RUN_DEPTH_M
from v2engine.situation import DEFENSE_PLACEE, TRANSITION_OFFENSIVE, SituationTracker
from v2engine.transition import TransitionPlay

GOAL = Vec2(105.0, 34.0)


def _p(name: str, team: str = "home", x: float = 50.0, y: float = 34.0, poste: str = "MC", **attributes: int) -> PlayerState:
    return PlayerState(name=name, team=team, poste=poste, position=Vec2(x, y), velocity=Vec2(0.0, 0.0), pace=60,
                       acceleration=60, stamina=60, home_target=Vec2(x, y),
                       attributes={k.replace("_", " "): v for k, v in attributes.items()} or None)


def _defenders(n: int, x: float = 70.0) -> list[PlayerState]:
    return [_p(f"D{i}", team="away", x=x, y=5.0 + 6.0 * i) for i in range(n)]


def test_counter_is_favorable_when_defenders_behind_the_ball_exceed_attackers_ahead_by_two_at_most() -> None:
    assert COUNTER_MAX_EXCESS == 2
    holder = _p("H", x=40)
    two_ahead = [_p("A1", x=60, y=10), _p("A2", x=60, y=50)]
    keeper = _p("GK", team="away", x=104, poste="GK")  # le gardien ne compte pas
    behind_me = _p("B", team="away", x=30)  # adversaire déjà dépassé : il ne compte pas
    assert counter_is_favorable(holder, [holder, keeper, behind_me, *two_ahead, *_defenders(4)])
    assert not counter_is_favorable(holder, [holder, keeper, behind_me, *two_ahead, *_defenders(5)])


def test_decisions_sets_the_chance_of_the_right_transition_choice() -> None:
    holder_free = [_p("A", x=60)]  # 0 défenseur devant : contre-attaque jouable
    rates = {}
    for note in (99, 11):
        holder = _p("H", x=40, Decisions=note)
        random.seed(11)
        rates[note] = sum(choose_transition(holder, [holder, *holder_free]) == CONTRE_ATTAQUE for _ in range(2000)) / 2000
    assert 0.92 < rates[99] < 0.98 and 0.40 < rates[11] < 0.50
    holder = _p("H", x=40, Decisions=99)
    random.seed(11)
    conserve = sum(choose_transition(holder, [holder, *_defenders(6)]) == CONSERVATION for _ in range(2000)) / 2000
    assert 0.92 < conserve < 0.98  # surnombre adverse : la conservation est le bon choix


def test_counter_considers_only_forward_passes_and_conservation_values_safety() -> None:
    holder = _p("H", x=40)
    back = _p("Back", x=28)  # passe en retrait, libre
    rival = _p("R", team="away", x=10, y=5)
    players = [holder, back, rival]

    def passes(mode):
        return [o for o in evaluate_options(holder, players, GOAL, None, mode) if o.kind == "pass"]
    assert passes(CONTRE_ATTAQUE) == []  # aucune passe vers l'avant : l'option n'existe pas (pas de cible au hasard)
    assert 0.0 < passes(None)[0].value < passes(CONSERVATION)[0].value
    forward = _p("Fwd", x=52, y=20)
    with_forward = [o for o in evaluate_options(holder, players + [forward], GOAL, None, CONTRE_ATTAQUE) if o.kind == "pass"]
    assert [o.target.name for o in with_forward] == ["Fwd"]



def test_pressed_holder_in_counter_can_still_play_back_but_after_any_forward_pass() -> None:
    holder = _p("H", x=40)
    back = _p("Back", x=28)  # coéquipier en retrait
    presser = _p("R", team="away", x=42)  # à 2 m : il est pressé

    def passes(players, mode=CONTRE_ATTAQUE):
        return [o for o in evaluate_options(holder, [holder, presser, *players], GOAL, None, mode) if o.kind == "pass"]
    assert len(passes([back])) == 1  # seul en retrait : une sortie de passe existe (réserve A2 de l'expert)
    assert 0.0 < passes([back])[0].value < passes([back], CONSERVATION)[0].value  # mais pas la valeur de conservation
    # ticket v2-collectif/33 : dans la monnaie du danger attendu, la ressortie n'est plus classée d'office après toute
    # passe vers l'avant (sous pression, le retrait peut être le meilleur choix) ; le sens reste : la contre-attaque
    # pèse le gain, donc valorise la passe vers l'avant et pénalise le retrait plus qu'en conservation.
    forward = _p("Fwd", x=52, y=20)

    def value(name, mode):
        return next(o.value for o in passes([back, forward], mode) if o.target.name == name)
    assert value("Fwd", CONTRE_ATTAQUE) > value("Fwd", CONSERVATION)
    assert value("Back", CONTRE_ATTAQUE) < value("Back", CONSERVATION)


def test_counter_weighs_the_danger_gained_by_driving_more_and_conservation_less() -> None:
    # ticket 33 : même sens que le doublement de la conduite du ticket 11, dans la monnaie du danger attendu
    holder = _p("H", x=40)

    def dribble(mode):
        return max(o.value for o in evaluate_options(holder, [holder, _p("R", team="away", x=80)], GOAL, None, mode)
                   if o.kind == "dribble")
    assert dribble(CONTRE_ATTAQUE) > dribble(None) > dribble(CONSERVATION)


def _recover(tracker: SituationTracker, play: TransitionPlay, now_s: float, holder: PlayerState,
             players: list[PlayerState], ball: BallState | None = None, scored: str | None = None) -> None:
    ball = ball or BallState(position=holder.position, velocity=Vec2(0.0, 0.0), holder=holder.name)
    tracker.update(now_s, ball, players, scored)
    play.update(tracker, ball, players, now_s)


def test_the_choice_lasts_the_offensive_transition_and_stops_with_it() -> None:
    home, away = _p("H", x=40), _p("V", team="away", x=60)
    players = [home, away, _p("A", x=60, y=10)]
    tracker, play = SituationTracker(), TransitionPlay()
    _recover(tracker, play, 0.0, away, players)  # première possession : pas une récupération
    assert play.mode == {}
    random.seed(3)
    _recover(tracker, play, 1.0, home, players)
    assert tracker.current["home"] == TRANSITION_OFFENSIVE and play.mode.get("home") in (CONTRE_ATTAQUE, CONSERVATION)
    chosen = play.mode["home"]
    _recover(tracker, play, 5.0, home, players)
    assert play.mode == {"home": chosen}  # un seul choix par récupération
    _recover(tracker, play, 10.0, home, players)  # fenêtre de 8 s écoulée : possession installée
    assert play.mode == {}


def test_the_choice_stops_in_the_final_third_and_at_the_loss_of_the_ball() -> None:
    home, away = _p("H", x=40), _p("V", team="away", x=60)
    players = [home, away]
    for later in (_p("H", x=80), away):  # dernier tiers ; puis perte du ballon
        tracker, play = SituationTracker(), TransitionPlay()
        _recover(tracker, play, 0.0, away, players)
        _recover(tracker, play, 1.0, home, players)
        assert "home" in play.mode
        _recover(tracker, play, 2.0, later, [later, away] if later.team == "home" else players)
        assert "home" not in play.mode


def test_no_choice_in_the_final_third_for_the_keeper_after_an_offside_or_at_kick_off() -> None:
    away = _p("V", team="away", x=60)
    cases = {
        "dernier tiers": (_p("H", x=80), None),
        "gardien": (_p("G", x=5, poste="GK"), None),
        "coup franc de hors-jeu": (_p("H", x=40), {"V": 2.0}),
    }
    for label, (holder, out) in cases.items():
        tracker, play = SituationTracker(), TransitionPlay()
        _recover(tracker, play, 0.0, away, [holder, away])
        ball = BallState(position=holder.position, velocity=Vec2(0.0, 0.0), holder=holder.name)
        if out:
            ball.offside_out_until = out
        _recover(tracker, play, 1.0, holder, [holder, away], ball)
        assert play.mode == {}, label
    tracker, play = SituationTracker(), TransitionPlay()
    _recover(tracker, play, 0.0, away, [away])
    tracker.update(1.0, BallState(position=Vec2(52.5, 34.0), velocity=Vec2(0.0, 0.0)), [away], "away")  # but
    _recover(tracker, play, 2.0, _p("H", x=52), [_p("H", x=52), away])  # engagement : pas une récupération
    assert play.mode == {}


def test_the_match_hands_the_team_choice_to_the_holder_decision(monkeypatch) -> None:
    from ligue1sim.clubs import load_clubs
    from ligue1sim.season import CLUBS_PATH
    from v2engine import match
    seen = []
    real = match.choose_action
    monkeypatch.setattr(match, "choose_action", lambda *args, **kwargs: seen.append(args[4]) or real(*args, **kwargs))
    clubs = load_clubs(CLUBS_PATH, "Ligue 1")
    # Deux minutes de jeu ne montrent pas toujours les deux choix : le tirage dépend du placement (le test cassait à chaque
    # ticket de placement, réserve A2 du ticket v2-realisme/02a). On joue donc des graines successives, 5 au plus, jusqu'à
    # voir les trois cas ; l'assertion reste la même.
    for seed in range(20260923, 20260928):
        random.seed(seed)
        match.simulate_match(clubs[0], clubs[1], duration_minutes=2.0)
        if {CONTRE_ATTAQUE, CONSERVATION} <= set(seen) and None in seen:
            break
    assert {CONTRE_ATTAQUE, CONSERVATION} <= set(seen) and None in seen


def _run_target(transition: TransitionPlay | None, situation: str, runs: dict) -> Vec2:
    holder, mate, rival = _p("H", x=40), _p("M", x=55, Off_the_Ball=99), _p("R", team="away", x=90, y=60)
    ball = BallState(position=holder.position, velocity=Vec2(0.0, 0.0), holder="H")
    random.seed(5)
    return cerveau.think(mate, ball, [holder, mate, rival], 1.0, runs, situation, None, None, transition).target


def test_teammate_ahead_of_the_ball_runs_into_depth_as_soon_as_he_perceives_the_counter() -> None:
    usual = _run_target(None, TRANSITION_OFFENSIVE, {})
    play = TransitionPlay(mode={"home": CONTRE_ATTAQUE})
    runs = {"M": (Vec2(65.0, 34.0), 61.0)}  # appel en cours, encore loin de son espace : il ne le lâcherait pas
    deep = _run_target(play, TRANSITION_OFFENSIVE, runs)
    assert deep != Vec2(65.0, 34.0) and abs((deep.x - usual.x) - COUNTER_RUN_DEPTH_M) < 1e-9
    assert play.launched == {"M"}
    # une seule relance : ensuite il garde son espace comme d'habitude
    assert _run_target(play, TRANSITION_OFFENSIVE, runs) == deep
    # pas encore perçu (délai de réaction) : appel en cours inchangé
    waiting = TransitionPlay(mode={"home": CONTRE_ATTAQUE})
    assert _run_target(waiting, DEFENSE_PLACEE, {"M": (Vec2(65.0, 34.0), 61.0)}) == Vec2(65.0, 34.0)
    assert waiting.launched == set()

"""Tests du hors-jeu (ticket v2-collectif/23) : loi 11 jugée AU DÉPART de la passe, coup franc indirect
seulement si le joueur signalé touche le ballon, appels réglés sur la ligne par Off the Ball, ligne défensive
qui peut monter (piège) et réaction décalée des défenseurs, « play the whistle » et sortie du fautif."""

from __future__ import annotations

import math
import random

from v2engine.ball_state import BallState
from v2engine.cerveau import HESITATION_INTENSITY, HORS_JEU, think
from v2engine.decision import evaluate_options
from v2engine.geometry import PITCH_LENGTH_M, Vec2
from v2engine.match import _award_offside_free_kick, _clear_offside, _step_ball
from v2engine.movement import PlayerState
from v2engine.offside import (
    OFFSIDE_OUT_S, OFFSIDE_TOLERANCE_M, PASS_MARGIN_REFERENCE_VISION,
    PASS_OFFSIDE_MARGIN_M, clamp_to_onside, is_clearly_offside, is_offside_position, keep_onside_probability,
    line_read_error_m, offside_at_pass, offside_line, pass_margin_m, perceived_defence_line, respects_the_line,
    second_last_defender_progress, sees_the_flag_probability,
)
from v2engine.trace import MatchTrace


def _p(name: str, x: float, y: float, poste: str = "MC", team: str = "home", **attrs: int) -> PlayerState:
    return PlayerState(name=name, team=team, poste=poste, position=Vec2(x, y), velocity=Vec2(0.0, 0.0), pace=60,
                       acceleration=60, stamina=60, home_target=Vec2(x, y), attributes=attrs or None)


def _defence(x_last: float = 82.0, x_third: float = 78.0) -> list[PlayerState]:
    """Défense extérieure devant le but x = 105 : gardien (dernier adversaire), dernier défenseur de champ (donc
    avant-dernier adversaire) et troisième adversaire. Domicile attaque vers x croissant."""
    return [_p("GK2", 101.0, 34.0, poste="GK", team="away"),
            _p("DL", x_last, 30.0, poste="DC", team="away"),
            _p("DS", x_third, 38.0, poste="DC", team="away"),
            _p("DM", 55.0, 20.0, team="away")]


# --- Le jugement (loi 11) -----------------------------------------------------------------------------------
def test_a_player_ahead_of_the_ball_and_the_second_last_defender_is_offside() -> None:
    defence = _defence()
    ball = Vec2(60.0, 34.0)
    assert math.isclose(second_last_defender_progress("home", defence), 82.0)  # le gardien est le dernier
    assert is_offside_position("home", Vec2(85.0, 34.0), ball, defence)


def test_level_with_the_second_last_defender_is_onside() -> None:
    defence = _defence()
    ball = Vec2(60.0, 34.0)
    assert not is_offside_position("home", Vec2(82.0 + OFFSIDE_TOLERANCE_M - 0.01, 34.0), ball, defence)


def test_no_offside_in_his_own_half() -> None:
    defence = [_p("GK2", 20.0, 34.0, poste="GK", team="away"), _p("DL", 18.0, 30.0, team="away")]
    assert not is_offside_position("home", Vec2(45.0, 34.0), Vec2(30.0, 34.0), defence)


def test_no_offside_behind_the_ball() -> None:
    defence = _defence()
    assert not is_offside_position("home", Vec2(55.0, 34.0), Vec2(60.0, 34.0), defence)


def test_check_is_symmetric_for_the_away_team() -> None:
    defence = [_p("GK", 4.0, 34.0, poste="GK", team="home"), _p("DL", 23.0, 30.0, team="home"),
               _p("DS", 27.0, 38.0, team="home")]
    ball = Vec2(45.0, 34.0)  # vu de l'extérieur, 60 m de son but
    assert is_offside_position("away", Vec2(20.0, 34.0), ball, defence)  # 85 m de son but, au-delà du 2e (78)
    assert not is_offside_position("away", Vec2(28.0, 34.0), ball, defence)


def test_only_the_flagged_players_at_the_departure_are_reported() -> None:
    defence = _defence()
    ball = Vec2(60.0, 34.0)
    mates = [_p("A1", 85.0, 34.0, poste="BU"), _p("A2", 70.0, 20.0), _p("A3", 50.0, 40.0)]
    assert offside_at_pass("home", ball, mates, defence) == {"A1"}
    assert offside_line("home", ball, defence) == 82.0


def test_without_a_second_opponent_nobody_is_offside() -> None:
    only_one = [_p("GK2", 101.0, 34.0, poste="GK", team="away")]
    assert second_last_defender_progress("home", only_one) is None
    assert not is_offside_position("home", Vec2(85.0, 34.0), Vec2(60.0, 34.0), only_one)


# --- Le coup franc et la sortie du fautif --------------------------------------------------------------------
def test_touching_the_ball_in_an_offside_position_gives_an_indirect_free_kick() -> None:
    ball = BallState(position=Vec2(80.0, 34.0), velocity=Vec2(4.0, 0.0))
    ball.offside_watch = {"A1"}
    players = [_p("A1", 80.0, 34.0, poste="BU"), *_defence()]
    events: list = []
    _step_ball(ball, 0.1, players, 10.0, offsides=events)
    assert [(e.player, e.team) for e in events] == [("A1", "home")]
    assert ball.holder == "DL"  # défenseur de champ le plus proche
    assert ball.offside_out_until["A1"] == 10.0 + OFFSIDE_OUT_S
    assert ball.offside_watch == set()
    _step_ball(ball, 0.1, players, 10.1, offsides=events)  # le sifflet ne tombe qu'une fois
    assert len(events) == 1


def test_the_free_kick_never_goes_to_the_keeper() -> None:
    """Directive du 28/10/2026 : jamais une passe en retrait au gardien, même s'il est le plus proche."""
    ball = BallState(position=Vec2(80.0, 34.0), velocity=Vec2(4.0, 0.0))
    ball.offside_watch = {"A1"}
    players = [_p("A1", 80.0, 34.0, poste="BU"),
               _p("GK2", 80.4, 34.0, poste="GK", team="away"),  # le plus proche, et pourtant exclu
               _p("DL", 92.0, 34.0, poste="DC", team="away")]
    _step_ball(ball, 0.1, players, 10.0, offsides=[])
    assert ball.holder == "DL"


def test_the_referee_does_not_blow_before_the_ball_is_touched() -> None:
    ball = BallState(position=Vec2(80.0, 34.0), velocity=Vec2(10.0, 0.0))
    ball.offside_watch = {"A1"}
    players = [_p("A1", 20.0, 34.0, poste="BU"), *_defence()]
    events: list = []
    _step_ball(ball, 0.1, players, 10.0, offsides=events)
    assert events == []
    assert ball.offside_watch == {"A1"}  # le signalement tient tant que la passe vit


def test_an_onside_player_receiving_clears_the_flag() -> None:
    random.seed(0)  # tirage de contrôle reproductible (First Touch 99, ballon à la vitesse idéale)
    ball = BallState(position=Vec2(70.0, 34.0), velocity=Vec2(6.0, 0.0))
    ball.offside_watch = {"A1"}
    receiver = _p("A2", 70.6, 34.0, **{"First Touch": 99})  # là où le ballon sera après ce tick
    players = [receiver, _p("A1", 85.0, 34.0, poste="BU"), *_defence()]
    _step_ball(ball, 0.1, players, 10.0, offsides=[])
    assert ball.holder == "A2"
    assert ball.offside_watch == set()


def test_the_offending_attacker_cannot_play_the_ball_while_he_steps_back(monkeypatch) -> None:
    """Directive du 28/10/2026 : le fautif est écarté de l'action 1,5 s -- il ne contrôle pas et il ne tacle pas."""
    ball = BallState(position=Vec2(80.0, 34.0), velocity=Vec2(0.0, 0.0))  # ballon libre à ses pieds
    ball.offside_out_until = {"A1": 100.0}
    attacker = _p("A1", 80.0, 34.0, poste="BU", **{"First Touch": 99})
    _step_ball(ball, 0.1, [attacker, *_defence()], 10.0, offsides=[])
    assert ball.holder is None  # il recule, il ne joue pas ce ballon

    ball = BallState(position=Vec2(80.0, 34.0), velocity=Vec2(0.0, 0.0), holder="DL")  # le preneur a le ballon
    ball.offside_out_until = {"A1": 1000.0}
    ball.next_decision_s = 1e9  # le preneur ne décide rien : seul le tacle peut changer le porteur
    taker = _p("DL", 80.0, 34.0, poste="DC", team="away")
    attacker = _p("A1", 81.0, 34.0, poste="BU", Aggression=99)
    # Tentative forcée : sans cela le test dépendrait du tirage d'Aggression (un joueur à 99 ne tente « que »
    # 5 fois par seconde) et pourrait passer à vide.
    monkeypatch.setattr("v2engine.match.should_attempt_tackle", lambda aggression, dt: True)
    for tick in range(3):
        _step_ball(ball, 0.1, [attacker, taker], tick * 0.1, offsides=[])
    assert "A1" not in ball.engaged  # il n'est même pas candidat au tacle
    assert ball.holder == "DL"


def test_the_offending_attacker_steps_back_after_the_whistle() -> None:
    ball = BallState(position=Vec2(80.0, 34.0), velocity=Vec2(0.0, 0.0))
    ball.offside_out_until = {"A1": 12.0}
    attacker = _p("A1", 80.0, 34.0, poste="BU")
    out = think(attacker, ball, [attacker], minute=0.1, runs={})  # 6 s : encore écarté
    assert out.role == HORS_JEU and out.action == "reculer"
    back = think(attacker, ball, [attacker], minute=0.25, runs={})  # 15 s : de retour dans le jeu
    assert back.role != HORS_JEU


def test_a_defender_who_sees_the_flag_hesitates_without_stopping() -> None:
    assert sees_the_flag_probability(99) > sees_the_flag_probability(55) > sees_the_flag_probability(11)
    ball = BallState(position=Vec2(80.0, 34.0), velocity=Vec2(0.0, 0.0), holder="A1")
    ball.hesitation = {"DL": 15.0}
    defender = _p("DL", 70.0, 30.0, poste="DC", team="away")
    holder = _p("A1", 80.0, 34.0, poste="BU")
    hesitation = think(defender, ball, [defender, holder], minute=0.1, runs={})  # 6 s < 15 s
    assert hesitation.reason == "il lève la main, il attend le sifflet"
    assert hesitation.intensity == HESITATION_INTENSITY
    after = think(defender, ball, [defender, holder], minute=0.3, runs={})  # 18 s : plus de flottement
    assert after.reason != "il lève la main, il attend le sifflet"


def test_the_hesitation_survives_the_end_of_the_pass_and_dies_with_the_whistle() -> None:
    """« Play the whistle » : le défenseur attend jusqu'à la fin de son flottement, même si la passe meurt avant
    (il ne sait pas encore que le drapeau ne se lèvera pas). Un coup franc, lui, remet tout le monde en jeu."""
    ball = BallState(position=Vec2(80.0, 34.0), velocity=Vec2(0.0, 0.0))
    ball.hesitation = {"DL": 15.0}
    _clear_offside(ball)
    assert ball.hesitation == {"DL": 15.0}
    _award_offside_free_kick(ball, _p("A1", 80.0, 34.0, poste="BU"), [_p("A1", 80.0, 34.0, poste="BU"), *_defence()],
                             10.0)
    assert ball.hesitation == {}


# --- Les appels réglés sur la ligne (Off the Ball) -----------------------------------------------------------
def test_off_the_ball_decides_who_respects_the_line() -> None:
    assert keep_onside_probability(99) > 0.9
    assert keep_onside_probability(11) < 0.6
    random.seed(7)
    high = sum(respects_the_line(_p("A", 80.0, 34.0, **{"Off the Ball": 99})) for _ in range(400))
    low = sum(respects_the_line(_p("B", 80.0, 34.0, **{"Off the Ball": 11})) for _ in range(400))
    assert high > low + 100  # 380 contre 220 environ


def test_the_passer_does_not_serve_a_mate_he_sees_clearly_offside(monkeypatch) -> None:
    """Ticket 23 : sans ce filtre, le porteur choisissait le coéquipier le plus avancé et le plus libre -- donc
    souvent celui qui était cinq mètres au-delà de la ligne. Mesuré : 21,5 hors-jeu par match au lieu de 3,4."""
    defence = _defence()  # ligne à 82 m de son but, ballon du porteur à 60 m
    near_line = _p("A1", 82.4, 34.0, poste="BU")  # 0,4 m au-delà : sous l'œil du passeur, il joue la passe
    far_beyond = _p("A2", 90.0, 20.0, poste="BU")  # 8 m au-delà : il le voit, il ne le sert pas
    ball = Vec2(60.0, 34.0)
    assert is_clearly_offside("home", far_beyond.position, ball, defence)
    assert not is_clearly_offside("home", near_line.position, ball, defence)
    # Câblage : la ligne perçue est fixée pour que le résultat ne dépende pas du tirage du porteur.
    monkeypatch.setattr("v2engine.decision.perceived_defence_line", lambda team, opponents, vision: 82.0)
    holder = _p("A4", 60.0, 34.0)
    # Seul A2 est disponible : le porteur préfère conduire plutôt que de le servir.
    options = evaluate_options(holder, [holder, far_beyond, *defence], Vec2(105.0, 34.0), None)
    assert all(a.kind != "pass" or a.target.name != "A2" for a in options)
    # A1 est à la limite mais dans la marge : il est bien proposé.
    options = evaluate_options(holder, [holder, near_line, *defence], Vec2(105.0, 34.0), None)
    assert next(a for a in options if a.kind == "pass").target.name == "A1"


# --- L'œil du passeur (Vision, deuxième passe du 28/10/2026) ------------------------------------------------
def test_the_blind_spot_narrows_as_the_passer_vision_grows() -> None:
    """Correction du 29/10/2026 (option S2) : la marge est un angle mort -- tout ce qu'elle dépasse la tolérance de
    l'arbitre est une passe sifflée. Elle se resserre donc avec la Vision, garde le seuil validé de 0,5 m pour un
    passeur moyen, et ne descend jamais sous la tolérance (le meilleur passeur ne refuse pas une passe légale)."""
    assert math.isclose(pass_margin_m(PASS_MARGIN_REFERENCE_VISION), PASS_OFFSIDE_MARGIN_M)  # Vision moyenne de la base
    margins = [pass_margin_m(v) for v in range(0, 101)]
    assert all(b <= a for a, b in zip(margins, margins[1:]))  # jamais plus large quand la Vision monte
    assert min(margins) >= OFFSIDE_TOLERANCE_M and math.isclose(pass_margin_m(100), OFFSIDE_TOLERANCE_M)
    assert pass_margin_m(11) > pass_margin_m(PASS_MARGIN_REFERENCE_VISION) > pass_margin_m(99)


def test_a_poor_passer_serves_a_mate_just_offside_that_a_great_one_refuses() -> None:
    """Même situation, seule la Vision change, lecture de la ligne parfaite (82 m). Le receveur à 0,4 m au-delà
    est hors-jeu pour l'arbitre : le passeur de Vision 11 ne le voit pas et le sert, celui de Vision 99 le voit et
    le refuse. Le receveur à 0,2 m au-delà est en jeu : les deux le servent."""
    defence = _defence()  # avant-dernier adversaire à 82 m, ballon à 60 m
    ball = Vec2(60.0, 34.0)
    offside_mate = _p("A1", 82.4, 34.0, poste="BU")
    onside_mate = _p("A2", 82.2, 34.0, poste="BU")
    assert offside_at_pass("home", ball, [offside_mate, onside_mate], defence) == {"A1"}  # l'arbitre, sans Vision
    assert not is_clearly_offside("home", offside_mate.position, ball, defence, pass_margin_m(11), 82.0)
    assert is_clearly_offside("home", offside_mate.position, ball, defence, pass_margin_m(99), 82.0)
    for vision in (11, 99):
        assert not is_clearly_offside("home", onside_mate.position, ball, defence, pass_margin_m(vision), 82.0)


def test_with_a_perfect_reading_no_passer_refuses_a_legal_pass() -> None:
    """Le meilleur passeur n'est jamais pénalisé : sur la vraie ligne, aucun coéquipier en jeu (jusqu'à la
    tolérance) n'est refusé, quelle que soit la Vision."""
    defence = _defence()
    ball = Vec2(60.0, 34.0)
    for vision in (0, 11, 55, 63.4, 80, 99, 100):
        for cm in range(-30, 31):
            mate = Vec2(82.0 + cm / 100.0, 34.0)
            assert not is_clearly_offside("home", mate, ball, defence, pass_margin_m(vision), 82.0), (vision, cm)


def test_better_vision_never_means_more_offside_errors(monkeypatch) -> None:
    """Banc discriminant réduit (audit du 29/10/2026) : vrai `evaluate_options`, un seul coéquipier toujours vu,
    placé de -0,3 à +1,2 m de la ligne ; seule la Vision du porteur varie. Erreurs = passes jouées vers un joueur
    réellement hors-jeu + passes légales refusées. Elles ne croissent pas avec la Vision, et restent possibles même
    chez les meilleurs (l'erreur de lecture de la ligne)."""
    defence = _defence()
    goal = Vec2(105.0, 34.0)
    monkeypatch.setattr("v2engine.decision.visible_teammates", lambda holder, mates, goal: mates)
    random.seed(20260923)
    offside_d = [0.31 + 0.05 * i for i in range(18)]
    onside_d = [-0.30 + 0.05 * i for i in range(13)]

    def played(vision: float, d: float, n: int = 60) -> float:
        holder = _p("A4", 60.0, 34.0, Vision=vision)
        mate = _p("A1", 82.0 + d, 34.0, poste="BU")
        return sum(any(a.kind == "pass" for a in evaluate_options(holder, [holder, mate, *defence], goal, None))
                   for _ in range(n)) / n

    errors = {}
    for vision in (11, 63.4, 99):
        whistled = sum(played(vision, d) for d in offside_d) / len(offside_d)
        refused = 1.0 - sum(played(vision, d) for d in onside_d) / len(onside_d)
        errors[vision] = whistled + refused
    assert errors[99] <= errors[63.4] + 0.01 <= errors[11] + 0.02, errors
    assert errors[63.4] > 0.0 and errors[99] > 0.0, errors


def test_the_line_the_passer_reads_is_wrong_by_at_most_his_vision_error() -> None:
    assert line_read_error_m(99) < line_read_error_m(55) < line_read_error_m(0)
    defence = _defence()
    random.seed(7)  # erreurs reproductibles : un passeur de Vision 0 surestime parfois, c'est la passe sifflée
    errors = [perceived_defence_line("home", defence, 0) - 82.0 for _ in range(200)]
    assert max(errors) > 0.1 and min(errors) < -0.1  # il se trompe dans les deux sens
    assert max(abs(e) for e in errors) <= line_read_error_m(0) + 1e-9


def test_a_perceived_line_turns_an_offside_mate_into_a_legal_one() -> None:
    """Le passeur qui surestime la ligne -- il ne voit pas le défenseur qui la tient -- sert un joueur hors-jeu,
    et l'arbitre siffle : c'est l'erreur humaine demandée le 28/10/2026."""
    defence = _defence()
    mate = _p("A1", 83.0, 34.0, poste="BU")  # 1 m au-delà de la vraie ligne
    ball = Vec2(60.0, 34.0)
    assert is_clearly_offside("home", mate.position, ball, defence, 0.5, 82.0)
    assert not is_clearly_offside("home", mate.position, ball, defence, 0.5, 84.0)  # ligne crue à 84 m


def test_the_offside_filter_uses_the_passer_own_margin(monkeypatch) -> None:
    """Câblage : `evaluate_options` lit bien `pass_margin_m` ET la ligne perçue (pas la ligne parfaite), avec la
    Vision du porteur en entrée."""
    defence = _defence()  # vraie ligne : 82 m
    holder = _p("A4", 60.0, 34.0, Vision=99)
    beyond = _p("A1", 83.5, 34.0, poste="BU")  # 1,5 m au-delà de la vraie ligne, seul coéquipier disponible
    squad = [holder, beyond, *defence]
    seen: list[float] = []

    def margin(vision: float) -> float:
        seen.append(vision)
        return 1.0  # bon passeur : il ose

    monkeypatch.setattr("v2engine.decision.visible_teammates", lambda holder, mates, goal: mates)
    monkeypatch.setattr("v2engine.decision.pass_margin_m", margin)
    # La VRAIE ligne (82 m) refuserait ce coéquipier, même avec 1 m de marge : seule une ligne crue plus haute
    # l'autorise -- c'est donc bien `perceived_defence_line` qui est lu, et non la ligne exacte.
    monkeypatch.setattr("v2engine.decision.perceived_defence_line", lambda team, opponents, vision: 85.0)
    assert next(a for a in evaluate_options(holder, squad, Vec2(105.0, 34.0), None)
                if a.kind == "pass").target.name == "A1"
    # Ligne crue plus basse que la vraie : il refuse un coéquipier à 82,8 m, que la vraie ligne autoriserait
    # (82,8 < 82 + 1,0) mais pas la ligne crue (82,8 > 80 + 1,0).
    close = _p("A1", 82.8, 34.0, poste="BU")
    monkeypatch.setattr("v2engine.decision.perceived_defence_line", lambda team, opponents, vision: 80.0)
    assert all(a.kind != "pass" for a in evaluate_options(holder, [holder, close, *defence], Vec2(105.0, 34.0), None))
    assert not is_clearly_offside("home", close.position, Vec2(60.0, 34.0), defence, 1.0, 82.0)
    # Et la Vision passée au seuil est bien celle du porteur, pas une constante.
    assert seen and set(seen) == {99}


def test_an_appel_that_respects_the_line_is_brought_back_just_behind_it() -> None:
    point = clamp_to_onside("home", Vec2(90.0, 20.0), 80.0)
    assert math.isclose(point.x, 79.0) and math.isclose(point.y, 20.0)
    assert clamp_to_onside("home", Vec2(40.0, 20.0), 80.0) == Vec2(40.0, 20.0)  # moitié défensive : intacte
    assert math.isclose(clamp_to_onside("away", Vec2(15.0, 20.0), 80.0).x, 26.0)  # symétrique pour l'extérieur


# --- Trace ---------------------------------------------------------------------------------------------------
def test_the_trace_records_the_whistle_and_where_it_happened() -> None:
    trace = MatchTrace(home="A", away="B", tick_seconds=1.0)
    ball = BallState(position=Vec2(80.0, 34.0), velocity=Vec2(4.0, 0.0))
    ball.offside_watch = {"A1"}
    players = [_p("A1", 80.0, 34.0, poste="BU"), *_defence()]
    _step_ball(ball, 0.1, players, 750.0, offsides=trace.offsides)  # 12 min 30
    event = trace.offsides[0]
    assert event.player == "A1" and event.team == "home"
    assert math.isclose(event.minute, 12.5) and event.x > 79.0 and event.y == 34.0


def test_the_offside_line_is_the_most_advanced_of_the_ball_and_the_second_last_defender() -> None:
    defence = _defence()
    assert offside_line("home", Vec2(90.0, 34.0), defence) == 90.0  # ballon plus avancé que le 2e défenseur
    assert math.isclose(PITCH_LENGTH_M, 105.0)

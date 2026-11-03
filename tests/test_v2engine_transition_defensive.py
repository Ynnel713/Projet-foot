"""Transition attaque-défense (ticket v2-collectif/10) : réaction à la perte (délai d'Anticipation), contre-pressing des
joueurs proches du ballon (hors les deux plus reculés), repli des autres à l'intensité de leur Work Rate."""

from __future__ import annotations

import random

from v2engine import cerveau
from v2engine.ball_state import BallState
from v2engine.bloc import Bloc
from v2engine.cerveau import APPEL, REPLI, Intention, think
from v2engine.defense import FOLLOW_M, DefensiveRoles, press_intensity
from v2engine.geometry import Vec2
from v2engine.movement import PlayerState
from v2engine.situation import POSSESSION_INSTALLEE, TRANSITION_DEFENSIVE, TRANSITION_OFFENSIVE


def _p(name: str, team: str = "home", x: float = 50.0, y: float = 34.0, poste: str = "MC", **attributes: int) -> PlayerState:
    return PlayerState(name=name, team=team, poste=poste, position=Vec2(x, y), velocity=Vec2(0.0, 0.0), pace=60,
                       acceleration=60, stamina=60, home_target=Vec2(x, y),
                       attributes={k.replace("_", " "): v for k, v in attributes.items()} or None)


def _loss(players: list[PlayerState], winner: str, situations: dict[str, str] | None) -> DefensiveRoles:
    """« Perdant » (domicile) a le ballon, puis `winner` (extérieur) le prend : une perte de domicile."""
    defense = DefensiveRoles()
    loser = next(p for p in players if p.name == "Perdant")
    defense.update(players, BallState(position=loser.position, velocity=Vec2(0.0, 0.0), holder="Perdant"), None, 0.0)
    holder = next(p for p in players if p.name == winner)
    defense.update(players, BallState(position=holder.position, velocity=Vec2(0.0, 0.0), holder=winner), None, 0.1,
                   situations)
    return defense


def _scene(holder_poste: str = "MC") -> list[PlayerState]:
    # domicile attaque vers x croissant : il perd le ballon à 70 m ; « Gagnant » le prend juste devant lui
    return [_p("Perdant", x=70, Teamwork=99), _p("Proche", x=62, y=40, Teamwork=99), _p("Loin", x=68, y=8, Teamwork=99),
            _p("Arrière1", x=58, y=30, poste="DC", Teamwork=99), _p("Arrière2", x=58, y=38, poste="DC", Teamwork=99),
            _p("Gagnant", team="away", x=71, poste=holder_poste), _p("R1", team="away", x=64, y=44),
            _p("R2", team="away", x=50, y=12)]


def test_loss_starts_a_counter_press_followed_near_the_ball_but_not_by_the_deepest() -> None:
    random.seed(1)
    players = _scene()
    defense = _loss(players, "Gagnant", {"home": TRANSITION_DEFENSIVE, "away": TRANSITION_OFFENSIVE})
    assert defense.trigger_until["home"] > 0.1
    assert defense.follows["Proche"] and defense.follows["Perdant"]  # à 15 m ou moins, Teamwork 99 : 95 %
    assert players[2].position.distance_to(players[5].position) > FOLLOW_M and not defense.follows["Loin"]
    # les deux plus reculés protègent l'axe, même à moins de 15 m du ballon
    assert not defense.follows["Arrière1"] and not defense.follows["Arrière2"]


def test_no_counter_press_on_a_goalkeeper_catch_nor_without_a_transition() -> None:
    assert "home" not in _loss(_scene("GK"), "Gagnant", {"home": TRANSITION_DEFENSIVE}).trigger_until
    # engagement après un but : la situation n'est pas une transition
    assert "home" not in _loss(_scene(), "Gagnant", {"home": "défense placée"}).trigger_until
    assert "home" not in _loss(_scene(), "Gagnant", None).trigger_until


def _bloc_scene(work_rate: int) -> tuple[PlayerState, BallState, list[PlayerState], Bloc]:
    ahead = _p("Devant", x=80, y=34, Work_Rate=work_rate, Teamwork=99)
    holder = _p("Porteur", team="away", x=60, y=34)
    players = [ahead, _p("D", x=30, y=34), holder, _p("A2", team="away", x=90, y=34)]
    bloc = Bloc.from_players(players)
    return ahead, BallState(position=holder.position, velocity=Vec2(0.0, 0.0), holder="Porteur"), players, bloc


def test_player_ahead_of_the_ball_retreats_at_his_work_rate_intensity() -> None:
    intensities = {}
    for note in (99, 11):
        ahead, ball, players, bloc = _bloc_scene(note)
        intention = think(ahead, ball, players, 1.0, {}, TRANSITION_DEFENSIVE, bloc, DefensiveRoles())
        assert intention.role == REPLI and intention.action == "se replier"
        assert intention.target.x < ahead.position.x  # il revient vers son but
        intensities[note] = intention.intensity
        assert intention.intensity == press_intensity(ahead)
    assert intensities[99] > intensities[11]


def test_retreat_ignores_the_teamwork_tolerance_but_only_in_defensive_transition() -> None:
    ahead, ball, players, bloc = _bloc_scene(55)
    place = bloc.target(ahead, ball.position, TRANSITION_DEFENSIVE, 60.0)
    near = PlayerState(**{**ahead.__dict__, "position": place + Vec2(1.5, 0.0)})  # sous sa tolérance (Teamwork 99 : 2 m)
    assert think(near, ball, players, 1.0, {}, TRANSITION_DEFENSIVE, bloc, DefensiveRoles()).role == REPLI
    assert think(near, ball, players, 1.0, {}, "défense placée", bloc, DefensiveRoles()).role == cerveau.REPLACEMENT


def test_until_he_perceives_the_loss_he_keeps_his_attacking_intention() -> None:
    ahead, ball, players, bloc = _bloc_scene(55)
    run = Intention(APPEL, "se démarquer", Vec2(95.0, 20.0), situation=POSSESSION_INSTALLEE)
    # situation perçue encore offensive (délai de réaction d'Anticipation, `SituationTracker.perceived`)
    assert think(ahead, ball, players, 1.0, {}, POSSESSION_INSTALLEE, bloc, DefensiveRoles(), previous=run) is run
    assert think(ahead, ball, players, 1.0, {}, TRANSITION_DEFENSIVE, bloc, DefensiveRoles(), previous=run).role == REPLI
    # un rôle défensif n'est pas prolongé
    hold = Intention(cerveau.REPLACEMENT, "tenir sa place", ahead.position)
    assert think(ahead, ball, players, 1.0, {}, POSSESSION_INSTALLEE, bloc, DefensiveRoles(), previous=hold) is not hold

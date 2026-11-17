"""Tests du moteur V2, ticket v2-attributs-contextes/03 réduit (repli après la perte mis au registre : Work Rate 0,7,
Teamwork 0,3, courbe du presseur inchangée). Voir .scratch/v2-attributs-contextes/issues/03-work-rate-offensif.md."""

from __future__ import annotations

import pytest

from v2engine.ball_state import BallState
from v2engine.bloc import Bloc
from v2engine.cerveau import REPLI, think
from v2engine.contextes import REPLI_APRES_LA_PERTE, contextual_rating
from v2engine.defense import DefensiveRoles, press_intensity, retreat_intensity
from v2engine.geometry import Vec2
from v2engine.situation import TRANSITION_DEFENSIVE
from tests.scenes import player


def test_retreat_follows_the_press_curve_on_the_context_note() -> None:
    # Work Rate et Teamwork égaux : même intensité qu'avant le ticket (courbe du presseur, Work Rate seul)
    for note in (11, 55, 99):
        p = player("P", Work_Rate=note, Teamwork=note)
        assert contextual_rating(p, REPLI_APRES_LA_PERTE) == pytest.approx(note)
        assert retreat_intensity(p) == pytest.approx(press_intensity(p))
    mixed = player("P", Work_Rate=99, Teamwork=11)  # 0,7 x 99 + 0,3 x 11 = 72,6
    assert contextual_rating(mixed, REPLI_APRES_LA_PERTE) == pytest.approx(72.6)
    assert press_intensity(player("P", Work_Rate=11)) < retreat_intensity(mixed) < press_intensity(mixed)


def test_teamwork_now_speeds_up_the_retreat_at_equal_work_rate() -> None:
    disciplined, loose = player("P", Work_Rate=55, Teamwork=99), player("P", Work_Rate=55, Teamwork=11)
    assert retreat_intensity(disciplined) > retreat_intensity(loose)
    # Work Rate garde la plus grande part : 99 / 11 contre 11 / 99
    assert retreat_intensity(player("P", Work_Rate=99, Teamwork=11)) > \
        retreat_intensity(player("P", Work_Rate=11, Teamwork=99))
    # le pressing, lui, reste à Work Rate seul
    assert press_intensity(disciplined) == pytest.approx(press_intensity(loose))


def test_the_retreating_player_runs_at_the_context_intensity() -> None:
    intensities = {}
    for teamwork in (99, 11):
        ahead = player("Devant", x=80, y=34, Work_Rate=55, Teamwork=teamwork)
        holder = player("Porteur", team="away", x=60, y=34)
        players = [ahead, player("D", x=30, y=34), holder, player("A2", team="away", x=90, y=34)]
        ball = BallState(position=holder.position, velocity=Vec2(0.0, 0.0), holder="Porteur")
        intention = think(ahead, ball, players, 1.0, {}, TRANSITION_DEFENSIVE, Bloc.from_players(players),
                          DefensiveRoles())
        assert intention.role == REPLI
        intensities[teamwork] = intention.intensity
    assert intensities[99] > intensities[11]

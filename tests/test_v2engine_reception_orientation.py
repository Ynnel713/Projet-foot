"""Temps de contrôle selon l'orientation (ticket v2-realisme/07d) : un contrôle non orienté dure plus ou moins selon le
type de réception au contact (07c) : de profil x 0,85, de face x 0,95, dos au jeu x 1,35 ; un ballon reçu dans le dos d'un
joueur non lancé compte dos au jeu (contrôle à l'aveugle, condition A1 de l'expert au 07c) ; un contrôle orienté (31b)
n'en dépend pas."""

from __future__ import annotations

from dataclasses import replace

import pytest

from v2engine.ball_state import BallState
from v2engine.geometry import Vec2
from v2engine.match import _step_ball
from v2engine.possession import RECEPTION_KIND_FACTORS, reception_delay_s
from v2engine.reception import DE_FACE, DE_PROFIL, DOS_AU_JEU, blind_reception
from tests.scenes import player


def test_back_to_play_is_slower_and_open_body_faster_for_a_plain_control() -> None:
    receiver = player("R", **{"First_Touch": 55})
    plain = {kind: reception_delay_s(receiver, oriented=False, kind=kind) for kind in (DE_PROFIL, DE_FACE, DOS_AU_JEU)}
    assert plain[DE_PROFIL] == pytest.approx(3.22 * 0.85)
    assert plain[DE_FACE] == pytest.approx(3.22 * 0.95)
    assert plain[DOS_AU_JEU] == pytest.approx(3.22 * 1.35)
    assert plain[DE_PROFIL] < plain[DE_FACE] < plain[DOS_AU_JEU]


def test_oriented_control_does_not_depend_on_the_reception_kind() -> None:
    receiver = player("R", **{"First_Touch": 55})
    for kind in (DE_PROFIL, DE_FACE, DOS_AU_JEU):
        assert reception_delay_s(receiver, oriented=True, kind=kind) == pytest.approx(1.38)


def test_factors_average_one_on_the_measured_geometric_shares() -> None:
    """Répartition par type géométrique (07c) mesurée avant le code : moyenne 1,01. Le contrôle à l'aveugle, ajouté sans
    renormaliser (option A validée par le propriétaire), la relève (environ 1,11 attendu) : le rythme ralentit un peu."""
    shares = {DE_FACE: 0.604, DE_PROFIL: 0.190, DOS_AU_JEU: 0.206}  # 1 250 contrôles non orientés, 4 matchs, 13/11/2026
    assert sum(shares[k] * RECEPTION_KIND_FACTORS[k] for k in shares) == pytest.approx(1.0, abs=0.015)


def _control(monkeypatch, facing: Vec2, ball_velocity: Vec2, receiver_velocity: Vec2 = Vec2(0.0, 0.0)):
    """Contrôle non orienté d'un receveur de l'équipe qui attaque vers x croissant ; rend le ballon après le contact."""
    monkeypatch.setattr("v2engine.match.attempt_control", lambda *args: True)
    monkeypatch.setattr("v2engine.match.orients_control", lambda *args: False)
    monkeypatch.setattr("v2engine.match.thinks_one_touch", lambda *args: False)
    receiver = replace(player("R", x=50.0, y=34.0, **{"First_Touch": 55}), facing=facing, velocity=receiver_velocity)
    start = Vec2(50.0, 34.0) - ball_velocity.normalized() * 0.4  # le ballon touche le receveur dans ce pas
    ball = BallState(position=start, velocity=ball_velocity, receiver="R", released_by="P")
    _step_ball(ball, 0.1, [receiver, player("P", x=10.0, y=10.0)], 10.0, None, None, None)
    assert ball.holder == "R"
    return ball


@pytest.mark.parametrize("facing, ball_velocity, kind_factor", [
    (Vec2(1.0, 0.0), Vec2(-6.0, 0.0), 0.95),  # de face, ballon devant lui
    (Vec2(0.0, 1.0), Vec2(0.0, -6.0), 0.85),  # de profil, ballon devant lui
    (Vec2(-1.0, 0.0), Vec2(6.0, 0.0), 1.35),  # dos au jeu, ballon devant lui
])
def test_the_match_applies_the_kind_seen_at_the_touch(monkeypatch, facing: Vec2, ball_velocity: Vec2,
                                                      kind_factor: float) -> None:
    ball = _control(monkeypatch, facing, ball_velocity)
    assert ball.next_decision_s == pytest.approx(10.0 + 3.22 * kind_factor)


@pytest.mark.parametrize("facing", [Vec2(1.0, 0.0), Vec2(0.0, 1.0)])
def test_ball_in_the_back_of_a_standing_player_counts_as_back_to_play(monkeypatch, facing: Vec2) -> None:
    """Condition A1 de l'expert au 07c : cap vers le but (ou de profil), ballon qui arrive de derrière, joueur arrêté :
    contrôle à l'aveugle, compté dos au jeu (x 1,35 au lieu de x 0,95 ou x 0,85)."""
    behind = facing * -1.0  # le ballon vient de derrière lui : il se déplace dans le sens de son cap
    ball = _control(monkeypatch, facing, facing * 6.0)
    assert behind.length() > 0.0
    assert ball.next_decision_s == pytest.approx(10.0 + 3.22 * 1.35)


def test_a_running_player_taking_the_ball_in_his_stride_keeps_his_reception_kind(monkeypatch) -> None:
    """Receveur lancé (au-dessus de 19,8 km/h) qui prend une passe en profondeur face au but : pas « à l'aveugle »."""
    ball = _control(monkeypatch, Vec2(1.0, 0.0), Vec2(8.0, 0.0), receiver_velocity=Vec2(6.0, 0.0))
    assert ball.next_decision_s == pytest.approx(10.0 + 3.22 * 0.95)


def test_blind_reception_rule() -> None:
    east = Vec2(1.0, 0.0)
    assert blind_reception(east, Vec2(6.0, 0.0), running=False)  # ballon dans le dos
    assert not blind_reception(east, Vec2(6.0, 0.0), running=True)  # lancé
    assert not blind_reception(east, Vec2(-6.0, 0.0), running=False)  # ballon devant
    assert not blind_reception(east, Vec2(0.0, 6.0), running=False)  # pile à 90° : pas au-delà
    assert not blind_reception(east, Vec2(0.0, 0.0), running=False)  # ballon arrêté

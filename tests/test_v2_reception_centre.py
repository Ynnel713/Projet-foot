"""Réception « centre » réservée au ballon reçu à sa première retombée (ticket v2-hauteur-ballon/02c) : un ballon en vol
qui n'a pas encore touché le sol depuis son lancement est reçu comme un centre ; après un rebond, comme une passe
ordinaire. Le filtre de contact en hauteur (bas du ballon au-dessus de 0,5 m : pas touché) est inchangé."""

from __future__ import annotations

import pytest

from v2engine.ball_state import BallState
from v2engine.geometry import Vec2
from v2engine.hauteur import AERIAL_THRESHOLD_M, step_height
from v2engine.match import (RECEIVER_REACH_M, TICK_SECONDS, _danger_origin, _ground, _ball_contacts, _launch_aerial,
                           _step_ball)
from tests.scenes import player

DT = 0.1
SPEED = 30.0  # m/s : le ballon parcourt 3 m par pas, au-delà du joueur (instant d'entrée exact dans `_contacts`)
AT = Vec2(60.0, 34.0)  # receveur « home »
SIDE_M = 0.6  # le ballon passe à 0,6 m du receveur : il entre à sa portée 0,8 m avant lui
PASS_FROM = Vec2(55.0, 34.0)  # 5 m gagnés : « passe au sol » selon `_pass_kind`


def _receive(monkeypatch, z: float, vz: float, landed: bool, entry_s: float = 0.01, one_touch: bool = False):
    """Un pas de ballon libre vers le receveur visé `R`, qui entre à sa portée `entry_s` après le début du pas ; rend
    l'événement de réception."""
    monkeypatch.setattr("v2engine.match.attempt_control", lambda *a, **k: True)
    monkeypatch.setattr("v2engine.match.thinks_one_touch", lambda *a, **k: one_touch)
    receiver = player("R", x=AT.x, y=AT.y)
    back = (RECEIVER_REACH_M ** 2 - SIDE_M ** 2) ** 0.5
    start = Vec2(AT.x - back - SPEED * entry_s, AT.y - SIDE_M)
    entry = _ball_contacts(start, start + Vec2(SPEED * DT, 0.0), DT, [receiver], BallState(start, Vec2(SPEED, 0.0), receiver="R"))
    assert entry[0][0] * DT == pytest.approx(entry_s)
    ball = BallState(position=start, velocity=Vec2(SPEED, 0.0), receiver="R", last_pass_team="home",
                     pass_from=PASS_FROM, z=z, vz=vz, landed=landed)
    receptions: list = []
    _step_ball(ball, DT, [receiver], 0.0, receptions=receptions)
    assert ball.holder == "R" and len(receptions) == 1
    return receptions[0]


def test_premiere_retombee_recue_en_centre(monkeypatch) -> None:
    assert step_height(0.3, -1.0, DT).first_contact_s is None  # pas d'impact dans le pas
    assert _receive(monkeypatch, 0.3, -1.0, landed=False).origin == "centre"


def test_apres_un_rebond_passe_ordinaire(monkeypatch) -> None:
    assert _receive(monkeypatch, 0.3, -1.0, landed=True).origin == "passe au sol"


def test_ballon_en_montee_passe_ordinaire(monkeypatch) -> None:
    """Décision du propriétaire (27/11/2026) : touché en montée, juste après la frappe, le ballon est reçu comme une
    passe ordinaire ; « centre » est réservé au ballon qui redescend."""
    assert _receive(monkeypatch, 0.0, 9.0, landed=False).origin == "passe au sol"


def test_ballon_au_sol_passe_ordinaire(monkeypatch) -> None:
    assert _receive(monkeypatch, 0.0, 0.0, landed=False).origin == "passe au sol"


@pytest.mark.parametrize("entry_s, expected", [(0.01, "centre"), (0.06, "passe au sol")])
def test_impact_dans_le_pas_du_contact(monkeypatch, entry_s: float, expected: str) -> None:
    """Le ballon touche le sol à ~0,042 s dans le pas : entré avant, le joueur le cueille à sa première retombée ;
    après, le ballon a rebondi."""
    impact = step_height(0.05, -1.0, DT).first_contact_s
    assert impact is not None and 0.02 < impact < 0.07
    assert _receive(monkeypatch, 0.05, -1.0, landed=False, entry_s=entry_s).origin == expected


@pytest.mark.parametrize("landed, first_time", [(False, False), (True, True)])
def test_jeu_de_premiere_interdit_a_la_premiere_retombee(monkeypatch, landed: bool, first_time: bool) -> None:
    """Décision du propriétaire (27/11/2026) : pas de jeu de première sur un ballon cueilli à sa première retombée ;
    permis après un rebond."""
    assert _receive(monkeypatch, 0.3, -1.0, landed=landed, one_touch=True).first_time is first_time


@pytest.mark.parametrize("landed, expected", [(False, "centre"), (True, "passe au sol")])
def test_danger_origin_meme_regle(landed: bool, expected: str) -> None:
    mate = player("R", x=AT.x, y=AT.y)
    ball = BallState(position=Vec2(58.0, 34.0), velocity=Vec2(SPEED, 0.0), last_pass_team="home",
                     pass_from=PASS_FROM, z=1.0, vz=-2.0, landed=landed)
    assert _danger_origin(ball, mate) == expected
    ball.z, ball.vz = 0.0, 0.0
    assert _danger_origin(ball, mate) == "passe au sol"  # au sol : jamais « centre »
    ball.z, ball.vz = 1.0, 2.0
    assert _danger_origin(ball, mate) == "passe au sol"  # en montée : pas « centre »


def test_ballon_qui_remonte_au_dessus_du_seuil_n_est_pas_touche(monkeypatch) -> None:
    """Filtre de contact préservé (réserve A1 du ticket) : après un rebond, un ballon dont le bas reste au-dessus de
    0,5 m sur tout le pas passe au-dessus du joueur."""
    monkeypatch.setattr("v2engine.match.attempt_control", lambda *a, **k: True)
    z0, vz0 = 0.6, 2.0
    assert step_height(z0, vz0, DT).z > AERIAL_THRESHOLD_M
    ball = BallState(position=Vec2(AT.x - 0.5, AT.y), velocity=Vec2(SPEED, 0.0), receiver="R", last_pass_team="home",
                     pass_from=PASS_FROM, z=z0, vz=vz0, landed=True)
    _step_ball(ball, DT, [player("R", x=AT.x, y=AT.y)], 0.0)
    assert ball.holder is None


def test_etat_touche_le_sol_au_lancement_au_rebond_et_pose() -> None:
    ball = BallState(position=Vec2(10.0, 34.0), velocity=Vec2(20.0, 0.0), landed=True)
    _launch_aerial(ball, 25.0)
    assert not ball.landed and not ball.first_drop  # en montée : pas encore une retombée
    for i in range(100):
        contact = step_height(ball.z, ball.vz, TICK_SECONDS).first_contact_s
        _step_ball(ball, TICK_SECONDS, [], i * TICK_SECONDS)
        if contact is not None:
            break
        assert ball.first_drop is (ball.vz < 0.0)
    assert ball.landed and not ball.first_drop
    _ground(ball)
    assert not ball.landed and not ball.first_drop

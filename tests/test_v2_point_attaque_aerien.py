"""Point d'attaque d'un ballon aérien (ticket v2-realisme/15a1) : sur le premier vol d'un ballon en l'air, le premier
point où le ballon passe sous un plafond donné (par défaut la tête en saut) et que le joueur atteint à temps (traînée
seule en vol, ticket 14a2b), sinon le point de chute. Le receveur, que personne ne conteste ici, vise ce point à hauteur
de poitrine (décision du propriétaire du 27/11/2026) ; au sol ou après le premier rebond, `meeting_point` inchangé. Voir
.scratch/v2-realisme/issues/15a1-point-d-attaque-aerien.md."""

from __future__ import annotations

import pytest

from v2engine import anticipation, cerveau, defense, freinage
from v2engine.anticipation import (ARRIVAL_EPSILON_S, aerial_attack_point, meeting_point, receiving_point)
from v2engine.ball_state import BallState
from v2engine.cerveau import RECEVEUR, Perception, decide
from v2engine.condition import effective_rating
from v2engine.geometry import Vec2
from v2engine.hauteur import height_at, step_height, time_to_ground
from v2engine.match import TICK_SECONDS, _launch_aerial, _step_ball
from v2engine.movement import max_speed_mps
from v2engine.portee import CORPS, PIED, SHOULDER_SHARE, TETE, player_body_ceiling_m, player_ceiling_m, player_height_m
from tests.scenes import player

START = Vec2(30.0, 34.0)
PASS_M = 40.0
SPEED = 20.0  # m/s horizontaux : passe lobée de 40 m


def _lofted() -> BallState:
    ball = BallState(position=START, velocity=Vec2(SPEED, 0.0), receiver="R", last_pass_team="home")
    _launch_aerial(ball, PASS_M)
    return ball


def _engine_landing(ball: BallState) -> tuple[Vec2, float]:
    """Point et instant de chute réels : le moteur au pas, sans joueur, jusqu'au premier contact au sol."""
    ball = BallState(position=ball.position, velocity=ball.velocity, z=ball.z, vz=ball.vz)
    elapsed = 0.0
    for _ in range(200):
        hit = step_height(ball.z, ball.vz, TICK_SECONDS).first_contact_s
        if hit is not None:
            return ball.position + ball.velocity * hit, elapsed + hit
        _step_ball(ball, TICK_SECONDS, [], elapsed)
        elapsed += TICK_SECONDS
    raise AssertionError("le ballon ne retombe pas")


def _reached_in_time(p, point: Vec2, t: float) -> bool:
    return p.position.distance_to(point) / max_speed_mps(effective_rating(p, "Pace")) <= t + ARRIVAL_EPSILON_S


def test_hors_d_atteinte_pendant_le_vol_point_de_chute_reel() -> None:
    """Receveur à 25 m du point de chute, sur le côté : il n'atteint aucun point du vol à temps ; il vise le point de
    chute, à moins de 1 m du point réel du moteur. `meeting_point` (loi au sol) visait plus court."""
    ball = _lofted()
    landing, _ = _engine_landing(ball)
    receiver = player("R", x=landing.x, y=landing.y - 25.0)
    point = aerial_attack_point(receiver, ball.position, ball.velocity, ball.z, ball.vz)
    assert point.distance_to(landing) < 1.0
    assert landing.distance_to(START) == pytest.approx(PASS_M, abs=1.0)  # le ballon retombe sur le point visé
    ground = meeting_point(receiver, ball.position, ball.velocity)
    assert ground.x < landing.x - 1.0  # l'ancienne cible, au sol, était trop courte


def test_sous_la_trajectoire_premier_point_sous_son_plafond_atteint_a_temps() -> None:
    """Receveur sur la ligne de la passe, 5 m avant le point de chute : il vise le premier point du vol où le ballon
    passe sous son plafond et qu'il atteint à temps, avant le point de chute."""
    ball = _lofted()
    landing, _ = _engine_landing(ball)
    receiver = player("R", x=landing.x - 5.0, y=34.0)
    point = aerial_attack_point(receiver, ball.position, ball.velocity, ball.z, ball.vz)
    assert START.x < point.x < landing.x - 0.5
    t = freinage.travel_time_s(point.x - START.x, SPEED, airborne=True)
    assert height_at(ball.z, ball.vz, t)[0] <= player_ceiling_m(receiver) + 1e-6
    assert _reached_in_time(receiver, point, t)


def test_ballon_au_dessus_de_lui_il_attend_la_redescente() -> None:
    """Receveur sous le sommet de la trajectoire : le ballon passe au-dessus de son plafond ; il le joue plus loin, à
    la redescente, pas à la verticale de sa position."""
    ball = _lofted()
    flight = time_to_ground(ball.z, ball.vz)
    apex_x = START.x + freinage.distance_after(SPEED, flight / 2.0, airborne=True)
    receiver = player("R", x=apex_x, y=34.0)
    assert height_at(ball.z, ball.vz, flight / 2.0)[0] > player_ceiling_m(receiver)
    point = aerial_attack_point(receiver, ball.position, ball.velocity, ball.z, ball.vz)
    assert point.x > apex_x + 1.0


def test_meme_point_a_l_epsilon_pres_sur_deux_appels() -> None:
    ball = _lofted()
    receiver = player("R", x=62.0, y=40.0)
    first = aerial_attack_point(receiver, ball.position, ball.velocity, ball.z, ball.vz)
    assert aerial_attack_point(receiver, ball.position, ball.velocity, ball.z, ball.vz) == first


@pytest.mark.parametrize("z, vz, landed", [(0.0, 0.0, False), (0.8, -2.0, True), (0.0, 3.0, True)])
def test_au_sol_ou_apres_le_premier_rebond_meeting_point(z: float, vz: float, landed: bool) -> None:
    receiver = player("R", x=60.0, y=36.0)
    ball = BallState(position=START, velocity=Vec2(SPEED, 0.0), receiver="R", z=z, vz=vz, landed=landed)
    assert receiving_point(receiver, ball) == meeting_point(receiver, ball.position, ball.velocity)


def test_premier_vol_point_d_attaque() -> None:
    ball = _lofted()
    receiver = player("R", x=65.0, y=34.0)
    assert receiving_point(receiver, ball) == aerial_attack_point(receiver, ball.position, ball.velocity, ball.z, ball.vz,
                                                                  player_body_ceiling_m(receiver))


def test_receveur_et_defense_lisent_le_meme_point() -> None:
    """Le receveur (`cerveau.decide`) vise `receiving_point` ; la défense lit la même fonction pour son point de
    réception (aucun des deux ne lit plus `meeting_point` directement)."""
    assert cerveau.receiving_point is anticipation.receiving_point
    assert defense.receiving_point is anticipation.receiving_point
    assert not hasattr(cerveau, "meeting_point") and not hasattr(defense, "meeting_point")
    ball = _lofted()
    receiver = player("R", x=65.0, y=34.0)
    seen = Perception(holder=None, is_receiver=True, read_point=None, ball_distance=ball.position.distance_to(receiver.position))
    intention = decide(receiver, RECEVEUR, ball, seen, [receiver], 10.0, None)
    assert intention.target == receiving_point(receiver, ball)


def test_receveur_vise_la_poitrine_apres_le_point_sous_la_tete() -> None:
    """Décision du propriétaire (27/11/2026) : le receveur que personne ne conteste va chercher le ballon sous son
    épaule (0,818 × taille), plus loin sur la descente que le point sous sa tête (réservé au ballon disputé, 15a2)."""
    ball = _lofted()
    receiver = player("R", x=65.0, y=34.0)
    assert player_body_ceiling_m(receiver) == pytest.approx(SHOULDER_SHARE * player_height_m(receiver))
    head = aerial_attack_point(receiver, ball.position, ball.velocity, ball.z, ball.vz)
    chest = receiving_point(receiver, ball)
    assert chest == aerial_attack_point(receiver, ball.position, ball.velocity, ball.z, ball.vz,
                                        player_body_ceiling_m(receiver))
    assert head.x < chest.x
    t = freinage.travel_time_s(chest.x - START.x, SPEED, airborne=True)
    assert height_at(ball.z, ball.vz, t)[0] <= player_body_ceiling_m(receiver) + 1e-6
    assert _reached_in_time(receiver, chest, t)


def test_gardien_dans_sa_surface_ses_mains() -> None:
    keeper = player("G", x=10.0, y=34.0, poste="GK")
    assert player_body_ceiling_m(keeper) == player_ceiling_m(keeper)
    outside = player("G", x=40.0, y=34.0, poste="GK")
    assert player_body_ceiling_m(outside) == pytest.approx(SHOULDER_SHARE * player_height_m(outside))


def _contact_band(monkeypatch, name: str, receiver: str | None, landed: bool = False, cross: bool = False) -> str:
    """Passe lobée de 40 m vers `receiver` ; le joueur `name` attend au point poitrine du receveur ; rend la tranche
    du contact (moteur au pas)."""
    monkeypatch.setattr("v2engine.match.attempt_control", lambda *a, **k: True)
    ball = _lofted()
    ball.receiver = receiver
    ball.landed = landed
    ball.set_piece_cross = cross
    spot = receiving_point(player("R", x=65.0, y=34.0), _lofted())
    waiting = player(name, x=spot.x, y=spot.y)
    receptions: list = []
    elapsed = 0.0
    for _ in range(80):
        _step_ball(ball, TICK_SECONDS, [waiting], elapsed, receptions=receptions)
        elapsed += TICK_SECONDS
        if receptions:
            return receptions[0].band
    raise AssertionError("aucun contact")


def test_le_receveur_laisse_descendre_le_ballon_jusqu_a_sa_poitrine(monkeypatch) -> None:
    """Option A du propriétaire (27/11/2026) : sur le premier vol de sa passe, le receveur visé joue le ballon sous sa
    poitrine, pas de la tête ; un autre joueur au même endroit le prend de la tête (règle du 03a inchangée)."""
    assert _contact_band(monkeypatch, "R", receiver="R") in (CORPS, PIED)
    assert _contact_band(monkeypatch, "X", receiver="R") == TETE


def test_contact_ceiling_ordinaire_hors_premier_vol() -> None:
    from v2engine.match import _contact_ceiling
    receiver = player("R", x=65.0, y=34.0)
    ball = _lofted()
    assert _contact_ceiling(receiver, ball, True) == player_body_ceiling_m(receiver)
    assert _contact_ceiling(receiver, ball, False) == player_ceiling_m(receiver)
    assert _contact_ceiling(player("X", x=65.0, y=34.0), ball, True) == player_ceiling_m(receiver)



def test_centre_de_coup_de_pied_arrete_le_receveur_garde_sa_tete(monkeypatch) -> None:
    """Option 2 du propriétaire (28/11/2026, réserve A1 de l'expert) : sur un centre de coup de pied arrêté dans la
    surface, le receveur visé attaque le ballon de la tête (point sous la tête, plafond du 03a), comme un défenseur."""
    assert _contact_band(monkeypatch, "R", receiver="R", cross=True) == TETE
    receiver = player("R", x=65.0, y=34.0)
    ball = _lofted()
    ball.set_piece_cross = True
    assert receiving_point(receiver, ball) == aerial_attack_point(receiver, ball.position, ball.velocity, ball.z, ball.vz)
    from v2engine.match import _contact_ceiling
    assert _contact_ceiling(receiver, ball, True) == player_ceiling_m(receiver)


@pytest.mark.parametrize("kind, spot, target_at, cross", [
    ("corner", Vec2(105.0, 0.0), Vec2(97.0, 34.0), True),  # corner centré dans la surface adverse
    ("sortie de but", Vec2(5.5, 34.0), Vec2(60.0, 34.0), False),  # relance longue : option A
])
def test_remise_aerienne_marque_le_centre_seulement_dans_la_surface(monkeypatch, kind: str, spot: Vec2,
                                                                     target_at: Vec2, cross: bool) -> None:
    from v2engine.match import _play_restart
    from v2engine.restart import Restart
    taker = player("T", x=spot.x, y=spot.y)
    target = player("R", x=target_at.x, y=target_at.y)
    monkeypatch.setattr("v2engine.match.restart_target", lambda *a, **k: target)
    ball = BallState(position=spot, velocity=Vec2(0.0, 0.0),
                     restart=Restart(kind, "home", spot, "T", until_s=0.0, minute=10.0))
    _play_restart(ball, [taker, target], 1.0, None)
    assert ball.receiver == "R" and ball.vz > 0.0  # lancée en l'air
    assert ball.set_piece_cross is cross

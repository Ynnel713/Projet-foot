"""Contre physique (ticket v2-realisme/05c) : le tir en vol touche un défenseur de champ qui passe à sa portée (son corps
avant le temps de réaction, jambe tendue ensuite) ; au contact, il contre avec la chance `BLOCK_CHANCE`. Plus de tirage
du contreur au départ du tir."""

from __future__ import annotations

from v2engine import match
from v2engine.ball_state import BallState
from v2engine.decision import Action
from v2engine.flux import TIR
from v2engine.geometry import PITCH_LENGTH_M, Vec2
from v2engine.match import GOAL_CENTER_Y, _step_ball
from v2engine.movement import PlayerState
from v2engine.shooting import BLOCK_BODY_M, BLOCK_REACTION_S, BLOCK_WIDTH_M, FLYING, block_reach_m

SHOOTER_AT = Vec2(PITCH_LENGTH_M - 20.0, GOAL_CENTER_Y)


def _player(name: str, team: str, poste: str, position: Vec2) -> PlayerState:
    return PlayerState(name=name, team=team, poste=poste, position=position, velocity=Vec2(0.0, 0.0), pace=60,
                       acceleration=60, stamina=60, home_target=position, attributes=None)


def _shoot(monkeypatch, defender_at: Vec2, error=None):
    """Un tir de 20 m face au but, un défenseur en `defender_at` ; retourne (tir tracé, ballon). `error` impose l'écart
    du tir, sinon il est tiré comme en match."""
    shooter = _player("Buteur", "home", "BU", SHOOTER_AT)
    keeper = _player("Gardien", "away", "GK", Vec2(PITCH_LENGTH_M - 1.0, GOAL_CENTER_Y))
    defender = _player("Defenseur", "away", "DC", defender_at)
    monkeypatch.setattr(match, "should_attempt_tackle", lambda aggression, dt: False)
    monkeypatch.setattr(match, "choose_action", lambda *args: Action("shot", 1.0))
    if error is not None:
        monkeypatch.setattr(match, "draw_shot_error", lambda *args: error)
    ball = BallState(position=shooter.position, velocity=Vec2(0.0, 0.0), holder="Buteur")
    shots = []
    for tick in range(15):
        _step_ball(ball, 0.1, [shooter, keeper, defender], tick * 0.1, shots=shots)
        if shots and shots[0].outcome != FLYING:
            break
    return shots[0], ball


def _blocked_share(monkeypatch, defender_at: Vec2, n: int = 300) -> float:
    blocked = 0
    for k in range(n):
        TIR.seed(k)
        blocked += _shoot(monkeypatch, defender_at)[0].outcome == "contré"
    return blocked / n


def test_the_reach_is_the_body_before_the_reaction_time_and_the_leg_after() -> None:
    assert block_reach_m(0.0) == block_reach_m(BLOCK_REACTION_S - 0.01) == BLOCK_BODY_M
    assert block_reach_m(BLOCK_REACTION_S) == BLOCK_WIDTH_M


def test_a_defender_close_in_the_line_blocks_more_often_than_a_far_one_and_never_off_the_line(monkeypatch) -> None:
    close = _blocked_share(monkeypatch, SHOOTER_AT + Vec2(1.0, 0.0))
    far = _blocked_share(monkeypatch, SHOOTER_AT + Vec2(8.0, 0.0))
    off = _blocked_share(monkeypatch, SHOOTER_AT + Vec2(5.0, 5.0))
    assert close > far + 0.1 and far > 0.1  # attendu : environ 0,55 contre 0,3
    assert off == 0.0


def test_the_block_happens_in_flight_and_is_traced_where_the_ball_touched_him(monkeypatch) -> None:
    monkeypatch.setattr(match, "BLOCK_CHANCE", 1.0)
    defender_at = SHOOTER_AT + Vec2(8.0, 0.6)  # 0,6 m de l'axe : jambe tendue (le ballon arrive après la réaction)
    shot, ball = _shoot(monkeypatch, defender_at, error=(0.0, 0.0))
    assert shot.outcome == "contré" and ball.last_toucher == "Defenseur" and ball.rebound and not ball.shot_in_flight
    contact = Vec2(shot.block_x, shot.block_y)
    assert abs(contact.y - GOAL_CENTER_Y) < 1e-6 and contact.distance_to(defender_at) <= BLOCK_WIDTH_M + 1e-6


def test_the_body_alone_cannot_reach_a_ball_passing_beside_him_at_once(monkeypatch) -> None:
    # à 1 m du tireur, 0,6 m de l'axe : le ballon passe avant qu'il tende la jambe, son corps (0,41 m) ne l'atteint pas
    monkeypatch.setattr(match, "BLOCK_CHANCE", 1.0)
    shot, _ = _shoot(monkeypatch, SHOOTER_AT + Vec2(1.0, 0.6), error=(0.0, 0.0))
    assert shot.outcome != "contré"


def test_the_shot_is_not_blocked_at_the_strike_any_more(monkeypatch) -> None:
    # garde : au départ, le tir est en vol ; le contre ne peut venir que du trajet
    monkeypatch.setattr(match, "BLOCK_CHANCE", 1.0)
    shooter = _player("Buteur", "home", "BU", SHOOTER_AT)
    defender = _player("Defenseur", "away", "DC", SHOOTER_AT + Vec2(15.0, 0.0))
    monkeypatch.setattr(match, "should_attempt_tackle", lambda aggression, dt: False)
    monkeypatch.setattr(match, "choose_action", lambda *args: Action("shot", 1.0))
    monkeypatch.setattr(match, "draw_shot_error", lambda *args: (0.0, 0.0))
    ball = BallState(position=shooter.position, velocity=Vec2(0.0, 0.0), holder="Buteur")
    shots = []
    _step_ball(ball, 0.1, [shooter, defender], 0.0, shots=shots)
    assert shots[0].outcome == FLYING and not hasattr(match, "draw_blocker")


def _deflected_side(monkeypatch, seed: int) -> float:
    """Défenseur qui traverse l'axe du tir à 5 m/s vers les y croissants, à 8 m du tireur : au contact (troisième pas), il
    est encore sous l'axe (environ -0,2 m) ; en fin de pas, il est déjà au-dessus (+0,1 m). Retourne la vitesse en y du
    ballon contré."""
    monkeypatch.setattr(match, "BLOCK_CHANCE", 1.0)
    monkeypatch.setattr(match, "should_attempt_tackle", lambda aggression, dt: False)
    monkeypatch.setattr(match, "choose_action", lambda *args: Action("shot", 1.0))
    monkeypatch.setattr(match, "draw_shot_error", lambda *args: (0.0, 0.0))
    shooter = _player("Buteur", "home", "BU", SHOOTER_AT)
    defender = _player("Defenseur", "away", "DC", SHOOTER_AT + Vec2(8.0, -1.4))
    defender.velocity = Vec2(0.0, 5.0)
    ball = BallState(position=shooter.position, velocity=Vec2(0.0, 0.0), holder="Buteur")
    shots = []
    TIR.seed(seed)
    _step_ball(ball, 0.1, [shooter, defender], 0.0, shots=shots)  # la frappe
    for tick in range(1, 6):
        defender.position = defender.position + defender.velocity * 0.1  # il court pendant le vol
        _step_ball(ball, 0.1, [shooter, defender], tick * 0.1, shots=shots)
        if shots[0].outcome != FLYING:
            break
    assert shots[0].outcome == "contré"
    return ball.velocity.y


def test_the_deflection_side_is_that_of_the_defender_at_the_contact_not_at_the_end_of_the_step(monkeypatch) -> None:
    # réserve A1 de l'expert (ticket 05d), reprise au 05g : le ballon passe au-dessus du corps au moment du contact, il
    # est dévié vers les y croissants, quelle que soit la place du défenseur à la fin du pas
    sides = [_deflected_side(monkeypatch, seed) for seed in range(40)]
    assert sum(y > 0.0 for y in sides) >= 36

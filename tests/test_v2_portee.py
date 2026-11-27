"""Tranches de hauteur des joueurs de champ (ticket v2-hauteur-ballon/03a) : un joueur ne touche le ballon que s'il passe
sous le plafond de son corps (pied, corps, tête en saut), selon sa taille et sa détente (Jumping Reach)."""

from __future__ import annotations

import ast
import inspect
import math
from dataclasses import replace

import pytest

import v2engine.match as match
import v2engine.portee as portee
from v2engine.ball_state import BallState
from v2engine.geometry import PITCH_LENGTH_M, Vec2
from v2engine.hauteur import height_at, step_height
from v2engine.match import BALL_RADIUS_M, CONTROL_RADIUS_M, _exit_share, _step_ball
from v2engine.portee import (CORPS, PIED, TETE, field_band, field_ceiling_m, first_reachable_s, jump_m,
                             neutral_height_m, player_band, player_ceiling_m)
from tests.scenes import player
from tests.test_v2_hauteur_tirs import _player, _shoot
from v2engine.cerveau import GOAL_CENTER_Y

DT = 0.1
SPEED = 30.0
AT = Vec2(60.0, 34.0)


def _tall(name: str, height_m: float, jumping_reach: int, team: str = "away", poste: str = "DC", x: float = AT.x,
          y: float = AT.y):
    return replace(player(name, team=team, x=x, y=y, poste=poste, Jumping_Reach=jumping_reach), height_m=height_m)


def _pass_over(monkeypatch, z0: float, vz0: float, players, x0: float = AT.x - 1.5) -> BallState:
    """Un pas de ballon libre, en ligne droite à `SPEED` le long de y = `AT.y`, au-dessus des joueurs posés sur sa
    ligne ; contrôle toujours réussi (on ne juge que le contact)."""
    monkeypatch.setattr(match, "attempt_control", lambda *a, **k: True)
    ball = BallState(position=Vec2(x0, AT.y), velocity=Vec2(SPEED, 0.0), last_pass_team="home",
                     pass_from=Vec2(40.0, AT.y), z=z0, vz=vz0, landed=False)
    _step_ball(ball, DT, players, 0.0)
    return ball


# --- constantes et tranches ---

def test_constantes_validees() -> None:
    assert (portee.HIP_SHARE, portee.SHOULDER_SHARE) == (0.530, 0.818)
    assert (portee.JUMP_MIN_M, portee.JUMP_MAX_M) == (0.35, 0.75)
    assert portee.BALL_RADIUS_M == BALL_RADIUS_M


def test_detente_lineaire_et_bornee() -> None:
    assert jump_m(1) == pytest.approx(0.35) and jump_m(99) == pytest.approx(0.75)
    assert jump_m(50) == pytest.approx(0.35 + 0.40 * 49 / 98)
    assert jump_m(-5) == jump_m(1) and jump_m(150) == jump_m(99)


def test_tranches_d_un_joueur_de_1_83_m() -> None:
    h, j = 1.83, jump_m(60)
    assert field_band(h, j, 0.0) == PIED
    assert field_band(h, j, 0.530 * h) == PIED and field_band(h, j, 0.530 * h + 0.01) == CORPS
    assert field_band(h, j, 0.818 * h) == CORPS and field_band(h, j, 0.818 * h + 0.01) == TETE
    assert field_band(h, j, h + j - BALL_RADIUS_M) == TETE
    assert field_band(h, j, h + j - BALL_RADIUS_M + 0.01) is None


@pytest.mark.parametrize("height_m", [1.60, 1.70, 1.83, 2.00])
@pytest.mark.parametrize("jumping_reach", [1, 99])
def test_ballon_a_0_5_m_jouable_du_pied_par_tous(height_m: float, jumping_reach: int) -> None:
    assert field_band(height_m, jump_m(jumping_reach), 0.5) == PIED


def test_taille_de_repli_mediane_du_poste() -> None:
    assert neutral_height_m("GK") == 1.90 and neutral_height_m("AD") == 1.78
    assert neutral_height_m("inconnu") == portee.BASE_MEDIAN_HEIGHT_M
    unknown = player("X", poste="DC")
    assert unknown.height_m is None
    assert player_ceiling_m(unknown) == pytest.approx(field_ceiling_m(1.88, jump_m(60)))


def test_tranches_de_champ_ne_lisent_pas_le_poste() -> None:
    """Isolation (le gardien et ses mains : ticket 03b) : `field_band` ne connaît pas le poste ; à taille et détente
    égales, un gardien et un joueur de champ ont les mêmes tranches."""
    source = inspect.getsource(field_band) + inspect.getsource(field_ceiling_m)
    names = {node.attr for node in ast.walk(ast.parse(source)) if isinstance(node, ast.Attribute)}
    assert "poste" not in names and "poste" not in source
    keeper, field = _tall("G", 1.88, 70, poste="GK"), _tall("D", 1.88, 70, poste="DC")
    for z in (0.0, 0.5, 1.2, 1.9, 2.3, 2.5):
        assert player_band(keeper, z) == player_band(field, z)


# --- scènes fixes (critères d'acceptation) ---

def test_ballon_a_2_5_m_passe_au_dessus_d_un_defenseur_de_1_70_m(monkeypatch) -> None:
    short = _tall("Petit", 1.70, 60)
    assert field_ceiling_m(1.70, jump_m(60)) < 2.5 - 0.1
    ball = _pass_over(monkeypatch, 2.5, 0.0, [short])
    assert ball.holder is None and ball.last_toucher != "Petit"


def test_ballon_a_2_5_m_repris_par_un_joueur_de_1_90_m_a_detente_elevee(monkeypatch) -> None:
    tall = _tall("Grand", 1.90, 99)
    ball = _pass_over(monkeypatch, 2.5, 0.0, [tall])
    assert ball.holder == "Grand"


def test_ballon_a_0_5_m_touche_par_un_joueur_de_1_60_m(monkeypatch) -> None:
    small = _tall("Petit", 1.60, 1)
    ball = _pass_over(monkeypatch, 0.5, 0.0, [small])
    assert ball.holder == "Petit"


# --- instant du contact ---

def test_ballon_qui_redescend_sous_le_plafond_pendant_son_passage_est_touche_en_centre(monkeypatch) -> None:
    """Il entre à portée au-dessus du plafond, passe dessous avant d'en sortir : touché, à l'instant où il passe sous
    le plafond (pas seulement l'instant d'entrée, ponytail du 02a1) ; ballon cueilli à sa première retombée : « centre »
    (règle du 02c inchangée)."""
    mate = player("R", team="home", x=AT.x, y=AT.y)
    ceiling = player_ceiling_m(mate)
    entry_s = 0.02
    x0 = AT.x - CONTROL_RADIUS_M - SPEED * entry_s
    z_entry, vz0 = ceiling + 0.08, -12.0
    z0 = z_entry - vz0 * entry_s + 0.5 * 9.81 * entry_s ** 2
    assert height_at(z0, vz0, entry_s)[0] > ceiling  # au-dessus à son entrée
    ball = _pass_over(monkeypatch, z0, vz0, [mate], x0=x0)
    assert ball.holder == "R"
    assert ball.came_from[1] == "centre"


def test_premier_qui_atteint_le_ballon_sous_son_plafond_tente_le_premier(monkeypatch) -> None:
    """A entre à portée le premier mais le ballon est au-dessus de sa tête jusqu'à plus tard ; B, plus grand, entre un
    peu après et l'atteint tout de suite : B le touche."""
    entry_a = 0.01
    a = _tall("A", 1.65, 1, x=AT.x)
    b = _tall("B", 1.95, 99, x=AT.x + 0.15)
    ceil_a, ceil_b = player_ceiling_m(a), player_ceiling_m(b)
    x0 = AT.x - CONTROL_RADIUS_M - SPEED * entry_a
    vz0 = -3.0
    z0 = (ceil_a + ceil_b) / 2.0 - vz0 * entry_a + 0.5 * 9.81 * entry_a ** 2  # entre les deux plafonds à l'entrée de A
    t_a = first_reachable_s(z0, vz0, ceil_a, entry_a, 1.0)
    entry_b = entry_a + 0.15 / SPEED
    assert t_a is not None and t_a > entry_b
    ball = _pass_over(monkeypatch, z0, vz0, [a, b], x0=x0)
    assert ball.holder == "B"


def test_first_reachable_s() -> None:
    assert first_reachable_s(1.0, 0.0, 2.0, 0.0, 0.1) == 0.0  # déjà dessous
    assert first_reachable_s(3.0, 0.0, 2.0, 0.0, 0.1) is None  # trop haut tout le pas
    t = first_reachable_s(2.1, -5.0, 2.0, 0.0, 0.1)
    assert t is not None and height_at(2.1, -5.0, t)[0] == pytest.approx(2.0)
    assert first_reachable_s(5.0, 10.0, 2.0, 0.0, 0.1) is None  # il monte : jamais dessous dans le pas


def test_exit_share_sur_une_ligne_droite() -> None:
    p = player("P", x=AT.x, y=AT.y)
    start, end = Vec2(AT.x - 1.5, AT.y), Vec2(AT.x + 1.5, AT.y)
    assert _exit_share(start, end, DT, p, CONTROL_RADIUS_M) == pytest.approx((1.5 + CONTROL_RADIUS_M) / 3.0)
    assert _exit_share(start, Vec2(AT.x + 0.1, AT.y), DT, p, CONTROL_RADIUS_M) == 1.0  # encore à portée en fin de pas


def test_tranche_tracee_a_la_reception(monkeypatch) -> None:
    monkeypatch.setattr(match, "attempt_control", lambda *a, **k: True)
    receptions = []
    for z, band in ((0.0, PIED), (1.3, CORPS), (1.9, TETE)):
        mate = _tall("R", 1.83, 60, team="home")
        ball = BallState(position=Vec2(AT.x - 1.5, AT.y), velocity=Vec2(SPEED, 0.0), last_pass_team="home",
                         pass_from=Vec2(40.0, AT.y), z=z, vz=0.0, landed=True)
        match._step_loose_ball(ball, DT, [mate], 0.0, None, None, None, None, None, None, receptions)
        assert receptions[-1].band == band


# --- contres ---

@pytest.mark.parametrize("aim_m, blocked", [(1.0, True), (8.0, False)])
def test_tir_au_dessus_de_la_tete_du_defenseur_n_est_pas_contre(monkeypatch, aim_m: float, blocked: bool) -> None:
    monkeypatch.setattr(match, "BLOCK_CHANCE", 1.0)
    defender = replace(_player("Defenseur", "away", "DC", Vec2(PITCH_LENGTH_M - 12.0, GOAL_CENTER_Y + 0.6)),
                       height_m=1.70)
    shots, _, heights, _ = _shoot(monkeypatch, aim_m, defender=defender, until_touched=True)
    assert (shots[0].outcome == "contré") is blocked
    if not blocked:
        assert max(z for z, _, _ in heights[:3]) > player_ceiling_m(defender)  # passé au-dessus de lui


def test_tranche_au_plafond_exact_est_la_tete(monkeypatch) -> None:
    """Ballon qui passe sous le plafond pendant le passage : l'instant calculé tombe sur le plafond, la tranche est la
    tête même si l'arrondi le laisse un rien au-dessus."""
    receptions = []
    monkeypatch.setattr(match, "attempt_control", lambda *a, **k: True)
    mate = player("R", team="home", x=AT.x, y=AT.y)
    ceiling, entry_s, vz0 = player_ceiling_m(mate), 0.02, -12.0
    z0 = ceiling + 0.08 - vz0 * entry_s + 0.5 * 9.81 * entry_s ** 2
    ball = BallState(position=Vec2(AT.x - CONTROL_RADIUS_M - SPEED * entry_s, AT.y), velocity=Vec2(SPEED, 0.0),
                     last_pass_team="home", pass_from=Vec2(40.0, AT.y), z=z0, vz=vz0)
    match._step_loose_ball(ball, DT, [mate], 0.0, None, None, None, None, None, None, receptions)
    assert receptions[-1].band == TETE


def test_la_taille_survit_au_pas_de_deplacement() -> None:
    """`movement.step` reconstruit le joueur champ par champ : la taille de la fiche doit suivre (bug trouvé par la garde
    des attributs au 03a : tout le monde retombait sur la médiane du poste dès le premier pas)."""
    from v2engine.movement import step
    moved = step(_tall("G", 2.01, 60), 0.1, Vec2(AT.x + 5.0, AT.y), 10.0)
    assert moved.height_m == 2.01

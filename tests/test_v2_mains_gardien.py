"""Mains du gardien (ticket v2-hauteur-ballon/03b) : dans sa surface, le gardien joue le ballon bras levés jusqu'à
`z + r ≤ 1,258 H + détente` ; hors de sa surface, il suit les tranches de champ (03a). Un seul modèle de portée pour le
tir en vol (`match._keeper_reaches`) et le ballon libre (`match._step_loose_ball`), un seul aiguillage
(`portee.player_ceiling_m` / `portee.player_band`) ; l'estimateur de tir (`shooting._goal_angles`) suit la résolution."""

from __future__ import annotations

import ast
import inspect
import math
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

import v2engine.match as match
import v2engine.portee as portee
from v2engine import shooting
from v2engine.attributes import player_attribute
from v2engine.ball_state import BallState, ShotFlight
from v2engine.decision import Action
from v2engine.geometry import PITCH_LENGTH_M, Vec2, in_penalty_area
from v2engine.hauteur import step_height
from v2engine.match import BALL_RADIUS_M, GOAL_CENTER_Y, _keeper_reaches, _step_ball
from v2engine.portee import (MAINS, PIED, TETE, field_ceiling_m, jump_m, keeper_band, keeper_hands_ceiling,
                             player_band, player_ceiling_m, uses_hands)
from v2engine.trace import ShotEvent
from tests.scenes import player
from tests.test_v2engine_arret_portee import _player

DT = 0.1
SPEED = 30.0
IN_BOX = Vec2(PITCH_LENGTH_M - 5.0, GOAL_CENTER_Y)  # surface du gardien « away » (attaquée par « home »)
OUT_OF_BOX = Vec2(PITCH_LENGTH_M - 25.0, GOAL_CENTER_Y)


def _man(name: str, poste: str, at: Vec2, height_m: float = 1.90, jumping_reach: int = 60, team: str = "away"):
    return replace(player(name, team=team, x=at.x, y=at.y, poste=poste, Jumping_Reach=jumping_reach), height_m=height_m)


def _loose_over(monkeypatch, z0: float, players, at: Vec2) -> BallState:
    """Un pas de ballon libre (passe adverse), en ligne droite à `SPEED` vers le but, au-dessus de `at` ; contrôle
    toujours réussi (on ne juge que le contact)."""
    monkeypatch.setattr(match, "attempt_control", lambda *a, **k: True)
    ball = BallState(position=Vec2(at.x - 1.5, at.y), velocity=Vec2(SPEED, 0.0), last_pass_team="home",
                     pass_from=Vec2(at.x - 30.0, at.y), z=z0, vz=0.0, landed=False)
    _step_ball(ball, DT, players, 0.0)
    return ball


# --- constantes, tranches, aiguillage ---

def test_plafond_des_mains_bras_leves() -> None:
    assert portee.HANDS_SHARE == pytest.approx(0.818 + 0.186 + 0.146 + 0.108) == pytest.approx(1.258)
    assert keeper_hands_ceiling(1.90, jump_m(60)) == pytest.approx(1.258 * 1.90 + jump_m(60) - BALL_RADIUS_M)
    assert keeper_hands_ceiling(1.90, jump_m(60)) > field_ceiling_m(1.90, jump_m(60)) + 0.4


def test_tranches_du_gardien_dans_sa_surface() -> None:
    h, j = 1.90, jump_m(60)
    assert keeper_band(h, j, 0.3) == PIED
    assert keeper_band(h, j, 0.530 * h + 0.01) == MAINS
    assert keeper_band(h, j, keeper_hands_ceiling(h, j)) == MAINS
    assert keeper_band(h, j, keeper_hands_ceiling(h, j) + 0.01) is None


def test_aiguillage_gardien_dans_sa_surface_seulement() -> None:
    keeper_in, keeper_out = _man("G", "GK", IN_BOX), _man("G", "GK", OUT_OF_BOX)
    field_in = _man("D", "DC", IN_BOX)
    assert in_penalty_area("home", IN_BOX) and not in_penalty_area("home", OUT_OF_BOX)
    assert uses_hands(keeper_in) and not uses_hands(keeper_out) and not uses_hands(field_in)
    assert not uses_hands(_man("G", "GK", IN_BOX, team="home"))  # surface adverse : pas ses mains
    hands, head = keeper_hands_ceiling(1.90, jump_m(60)), field_ceiling_m(1.90, jump_m(60))
    assert player_ceiling_m(keeper_in) == pytest.approx(hands)
    assert player_ceiling_m(keeper_out) == pytest.approx(head) == pytest.approx(player_ceiling_m(field_in))
    assert player_band(keeper_in, 2.5) == MAINS and player_band(keeper_out, 2.2) == TETE
    assert player_band(keeper_out, 2.5) is None


def test_la_tranche_mains_n_est_lue_que_par_l_aiguillage() -> None:
    """Isolation : `keeper_hands_ceiling` et `keeper_band` ne sont appelés que dans `portee`, par l'aiguillage
    (`player_ceiling_m`, `player_band`) et le repli neutre de l'estimateur ; aucun autre module ne les lit."""
    hands = {"keeper_hands_ceiling", "keeper_band"}
    engine = Path(portee.__file__).parent
    for path in sorted(engine.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for func in (n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)):
            called = {c.func.id if isinstance(c.func, ast.Name) else getattr(c.func, "attr", None)
                      for c in ast.walk(func) if isinstance(c, ast.Call)}
            if called & hands:
                assert path.name == "portee.py", (path.name, func.name)
                assert func.name in {"player_ceiling_m", "player_band", "neutral_keeper_ceiling_m",
                                     "keeper_band"}, func.name
    for name in ("field_band", "field_ceiling_m", "keeper_hands_ceiling", "keeper_band"):
        assert "poste" not in inspect.getsource(getattr(portee, name))  # le poste n'est lu que par `uses_hands`


def test_note_neutre_de_jumping_reach() -> None:
    assert portee.NEUTRAL_JUMPING_REACH == player_attribute(SimpleNamespace(attributes=None), "Jumping Reach")
    assert portee.neutral_keeper_ceiling_m() == pytest.approx(keeper_hands_ceiling(1.90, jump_m(60)))


# --- ballon libre (critère d'acceptation) ---

def test_le_gardien_capte_dans_sa_surface_un_ballon_hors_de_portee_d_un_joueur_de_champ(monkeypatch) -> None:
    z0 = 2.6  # passe à 2,55 m en fin de pas : au-dessus de la tête d'un 1,83 m (2,31 m), sous les mains (2,87 m)
    assert field_ceiling_m(1.83, jump_m(60)) < step_height(z0, 0.0, DT).z
    assert keeper_hands_ceiling(1.90, jump_m(60)) > z0
    field = _man("Défenseur", "DC", IN_BOX, height_m=1.83)
    assert _loose_over(monkeypatch, z0, [field], IN_BOX).last_toucher != "Défenseur"
    keeper = _man("Gardien", "GK", IN_BOX)
    receptions = []
    monkeypatch.setattr(match, "attempt_control", lambda *a, **k: True)
    ball = BallState(position=Vec2(IN_BOX.x - 1.5, IN_BOX.y), velocity=Vec2(SPEED, 0.0), last_pass_team="home",
                     pass_from=Vec2(IN_BOX.x - 30.0, IN_BOX.y), z=z0, vz=0.0, landed=False)
    _step_ball(ball, DT, [keeper], 0.0, receptions=receptions)
    assert ball.holder == "Gardien" and receptions[-1].band == MAINS


def test_hors_de_sa_surface_le_gardien_suit_les_tranches_de_champ(monkeypatch) -> None:
    keeper = _man("Gardien", "GK", OUT_OF_BOX)
    assert _loose_over(monkeypatch, 2.6, [keeper], OUT_OF_BOX).last_toucher != "Gardien"
    keeper_in = _man("Gardien", "GK", IN_BOX)
    assert _loose_over(monkeypatch, 2.6, [keeper_in], IN_BOX).holder == "Gardien"


# --- tir en vol (critère d'acceptation) ---

def _judge(keeper_at: Vec2, z0: float) -> tuple[bool, list]:
    """`_keeper_reaches` sur un pas qui passe sur le gardien (écart nul), bas du ballon à `z0` au début du pas."""
    keeper = _player("Gardien", "away", "GK", keeper_at)
    origin = Vec2(keeper_at.x - 14.0, keeper_at.y)
    start, end = Vec2(keeper_at.x - 3.0, keeper_at.y), keeper_at
    ball = BallState(position=start, velocity=Vec2(SPEED, 0.0), z=z0, vz=0.0)
    flight = ShotFlight("home", origin, 0.0, 0, on_target=True, keeper_at_m=14.0, elapsed_s=0.4)
    flight.keeper_from = keeper_at
    shots = [ShotEvent(0.0, "home", "Buteur", origin.x, origin.y, 0.3, shooting.FLYING, "passe au sol")]
    return _keeper_reaches(ball, flight, start, end, DT, [keeper], 0.0, shots), shots


def test_tir_a_1_01_m_capte_par_keeper_reaches() -> None:
    reached, shots = _judge(IN_BOX, 1.01 + 0.049)  # 1,01 m au passage (chute de 4,9 cm sur le pas)
    assert reached and shots[0].outcome in (shooting.HELD, shooting.PARRIED, shooting.TIPPED)


def test_tir_au_dessus_du_plafond_des_mains_non_atteint() -> None:
    hands = keeper_hands_ceiling(1.90, jump_m(60))
    reached, shots = _judge(IN_BOX, hands + 0.1 + 0.049)
    assert not reached and shots[0].keeper_gap_m == pytest.approx(0.0) and shots[0].post_shot_xg == 1.0
    assert _judge(IN_BOX, hands - 0.1 + 0.049)[0]  # juste sous ses mains : atteint


def test_tir_hors_de_sa_surface_juge_aux_tranches_de_champ() -> None:
    z = field_ceiling_m(1.90, jump_m(60)) + 0.2  # au-dessus de sa tête, sous ses mains
    assert not _judge(OUT_OF_BOX, z + 0.049)[0]
    assert _judge(IN_BOX, z + 0.049)[0]


def _shoot(monkeypatch, distance_m: float, keeper_depth_m: float, vertical_deg: float):
    """Tir face au but, dans l'axe, écart en hauteur `vertical_deg` (scène de `test_v2engine_arret_portee._shoot`)."""
    shooter = _player("Buteur", "home", "BU", Vec2(PITCH_LENGTH_M - distance_m, GOAL_CENTER_Y))
    keeper = _player("Gardien", "away", "GK", Vec2(PITCH_LENGTH_M - keeper_depth_m, GOAL_CENTER_Y))
    ball = BallState(position=shooter.position, velocity=Vec2(0.0, 0.0), holder="Buteur")
    monkeypatch.setattr(match, "should_attempt_tackle", lambda aggression, dt: False)
    monkeypatch.setattr(match, "choose_action", lambda *args: Action("shot", 1.0))
    monkeypatch.setattr(match, "BLOCK_CHANCE", 0.0)
    monkeypatch.setattr(match, "draw_shot_error", lambda *args: (0.0, math.radians(vertical_deg)))
    shots, scored = [], None
    for tick in range(60):
        scored = _step_ball(ball, DT, [shooter, keeper], tick * DT, shots=shots)
        if scored is not None or not ball.shot_in_flight:
            break
    return shots[0], scored


def test_en_match_le_tir_ras_de_20_m_reste_arrete(monkeypatch) -> None:
    shot, scored = _shoot(monkeypatch, 20.0, 1.0, 0.0)
    assert scored is None and shot.outcome in (shooting.HELD, shooting.PARRIED, shooting.TIPPED)


def test_en_match_un_lob_passe_au_dessus_du_gardien_sorti(monkeypatch) -> None:
    """Tir de 35 m dans l'axe, gardien à 10 m de sa ligne : le ballon (frappé du sol, il redescend vers la ligne) passe
    au-dessus de ses mains, à écart nul ; but. Avant le 03b, arrêté (seul l'écart comptait)."""
    shot, scored = _shoot(monkeypatch, 35.0, 10.0, 0.0)
    assert scored == "home" and shot.outcome == "but"
    assert shot.keeper_gap_m == pytest.approx(0.0, abs=0.05) and shot.post_shot_xg == 1.0


# --- estimateur de tir (suit la résolution) ---

def test_l_estimateur_compte_les_tirs_au_dessus_des_mains() -> None:
    shooter = _player("Buteur", "home", "BU", Vec2(PITCH_LENGTH_M - 35.0, GOAL_CENTER_Y))
    goal = Vec2(PITCH_LENGTH_M, GOAL_CENTER_Y)
    sigma = shooting.shot_error_sigma(shooter, goal, [])
    out = _player("Gardien", "away", "GK", Vec2(PITCH_LENGTH_M - 10.0, GOAL_CENTER_Y))
    home = _player("Gardien", "away", "GK", Vec2(PITCH_LENGTH_M - 1.0, GOAL_CENTER_Y))
    _, kept_out, over_out = shooting._goal_angles(shooter, goal, out, sigma)
    _, _, over_home = shooting._goal_angles(shooter, goal, home, sigma)
    assert kept_out and 0.0 < over_out <= 1.0
    assert over_home == 0.0  # sur sa ligne, tout tir sous la barre passe sous ses mains
    # cohérence : la chance de but estimée augmente quand le plafond baisse
    low = replace(out, height_m=1.60)
    assert shooting.physical_shot_chance(shooter, goal, low, [low]) > shooting.physical_shot_chance(shooter, goal, out, [out])


def test_l_estimateur_suit_l_aiguillage_hors_de_la_surface(monkeypatch) -> None:
    shooter = _player("Buteur", "home", "BU", Vec2(PITCH_LENGTH_M - 40.0, GOAL_CENTER_Y))
    goal = Vec2(PITCH_LENGTH_M, GOAL_CENTER_Y)
    sigma = shooting.shot_error_sigma(shooter, goal, [])
    keeper = _player("Gardien", "away", "GK", Vec2(PITCH_LENGTH_M - 20.0, GOAL_CENTER_Y))
    assert not uses_hands(keeper)
    seen = []
    monkeypatch.setattr(shooting, "_under_error", lambda s, d, t, ceiling: seen.append(ceiling) or math.inf)
    shooting._goal_angles(shooter, goal, keeper, sigma)
    assert seen == [pytest.approx(field_ceiling_m(1.90, jump_m(60)))]

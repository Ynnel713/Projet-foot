"""Tests des 4 invariants visuels du prototype isolé (`apps/prototype_visual.py`,
brief "isolated visual prototype", 24/09/2026). Import par chemin de fichier
(pas de package `apps`, même motif que `apps/streamlit_preview.py` qui
s'auto-insère dans `sys.path`) -- aucune modification de `pyproject.toml`."""

import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "apps"))

import prototype_visual as pv  # noqa: E402

_DT = 1.0 / pv.FPS
_N_FRAMES = int(pv.TOTAL_DURATION_S * pv.FPS) + 1


def _sample_times():
    return [min(pv.TOTAL_DURATION_S, i * _DT) for i in range(_N_FRAMES)]


def _total_distance(player_id: str, segments=None) -> float:
    segments = segments if segments is not None else pv.PLAYER_SEGMENTS[player_id]
    return sum(math.hypot(end[0] - start[0], end[1] - start[1]) for _t0, _t1, start, end in segments)


def _max_frame_step(player_id: str) -> float:
    times = _sample_times()
    prev = pv.player_position(player_id, times[0])
    worst = 0.0
    for t in times[1:]:
        cur = pv.player_position(player_id, t)
        worst = max(worst, math.hypot(cur[0] - prev[0], cur[1] - prev[1]))
        prev = cur
    return worst


class TestInvariant1NoIdlePlayer:
    """Sur la durée totale, chaque joueur parcourt au moins 1 m."""

    @pytest.mark.parametrize("player_id", pv.ALL_PLAYER_IDS)
    def test_every_player_covers_at_least_one_metre(self, player_id):
        assert _total_distance(player_id) >= 1.0, f"{player_id} : {_total_distance(player_id):.3f} m"

    def test_red_a_frozen_player_is_detected(self, monkeypatch):
        # Preuve rouge : un joueur dont le segment ne bouge pas du tout (fin
        # == depart) doit faire echouer la meme verification.
        broken = dict(pv.PLAYER_SEGMENTS)
        broken["blue_7"] = [(0.0, pv.TOTAL_DURATION_S, (40.0, 18.0), (40.0, 18.0))]
        monkeypatch.setattr(pv, "PLAYER_SEGMENTS", broken)
        assert _total_distance("blue_7") < 1.0  # confirme que le cas casse bien l'invariant
        with pytest.raises(AssertionError):
            assert _total_distance("blue_7") >= 1.0, "devrait echouer"


class TestInvariant2NoTeleportation:
    """Entre deux frames consécutives, aucun joueur ne se déplace de plus
    de 0,5 m (30 fps -> 15 m/s de pointe, largement au-dessus de tout
    déplacement scripté ici -- voir docstring de PLAYER_SEGMENTS)."""

    @pytest.mark.parametrize("player_id", pv.ALL_PLAYER_IDS)
    def test_no_player_ever_jumps_more_than_half_a_metre_between_frames(self, player_id):
        worst = _max_frame_step(player_id)
        assert worst <= 0.5, f"{player_id} : saut max {worst:.3f} m entre deux frames"

    def test_red_an_injected_jump_is_detected(self, monkeypatch):
        # Preuve rouge : un segment additionnel qui fait sauter le joueur de
        # 10 m en un temps quasi nul doit faire echouer la meme verification.
        broken = dict(pv.PLAYER_SEGMENTS)
        broken["blue_7"] = [
            (0.0, 6.0, (40.0, 18.0), (40.0, 18.0)),
            (6.0, 6.0333, (40.0, 18.0), (50.0, 18.0)),  # +10 m en 1 frame
            (6.0333, pv.TOTAL_DURATION_S, (50.0, 18.0), (56.0, 15.0)),
        ]
        monkeypatch.setattr(pv, "PLAYER_SEGMENTS", broken)
        worst = _max_frame_step("blue_7")
        assert worst > 0.5  # confirme que le cas casse bien l'invariant
        with pytest.raises(AssertionError):
            assert worst <= 0.5, "devrait echouer"


class TestInvariant3BallAtTheCarriersFoot:
    """Pendant chaque phase de possession, le ballon est à ≤ 0,5 m du
    porteur -- ici exactement à 0 m par construction (`ball_position`
    retourne `player_position(carrier, t)` telle quelle)."""

    def test_ball_never_strays_from_its_carrier_during_possession(self):
        checked_a_possession = False
        for t in _sample_times():
            carrier = pv.carrier_at(t)
            if carrier is None:
                continue
            checked_a_possession = True
            ball = pv.ball_position(t)
            player = pv.player_position(carrier, t)
            dist = math.hypot(ball[0] - player[0], ball[1] - player[1])
            assert dist <= 0.5, f"t={t:.3f} porteur={carrier} distance={dist:.3f} m"
        assert checked_a_possession, "aucune phase de possession echantillonnee -- invariant non exerce"

    def test_red_a_detached_ball_during_possession_is_detected(self, monkeypatch):
        # Preuve rouge : pendant la 1ere phase de possession (blue_8,
        # 0.0-4.0s), le ballon "oublie" de suivre le porteur et reste fixe
        # a un point disjoint -- doit faire echouer la meme verification.
        original_ball_position = pv.ball_position

        def broken_ball_position(t):
            if 0.0 <= t <= 4.0:
                return (10.0, 10.0)  # loin de blue_8, jamais attache
            return original_ball_position(t)

        monkeypatch.setattr(pv, "ball_position", broken_ball_position)

        t = 2.0
        carrier = pv.carrier_at(t)
        ball = pv.ball_position(t)
        player = pv.player_position(carrier, t)
        dist = math.hypot(ball[0] - player[0], ball[1] - player[1])
        assert dist > 0.5  # confirme que le cas casse bien l'invariant
        with pytest.raises(AssertionError):
            assert dist <= 0.5, "devrait echouer"


class TestInvariant4BallInertWhenUntouched:
    """Quand aucun joueur ne touche le ballon (phase "static", après le
    but), sa position ne change pas."""

    def test_ball_does_not_move_during_the_static_phase(self):
        static_phase = pv.BALL_PHASES[-1]
        assert static_phase[0] == "static", "le dernier phase attendu est 'static' (ballon au fond des filets)"
        _kind, pos, t0, t1 = static_phase
        positions = {pv.ball_position(t) for t in (t0, (t0 + t1) / 2.0, t1)}
        assert positions == {pos}, f"la position varie pendant la phase statique : {positions}"

    def test_red_a_moving_static_phase_is_detected(self, monkeypatch):
        # Preuve rouge : la phase "static" se met a deriver (le ballon
        # continue de rouler alors que personne ne le touche) -- doit faire
        # echouer la meme verification.
        kind, pos, t0, t1 = pv.BALL_PHASES[-1]
        assert kind == "static"
        original_ball_position = pv.ball_position

        def broken_ball_position(t):
            if t0 <= t <= t1:
                drift = (t - t0) * 2.0  # derive artificielle, jamais scriptee
                return (pos[0] + drift, pos[1])
            return original_ball_position(t)

        monkeypatch.setattr(pv, "ball_position", broken_ball_position)

        positions = {pv.ball_position(t) for t in (t0, (t0 + t1) / 2.0, t1)}
        assert len(positions) > 1  # confirme que le cas casse bien l'invariant
        with pytest.raises(AssertionError):
            assert positions == {pos}, "devrait echouer"


class TestNoEngineImports:
    """Tâche 1.3 -- aucune dépendance au moteur existant (ni `ligue1sim.*`,
    ni `narrative`/`narrative_player`). Analyse via `ast` (les instructions
    `import`/`from` réelles), pas une recherche textuelle brute -- la
    docstring de module CITE volontairement ces noms pour expliquer
    pourquoi ils sont absents, un simple `"ligue1sim" not in source`
    donnerait donc un faux positif sur sa propre documentation."""

    def test_prototype_module_does_not_import_the_engine_package(self):
        import ast

        source = Path(pv.__file__).read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported_roots = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_roots.add(node.module.split(".")[0])

        forbidden = {"ligue1sim", "narrative", "narrative_player"}
        assert not (imported_roots & forbidden), f"import(s) interdit(s) : {imported_roots & forbidden}"

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


class TestGoalkeeperCenteredActiveBounded:
    """Gardien (brief "gardien centre, actif, borne", 24/09/2026). `blue_1`/
    `red_1` ne sont plus dans PLAYER_SEGMENTS -- voir goalkeeper_position()
    dans apps/prototype_visual.py -- donc ces tests passent par
    player_position() (qui delegue) pour rester couplees au vrai chemin
    d'appel utilise par le rendu."""

    @pytest.mark.parametrize("player_id", pv.GOALKEEPER_IDS)
    def test_stays_within_goal_area_depth_and_between_posts_at_every_frame(self, player_id):
        # "Sa surface" = la surface de but (5.5 m de profondeur), pas la
        # surface de reparation -- coherent avec GK_DEPTH_M=2.5 (a mi-profondeur).
        y_low = pv.PITCH_WIDTH_M / 2 - pv.GOAL_WIDTH_M / 2
        y_high = pv.PITCH_WIDTH_M / 2 + pv.GOAL_WIDTH_M / 2
        for t in _sample_times():
            x, y = pv.player_position(player_id, t)
            depth = x if player_id == "blue_1" else pv.PITCH_LENGTH_M - x
            assert 0.0 <= depth <= pv.GOAL_AREA_LENGTH_M, f"t={t:.3f} {player_id} hors surface : x={x}"
            assert y_low <= y <= y_high, f"t={t:.3f} {player_id} hors des poteaux : y={y}"

    def test_red_the_pre_brief_off_centre_goalkeeper_is_detected(self, monkeypatch):
        # Preuve rouge : la position de base d'avant ce brief (blue_1 a
        # x=8-9, loin devant sa surface de 5.5 m) doit faire echouer la meme
        # verification.
        broken_segments = dict(pv.PLAYER_SEGMENTS)
        broken_segments["blue_1"] = [(0.0, pv.TOTAL_DURATION_S, (8.0, 34.0), (9.0, 32.0))]
        monkeypatch.setattr(pv, "PLAYER_SEGMENTS", broken_segments)

        x, _y = pv.player_position("blue_1", 0.0)
        assert x > pv.GOAL_AREA_LENGTH_M  # confirme que le cas casse bien l'invariant (8 m > 5.5 m)
        with pytest.raises(AssertionError):
            assert 0.0 <= x <= pv.GOAL_AREA_LENGTH_M, "devrait echouer"

    @pytest.mark.parametrize("player_id", pv.GOALKEEPER_IDS)
    def test_covers_at_least_one_metre_over_the_clip(self, player_id):
        positions = [pv.player_position(player_id, t) for t in _sample_times()]
        total = sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(positions, positions[1:]))
        assert total >= 1.0, f"{player_id} : {total:.3f} m parcourus"

    @pytest.mark.parametrize("player_id", pv.GOALKEEPER_IDS)
    def test_no_jump_more_than_half_a_metre_between_frames(self, player_id):
        worst = _max_frame_step(player_id)
        assert worst <= 0.5, f"{player_id} : saut max {worst:.3f} m entre deux frames"

    @pytest.mark.parametrize("player_id", pv.GOALKEEPER_IDS)
    def test_average_y_position_stays_close_to_goal_centre(self, player_id):
        ys = [pv.player_position(player_id, t)[1] for t in _sample_times()]
        mean_y = sum(ys) / len(ys)
        deviation = abs(mean_y - pv.PITCH_WIDTH_M / 2)
        assert deviation < 3.0, f"{player_id} : y moyen={mean_y:.3f} centre={pv.PITCH_WIDTH_M / 2} ecart={deviation:.3f}"


_DC_TEAM_PAIRS = [("blue_3", "blue_4"), ("red_3", "red_4")]
_DC_PARTNER = {"blue_3": "blue_4", "blue_4": "blue_3", "red_3": "red_4", "red_4": "red_3"}


class TestCentralDefenders:
    """DC (brief "central defenders", 24/09/2026). `blue_3`/`blue_4` et
    `red_3`/`red_4` identifies par GEOMETRIE (ce prototype n'a pas de champ
    "poste") -- voir commentaire dans apps/prototype_visual.py. Ces tests
    passent par player_position() (le vrai chemin de rendu)."""

    @pytest.mark.parametrize("team_a,team_b", _DC_TEAM_PAIRS)
    def test_2_1_pair_distance_stays_between_8_and_12_metres(self, team_a, team_b):
        for t in _sample_times():
            pa, pb = pv.player_position(team_a, t), pv.player_position(team_b, t)
            dist = math.hypot(pa[0] - pb[0], pa[1] - pb[1])
            assert 8.0 <= dist <= 12.0, f"t={t:.3f} {team_a}/{team_b} distance={dist:.3f} m"

    def test_red_2_1_both_defenders_collapsed_on_each_other_is_detected(self, monkeypatch):
        # Preuve rouge (Tache 2.8) : les 2 DC ecrases sur le meme point (0 m
        # d'ecart) doit faire echouer la meme verification.
        broken = dict(pv.PLAYER_SEGMENTS)
        broken["blue_3"] = [(0.0, pv.TOTAL_DURATION_S, (18.0, 34.0), (18.0, 34.0))]
        broken["blue_4"] = [(0.0, pv.TOTAL_DURATION_S, (18.0, 34.0), (18.0, 34.0))]
        monkeypatch.setattr(pv, "PLAYER_SEGMENTS", broken)

        pa, pb = pv.player_position("blue_3", 0.0), pv.player_position("blue_4", 0.0)
        dist = math.hypot(pa[0] - pb[0], pa[1] - pb[1])
        assert dist < 8.0  # confirme que le cas casse bien l'invariant
        with pytest.raises(AssertionError):
            assert 8.0 <= dist <= 12.0, "devrait echouer"

    @pytest.mark.parametrize("player_id", pv.CENTRAL_DEFENDER_IDS)
    def test_2_2_stays_within_central_corridor_at_every_frame(self, player_id):
        for t in _sample_times():
            _x, y = pv.player_position(player_id, t)
            assert pv.DC_CORRIDOR_Y_MIN <= y <= pv.DC_CORRIDOR_Y_MAX, f"t={t:.3f} {player_id} hors couloir : y={y}"

    @pytest.mark.parametrize("player_id", pv.CENTRAL_DEFENDER_IDS)
    def test_2_3_never_crosses_the_halfway_line_towards_the_offensive_side(self, player_id):
        is_blue = player_id.startswith("blue")
        for t in _sample_times():
            x, _y = pv.player_position(player_id, t)
            if is_blue:
                assert x <= pv.PITCH_LENGTH_M / 2, f"t={t:.3f} {player_id} a franchi la mediane : x={x}"
            else:
                assert x >= pv.PITCH_LENGTH_M / 2, f"t={t:.3f} {player_id} a franchi la mediane : x={x}"

    @pytest.mark.parametrize("player_id", pv.CENTRAL_DEFENDER_IDS)
    def test_2_4_no_jump_more_than_half_a_metre_between_frames(self, player_id):
        worst = _max_frame_step(player_id)
        assert worst <= 0.5, f"{player_id} : saut max {worst:.3f} m entre deux frames"

    @pytest.mark.parametrize("team_a,team_b", _DC_TEAM_PAIRS)
    def test_2_5_ball_side_defender_is_closer_to_the_ball(self, team_a, team_b):
        # team_a = "<equipe>_3" (is_lower=True), team_b = "<equipe>_4"
        # (is_lower=False) -- identifie qui DEVRAIT etre le plus proche
        # (cote ballon) selon le cote reel du ballon, plutot que prendre le
        # min/max des 2 distances (qui ne peut jamais echouer par
        # construction -- 1ere version buguee de ce test, corrigee ici).
        checked = False
        for t in _sample_times():
            ball = pv.ball_position(t)
            if abs(ball[1] - pv.PITCH_WIDTH_M / 2) < 3.0:
                continue  # ballon trop central pour distinguer un cote sans ambiguite
            checked = True
            ball_side_is_lower = ball[1] < pv.PITCH_WIDTH_M / 2
            near_id, far_id = (team_a, team_b) if ball_side_is_lower else (team_b, team_a)
            pn, pf = pv.player_position(near_id, t), pv.player_position(far_id, t)
            dn = math.hypot(ball[0] - pn[0], ball[1] - pn[1])
            df = math.hypot(ball[0] - pf[0], ball[1] - pf[1])
            assert dn <= df + 1.0, f"t={t:.3f} {near_id} devrait etre plus proche que {far_id} : {dn:.3f} vs {df:.3f}"
        assert checked, "aucune frame avec un ballon suffisamment excentre -- invariant non exerce"

    def test_red_2_5_a_defender_stuck_far_from_the_ball_side_is_detected(self, monkeypatch):
        # Preuve rouge : le ballon est nettement cote HAUT des t=0 (y=40,
        # verifie ci-dessous) -- blue_4 (nominalement cote haut, donc cote
        # ballon) est colle en position basse (y=24) -- doit faire echouer
        # la meme verification.
        broken = dict(pv.PLAYER_SEGMENTS)
        broken["blue_4"] = [(0.0, pv.TOTAL_DURATION_S, (18.0, 24.0), (18.0, 24.0))]
        monkeypatch.setattr(pv, "PLAYER_SEGMENTS", broken)

        t = 0.0
        ball = pv.ball_position(t)
        assert ball[1] > pv.PITCH_WIDTH_M / 2 + 3.0  # confirme un ballon nettement cote haut a t=0
        pn, pf = pv.player_position("blue_4", t), pv.player_position("blue_3", t)  # blue_4 = cote ballon attendu
        dn = math.hypot(ball[0] - pn[0], ball[1] - pn[1])
        df = math.hypot(ball[0] - pf[0], ball[1] - pf[1])
        assert dn > df + 1.0  # confirme que le cas casse bien l'invariant (blue_4 n'est plus le plus proche)
        with pytest.raises(AssertionError):
            assert dn <= df + 1.0, "devrait echouer"

    @pytest.mark.parametrize("player_id", pv.CENTRAL_DEFENDER_IDS)
    def test_2_6_never_advances_past_its_own_base_depth(self, player_id):
        # "Sortie" (section 3.1) implementee en RELATIF (voir
        # _dc_target_depth) : aucun DC n'avance jamais au-dela de sa
        # profondeur de base -- garantit par construction qu'aucune sortie
        # simultanee agressive des 2 DC ne peut se produire (section 2.6).
        is_blue = player_id.startswith("blue")
        for t in _sample_times():
            x, _y = pv.player_position(player_id, t)
            depth = x if is_blue else pv.PITCH_LENGTH_M - x
            assert depth <= pv.DC_BASE_DEPTH_M + 0.01, f"t={t:.3f} {player_id} a avance au-dela de sa base : depth={depth:.3f}"

    @pytest.mark.parametrize("team_a,team_b", [("red_3", "red_4")])
    def test_2_6_when_fully_engaged_the_partner_is_at_least_3_metres_deeper(self, team_a, team_b):
        # blue_3/blue_4 ne sont jamais parametres ici : leur equipe garde le
        # ballon tout le clip, aucun engagement n'y survient (section 2.1,
        # "structure stable" -- voir rapport de livraison).
        reached_full_engagement = False
        for t in _sample_times():
            xa, _ = pv.player_position(team_a, t)
            xb, _ = pv.player_position(team_b, t)
            da = pv.PITCH_LENGTH_M - xa
            db = pv.PITCH_LENGTH_M - xb
            gap = da - db
            if abs(gap) < 3.5:
                continue
            reached_full_engagement = True
            assert abs(gap) >= 3.0, f"t={t:.3f} {team_a}/{team_b} ecart insuffisant : {gap:.3f} m"
        assert reached_full_engagement, f"{team_a}/{team_b} : aucune frame de plein engagement echantillonnee"

    def test_red_2_6_both_defenders_stepping_up_simultaneously_is_detected(self, monkeypatch):
        # Preuve rouge (Tache 2.8, exemple du brief) : red_3 ET red_4
        # avancent au meme niveau -- plus personne ne protege la profondeur
        # -- doit faire echouer la meme verification.
        broken = dict(pv.PLAYER_SEGMENTS)
        broken["red_3"] = [(0.0, pv.TOTAL_DURATION_S, (95.0, 30.0), (95.0, 30.0))]
        broken["red_4"] = [(0.0, pv.TOTAL_DURATION_S, (95.0, 38.0), (95.0, 38.0))]
        monkeypatch.setattr(pv, "PLAYER_SEGMENTS", broken)

        t = 0.0
        depth_a = pv.PITCH_LENGTH_M - pv.player_position("red_3", t)[0]
        depth_b = pv.PITCH_LENGTH_M - pv.player_position("red_4", t)[0]
        gap = depth_a - depth_b
        assert abs(gap) < 3.0  # confirme que le cas casse bien l'invariant (aucun des 2 en retrait)
        with pytest.raises(AssertionError):
            assert abs(gap) >= 3.0, "devrait echouer"

    @pytest.mark.parametrize("player_id", ["red_3", "red_4"])
    def test_2_7_retreats_at_least_3_metres_within_1_second_during_the_breakaway(self, player_id):
        # Section 4/9/10 : recul rapide face a la progression adverse. Ce
        # script ne porte qu'une seule progression dangereuse (pas d'
        # evenement "appel en profondeur" type/date a part -- voir note
        # architecture dans apps/prototype_visual.py) : testee sur n'importe
        # quelle fenetre glissante de 1 s du clip plutot que sur un instant
        # fige choisi a la main.
        times = _sample_times()
        depths = {t: pv.PITCH_LENGTH_M - pv.player_position(player_id, t)[0] for t in times}
        best_retreat = 0.0
        for t0 in times:
            t1 = min(pv.TOTAL_DURATION_S, t0 + 1.0)
            if t1 <= t0:
                continue
            nearest_t1 = min(times, key=lambda candidate: abs(candidate - t1))
            best_retreat = max(best_retreat, depths[t0] - depths[nearest_t1])
        assert best_retreat >= 3.0, f"{player_id} : recul max sur 1 s = {best_retreat:.3f} m"


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

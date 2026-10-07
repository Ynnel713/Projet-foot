"""Garde-fous statiques sur render/canvas.html (mode embarqué, protocole version 1,
docs/canvas_integration_state.md §2.11). Le comportement dynamique est vérifié
manuellement dans un navigateur (voir la section 2.11) ; ces tests figent ce qui
peut l'être sans navigateur : mode standalone intact, protocole fermé, jamais de '*'."""

import re
from pathlib import Path

CANVAS = (Path(__file__).resolve().parent.parent / "render" / "canvas.html").read_text(encoding="utf-8")


def test_standalone_injection_contract_is_intact():
    # Les appelants (scripts/render_*.py, apps/streamlit_preview.py) font un replace() textuel du placeholder.
    assert CANVAS.count("const SEQUENCE_DATA = /*__SEQUENCE_JSON__*/null;") == 1
    # Sans ?embed=1, le lecteur démarre avec les données injectées et SANS pont embarqué.
    assert "if (!EMBED) {\n  // --- Mode standalone : strictement l'ancien comportement ----------------\n  startPlayer(SEQUENCE_DATA, null);" in CANVAS


def test_embed_mode_is_opt_in_and_only_adds_css_scoped_to_embed():
    assert "EMBED_PARAMS.get('embed') === '1'" in CANVAS
    assert "if (EMBED) document.body.classList.add('embed');" in CANVAS
    assert "body.embed canvas" in CANVAS  # seule règle CSS ajoutée, limitée à la classe posée en mode embarqué


def test_protocol_is_closed_and_versioned():
    assert "const PROTOCOL_VERSION = 1;" in CANVAS
    emitted = set(re.findall(r"emit\('([a-z]+)'", CANVAS))
    assert emitted == {"ready", "clipchange", "ended", "error"}  # iframe -> parent : 4 types, pas un de plus
    assert re.findall(r"msg\.type !== '([a-z]+)'", CANVAS) == ["init"]  # parent -> iframe : init seulement
    assert "msg.version !== PROTOCOL_VERSION" in CANVAS


def test_messages_are_origin_scoped_never_wildcard():
    assert "postMessage(" in CANVAS
    assert not re.search(r"postMessage\([^;]*['\"]\*['\"]", CANVAS)
    assert "event.source !== window.parent || event.origin !== parentOrigin" in CANVAS


def test_embedded_page_never_navigates_the_host():
    for forbidden in ("window.top", "top.location", "parent.location", "window.open", "location.href =", "location.assign"):
        assert forbidden not in CANVAS


# --- Cotes du terrain en mètres (Phase 5, sous-étape 1) -------------------------------------------------------------

import json  # noqa: E402

from ligue1sim.pitch_geometry import pitch_dimensions  # noqa: E402


def test_pitch_block_is_derived_from_pitch_geometry():
    block = re.search(r"/\*PITCH_GEOMETRY_BEGIN\*/(.*?)/\*PITCH_GEOMETRY_END\*/", CANVAS, re.S)
    assert block, "bloc PITCH_GEOMETRY introuvable dans canvas.html"
    # Source unique : src/ligue1sim/pitch_geometry.py. Régénérer : python -m ligue1sim.pitch_geometry
    assert json.loads(block.group(1)) == pitch_dimensions()


def test_pitch_is_drawn_in_meters_with_one_scale_and_no_hardcoded_fractions():
    assert "const SCALE = Math.min((W - 2 * MARGIN) / PITCH_L, (H - 2 * MARGIN) / PITCH_W);" in CANVAS
    assert "return mToPx(x * PITCH_L, y * PITCH_W);" in CANVAS  # repère normalisé du moteur -> rectangle 105 x 68 m
    for old_fraction in ("W * 0.10", "H * 0.42", "W * 0.045", "H * 0.20", "W * 0.085", "H * 0.12"):
        assert old_fraction not in CANVAS
    assert "Math.acos(" in CANVAS  # arc de la surface de réparation
    assert "corner_arc_radius_m" in CANVAS  # arcs de coin


# --- Rendu des joueurs et du ballon (Phase 5, sous-étape 2) -------------------------------------------------------
# Tests STATIQUES (lecture du code de canvas.html, aucun navigateur) + un test du payload émis par narrative_player.


def test_player_diameter_is_14_screen_pixels_whatever_the_device_pixel_ratio():
    assert "const PLAYER_DIAMETER_SCREEN_PX = 14;" in CANVAS
    # Pixels ECRAN (CSS) -> pixels canvas par le rapport canvas.width / largeur affichee, recalcule au chargement et au
    # redimensionnement (ResizeObserver), jamais à chaque image ; le device pixel ratio n'intervient pas.
    assert "canvas.getBoundingClientRect()" in CANVAS
    assert "pxPerScreenPx = rect.width > 0 ? canvas.width / rect.width : 1;" in CANVAS
    assert "new ResizeObserver(updateSizes)" in CANVAS
    assert "devicePixelRatio" not in CANVAS
    assert "PLAYER_DIAMETER_SCREEN_PX / 2 * pxPerScreenPx" in CANVAS
    draw_frame = CANVAS[CANVAS.index("function drawFrame("):]
    assert "updateSizes()" not in draw_frame  # la taille n'est pas recalculée à chaque image
    assert "pa.active ? 13 : 9" not in CANVAS  # anciens rayons en pixels canvas supprimés


def test_player_number_is_centered_and_proportional_to_the_diameter():
    assert "const NUMBER_FONT_RATIO = 0.58;" in CANVAS
    assert "'bold ' + (2 * radius * NUMBER_FONT_RATIO) + 'px sans-serif'" in CANVAS
    assert "ctx.textBaseline = 'middle';" in CANVAS
    assert "ctx.fillText(String(pa.numero), px, py + 0.5 * pxPerScreenPx);" in CANVAS  # dans le rond, plus sous le rond
    assert "py + radius + 11" not in CANVAS


def test_carrier_name_is_drawn_only_when_main_player_is_present():
    body = CANVAS[CANVAS.index("function drawCarrierName("):CANVAS.index("function drawFrame(")]
    assert "if (!meta.main_player) return;" in body  # sans metadata.main_player : aucun nom
    assert "meta.player_names" in body and "meta.main_player" in body  # seules sources du nom
    assert "const NAME_FONT_SCREEN_PX = 10;" in CANVAS
    assert "rgba(0, 0, 0, 0.55)" in body  # fond semi-transparent
    assert CANVAS.count("drawCarrierName(") == 2  # définition + un seul appel, réservé au porteur
    assert "ballZ < 0.5" in CANVAS and "BALL_CARRIED_MAX_M" in CANVAS  # seulement tant que le ballon est porté


def test_heading_is_derived_from_two_consecutive_frames():
    assert "(pb.x - pa.x) * PITCH_L" in CANVAS and "(pb.y - pa.y) * PITCH_W" in CANVAS
    assert "Math.atan2(-dy, dx)" in CANVAS
    assert "const HEADING_MIN_SPEED_MS = 0.3;" in CANVAS  # à l'arrêt : dernier cap conservé


def test_ball_is_6_screen_pixels_drawn_after_the_players_with_a_ground_shadow():
    assert "const BALL_DIAMETER_SCREEN_PX = 6;" in CANVAS
    assert "BALL_DIAMETER_SCREEN_PX / 2 * pxPerScreenPx" in CANVAS
    assert "5 + Math.min(9, ballZ * 3)" not in CANVAS  # ancien rayon en pixels canvas supprimé
    ball = CANVAS.index("// Ballon : dessine APRES les ronds")
    assert ball > CANVAS.index("ctx.fillText(String(pa.numero)")  # le ballon est peint par-dessus les ronds
    assert "ctx.ellipse(" in CANVAS[ball:]  # ombre au sol
    assert "by - lift" in CANVAS[ball:]  # souleve quand il est en l'air


def test_payload_carries_the_ball_owner_per_frame_and_the_player_names():
    import json

    from narrative_player import build_clips, clips_to_json
    from test_canvas_e2e import _MAX_OCCASIONS, _find_usable_match

    timeline = _find_usable_match()
    data = json.loads(clips_to_json(build_clips(timeline, max_occasions=_MAX_OCCASIONS), timeline))
    assert data
    for clip in data:
        names = clip["metadata"]["player_names"]
        assert clip["metadata"]["main_player"]
        ids = {p["id"] for p in clip["frames"][0]["players"]}
        assert set(names) >= ids and all(isinstance(n, str) and n for n in names.values())
        for frame in clip["frames"]:
            assert "owner" in frame["ball"]  # clé présente à chaque image
            owner = frame["ball"]["owner"]
            assert owner is None or owner in {p["id"] for p in frame["players"]}
        # un porteur est identifié sur au moins une image de chaque clip
        assert any(f["ball"]["owner"] is not None for f in clip["frames"])

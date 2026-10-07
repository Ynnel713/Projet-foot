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

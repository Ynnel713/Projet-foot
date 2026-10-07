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

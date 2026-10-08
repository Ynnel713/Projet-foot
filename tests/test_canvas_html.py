"""Garde-fous statiques sur render/canvas.html (mode embarqué, protocole version 1,
docs/canvas_integration_state.md §2.11). Le comportement dynamique est vérifié
manuellement dans un navigateur (voir la section 2.11) ; ces tests figent ce qui
peut l'être sans navigateur : mode standalone intact, protocole fermé, jamais de '*'."""

import re
from pathlib import Path

import pytest

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


# --- Pelouse à bandes, bloc score, bandeau de lecture (Phase 5, sous-étape 3) ------------------------------------
# Tests STATIQUES (lecture du code de canvas.html, aucun navigateur).


def _relative_luminance(hex_color: str) -> float:
    n = int(hex_color.lstrip("#"), 16)

    def lin(c: int) -> float:
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    return 0.2126 * lin(n >> 16 & 255) + 0.7152 * lin(n >> 8 & 255) + 0.0722 * lin(n & 255)


def test_pitch_has_at_least_7_mowing_stripes_in_two_close_greens():
    count = int(re.search(r"const STRIPE_COUNT = (\d+);", CANVAS).group(1))
    assert count >= 7 and count % 2 == 1  # nombre impair : les deux bords ont le même ton
    dark = re.search(r"const GRASS_DARK = '(#[0-9a-fA-F]{6})';", CANVAS).group(1)
    light = re.search(r"const GRASS_LIGHT = '(#[0-9a-fA-F]{6})';", CANVAS).group(1)
    gap = _relative_luminance(light) / _relative_luminance(dark) - 1
    assert 0.05 <= gap <= 0.08, f"écart de luminance {gap:.1%} hors de 5-8 %"
    # Bandes horizontales (parallèles aux touches) sur le terrain seulement, peintes AVANT les lignes.
    stripes = CANVAS.index("for (let i = 1; i < STRIPE_COUNT; i += 2) ctx.fillRect(OX, OY + i * bandH, PITCH_L * SCALE, bandH);")
    assert "const bandH = PITCH_W * SCALE / STRIPE_COUNT;" in CANVAS
    assert stripes < CANVAS.index("ctx.strokeRect(x0, y0, PITCH_L * SCALE, PITCH_W * SCALE);")


def test_scoreboard_shows_both_clubs_the_score_and_the_minute_in_a_fixed_compact_box():
    for element in ('id="sbHome"', 'id="sbScore"', 'id="sbAway"', 'id="sbMinute"'):
        assert element in CANVAS
    # shownScore fournit le score, updateScoreboard l'écrit : on lit les deux fonctions.
    body = CANVAS[CANVAS.index("function shownScore("):CANVAS.index("let currentIdx = 0;")]
    for source in ("clip.metadata.home_team", "clip.metadata.away_team", "clip.metadata.score_after", "clip.metadata.minute"):
        assert source in body
    for target in ("sbHomeEl.textContent", "sbScoreEl.textContent", "sbAwayEl.textContent", "sbMinuteEl.textContent"):
        assert target in body
    css = CANVAS[CANVAS.index("#scoreboard {"):CANVAS.index("#scoreboard .sb-score")]
    assert "background: rgba(0, 0, 0, 0.6)" in css and "border: 1px solid" in css
    assert "height: 26px" in css and "max-width: 200px" in css  # dimensions maximales fixées
    assert "left: 50%" in css and "top: 6px" in css  # haut-centre, loin des surfaces de réparation
    assert "const NAME_NOISE" in CANVAS and "slice(0, 3).toUpperCase()" in CANVAS  # abréviation à 3 lettres


def test_playbar_has_the_four_controls_in_order_and_a_clip_counter():
    bar = CANVAS[CANVAS.index('<div id="playbar">'):CANVAS.index('<div id="controls">')]
    order = [bar.index(f'id="{i}"') for i in ("playPause", "prevClip", "nextClip", "progressBar", "clipCounter")]
    assert order == sorted(order)  # lecture/pause, précédent, suivant, progression, compteur (de gauche à droite)
    assert "<svg" in bar and "&#9208;" not in CANVAS  # icônes SVG monochromes (currentColor), plus d'emoji
    css = CANVAS[CANVAS.index("#playbar {"):CANVAS.index("#playerControls {")]
    height = int(re.search(r"height: (\d+)px", css).group(1))
    assert 48 <= height <= 56 and "background: rgba(0, 0, 0, 0.7)" in css
    assert "width: 32px; height: 32px" in CANVAS  # boutons de 32 x 32 px
    assert "'Clip ' + (activeIdx + 1) + ' / ' + clips.length" in CANVAS
    # Comportement : lecture/pause bascule l'icône, précédent/suivant naviguent, un marqueur saute au clip.
    assert "playPauseBtn.innerHTML = playing ? ICON_PAUSE : ICON_PLAY;" in CANVAS
    assert "jumpToClip(currentIdx - 1)" in CANVAS and "jumpToClip(currentIdx + 1)" in CANVAS
    assert "marker.addEventListener('click', () => jumpToClip(idx));" in CANVAS


def test_progress_bar_distinguishes_goal_markers_from_chance_markers():
    assert "const isGoal = clip.metadata.issue === 'but';" in CANVAS
    assert "'progress-marker ' + (isGoal ? 'goal' : 'chance')" in CANVAS
    goal = re.search(r"\.progress-marker\.goal \{([^}]*)\}", CANVAS).group(1)
    chance = re.search(r"\.progress-marker\.chance \{([^}]*)\}", CANVAS).group(1)
    assert "border-radius: 50%" in goal and "#ffffff" in goal  # but : cercle blanc plein
    assert "rotate(45deg)" in chance and "#9aa0a6" in chance  # occasion : losange gris
    assert "z-index: 2" in goal and "z-index: 1" in chance  # un but n'est jamais masqué par une occasion voisine


# --- Filets de but, animation au but, éclaircissement du score (Phase 5, sous-étape 4) ---------------------------
# Tests STATIQUES (lecture du code de canvas.html, aucun navigateur) + cohérence avec le payload réel.


def test_two_nets_one_per_goal_drawn_behind_players_and_ball():
    assert "function drawNet(dir, deform)" in CANVAS
    body = CANVAS[CANVAS.index("function drawNets("):CANVAS.index("function drawFrame(")]
    assert "for (const dir of [1, -1])" in body and "drawNet(dir," in body  # un filet par but (gauche et droite)
    # Dimensions : cotes de PITCH (pitch_geometry.py), maillage fin, tracé au repos mis en cache (Path2D).
    net = CANVAS[CANVAS.index("function drawNet(dir, deform)"):CANVAS.index("function drawNets(")]
    assert "PITCH.goal_net_depth_m" in net and "PITCH.goal_width_m" in net
    assert "new Path2D()" in net and "staticNetPaths" in CANVAS
    assert "rgba(235, 235, 235, 0.55)" in net  # blanc cassé semi-transparent
    # z-order : après la pelouse et les lignes, AVANT les joueurs et le ballon.
    frame = CANVAS[CANVAS.index("function drawFrame("):]
    assert frame.index("drawPitch();") < frame.index("drawNets(clipData, playhead);") < frame.index("for (const pa of fa.players)")
    assert frame.index("for (const pa of fa.players)") < frame.index("// Ballon : dessine APRES les ronds")


def test_net_animation_is_triggered_only_when_a_goal_is_detected():
    assert 0.4 <= float(re.search(r"const NET_ANIM_S = ([\d.]+);", CANVAS).group(1)) <= 0.6
    detection = CANVAS[CANVAS.index("function goalEvents("):CANVAS.index("function playEnd(")]
    assert "clipData.metadata.issue === 'but'" in detection  # sans but : aucun évènement, donc aucune animation
    assert "Math.abs(b.y - 0.5) <= halfGoal" in detection  # le ballon franchit la ligne ENTRE LES POTEAUX
    assert "f.t - events[events.length - 1].t >= NET_ANIM_S" in detection  # deux animations ne se chevauchent jamais
    net = CANVAS[CANVAS.index("function drawNet(dir, deform)"):CANVAS.index("function drawNets(")]
    assert "Math.exp(-NET_DECAY_PER_S * deform.t) * Math.sin(2 * Math.PI * NET_FREQ_HZ * deform.t)" in net  # sinusoïde amortie
    nets = CANVAS[CANVAS.index("function drawNets("):CANVAS.index("function drawFrame(")]
    assert "goalEvents(clipData)" in nets and "playhead - ev.t < NET_ANIM_S" in nets  # s'arrête d'elle-même
    assert "function drawFrame(clipData, t, playhead = t)" in CANVAS  # mode isolé : aucun évènement, filets au repos
    # Fin de clip prolongée après un but pour que l'animation soit visible avant la carte de titre.
    assert float(re.search(r"const GOAL_HOLD_S = ([\d.]+);", CANVAS).group(1)) >= float(re.search(r"const GOAL_FLASH_S = ([\d.]+);", CANVAS).group(1))
    assert "if (playhead >= endAt) {" in CANVAS and "const endAt = playEnd(clip);" in CANVAS


def test_scoreboard_lightens_once_per_goal_with_a_soft_fade():
    css = CANVAS[CANVAS.index("#scoreboard { transition:"):CANVAS.index("/* Bandeau de lecture")]
    assert "transition: background-color 0.3s ease" in css  # fondu doux
    flash = re.search(r"#scoreboard\.goal-flash \{ background: rgba\((\d+), (\d+), (\d+), ([\d.]+)\);", css)
    assert flash and int(flash.group(1)) > 60  # fond plus clair que rgba(0, 0, 0, 0.6)
    assert float(re.search(r"const GOAL_FLASH_S = ([\d.]+);", CANVAS).group(1)) == 1.0
    body = CANVAS[CANVAS.index("function updateGoalFlash("):CANVAS.rindex("function tick(")]
    assert "if (on !== goalFlashOn) {" in body and "scoreboardEl.classList.toggle('goal-flash', on);" in body  # une fois par but
    assert "updateGoalFlash(" not in CANVAS[CANVAS.index("function drawFrame("):CANVAS.index("// --- Mode \"player\"")]  # jamais dans le rendu de l'image


def _find_match_with_a_goal():
    """Premier match simulé (seed fixe, tentatives bornées) dont les buts sont dans les occasions retenues."""
    import random

    import numpy as np
    from test_canvas_e2e import _MAX_OCCASIONS, _squad

    from ligue1sim.clubs import Club
    from ligue1sim.lineup import pick_best_formation
    from ligue1sim.schedule import Match
    from ligue1sim.simulation import LeagueContext, simulate_match
    from narrative import build_timeline, match_result_from

    for seed in range(100, 400):
        random.seed(seed)
        np.random.seed(seed)
        home, away = Club(name="Home FC", players=_squad("home", 72.0)), Club(name="Away FC", players=_squad("away", 68.0))
        context = LeagueContext.from_clubs([home, away])
        home_lineup, away_lineup = pick_best_formation(home), pick_best_formation(away)
        home_goals, away_goals, events = simulate_match(home, away, context)
        if events is None or home_goals + away_goals == 0:
            continue
        match = Match(home=home.name, away=away.name, home_goals=home_goals, away_goals=away_goals, events=events)
        timeline = build_timeline(match_result_from(match, events, home_lineup, away_lineup, date=str(seed)))
        if any(e.outcome == "but" for e in timeline.events[:_MAX_OCCASIONS]):
            return timeline
    raise AssertionError("aucun match avec un but trouvé")


def test_goal_clips_of_a_real_payload_cross_the_line_between_the_posts():
    import json

    from narrative_player import build_clips, clips_to_json
    from test_canvas_e2e import _MAX_OCCASIONS

    timeline = _find_match_with_a_goal()
    data = json.loads(clips_to_json(build_clips(timeline, max_occasions=_MAX_OCCASIONS), timeline))
    half_goal = 3.66 / 68

    # Echantillonnage a 30 images/s : la derniere image peut tomber juste AVANT la ligne (repli documente de `goalEvents` :
    # « un clip de but sans franchissement mesurable declenche a sa derniere image »). 15,3 % des clips de but sont dans ce cas
    # avant B5, 18,3 % apres (graines 1 a 100) ; on exige donc le franchissement OU une derniere image a moins d'une image de
    # vol (1,5 m a 40 m/s) de la ligne, entre les poteaux.
    last_frame_tolerance = 1.5 / 105

    def crosses(clip):
        if any((f["ball"]["x"] >= 1 or f["ball"]["x"] <= 0) and abs(f["ball"]["y"] - 0.5) <= half_goal for f in clip["frames"]):
            return True
        last = clip["frames"][-1]["ball"]
        distance_to_line = min(abs(last["x"] - 1.0), abs(last["x"]))
        return distance_to_line <= last_frame_tolerance and abs(last["y"] - 0.5) <= half_goal

    goals = [c for c in data if c["metadata"]["issue"] == "but"]
    assert goals, "le match choisi doit contenir au moins un clip de but"
    for clip in goals:
        assert crosses(clip), f"clip de but {clip['metadata']['minute']}' sans franchissement de la ligne entre les poteaux"
    for clip in data:
        if clip["metadata"]["issue"] != "but":
            assert not crosses(clip), "un clip sans but ne doit pas franchir la ligne entre les poteaux"


# --- Score synchronisé avec le but (Phase 5, sous-étape 4 bis) -----------------------------------------------------


def test_scoreboard_keeps_the_old_score_until_the_crossing_frame_then_switches_with_the_flash():
    shown = CANVAS[CANVAS.index("function shownScore("):CANVAS.index("// Bloc score : abreviations")]
    # Avant la frame de franchissement : ancien score ; à partir de cette frame : nouveau score.
    assert "events.length && playhead < events[0].t ? clip.metadata.score_before : clip.metadata.score_after" in shown
    # Hors clip de but (aucun évènement) : score_after dès le début, comme avant.
    assert "const events = goalEvents(clip);" in shown
    assert "function updateScoreboard(clip, playhead = 0) {" in CANVAS  # sans position de lecture : début du clip
    assert "const [dom, ext] = shownScore(clip, playhead);" in CANVAS
    # Même frame que le flash : même position de lecture, même instant de franchissement (conditions complémentaires).
    flash = CANVAS[CANVAS.index("function updateGoalFlash("):CANVAS.rindex("function tick(")]
    assert "playhead >= ev.t && playhead - ev.t < GOAL_FLASH_S" in flash  # flash actif dès playhead >= ev.t
    assert "updateScoreboard(clip, playhead);\n    updateGoalFlash(clip, playhead);" in CANVAS.replace("\r\n", "\n")  # même appel, même playhead
    # Le temps de franchissement est celui de la détection (sous-étape 4), inchangé.
    assert "events.push({ t: f.t, dir: side, yM: b.y * PITCH_W });" in CANVAS


def test_goal_clips_carry_a_score_that_changes_by_exactly_one_goal():
    import json

    from narrative_player import build_clips, clips_to_json
    from test_canvas_e2e import _MAX_OCCASIONS

    timeline = _find_match_with_a_goal()
    data = json.loads(clips_to_json(build_clips(timeline, max_occasions=_MAX_OCCASIONS), timeline))
    for clip in data:
        before, after = clip["metadata"]["score_before"], clip["metadata"]["score_after"]
        delta = (after[0] - before[0]) + (after[1] - before[1])
        assert delta == (1 if clip["metadata"]["issue"] == "but" else 0), f"clip {clip['metadata']['minute']}' : {before} -> {after}"


# --- Phase 6, B4-bis : consommation de `metadata.events_ball` (parade, poteau, barre, corner, sortie de but) ------
# Tests STATIQUES (lecture du code, aucun navigateur) + cohérence avec le payload réel. Le rendu a été vérifié dans
# le navigateur intégré (captures avant / après dans docs/previews/phase6/b4_bis/).


def test_canvas_reads_the_optional_ball_events_field_of_the_payload():
    assert "clipData.metadata.events_ball" in CANVAS
    assert "Array.isArray(clipData.metadata.events_ball)" in CANVAS  # champ OPTIONNEL : absent -> liste vide, rien n'est dessiné
    assert (
        "const BALL_FX_LABELS = { parade: 'Parade', poteau: 'Poteau', barre: 'Barre', corner: 'Corner', sortie_but: 'Sortie de but' };"
        in CANVAS
    )
    # Seuls les types connus sont retenus (un type inconnu ou `but` / `touche` / `degagement` est ignoré).
    assert "Object.prototype.hasOwnProperty.call(BALL_FX_LABELS, ev.type)" in CANVAS
    assert "'but'" not in CANVAS[CANVAS.index("const BALL_FX_LABELS"):CANVAS.index("const BALL_FX_LABELLED")]


def test_each_visible_ball_event_has_its_own_animation_drawn_after_the_ball():
    body = CANVAS[CANVAS.index("function drawBallEvents("):CANVAS.index("function drawNet(dir, deform)")]
    assert "ev.type === 'parade'" in body and "ev.direction_deg" in body  # anneau + flèche dans le cap de sortie
    assert "ev.type === 'poteau'" in body  # flash discret sur le poteau
    assert "ev.type === 'barre'" in body  # flash sur la barre (largeur du but)
    assert "ev.type === 'corner'" in body  # éclair sur la ligne + anneau au poteau de corner ; sortie de but : éclair seul
    assert "BALL_FX_LABELLED.has(ev.type)" in body  # étiquette : parade, corner, sortie de but (poteau / barre : discrets)
    frame = CANVAS[CANVAS.index("function drawFrame("):]
    assert frame.index("// Ballon : dessine APRES les ronds") < frame.index("drawBallEvents(clipData, playhead);") < frame.index("if (DEBUG) {")
    assert "if (age < 0 || age >= BALL_FX_LABEL_S) continue;" in body  # chaque effet s'éteint de lui-même


def test_ball_events_reuse_the_existing_durations_and_leave_goal_detection_untouched():
    assert "const BALL_FX_S = NET_ANIM_S;" in CANVAS and "const BALL_FX_LABEL_S = GOAL_FLASH_S;" in CANVAS
    detection = CANVAS[CANVAS.index("function goalEvents("):CANVAS.index("function playEnd(")]
    assert "events_ball" not in detection and "ballEvents" not in detection  # `goalEvents` n'a pas bougé
    # Un évènement de fin de clip (sortie de but) reste visible avant la carte de titre ; le maintien du but est inchangé.
    assert "return Math.max(base, ballEventsEnd(clipData));" in CANVAS
    assert "const base = events.length ? Math.max(clipData.duration, events[events.length - 1].t) + GOAL_HOLD_S : clipData.duration;" in CANVAS
    assert "function ballEventsEnd(clipData)" in CANVAS and "end = Math.max(end, ev.t + BALL_FX_S)" in CANVAS


def test_standalone_contract_and_protocol_are_untouched_by_ball_events():
    assert CANVAS.count("const SEQUENCE_DATA = /*__SEQUENCE_JSON__*/null;") == 1
    assert CANVAS.count("startPlayer(SEQUENCE_DATA, null);") == 1
    assert set(re.findall(r"emit\('([a-z]+)'", CANVAS)) == {"ready", "clipchange", "ended", "error"}
    # Aucun accès réseau ni stockage ajouté par la consommation des évènements.
    for forbidden in ("fetch(", "XMLHttpRequest", "localStorage", "sessionStorage", "WebSocket"):
        assert forbidden not in CANVAS


def test_real_payload_ball_events_match_what_the_player_consumes():
    import json

    from narrative_player import build_clips, clips_to_json
    from test_canvas_e2e import _MAX_OCCASIONS

    known = {"but", "parade", "poteau", "barre", "corner", "sortie_but", "touche", "degagement"}
    timeline = _find_match_with_a_goal()
    data = json.loads(clips_to_json(build_clips(timeline, max_occasions=_MAX_OCCASIONS), timeline))
    seen = set()
    for clip in data:
        events = clip["metadata"].get("events_ball", [])
        for event in events:
            assert event["type"] in known
            assert isinstance(event["t"], (int, float)) and 0.0 <= event["t"] <= clip["duration"] + 1e-6
            assert 0.0 <= event["x"] <= 1.02 and 0.0 <= event["y"] <= 1.0
            assert event["direction_deg"] is None or isinstance(event["direction_deg"], (int, float))
            seen.add(event["type"])
        if clip["metadata"]["issue"] == "arret":
            assert events and events[0]["type"] == "parade"
    assert "but" in seen  # le but reste détecté par le navigateur ; le moteur le signale aussi


# --- Phase 6, B3 : traînée de rotation du ballon (frappes enroulées, `ball.spin`) -----------------------------
# Tests STATIQUES (lecture du code) + comportementaux : les fonctions de traînée sont extraites de canvas.html et
# exécutées sous Node avec un contexte 2D factice (ignorés si Node est absent). Rendu vérifié dans le navigateur
# intégré (captures avant / après dans docs/previews/phase6/b3/).

def _trail_block():
    return CANVAS[CANVAS.index("  const BALL_TRAIL_POINTS"):CANVAS.index("  // --- Filets ---")]


def _trail_constant(name):
    return float(re.search(r"const " + name + r" = ([0-9.]+);", CANVAS).group(1))


def _run_trail(clip_cases):
    """Exécute `drawBallTrail` sur chaque (clip, t) ; renvoie, par cas, la liste des tracés (points, épaisseur, style)."""
    import json
    import shutil
    import subprocess

    import pytest

    node = shutil.which("node")
    if node is None:
        pytest.skip("Node absent : test comportemental de la traînée ignoré")
    find_segment = CANVAS[CANVAS.index("  function findSegment(clipData, t)"):CANVAS.index("  // --- Tailles en PIXELS ECRAN")]
    lerp = CANVAS[CANVAS.index("  function lerp(a, b, f)"):CANVAS.index("  function dot(px, py)")]
    harness = (
        "const SCALE = 10, pxPerScreenPx = 1;\n"
        "function toPx(x, y) { return [x * 1000, y * 600]; }\n"
        "let cur = []; const calls = [];\n"
        "const ctx = { lineCap: '', lineWidth: 0, strokeStyle: '', save() {}, restore() {}, beginPath() { cur = []; },\n"
        "  moveTo(x, y) { cur = [[x, y]]; }, lineTo(x, y) { cur.push([x, y]); },\n"
        "  stroke() { calls.push({ pts: cur.slice(), w: this.lineWidth, style: this.strokeStyle }); } };\n"
        + find_segment + lerp + _trail_block()
        + "const cases = JSON.parse(require('fs').readFileSync(0, 'utf8')); const out = [];\n"
        "for (const [clip, t] of cases) { calls.length = 0; drawBallTrail(clip, t); out.push(calls.slice()); }\n"
        "process.stdout.write(JSON.stringify(out));\n"
    )
    result = subprocess.run([node, "-e", harness], input=json.dumps(clip_cases), capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def _fake_clip(spin, x_step=0.01, n=60):
    """Clip de n images à 30 images/s ; le ballon avance de `x_step` (normalisé) par image, avec ce `spin`."""
    frames = [{"t": round(k / 30, 6), "ball": {"x": 0.1 + k * x_step, "y": 0.5, "z": 0.0, "spin": spin, "owner": None}, "players": []} for k in range(n)]
    return {"fps_target": 30, "frames": frames}


def test_ball_trail_is_drawn_above_the_spin_threshold_and_not_below():
    threshold = _trail_constant("BALL_TRAIL_MIN_SPIN_RAD_S")
    assert threshold == 5
    t = 1.5
    drawn, at_threshold, below, none, negative = _run_trail([
        (_fake_clip(50.0), t), (_fake_clip(threshold), t), (_fake_clip(threshold - 0.1), t), (_fake_clip(0.0), t), (_fake_clip(-50.0), t),
    ])
    assert len(drawn) > 0  # spin = 50 rad/s (frappe enroulée) : traînée
    assert at_threshold == [] and below == [] and none == []  # |spin| <= seuil : rien (le seuil est strict)
    assert len(negative) > 0  # le sens de rotation importe peu : c'est |spin| qui compte


def test_ball_trail_length_is_between_10_and_15_positions():
    points = int(_trail_constant("BALL_TRAIL_POINTS"))
    assert 10 <= points <= 15
    (strokes,) = _run_trail([(_fake_clip(50.0), 1.5)])
    assert len(strokes) == points - 1  # N positions -> N - 1 segments, tous dessinés quand le ballon est lancé
    # Début de clip : moins de positions disponibles ne fausse pas le tracé (positions confondues -> rien d'aberrant).
    (early,) = _run_trail([(_fake_clip(50.0), 0.1)])
    assert len(early) <= points - 1
    # Chaque tracé est un segment entre deux positions consécutives, de l'épaisseur et de l'opacité décroissantes.
    widths = [s["w"] for s in strokes]
    assert widths == sorted(widths, reverse=True) and widths[0] <= 2.0 + 1e-9 and widths[-1] >= 0.4 - 1e-9
    alphas = [float(re.search(r", ([0-9.]+)\)$", s["style"]).group(1)) for s in strokes]
    assert alphas == sorted(alphas, reverse=True) and alphas[0] <= 0.6 + 1e-9 and alphas[-1] > 0.0


def test_ball_trail_follows_the_real_ball_positions_and_is_deterministic():
    clip = _fake_clip(50.0)
    # Trajectoire non rectiligne : le ballon dévie latéralement (parabole), la traînée doit épouser ces positions.
    for k, frame in enumerate(clip["frames"]):
        frame["ball"]["y"] = 0.5 + 0.0004 * k * k
    t = 1.5
    first, second = _run_trail([(clip, t), (clip, t)])
    assert first == second  # même payload, même instant : mêmes tracés
    for k, stroke in enumerate(first):
        for j, (px, py) in enumerate(stroke["pts"]):
            frame = clip["frames"][round((t - (k + j) / 30) * 30)]
            assert px == pytest.approx(frame["ball"]["x"] * 1000, abs=1e-2) and py == pytest.approx(frame["ball"]["y"] * 600, abs=1e-2)


def test_ball_trail_is_not_drawn_while_the_ball_is_rolling_without_spin_or_at_rest():
    moving_without_spin = _fake_clip(0.0, x_step=0.01)  # passe / ballon qui roule : spin = 0
    resting_with_spin = _fake_clip(50.0, x_step=0.0)  # spin posé mais ballon immobile : pas de traînée
    slow_roll = _fake_clip(0.0, x_step=0.0004)
    a, b, c = _run_trail([(moving_without_spin, 1.5), (resting_with_spin, 1.5), (slow_roll, 1.5)])
    assert a == [] and b == [] and c == []


def test_ball_trail_is_drawn_under_the_ball_after_the_players_and_leaves_the_payload_alone():
    frame = CANVAS[CANVAS.index("function drawFrame("):]
    assert frame.index("drawBallTrail(clipData, t);") < frame.index("// Ballon : dessine APRES les ronds") < frame.index("drawBallEvents(clipData, playhead);")
    assert "BALL_DIAMETER_SCREEN_PX = 6;" in CANVAS  # le ballon reste à 6 px (décision Phase 5)
    block = _trail_block()
    assert ".spin =" not in block and "frames.push" not in block  # le payload n'est que lu
    for forbidden in ("Math.random", "Date.now", "performance.now"):
        assert forbidden not in block  # traînée déterministe : fonction pure de l'instant
    # Contrat standalone et protocole intacts.
    assert CANVAS.count("const SEQUENCE_DATA = /*__SEQUENCE_JSON__*/null;") == 1
    assert CANVAS.count("startPlayer(SEQUENCE_DATA, null);") == 1
    assert set(re.findall(r"emit\('([a-z]+)'", CANVAS)) == {"ready", "clipchange", "ended", "error"}
    for forbidden in ("fetch(", "XMLHttpRequest", "localStorage", "sessionStorage", "WebSocket"):
        assert forbidden not in CANVAS

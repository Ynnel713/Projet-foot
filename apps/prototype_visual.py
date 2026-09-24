"""Prototype visuel ISOLÉ (brief "isolated visual prototype", 24/09/2026) --
le rendu existant (moteur d'animation complet : templates/sequence_generator/
motion/ball/state/physics) reste à 1/10 malgré 3 briefs de correctifs
techniques empilés (band, porteur-ballon, drift, contrainte d'accélération)
: aucun n'a changé la perception visuelle. Ce fichier répond à une question
différente -- "sait-on faire crédible sans l'architecture existante ?" --
en scriptant à la main UNE séquence, sans réutiliser une seule ligne du
moteur.

AUCUNE DÉPENDANCE AU MOTEUR : aucun import de `ligue1sim.animation.*`
(templates/narrative_player/motion/ball/sequence_generator/state/physics).
Fichier 100% autosuffisant -- ses propres constantes de terrain, sa propre
interpolation, son propre rendu HTML/JS embarqué (aucune lib externe, aucun
CDN).

Référentiel : mètres, x ∈ [0, 105] (longueur), y ∈ [0, 68] (largeur),
origine bas-gauche. L'équipe "blue" attaque vers x=105 (son but est en
x=0) ; l'équipe "red" attaque vers x=0 (son but est en x=105).

Trajectoires PARAMÉTRÉES (Tâche 2.3) : chaque joueur est une liste de
SEGMENTS `(t0, t1, (x0, y0), (x1, y1))` -- une poignée par joueur clé (2 à 5
segments pour re-scripter recuperation -> conduite -> passe -> course ->
tir), UN SEUL pour les 19 autres (position de départ -> position d'arrivée
sur toute la durée du clip, mouvement de fond continu : latéral qui recule,
ailier qui appelle, gardien qui suit le ballon du regard). Aucun tableau de
positions frame par frame.

Interpolation : `ease()` est un "smoothstep" (`3u² - 2u³`), dérivée nulle
aux DEUX bornes de chaque segment -- contrairement au système existant (12
gabarits + Bézier + Sequence.keyframes), enchaîner un segment qui se termine
à vitesse nulle avec un segment suivant qui démarre à vitesse nulle ne
produit JAMAIS de saut de vitesse à la jonction : c'est la raison
structurelle pour laquelle ce prototype n'a pas les artefacts du moteur
existant (pas une meilleure formule magique, juste une continuité de
vitesse garantie par construction aux points de recollement)."""

from __future__ import annotations

import json
import math
from pathlib import Path

import streamlit as st

# --- Terrain (dimensions FIFA, voir docs/visual_backlog.md #1/#4/#5) -------
PITCH_LENGTH_M = 105.0
PITCH_WIDTH_M = 68.0
GOAL_WIDTH_M = 7.32
PENALTY_AREA_LENGTH_M = 16.5
PENALTY_AREA_WIDTH_M = 40.32
GOAL_AREA_LENGTH_M = 5.5
GOAL_AREA_WIDTH_M = 18.32
PENALTY_SPOT_DIST_M = 11.0
CENTER_CIRCLE_RADIUS_M = 9.15

TOTAL_DURATION_S = 12.0
FPS = 30

# --- Trajectoires des joueurs (Tâche 2.3) ----------------------------------
# `Segment = (t0, t1, (x0, y0), (x1, y1))`. Un seul segment = mouvement de
# fond continu sur tout le clip ; plusieurs segments = les 3 protagonistes
# du script (Tâche 2.1).
PLAYER_SEGMENTS: dict[str, list[tuple[float, float, tuple[float, float], tuple[float, float]]]] = {
    # --- Blue (attaque vers x=105) -----------------------------------------
    "blue_1": [(0.0, TOTAL_DURATION_S, (8.0, 34.0), (9.0, 32.0))],  # gardien -- suit le ballon du regard, micro-lateral
    "blue_2": [(0.0, TOTAL_DURATION_S, (22.0, 12.0), (26.0, 14.0))],
    "blue_3": [(0.0, TOTAL_DURATION_S, (18.0, 26.0), (22.0, 27.0))],
    "blue_4": [(0.0, TOTAL_DURATION_S, (18.0, 42.0), (22.0, 41.0))],
    "blue_5": [(0.0, TOTAL_DURATION_S, (22.0, 56.0), (27.0, 54.0))],
    "blue_6": [(0.0, TOTAL_DURATION_S, (35.0, 34.0), (42.0, 35.0))],
    "blue_7": [(0.0, TOTAL_DURATION_S, (40.0, 18.0), (56.0, 15.0))],  # cote oppose -- appel
    "blue_11": [(0.0, TOTAL_DURATION_S, (48.0, 14.0), (60.0, 12.0))],  # cote oppose -- appel
    # #8 : recupere (0-2s), conduit balle au pied en accelerant (2-4s), puis
    # soutien apres la passe (4-12s).
    "blue_8": [
        (0.0, 2.0, (32.0, 40.0), (33.0, 39.0)),
        (2.0, 4.0, (33.0, 39.0), (46.0, 35.0)),
        (4.0, TOTAL_DURATION_S, (46.0, 35.0), (50.0, 33.0)),
    ],
    # #10 : en place (0-3.5s), appel en profondeur pour recevoir (3.5-5s),
    # conduit vers la surface (5-8.7s), soutien apres la 2e passe.
    "blue_10": [
        (0.0, 3.5, (50.0, 55.0), (58.0, 50.0)),
        (3.5, 5.0, (58.0, 50.0), (64.0, 42.0)),
        (5.0, 8.7, (64.0, 42.0), (85.0, 36.0)),
        (8.7, TOTAL_DURATION_S, (85.0, 36.0), (88.0, 35.0)),
    ],
    # #9 : en place puis remonte progressivement dans la surface (0-8.7s),
    # dernier ajustement pour recevoir (8.7-9.3s), controle+frappe (9.3-9.6s),
    # celebration (9.6-12s).
    "blue_9": [
        (0.0, 5.0, (55.0, 34.0), (60.0, 33.0)),
        (5.0, 8.7, (60.0, 33.0), (88.0, 32.0)),
        (8.7, 9.3, (88.0, 32.0), (90.0, 33.0)),
        (9.3, 9.6, (90.0, 33.0), (91.0, 33.0)),
        (9.6, TOTAL_DURATION_S, (91.0, 33.0), (94.0, 36.0)),
    ],
    # --- Red (attaque vers x=0, defend pres de x=105) -----------------------
    "red_1": [(0.0, TOTAL_DURATION_S, (97.0, 34.0), (97.0, 30.0))],  # gardien -- suit le ballon du regard
    "red_2": [(0.0, TOTAL_DURATION_S, (75.0, 14.0), (88.0, 16.0))],  # recule
    "red_3": [(0.0, TOTAL_DURATION_S, (80.0, 26.0), (90.0, 27.0))],
    "red_4": [(0.0, TOTAL_DURATION_S, (80.0, 42.0), (90.0, 40.0))],
    "red_5": [(0.0, TOTAL_DURATION_S, (75.0, 56.0), (88.0, 54.0))],
    "red_6": [(0.0, TOTAL_DURATION_S, (68.0, 34.0), (80.0, 34.0))],
    "red_7": [(0.0, TOTAL_DURATION_S, (65.0, 16.0), (78.0, 18.0))],
    "red_8": [(0.0, TOTAL_DURATION_S, (60.0, 42.0), (75.0, 38.0))],
    "red_9": [(0.0, TOTAL_DURATION_S, (50.0, 30.0), (65.0, 33.0))],  # attaquant qui repli defensivement
    "red_10": [(0.0, TOTAL_DURATION_S, (55.0, 50.0), (70.0, 45.0))],
    "red_11": [(0.0, TOTAL_DURATION_S, (58.0, 34.0), (72.0, 35.0))],
}

# --- Trajectoire du ballon (Tâche 2.4, invariants 3/4) ---------------------
# 3 types de phase :
#   ("possession", carrier_id, t0, t1)      -- ballon COLLE au porteur (invariant 3, distance 0 <= 0.5 m)
#   ("flight", (x0,y0), (x1,y1), t0, t1)    -- vol explicitement scripté (invariant 4), independant de tout joueur
#   ("static", (x, y), t0, t1)              -- immobile, jamais touche (invariant 4)
# Chaque frontiere possession<->flight utilise EXACTEMENT la position du
# porteur au bord du segment (voir PLAYER_SEGMENTS ci-dessus) : continuité
# du ballon garantie par construction, jamais un recalage a posteriori.
BALL_PHASES: list[tuple] = [
    ("possession", "blue_8", 0.0, 4.0),
    ("flight", (46.0, 35.0), (64.0, 42.0), 4.0, 5.0),
    ("possession", "blue_10", 5.0, 8.7),
    ("flight", (85.0, 36.0), (90.0, 33.0), 8.7, 9.3),
    ("possession", "blue_9", 9.3, 9.6),
    ("flight", (91.0, 33.0), (105.0, 31.0), 9.6, 10.2),
    ("static", (105.0, 31.0), 10.2, TOTAL_DURATION_S),
]


def ease(u: float) -> float:
    """Smoothstep -- dérivée nulle en u=0 et u=1 (voir docstring de
    module) : c'est ce qui garantit une vitesse CONTINUE à la jonction
    entre deux segments consécutifs, sans rien de plus."""
    u = min(1.0, max(0.0, u))
    return 3.0 * u * u - 2.0 * u * u * u


def _interp_segment(t0: float, t1: float, start: tuple[float, float], end: tuple[float, float], t: float) -> tuple[float, float]:
    if t1 <= t0:
        return end
    u = ease((t - t0) / (t1 - t0))
    return (start[0] + (end[0] - start[0]) * u, start[1] + (end[1] - start[1]) * u)


def player_position(player_id: str, t: float) -> tuple[float, float]:
    segments = PLAYER_SEGMENTS[player_id]
    t = min(max(t, segments[0][0]), segments[-1][1])
    for t0, t1, start, end in segments:
        if t0 <= t <= t1:
            return _interp_segment(t0, t1, start, end, t)
    return segments[-1][3]


def ball_position(t: float) -> tuple[float, float]:
    t = min(max(t, 0.0), TOTAL_DURATION_S)
    for phase in BALL_PHASES:
        kind, t0, t1 = phase[0], phase[-2], phase[-1]
        if not (t0 <= t <= t1):
            continue
        if kind == "possession":
            _, carrier, _, _ = phase
            return player_position(carrier, t)
        if kind == "flight":
            _, start, end, _, _ = phase
            return _interp_segment(t0, t1, start, end, t)
        # "static"
        _, pos, _, _ = phase
        return pos
    last = BALL_PHASES[-1]
    return last[1]  # dernier phase = "static", position fixe


def carrier_at(t: float) -> str | None:
    """Porteur du ballon à `t`, ou `None` pendant un vol/à l'arrêt --
    utilisé pour l'invariant 3 (voir tests/test_prototype_visual.py)."""
    for phase in BALL_PHASES:
        kind, t0, t1 = phase[0], phase[-2], phase[-1]
        if t0 <= t <= t1 and kind == "possession":
            return phase[1]
    return None


ALL_PLAYER_IDS = list(PLAYER_SEGMENTS.keys())


def _frame_positions(t: float) -> dict[str, tuple[float, float]]:
    return {pid: player_position(pid, t) for pid in ALL_PLAYER_IDS}


def _build_frames_json() -> str:
    """Précalcule les positions à 30 fps -- le JS n'a plus qu'à interpoler
    linéairement entre 2 frames pré-échantillonnées pour l'affichage (même
    principe que le lecteur existant, `render/canvas.html`, mais aucune
    ligne de ce fichier n'est réutilisée -- implémentation indépendante)."""
    n_frames = int(TOTAL_DURATION_S * FPS) + 1
    frames = []
    for i in range(n_frames):
        t = min(TOTAL_DURATION_S, i / FPS)
        frames.append({
            "t": t,
            "players": {pid: list(pos) for pid, pos in _frame_positions(t).items()},
            "ball": list(ball_position(t)),
        })
    return json.dumps({
        "pitch": {"length": PITCH_LENGTH_M, "width": PITCH_WIDTH_M, "goal_width": GOAL_WIDTH_M,
                  "penalty_area": [PENALTY_AREA_LENGTH_M, PENALTY_AREA_WIDTH_M],
                  "goal_area": [GOAL_AREA_LENGTH_M, GOAL_AREA_WIDTH_M],
                  "penalty_spot": PENALTY_SPOT_DIST_M, "center_circle": CENTER_CIRCLE_RADIUS_M},
        "duration": TOTAL_DURATION_S,
        "frames": frames,
    })


_HTML_TEMPLATE = """
<div id="wrap" style="background:#0b0b0b; font-family:sans-serif; display:flex; flex-direction:column; align-items:center; padding:8px;">
  <canvas id="pitch" width="1050" height="680" style="background:#1e824c; max-width:100%; height:auto;"></canvas>
  <div id="controls" style="padding:8px 0;">
    <button id="play" style="font-size:14px; padding:6px 16px; margin:0 4px;">Pause</button>
    <button id="replay" style="font-size:14px; padding:6px 16px; margin:0 4px;">Recommencer</button>
  </div>
</div>
<script>
const DATA = __DATA_JSON__;
(function () {
  const canvas = document.getElementById('pitch');
  const ctx = canvas.getContext('2d');
  const W = canvas.width, H = canvas.height;
  const P = DATA.pitch;
  const MARGIN = 20;
  const scaleX = (W - 2 * MARGIN) / P.length;
  const scaleY = (H - 2 * MARGIN) / P.width;

  function toPx(x, y) {
    return [MARGIN + x * scaleX, H - (MARGIN + y * scaleY)];
  }

  function drawPitch() {
    ctx.fillStyle = '#1e824c';
    ctx.fillRect(0, 0, W, H);
    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 2;
    ctx.strokeRect(MARGIN, MARGIN, W - 2 * MARGIN, H - 2 * MARGIN);

    const [midTopX, midTopY] = toPx(P.length / 2, P.width);
    const [midBotX, midBotY] = toPx(P.length / 2, 0);
    ctx.beginPath(); ctx.moveTo(midTopX, midTopY); ctx.lineTo(midBotX, midBotY); ctx.stroke();

    const [cx, cy] = toPx(P.length / 2, P.width / 2);
    ctx.beginPath(); ctx.arc(cx, cy, P.center_circle * scaleX, 0, Math.PI * 2); ctx.stroke();
    ctx.beginPath(); ctx.arc(cx, cy, 3, 0, Math.PI * 2); ctx.fillStyle = '#fff'; ctx.fill();

    // Surfaces + arcs + points de penalty, cote gauche (x=0) et droit (x=length)
    for (const side of [0, 1]) {
      const sign = side === 0 ? 1 : -1;
      const baseX = side === 0 ? 0 : P.length;
      const [paX, paY] = toPx(side === 0 ? P.penalty_area[0] : P.length - P.penalty_area[0], P.width / 2 - P.penalty_area[1] / 2);
      const paW = P.penalty_area[0] * scaleX;
      const paH = P.penalty_area[1] * scaleY;
      ctx.strokeRect(side === 0 ? MARGIN : paX, paY, paW, paH);

      const [gaX, gaY] = toPx(side === 0 ? P.goal_area[0] : P.length - P.goal_area[0], P.width / 2 - P.goal_area[1] / 2);
      const gaW = P.goal_area[0] * scaleX;
      const gaH = P.goal_area[1] * scaleY;
      ctx.strokeRect(side === 0 ? MARGIN : gaX, gaY, gaW, gaH);

      const [spotX, spotY] = toPx(side === 0 ? P.penalty_spot : P.length - P.penalty_spot, P.width / 2);
      ctx.beginPath(); ctx.arc(spotX, spotY, 3, 0, Math.PI * 2); ctx.fill();

      ctx.beginPath();
      const startAngle = side === 0 ? -0.9 : Math.PI - 0.9;
      const endAngle = side === 0 ? 0.9 : Math.PI + 0.9;
      ctx.arc(spotX, spotY, P.center_circle * scaleX, startAngle, endAngle);
      ctx.stroke();

      const goalHalf = (P.goal_width / 2) * scaleY;
      const [gx, gyTop] = toPx(baseX, P.width / 2 + P.goal_width / 2);
      const [, gyBot] = toPx(baseX, P.width / 2 - P.goal_width / 2);
      ctx.lineWidth = 4;
      ctx.beginPath(); ctx.moveTo(gx, gyTop); ctx.lineTo(gx, gyBot); ctx.stroke();
      ctx.lineWidth = 2;
    }
  }

  function findFrame(t) {
    const frames = DATA.frames;
    const idx = Math.min(frames.length - 1, Math.max(0, Math.round(t / (DATA.duration / (frames.length - 1)))));
    return frames[idx];
  }

  function drawFrame(t) {
    drawPitch();
    const frame = findFrame(t);
    for (const [pid, pos] of Object.entries(frame.players)) {
      const [px, py] = toPx(pos[0], pos[1]);
      const numero = pid.split('_')[1];
      ctx.beginPath();
      ctx.arc(px, py, 6, 0, Math.PI * 2);
      ctx.fillStyle = pid.startsWith('blue') ? '#1d4ed8' : '#dc2626';
      ctx.fill();
      ctx.lineWidth = 1;
      ctx.strokeStyle = '#000';
      ctx.stroke();
      ctx.fillStyle = '#fff';
      ctx.font = '9px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(numero, px, py - 9);
    }
    const [bx, by] = toPx(frame.ball[0], frame.ball[1]);
    ctx.beginPath();
    ctx.arc(bx, by, 3, 0, Math.PI * 2);
    ctx.fillStyle = '#ffffff';
    ctx.fill();
    ctx.lineWidth = 1;
    ctx.strokeStyle = '#000';
    ctx.stroke();
  }

  let playing = true;
  let pausedAtS = 0;
  let startPerfMs = null;

  function currentT(nowMs) {
    if (!playing) return pausedAtS;
    if (startPerfMs === null) startPerfMs = nowMs - pausedAtS * 1000;
    return Math.min(DATA.duration, (nowMs - startPerfMs) / 1000);
  }

  function tick(nowMs) {
    const t = currentT(nowMs);
    if (playing) pausedAtS = t;
    drawFrame(t);
    requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);

  document.getElementById('play').addEventListener('click', () => {
    playing = !playing;
    document.getElementById('play').textContent = playing ? 'Pause' : 'Lecture';
    if (playing) startPerfMs = null;
  });
  document.getElementById('replay').addEventListener('click', () => {
    pausedAtS = 0;
    startPerfMs = null;
    playing = true;
    document.getElementById('play').textContent = 'Pause';
  });
})();
</script>
"""


def render_html() -> str:
    return _HTML_TEMPLATE.replace("__DATA_JSON__", _build_frames_json())


if __name__ == "__main__":
    st.set_page_config(page_title="Prototype visuel isolé", layout="wide")
    st.title("Prototype visuel isolé -- contre-attaque scriptée")
    st.caption(
        "Aucune dépendance au moteur existant (templates/narrative_player/motion/ball/sequence_generator/state/physics). "
        "22 joueurs, trajectoires paramétrées (segments start/end/t0/t1, interpolation smoothstep), "
        f"{TOTAL_DURATION_S:.0f} s de contre-attaque."
    )
    st.components.v1.html(render_html(), height=760, scrolling=False)

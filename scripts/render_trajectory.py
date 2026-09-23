"""Preuve visuelle stroboscopique de l'effet Magnus (brief "trajectory
stroboscopic proof", 23/09/2026) -- ne modifie ni ball.py, ni templates.py,
ni canvas.html : lit uniquement `ball_state_at` sur une `Sequence` produite
par le pipeline existant. Le spin de comparaison (`--spin 0`) est forcé sur
une COPIE locale de la Sequence (`dataclasses.replace`), jamais sur le
gabarit lui-même -- `build_from_template` reste intact.

Le brief demande "decalege_enroulee" -- "decalage_enroulee" (voir
templates.py) est le nom réel, même substitution documentée que dans les
briefs précédents.

Usage :
    uv run python scripts/render_trajectory.py [--template NOM] [--spin VALEUR] [--output CHEMIN]
"""

from __future__ import annotations

import argparse
import math
import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from PIL import Image, ImageDraw  # noqa: E402

from ligue1sim.animation.ball import ball_state_at  # noqa: E402
from ligue1sim.animation.templates import BUILDERS  # noqa: E402
from ligue1sim.events import GoalEvent  # noqa: E402
from ligue1sim.lineup import Lineup  # noqa: E402
from ligue1sim.pitch_geometry import PITCH_LENGTH_M, PITCH_WIDTH_M, PitchPoint, Zone  # noqa: E402
from ligue1sim.players import Player  # noqa: E402

_TEMPLATE_NAME = "decalage_enroulee"
_N_SAMPLES = 10
_OUTPUT_DIR = Path(__file__).resolve().parent.parent / "docs" / "previews" / "canvas"
_W, _H, _MARGIN_PX = 900, 600, 70


def _lineup() -> Lineup:
    names = [("GK", "gk"), ("DC", "cb0"), ("DC", "cb1"), ("LB", "lb"), ("RB", "rb"), ("MDC", "mdc"), ("MC", "mc0"), ("MC", "mc1"), ("AG", "ag"), ("AD", "ad"), ("BU", "bu")]
    players = [Player(prenom=n, nom="", nationalite="France", age=25, poste=p, note=70.0, club="C", championnat="T", id=i + 1) for i, (p, n) in enumerate(names)]
    return Lineup(club_name="Test FC", formation="4-3-3", players=players, rating=70.0)


def _event() -> GoalEvent:
    return GoalEvent(club_name="Test FC", scorer="bu", assist="mc0", minute=34, zone=Zone(col=10, row=4), assist_zone=Zone(col=7, row=3))


def _force_spin(sequence, spin: float):
    keyframes = [replace(kf, ball=replace(kf.ball, spin=spin)) if kf.physics_tag == "shot" else kf for kf in sequence.keyframes]
    return replace(sequence, keyframes=keyframes)


def sample_positions(template_name: str, spin_override: float | None):
    lineup = _lineup()
    event = _event()
    start_positions = {p.id: PitchPoint(x=0.15 + 0.06 * i, y=0.1 + 0.07 * i) for i, p in enumerate(lineup.players)}
    sequence = BUILDERS[template_name](event, lineup, start_positions)
    shot_kf = next(kf for kf in sequence.keyframes if kf.physics_tag == "shot")
    shot_spin = shot_kf.ball.spin if spin_override is None else spin_override
    if spin_override is not None:
        sequence = _force_spin(sequence, spin_override)

    t_start = shot_kf.t
    t_end = t_start + (sequence.keyframes[-1].t - t_start) / 2  # brief : "t=2.4 a 4.2s", moitie du segment shot
    times = [t_start + i * (t_end - t_start) / (_N_SAMPLES - 1) for i in range(_N_SAMPLES)]
    states = [ball_state_at(sequence, t) for t in times]
    return states, shot_spin, t_start, t_end


def max_deviation_m(states) -> float:
    """Distance max (m) des points échantillonnés à la corde reliant le
    premier et le dernier point -- 0 par construction si la trajectoire est
    droite (spin=0), > 0 si elle courbe (voir DoD Tâche 2)."""
    start, end = states[0], states[-1]
    dx_m, dy_m = (end.x - start.x) * PITCH_LENGTH_M, (end.y - start.y) * PITCH_WIDTH_M
    chord_len = math.hypot(dx_m, dy_m)
    if chord_len < 1e-9:
        return 0.0
    px_m, py_m = -dy_m / chord_len, dx_m / chord_len  # unitaire perpendiculaire a la corde
    return max(abs((s.x - start.x) * PITCH_LENGTH_M * px_m + (s.y - start.y) * PITCH_WIDTH_M * py_m) for s in states)


def draw_trajectory(states, label: str, output_path: Path) -> None:
    xs, ys = [s.x for s in states], [s.y for s in states]
    span_x, span_y = max(xs) - min(xs) or 1e-6, max(ys) - min(ys) or 1e-6
    x0, x1 = min(xs) - 0.2 * span_x, max(xs) + 0.2 * span_x
    y0, y1 = min(ys) - 0.2 * span_y, max(ys) + 0.2 * span_y

    def to_px(x, y):
        return (x - x0) / (x1 - x0) * (_W - 2 * _MARGIN_PX) + _MARGIN_PX, _H - _MARGIN_PX - (y - y0) / (y1 - y0) * (_H - 2 * _MARGIN_PX)

    base = Image.new("RGBA", (_W, _H), (30, 130, 70, 255))  # meme vert que render/canvas.html
    overlay = Image.new("RGBA", (_W, _H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    start_px, end_px = to_px(xs[0], ys[0]), to_px(xs[-1], ys[-1])
    draw.line([start_px, end_px], fill=(255, 255, 255, 150), width=2)  # ligne droite de reference (corde)

    prev = None
    for i, s in enumerate(states):
        frac = i / (_N_SAMPLES - 1)
        point = to_px(s.x, s.y)
        if prev is not None:
            draw.line([prev, point], fill=(255, 210, 0, 220), width=3)  # trajectoire reelle
        radius = 5 + frac * 6
        color = (255, int(60 + 150 * (1 - frac)), 0, 150 + int(80 * frac))  # degrade jaune->rouge = progression temporelle
        draw.ellipse([point[0] - radius, point[1] - radius, point[0] + radius, point[1] + radius], fill=color, outline=(255, 255, 255, 200))
        prev = point

    img = Image.alpha_composite(base, overlay).convert("RGB")
    ImageDraw.Draw(img).text((12, 10), label, fill="white")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--template", default=_TEMPLATE_NAME, help=f"nom du gabarit (defaut {_TEMPLATE_NAME!r})")
    parser.add_argument("--spin", type=float, default=None, help="force le spin du segment shot (ex. 0 pour la comparaison droite) -- defaut : spin reel du gabarit")
    parser.add_argument("--output", default=None, help="chemin de sortie (defaut docs/previews/canvas/trajectory_<template>.png, ou trajectory_straight_comparison.png si --spin 0)")
    args = parser.parse_args()

    if args.template not in BUILDERS:
        raise SystemExit(f"Gabarit inconnu : {args.template!r} -- choisir parmi {sorted(BUILDERS)}")

    states, shot_spin, t_start, t_end = sample_positions(args.template, args.spin)
    deviation_m = max_deviation_m(states)
    label = f"{args.template} -- spin={shot_spin:.1f} rad/s -- segment shot t={t_start:.1f}-{t_end:.1f}s -- deviation max={deviation_m:.2f}m"

    default_name = "trajectory_straight_comparison.png" if args.spin == 0.0 else f"trajectory_{args.template}.png"
    output_path = Path(args.output) if args.output else _OUTPUT_DIR / default_name
    draw_trajectory(states, label, output_path)
    print(f"{output_path} genere -- deviation max mesuree : {deviation_m:.4f} m")

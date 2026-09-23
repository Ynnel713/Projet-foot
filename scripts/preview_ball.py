"""Phase 3.2 : visualise la trajectoire du ballon (`animation.ball.ball_state_at`)
pour chacun des 12 gabarits -- une image PNG par gabarit, dans
docs/previews/ball/ (emplacement canonique, voir docs/simulation_physique_archi.md).

Chaque PNG a deux panneaux :
    - en haut, la trajectoire au sol (x, y) sur le terrain, échantillonnée
      finement, avec les keyframes marquées et colorées par `physics_tag`
      résolu du segment qui les précède (voir animation.ball) ;
    - en bas, un graphe z(t) (hauteur du ballon en mètres au cours du temps).

Usage :
    uv run python scripts/preview_ball.py [gabarit] [dossier_de_sortie]

Sans argument : génère les 12 gabarits d'un coup dans
docs/previews/ball/. Pas de PIL/matplotlib externe au-delà de Pillow
(déjà une dépendance du projet, voir scripts/preview_motion.py) -- le
graphe z(t) est dessiné à la main (axes, grille, polyligne), pas de
nouvelle dépendance ajoutée pour ce script.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from ligue1sim.animation.ball import _find_ball_segment, _resolve_physics_tag, ball_state_at  # noqa: E402
from ligue1sim.animation.templates import BUILDERS  # noqa: E402
from ligue1sim.events import GoalEvent  # noqa: E402
from ligue1sim.lineup import Lineup  # noqa: E402
from ligue1sim.pitch_geometry import CANVAS_WIDTH_PX, PitchPoint, Zone, to_canvas_px  # noqa: E402
from ligue1sim.players import Player  # noqa: E402

_SCORER_ZONE = Zone(col=10, row=4)
_ASSIST_ZONE = Zone(col=7, row=3)
_SAMPLES = 240

_PITCH_H = 420
_GRAPH_H = 220
_MARGIN = 20
_CANVAS_W = CANVAS_WIDTH_PX

_TAG_COLORS = {
    "pass_ground": (90, 160, 230),
    "pass_lob": (230, 190, 60),
    "shot": (220, 60, 60),
    "cross": (60, 200, 120),
    "deflect": (190, 90, 220),
}


def _player(poste: str, note: float, name: str, player_id: int) -> Player:
    return Player(
        prenom=name, nom="", nationalite="France", age=25, poste=poste, note=note,
        club="Test FC", championnat="TEST", id=player_id,
    )


def _lineup() -> Lineup:
    postes_names = [
        ("GK", "gk"), ("DC", "cb0"), ("DC", "cb1"), ("LB", "lb"), ("RB", "rb"),
        ("MDC", "mdc"), ("MC", "mc0"), ("MC", "mc1"), ("AG", "ag"), ("AD", "ad"), ("BU", "bu"),
    ]
    return Lineup(
        club_name="Test FC", formation="4-3-3",
        players=[_player(poste, 70.0, name, i + 1) for i, (poste, name) in enumerate(postes_names)],
        rating=70.0,
    )


def _start_positions(lineup: Lineup) -> dict[int, PitchPoint]:
    return {p.id: PitchPoint(x=0.12 + 0.06 * i, y=0.1 + 0.07 * i) for i, p in enumerate(lineup.players)}


def _goal_event() -> GoalEvent:
    return GoalEvent(
        club_name="Test FC", scorer="bu", assist="mc0", minute=34, penalty=False,
        zone=_SCORER_ZONE, assist_zone=_ASSIST_ZONE,
    )


def _font(size: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("arial.ttf", size)
    except OSError:
        return ImageFont.load_default()


def _segment_tag_at(sequence, kf_index: int) -> str:
    is_last = kf_index == len(sequence.keyframes) - 2
    return _resolve_physics_tag(sequence, sequence.keyframes[kf_index], is_last_segment=is_last)


def _draw_frame(sequence, template_name: str, font: ImageFont.ImageFont, legend_font: ImageFont.ImageFont) -> Image.Image:
    total_h = _MARGIN + _PITCH_H + _MARGIN + _GRAPH_H + _MARGIN + 30
    img = Image.new("RGB", (_CANVAS_W, total_h), (15, 15, 20))
    draw = ImageDraw.Draw(img)
    draw.text((10, 6), f"ball.py -- {template_name}", fill="white", font=font)

    pitch_top = 30
    draw.rectangle([_MARGIN, pitch_top, _CANVAS_W - _MARGIN, pitch_top + _PITCH_H], fill=(34, 120, 62), outline="white", width=2)
    mid_x = (_MARGIN + _CANVAS_W - _MARGIN) / 2
    draw.line([(mid_x, pitch_top), (mid_x, pitch_top + _PITCH_H)], fill="white", width=1)

    def to_px(x: float, y: float) -> tuple[float, float]:
        inner_w = _CANVAS_W - 2 * _MARGIN
        return (_MARGIN + x * inner_w, pitch_top + y * _PITCH_H)

    duration = sequence.duration
    samples = [i / _SAMPLES * duration for i in range(_SAMPLES + 1)]
    points_by_tag: list[tuple[str, tuple[float, float]]] = []
    for t in samples:
        state = ball_state_at(sequence, t)
        kf_a, _kf_b, _s, _is_last = _find_ball_segment(sequence, t)
        idx = sequence.keyframes.index(kf_a)
        tag = _segment_tag_at(sequence, idx) if idx < len(sequence.keyframes) - 1 else _segment_tag_at(sequence, idx - 1)
        points_by_tag.append((tag, to_px(state.x, state.y)))

    for (tag_a, pt_a), (_tag_b, pt_b) in zip(points_by_tag, points_by_tag[1:]):
        draw.line([pt_a, pt_b], fill=_TAG_COLORS.get(tag_a, (200, 200, 200)), width=3)

    for kf in sequence.keyframes:
        px, py = to_px(kf.ball.x, kf.ball.y)
        draw.ellipse([px - 6, py - 6, px + 6, py + 6], fill="white", outline="black", width=1)
        draw.text((px + 8, py - 6), f"t={kf.t:.1f}", fill="white", font=legend_font)

    legend_y = pitch_top + 6
    legend_x = _CANVAS_W - _MARGIN - 140
    for tag, color in _TAG_COLORS.items():
        draw.line([(legend_x, legend_y + 6), (legend_x + 20, legend_y + 6)], fill=color, width=4)
        draw.text((legend_x + 26, legend_y), tag, fill="white", font=legend_font)
        legend_y += 16

    graph_top = pitch_top + _PITCH_H + _MARGIN
    graph_left, graph_right = _MARGIN + 40, _CANVAS_W - _MARGIN
    graph_bottom = graph_top + _GRAPH_H
    z_values = [ball_state_at(sequence, t).z for t in samples]
    z_max = max(0.1, max(z_values))
    draw.line([(graph_left, graph_top), (graph_left, graph_bottom)], fill="white", width=1)
    draw.line([(graph_left, graph_bottom), (graph_right, graph_bottom)], fill="white", width=1)
    draw.text((6, graph_top - 4), f"{z_max:.2f}m", fill="white", font=legend_font)
    draw.text((6, graph_bottom - 8), "0m", fill="white", font=legend_font)
    draw.text((graph_left, graph_bottom + 6), "t=0", fill="white", font=legend_font)
    draw.text((graph_right - 30, graph_bottom + 6), f"t={duration:.1f}s", fill="white", font=legend_font)

    graph_points = []
    for t, z in zip(samples, z_values):
        gx = graph_left + (t / duration) * (graph_right - graph_left)
        gy = graph_bottom - (z / z_max) * (_GRAPH_H - 10)
        graph_points.append((gx, gy))
    for (tag, _pt), p_a, p_b in zip(points_by_tag, graph_points, graph_points[1:]):
        draw.line([p_a, p_b], fill=_TAG_COLORS.get(tag, (200, 200, 200)), width=2)

    return img


def run(template_name: str, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    lineup = _lineup()
    event = _goal_event()
    start_positions = _start_positions(lineup)
    sequence = BUILDERS[template_name](event, lineup, start_positions)

    font = _font(14)
    legend_font = _font(11)
    img = _draw_frame(sequence, template_name, font, legend_font)
    out_path = output_dir / f"{template_name}.png"
    img.save(out_path)
    print(f"{out_path}")


if __name__ == "__main__":
    names = [sys.argv[1]] if len(sys.argv) > 1 and sys.argv[1] in BUILDERS else sorted(BUILDERS)
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).resolve().parent.parent / "docs" / "previews" / "ball"
    for name in names:
        run(name, out)

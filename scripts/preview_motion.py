"""Phase 3.1 : rejoue une `Sequence` interpolée en continu (`animation.motion
.interpolate`) et exporte une image PNG toutes les 0,1 s -- pour voir à
l'œil si le mouvement est crédible (accélération/décélération, vitesses
plafonnées par poste, décalage des joueurs non impliqués, évitement) avant
de passer à la phase 3.2 (ballon).

Usage :
    uv run python scripts/preview_motion.py [gabarit] [dossier_de_sortie]

`gabarit` : un des 12 noms de animation.templates.BUILDERS (défaut :
"corner", qui montre les 3 comportements à la fois -- un rôle "support1"
décalé/runner, un ballon en cloche, un évitement possible en zone dense).

Produit un PNG par frame (frame_0000.png, frame_0001.png...) ET un GIF animé
(le plus utile pour juger d'un coup d'œil) dans le dossier de sortie (défaut
scripts/output/motion_preview/<gabarit>/).
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from ligue1sim.animation.motion import interpolate  # noqa: E402
from ligue1sim.animation.templates import BUILDERS  # noqa: E402
from ligue1sim.events import GoalEvent, PlayerMatchStat  # noqa: E402
from ligue1sim.lineup import Lineup  # noqa: E402
from ligue1sim.pitch_geometry import CANVAS_HEIGHT_PX, CANVAS_WIDTH_PX, PitchPoint, Zone, to_canvas_px  # noqa: E402
from ligue1sim.pitch_layout import place_starting_xi  # noqa: E402
from ligue1sim.animation.spatial import placed_player_to_normalized  # noqa: E402
from ligue1sim.players import Player  # noqa: E402

_SCORER_ZONE = Zone(col=10, row=4)
_ASSIST_ZONE = Zone(col=7, row=3)

_ROLE_COLORS = {
    "scorer": (220, 40, 40),
    "assist": (40, 90, 220),
    "support1": (230, 150, 20),
    "support2": (150, 60, 200),
}
_BACKGROUND_COLOR = (235, 235, 235)  # joueur non impliqué (voir motion._is_primary_role)
_AWAY_COLOR = (140, 150, 170)
_STEP_S = 0.1


def _player(poste: str, note: float, name: str, player_id: int) -> Player:
    return Player(
        prenom=name, nom="", nationalite="France", age=25, poste=poste, note=note,
        club="Test FC", championnat="TEST", id=player_id,
    )


def _four_three_three(id_offset: int) -> list[Player]:
    postes_names = [
        ("GK", "gk"), ("DC", "cb0"), ("DC", "cb1"), ("LB", "lb"), ("RB", "rb"),
        ("MDC", "mdc"), ("MC", "mc0"), ("MC", "mc1"), ("AG", "ag"), ("AD", "ad"), ("BU", "bu"),
    ]
    return [_player(poste, 70.0, name, id_offset + i) for i, (poste, name) in enumerate(postes_names)]


def _home_lineup() -> Lineup:
    return Lineup(club_name="Home FC", formation="4-3-3", players=_four_three_three(1), rating=70.0)


def _away_lineup() -> Lineup:
    return Lineup(club_name="Away FC", formation="4-3-3", players=_four_three_three(101), rating=70.0)


def _placed(lineup: Lineup, *, attacking_up: bool):
    stats = [
        PlayerMatchStat(player_name=p.name, club_name=lineup.club_name, poste=p.poste, started=True)
        for p in lineup.players
    ]
    return place_starting_xi(stats, attacking_up=attacking_up)


def _start_positions(lineup: Lineup) -> dict[int, PitchPoint]:
    by_name = {p.name: p for p in lineup.players}
    positions: dict[int, PitchPoint] = {}
    for pl in _placed(lineup, attacking_up=False):
        player = by_name.get(pl.stat.player_name)
        if player is not None:
            positions[player.id] = placed_player_to_normalized(pl, attacking_up=False)
    return positions


def _away_static_points(away_lineup: Lineup) -> list[PitchPoint]:
    # Même miroir que scripts/preview_templates.py (référentiel relatif à
    # l'équipe -- voir spatial.py) : sans lui, l'adversaire se superpose à
    # l'équipe qui marque sur la scène partagée.
    points = [placed_player_to_normalized(pl, attacking_up=True) for pl in _placed(away_lineup, attacking_up=True)]
    return [PitchPoint(x=1.0 - p.x, y=p.y) for p in points]


def _goal_event() -> GoalEvent:
    return GoalEvent(
        club_name="Home FC", scorer="bu", assist="mc0", minute=34, penalty=False,
        zone=_SCORER_ZONE, assist_zone=_ASSIST_ZONE,
    )


def _font(size: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("arial.ttf", size)
    except OSError:
        return ImageFont.load_default()


def _draw_pitch() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (CANVAS_WIDTH_PX, CANVAS_HEIGHT_PX), (34, 120, 62))
    draw = ImageDraw.Draw(img)
    margin = 20
    draw.rectangle([margin, margin, CANVAS_WIDTH_PX - margin, CANVAS_HEIGHT_PX - margin], outline="white", width=3)
    draw.line([(CANVAS_WIDTH_PX // 2, margin), (CANVAS_WIDTH_PX // 2, CANVAS_HEIGHT_PX - margin)], fill="white", width=2)
    box_w, box_h = int(CANVAS_WIDTH_PX * 0.10), int(CANVAS_HEIGHT_PX * 0.42)
    draw.rectangle([margin, CANVAS_HEIGHT_PX // 2 - box_h // 2, margin + box_w, CANVAS_HEIGHT_PX // 2 + box_h // 2], outline="white", width=1)
    draw.rectangle(
        [CANVAS_WIDTH_PX - margin - box_w, CANVAS_HEIGHT_PX // 2 - box_h // 2, CANVAS_WIDTH_PX - margin, CANVAS_HEIGHT_PX // 2 + box_h // 2],
        outline="white", width=1,
    )
    return img, draw


def _px(x: float, y: float) -> tuple[float, float]:
    return to_canvas_px(PitchPoint(x=x, y=y))


def _draw_frame(
    t: float, frame, away_points: list[PitchPoint], sequence, font: ImageFont.ImageFont, template_name: str
) -> Image.Image:
    img, draw = _draw_pitch()

    for point in away_points:
        px, py = _px(point.x, point.y)
        draw.ellipse([px - 8, py - 8, px + 8, py + 8], fill=_AWAY_COLOR, outline="black", width=1)

    for player_id, state in frame.players.items():
        role = sequence.roster[player_id].role
        color = _ROLE_COLORS.get(role, _BACKGROUND_COLOR)
        px, py = _px(state.x, state.y)
        radius = 11 if role else 8

        # Vecteur vitesse : petit segment dans la direction (vx, vy),
        # longueur proportionnelle à la vitesse (plafonnée visuellement).
        speed = (state.vx**2 + state.vy**2) ** 0.5
        if speed > 1e-6:
            scale = min(45.0, speed * 90.0)
            end_x = px + (state.vx / speed) * scale
            end_y = py - (state.vy / speed) * scale  # axe Y canvas inversé, voir to_canvas_px
            draw.line([(px, py), (end_x, end_y)], fill=(255, 255, 0), width=2)

        outline = (255, 215, 0) if state.is_ball_carrier else "black"
        outline_width = 3 if state.is_ball_carrier else 1
        draw.ellipse([px - radius, py - radius, px + radius, py + radius], fill=color, outline=outline, width=outline_width)
        if role:
            draw.text((px + 13, py - 8), role, fill="white", font=font)

    draw.rectangle([0, 0, CANVAS_WIDTH_PX, 28], fill=(0, 0, 0))
    draw.text((8, 6), f"{template_name} — t={t:.1f}s", fill="white", font=font)
    return img


def run(template_name: str, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    home_lineup = _home_lineup()
    away_lineup = _away_lineup()
    event = _goal_event()
    start_positions = _start_positions(home_lineup)
    away_points = _away_static_points(away_lineup)

    sequence = BUILDERS[template_name](event, home_lineup, start_positions)
    font = _font(14)

    frames: list[Image.Image] = []
    t = 0.0
    index = 0
    while t <= sequence.duration + 1e-9:
        frame = interpolate(sequence, t)
        img = _draw_frame(t, frame, away_points, sequence, font, template_name)
        img.save(output_dir / f"frame_{index:04d}.png")
        frames.append(img)
        index += 1
        t += _STEP_S

    gif_path = output_dir / f"{template_name}.gif"
    frames[0].save(gif_path, save_all=True, append_images=frames[1:], duration=int(_STEP_S * 1000), loop=0)
    print(f"{index} frames PNG + GIF anime : {gif_path}")


if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else "corner"
    if name not in BUILDERS:
        raise SystemExit(f"Gabarit inconnu : {name!r} -- choisir parmi {sorted(BUILDERS)}")
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).resolve().parent / "output" / "motion_preview" / name
    run(name, out)

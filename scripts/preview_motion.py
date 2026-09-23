"""Rejoue une `Sequence` interpolée en continu (`animation.motion.interpolate`)
et exporte un GIF -- pour voir à l'œil si le mouvement est crédible
(accélération/décélération, vitesses plafonnées par poste, décalage des
joueurs non impliqués, évitement) avant de passer à la phase 3.2 (ballon).

Emplacement CANONIQUE des GIFs de validation : docs/previews/ -- c'est là
qu'ils doivent être commités pour rester consultables sans relancer le
script (voir docs/simulation_physique_archi.md).

Par défaut (patché le 23/09/2026, Tâche 4 du brief "contre_attaque carrier
movement") : pipeline COMPLET -- `enrich_with_background` est TOUJOURS
appliqué, donc chaque GIF montre les 22 joueurs (l'équipe qui marque au
complet + les 11 adverses), pas seulement les 2-4 actifs du gabarit sur un
terrain vide. Légende visuelle :
    - contour DORÉ, 3 px : joueur ACTIF (rôle nommé par le gabarit --
      buteur/passeur/support).
    - contour fin, 1 px : joueur "décor" (coéquipier en soutien ou adversaire
      en repli, voir `sequence_generator.enrich_with_background`).
    - couleur de remplissage : équipe (voir `kits.match_kit_colors`).
    - numéro sous chaque rond : `RosterEntry.numero`.
    - petit disque blanc superposé : le porteur du ballon à cet instant.

`--legacy-minimal` reproduit l'ANCIEN comportement (avant `enrich_with_background`,
11 joueurs de l'équipe qui marque + l'adversaire peint en dots statiques
jamais simulés) -- DEBUG UNIQUEMENT, ne montre plus l'état réel du pipeline,
ne pas l'utiliser pour un GIF de validation.

Usage :
    uv run python scripts/preview_motion.py [gabarit] [dossier_de_sortie] [--legacy-minimal] [--fps N]

`gabarit` : un des 12 noms de animation.templates.BUILDERS (défaut : "corner").
`dossier_de_sortie` : défaut scripts/output/motion_preview/<gabarit>/.
`--fps` : images par seconde du GIF (défaut 30).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from ligue1sim.animation.motion import interpolate  # noqa: E402
from ligue1sim.animation.sequence_generator import enrich_with_background  # noqa: E402
from ligue1sim.animation.spatial import placed_player_to_normalized  # noqa: E402
from ligue1sim.animation.templates import BUILDERS  # noqa: E402
from ligue1sim.events import GoalEvent, PlayerMatchStat  # noqa: E402
from ligue1sim.kits import match_kit_colors  # noqa: E402
from ligue1sim.lineup import Lineup  # noqa: E402
from ligue1sim.pitch_geometry import CANVAS_HEIGHT_PX, CANVAS_WIDTH_PX, PitchPoint, Zone, to_canvas_px  # noqa: E402
from ligue1sim.pitch_layout import place_starting_xi  # noqa: E402
from ligue1sim.players import Player  # noqa: E402

_SCORER_ZONE = Zone(col=10, row=4)
_ASSIST_ZONE = Zone(col=7, row=3)
_DEFAULT_FPS = 30

# Clubs réels choisis UNIQUEMENT pour leurs couleurs bien distinctes via
# kits.py (voir match_kit_colors) -- les compos elles-mêmes sont synthétiques
# (joueurs inventés), aucun rapport avec les vrais effectifs de ces clubs.
_SCORER_CLUB = "Paris Saint-Germain"
_OPPONENT_CLUB = "AS Monaco"

_ACTIVE_OUTLINE = (255, 215, 0)  # doré, voir légende en tête de module
_ACTIVE_OUTLINE_WIDTH = 3
_BACKGROUND_OUTLINE = (25, 25, 25)
_BACKGROUND_OUTLINE_WIDTH = 1
_ACTIVE_RADIUS = 12
_BACKGROUND_RADIUS = 9
_BALL_MARKER_RADIUS = 4

# Legacy (--legacy-minimal) : couleurs par rôle, comportement pré-22-joueurs.
_LEGACY_ROLE_COLORS = {
    "scorer": (220, 40, 40),
    "assist": (40, 90, 220),
    "support1": (230, 150, 20),
    "support2": (150, 60, 200),
}
_LEGACY_BACKGROUND_COLOR = (235, 235, 235)
_LEGACY_AWAY_COLOR = (140, 150, 170)


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


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


def _scorer_lineup() -> Lineup:
    return Lineup(club_name=_SCORER_CLUB, formation="4-3-3", players=_four_three_three(1), rating=70.0)


def _opponent_lineup() -> Lineup:
    return Lineup(club_name=_OPPONENT_CLUB, formation="4-3-3", players=_four_three_three(101), rating=65.0)


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


def _away_static_points(opponent_lineup: Lineup) -> list[PitchPoint]:
    # --legacy-minimal uniquement : référentiel relatif à l'équipe (voir
    # spatial.py) -- sans miroir, l'adversaire se superposerait à l'équipe
    # qui marque sur la scène partagée.
    points = [placed_player_to_normalized(pl, attacking_up=True) for pl in _placed(opponent_lineup, attacking_up=True)]
    return [PitchPoint(x=1.0 - p.x, y=p.y) for p in points]


def _goal_event() -> GoalEvent:
    return GoalEvent(
        club_name=_SCORER_CLUB, scorer="bu", assist="mc0", minute=34, penalty=False,
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


def _draw_number(draw: ImageDraw.ImageDraw, cx: float, cy: float, text: str, font: ImageFont.ImageFont) -> None:
    """Numéro centré sous le rond, avec un léger liseré noir (dessiné 4x
    décalé) pour rester lisible sur fond clair OU foncé, sans zoomer."""
    bbox = draw.textbbox((0, 0), text, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x, y = cx - w / 2, cy - h / 2
    for ox, oy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        draw.text((x + ox, y + oy), text, fill="black", font=font)
    draw.text((x, y), text, fill="white", font=font)


def _draw_frame_full(
    t: float,
    frame,
    sequence,
    scorer_colors: tuple[tuple[int, int, int], tuple[int, int, int]],
    opponent_colors: tuple[tuple[int, int, int], tuple[int, int, int]],
    font: ImageFont.ImageFont,
    number_font: ImageFont.ImageFont,
    template_name: str,
) -> Image.Image:
    img, draw = _draw_pitch()
    carrier_id = next((pid for pid, state in frame.players.items() if state.is_ball_carrier), None)

    for player_id, state in frame.players.items():
        entry = sequence.roster[player_id]
        fill, _secondary = scorer_colors if entry.team_side == "scorer" else opponent_colors
        active = entry.role is not None
        outline = _ACTIVE_OUTLINE if active else _BACKGROUND_OUTLINE
        outline_width = _ACTIVE_OUTLINE_WIDTH if active else _BACKGROUND_OUTLINE_WIDTH
        radius = _ACTIVE_RADIUS if active else _BACKGROUND_RADIUS
        px, py = _px(state.x, state.y)

        draw.ellipse([px - radius, py - radius, px + radius, py + radius], fill=fill, outline=outline, width=outline_width)
        if player_id == carrier_id:
            draw.ellipse([px - _BALL_MARKER_RADIUS, py - _BALL_MARKER_RADIUS, px + _BALL_MARKER_RADIUS, py + _BALL_MARKER_RADIUS], fill="white", outline="black", width=1)
        _draw_number(draw, px, py + radius + 9, str(entry.numero), number_font)

    draw.rectangle([0, 0, CANVAS_WIDTH_PX, 28], fill=(0, 0, 0))
    draw.text((8, 6), f"{template_name} — t={t:.1f}s — {len(frame.players)} joueurs (22 attendus)", fill="white", font=font)

    legend_x, legend_y = 8, 36
    draw.ellipse([legend_x, legend_y, legend_x + 12, legend_y + 12], fill=scorer_colors[0], outline=_ACTIVE_OUTLINE, width=_ACTIVE_OUTLINE_WIDTH)
    draw.text((legend_x + 18, legend_y - 1), "Actif (contour dore)", fill="white", font=font)
    legend_y += 18
    draw.ellipse([legend_x, legend_y, legend_x + 12, legend_y + 12], fill=scorer_colors[0], outline=_BACKGROUND_OUTLINE, width=_BACKGROUND_OUTLINE_WIDTH)
    draw.text((legend_x + 18, legend_y - 1), "Coequipier (decor)", fill="white", font=font)
    legend_y += 18
    draw.ellipse([legend_x, legend_y, legend_x + 12, legend_y + 12], fill=opponent_colors[0], outline=_BACKGROUND_OUTLINE, width=_BACKGROUND_OUTLINE_WIDTH)
    draw.text((legend_x + 18, legend_y - 1), "Adversaire", fill="white", font=font)
    return img


def _draw_frame_legacy(
    t: float, frame, away_points: list[PitchPoint], sequence, font: ImageFont.ImageFont, template_name: str
) -> Image.Image:
    img, draw = _draw_pitch()

    for point in away_points:
        px, py = _px(point.x, point.y)
        draw.ellipse([px - 8, py - 8, px + 8, py + 8], fill=_LEGACY_AWAY_COLOR, outline="black", width=1)

    for player_id, state in frame.players.items():
        role = sequence.roster[player_id].role
        color = _LEGACY_ROLE_COLORS.get(role, _LEGACY_BACKGROUND_COLOR)
        px, py = _px(state.x, state.y)
        radius = 11 if role else 8

        speed = (state.vx**2 + state.vy**2) ** 0.5
        if speed > 1e-6:
            scale = min(45.0, speed * 90.0)
            end_x = px + (state.vx / speed) * scale
            end_y = py - (state.vy / speed) * scale
            draw.line([(px, py), (end_x, end_y)], fill=(255, 255, 0), width=2)

        outline = (255, 215, 0) if state.is_ball_carrier else "black"
        outline_width = 3 if state.is_ball_carrier else 1
        draw.ellipse([px - radius, py - radius, px + radius, py + radius], fill=color, outline=outline, width=outline_width)
        if role:
            draw.text((px + 13, py - 8), role, fill="white", font=font)

    draw.rectangle([0, 0, CANVAS_WIDTH_PX, 28], fill=(0, 0, 0))
    draw.text((8, 6), f"{template_name} — t={t:.1f}s [--legacy-minimal, DEBUG]", fill="white", font=font)
    return img


def run(template_name: str, output_dir: Path, *, legacy_minimal: bool, fps: int) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    step_s = 1.0 / fps
    scorer_lineup = _scorer_lineup()
    event = _goal_event()
    start_positions = _start_positions(scorer_lineup)
    sequence = BUILDERS[template_name](event, scorer_lineup, start_positions)

    if legacy_minimal:
        opponent_lineup = _opponent_lineup()
        away_points = _away_static_points(opponent_lineup)
        font = _font(14)
        frames: list[Image.Image] = []
        t = 0.0
        index = 0
        while t <= sequence.duration + 1e-9:
            frame = interpolate(sequence, t)
            frames.append(_draw_frame_legacy(t, frame, away_points, sequence, font, template_name))
            index += 1
            t += step_s
    else:
        sequence = enrich_with_background(sequence, _opponent_lineup())
        scorer_colors = tuple(_hex_to_rgb(c) for c in match_kit_colors(_SCORER_CLUB, _OPPONENT_CLUB)[0])
        opponent_colors = tuple(_hex_to_rgb(c) for c in match_kit_colors(_SCORER_CLUB, _OPPONENT_CLUB)[1])
        font = _font(14)
        number_font = _font(11)
        frames = []
        t = 0.0
        index = 0
        while t <= sequence.duration + 1e-9:
            frame = interpolate(sequence, t)
            frames.append(_draw_frame_full(t, frame, sequence, scorer_colors, opponent_colors, font, number_font, template_name))
            index += 1
            t += step_s

    for i, img in enumerate(frames):
        img.save(output_dir / f"frame_{i:04d}.png")

    suffix = "_legacy" if legacy_minimal else "_22players"
    gif_path = output_dir / f"{template_name}{suffix}.gif"
    frame_duration_ms = round(1000 / fps)
    frames[0].save(gif_path, save_all=True, append_images=frames[1:], duration=frame_duration_ms, loop=0)
    print(f"{index} frames PNG + GIF anime ({fps} fps) : {gif_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("template", nargs="?", default="corner", help="nom du gabarit (animation.templates.BUILDERS)")
    parser.add_argument("output_dir", nargs="?", default=None, help="dossier de sortie (defaut scripts/output/motion_preview/<gabarit>/)")
    parser.add_argument(
        "--legacy-minimal", action="store_true",
        help="DEBUG UNIQUEMENT : reproduit le comportement pre-enrich_with_background (11 joueurs actifs + adversaire en dots statiques jamais simules). Ne montre plus l'etat reel du pipeline -- ne pas utiliser pour un GIF de validation.",
    )
    parser.add_argument("--fps", type=int, default=_DEFAULT_FPS, help=f"images par seconde du GIF (defaut {_DEFAULT_FPS})")
    args = parser.parse_args()

    if args.template not in BUILDERS:
        raise SystemExit(f"Gabarit inconnu : {args.template!r} -- choisir parmi {sorted(BUILDERS)}")
    out = Path(args.output_dir) if args.output_dir else Path(__file__).resolve().parent / "output" / "motion_preview" / args.template
    run(args.template, out, legacy_minimal=args.legacy_minimal, fps=args.fps)

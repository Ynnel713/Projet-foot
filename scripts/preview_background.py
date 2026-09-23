"""Point 3 du brief du 23/09/2026 : GIF de validation des 22 joueurs
(Point 1, `sequence_generator.enrich_with_background`) sur `contre_attaque`
-- vérifie à l'œil que la scène complète (actifs + coéquipiers en soutien +
adversaires en repli) est lisible et cohérente tactiquement (Point 2, drift
par rôle), pas seulement que `interpolate` ne plante pas.

Usage :
    uv run python scripts/preview_background.py [gabarit] [dossier_de_sortie]

`gabarit` : un des 12 noms de animation.templates.BUILDERS (défaut :
"contre_attaque", demandé explicitement dans le brief).

Légende visuelle (voir `_style_for`) : joueurs ACTIFS (rôle de gabarit --
buteur/passeur/support) en couleur vive + contour épais (3 px, doré) ;
coéquipiers "décor" en couleur pastel de la même famille + contour fin
(1 px) ; adversaires en gris-bleu + contour fin. Une légende texte discrète
est dessinée en haut à gauche de chaque frame.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from ligue1sim.animation.motion import interpolate  # noqa: E402
from ligue1sim.animation.sequence_generator import enrich_with_background  # noqa: E402
from ligue1sim.animation.spatial import placed_player_to_normalized  # noqa: E402
from ligue1sim.animation.templates import BUILDERS  # noqa: E402
from ligue1sim.events import GoalEvent, PlayerMatchStat  # noqa: E402
from ligue1sim.lineup import Lineup  # noqa: E402
from ligue1sim.pitch_geometry import CANVAS_HEIGHT_PX, CANVAS_WIDTH_PX, PitchPoint, Zone, to_canvas_px  # noqa: E402
from ligue1sim.pitch_layout import place_starting_xi  # noqa: E402
from ligue1sim.players import Player  # noqa: E402

_SCORER_ZONE = Zone(col=10, row=4)
_ASSIST_ZONE = Zone(col=7, row=3)
_STEP_S = 0.1

# Contour "actif" : 3 px, doré -- la légende visuelle demandée par Olivier
# (Point 3), distincte du contour "décor" (1 px, noir).
_ACTIVE_OUTLINE = (255, 215, 0)
_ACTIVE_OUTLINE_WIDTH = 3
_BACKGROUND_OUTLINE = (20, 20, 20)
_BACKGROUND_OUTLINE_WIDTH = 1

_ACTIVE_ROLE_COLORS = {
    "scorer": (220, 40, 40),
    "assist": (40, 90, 220),
    "support1": (230, 150, 20),
    "support2": (150, 60, 200),
}
_SCORER_BACKGROUND_COLOR = (220, 150, 150)  # pastel de la même famille que le buteur (rouge)
_OPPONENT_BACKGROUND_COLOR = (140, 150, 170)  # gris-bleu, jamais confondu avec l'équipe qui marque


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
    return Lineup(club_name="Home FC", formation="4-3-3", players=_four_three_three(1), rating=70.0)


def _opponent_lineup() -> Lineup:
    return Lineup(club_name="Away FC", formation="4-3-3", players=_four_three_three(101), rating=65.0)


def _start_positions(lineup: Lineup) -> dict[int, PitchPoint]:
    stats = [
        PlayerMatchStat(player_name=p.name, club_name=lineup.club_name, poste=p.poste, started=True)
        for p in lineup.players
    ]
    by_name = {p.name: p for p in lineup.players}
    positions: dict[int, PitchPoint] = {}
    for pl in place_starting_xi(stats, attacking_up=False):
        player = by_name.get(pl.stat.player_name)
        if player is not None:
            positions[player.id] = placed_player_to_normalized(pl, attacking_up=False)
    return positions


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


def _style_for(entry) -> tuple[tuple[int, int, int], tuple[int, int, int], int, int]:
    """(fill, outline, outline_width, radius) pour un joueur -- voir la
    légende dans la docstring de module. `entry` : `RosterEntry`."""
    if entry.role is not None:
        fill = _ACTIVE_ROLE_COLORS.get(entry.role, (230, 230, 230))
        return fill, _ACTIVE_OUTLINE, _ACTIVE_OUTLINE_WIDTH, 11
    if entry.team_side == "scorer":
        return _SCORER_BACKGROUND_COLOR, _BACKGROUND_OUTLINE, _BACKGROUND_OUTLINE_WIDTH, 8
    return _OPPONENT_BACKGROUND_COLOR, _BACKGROUND_OUTLINE, _BACKGROUND_OUTLINE_WIDTH, 8


def _draw_legend(draw: ImageDraw.ImageDraw, font: ImageFont.ImageFont) -> None:
    """Légende visuelle discrète (Point 3) : un swatch + libellé par
    catégorie, coin haut-gauche, sous la barre de titre."""
    entries = [
        ("Actif (contour dore)", _ACTIVE_ROLE_COLORS["scorer"], _ACTIVE_OUTLINE, _ACTIVE_OUTLINE_WIDTH),
        ("Coequipier", _SCORER_BACKGROUND_COLOR, _BACKGROUND_OUTLINE, _BACKGROUND_OUTLINE_WIDTH),
        ("Adversaire", _OPPONENT_BACKGROUND_COLOR, _BACKGROUND_OUTLINE, _BACKGROUND_OUTLINE_WIDTH),
    ]
    x, y = 8, 36
    for label, fill, outline, outline_width in entries:
        draw.ellipse([x, y, x + 12, y + 12], fill=fill, outline=outline, width=outline_width)
        draw.text((x + 18, y - 1), label, fill="white", font=font)
        y += 18


def _draw_frame(t: float, frame, sequence, font: ImageFont.ImageFont, template_name: str) -> Image.Image:
    img, draw = _draw_pitch()

    for player_id, state in frame.players.items():
        entry = sequence.roster[player_id]
        fill, outline, outline_width, radius = _style_for(entry)
        px, py = _px(state.x, state.y)

        speed = (state.vx**2 + state.vy**2) ** 0.5
        if speed > 1e-6:
            scale = min(45.0, speed * 90.0)
            end_x = px + (state.vx / speed) * scale
            end_y = py - (state.vy / speed) * scale
            draw.line([(px, py), (end_x, end_y)], fill=(255, 255, 0), width=1)

        if state.is_ball_carrier:
            outline, outline_width = (255, 255, 255), 4
        draw.ellipse([px - radius, py - radius, px + radius, py + radius], fill=fill, outline=outline, width=outline_width)
        if entry.role:
            draw.text((px + 13, py - 8), f"{entry.role} #{entry.numero}", fill="white", font=font)

    draw.rectangle([0, 0, CANVAS_WIDTH_PX, 28], fill=(0, 0, 0))
    draw.text((8, 6), f"{template_name} — t={t:.1f}s — {len(frame.players)} joueurs", fill="white", font=font)
    _draw_legend(draw, font)
    return img


def run(template_name: str, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    scorer_lineup = _scorer_lineup()
    opponent_lineup = _opponent_lineup()
    event = _goal_event()
    start_positions = _start_positions(scorer_lineup)

    sequence = BUILDERS[template_name](event, scorer_lineup, start_positions)
    sequence = enrich_with_background(sequence, opponent_lineup)
    font = _font(13)

    frames: list[Image.Image] = []
    t = 0.0
    index = 0
    while t <= sequence.duration + 1e-9:
        frame = interpolate(sequence, t)
        img = _draw_frame(t, frame, sequence, font, template_name)
        img.save(output_dir / f"frame_{index:04d}.png")
        frames.append(img)
        index += 1
        t += _STEP_S

    gif_path = output_dir / f"{template_name}_22players.gif"
    frames[0].save(gif_path, save_all=True, append_images=frames[1:], duration=int(_STEP_S * 1000), loop=0)
    nb_active = sum(1 for e in sequence.roster.values() if e.role is not None)
    nb_scorer_bg = sum(1 for e in sequence.roster.values() if e.role is None and e.team_side == "scorer")
    nb_opponent_bg = sum(1 for e in sequence.roster.values() if e.team_side == "opponent")
    print(f"{index} frames PNG + GIF anime : {gif_path}")
    print(f"{nb_active} actifs, {nb_scorer_bg} coequipiers en soutien, {nb_opponent_bg} adversaires en repli")


if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else "contre_attaque"
    if name not in BUILDERS:
        raise SystemExit(f"Gabarit inconnu : {name!r} -- choisir parmi {sorted(BUILDERS)}")
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).resolve().parent / "output" / "background_preview" / name
    run(name, out)

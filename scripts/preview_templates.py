"""Audit visuel des 12 gabarits de but (`animation.templates`) -- scène
COMPLÈTE : 22 joueurs (les deux équipes, vraies positions de formation d'un
4-3-3 via `pitch_layout.place_starting_xi` + `spatial.placed_player_to_normalized`,
pas un placement synthétique arbitraire) + le ballon, échantillonnés à 3
instants (t=0%, 50%, 100% de la durée du gabarit) plus une bande temporelle
du ballon (sa trajectoire complète, échantillonnée à intervalles réguliers).
Objectif : décider visuellement lesquels des 12 gabarits sont réellement
redondants, sans se fier à l'impression donnée par un fixture synthétique
(voir la version précédente de ce script, dont l'audit avait montré des
gabarits qui SEMBLAIENT similaires uniquement à cause du placement arbitraire
des joueurs -- voir docs/simulation_physique_archi.md).

Usage :
    uv run python scripts/preview_templates.py [dossier_de_sortie]

Seule l'équipe qui marque (11 joueurs) est suivie par la `Sequence` réelle
(voir animation.types) -- l'équipe adverse (11 autres) n'est qu'un DÉCOR
statique à sa vraie position de formation, pour une scène crédible à 22
joueurs, jamais animée (le pipeline actuel ne modélise que l'équipe qui
marque, voir docs/simulation_physique_archi.md).

Effectif synthétique auto-contenu (même squad que tests/test_templates.py
pour l'équipe qui marque) -- aucune dépendance à data/joueurs.xlsx.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from ligue1sim.animation.spatial import PitchLayoutState, placed_player_to_normalized  # noqa: E402
from ligue1sim.animation.templates import BUILDERS, player_id_of  # noqa: E402
from ligue1sim.animation.types import Sequence  # noqa: E402
from ligue1sim.events import GoalEvent, PlayerMatchStat  # noqa: E402
from ligue1sim.lineup import Lineup  # noqa: E402
from ligue1sim.pitch_geometry import CANVAS_HEIGHT_PX, CANVAS_WIDTH_PX, PitchPoint, Zone, to_canvas_px, zone_of  # noqa: E402
from ligue1sim.pitch_layout import place_starting_xi  # noqa: E402
from ligue1sim.players import Player  # noqa: E402

_SCORER_ZONE = Zone(col=10, row=4)
_ASSIST_ZONE = Zone(col=7, row=3)

_ROLE_COLORS = {
    "scorer": (220, 40, 40),
    "assist": (40, 90, 220),
    "support1": (230, 150, 20),
    "support2": (150, 60, 200),
}
_HOME_COLOR = (220, 40, 40)  # équipe qui marque, rôles non actifs (voir _ROLE_COLORS pour les rôles actifs)
_AWAY_COLOR = (140, 150, 170)  # équipe adverse, purement décorative
_BALL_COLOR = (255, 255, 255)
_BALL_OUTLINE = (20, 20, 20)


def _player(poste: str, note: float, name: str, player_id: int) -> Player:
    return Player(
        prenom=name, nom="", nationalite="France", age=25, poste=poste, note=note,
        club="Test FC", championnat="TEST", id=player_id,
    )


def _four_three_three(club: str, id_offset: int) -> list[Player]:
    postes_names = [
        ("GK", "gk"), ("DC", "cb0"), ("DC", "cb1"), ("LB", "lb"), ("RB", "rb"),
        ("MDC", "mdc"), ("MC", "mc0"), ("MC", "mc1"), ("AG", "ag"), ("AD", "ad"), ("BU", "bu"),
    ]
    return [
        _player(poste, 70.0, name, id_offset + i) for i, (poste, name) in enumerate(postes_names)
    ]


def _home_lineup() -> Lineup:
    return Lineup(club_name="Home FC", formation="4-3-3", players=_four_three_three("Home FC", 1), rating=70.0)


def _away_lineup() -> Lineup:
    return Lineup(club_name="Away FC", formation="4-3-3", players=_four_three_three("Away FC", 101), rating=70.0)


def _placed(lineup: Lineup, *, attacking_up: bool) -> list:
    stats = [
        PlayerMatchStat(player_name=p.name, club_name=lineup.club_name, poste=p.poste, started=True)
        for p in lineup.players
    ]
    return place_starting_xi(stats, attacking_up=attacking_up)


def _start_positions(lineup: Lineup, placed: list) -> dict[int, PitchPoint]:
    by_name = {p.name: p for p in lineup.players}
    positions: dict[int, PitchPoint] = {}
    for pl in placed:
        player = by_name.get(pl.stat.player_name)
        if player is not None:
            positions[player_id_of(player)] = placed_player_to_normalized(pl, attacking_up=False)
    return positions


def _away_static_points(away_lineup: Lineup) -> list[PitchPoint]:
    """Positions décoratives de l'adversaire sur la scène PARTAGÉE avec
    l'équipe qui marque. `placed_player_to_normalized` est un référentiel
    RELATIF À L'ÉQUIPE (x=0 -> son propre but, voir spatial.py) -- deux
    équipes affichées côte à côte auraient donc chacune leur propre but à
    x=0 et se superposeraient exactement si on les composait telles
    quelles. Miroir sur x (1-x) pour l'adversaire seulement : son but reste
    à l'opposé de celui de l'équipe qui marque sur le canvas partagé. Le
    latéral (y) n'a pas besoin de miroir : `pitch_layout._screen_lane` gère
    déjà ce retournement en amont, `placed_player_to_normalized` le reprend
    tel quel (voir tests/test_spatial.py, y inchangé par attacking_up)."""
    placed_away = _placed(away_lineup, attacking_up=True)
    points = [placed_player_to_normalized(pl, attacking_up=True) for pl in placed_away]
    return [PitchPoint(x=1.0 - p.x, y=p.y) for p in points]


def _goal_event() -> GoalEvent:
    return GoalEvent(
        club_name="Home FC", scorer="bu", assist="mc0", minute=34, penalty=False,
        zone=_SCORER_ZONE, assist_zone=_ASSIST_ZONE,
    )


def _sample_players_at(sequence: Sequence, t: float) -> dict[int, tuple[float, float]]:
    """Interpolation linéaire entre les deux keyframes encadrant `t`
    (secondes) -- UNIQUEMENT pour cet outil d'aperçu offline (échantillonner
    à 0/50/100%), pas une réimplémentation de l'interpolation du rendu réel
    (qui vivra côté JS, voir invariant 7, docs/simulation_physique_archi.md)."""
    keyframes = sequence.keyframes
    if t <= keyframes[0].t:
        return dict(keyframes[0].players)
    if t >= keyframes[-1].t:
        return dict(keyframes[-1].players)
    for a, b in zip(keyframes, keyframes[1:]):
        if a.t <= t <= b.t:
            ratio = (t - a.t) / (b.t - a.t) if b.t > a.t else 0.0
            return {
                player_id: (ax + (bx - ax) * ratio, ay + (by - ay) * ratio)
                for player_id, ((ax, ay), (bx, by)) in (
                    (pid, (a.players[pid], b.players[pid])) for pid in a.players
                )
            }
    return dict(keyframes[-1].players)


def _sample_ball_at(sequence: Sequence, t: float) -> tuple[float, float, float]:
    keyframes = sequence.keyframes
    if t <= keyframes[0].t:
        b = keyframes[0].ball
        return b.x, b.y, b.z
    if t >= keyframes[-1].t:
        b = keyframes[-1].ball
        return b.x, b.y, b.z
    for a, b in zip(keyframes, keyframes[1:]):
        if a.t <= t <= b.t:
            ratio = (t - a.t) / (b.t - a.t) if b.t > a.t else 0.0
            return (
                a.ball.x + (b.ball.x - a.ball.x) * ratio,
                a.ball.y + (b.ball.y - a.ball.y) * ratio,
                a.ball.z + (b.ball.z - a.ball.z) * ratio,
            )
    return keyframes[-1].ball.x, keyframes[-1].ball.y, keyframes[-1].ball.z


def _px(point_or_xy) -> tuple[float, float]:
    if isinstance(point_or_xy, PitchPoint):
        return to_canvas_px(point_or_xy)
    x, y = point_or_xy
    return to_canvas_px(PitchPoint(x=x, y=y))


def _draw_pitch(width: int = CANVAS_WIDTH_PX, height: int = CANVAS_HEIGHT_PX) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGB", (width, height), (34, 120, 62))
    draw = ImageDraw.Draw(img)
    margin = max(4, int(20 * width / CANVAS_WIDTH_PX))
    draw.rectangle([margin, margin, width - margin, height - margin], outline="white", width=max(1, margin // 8))
    draw.line([(width // 2, margin), (width // 2, height - margin)], fill="white", width=max(1, margin // 12))
    box_w, box_h = int(width * 0.10), int(height * 0.42)
    draw.rectangle([margin, height // 2 - box_h // 2, margin + box_w, height // 2 + box_h // 2], outline="white", width=1)
    draw.rectangle([width - margin - box_w, height // 2 - box_h // 2, width - margin, height // 2 + box_h // 2], outline="white", width=1)
    return img, draw


def _font(size: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("arial.ttf", size)
    except OSError:
        return ImageFont.load_default()


def _draw_dot(draw: ImageDraw.ImageDraw, xy, color, radius: int, outline="black") -> None:
    px, py = _px(xy)
    draw.ellipse([px - radius, py - radius, px + radius, py + radius], fill=color, outline=outline, width=1)


def _snapshot(
    name: str,
    sequence: Sequence,
    lineup: Lineup,
    away_points: list[PitchPoint],
    t_ratio: float,
    font: ImageFont.ImageFont,
) -> Image.Image:
    img, draw = _draw_pitch()
    t = t_ratio * sequence.duration
    id_by_name = {p.name: p.id for p in lineup.players}
    roles = sequence.meta.get("roles", {})
    role_by_player_id = {id_by_name[player_name]: role for role, player_name in roles.items() if player_name in id_by_name}

    for point in away_points:
        _draw_dot(draw, point, _AWAY_COLOR, 8)

    players_now = _sample_players_at(sequence, t)
    for player_id, xy in players_now.items():
        role = role_by_player_id.get(player_id)
        color = _ROLE_COLORS.get(role, _HOME_COLOR) if role else _HOME_COLOR
        radius = 11 if role else 8
        _draw_dot(draw, xy, color, radius)
        if role:
            px, py = _px(xy)
            draw.text((px + 13, py - 8), role, fill="white", font=font)

    ball_x, ball_y, ball_z = _sample_ball_at(sequence, t)
    ball_radius = 8 + int(ball_z * 10)  # un ballon "en l'air" (z>0) dessiné plus gros -- pseudo-profondeur
    _draw_dot(draw, (ball_x, ball_y), _BALL_COLOR, ball_radius, outline=_BALL_OUTLINE)

    draw.rectangle([0, 0, CANVAS_WIDTH_PX, 28], fill=(0, 0, 0))
    draw.text((8, 6), f"{name} — t={t:.1f}s ({t_ratio * 100:.0f}%)", fill="white", font=font)
    return img


def _ball_strip(name: str, sequence: Sequence, font: ImageFont.ImageFont, nb_samples: int = 10) -> Image.Image:
    """Bande temporelle : `nb_samples` mini-terrains alignés horizontalement,
    chacun montrant la position du ballon à un instant régulièrement espacé
    sur toute la durée -- pour lire d'un coup d'œil toute la trajectoire du
    ballon, pas seulement 3 instants isolés."""
    tile_w, tile_h = 220, 150
    strip = Image.new("RGB", (tile_w * nb_samples, tile_h + 24), (10, 10, 10))
    draw_strip = ImageDraw.Draw(strip)
    draw_strip.text((6, 4), f"{name} — trajectoire du ballon", fill="white", font=font)

    for i in range(nb_samples):
        t_ratio = i / (nb_samples - 1) if nb_samples > 1 else 0.0
        t = t_ratio * sequence.duration
        tile, tile_draw = _draw_pitch(tile_w, tile_h)
        ball_x, ball_y, ball_z = _sample_ball_at(sequence, t)
        px, py = to_canvas_px(PitchPoint(x=ball_x, y=ball_y), canvas_width=tile_w, canvas_height=tile_h)
        radius = 5 + int(ball_z * 6)
        tile_draw.ellipse([px - radius, py - radius, px + radius, py + radius], fill=_BALL_COLOR, outline=_BALL_OUTLINE, width=1)
        tile_draw.text((4, tile_h - 14), f"t={t:.1f}s", fill="white", font=font)
        strip.paste(tile, (i * tile_w, 24))

    return strip


def _count_passes(sequence: Sequence) -> int:
    passes = 0
    last_owner = None
    for kf in sequence.keyframes:
        owner = kf.ball.owner_id
        if owner is not None:
            if last_owner is not None and owner != last_owner:
                passes += 1
            last_owner = owner
    return passes


def run(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    home_lineup = _home_lineup()
    away_lineup = _away_lineup()
    event = _goal_event()

    home_placed = _placed(home_lineup, attacking_up=False)
    start_positions = _start_positions(home_lineup, home_placed)
    away_points = _away_static_points(away_lineup)

    small_font = _font(14)
    print(f"{'gabarit':25s} {'duree':>6s} {'kf':>3s} {'roles':>6s} {'passes':>6s}  {'depart':>10s}  {'tir':>10s}")

    montage_tiles: list[Image.Image] = []
    for name in sorted(BUILDERS):
        sequence = BUILDERS[name](event, home_lineup, start_positions)
        nb_roles = len(sequence.meta.get("roles", {}))

        for t_ratio, label in ((0.0, "t0"), (0.5, "t50"), (1.0, "t100")):
            img = _snapshot(name, sequence, home_lineup, away_points, t_ratio, small_font)
            img.save(output_dir / f"{name}_{label}.png")
            if label == "t100":
                montage_tiles.append(img)

        strip = _ball_strip(name, sequence, small_font)
        strip.save(output_dir / f"{name}_ball_strip.png")

        start_zone = zone_of(sequence.keyframes[0].ball.x, sequence.keyframes[0].ball.y)
        shot_zone = zone_of(sequence.keyframes[-1].ball.x, sequence.keyframes[-1].ball.y)
        print(
            f"{name:25s} {sequence.duration:5.1f}s {len(sequence.keyframes):3d} {nb_roles:6d} {_count_passes(sequence):6d}  "
            f"{str(start_zone):>10s}  {str(shot_zone):>10s}"
        )

    cols, rows = 4, 3
    scale = 0.4
    tile_w, tile_h = int(CANVAS_WIDTH_PX * scale), int(CANVAS_HEIGHT_PX * scale)
    montage = Image.new("RGB", (tile_w * cols, tile_h * rows), (10, 10, 10))
    for i, tile in enumerate(montage_tiles):
        resized = tile.resize((tile_w, tile_h))
        montage.paste(resized, ((i % cols) * tile_w, (i // cols) * tile_h))
    montage_path = output_dir / "montage_t100_12_gabarits.png"
    montage.save(montage_path)
    print(f"\n{len(montage_tiles) * 4} images individuelles + montage : {montage_path}")


if __name__ == "__main__":
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent / "output" / "template_previews"
    run(out)

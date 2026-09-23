"""Genere un JSON de sequence pour un gabarit et l'injecte dans une copie de
`render/canvas.html`, produisant `render/canvas_preview.html` -- ouvrable
directement dans un navigateur, sans Streamlit (brief "canvas vertical
slice", 23/09/2026, Tache 3.2).

Le brief demande le gabarit "frappe_enroulee" -- inexistant dans
`animation.templates.BUILDERS` (12 gabarits reels). "decalage_enroulee" est
le seul nom apparente ("frappe enroulee" decrit la conclusion en enroule de
ce gabarit, voir templates.py) -- substitution documentee dans le retour de
tache, pas un gabarit invente. Meme pipeline que
`scripts/preview_motion.py` (lineup/event synthetiques, `enrich_with_background`
pour les 22 joueurs) pour rester coherent avec les scripts de preview
existants.

Extension (brief "vertical slice validation", Tache 4, 23/09/2026) :
`--template` accepte aussi "corner" et "contre_attaque" (voir
docs/next_step_canvas.md pour les notes d'iteration sur ces 2 gabarits).

Usage :
    uv run python scripts/render_preview.py [--template NOM] [--fps N]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from ligue1sim.animation.motion import interpolate  # noqa: E402
from ligue1sim.animation.sequence_generator import enrich_with_background  # noqa: E402
from ligue1sim.animation.serialize import frame_sequence_to_json  # noqa: E402
from ligue1sim.animation.templates import BUILDERS  # noqa: E402
from ligue1sim.events import GoalEvent  # noqa: E402
from ligue1sim.kits import match_kit_colors  # noqa: E402
from ligue1sim.lineup import Lineup  # noqa: E402
from ligue1sim.pitch_geometry import PitchPoint, Zone  # noqa: E402
from ligue1sim.players import Player  # noqa: E402

_TEMPLATE_NAME = "decalage_enroulee"
_SCORER_CLUB = "Paris Saint-Germain"
_OPPONENT_CLUB = "AS Monaco"
_SCORER_ZONE = Zone(col=10, row=4)
_ASSIST_ZONE = Zone(col=7, row=3)
_DEFAULT_FPS = 30

_CANVAS_HTML = Path(__file__).resolve().parent.parent / "render" / "canvas.html"
_OUTPUT_HTML = Path(__file__).resolve().parent.parent / "render" / "canvas_preview.html"
_PLACEHOLDER = "/*__SEQUENCE_JSON__*/null"


def _player(poste: str, name: str, player_id: int) -> Player:
    return Player(prenom=name, nom="", nationalite="France", age=25, poste=poste, note=70.0, club="C", championnat="T", id=player_id)


def _four_three_three(id_offset: int) -> list[Player]:
    postes_names = [
        ("GK", "gk"), ("DC", "cb0"), ("DC", "cb1"), ("LB", "lb"), ("RB", "rb"),
        ("MDC", "mdc"), ("MC", "mc0"), ("MC", "mc1"), ("AG", "ag"), ("AD", "ad"), ("BU", "bu"),
    ]
    return [_player(poste, name, id_offset + i) for i, (poste, name) in enumerate(postes_names)]


def _scorer_lineup() -> Lineup:
    return Lineup(club_name=_SCORER_CLUB, formation="4-3-3", players=_four_three_three(1), rating=70.0)


def _opponent_lineup() -> Lineup:
    return Lineup(club_name=_OPPONENT_CLUB, formation="4-3-3", players=_four_three_three(101), rating=65.0)


def _goal_event() -> GoalEvent:
    return GoalEvent(club_name=_SCORER_CLUB, scorer="bu", assist="mc0", minute=34, zone=_SCORER_ZONE, assist_zone=_ASSIST_ZONE)


def build_sequence(template_name: str = _TEMPLATE_NAME):
    lineup = _scorer_lineup()
    event = _goal_event()
    start_positions = {p.id: PitchPoint(x=0.15 + 0.06 * i, y=0.1 + 0.07 * i) for i, p in enumerate(lineup.players)}
    sequence = BUILDERS[template_name](event, lineup, start_positions)
    return enrich_with_background(sequence, _opponent_lineup())


def build_json(*, template_name: str = _TEMPLATE_NAME, fps: int = _DEFAULT_FPS) -> str:
    sequence = build_sequence(template_name)

    step = 1.0 / fps
    frames = []
    t = 0.0
    while t <= sequence.duration + 1e-9:
        frames.append(interpolate(sequence, t))
        t += step

    (scorer_fill, scorer_outline), (opp_fill, opp_outline) = match_kit_colors(_SCORER_CLUB, _OPPONENT_CLUB)
    roster = {
        str(player_id): {"team": entry.team_side, "numero": entry.numero, "active": entry.role is not None}
        for player_id, entry in sequence.roster.items()
    }
    metadata = {
        "duration": sequence.duration,
        "fps_target": fps,
        "template": template_name,
        "teams": {
            "scorer": {"name": _SCORER_CLUB, "color_fill": scorer_fill, "color_outline": scorer_outline},
            "opponent": {"name": _OPPONENT_CLUB, "color_fill": opp_fill, "color_outline": opp_outline},
        },
        "roster": roster,
    }
    return frame_sequence_to_json(frames, metadata)


def run(*, template_name: str = _TEMPLATE_NAME, fps: int) -> Path:
    sequence_json = build_json(template_name=template_name, fps=fps)
    html = _CANVAS_HTML.read_text(encoding="utf-8")
    if _PLACEHOLDER not in html:
        raise ValueError(f"placeholder {_PLACEHOLDER!r} introuvable dans {_CANVAS_HTML} -- injection impossible")
    html = html.replace(_PLACEHOLDER, sequence_json)
    _OUTPUT_HTML.write_text(html, encoding="utf-8")
    return _OUTPUT_HTML


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--template", default=_TEMPLATE_NAME, help=f"nom du gabarit, animation.templates.BUILDERS (defaut {_TEMPLATE_NAME!r})")
    parser.add_argument("--fps", type=int, default=_DEFAULT_FPS, help=f"images par seconde generees (defaut {_DEFAULT_FPS})")
    args = parser.parse_args()

    if args.template not in BUILDERS:
        raise SystemExit(f"Gabarit inconnu : {args.template!r} -- choisir parmi {sorted(BUILDERS)}")
    output_path = run(template_name=args.template, fps=args.fps)
    print(f"HTML autonome genere ({args.template}) : {output_path}")

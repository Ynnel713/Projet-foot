"""Preview Streamlit autonome du rendu canvas (brief "canvas vertical
slice", 23/09/2026, Tache 4) -- charge un gabarit via le pipeline existant
(`templates.BUILDERS` + `sequence_generator.enrich_with_background`, meme
principe que `scripts/preview_motion.py`), le serialise en JSON (Tache 2,
`animation.serialize.frame_sequence_to_json`), injecte `render/canvas.html`
et l'affiche via `st.components.v1.html`.

Fichier AUTONOME, volontairement NON ajoute a `Lancer l'appli.bat` (brief,
4.2) -- le proprietaire le lance manuellement :

    uv run streamlit run apps/streamlit_preview.py --server.port 8600

(voir docs/next_step_canvas.md pour la commande exacte documentee). Ne
touche ni a `app.py` (l'app Streamlit principale), ni a `ui/` (la PWA React).

Le premier brief demandait le gabarit "frappe_enroulee" -- inexistant dans
`animation.templates.BUILDERS` (12 gabarits reels). "decalage_enroulee" est
le seul nom apparente ("frappe enroulee" decrit la conclusion en enroule de
ce gabarit) -- substitution confirmee comme correcte par Olivier (erratum
du brief du 23/09/2026 "vertical slice validation"), pas un gabarit
invente.

Extension (brief "vertical slice validation", Tache 4, 23/09/2026, option
A) : sélecteur `corner`/`contre_attaque` en plus de `decalage_enroulee` --
voir docs/next_step_canvas.md pour les notes d'iteration sur ces 2 gabarits
supplementaires.

Lineup/event synthetiques dupliques depuis `scripts/render_preview.py`
(meme motif deja repete dans `scripts/preview_motion.py`/
`tests/test_serialize.py`) plutot qu'importes depuis `scripts/` : garde ce
fichier autonome, sans dependance inter-dossiers fragile."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import streamlit as st  # noqa: E402

from ligue1sim.animation.motion import interpolate  # noqa: E402
from ligue1sim.animation.sequence_generator import enrich_with_background  # noqa: E402
from ligue1sim.animation.serialize import frame_sequence_to_json  # noqa: E402
from ligue1sim.animation.templates import BUILDERS  # noqa: E402
from ligue1sim.events import GoalEvent  # noqa: E402
from ligue1sim.kits import match_kit_colors  # noqa: E402
from ligue1sim.lineup import Lineup  # noqa: E402
from ligue1sim.pitch_geometry import PitchPoint, Zone  # noqa: E402
from ligue1sim.players import Player  # noqa: E402

_AVAILABLE_TEMPLATES = ("decalage_enroulee", "corner", "contre_attaque")
_DEFAULT_TEMPLATE = "decalage_enroulee"
_SCORER_CLUB = "Paris Saint-Germain"
_OPPONENT_CLUB = "AS Monaco"
_SCORER_ZONE = Zone(col=10, row=4)
_ASSIST_ZONE = Zone(col=7, row=3)
_FPS = 30

_CANVAS_HTML = Path(__file__).resolve().parent.parent / "render" / "canvas.html"
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


@st.cache_data
def build_sequence_json(template_name: str, *, fps: int = _FPS) -> str:
    # `template_name` fait partie de la clé de cache de st.cache_data (tous
    # les arguments de la fonction en font partie par defaut) -- un
    # changement de selection regenere donc bien le JSON, pas de cache
    # agressif qui bloquerait sur l'ancien gabarit (brief, Tache 4.2).
    lineup = _scorer_lineup()
    event = _goal_event()
    start_positions = {p.id: PitchPoint(x=0.15 + 0.06 * i, y=0.1 + 0.07 * i) for i, p in enumerate(lineup.players)}
    sequence = BUILDERS[template_name](event, lineup, start_positions)
    sequence = enrich_with_background(sequence, _opponent_lineup())

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


st.set_page_config(page_title="Canvas preview", layout="wide")
st.title("Rendu canvas -- vertical slice")

template_name = st.selectbox(
    "Gabarit", _AVAILABLE_TEMPLATES, index=_AVAILABLE_TEMPLATES.index(_DEFAULT_TEMPLATE)
)
st.caption(
    f"Gabarit : {template_name} -- \"frappe_enroulee\" (demande initiale du premier brief) n'existe pas dans "
    "animation.templates.BUILDERS, voir docs/next_step_canvas.md pour la substitution documentee "
    "(confirmee correcte)."
)

sequence_json = build_sequence_json(template_name)
html = _CANVAS_HTML.read_text(encoding="utf-8")
if _PLACEHOLDER not in html:
    st.error(f"placeholder {_PLACEHOLDER!r} introuvable dans {_CANVAS_HTML}")
else:
    html = html.replace(_PLACEHOLDER, sequence_json)
    st.components.v1.html(html, height=880, scrolling=False)

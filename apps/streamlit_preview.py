"""Preview Streamlit autonome du rendu canvas (brief "canvas vertical
slice", 23/09/2026, Tache 4, puis "canvas player", meme date, Tache 5) --
deux modes :

- `mode = "gabarit"` (existant, INCHANGE) : charge un gabarit isole via le
  pipeline existant (`templates.BUILDERS` + `sequence_generator.
  enrich_with_background`, meme principe que `scripts/preview_motion.py`),
  le serialise en JSON (`animation.serialize.frame_sequence_to_json`).
- `mode = "match"` (nouveau, Tache 5) : simule un match deterministe via le
  pipeline existant, construit sa `Timeline` (`engine.narrative.build_timeline`)
  puis ses clips (`engine.narrative_player.build_clips`, `max_occasions=4`),
  serialise en JSON (`engine.narrative_player.clips_to_json`).

Les deux modes injectent `render/canvas.html` (qui detecte lui-meme le mode
gabarit-isole vs player selon la forme du JSON, voir Tache 4.1) et l'affichent
via `st.components.v1.html`.

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
fichier autonome, sans dependance inter-dossiers fragile. Meme motif pour le
mode `match` : squad/clubs synthetiques dupliques depuis
`scripts/render_player_preview.py` (meme raison, autonomie du fichier)."""

from __future__ import annotations

import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "engine"))

import numpy as np  # noqa: E402
import streamlit as st  # noqa: E402

from ligue1sim.animation.motion import interpolate  # noqa: E402
from ligue1sim.animation.sequence_generator import enrich_with_background  # noqa: E402
from ligue1sim.animation.serialize import frame_sequence_to_json  # noqa: E402
from ligue1sim.animation.templates import BUILDERS  # noqa: E402
from ligue1sim.clubs import Club  # noqa: E402
from ligue1sim.events import GoalEvent  # noqa: E402
from ligue1sim.kits import match_kit_colors  # noqa: E402
from ligue1sim.lineup import Lineup, pick_best_formation  # noqa: E402
from ligue1sim.pitch_geometry import PitchPoint, Zone  # noqa: E402
from ligue1sim.players import Player  # noqa: E402
from ligue1sim.schedule import Match  # noqa: E402
from ligue1sim.simulation import LeagueContext, simulate_match  # noqa: E402

from narrative import build_timeline, match_result_from  # noqa: E402
from narrative_player import build_clips, clips_to_json  # noqa: E402

_AVAILABLE_TEMPLATES = ("decalage_enroulee", "corner", "contre_attaque")
_DEFAULT_TEMPLATE = "decalage_enroulee"
_SCORER_CLUB = "Paris Saint-Germain"
_OPPONENT_CLUB = "AS Monaco"
_SCORER_ZONE = Zone(col=10, row=4)
_ASSIST_ZONE = Zone(col=7, row=3)
_FPS = 30

# Mode "match" (Tache 5.3) -- match fixe, deterministe (seed fixe + memes
# clubs synthetiques que le mode "gabarit" ci-dessus, note volontairement
# differente pour un ecart de forces credible). PAS le "premier match de la
# ligue 1 generee" suggere en exemple par le brief : ce fichier n'a jamais
# dependu de `season.py`/`schedule.py` (deja le cas pour le mode "gabarit"
# existant, memes clubs synthetiques) -- brancher une vraie journee de
# championnat est hors scope de ce premier jet, non demande explicitement
# ailleurs que dans un exemple entre parentheses du brief.
_MATCH_HOME_CLUB = _SCORER_CLUB
_MATCH_AWAY_CLUB = _OPPONENT_CLUB
_MATCH_HOME_NOTE = 80.0
_MATCH_AWAY_NOTE = 70.0
_MATCH_SEED = 7  # voir scripts/render_player_preview.py -- meme seed, meme profil (1 occasion puis 2 buts sur les 4 premiers clips), reutilisee ici pour la coherence entre le script de capture et l'appli
_MATCH_MAX_OCCASIONS = 4

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


def _match_player(poste: str, note: float, name: str) -> Player:
    return Player(prenom=name, nom="", nationalite="France", age=25, poste=poste, note=note, club="Test FC", championnat="TEST")


def _match_squad(club_name: str, note: float) -> list[Player]:
    squad = [_match_player("GK", note, f"{club_name}_gk{i}") for i in range(2)]
    squad += [_match_player("DC", note, f"{club_name}_cb{i}") for i in range(4)]
    squad += [_match_player("LB", note, f"{club_name}_lb{i}") for i in range(2)]
    squad += [_match_player("RB", note, f"{club_name}_rb{i}") for i in range(2)]
    squad += [_match_player("MC", note, f"{club_name}_cm{i}") for i in range(4)]
    squad += [_match_player("MOC", note, f"{club_name}_am{i}") for i in range(2)]
    squad += [_match_player("AG", note, f"{club_name}_lw{i}") for i in range(2)]
    squad += [_match_player("AD", note, f"{club_name}_rw{i}") for i in range(2)]
    squad += [_match_player("BU", note, f"{club_name}_cf{i}") for i in range(4)]
    return squad


@st.cache_data
def build_match_clips_json(seed: int, max_occasions: int) -> tuple[str, str, str]:
    """Simule le match fixe (Tache 5.3), construit ses clips et les
    serialise -- `seed` fait partie de la clé de cache (voir
    `build_sequence_json` ci-dessus pour le meme principe). Retourne
    `(clips_json, home_team, away_team)` -- les deux derniers pour l'affichage
    Streamlit (nombre de clips, score final), pas pour le JSON lui-meme."""
    random.seed(seed)
    np.random.seed(seed)

    home = Club(name=_MATCH_HOME_CLUB, players=_match_squad("home", _MATCH_HOME_NOTE))
    away = Club(name=_MATCH_AWAY_CLUB, players=_match_squad("away", _MATCH_AWAY_NOTE))
    context = LeagueContext.from_clubs([home, away])
    home_lineup, away_lineup = pick_best_formation(home), pick_best_formation(away)

    home_goals, away_goals, events = simulate_match(home, away, context)
    while events is None:  # repli deterministe -- meme principe que _simulate_n des tests, voir docstring
        home_goals, away_goals, events = simulate_match(home, away, context)
    match = Match(home=home.name, away=away.name, home_goals=home_goals, away_goals=away_goals, events=events)
    result = match_result_from(match, events, home_lineup, away_lineup, date=str(seed))

    timeline = build_timeline(result)
    clips = build_clips(timeline, max_occasions=max_occasions)
    return clips_to_json(clips, timeline), timeline.home_team, timeline.away_team


st.set_page_config(page_title="Canvas preview", layout="wide")
st.title("Rendu canvas -- vertical slice / lecteur de clips")

mode = st.radio("Mode", ("gabarit", "match"), horizontal=True)

if mode == "gabarit":
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
else:
    clips_json, home_team, away_team = build_match_clips_json(_MATCH_SEED, _MATCH_MAX_OCCASIONS)
    st.caption(
        f"Match fixe et deterministe (Tache 5.3) : {home_team} vs {away_team}, seed={_MATCH_SEED}, "
        f"{_MATCH_MAX_OCCASIONS} premiers clips construisibles (voir engine/narrative_player.build_clips "
        "pour la limite connue sur un protagoniste remplacant)."
    )
    html = _CANVAS_HTML.read_text(encoding="utf-8")
    if _PLACEHOLDER not in html:
        st.error(f"placeholder {_PLACEHOLDER!r} introuvable dans {_CANVAS_HTML}")
    else:
        html = html.replace(_PLACEHOLDER, clips_json)
        # Plus haut que le mode gabarit (880) : la barre de progression + les
        # boutons de navigation du mode player (Tache 4) ajoutent de la
        # hauteur sous le canvas.
        st.components.v1.html(html, height=980, scrolling=False)

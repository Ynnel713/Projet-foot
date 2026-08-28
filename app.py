"""Interface Streamlit : simulateur de saison multi-championnats + Compétition Perso."""

from __future__ import annotations

import base64
import textwrap
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd
import streamlit as st

from ligue1sim.champions_league import start_champions_league
from ligue1sim.clubs import Club, ClubOption, list_championnats, load_all_clubs, load_clubs
from ligue1sim.clubs import clear_cache as clear_clubs_cache
from ligue1sim.custom_competition import (
    CompetitionFormat,
    CustomCompetition,
    clear_custom_competition,
    get_custom_competition,
    start_custom_competition,
    store_custom_competition,
)
from ligue1sim.coaches import coach_name
from ligue1sim.coaches import clear_cache as clear_coaches_cache
from ligue1sim.lineup import clear_cache as clear_lineup_cache
from ligue1sim.nations import CHAMPIONNAT_LABEL as NATIONS_CHAMPIONNAT_LABEL
from ligue1sim.nations import load_national_teams
from ligue1sim.nations import clear_cache as clear_nations_cache
from ligue1sim.events import AvailabilityTracker, MatchEvents, PlayerMatchStat, compute_leaderboards
from ligue1sim.groups import QUALIFIERS_PER_GROUP
from ligue1sim.kits import match_kit_colors, primary_color
from ligue1sim.knockout import Round
from ligue1sim.pitch_layout import PlacedPlayer, actual_formation_label, place_starting_xi
from ligue1sim.players import Player
from ligue1sim.schedule import Match
from ligue1sim.season import (
    CLUBS_PATH,
    Season,
    get_season,
    get_selected_championnat,
    go_to_home,
    reset_season,
    select_championnat,
)

st.set_page_config(page_title="Simulafoot", page_icon="⚽", layout="wide")

_HOME_SPLASH_PATH = Path(__file__).parent / "assets" / "backgrounds" / "home-splash.jpg"

# Drapeau du pays représentatif de chaque championnat (remplace les anciens
# logos PNG de assets/logos/ -- plus léger visuellement, pas de question de
# droit d'usage de logo de compétition).
_CHAMPIONNAT_FLAG = {
    "Ligue 1": "🇫🇷",
    "Premier League": "🇬🇧",
    "LaLiga": "🇪🇸",
    "Bundesliga": "🇩🇪",
    "Serie A": "🇮🇹",
    "Liga Portugal": "🇵🇹",
    "Jupiler Pro League": "🇧🇪",
    "Eredivisie": "🇳🇱",
}
_CHAMPIONS_LEAGUE_ICON = "⭐"
_NATIONS_ICON = "🌍"
_PERSO_ICON = "🏆"

_CLUB_SELECTION_KEY = "perso_selected_clubs"
_CLUB_TABLE_VERSION_KEY = "perso_table_version"
_PERSO_CLUB_SOURCE_KEY = "perso_club_source"
_OPEN_MATCH_KEY = "open_match_detail"
# Liste des matchs de la journée/manche où le match ouvert a été trouvé, et
# son indice dans cette liste -- permet la navigation "Match précédent" /
# "Match suivant" sans avoir à retrouver la journée depuis l'écran de détail
# (voir `_render_match_rows`/`render_match_detail_screen`).
_OPEN_MATCH_LIST_KEY = "open_match_list"
_OPEN_MATCH_INDEX_KEY = "open_match_index"
_OPEN_CLUB_KEY = "open_club_detail"

_WIZARD_KEYS = [
    "perso_wizard_step",
    "perso_format",
    "perso_team_count",
    "perso_legs",
    _CLUB_SELECTION_KEY,
    _CLUB_TABLE_VERSION_KEY,
    _PERSO_CLUB_SOURCE_KEY,
]

_FORMAT_CHOICES = [
    (CompetitionFormat.LEAGUE, "Championnat pur", "Toutes les équipes s'affrontent, classement final."),
    (CompetitionFormat.KNOCKOUT, "Élimination directe", "Tableau à élimination directe jusqu'à la finale."),
    (
        CompetitionFormat.HYBRID,
        "Championnat + élimination",
        "Poules de 4 façon Coupe du Monde, les 2 premiers de chaque poule passent en élimination directe.",
    ),
]

_LEGS_LABELS = {1: "Match simple", 2: "Aller-retour", 4: "Double aller-retour"}

_ROUND_NAMES = {
    1: "Finale",
    2: "Demi-finales",
    4: "Quarts de finale",
    8: "Huitièmes de finale",
    16: "Seizièmes de finale",
    32: "Trente-deuxièmes de finale",
}


def _reset_wizard() -> None:
    for key in _WIZARD_KEYS:
        st.session_state.pop(key, None)


# --- Écran d'accueil ---------------------------------------------------

# Hauteur (en vh) de la zone "hero" (wordmark + accroche) au-dessus du fond
# de stade : pilote à la fois le dégradé d'assombrissement de l'image et la
# hauteur minimale du bloc hero, pour que les deux restent synchronisés.
_HOME_HERO_HEIGHT_VH = 42


def _home_css() -> str:
    """CSS complet de l'écran d'accueil : polices, jetons de couleur, fond de
    stade, wordmark, sections et système de tuiles rondes cliquables. Scopé à
    cet écran uniquement (pas d'impact sur le reste de l'appli)."""
    splash_b64 = base64.b64encode(_HOME_SPLASH_PATH.read_bytes()).decode() if _HOME_SPLASH_PATH.exists() else ""
    background = (
        f"""
        [data-testid="stAppViewContainer"] {{
            background-image:
                linear-gradient(to bottom, rgba(9, 12, 18, 0.32) 0%, rgba(9, 12, 18, 0.74) {_HOME_HERO_HEIGHT_VH - 18}vh, var(--sf-bg) {_HOME_HERO_HEIGHT_VH}vh),
                url("data:image/jpeg;base64,{splash_b64}");
            background-repeat: no-repeat;
            background-size: cover;
            background-position: top center;
            background-attachment: fixed;
        }}
        """
        if splash_b64
        else ""
    )
    return textwrap.dedent(f"""\
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Big+Shoulders+Display:wght@700;800&family=Manrope:wght@400;500;600;700&display=swap');
    :root {{
        --sf-bg: #090d14;
        --sf-surface: rgba(24, 30, 44, 0.55);
        --sf-surface-hover: rgba(36, 45, 62, 0.80);
        --sf-border: rgba(255, 255, 255, 0.10);
        --sf-text: #F4F6F9;
        --sf-text-muted: rgba(244, 246, 249, 0.58);
        --sf-accent: #FF4B4B;
        --sf-accent-soft: rgba(255, 75, 75, 0.38);
        --sf-gold-soft: rgba(217, 180, 94, 0.5);
    }}
    {background}

    .sf-hero {{
        min-height: {_HOME_HERO_HEIGHT_VH}vh;
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        text-align: center;
        padding: 2rem 1rem 1.4rem;
    }}
    .sf-wordmark {{
        font-family: "Big Shoulders Display", sans-serif;
        font-weight: 800;
        font-size: clamp(2.6rem, 6vw, 4.6rem);
        letter-spacing: 0.05em;
        text-transform: uppercase;
        color: var(--sf-text);
        line-height: 1;
        margin: 0;
        text-shadow: 0 2px 28px rgba(0, 0, 0, 0.6);
    }}
    .sf-wordmark-rule {{
        display: flex; align-items: center; justify-content: center; gap: 14px;
        width: min(220px, 55%);
        margin: 1.1rem auto 1.2rem;
    }}
    .sf-wordmark-rule::before, .sf-wordmark-rule::after {{
        content: ""; flex: 1; height: 1px;
        background: linear-gradient(to right, transparent, rgba(255, 255, 255, 0.35), transparent);
    }}
    .sf-kickoff-dot {{
        width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0;
        background: var(--sf-accent);
        box-shadow: 0 0 14px 3px var(--sf-accent-soft);
    }}
    .sf-tagline {{
        font-family: "Manrope", sans-serif;
        font-weight: 500;
        font-size: 1rem;
        color: var(--sf-text-muted);
        text-shadow: 0 1px 14px rgba(0, 0, 0, 0.55);
        margin: 0;
    }}

    div[class*="st-key-sf_section_"] {{
        max-width: 1120px;
        margin: 2.6rem auto 0;
        padding: 0 1rem;
    }}
    .sf-section-title {{
        font-family: "Big Shoulders Display", sans-serif;
        font-weight: 700;
        font-size: 1.05rem;
        letter-spacing: 0.16em;
        text-transform: uppercase;
        color: var(--sf-text-muted);
        display: flex; align-items: center; gap: 0.65rem;
        margin: 0 0 1.4rem;
    }}
    .sf-section-title::before {{
        content: ""; width: 3px; height: 1.05em; border-radius: 2px;
        background: var(--sf-accent);
        display: inline-block;
    }}

    div[class*="st-key-sf_grid_leagues"] {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(92px, 1fr));
        gap: 1.7rem 0.8rem;
    }}
    div[class*="st-key-sf_grid_intl"] {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
        max-width: 620px;
        gap: 1.7rem 1.4rem;
    }}

    div[class*="st-key-sf_tile_"] {{ position: relative; width: 100%; }}
    div[class*="st-key-sf_btn_"] {{ position: static !important; width: 100% !important; }}
    div[class*="st-key-sf_btn_"] button {{
        position: absolute !important; inset: 0 !important; width: 100% !important; height: 100% !important;
        opacity: 0 !important; z-index: 3; cursor: pointer; border-radius: 16px;
    }}
    div[class*="st-key-sf_tile_"]:has(button:focus-visible) .sf-tile-badge,
    div[class*="st-key-sf_banner_"]:has(button:focus-visible) .sf-banner {{
        outline: 2px solid var(--sf-accent); outline-offset: 3px;
    }}

    .sf-tile {{
        display: flex; flex-direction: column; align-items: center; gap: 0.6rem;
        text-align: center; pointer-events: none;
    }}
    .sf-tile-badge {{
        position: relative;
        width: 74px; height: 74px;
        border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 2rem;
        background: var(--sf-surface);
        border: 1px solid var(--sf-border);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        transition: background 0.18s ease, transform 0.18s ease;
    }}
    .sf-tile-badge::after {{
        content: ""; position: absolute; inset: -16px; border-radius: 50%; z-index: -1;
        background: radial-gradient(circle, rgba(255, 255, 255, 0.12), transparent 70%);
        opacity: 0.45;
        transition: opacity 0.18s ease;
    }}
    .sf-tile-badge--gold::after {{
        background: radial-gradient(circle, var(--sf-gold-soft), transparent 70%);
        opacity: 0.55;
    }}
    div[class*="st-key-sf_tile_"]:hover .sf-tile-badge {{
        background: var(--sf-surface-hover);
        transform: translateY(-3px);
    }}
    div[class*="st-key-sf_tile_"]:hover .sf-tile-badge::after {{ opacity: 0.85; }}
    .sf-tile-name {{
        font-family: "Manrope", sans-serif; font-weight: 600; font-size: 0.84rem;
        color: var(--sf-text); line-height: 1.15;
    }}
    .sf-tile-meta {{
        font-family: "Manrope", sans-serif; font-size: 0.7rem; color: var(--sf-text-muted);
    }}

    div[class*="st-key-sf_banner_"] {{ position: relative; width: 100%; max-width: 640px; }}
    .sf-banner {{
        display: flex; align-items: center; gap: 1.1rem;
        padding: 1.15rem 1.4rem;
        border-radius: 18px;
        background: var(--sf-surface);
        border: 1px solid var(--sf-border);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        pointer-events: none;
        transition: background 0.18s ease;
    }}
    div[class*="st-key-sf_banner_"]:hover .sf-banner {{ background: var(--sf-surface-hover); }}
    .sf-banner-icon {{ font-size: 1.8rem; flex-shrink: 0; }}
    .sf-banner-text {{ text-align: left; flex: 1; }}
    .sf-banner-title {{
        font-family: "Manrope", sans-serif; font-weight: 700; font-size: 0.98rem; color: var(--sf-text);
    }}
    .sf-banner-desc {{
        font-family: "Manrope", sans-serif; font-size: 0.8rem; color: var(--sf-text-muted); margin-top: 0.2rem;
    }}
    .sf-banner-arrow {{ font-size: 1.2rem; color: var(--sf-text-muted); flex-shrink: 0; }}
    </style>
    """)


def _render_tile(*, key: str, icon: str, name: str, meta: str | None = None, gold: bool = False) -> bool:
    """Tuile ronde entièrement cliquable (icône + nom + méta optionnelle,
    aucun bouton "Jouer" séparé) : un vrai `st.button` invisible est
    superposé pile sur la tuile visuelle via CSS (voir `_home_css`), donc le
    clic fonctionne sur toute la surface tout en restant un widget Streamlit
    natif (accessible au clavier, pas de bidouillage fragile)."""
    badge_class = "sf-tile-badge sf-tile-badge--gold" if gold else "sf-tile-badge"
    meta_html = f'<div class="sf-tile-meta">{meta}</div>' if meta else ""
    with st.container(key=f"sf_tile_{key}"):
        st.markdown(
            f'<div class="sf-tile"><div class="{badge_class}">{icon}</div>'
            f'<div class="sf-tile-name">{name}</div>{meta_html}</div>',
            unsafe_allow_html=True,
        )
        clicked = st.button("", key=f"sf_btn_{key}")
    return clicked


def _render_banner(*, key: str, icon: str, title: str, description: str) -> bool:
    """Bannière large entièrement cliquable, même principe que `_render_tile`
    -- pour une entrée qui ouvre un parcours (assistant) plutôt qu'une
    compétition prête à jouer."""
    with st.container(key=f"sf_banner_{key}"):
        st.markdown(
            f'<div class="sf-banner"><div class="sf-banner-icon">{icon}</div>'
            f'<div class="sf-banner-text"><div class="sf-banner-title">{title}</div>'
            f'<div class="sf-banner-desc">{description}</div></div>'
            f'<div class="sf-banner-arrow">→</div></div>',
            unsafe_allow_html=True,
        )
        clicked = st.button("", key=f"sf_btn_{key}")
    return clicked


def _reload_all_data_caches() -> None:
    """Vide les caches `@lru_cache` de joueurs.xlsx/entraineurs.xlsx (clubs,
    coaches, dispositifs tactiques, sélections nationales) pour forcer une
    relecture depuis le disque au prochain accès -- sans ça, une édition du
    classeur pendant que le serveur Streamlit tourne n'est jamais reprise en
    compte (le cache vit pour toute la durée du process, pas juste le rerun
    Streamlit courant)."""
    clear_clubs_cache()
    clear_coaches_cache()
    clear_lineup_cache()
    clear_nations_cache()


def render_home_screen() -> None:
    st.markdown(_home_css(), unsafe_allow_html=True)

    st.markdown(
        '<div class="sf-hero">'
        '<p class="sf-wordmark">Simulafoot</p>'
        '<div class="sf-wordmark-rule"><span class="sf-kickoff-dot"></span></div>'
        '<p class="sf-tagline">Simulateur de football complet — saison 2026-2027</p>'
        "</div>",
        unsafe_allow_html=True,
    )

    _, col_reload = st.columns([5, 1])
    with col_reload:
        if st.button("🔄 Recharger les données", key="sf_reload_data", width="stretch"):
            _reload_all_data_caches()
            st.rerun()

    with st.container(key="sf_section_leagues"):
        st.markdown('<div class="sf-section-title">Championnats nationaux</div>', unsafe_allow_html=True)
        with st.container(key="sf_grid_leagues"):
            for championnat in list_championnats(CLUBS_PATH):
                flag = _CHAMPIONNAT_FLAG.get(championnat, "⚽")
                nb_clubs = len(load_clubs(CLUBS_PATH, championnat))
                if _render_tile(key=f"league_{championnat}", icon=flag, name=championnat, meta=f"{nb_clubs} clubs"):
                    select_championnat(championnat)
                    st.rerun()

    with st.container(key="sf_section_intl"):
        st.markdown('<div class="sf-section-title">Compétitions internationales</div>', unsafe_allow_html=True)
        with st.container(key="sf_grid_intl"):
            if _render_tile(
                key="champions_league",
                icon=_CHAMPIONS_LEAGUE_ICON,
                name="Ligue des Champions",
                meta="36 clubs · poules + élimination",
                gold=True,
            ):
                store_custom_competition(start_champions_league(CLUBS_PATH))
                st.rerun()
            if _render_tile(
                key="nations", icon=_NATIONS_ICON, name="Sélections nationales", meta="Sélections complètes (23/23)"
            ):
                st.session_state["perso_wizard_step"] = 1
                st.session_state[_PERSO_CLUB_SOURCE_KEY] = "nations"
                st.rerun()

    with st.container(key="sf_section_perso"):
        if _render_banner(
            key="perso",
            icon=_PERSO_ICON,
            title="Compétition personnalisée",
            description="Choisis le format, le nombre d'équipes et les clubs toi-même.",
        ):
            st.session_state["perso_wizard_step"] = 1
            st.rerun()


# --- Championnat officiel --------------------------------------------------
#
# Palette volontairement distincte de `_home_css`/`_MATCH_DETAIL_STYLE` (gris
# neutre `#121212`/`#1E1E1E` plutôt que bleu nuit) : écran dense en donnees
# (liste de matchs + classement complet), pense pour la lisibilite et la
# densite d'info plutot que pour l'immersion visuelle des ecrans "spectacle"
# (accueil, detail de match).
_SEASON_STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

div[class*="st-key-ms_header"] {
    font-family: "Inter", sans-serif;
}
.ms-header-title {
    font-family: "Inter", sans-serif; font-weight: 700; font-size: 24px; color: #fff;
    margin: 0 0 0.6rem;
}

div[class*="st-key-ms_top_btn_"] button, div[class*="st-key-ms_bottom_btn_"] button {
    background: #2e2e2e !important; border: 1px solid #444 !important; color: #fff !important;
    border-radius: 8px !important; font-family: "Inter", sans-serif; font-weight: 600;
    transition: all 0.2s ease;
}
div[class*="st-key-ms_top_btn_"] button:hover, div[class*="st-key-ms_bottom_btn_"] button:hover {
    background: #3e3e3e !important; border-color: #555 !important;
}
div[class*="st-key-ms_bottom_btn_"] button { padding: 12px 24px !important; font-size: 1.05rem; }

div[class*="st-key-ms_card_"] {
    background: #252525; border: 1px solid #333; border-radius: 8px;
    padding: 12px 18px; margin-bottom: 8px;
}
.ms-team { display: flex; align-items: center; gap: 10px; font-family: "Inter", sans-serif; min-width: 0; }
.ms-team-away { flex-direction: row-reverse; text-align: right; }
.ms-team-badge {
    flex: 0 0 auto; width: 24px; height: 24px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 9px; font-weight: 800; color: #111;
    border: 1px solid rgba(255,255,255,0.25);
}
.ms-team-text { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ms-team-name { font-size: 15px; font-weight: 600; color: #fff; }
.ms-scorers { font-size: 12px; color: #aaaaaa; }
div[class*="st-key-ms_teamwrap_"] { position: relative; height: 26px; }
div[class*="st-key-ms_clubbtn_"] { position: static !important; }
div[class*="st-key-ms_clubbtn_"] button {
    position: absolute !important; top: 0; left: 0; width: 100% !important; height: 24px !important;
    opacity: 0 !important; z-index: 2; cursor: pointer;
}
/* Le score est un st.button dans les 3 états (joué/pas joué/pas de détail
   -- voir _render_match_rows), désactivé quand il n'y a rien à ouvrir :
   même widget partout, donc même hauteur "naturelle" Streamlit sans avoir
   à la forcer -- sans ça (ex. un simple texte pour l'état "pas joué"), la
   ligne "score" change de hauteur une fois le match joué et étire toute la
   carte avec elle (les colonnes d'une rangée Streamlit s'alignent sur la
   plus haute), ce qui déplace la barre d'actions du bas d'une journée à
   l'autre. */
div[class*="st-key-ms_score_"] button, div[class*="st-key-ms_score_"] [data-testid="stBaseButton-secondary"] {
    background: transparent !important; border: none !important;
    font-family: "Inter", sans-serif; font-weight: 700 !important; font-size: 20px !important;
    box-shadow: none !important;
    height: 32px !important; min-height: 32px !important; padding: 0 !important; line-height: 32px !important;
}
/* Le libellé est rendu dans un <p> imbriqué (button > div > span > div > p).
   Streamlit fixe la couleur du <button> lui-même par un mécanisme qui reste
   gagnant même face à un `!important` en ligne posé directement dessus
   (vérifié) -- `color: inherit` sur le <p> hériterait donc de cette même
   couleur imposée. Il faut fixer une couleur EXPLICITE sur le <p> (jamais
   `inherit`) : lui, contrairement au <button>, accepte bien un override. */
div[class*="st-key-ms_score_"] [data-testid="stBaseButton-secondary"] p {
    color: #fff !important; transition: color 0.2s ease;
}
div[class*="st-key-ms_score_"] [data-testid="stBaseButton-secondary"]:hover:not(:disabled) p { color: #00a3ff !important; }
div[class*="st-key-ms_score_"] [data-testid="stBaseButton-secondary"]:disabled p { color: #555 !important; }
div[class*="st-key-ms_score_"] [data-testid="stBaseButton-secondary"]:disabled { opacity: 1 !important; cursor: default; }

.ms-standings-title {
    font-family: "Inter", sans-serif; font-weight: 700; font-size: 1.3rem; color: #fff;
    margin: 1.6rem 0 0.8rem;
}
div[class*="st-key-ms_standings_wrap"] {
    border: 1px solid #333; border-radius: 10px; overflow: hidden;
}
.ms-standings-head {
    display: grid; grid-template-columns: 44px 2.2fr repeat(8, 1fr);
    background: #1e1e1e; padding: 10px 14px; gap: 6px;
    font-family: "Inter", sans-serif; font-weight: 700; font-size: 16px;
    color: #fff;
}
.ms-standings-head span:not(:nth-child(2)) { text-align: center; }
div[class*="st-key-ms_row_"] { position: relative; }
div[class*="st-key-ms_rowbtn_"] { position: static !important; }
div[class*="st-key-ms_rowbtn_"] button {
    position: absolute !important; inset: 0 !important; width: 100% !important; height: 100% !important;
    opacity: 0 !important; z-index: 3; cursor: pointer;
}
.ms-standings-row {
    display: grid; grid-template-columns: 44px 2.2fr repeat(8, 1fr);
    padding: 9px 14px; gap: 6px; align-items: center;
    font-family: "Inter", sans-serif; font-size: 14px; color: #ddd;
    transition: background 0.15s ease;
}
.ms-standings-row span:not(:nth-child(2)) { text-align: center; }
.ms-standings-row .ms-pts { font-weight: 800; color: #fff; }
.ms-standings-row.ms-row-even { background: #121212; }
.ms-standings-row.ms-row-odd { background: #181818; }
div[class*="st-key-ms_row_"]:hover .ms-standings-row { background: #232323; }
.ms-club-cell {
    display: flex; align-items: center; gap: 8px; font-weight: 600; color: #fff;
    overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.ms-rank { color: #888888; font-weight: 700; }
.ms-w { color: #4caf50; } .ms-d { color: #aaaaaa; } .ms-l { color: #ef4444; }

/* Menu ☰ (st.popover) : uniquement visible en mobile, la paire de boutons
   desktop reste l'affichage par défaut (voir _render_season_body). */
div[class*="st-key-ms_mobile_menu"] { display: none; }

@media (max-width: 900px) {
    [data-testid="stHorizontalBlock"]:has(div[class*="st-key-ms_card_"]) { flex-direction: column !important; }
    .ms-standings-head, .ms-standings-row { grid-template-columns: 32px 1.6fr repeat(8, 1fr); font-size: 11px; }
}

/* --- Mobile (<= 480px) --------------------------------------------------
   Une seule colonne, pouce-compatible (cible >= 48px), barre d'actions
   fixée en bas -- CSS uniquement : même DOM qu'en desktop (mêmes widgets
   Streamlit, mêmes données), juste une disposition différente. Le swipe/
   tap-long/vibration/pull-to-refresh demandés ailleurs ne sont volontairement
   pas implémentés : Streamlit reexecute le script Python à chaque
   interaction (pas de survie d'un event listener JS custom entre les
   reruns) -- les faire marcher demanderait un vrai composant JS/Python
   (streamlit.components.v1 ou une lib tierce), hors de portée d'une passe
   CSS responsive et contraire à la consigne d'éviter les dépendances
   lourdes. Le bouton "🔄 Recharger les données" (écran d'accueil) couvre
   déjà le besoin de rafraîchissement manuel. */
@media (max-width: 480px) {
    div[class*="st-key-ms_desktop_actions"] { display: none; }
    div[class*="st-key-ms_mobile_menu"] { display: block; }

    .ms-header-title { font-size: 18px; }

    div[class*="st-key-ms_card_"] { padding: 12px; margin-bottom: 12px; }
    .ms-team-name { font-size: 16px; }
    .ms-scorers { font-size: 12px; }
    .ms-team-badge { width: 20px; height: 20px; }

    /* Barre d'actions fixée en bas, cible tactile 48px (repère Google). */
    div[class*="st-key-ms_bottom_bar"] {
        position: fixed; bottom: 0; left: 0; right: 0; z-index: 999;
        background: #121212; padding: 8px 12px; margin: 0;
        box-shadow: 0 -4px 8px rgba(0,163,255,0.15);
    }
    div[class*="st-key-ms_bottom_btn_"] button {
        background: #00a3ff !important; border: none !important; color: #fff !important;
        height: 48px !important; font-size: 16px !important; border-radius: 8px !important;
        box-shadow: 0 4px 8px rgba(0,163,255,0.3);
    }
    /* Marge pour que la barre fixe ne masque pas le bas du classement. */
    [data-testid="stAppViewContainer"] { padding-bottom: 76px; }

    /* Classement : en-tête collant, icônes W/D/L masquées (gain de place),
       défilement horizontal plutôt qu'un tassement illisible des colonnes. */
    div[class*="st-key-ms_standings_wrap"] { overflow-x: auto; }
    .ms-standings-head {
        position: sticky; top: 0; z-index: 1;
        grid-template-columns: 20px 120px repeat(8, 40px);
        min-width: 580px; font-size: 14px;
    }
    .ms-standings-row {
        grid-template-columns: 20px 120px repeat(8, 40px);
        min-width: 580px; font-size: 12px;
    }
    .ms-club-cell { max-width: 120px; }
    .ms-icon { display: none; }
}
</style>
"""


def _club_initials(club_name: str) -> str:
    words = [w for w in club_name.split() if not w.isdigit()] or club_name.split()
    if not words:
        return "?"
    if len(words) == 1:
        return words[0][:2].upper()
    return (words[0][0] + words[1][0]).upper()


def render_season_screen() -> None:
    season = get_season()
    _render_season_body(
        season,
        on_home=lambda: (go_to_home(), st.rerun()),
        on_reset=lambda: (reset_season(), st.rerun()),
        home_label="Changer de championnat",
        reset_label="Réinitialiser la saison",
    )


def _render_season_body(
    season: Season,
    *,
    on_home: Callable[[], None],
    on_reset: Callable[[], None],
    home_label: str,
    reset_label: str,
) -> None:
    st.markdown(_SEASON_STYLE, unsafe_allow_html=True)

    with st.container(key="ms_header"):
        col_title, col_actions = st.columns([2, 2])
        with col_title:
            st.markdown(
                f'<div class="ms-header-title">⚽ {season.championnat} | '
                f'Journée {season.current_journee_number} / {season.total_journees}</div>',
                unsafe_allow_html=True,
            )
        with col_actions:
            # Bouton "Changer de championnat"/"Réinitialiser" côte à côte en
            # desktop, menu ☰ (st.popover, widget natif -- pas de JS custom
            # fragile) en mobile : les deux sont toujours montés, CSS
            # n'affiche que celui adapté à la largeur d'écran (voir
            # `@media (max-width: 480px)` dans _SEASON_STYLE).
            with st.container(key="ms_desktop_actions"):
                col_home, col_reset = st.columns(2)
                with col_home:
                    if st.button(home_label, key="ms_top_btn_home", width="stretch"):
                        on_home()
                with col_reset:
                    if st.button(f"🔄 {reset_label}", key="ms_top_btn_reset", width="stretch"):
                        on_reset()
            with st.container(key="ms_mobile_menu"):
                with st.popover("☰", width="stretch"):
                    if st.button(f"🏆 {home_label}", key="ms_menu_btn_home", width="stretch"):
                        on_home()
                    if st.button(f"🔄 {reset_label}", key="ms_menu_btn_reset", width="stretch"):
                        on_reset()

    journee = season.current_journee

    st.markdown("### Matchs de la journée")
    _render_match_rows(journee.matches)

    # Un seul bouton qui alterne selon l'état de la journée courante :
    # "Simuler la journée" tant qu'elle n'a pas été jouée, puis "Journée
    # suivante" une fois jouée -- plutôt que deux boutons dont un seul est
    # jamais actif à la fois.
    season_over = journee.played and season.current_journee_number >= season.total_journees
    if journee.played:
        label, action = "Journée suivante →", season.next_journee
    else:
        label, action = "Simuler la journée", season.simulate_current_journee
    with st.container(key="ms_bottom_bar"):
        if st.button(label, key="ms_bottom_btn_toggle", type="primary", width="stretch", disabled=season_over):
            action()
            st.rerun()

    if season.is_season_over:
        st.success("Saison terminée ! Voici le classement final.")

    _render_standings_table(season.standings(), key=f"standings_{season.championnat}")

    _render_leaderboards(season.all_matches)
    _render_availability_panel(season.suspensions, season.injuries)


# --- Assistant Compétition Perso ----------------------------------------


def _perso_uses_nations() -> bool:
    return st.session_state.get(_PERSO_CLUB_SOURCE_KEY) == "nations"


def _perso_club_pool() -> list[ClubOption]:
    if _perso_uses_nations():
        return [
            ClubOption(name=team.name, players=team.players, championnat=NATIONS_CHAMPIONNAT_LABEL)
            for team in load_national_teams(CLUBS_PATH)
        ]
    return load_all_clubs(CLUBS_PATH)


def render_custom_wizard() -> None:
    st.title("🌍 Sélections nationales" if _perso_uses_nations() else "⚽ Compétition Perso")
    if st.button("← Retour à l'accueil"):
        _reset_wizard()
        st.rerun()

    step = st.session_state.get("perso_wizard_step", 1)
    if step == 1:
        _render_format_step()
    elif step == 2:
        _render_team_count_step()
    elif step == 3:
        _render_match_format_step()
    else:
        _render_club_picker_step()


def _render_format_step() -> None:
    st.subheader("1. Type de compétition")
    for fmt, label, description in _FORMAT_CHOICES:
        if st.button(f"{label} — {description}", width="stretch", key=f"perso_format_{fmt}"):
            st.session_state["perso_format"] = fmt
            st.session_state["perso_wizard_step"] = 2
            st.rerun()


def _render_team_count_step() -> None:
    fmt = st.session_state["perso_format"]
    st.subheader("2. Nombre d'équipes")

    if fmt == CompetitionFormat.LEAGUE:
        st.caption("De 3 à 50 équipes.")
        min_teams, max_teams, default = 3, 50, 18
    elif fmt == CompetitionFormat.KNOCKOUT:
        st.caption(
            "Au moins 2 équipes. Si le nombre n'est pas une puissance de 2, "
            "les mieux classées sont exemptées du 1er tour."
        )
        min_teams, max_teams, default = 2, 64, 16
    else:
        st.caption(
            f"Au moins {2 * QUALIFIERS_PER_GROUP} équipes (poules de 4 ; la "
            "dernière poule a 3 équipes si l'effectif ne tombe pas juste)."
        )
        min_teams, max_teams, default = 2 * QUALIFIERS_PER_GROUP, 64, 16

    if _perso_uses_nations():
        available = len(load_national_teams(CLUBS_PATH))
        max_teams = min(max_teams, available)
        default = min(default, max_teams)
        st.caption(f"{available} sélections complètes (23/23) disponibles actuellement.")

    count = st.number_input(
        "Nombre d'équipes", min_value=min_teams, max_value=max_teams, value=default, step=1
    )

    col_back, col_next = st.columns(2)
    with col_back:
        if st.button("← Précédent", width="stretch", key="perso_step2_back"):
            st.session_state["perso_wizard_step"] = 1
            st.rerun()
    with col_next:
        if st.button("Suivant →", type="primary", width="stretch", key="perso_step2_next"):
            st.session_state["perso_team_count"] = int(count)
            st.session_state["perso_wizard_step"] = 3
            st.rerun()


def _render_match_format_step() -> None:
    fmt = st.session_state["perso_format"]
    st.subheader("3. Format des matchs")
    if fmt == CompetitionFormat.KNOCKOUT:
        st.caption("Nombre de manches par confrontation.")
    elif fmt == CompetitionFormat.HYBRID:
        st.caption("Format des matchs en phase de poules (les confrontations à élimination reprennent ce format).")
    else:
        st.caption("Nombre de fois où chaque paire d'équipes s'affronte.")

    legs = st.radio(
        "Format",
        options=list(_LEGS_LABELS.keys()),
        format_func=lambda l: _LEGS_LABELS[l],
        key="perso_legs_radio",
    )

    col_back, col_next = st.columns(2)
    with col_back:
        if st.button("← Précédent", width="stretch", key="perso_step3_back"):
            st.session_state["perso_wizard_step"] = 2
            st.rerun()
    with col_next:
        if st.button("Suivant →", type="primary", width="stretch", key="perso_step3_next"):
            st.session_state["perso_legs"] = legs
            st.session_state["perso_wizard_step"] = 4
            st.rerun()


def _render_club_picker_step() -> None:
    team_count = st.session_state["perso_team_count"]
    st.subheader("4. Choix des clubs")
    st.caption(f"Sélectionne exactement {team_count} clubs : coche-les directement dans le tableau.")

    if _CLUB_SELECTION_KEY not in st.session_state:
        st.session_state[_CLUB_SELECTION_KEY] = []
    if _CLUB_TABLE_VERSION_KEY not in st.session_state:
        st.session_state[_CLUB_TABLE_VERSION_KEY] = 0

    all_clubs = _perso_club_pool()
    selected_names = set(st.session_state[_CLUB_SELECTION_KEY])
    names_by_championnat: dict[str, list[str]] = {}
    for c in all_clubs:
        names_by_championnat.setdefault(c.championnat, []).append(c.name)

    def _apply_selection(new_selection: set[str]) -> None:
        st.session_state[_CLUB_SELECTION_KEY] = sorted(new_selection)
        st.session_state[_CLUB_TABLE_VERSION_KEY] += 1  # force le tableau à reprendre cette sélection
        st.rerun()

    col_clear, col_random = st.columns(2)
    with col_clear:
        if st.button("Vider la sélection", width="stretch", key="perso_clear_selection"):
            _apply_selection(set())
    with col_random:
        if st.button("🎲 Finaliser aléatoirement", width="stretch", key="perso_random_fill"):
            diff = team_count - len(selected_names)
            new_selection = set(selected_names)
            if diff > 0:
                pool = [c.name for c in all_clubs if c.name not in new_selection]
                picks = np.random.choice(pool, size=min(diff, len(pool)), replace=False)
                new_selection.update(picks.tolist())
            elif diff < 0:
                to_remove = np.random.choice(sorted(new_selection), size=-diff, replace=False)
                new_selection.difference_update(to_remove.tolist())
            _apply_selection(new_selection)

    st.markdown("**Filtrer par championnat**")
    filter_options = ["Tous"] + sorted(names_by_championnat)
    selected_filter = st.radio(
        "Filtrer par championnat",
        options=filter_options,
        horizontal=True,
        label_visibility="collapsed",
        key="perso_championnat_filter",
    )
    displayed_clubs = [
        c for c in all_clubs if selected_filter == "Tous" or c.championnat == selected_filter
    ]

    st.markdown("**Clubs**")
    table = pd.DataFrame(
        {
            "Sélectionné": [c.name in selected_names for c in displayed_clubs],
            "Club": [c.name for c in displayed_clubs],
            "Championnat": [c.championnat for c in displayed_clubs],
        }
    )
    edited = st.data_editor(
        table,
        hide_index=True,
        width="stretch",
        height=420,
        disabled=["Club", "Championnat"],
        column_config={"Sélectionné": st.column_config.CheckboxColumn(required=True)},
        key=f"perso_club_table_{st.session_state[_CLUB_TABLE_VERSION_KEY]}_{selected_filter}",
    )
    displayed_names = {c.name for c in displayed_clubs}
    edited_selection_in_view = set(edited.loc[edited["Sélectionné"], "Club"])
    selected_names = (selected_names - displayed_names) | edited_selection_in_view
    st.session_state[_CLUB_SELECTION_KEY] = sorted(selected_names)

    count = len(selected_names)
    if count == team_count:
        st.success(f"{count} / {team_count} sélectionnés")
    elif count > team_count:
        st.warning(f"{count} / {team_count} sélectionnés — retire-en {count - team_count}")
    else:
        st.write(f"{count} / {team_count} sélectionnés")

    col_back, col_start = st.columns(2)
    with col_back:
        if st.button("← Précédent", width="stretch", key="perso_step4_back"):
            st.session_state["perso_wizard_step"] = 3
            st.rerun()
    with col_start:
        if st.button(
            "Démarrer la compétition",
            type="primary",
            width="stretch",
            disabled=count != team_count,
            key="perso_step4_start",
        ):
            clubs = [c.as_club() for c in all_clubs if c.name in selected_names]
            start_custom_competition(st.session_state["perso_format"], st.session_state["perso_legs"], clubs)
            _reset_wizard()
            st.rerun()


# --- Écrans de compétition perso en cours -------------------------------


def render_custom_competition_screen(competition: CustomCompetition) -> None:
    if competition.format == CompetitionFormat.LEAGUE:
        _render_season_body(
            competition.season,
            on_home=lambda: (clear_custom_competition(), st.rerun()),
            on_reset=lambda: (
                start_custom_competition(competition.format, competition.legs, competition.clubs),
                st.rerun(),
            ),
            home_label="Changer de compétition",
            reset_label="Réinitialiser la compétition",
        )
    elif competition.format == CompetitionFormat.KNOCKOUT:
        render_knockout_screen(competition)
    else:
        render_hybrid_screen(competition)


def render_knockout_screen(
    competition: CustomCompetition, title: str = "⚽ Compétition Perso — Élimination directe"
) -> None:
    st.title(title)
    if st.button("Changer de compétition", key="knockout_home"):
        clear_custom_competition()
        _reset_wizard()
        st.rerun()

    bracket = competition.bracket
    round_ = bracket.current_round
    st.subheader(_round_label(round_))

    _render_knockout_ties(round_)

    col_sim, col_next = st.columns(2)
    with col_sim:
        if st.button(
            "Simuler ce tour", type="primary", width="stretch", disabled=round_.played, key="knockout_sim"
        ):
            competition.simulate_bracket_round()
            st.rerun()
    with col_next:
        if st.button(
            "Tour suivant",
            width="stretch",
            disabled=not round_.played or len(round_.ties) == 1,
            key="knockout_next",
        ):
            competition.advance_bracket_round()
            st.rerun()

    if bracket.is_complete:
        st.success(f"🏆 Champion : {bracket.champion}")

    _render_leaderboards(competition.all_matches)
    _render_availability_panel(competition.suspensions, competition.injuries)


def render_hybrid_screen(competition: CustomCompetition) -> None:
    st.title(f"⚽ {competition.label or 'Compétition Perso'} — Championnat + élimination")
    if st.button("Changer de compétition", key="hybrid_home"):
        clear_custom_competition()
        _reset_wizard()
        st.rerun()

    if not competition.groups_complete:
        st.subheader("Phase de poules")
        _render_groups_standings(competition)
        if st.button("Simuler la journée des poules", type="primary", width="stretch"):
            competition.simulate_groups_matchday()
            st.rerun()
        _render_leaderboards(competition.all_matches)
        _render_availability_panel(competition.suspensions, competition.injuries)
    elif competition.bracket is None:
        st.success("Phase de poules terminée !")
        _render_groups_standings(competition)
        if st.button("Lancer la phase à élimination directe", type="primary", width="stretch"):
            competition.start_knockout_from_groups()
            st.rerun()
        _render_leaderboards(competition.all_matches)
        _render_availability_panel(competition.suspensions, competition.injuries)
    else:
        render_knockout_screen(competition, title="⚽ Compétition Perso — Phase finale (élimination directe)")


def _render_groups_standings(competition: CustomCompetition) -> None:
    for group in competition.groups:
        st.markdown(f"**{group.name}**")
        _render_clickable_club_table(group.standings(), key=f"standings_{group.name}")
        played_matches = [m for journee in group.calendar for m in journee.matches if m.played]
        if played_matches:
            with st.expander(f"Matchs joués — {group.name}"):
                _render_match_rows(played_matches)


def _round_label(round_: Round) -> str:
    return _ROUND_NAMES.get(len(round_.ties), f"Tour {round_.number}")


def _render_knockout_ties(round_: Round) -> None:
    for tie in round_.ties:
        if tie.is_bye:
            st.write(f"**{tie.home}** — Qualifié d'office (exempt)")
        elif tie.played:
            agg_home, agg_away = tie.aggregate()
            st.markdown(f"**{tie.home} vs {tie.away}** — {agg_home}-{agg_away}")
            _render_match_rows(tie.legs)
        else:
            st.write(f"**{tie.home} vs {tie.away}** — —")


# --- Matchs cliquables + écran de détail ---------------------------------


def _render_match_rows(matches: list[Match]) -> None:
    st.markdown(_SEASON_STYLE, unsafe_allow_html=True)
    for index, match in enumerate(matches):
        with st.container(key=f"ms_card_{id(match)}_{index}"):
            col_home, col_score, col_away = st.columns([3, 1, 3])
            with col_home:
                _render_team_cell(match, match.home, index, side="home")
            with col_away:
                _render_team_cell(match, match.away, index, side="away")
            with col_score:
                # Le même widget (st.button, désactivé si pas de détail à
                # ouvrir) dans les 3 cas plutôt qu'un st.markdown pour l'état
                # "pas encore joué" : Streamlit donne une hauteur "naturelle"
                # différente à ses conteneurs internes selon le type de
                # widget qu'ils contiennent, impossible à égaliser depuis
                # notre CSS (même avec !important) -- utiliser le même type
                # de widget partout élimine le problème à la racine plutôt
                # que d'essayer de forcer deux tailles internes à converger.
                if match.played and match.events is not None:
                    if st.button(
                        f"{match.home_goals} - {match.away_goals}",
                        key=f"ms_score_{id(match)}_{index}",
                        width="stretch",
                    ):
                        st.session_state[_OPEN_MATCH_KEY] = match
                        st.session_state[_OPEN_MATCH_LIST_KEY] = matches
                        st.session_state[_OPEN_MATCH_INDEX_KEY] = index
                        st.rerun()
                elif match.played:
                    st.button(
                        f"{match.home_goals} - {match.away_goals}",
                        key=f"ms_score_{id(match)}_{index}",
                        width="stretch",
                        disabled=True,
                    )
                else:
                    st.button("—", key=f"ms_score_{id(match)}_{index}", width="stretch", disabled=True)


def _render_team_cell(match: Match, club: str, index: int, *, side: str) -> None:
    """Nom de club + pastille de couleur (24px, à la place d'un logo -- voir
    la note de `kits.py` sur l'absence volontaire de logos officiels) et
    buteurs éventuels sur la même ligne (ex. "AS Monaco (M. Abline 47')"),
    cliquable pour ouvrir l'effectif (même bouton invisible superposé que
    `_render_tile`/les cartes joueur de l'écran de match)."""
    color = primary_color(club)
    badge = f'<span class="ms-team-badge" style="background:{color};">{_club_initials(club)}</span>'
    scorers = _scorers_inline(match, club)
    scorers_html = f' <span class="ms-scorers">({scorers})</span>' if scorers else ""
    text = f'<span class="ms-team-text"><span class="ms-team-name">{club}</span>{scorers_html}</span>'
    parts = [badge, text] if side == "home" else [text, badge]
    with st.container(key=f"ms_teamwrap_{side}_{id(match)}_{index}"):
        st.markdown(f'<div class="ms-team ms-team-{side}">{"".join(parts)}</div>', unsafe_allow_html=True)
        if st.button("", key=f"ms_clubbtn_{side}_{id(match)}_{index}"):
            st.session_state[_OPEN_CLUB_KEY] = club
            st.rerun()


def _scorers_inline(match: Match, club_name: str) -> str | None:
    """Comme `_scorers_caption`, mais sans parenthèses individuelles autour
    de chaque minute (ex. "M. Abline 47', M. Biereth 49'") -- pour un
    affichage "Club (buteurs)" avec une seule paire de parenthèses globale
    (voir `_render_team_cell`), plutôt que la légende sous le score du
    détail de match (`_render_scoreboard`) qui garde le format d'origine."""
    if match.events is None:
        return None
    goals = sorted((g for g in match.events.goals if g.club_name == club_name), key=lambda g: g.minute)
    if not goals:
        return None
    return ", ".join(f"{_short_name(g.scorer)} {g.minute}'" for g in goals)


def _scorers_caption(match: Match, club_name: str) -> str | None:
    """Buteurs de `club_name` dans ce match, triés par minute, en petit texte
    du genre "J. Pedro (44'), M. Rogers (77')" -- None si pas de buts (ou pas
    encore joué / pas d'événements)."""
    if match.events is None:
        return None
    goals = sorted((g for g in match.events.goals if g.club_name == club_name), key=lambda g: g.minute)
    if not goals:
        return None
    return ", ".join(f"{_short_name(g.scorer)} ({g.minute}')" for g in goals)


def _coach_suffix(coach: str | None) -> str:
    return f" ({coach})" if coach else ""


def render_match_detail_screen(match: Match) -> None:
    events = match.events

    st.markdown(_MATCH_DETAIL_STYLE, unsafe_allow_html=True)

    with st.container(key="md_page"):
        _render_nav_row(match)

        if events is None:
            st.title(f"⚽ {match.home} {match.home_goals} - {match.away_goals} {match.away}")
            st.info("Pas de détails disponibles pour ce match.")
            return

        home_formation = actual_formation_label([s for s in events.home_lineup if s.started])
        away_formation = actual_formation_label([s for s in events.away_lineup if s.started])

        col_pitch, col_timeline = st.columns([3, 1])
        with col_pitch:
            _render_scoreboard(match)
            _render_tactical_info(match, home_formation, away_formation)
            _render_pitch(match, events)
            _render_bench_chips(match, events)
        with col_timeline:
            _render_match_timeline(match, events)

    _render_compositions(match, events, home_formation, away_formation)


def _render_nav_row(match: Match) -> None:
    """Bouton Retour + navigation Match précédent/suivant, quand le match a
    été ouvert depuis une liste connue (voir `_render_match_rows`) -- pas de
    navigation possible si on arrive ici autrement (état de session
    incohérent ou périmé)."""
    match_list = st.session_state.get(_OPEN_MATCH_LIST_KEY)
    match_index = st.session_state.get(_OPEN_MATCH_INDEX_KEY)
    has_nav = (
        isinstance(match_list, list)
        and isinstance(match_index, int)
        and 0 <= match_index < len(match_list)
        and match_list[match_index] is match
    )

    col_back, _spacer, col_prev, col_next = st.columns([2, 5, 1.6, 1.6])
    with col_back:
        if st.button("← Retour", key="md_back"):
            st.session_state.pop(_OPEN_MATCH_KEY, None)
            st.rerun()
    if has_nav:
        with col_prev:
            if st.button("← Match précédent", key="md_prev", disabled=match_index <= 0, width="stretch"):
                _open_match_at(match_list, match_index - 1)
        with col_next:
            if st.button(
                "Match suivant →", key="md_next", disabled=match_index >= len(match_list) - 1, width="stretch"
            ):
                _open_match_at(match_list, match_index + 1)


def _open_match_at(match_list: list[Match], index: int) -> None:
    st.session_state[_OPEN_MATCH_KEY] = match_list[index]
    st.session_state[_OPEN_MATCH_INDEX_KEY] = index
    st.rerun()


def _render_tactical_info(match: Match, home_formation: str, away_formation: str) -> None:
    st.markdown(
        f'<div class="md-tactical">'
        f"{_tactical_block_html(match.home, coach_name(match.home), home_formation)}"
        f'<div class="md-tactical-vs">VS</div>'
        f"{_tactical_block_html(match.away, coach_name(match.away), away_formation)}"
        f"</div>",
        unsafe_allow_html=True,
    )


def _tactical_block_html(club: str, coach: str | None, formation: str) -> str:
    color = primary_color(club)
    coach_html = f'<div class="md-tactical-coach">👤 {coach}</div>' if coach else ""
    return (
        f'<div class="md-tactical-block">'
        f'<div class="md-tactical-team" style="color:{color};">{club}</div>'
        f"{coach_html}"
        f'<div class="md-tactical-formation" style="background:{color}33;">{formation}</div>'
        f"</div>"
    )


def _render_bench_chips(match: Match, events: MatchEvents) -> None:
    """Aperçu compact du banc (nom + note) juste sous le terrain, par équipe
    -- pour un coup d'œil rapide sans avoir à dérouler les compositions
    complètes (voir `_render_compositions`, repliées par défaut)."""
    home_subs = [s for s in events.home_lineup if not s.started]
    away_subs = [s for s in events.away_lineup if not s.started]
    if not home_subs and not away_subs:
        return
    st.markdown(
        f'<div class="md-bench">'
        f'<div class="md-bench-title">🪑 Banc de touche</div>'
        f'<div class="md-bench-row">'
        f'{_bench_team_html(match.home, home_subs)}'
        f'{_bench_team_html(match.away, away_subs)}'
        f"</div></div>",
        unsafe_allow_html=True,
    )


def _bench_team_html(club: str, subs: list[PlayerMatchStat]) -> str:
    chips = "".join(
        f'<span class="md-bench-chip">{_short_name(s.player_name)} '
        f'<span class="md-rating-pill md-rating-{_rating_tier(s.rating)}" style="position:static;">{s.rating:.1f}</span>'
        f"</span>"
        for s in subs
    )
    return f'<div class="md-bench-team"><div class="md-bench-team-label">{club}</div><div class="md-bench-chips">{chips}</div></div>'


def _render_compositions(match: Match, events: MatchEvents, home_formation: str, away_formation: str) -> None:
    with st.expander("📋 Voir les compositions détaillées et statistiques", expanded=False):
        st.caption("Clique sur un joueur pour voir sa fiche (poste, âge, nationalité, note...).")
        sub_on_minute = {(sub.club_name, sub.player_on): sub.minute for sub in events.substitutions}
        col_home, col_away = st.columns(2)
        with col_home:
            st.subheader(f"{match.home}{_coach_suffix(coach_name(match.home))} — {home_formation}")
            _render_squad_cards(events.home_lineup, sub_on_minute, key_prefix=f"home_{match.home}_{match.away}")
        with col_away:
            st.subheader(f"{match.away}{_coach_suffix(coach_name(match.away))} — {away_formation}")
            _render_squad_cards(events.away_lineup, sub_on_minute, key_prefix=f"away_{match.home}_{match.away}")


def _render_squad_cards(
    stats: list[PlayerMatchStat], sub_on_minute: dict[tuple[str, str], int], *, key_prefix: str
) -> None:
    starters = [s for s in stats if s.started]
    subs = [s for s in stats if not s.started]

    st.markdown('<div class="md-squad-title">Titulaires</div>', unsafe_allow_html=True)
    selected = _render_player_card_grid(starters, sub_on_minute, key_prefix=f"{key_prefix}_start")
    if selected is not None:
        _render_player_card(selected)

    if subs:
        st.markdown('<div class="md-squad-title">Remplaçants</div>', unsafe_allow_html=True)
        selected = _render_player_card_grid(subs, sub_on_minute, key_prefix=f"{key_prefix}_sub")
        if selected is not None:
            _render_player_card(selected)


def _render_player_card_grid(
    stats: list[PlayerMatchStat], sub_on_minute: dict[tuple[str, str], int], *, key_prefix: str
) -> PlayerMatchStat | None:
    if not stats:
        return None
    selected_key = f"md_selected_{key_prefix}"
    with st.container(key=f"md_grid_{key_prefix}"):
        for i, stat in enumerate(stats):
            with st.container(key=f"md_card_{key_prefix}_{i}"):
                minute_on = sub_on_minute.get((stat.club_name, stat.player_name))
                st.markdown(_player_card_html(stat, minute_on), unsafe_allow_html=True)
                if st.button("", key=f"md_cardbtn_{key_prefix}_{i}"):
                    st.session_state[selected_key] = i
                    st.rerun()
    selected_idx = st.session_state.get(selected_key)
    if isinstance(selected_idx, int) and 0 <= selected_idx < len(stats):
        return stats[selected_idx]
    return None


def _player_card_html(stat: PlayerMatchStat, minute_on: int | None) -> str:
    badges = _player_badges(stat, None)
    badges_html = f'<div class="md-card-badges">{badges}</div>' if badges else ""
    entered_html = f'<div class="md-card-entered">Entré à la {minute_on}\'</div>' if minute_on is not None else ""
    return (
        f'<div class="md-player-card">'
        f'<div class="md-card-name">{stat.player_name}</div>'
        f'<div class="md-card-poste">{stat.poste}</div>'
        f'<div class="md-rating-pill md-rating-{_rating_tier(stat.rating)}">{stat.rating:.1f}</div>'
        f"{badges_html}{entered_html}"
        f"</div>"
    )


# --- Vue "stade" (terrain + fil du match) ---------------------------------
#
# Terrain rendu à l'HORIZONTALE (domicile à gauche, attaque vers la droite ;
# extérieur à droite, attaque vers la gauche). `pitch_layout.place_starting_xi`
# calcule des coordonnées pensées pour un terrain VERTICAL (x = latéral,
# y = profondeur du but vers le milieu, conçu pour une vue "derrière le but")
# -- plutôt que dupliquer cette logique de placement par poste, on permute
# les axes à l'affichage (CSS left = y, top = 100 - x) pour obtenir une vue
# "ligne de touche" cohérente avec les conventions d'affichage habituelles
# (FotMob, SofaScore...) : une équipe qui attaque vers la DROITE a son côté
# droit (RB, ailier droit...) en BAS de l'écran et son côté gauche en HAUT --
# le symétrique de `x` brut, pas `x` lui-même, sans quoi les latéraux/ailiers
# se retrouvent inversés (voir `_player_token_html`).
_MATCH_DETAIL_STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Big+Shoulders+Display:wght@700;800&family=Manrope:wght@400;500;600;700&display=swap');

[data-testid="stAppViewContainer"] {
    background-image:
        radial-gradient(rgba(255,255,255,0.028) 1px, transparent 1px),
        radial-gradient(circle at 15% -10%, rgba(255,75,75,0.06), transparent 45%),
        linear-gradient(160deg, #0a0e1a 0%, #1a1f2e 100%);
    background-size: 3px 3px, cover, cover;
    background-attachment: fixed;
}

div[class*="st-key-md_page"] { animation: mdFadeIn 0.3s ease; }
@keyframes mdFadeIn {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: none; }
}

div[class*="st-key-md_back"] button {
    background: transparent !important;
    border: 1px solid rgba(255,255,255,0.35) !important;
    color: #F4F6F9 !important;
    border-radius: 8px !important;
    font-family: "Manrope", sans-serif;
    transition: background 0.15s ease, border-color 0.15s ease;
}
div[class*="st-key-md_back"] button:hover {
    background: rgba(255,255,255,0.10) !important;
    border-color: rgba(255,255,255,0.55) !important;
}

.md-scoreboard {
    background: rgba(0,0,0,0.7);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 14px;
    padding: 1rem 1.4rem;
    text-align: center;
    margin: 0.9rem 0 1rem;
}
.md-score-line {
    font-family: "Big Shoulders Display", sans-serif;
    font-weight: 800;
    font-size: clamp(1.6rem, 2.6vw, 2.5rem);
    letter-spacing: 0.02em;
    text-transform: uppercase;
    color: #ffffff;
    line-height: 1.15;
    margin: 0;
}
.md-score-num { padding: 0 0.15em; }
.md-scorers {
    font-family: "Manrope", sans-serif;
    font-size: 0.85rem;
    color: rgba(230,230,235,0.72);
    margin-top: 0.35rem;
}

.md-pitch-wrap { display: flex; justify-content: center; }
.md-pitch {
    position: relative;
    width: 100%;
    max-width: 900px;
    aspect-ratio: 8 / 5;
    border-radius: 12px;
    border: 2px solid rgba(255,255,255,0.4);
    overflow: hidden;
    background: repeating-linear-gradient(90deg, #2e7d32 0%, #2e7d32 10%, #358a38 10%, #358a38 20%);
    box-shadow: 0 18px 50px rgba(0,0,0,0.5);
    margin-bottom: 0.5rem;
}
.md-halfway {
    position: absolute; top: 0; left: 50%; width: 2px; height: 100%;
    background: rgba(255,255,255,0.55); transform: translateX(-50%);
}
.md-circle-mid {
    position: absolute; left: 50%; top: 50%; width: 15%; height: 26%;
    border: 2px solid rgba(255,255,255,0.55); border-radius: 50%;
    transform: translate(-50%, -50%);
}
.md-goalbox {
    position: absolute; top: 50%; width: 6%; height: 46%;
    border: 2px solid rgba(255,255,255,0.55); transform: translateY(-50%);
}
.md-goalbox-left { left: 0; border-left: none; }
.md-goalbox-right { right: 0; border-right: none; }

.md-token {
    position: absolute; transform: translate(-50%, -50%);
    display: flex; flex-direction: column; align-items: center; width: 78px;
}
.md-badges {
    font-size: 12px; line-height: 1; margin-bottom: 3px; white-space: nowrap;
    text-shadow: 0 1px 2px rgba(0,0,0,0.7);
}
.md-jersey-wrap { position: relative; width: 40px; height: 40px; }
.md-jersey-circle {
    width: 40px; height: 40px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-family: "Manrope", sans-serif; font-weight: 800; font-size: 13px;
    border: 2px solid rgba(255,255,255,0.55);
    box-shadow: 0 2px 6px rgba(0,0,0,0.5);
}
.md-rating-badge {
    position: absolute; right: -6px; bottom: -6px;
    width: 20px; height: 20px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-weight: 700; font-size: 10px; color: #fff;
    border: 2px solid rgba(0,0,0,0.3); box-shadow: 0 1px 3px rgba(0,0,0,0.5);
}
.md-rating-good { background: #1e8e3e; }
.md-rating-avg { background: #c99a12; }
.md-rating-poor { background: #c0392b; }
.md-name {
    font-size: 11px; font-weight: 600; color: #fff; margin-top: 4px;
    white-space: nowrap; text-shadow: 0 1px 2px rgba(0,0,0,0.85);
}

.md-bench {
    margin-top: 0.7rem; padding: 0.7rem 0.9rem;
    background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px;
}
.md-bench-title {
    font-family: "Manrope", sans-serif; font-weight: 700; font-size: 12px;
    letter-spacing: 0.06em; text-transform: uppercase;
    color: rgba(230,230,235,0.6); margin-bottom: 0.5rem;
}
.md-bench-row { display: flex; gap: 1.2rem; flex-wrap: wrap; }
.md-bench-team { flex: 1; min-width: 220px; }
.md-bench-team-label {
    font-family: "Manrope", sans-serif; font-weight: 700; font-size: 12px;
    color: rgba(230,230,235,0.75); margin-bottom: 0.35rem;
}
.md-bench-chips { display: flex; flex-wrap: wrap; gap: 6px; }
.md-bench-chip {
    display: inline-flex; align-items: center; gap: 6px;
    background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.1);
    border-radius: 14px; padding: 3px 10px 3px 12px;
    font-family: "Manrope", sans-serif; font-size: 12px; color: #e5e7eb;
}

.md-timeline-card {
    background: rgba(20,20,30,0.9);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 14px;
    padding: 1rem 1rem 0.6rem;
    margin-top: 0.9rem;
}
.md-timeline-title {
    font-family: "Manrope", sans-serif; font-weight: 700; font-size: 16px;
    color: #fff; margin-bottom: 0.8rem;
}
.md-timeline-list { max-height: 500px; overflow-y: auto; padding-right: 6px; }
.md-timeline-list::-webkit-scrollbar { width: 4px; }
.md-timeline-list::-webkit-scrollbar-track { background: #374151; border-radius: 2px; }
.md-timeline-list::-webkit-scrollbar-thumb { background: #6b7280; border-radius: 2px; }
/* Chronologie verticale : une fine ligne (1px) traverse tous les
   événements, chacun étant un "nœud" coloré posé sur cette ligne -- minute
   à gauche, nœud au centre, description à droite (voir `match-timeline` /
   `timeline-event` dans `_render_match_timeline`). */
.match-timeline { position: relative; }
.match-timeline::before {
    content: ""; position: absolute;
    left: 62px; top: 4px; bottom: 4px; width: 1px;
    background: rgba(255,255,255,0.14);
}
.timeline-event {
    display: grid; grid-template-columns: 40px 24px 1fr;
    column-gap: 10px; align-items: start;
    margin-bottom: 14px; font-family: "Manrope", sans-serif;
}
.timeline-event:last-child { margin-bottom: 0; }
.timeline-minute {
    text-align: right; font-weight: 700; font-size: 12px;
    color: #e5e7eb; padding-top: 3px;
}
.timeline-node {
    position: relative; z-index: 1;
    width: 22px; height: 22px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 11px;
}
.timeline-node--goal { background: #10b981; }
.timeline-node--card_yellow { background: #fbbf24; }
.timeline-node--card_red { background: #ef4444; }
.timeline-node--sub { background: #3b82f6; }
.timeline-node--other { background: #9ca3af; }
.timeline-desc { font-size: 13px; color: #e5e7eb; padding-top: 3px; }
.md-sub-line2 { color: rgba(230,230,235,0.55); font-size: 11.5px; margin-top: 1px; }
.md-halftime-sep {
    display: grid; grid-template-columns: 40px 24px 1fr; column-gap: 10px;
    margin: 2px 0 16px; color: rgba(230,230,235,0.5);
}
.md-halftime-sep span {
    grid-column: 2 / 4;
    display: flex; align-items: center; gap: 10px;
    font-family: "Manrope", sans-serif; font-size: 10px; font-style: italic;
    letter-spacing: 0.08em; white-space: nowrap;
}
.md-halftime-sep span::before, .md-halftime-sep span::after {
    content: ""; flex: 1; height: 1px; background: rgba(255,255,255,0.12);
}

.md-tactical {
    display: flex; align-items: center; justify-content: center; gap: 1.2rem;
    margin: 0 0 0.9rem;
}
.md-tactical-block { flex: 1; text-align: center; }
.md-tactical-team {
    font-family: "Manrope", sans-serif; font-weight: 700; font-size: 16px;
}
.md-tactical-coach {
    font-family: "Manrope", sans-serif; font-size: 13px;
    color: rgba(230,230,235,0.72); margin-top: 0.2rem;
}
.md-tactical-formation {
    display: inline-block; margin-top: 0.5rem; padding: 0.25rem 0.8rem;
    border-radius: 8px; font-family: "Big Shoulders Display", sans-serif;
    font-weight: 800; font-size: 18px; color: #fff;
}
.md-tactical-vs {
    font-family: "Big Shoulders Display", sans-serif; font-weight: 800;
    font-size: 20px; color: rgba(230,230,235,0.5); padding: 0 0.2rem;
}

.md-squad-title {
    font-family: "Manrope", sans-serif; font-weight: 700; font-size: 12px;
    letter-spacing: 0.08em; text-transform: uppercase;
    color: rgba(230,230,235,0.6); margin: 1rem 0 0.6rem;
}
div[class*="st-key-md_grid_"] {
    display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.7rem;
}
div[class*="st-key-md_card_"] { position: relative; }
div[class*="st-key-md_cardbtn_"] { position: static !important; width: 100% !important; }
div[class*="st-key-md_cardbtn_"] button {
    position: absolute !important; inset: 0 !important; width: 100% !important; height: 100% !important;
    opacity: 0 !important; z-index: 3; cursor: pointer; border-radius: 10px;
}
.md-player-card {
    position: relative;
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 10px;
    padding: 0.6rem 0.7rem;
    transition: background 0.15s ease, border-color 0.15s ease;
}
div[class*="st-key-md_card_"]:hover .md-player-card {
    background: rgba(255,255,255,0.08); border-color: rgba(255,255,255,0.2);
}
.md-card-name {
    font-family: "Manrope", sans-serif; font-weight: 700; font-size: 14px;
    color: #fff; padding-right: 32px; line-height: 1.25;
}
.md-card-poste {
    font-family: "Manrope", sans-serif; font-size: 11px;
    color: rgba(230,230,235,0.6); margin-top: 2px;
}
.md-rating-pill {
    position: absolute; top: 0.6rem; right: 0.6rem;
    min-width: 26px; height: 26px; padding: 0 4px; border-radius: 13px;
    display: flex; align-items: center; justify-content: center;
    font-family: "Manrope", sans-serif; font-weight: 700; font-size: 11px; color: #fff;
}
.md-card-badges { margin-top: 0.4rem; font-size: 13px; }
.md-card-entered {
    margin-top: 0.3rem; font-size: 11px; font-style: italic;
    color: rgba(230,230,235,0.55);
}

div[class*="st-key-md_prev"] button, div[class*="st-key-md_next"] button {
    background: transparent !important;
    border: 1px solid rgba(255,255,255,0.35) !important;
    color: #F4F6F9 !important;
    border-radius: 8px !important;
    font-family: "Manrope", sans-serif;
    transition: background 0.15s ease, border-color 0.15s ease;
}
div[class*="st-key-md_prev"] button:hover, div[class*="st-key-md_next"] button:hover {
    background: rgba(255,255,255,0.10) !important; border-color: rgba(255,255,255,0.55) !important;
}
div[class*="st-key-md_prev"] button:disabled, div[class*="st-key-md_next"] button:disabled {
    opacity: 0.3 !important;
}

@media (max-width: 1200px) {
    [data-testid="stHorizontalBlock"] { flex-direction: column !important; }
    div[class*="st-key-md_grid_"] { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 480px) {
    .md-score-line { font-size: 1.4rem; }
    .md-token { width: 56px; }
    .md-jersey-circle, .md-jersey-wrap { width: 32px; height: 32px; }
    .md-name { font-size: 10px; }
    .md-badges { font-size: 10px; }
    div[class*="st-key-md_grid_"] { grid-template-columns: 1fr; }
    div[class*="st-key-md_prev"], div[class*="st-key-md_next"] { display: none; }
}
</style>
"""


def _render_scoreboard(match: Match) -> None:
    home_scorers = _scorers_caption(match, match.home)
    away_scorers = _scorers_caption(match, match.away)
    scorer_parts = [s for s in (home_scorers, away_scorers) if s]
    scorers_html = f'<div class="md-scorers">{" &nbsp;·&nbsp; ".join(scorer_parts)}</div>' if scorer_parts else ""
    st.markdown(
        f'<div class="md-scoreboard">'
        f'<h1 class="md-score-line">{match.home.upper()} '
        f'<span class="md-score-num">{match.home_goals}</span> - '
        f'<span class="md-score-num">{match.away_goals}</span> {match.away.upper()}</h1>'
        f"{scorers_html}"
        f"</div>",
        unsafe_allow_html=True,
    )


def _render_pitch(match: Match, events: MatchEvents) -> None:
    home_starters = [s for s in events.home_lineup if s.started]
    away_starters = [s for s in events.away_lineup if s.started]
    # L'équipe à domicile "en haut" du repère vertical d'origine devient,
    # une fois les axes permutés à l'affichage, l'équipe à GAUCHE du terrain
    # horizontal (attaque vers la droite) ; l'extérieur est à droite.
    placed = place_starting_xi(home_starters, attacking_up=False) + place_starting_xi(
        away_starters, attacking_up=True
    )

    # Couleurs par équipe (pas juste par club) : deux clubs aux couleurs
    # primaires proches (ex. Monaco/Brest, rouge sur rouge) doivent quand
    # même rester visuellement distincts sur le terrain -- voir
    # `kits.match_kit_colors` (bascule sur la couleur secondaire façon
    # maillot extérieur en cas de clash).
    (home_fill, home_border), (away_fill, away_border) = match_kit_colors(match.home, match.away)
    colors_by_club = {match.home: (home_fill, home_border), match.away: (away_fill, away_border)}

    subbed_off_minute = {(sub.club_name, sub.player_off): sub.minute for sub in events.substitutions}
    tokens_html = "".join(
        _player_token_html(p, subbed_off_minute, *colors_by_club[p.stat.club_name]) for p in placed
    )

    st.markdown(
        f"""
        <div class="md-pitch-wrap">
            <div class="md-pitch">
                <div class="md-halfway"></div>
                <div class="md-circle-mid"></div>
                <div class="md-goalbox md-goalbox-left"></div>
                <div class="md-goalbox md-goalbox-right"></div>
                {tokens_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _player_token_html(
    placed: PlacedPlayer, subbed_off_minute: dict[tuple[str, str], int], fill: str, border: str
) -> str:
    stat = placed.stat
    minute_off = subbed_off_minute.get((stat.club_name, stat.player_name))
    badges = _player_badges(stat, minute_off)
    badges_html = f'<div class="md-badges">{badges}</div>' if badges else ""
    fg = _contrast_text_color(fill)
    # left = y, top = 100 - x : voir la note en tête de section sur la permutation d'axes.
    return (
        f'<div class="md-token" style="left:{placed.y:.1f}%; top:{100 - placed.x:.1f}%;">'
        f"{badges_html}"
        f'<div class="md-jersey-wrap">'
        f'<div class="md-jersey-circle" style="background:{fill}; color:{fg}; border-color:{border};">'
        f"{_initials(stat.player_name)}</div>"
        f'<div class="md-rating-badge md-rating-{_rating_tier(stat.rating)}">{stat.rating:.1f}</div>'
        f"</div>"
        f'<div class="md-name">{_short_name(stat.player_name)}</div>'
        f"</div>"
    )


def _initials(full_name: str) -> str:
    parts = full_name.split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[-1][0]).upper()
    return full_name[:2].upper() if full_name else "?"


def _contrast_text_color(hex_color: str) -> str:
    """Texte noir ou blanc selon la luminance de `hex_color` (#rrggbb), pour
    que les initiales restent lisibles sur un maillot clair (ex. Real Madrid,
    Juventus) comme sur un maillot sombre."""
    h = hex_color.lstrip("#")
    if len(h) != 6:
        return "#ffffff"
    r, g, b = (int(h[i : i + 2], 16) for i in (0, 2, 4))
    luminance = 0.299 * r + 0.587 * g + 0.114 * b
    return "#111111" if luminance > 150 else "#ffffff"


def _player_badges(stat: PlayerMatchStat, subbed_off_minute: int | None) -> str:
    badges = []
    if stat.goals:
        badges.append("⚽" * stat.goals)
    if stat.assists:
        badges.append("🅰️" * stat.assists)
    card = _card_label(stat)
    if card:
        badges.append(card)
    if subbed_off_minute is not None:
        badges.append(f"🔻{subbed_off_minute}'")
    return " ".join(badges)


def _rating_tier(rating: float) -> str:
    if rating > 7.0:
        return "good"
    if rating >= 5.0:
        return "avg"
    return "poor"


def _short_name(full_name: str) -> str:
    parts = full_name.split()
    if len(parts) <= 1:
        return full_name
    return f"{parts[0][0]}. {parts[-1]}"


# Icône du nœud de chronologie par nature d'événement (voir
# `.timeline-node--*` pour la couleur associée à chaque valeur).
_TIMELINE_NODE_ICON = {
    "goal": "⚽",
    "card_yellow": "🟨",
    "card_red": "🟥",
    "sub": "🔄",
    "other": "•",
}


def _render_match_timeline(match: Match, events: MatchEvents) -> None:
    entries = _match_timeline_entries(match, events)
    if entries:
        rows_parts = []
        halftime_shown = False
        for minute, kind, html in entries:
            if not halftime_shown and minute > 45:
                rows_parts.append('<div class="md-halftime-sep"><span>MI-TEMPS</span></div>')
                halftime_shown = True
            icon = _TIMELINE_NODE_ICON.get(kind, "•")
            rows_parts.append(
                f'<div class="timeline-event">'
                f'<div class="timeline-minute">{minute}\'</div>'
                f'<div class="timeline-node timeline-node--{kind}">{icon}</div>'
                f'<div class="timeline-desc">{html}</div></div>'
            )
        rows = "".join(rows_parts)
    else:
        rows = '<p style="color: rgba(230,230,235,0.6); font-size: 13px; margin: 0;">Aucun fait de jeu à signaler.</p>'
    st.markdown(
        f'<div class="md-timeline-card">'
        f'<div class="md-timeline-title">📋 Fil du match</div>'
        f'<div class="md-timeline-list"><div class="match-timeline">{rows}</div></div>'
        f"</div>",
        unsafe_allow_html=True,
    )


def _match_timeline_entries(match: Match, events: MatchEvents) -> list[tuple[int, str, str]]:
    """(minute, kind, html) trié par minute -- `kind` pilote la couleur/icône
    du nœud de chronologie (voir `_TIMELINE_NODE_ICON`, `.timeline-node--*`) :
    "goal", "card_yellow", "card_red", "sub" ou "other". La minute n'est
    volontairement pas répétée dans `html` : elle est déjà affichée à gauche
    de la ligne de temps (voir `_render_match_timeline`)."""
    entries: list[tuple[int, str, str]] = []

    running_score = {match.home: 0, match.away: 0}
    for goal in sorted(events.goals, key=lambda g: g.minute):
        running_score[goal.club_name] = running_score.get(goal.club_name, 0) + 1
        score = f"{running_score.get(match.home, 0)}-{running_score.get(match.away, 0)}"
        penalty_text = " (penalty)" if goal.penalty else ""
        # Le club n'est volontairement pas répété ici (deja lisible via
        # l'évolution du score) ; le passeur reste accessible en survol
        # plutôt que d'alourdir la ligne.
        title_attr = f' title="Passe déc. : {goal.assist}"' if goal.assist else ""
        entries.append(
            (goal.minute, "goal", f"<span{title_attr}><b>{goal.scorer}</b>{penalty_text} — {score}</span>")
        )

    card_kind = {"direct": "card_red", "second_yellow": "card_red", "yellow": "card_yellow"}
    for card in events.cards:
        entries.append((card.minute, card_kind[card.card_type], f"<b>{card.player}</b>"))

    for sub in events.substitutions:
        entries.append(
            (
                sub.minute,
                "sub",
                f'<div class="md-sub-line1"><b>{sub.player_on}</b> ↻ {sub.player_off}</div>'
                f'<div class="md-sub-line2">{sub.club_name}</div>',
            )
        )

    for injury in events.injuries:
        entries.append((injury.minute, "other", f"🚑 <b>{injury.player}</b> ({injury.club_name}) — blessure"))

    for missed in events.penalties_missed:
        entries.append((missed.minute, "other", f"❌ Penalty manqué par <b>{missed.player}</b> ({missed.club_name})"))

    entries.sort(key=lambda e: e[0])
    return entries


def _card_label(stat: PlayerMatchStat) -> str:
    if stat.red_card_type == "direct":
        return "🟥"
    if stat.red_card_type == "second_yellow":
        return "🟨🟥"
    if stat.yellow_cards == 1:
        return "🟨"
    return ""


def _render_player_card(stat: PlayerMatchStat) -> None:
    st.markdown(f"**{stat.player_name}** — {stat.club_name}")
    cols = st.columns(4)
    cols[0].metric("Poste", stat.poste)
    cols[1].metric("Âge", stat.age)
    cols[2].metric("Note /100", f"{stat.note:.1f}")
    cols[3].metric("Note du match", f"{stat.rating:.1f}")

    details = [stat.nationalite, "Titulaire" if stat.started else "Entrant"]
    st.caption(" · ".join(d for d in details if d))

    highlights = []
    if stat.goals:
        highlights.append(f"⚽ {stat.goals} but{'s' if stat.goals > 1 else ''}")
    if stat.assists:
        highlights.append(f"🅰️ {stat.assists} passe{'s' if stat.assists > 1 else ''} déc.")
    card = _card_label(stat)
    if card:
        highlights.append(f"{card} carton")
    if stat.injured:
        highlights.append(f"🚑 blessure ({stat.injury_duration} match{'s' if stat.injury_duration > 1 else ''})")
    if highlights:
        st.write(" · ".join(highlights))


# --- Clubs et joueurs cliquables (communs à tous les formats) --------------

# Ordre d'affichage des effectifs de club : défense -> milieu -> attaque,
# cohérent avec l'ordre tactique habituel plutôt que l'ordre d'apparition
# dans le fichier source.
_POSTE_DISPLAY_ORDER = ["GK", "DC", "LB", "RB", "MDC", "MC", "MOC", "AG", "AD", "SA", "BU", "ATT"]


def _find_club(club_name: str) -> Club | None:
    """Reconstruit un `Club` (effectif complet) à partir de son seul nom, en
    cherchant dans le vivier complet (`load_all_clubs`, mis en cache côté
    `clubs.py`) -- fonctionne quel que soit l'écran d'où vient le clic
    (saison officielle, Compétition Perso, poules...), sans avoir à faire
    transiter l'objet `Club` lui-même à travers chaque tableau cliquable."""
    option = next((o for o in load_all_clubs(CLUBS_PATH) if o.name == club_name), None)
    return option.as_club() if option is not None else None


def render_club_detail_screen(club_name: str) -> None:
    if st.button("← Retour"):
        st.session_state.pop(_OPEN_CLUB_KEY, None)
        st.rerun()

    club = _find_club(club_name)
    if club is None:
        st.error(f"Club introuvable : {club_name}")
        return

    st.title(f"⚽ {club.name}")
    st.caption(f"{len(club.players)} joueurs")

    by_poste: dict[str, list[Player]] = {}
    for player in club.players:
        by_poste.setdefault(player.poste, []).append(player)

    ordered_postes = [p for p in _POSTE_DISPLAY_ORDER if p in by_poste]
    ordered_postes += sorted(p for p in by_poste if p not in _POSTE_DISPLAY_ORDER)

    for poste in ordered_postes:
        players = sorted(by_poste[poste], key=lambda p: -p.note)
        st.markdown(f"**{poste}** &nbsp;·&nbsp; {len(players)} joueur{'s' if len(players) > 1 else ''}", unsafe_allow_html=True)
        _render_roster_table(players, key=f"roster_{club.name}_{poste}")


def _render_roster_table(players: list[Player], *, key: str) -> None:
    rows = [
        {"Joueur": p.name, "Âge": p.age, "Nationalité": p.nationalite, "Moyenne joueur": p.note}
        for p in players
    ]
    event = st.dataframe(
        rows,
        hide_index=True,
        width="stretch",
        on_select="rerun",
        selection_mode="single-row",
        column_config={
            "Moyenne joueur": st.column_config.ProgressColumn("Moyenne joueur", min_value=0, max_value=100, format="%.0f")
        },
        key=key,
    )
    selected_rows = event.selection.rows if event is not None else []
    if selected_rows:
        _render_player_profile_card(players[selected_rows[0]])


def _render_player_profile_card(player: Player) -> None:
    st.markdown(f"**{player.name}** — {player.club}")
    cols = st.columns(3)
    cols[0].metric("Poste", player.poste)
    cols[1].metric("Âge", player.age)
    cols[2].metric("Moyenne joueur", f"{player.note:.1f}")

    details = [player.nationalite, player.championnat]
    if player.poste_secondaire:
        details.append("Dépanne aussi : " + " / ".join(player.poste_secondaire))
    st.caption(" · ".join(d for d in details if d))

    if player.categorie:
        st.write(f"**Style de jeu :** {player.categorie.replace('_', ' ')}")


_STANDINGS_HEADER = ["Rang", "Club", "J", "G", "N", "P", "BP", "BC", "Diff", "Pts"]


def _render_standings_table(table: pd.DataFrame, *, key: str) -> None:
    """Classement (voir `standings.compute_standings`, colonnes Rang/Club/J/
    G/N/P/BP/BC/Diff/Pts) en HTML natif -- pas `st.dataframe` : ses cellules
    sont peintes sur un <canvas> (glide-data-grid), impossible d'y injecter
    les icônes ✔/⚫/✖ ou l'alternance de fond ligne par ligne demandées.
    Chaque ligne reste cliquable (bouton invisible superposé, même principe
    que `_render_team_cell`) pour ouvrir l'effectif du club."""
    st.markdown(_SEASON_STYLE, unsafe_allow_html=True)
    st.markdown('<div class="ms-standings-title">🏆 Classement</div>', unsafe_allow_html=True)

    query = st.text_input("🔍 Filtrer par équipe", key=f"ms_filter_{key}", placeholder="Nom du club...")
    filtered = table[table["Club"].str.contains(query, case=False, na=False)] if query else table

    head = "".join(f"<span>{col}</span>" for col in _STANDINGS_HEADER)
    with st.container(key="ms_standings_wrap"):
        st.markdown(f'<div class="ms-standings-head">{head}</div>', unsafe_allow_html=True)
        if filtered.empty:
            st.markdown('<p style="color:#888888; padding: 10px 14px;">Aucun club ne correspond.</p>', unsafe_allow_html=True)
        for i, (rang, row) in enumerate(filtered.iterrows()):
            row_class = "ms-row-even" if i % 2 == 0 else "ms-row-odd"
            badge = f'<span class="ms-team-badge" style="background:{primary_color(row["Club"])};">{_club_initials(row["Club"])}</span>'
            cells = (
                f'<span class="ms-rank">{rang}</span>'
                f'<span class="ms-club-cell">{badge}{row["Club"]}</span>'
                f'<span>{row["J"]}</span>'
                f'<span class="ms-w"><span class="ms-icon">✔</span> {row["G"]}</span>'
                f'<span class="ms-d"><span class="ms-icon">⚫</span> {row["N"]}</span>'
                f'<span class="ms-l"><span class="ms-icon">✖</span> {row["P"]}</span>'
                f'<span>{row["BP"]}</span>'
                f'<span>{row["BC"]}</span>'
                f'<span>{row["Diff"]:+d}</span>'
                f'<span class="ms-pts">{row["Pts"]}</span>'
            )
            with st.container(key=f"ms_row_{key}_{i}"):
                st.markdown(f'<div class="ms-standings-row {row_class}">{cells}</div>', unsafe_allow_html=True)
                if st.button("", key=f"ms_rowbtn_{key}_{i}"):
                    st.session_state[_OPEN_CLUB_KEY] = row["Club"]
                    st.rerun()


def _render_clickable_club_table(table: pd.DataFrame, *, key: str, hide_index: bool = False) -> None:
    """N'importe quel tableau avec une colonne "Club" (classement, buteurs,
    passeurs, indisponibilités...), rendu avec chaque ligne cliquable --
    ouvre l'effectif du club correspondant (voir `render_club_detail_screen`)."""
    event = st.dataframe(
        table, hide_index=hide_index, width="stretch", on_select="rerun", selection_mode="single-row", key=key
    )
    selected_rows = event.selection.rows if event is not None else []
    if selected_rows:
        st.session_state[_OPEN_CLUB_KEY] = table.iloc[selected_rows[0]]["Club"]
        st.rerun()


# --- Classements et indisponibilités (communs à tous les formats) ----------


def _render_leaderboards(matches: list[Match], *, key_prefix: str = "leaderboard") -> None:
    buteurs, passeurs = compute_leaderboards(matches)
    if buteurs.empty and passeurs.empty:
        return
    st.markdown("### Classements")
    col_buteurs, col_passeurs = st.columns(2)
    with col_buteurs:
        st.markdown("**Buteurs**")
        _render_clickable_club_table(buteurs.head(15), key=f"{key_prefix}_buteurs", hide_index=True)
    with col_passeurs:
        st.markdown("**Passeurs**")
        _render_clickable_club_table(passeurs.head(15), key=f"{key_prefix}_passeurs", hide_index=True)


def _render_availability_panel(suspensions: AvailabilityTracker, injuries: AvailabilityTracker) -> None:
    suspended = suspensions.active_bans()
    injured = injuries.active_bans()
    if not suspended and not injured:
        return

    with st.expander("Suspensions et blessures en cours"):
        col_susp, col_inj = st.columns(2)
        with col_susp:
            st.markdown("**Suspensions**")
            if suspended:
                _render_clickable_club_table(
                    pd.DataFrame(_availability_rows(suspended)), key="availability_suspensions", hide_index=True
                )
            else:
                st.write("Aucune.")
        with col_inj:
            st.markdown("**Blessures**")
            if injured:
                _render_clickable_club_table(
                    pd.DataFrame(_availability_rows(injured)), key="availability_injuries", hide_index=True
                )
            else:
                st.write("Aucune.")


def _availability_rows(bans: list[tuple[str, str, int]]) -> list[dict]:
    return [{"Club": club, "Joueur": player, "Matchs restants": n} for club, player, n in bans]


# --- Routage principal ---------------------------------------------------


if st.session_state.get(_OPEN_MATCH_KEY) is not None:
    render_match_detail_screen(st.session_state[_OPEN_MATCH_KEY])
elif st.session_state.get(_OPEN_CLUB_KEY) is not None:
    render_club_detail_screen(st.session_state[_OPEN_CLUB_KEY])
elif get_custom_competition() is not None:
    render_custom_competition_screen(get_custom_competition())
elif st.session_state.get("perso_wizard_step") is not None:
    render_custom_wizard()
elif get_selected_championnat() is not None:
    render_season_screen()
else:
    render_home_screen()

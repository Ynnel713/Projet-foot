"""Interface Streamlit : simulateur de saison multi-championnats + Compétition Perso."""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd
import streamlit as st

from ligue1sim.clubs import Club, list_championnats, load_all_clubs, load_clubs
from ligue1sim.custom_competition import (
    CompetitionFormat,
    CustomCompetition,
    clear_custom_competition,
    get_custom_competition,
    start_custom_competition,
)
from ligue1sim.coaches import coach_name
from ligue1sim.events import AvailabilityTracker, MatchEvents, PlayerMatchStat, compute_leaderboards
from ligue1sim.groups import QUALIFIERS_PER_GROUP
from ligue1sim.kits import jersey_svg
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
_CHAMPIONNATS_PER_ROW = 4

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

_CLUB_SELECTION_KEY = "perso_selected_clubs"
_CLUB_TABLE_VERSION_KEY = "perso_table_version"
_OPEN_MATCH_KEY = "open_match_detail"
_OPEN_CLUB_KEY = "open_club_detail"

_WIZARD_KEYS = [
    "perso_wizard_step",
    "perso_format",
    "perso_team_count",
    "perso_legs",
    _CLUB_SELECTION_KEY,
    _CLUB_TABLE_VERSION_KEY,
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


_HOME_STYLE = """
<style>
.ls-championnat-flag { display: flex; justify-content: center; font-size: 3rem; line-height: 1.2; }
</style>
"""

_HOME_SPLASH_HEIGHT_VH = 48


def _home_splash_style() -> str:
    if not _HOME_SPLASH_PATH.exists():
        return ""
    splash_b64 = base64.b64encode(_HOME_SPLASH_PATH.read_bytes()).decode()
    return f"""
    <style>
    [data-testid="stAppViewContainer"] {{
        background-image:
            linear-gradient(to bottom, rgba(14, 17, 23, 0) 0%, rgba(14, 17, 23, 0.75) {_HOME_SPLASH_HEIGHT_VH - 10}vh, #0e1117 {_HOME_SPLASH_HEIGHT_VH + 8}vh),
            url("data:image/jpeg;base64,{splash_b64}");
        background-repeat: no-repeat;
        background-size: cover;
        background-position: top center;
        background-attachment: fixed;
    }}
    </style>
    <div style="height: {_HOME_SPLASH_HEIGHT_VH}vh;"></div>
    """


def render_home_screen() -> None:
    st.markdown(_HOME_STYLE, unsafe_allow_html=True)
    st.markdown(_home_splash_style(), unsafe_allow_html=True)

    championnats = list_championnats(CLUBS_PATH)
    for i in range(0, len(championnats), _CHAMPIONNATS_PER_ROW):
        row = championnats[i : i + _CHAMPIONNATS_PER_ROW]
        for col, championnat in zip(st.columns(_CHAMPIONNATS_PER_ROW), row):
            with col:
                _render_championnat_card(championnat)

    st.write("")
    with st.container(border=True):
        col_text, col_button = st.columns([3, 1], vertical_alignment="center")
        with col_text:
            st.markdown("**🏆 Compétition Perso**")
            st.caption("Choisis le format, le nombre d'équipes et les clubs toi-même.")
        with col_button:
            if st.button("Construire", width="stretch", type="primary", key="home_perso"):
                st.session_state["perso_wizard_step"] = 1
                st.rerun()


def _render_championnat_card(championnat: str) -> None:
    with st.container(border=True):
        flag = _CHAMPIONNAT_FLAG.get(championnat, "⚽")
        st.markdown(f'<div class="ls-championnat-flag">{flag}</div>', unsafe_allow_html=True)
        nb_clubs = len(load_clubs(CLUBS_PATH, championnat))
        st.markdown(f"**{championnat}**")
        st.caption(f"{nb_clubs} clubs")
        if st.button("Jouer", width="stretch", key=f"home_{championnat}"):
            select_championnat(championnat)
            st.rerun()


# --- Championnat officiel --------------------------------------------------


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
    st.title(f"⚽ {season.championnat}")

    col_title, col_home, col_reset = st.columns([2, 1, 1])
    with col_title:
        st.subheader(f"Journée {season.current_journee_number} / {season.total_journees}")
    with col_home:
        if st.button(home_label, width="stretch"):
            on_home()
    with col_reset:
        if st.button(reset_label, width="stretch"):
            on_reset()

    journee = season.current_journee

    st.markdown("### Matchs de la journée")
    _render_match_rows(journee.matches)

    col_simulate, col_next = st.columns(2)
    with col_simulate:
        if st.button(
            "Simuler la journée",
            type="primary",
            width="stretch",
            disabled=journee.played,
        ):
            season.simulate_current_journee()
            st.rerun()
    with col_next:
        if st.button(
            "Journée suivante",
            width="stretch",
            disabled=not journee.played or season.current_journee_number >= season.total_journees,
        ):
            season.next_journee()
            st.rerun()

    if season.is_season_over:
        st.success("Saison terminée ! Voici le classement final.")

    st.markdown("### Classement")
    _render_clickable_club_table(season.standings(), key=f"standings_{season.championnat}")

    _render_leaderboards(season.all_matches)
    _render_availability_panel(season.suspensions, season.injuries)


# --- Assistant Compétition Perso ----------------------------------------


def render_custom_wizard() -> None:
    st.title("⚽ Compétition Perso")
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

    all_clubs = load_all_clubs(CLUBS_PATH)
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
    st.title("⚽ Compétition Perso — Championnat + élimination")
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
    for index, match in enumerate(matches):
        col_home, col_score, col_away = st.columns([3, 1, 3])
        with col_home:
            _render_club_link(match.home, key=f"club_link_{id(match)}_{index}_home")
            _render_scorers_caption(match, match.home)
        with col_away:
            _render_club_link(match.away, key=f"club_link_{id(match)}_{index}_away")
            _render_scorers_caption(match, match.away)
        with col_score:
            if match.played and match.events is not None:
                label = f"{match.home_goals} - {match.away_goals}"
                if st.button(label, key=f"match_{id(match)}_{index}", width="stretch"):
                    st.session_state[_OPEN_MATCH_KEY] = match
                    st.rerun()
            elif match.played:
                st.write(f"{match.home_goals} - {match.away_goals}")
            else:
                st.write("—")


def _render_scorers_caption(match: Match, club_name: str) -> None:
    """Buteurs de `club_name` dans ce match, sous le lien vers le club, en
    petit texte du genre "J. Pedro (44'), M. Rogers (77')" -- rien si le club
    n'a pas marqué (ou match pas encore joué)."""
    scorers = _scorers_caption(match, club_name)
    if scorers:
        st.caption(scorers)


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

    if st.button("← Retour"):
        st.session_state.pop(_OPEN_MATCH_KEY, None)
        st.rerun()

    st.title(f"⚽ {match.home} {match.home_goals} - {match.away_goals} {match.away}")

    if events is None:
        st.info("Pas de détails disponibles pour ce match.")
        return

    home_formation = actual_formation_label([s for s in events.home_lineup if s.started])
    away_formation = actual_formation_label([s for s in events.away_lineup if s.started])
    home_coach = coach_name(match.home)
    away_coach = coach_name(match.away)

    col_pitch, col_timeline = st.columns([3, 2])
    with col_pitch:
        _render_pitch(events)
        st.caption(
            f"🏠 **{match.home}**{_coach_suffix(home_coach)} — {home_formation}  ·  "
            f"🚌 **{match.away}**{_coach_suffix(away_coach)} — {away_formation}"
        )
    with col_timeline:
        _render_match_timeline(match, events)

    with st.expander("Compositions complètes et remplaçants", expanded=True):
        st.caption("Clique sur un joueur pour voir sa fiche (poste, âge, nationalité, note...).")
        col_home, col_away = st.columns(2)
        with col_home:
            st.subheader(f"{match.home}{_coach_suffix(home_coach)} — {home_formation}")
            _render_clickable_lineup(events.home_lineup, key=f"lineup_home_{match.home}_{match.away}")
        with col_away:
            st.subheader(f"{match.away}{_coach_suffix(away_coach)} — {away_formation}")
            _render_clickable_lineup(events.away_lineup, key=f"lineup_away_{match.home}_{match.away}")


# --- Vue "stade" (terrain + fil du match) ---------------------------------

_PITCH_STYLE = """
<style>
.ls-pitch {
    position: relative;
    width: 100%;
    aspect-ratio: 2 / 3;
    border-radius: 10px;
    border: 2px solid rgba(255,255,255,0.4);
    overflow: hidden;
    background:
        repeating-linear-gradient(180deg, #2e7d32 0%, #2e7d32 10%, #358a38 10%, #358a38 20%);
    margin-bottom: 0.5rem;
}
.ls-halfway {
    position: absolute; left: 0; top: 50%; width: 100%; height: 2px;
    background: rgba(255,255,255,0.55); transform: translateY(-50%);
}
.ls-circle-mid {
    position: absolute; left: 50%; top: 50%; width: 22%; height: 14.7%;
    border: 2px solid rgba(255,255,255,0.55); border-radius: 50%;
    transform: translate(-50%, -50%);
}
.ls-goalbox {
    position: absolute; left: 50%; width: 34%; height: 7%;
    border: 2px solid rgba(255,255,255,0.55); border-top: none; transform: translateX(-50%);
}
.ls-goalbox-top { top: 0; border-top: none; border-bottom: 2px solid rgba(255,255,255,0.55); }
.ls-goalbox-bottom { bottom: 0; }
.ls-token {
    position: absolute; transform: translate(-50%, -50%);
    display: flex; flex-direction: column; align-items: center; width: 92px;
}
.ls-badges {
    font-size: 13px; line-height: 1; margin-bottom: 3px; white-space: nowrap;
    text-shadow: 0 1px 2px rgba(0,0,0,0.7);
}
.ls-jersey-wrap {
    position: relative; width: 44px; height: 44px;
    filter: drop-shadow(0 1px 3px rgba(0,0,0,0.5));
}
.ls-rating-badge {
    position: absolute; right: -7px; bottom: -6px;
    width: 22px; height: 22px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-weight: 700; font-size: 10.5px; color: #fff;
    border: 2px solid rgba(0,0,0,0.3); box-shadow: 0 1px 3px rgba(0,0,0,0.5);
}
.ls-rating-badge.ls-circle-good { background: #1e8e3e; }
.ls-rating-badge.ls-circle-avg { background: #c99a12; }
.ls-rating-badge.ls-circle-poor { background: #c0392b; }
.ls-name {
    font-size: 12px; font-weight: 600; color: #fff; margin-top: 4px;
    white-space: nowrap; text-shadow: 0 1px 2px rgba(0,0,0,0.85);
}
.ls-timeline {
    max-height: 720px; overflow-y: auto; padding-right: 4px;
}
.ls-timeline-row {
    display: flex; gap: 10px; padding: 8px 6px; font-size: 14.5px;
    border-bottom: 1px solid rgba(128,128,128,0.25);
    border-left: 3px solid transparent;
}
.ls-timeline-minute {
    flex: 0 0 36px; font-weight: 700; opacity: 0.75;
}
.ls-timeline-row--goal {
    padding: 10px 8px; font-size: 16.5px; font-weight: 700;
    background: rgba(30,142,62,0.16);
    border-left: 3px solid #1e8e3e;
    border-radius: 4px;
}
.ls-timeline-row--goal .ls-timeline-minute { opacity: 1; color: #1e8e3e; }
.ls-timeline-row--minor { opacity: 0.72; font-size: 13.5px; }
</style>
"""


def _render_pitch(events: MatchEvents) -> None:
    st.markdown(_PITCH_STYLE, unsafe_allow_html=True)

    home_starters = [s for s in events.home_lineup if s.started]
    away_starters = [s for s in events.away_lineup if s.started]
    # L'équipe à domicile en haut du terrain (gardien près du bord supérieur,
    # attaque vers le bas) ; l'équipe à l'extérieur en bas (inverse).
    placed = place_starting_xi(home_starters, attacking_up=False) + place_starting_xi(
        away_starters, attacking_up=True
    )

    subbed_off_minute = {(sub.club_name, sub.player_off): sub.minute for sub in events.substitutions}
    tokens_html = "".join(_player_token_html(p, subbed_off_minute) for p in placed)

    st.markdown(
        f"""
        <div class="ls-pitch">
            <div class="ls-halfway"></div>
            <div class="ls-circle-mid"></div>
            <div class="ls-goalbox ls-goalbox-top"></div>
            <div class="ls-goalbox ls-goalbox-bottom"></div>
            {tokens_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _player_token_html(placed: PlacedPlayer, subbed_off_minute: dict[tuple[str, str], int]) -> str:
    stat = placed.stat
    minute_off = subbed_off_minute.get((stat.club_name, stat.player_name))
    badges = _player_badges(stat, minute_off)
    badges_html = f'<div class="ls-badges">{badges}</div>' if badges else ""
    badge_id = f"{stat.club_name}-{stat.player_name}"
    jersey = jersey_svg(stat.club_name, size=44, badge_id=badge_id)
    return (
        f'<div class="ls-token" style="left:{placed.x:.1f}%; top:{placed.y:.1f}%;">'
        f"{badges_html}"
        f'<div class="ls-jersey-wrap">'
        f"{jersey}"
        f'<div class="ls-rating-badge ls-circle-{_rating_tier(stat.rating)}">{stat.rating:.1f}</div>'
        f"</div>"
        f'<div class="ls-name">{_short_name(stat.player_name)}</div>'
        f"</div>"
    )


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
    if rating >= 7.0:
        return "good"
    if rating >= 6.0:
        return "avg"
    return "poor"


def _short_name(full_name: str) -> str:
    parts = full_name.split()
    if len(parts) <= 1:
        return full_name
    return f"{parts[0][0]}. {parts[-1]}"


def _render_match_timeline(match: Match, events: MatchEvents) -> None:
    st.markdown("#### 📋 Fil du match")
    entries = _match_timeline_entries(match, events)
    if not entries:
        st.caption("Aucun fait de jeu à signaler.")
        return
    rows = "".join(
        f'<div class="ls-timeline-row ls-timeline-row--{kind}">'
        f'<div class="ls-timeline-minute">{minute}\'</div><div>{html}</div></div>'
        for minute, kind, html in entries
    )
    st.markdown(f'<div class="ls-timeline">{rows}</div>', unsafe_allow_html=True)


def _match_timeline_entries(match: Match, events: MatchEvents) -> list[tuple[int, str, str]]:
    entries: list[tuple[int, str, str]] = []

    running_score = {match.home: 0, match.away: 0}
    for goal in sorted(events.goals, key=lambda g: g.minute):
        running_score[goal.club_name] = running_score.get(goal.club_name, 0) + 1
        score = f"{running_score.get(match.home, 0)}-{running_score.get(match.away, 0)}"
        penalty_text = " (penalty)" if goal.penalty else ""
        assist_text = f" — passe déc. : {goal.assist}" if goal.assist else ""
        entries.append(
            (
                goal.minute,
                "goal",
                f"⚽ <b>{goal.scorer}</b> ({goal.club_name}){penalty_text} · {score}{assist_text}",
            )
        )

    card_icons = {"direct": "🟥", "second_yellow": "🟨🟥", "yellow": "🟨"}
    for card in events.cards:
        entries.append(
            (card.minute, "minor", f"{card_icons[card.card_type]} <b>{card.player}</b> ({card.club_name})")
        )

    for sub in events.substitutions:
        entries.append(
            (
                sub.minute,
                "minor",
                f"🔄 {sub.club_name} : <b>{sub.player_on}</b> entre à la place de {sub.player_off}",
            )
        )

    for injury in events.injuries:
        entries.append((injury.minute, "minor", f"🚑 <b>{injury.player}</b> ({injury.club_name}) — blessure"))

    for missed in events.penalties_missed:
        entries.append((missed.minute, "minor", f"❌ Penalty manqué par <b>{missed.player}</b> ({missed.club_name})"))

    entries.sort(key=lambda e: e[0])
    return entries


def _render_clickable_lineup(stats: list[PlayerMatchStat], *, key: str) -> None:
    """Tableau de compo dont chaque ligne (chaque joueur) est cliquable :
    sélectionner une ligne affiche la fiche du joueur juste en dessous (voir
    `_render_player_card`)."""
    event = st.dataframe(
        _lineup_rows(stats),
        hide_index=True,
        width="stretch",
        on_select="rerun",
        selection_mode="single-row",
        key=key,
    )
    selected_rows = event.selection.rows if event is not None else []
    if selected_rows:
        _render_player_card(stats[selected_rows[0]])


def _lineup_rows(stats: list[PlayerMatchStat]) -> list[dict]:
    return [
        {
            "Joueur": s.player_name,
            "Poste": s.poste,
            "Statut": "Titulaire" if s.started else "Entrant",
            "Buts": s.goals,
            "Passes D.": s.assists,
            "Carton": _card_label(s),
            "Note /10": s.rating,
        }
        for s in stats
    ]


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


def _render_club_link(club_name: str, *, key: str) -> None:
    """Bouton discret (style lien) qui ouvre l'effectif du club -- même
    principe que les scores cliquables de `_render_match_rows`, mais stocke
    le NOM du club plutôt que l'objet : un nom de club peut apparaître dans
    des contextes très divers (classement, buteurs, compo...), alors qu'un
    seul et même `Club` fait référence pour tous (voir `_find_club`)."""
    if st.button(club_name, key=key, type="tertiary"):
        st.session_state[_OPEN_CLUB_KEY] = club_name
        st.rerun()


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

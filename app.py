"""Interface Streamlit : simulateur de saison multi-championnats + Compétition Perso."""

from __future__ import annotations

from typing import Callable

import numpy as np
import pandas as pd
import streamlit as st

from ligue1sim.clubs import list_championnats, load_all_clubs, load_clubs
from ligue1sim.custom_competition import (
    CompetitionFormat,
    CustomCompetition,
    clear_custom_competition,
    get_custom_competition,
    start_custom_competition,
)
from ligue1sim.events import AvailabilityTracker, PlayerMatchStat, compute_leaderboards
from ligue1sim.groups import QUALIFIERS_PER_GROUP
from ligue1sim.knockout import Round
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

st.set_page_config(page_title="Simulateur de championnat", page_icon="⚽", layout="centered")

_CLUB_SELECTION_KEY = "perso_selected_clubs"
_CLUB_TABLE_VERSION_KEY = "perso_table_version"
_OPEN_MATCH_KEY = "open_match_detail"

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


def render_home_screen() -> None:
    st.title("⚽ Simulateur de championnat 2026-2027")
    st.subheader("Choisis un championnat à simuler")
    for championnat in list_championnats(CLUBS_PATH):
        nb_clubs = len(load_clubs(CLUBS_PATH, championnat))
        if st.button(f"{championnat} ({nb_clubs} clubs)", width="stretch"):
            select_championnat(championnat)
            st.rerun()

    st.divider()
    st.subheader("Ou construis ta propre compétition")
    if st.button("🏆 Compétition Perso", width="stretch"):
        st.session_state["perso_wizard_step"] = 1
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
    st.dataframe(season.standings(), width="stretch")

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
        st.dataframe(group.standings(), width="stretch")
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
            st.write(match.home)
        with col_away:
            st.write(match.away)
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


def render_match_detail_screen(match: Match) -> None:
    events = match.events

    if st.button("← Retour"):
        st.session_state.pop(_OPEN_MATCH_KEY, None)
        st.rerun()

    st.title(f"⚽ {match.home} {match.home_goals} - {match.away_goals} {match.away}")

    if events is None:
        st.info("Pas de détails disponibles pour ce match.")
        return

    col_home, col_away = st.columns(2)
    with col_home:
        st.subheader(f"{match.home} — {events.home_formation}")
        st.dataframe(_lineup_rows(events.home_lineup), hide_index=True, width="stretch")
    with col_away:
        st.subheader(f"{match.away} — {events.away_formation}")
        st.dataframe(_lineup_rows(events.away_lineup), hide_index=True, width="stretch")

    st.markdown("### Buteurs")
    if events.goals:
        for goal in events.goals:
            assist_text = f" (passe décisive : {goal.assist})" if goal.assist else ""
            st.write(f"⚽ **{goal.scorer}** ({goal.club_name}){assist_text}")
    else:
        st.write("Aucun but inscrit.")

    if events.substitutions:
        st.markdown("### Remplacements")
        for sub in events.substitutions:
            st.write(f"🔄 {sub.club_name} : **{sub.player_on}** entre à la place de {sub.player_off}")


def _lineup_rows(stats: list[PlayerMatchStat]) -> list[dict]:
    return [
        {
            "Joueur": s.player_name,
            "Poste": s.poste,
            "Statut": "Titulaire" if s.started else "Entrant",
            "Buts": s.goals,
            "Passes D.": s.assists,
            "Carton": _card_label(s),
            "Note": s.rating,
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


# --- Classements et indisponibilités (communs à tous les formats) ----------


def _render_leaderboards(matches: list[Match]) -> None:
    buteurs, passeurs = compute_leaderboards(matches)
    if buteurs.empty and passeurs.empty:
        return
    st.markdown("### Classements")
    col_buteurs, col_passeurs = st.columns(2)
    with col_buteurs:
        st.markdown("**Buteurs**")
        st.dataframe(buteurs.head(15), hide_index=True, width="stretch")
    with col_passeurs:
        st.markdown("**Passeurs**")
        st.dataframe(passeurs.head(15), hide_index=True, width="stretch")


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
                st.dataframe(_availability_rows(suspended), hide_index=True, width="stretch")
            else:
                st.write("Aucune.")
        with col_inj:
            st.markdown("**Blessures**")
            if injured:
                st.dataframe(_availability_rows(injured), hide_index=True, width="stretch")
            else:
                st.write("Aucune.")


def _availability_rows(bans: list[tuple[str, str, int]]) -> list[dict]:
    return [{"Club": club, "Joueur": player, "Matchs restants": n} for club, player, n in bans]


# --- Routage principal ---------------------------------------------------


if st.session_state.get(_OPEN_MATCH_KEY) is not None:
    render_match_detail_screen(st.session_state[_OPEN_MATCH_KEY])
elif get_custom_competition() is not None:
    render_custom_competition_screen(get_custom_competition())
elif st.session_state.get("perso_wizard_step") is not None:
    render_custom_wizard()
elif get_selected_championnat() is not None:
    render_season_screen()
else:
    render_home_screen()

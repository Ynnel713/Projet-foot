"""Cycle de vie d'une compétition : création, simulation journée par journée
ou d'un coup, classement, matchs.

Format LEAGUE (championnats officiels et Compétition Perso en championnat
pur) et HYBRID (Ligue des Champions -- poules puis élimination directe).
KNOCKOUT seul (Compétition Perso en élimination directe pure) pas encore
branché ici -- le moteur le gère déjà (`CustomCompetition`), il reste à
écrire l'équivalent HTTP de `simulate_bracket_round`/`advance_bracket_round`
hors contexte HYBRID.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ligue1sim.champions_league import start_champions_league
from ligue1sim.clubs import load_clubs, list_perso_clubs
from ligue1sim.custom_competition import CompetitionFormat, CustomCompetition
from ligue1sim.nations import load_national_teams
from ligue1sim.season import CLUBS_PATH

from api import store
from api.schemas import (
    BracketOut,
    CompetitionStatus,
    CreateCompetitionRequest,
    GroupsStatusOut,
    MatchOut,
    PitchViewOut,
    SimulateResponse,
)
from api.serializers import (
    bracket_out,
    groups_status,
    match_out,
    pitch_view,
    standings as serialize_standings,
    status as serialize_status,
)

router = APIRouter(prefix="/competitions", tags=["competitions"])


def _get_or_404(comp_id: str) -> CustomCompetition:
    try:
        return store.get(comp_id)
    except KeyError:
        raise HTTPException(404, "Compétition introuvable.")


@router.post("", response_model=CompetitionStatus)
def create_competition(req: CreateCompetitionRequest) -> CompetitionStatus:
    if req.source == "league":
        clubs = load_clubs(CLUBS_PATH, req.championnat)
    else:
        # Clubs ET sélections nationales dans le même vivier, sans
        # restriction (voir app._perso_club_pool -- même comportement côté
        # Streamlit) : rien n'empêche d'aligner un club et une sélection
        # dans la même compétition perso.
        pool = {c.name: c.as_club() for c in list_perso_clubs(CLUBS_PATH)}
        pool.update({t.name: t for t in load_national_teams(CLUBS_PATH)})
        missing = [name for name in req.club_names if name not in pool]
        if missing:
            raise HTTPException(422, f"Clubs/sélections inconnus : {missing}")
        clubs = [pool[name] for name in req.club_names]

    # `label` : nom d'affichage de la compétition (voir CustomCompetition) --
    # sans lui, `competition.season.championnat` vaut toujours "Compétition
    # Perso" en interne, même pour un championnat officiel.
    label = req.championnat if req.source == "league" else None
    competition = CustomCompetition(format=req.format, legs=req.legs, clubs=clubs, label=label)
    comp_id = store.create(competition)
    return serialize_status(comp_id, competition)


@router.post("/champions-league", response_model=CompetitionStatus)
def create_champions_league() -> CompetitionStatus:
    """Nouvelle Ligue des Champions : 36 clubs, poules tirées au sort par
    chapeau -- voir `champions_league.start_champions_league`."""
    competition = start_champions_league(CLUBS_PATH)
    comp_id = store.create(competition)
    return serialize_status(comp_id, competition)


@router.get("/{comp_id}", response_model=CompetitionStatus)
def get_competition(comp_id: str) -> CompetitionStatus:
    return serialize_status(comp_id, _get_or_404(comp_id))


@router.post("/{comp_id}/simulate-current", response_model=SimulateResponse)
def simulate_current(comp_id: str) -> SimulateResponse:
    """Simule la journée courante SANS avancer -- un bouton qui alterne entre
    "Simuler la journée" (cet endpoint) et "Journée suivante →" (`/advance`
    ci-dessous), un seul actif à la fois selon que la journée courante a déjà
    été jouée. Voir `app._render_match_simulation_screen` pour la même
    logique côté Streamlit."""
    competition = _get_or_404(comp_id)
    if competition.format != CompetitionFormat.LEAGUE:
        raise HTTPException(501, "Seul le format LEAGUE est simulable pour le moment.")
    season = competition.season
    if season.current_journee.played:
        raise HTTPException(409, "Cette journée est déjà jouée -- utilise /advance.")

    journee = season.current_journee
    season.simulate_current_journee()

    prev_ranks = store.previous_ranks(comp_id)
    rows = serialize_standings(competition, prev_ranks)
    store.update_ranks(comp_id, {row.club: row.rank for row in rows})

    return SimulateResponse(
        status=serialize_status(comp_id, competition),
        matches_played=[match_out(m) for m in journee.matches],
        standings=rows,
    )


@router.post("/{comp_id}/advance", response_model=SimulateResponse)
def advance(comp_id: str) -> SimulateResponse:
    """Avance à la journée suivante SANS simuler -- voir `simulate_current`
    ci-dessus pour le pendant "simuler"."""
    competition = _get_or_404(comp_id)
    if competition.format != CompetitionFormat.LEAGUE:
        raise HTTPException(501, "Seul le format LEAGUE est simulable pour le moment.")
    season = competition.season
    if not season.current_journee.played:
        raise HTTPException(409, "La journée courante n'est pas encore jouée -- utilise /simulate-current.")
    if competition.is_over:
        raise HTTPException(409, "Compétition déjà terminée.")

    season.next_journee()
    journee = season.current_journee

    return SimulateResponse(
        status=serialize_status(comp_id, competition),
        # Pas encore joués (played=False, home_goals/away_goals=None) -- le
        # calendrier à venir de la nouvelle journée courante, pour que le
        # client puisse l'afficher AVANT de simuler (voir MatchRow, qui gère
        # déjà ce cas -- même sérialisation que /matches).
        matches_played=[match_out(m) for m in journee.matches],
        standings=serialize_standings(competition, store.previous_ranks(comp_id)),
    )


@router.post("/{comp_id}/simulate-all", response_model=SimulateResponse)
def simulate_all(comp_id: str) -> SimulateResponse:
    competition = _get_or_404(comp_id)
    if competition.format != CompetitionFormat.LEAGUE:
        raise HTTPException(501, "Seul le format LEAGUE est simulable pour le moment.")

    all_played: list[MatchOut] = []
    season = competition.season
    while not season.is_season_over:
        journee = season.current_journee
        season.simulate_current_journee()
        all_played += [match_out(m) for m in journee.matches]
        if not season.is_season_over:
            season.next_journee()

    rows = serialize_standings(competition, {})
    store.update_ranks(comp_id, {row.club: row.rank for row in rows})

    return SimulateResponse(
        status=serialize_status(comp_id, competition),
        matches_played=all_played,
        standings=rows,
    )


@router.get("/{comp_id}/standings", response_model=list)
def get_standings(comp_id: str):
    competition = _get_or_404(comp_id)
    return serialize_standings(competition, store.previous_ranks(comp_id))


@router.get("/{comp_id}/matches", response_model=list[MatchOut])
def get_matches(comp_id: str, journee: int | None = None) -> list[MatchOut]:
    competition = _get_or_404(comp_id)
    season = competition.season
    if journee is not None:
        if not (1 <= journee <= season.total_journees):
            raise HTTPException(422, f"Journée hors bornes (1-{season.total_journees}).")
        matches = season.calendar[journee - 1].matches
    else:
        matches = season.all_matches
    return [match_out(m) for m in matches]


@router.get("/{comp_id}/pitch", response_model=PitchViewOut)
def get_pitch_view(comp_id: str, journee: int, home: str, away: str) -> PitchViewOut:
    """Placement des deux compositions sur un terrain partagé (vue "stade"),
    pour un match déjà joué -- voir `pitch_layout.place_starting_xi`."""
    competition = _get_or_404(comp_id)
    season = competition.season
    if not (1 <= journee <= season.total_journees):
        raise HTTPException(422, f"Journée hors bornes (1-{season.total_journees}).")

    match = next(
        (m for m in season.calendar[journee - 1].matches if m.home == home and m.away == away),
        None,
    )
    if match is None:
        raise HTTPException(404, "Match introuvable pour cette journée.")
    if not match.played or match.events is None:
        raise HTTPException(409, "Ce match n'a pas encore été joué (ou n'a pas d'effectif réel).")

    return pitch_view(match)


# --- Phase de poules + élimination directe (HYBRID -- Ligue des Champions) ---


def _require_hybrid(competition: CustomCompetition) -> None:
    if competition.format != CompetitionFormat.HYBRID:
        raise HTTPException(501, "Ce format n'a pas de phase de poules.")


@router.get("/{comp_id}/groups", response_model=GroupsStatusOut)
def get_groups(comp_id: str) -> GroupsStatusOut:
    competition = _get_or_404(comp_id)
    _require_hybrid(competition)
    return groups_status(competition)


@router.post("/{comp_id}/groups/simulate-matchday", response_model=GroupsStatusOut)
def simulate_groups_matchday(comp_id: str) -> GroupsStatusOut:
    """Simule la prochaine journée de TOUTES les poules à la fois (un seul
    compteur de journée partagé -- voir `CustomCompetition.simulate_groups_matchday`),
    pas poule par poule."""
    competition = _get_or_404(comp_id)
    _require_hybrid(competition)
    if competition.groups_complete:
        raise HTTPException(409, "Phase de poules déjà terminée.")
    competition.simulate_groups_matchday()
    return groups_status(competition)


@router.post("/{comp_id}/knockout/start", response_model=BracketOut)
def start_knockout(comp_id: str) -> BracketOut:
    competition = _get_or_404(comp_id)
    _require_hybrid(competition)
    if not competition.groups_complete:
        raise HTTPException(409, "Phase de poules pas encore terminée.")
    if competition.bracket is not None:
        raise HTTPException(409, "Phase à élimination déjà commencée.")
    competition.start_knockout_from_groups()
    return bracket_out(competition.bracket)


@router.get("/{comp_id}/bracket", response_model=BracketOut)
def get_bracket(comp_id: str) -> BracketOut:
    competition = _get_or_404(comp_id)
    _require_hybrid(competition)
    if competition.bracket is None:
        raise HTTPException(409, "Phase à élimination pas encore commencée -- utilise /knockout/start.")
    return bracket_out(competition.bracket)


@router.post("/{comp_id}/bracket/simulate-round", response_model=BracketOut)
def simulate_bracket_round(comp_id: str) -> BracketOut:
    competition = _get_or_404(comp_id)
    _require_hybrid(competition)
    if competition.bracket is None:
        raise HTTPException(409, "Phase à élimination pas encore commencée -- utilise /knockout/start.")
    if competition.bracket.current_round.played:
        raise HTTPException(409, "Ce tour est déjà joué -- utilise /bracket/advance.")
    competition.simulate_bracket_round()
    return bracket_out(competition.bracket)


@router.post("/{comp_id}/bracket/advance", response_model=BracketOut)
def advance_bracket(comp_id: str) -> BracketOut:
    competition = _get_or_404(comp_id)
    _require_hybrid(competition)
    if competition.bracket is None:
        raise HTTPException(409, "Phase à élimination pas encore commencée -- utilise /knockout/start.")
    if not competition.bracket.current_round.played:
        raise HTTPException(409, "Ce tour n'est pas encore joué -- utilise /bracket/simulate-round.")
    competition.advance_bracket_round()
    return bracket_out(competition.bracket)

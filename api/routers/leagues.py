"""Listes de référence : championnats officiels et vivier de clubs
disponibles pour la Compétition Perso."""

from __future__ import annotations

from fastapi import APIRouter

from ligue1sim.clubs import list_championnats, list_perso_clubs, load_clubs
from ligue1sim.lineup import club_strength
from ligue1sim.nations import confederation as national_team_confederation
from ligue1sim.nations import load_national_teams
from ligue1sim.season import CLUBS_PATH

from api.schemas import ClubSummary, LeagueSummary, NationSummary

router = APIRouter(tags=["leagues"])

_COUNTRY_CODE = {
    "Ligue 1": "fr",
    "Premier League": "gb-eng",
    "Championship": "gb-eng",
    "LaLiga": "es",
    "Bundesliga": "de",
    "Serie A": "it",
    "Eredivisie": "nl",
    "Liga Portugal": "pt",
    "Jupiler Pro League": "be",
}


@router.get("/leagues", response_model=list[LeagueSummary])
def list_leagues() -> list[LeagueSummary]:
    return [
        LeagueSummary(
            championnat=championnat,
            nb_clubs=len(load_clubs(CLUBS_PATH, championnat)),
            country_code=_COUNTRY_CODE.get(championnat),
        )
        for championnat in list_championnats(CLUBS_PATH)
    ]


@router.get("/clubs", response_model=list[ClubSummary])
def list_perso_club_pool() -> list[ClubSummary]:
    """Vivier de la Compétition Perso (voir `clubs.list_perso_clubs` pour le
    filtre) -- inclut la force de chaque club pour l'étoile côté UI."""
    return [
        ClubSummary(name=c.name, championnat=c.championnat, strength=club_strength(c.as_club()))
        for c in list_perso_clubs(CLUBS_PATH)
    ]


@router.get("/nations", response_model=list[NationSummary])
def list_nations() -> list[NationSummary]:
    """Sélections nationales complètes (23/23), groupées par confédération --
    pour l'écran dédié "Sélections nationales" ET pour la Compétition Perso,
    qui mélange clubs et sélections sans restriction (voir
    `competitions.create_competition`)."""
    return [
        NationSummary(
            name=team.name,
            confederation=national_team_confederation(CLUBS_PATH, team.name),
            strength=club_strength(team),
        )
        for team in load_national_teams(CLUBS_PATH)
    ]

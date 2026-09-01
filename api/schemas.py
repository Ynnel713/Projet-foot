"""Modèles Pydantic exposés par l'API -- indépendants du moteur (voir
api/serializers.py pour la conversion depuis les objets ligue1sim)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, model_validator


class LeagueSummary(BaseModel):
    championnat: str
    nb_clubs: int
    country_code: str | None = None


class ClubSummary(BaseModel):
    name: str
    championnat: str
    strength: float


class NationSummary(BaseModel):
    name: str
    confederation: str
    strength: float


class CreateCompetitionRequest(BaseModel):
    format: Literal["LEAGUE"] = "LEAGUE"  # KNOCKOUT pas encore branché côté API -- HYBRID : voir /champions-league
    legs: Literal[1, 2, 4] = 2
    source: Literal["league", "custom"]
    championnat: str | None = None
    club_names: list[str] | None = None

    @model_validator(mode="after")
    def _check_source(self) -> "CreateCompetitionRequest":
        if self.source == "league" and not self.championnat:
            raise ValueError("championnat requis quand source='league'")
        if self.source == "custom" and not self.club_names:
            raise ValueError("club_names requis quand source='custom'")
        return self


class ScorerOut(BaseModel):
    club: str
    player: str
    minute: int
    penalty: bool


class MatchOut(BaseModel):
    home: str
    away: str
    home_goals: int | None
    away_goals: int | None
    played: bool
    summary: str | None = None
    scorers: list[ScorerOut] = []


class StandingRow(BaseModel):
    rank: int
    rank_change: int
    club: str
    played: int
    won: int
    drawn: int
    lost: int
    goals_for: int
    goals_against: int
    goal_diff: int
    points: int


class CompetitionStatus(BaseModel):
    id: str
    format: str
    championnat: str | None
    is_over: bool
    current_journee: int | None
    current_journee_played: bool = False
    total_journees: int | None
    champion: str | None


class SimulateResponse(BaseModel):
    status: CompetitionStatus
    matches_played: list[MatchOut]
    standings: list[StandingRow]


class PlacedPlayerOut(BaseModel):
    name: str
    poste: str
    x: float
    y: float
    rating: float
    goals: int
    yellow_cards: int
    red_card: bool
    started: bool


class PitchViewOut(BaseModel):
    home: str
    away: str
    home_goals: int
    away_goals: int
    home_formation: str
    away_formation: str
    home_players: list[PlacedPlayerOut]
    away_players: list[PlacedPlayerOut]


class GroupOut(BaseModel):
    name: str
    is_complete: bool
    standings: list[StandingRow]
    current_matches: list[MatchOut]  # résultats de la dernière journée de poule jouée (vide si aucune encore)


class GroupsStatusOut(BaseModel):
    groups: list[GroupOut]
    groups_matchday: int  # journées de poules déjà jouées
    groups_complete: bool
    knockout_started: bool


class TieOut(BaseModel):
    home: str
    away: str | None  # None uniquement pour une exemption ("bye")
    legs: list[MatchOut]  # chaque manche jouée (aller/retour), dans l'ordre -- vide si bye ou pas encore commencée
    home_goals: int | None  # score agrégé sur toutes les manches, une fois joué
    away_goals: int | None
    winner: str | None
    is_bye: bool
    decided_by_penalties: bool = False


class RoundOut(BaseModel):
    number: int
    ties: list[TieOut]
    played: bool


class BracketOut(BaseModel):
    rounds: list[RoundOut]
    is_complete: bool
    champion: str | None


class LeaderboardRow(BaseModel):
    player: str
    club: str
    count: int


class LeaderboardsOut(BaseModel):
    scorers: list[LeaderboardRow]
    assists: list[LeaderboardRow]

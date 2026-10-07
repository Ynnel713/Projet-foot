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
    # KNOCKOUT (28/09/2026, assistant Compétition Perso) et HYBRID ("championnat
    # + élimination" personnalisé, sans poules préconstruites -- distinct de
    # /champions-league et /world-cup qui restent leurs propres routes dédiées
    # avec tirage par chapeau) sont désormais acceptés ici.
    format: Literal["LEAGUE", "KNOCKOUT", "HYBRID"] = "LEAGUE"
    legs: Literal[1, 2, 4] = 2
    # Manches par confrontation à élimination directe (hors finale) / pour la
    # finale seule -- `None` reprend `legs` (voir CustomCompetition._round_legs).
    # Sans objet pour format="LEAGUE" (pas de tableau).
    knockout_legs: Literal[1, 2, 4] | None = None
    final_legs: Literal[1, 2, 4] | None = None
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


class BenchPlayerOut(BaseModel):
    name: str
    poste: str
    # `None` pour un remplaçant jamais entré en jeu (pas de note de match --
    # voir `rating` de PlayerMatchStat, qui n'existe que pour les joueurs
    # ayant réellement joué). `entered_minute` : minute d'entrée si ce
    # remplaçant a été utilisé pendant le match, `None` sinon (retour terrain
    # du 28/09/2026 -- "reste de l'effectif" avec entrées en jeu en
    # surbrillance, voir PitchView.jsx).
    rating: float | None = None
    entered_minute: int | None = None


class UnavailablePlayerOut(BaseModel):
    name: str
    poste: str
    reason: Literal["blessure", "suspension"]


class TeamStatsOut(BaseModel):
    """Possession/tirs/tirs cadrés/xG d'une équipe pour un match (voir
    ligue1sim.match_stats) -- dérivés du score et du lambda déjà décidés par
    le moteur, jamais l'inverse."""

    possession: float
    shots: int
    shots_on_target: int
    xg: float


class TextPartOut(BaseModel):
    """Morceau de texte d'un événement live ; `player` : nom de joueur, à mettre en valeur côté UI."""

    text: str
    player: bool = False


class LiveEventOut(BaseModel):
    """Événement du fil « commentaire en direct » (voir api.live_commentary) : les événements réels du match, en texte français."""

    minute: int
    kind: Literal[
        "start", "goal", "penalty_missed", "yellow", "second_yellow", "red", "sub", "shot_off", "save", "defense", "end"
    ]
    title: str
    side: Literal["home", "away"] | None = None
    club: str | None = None
    parts: list[TextPartOut]


class PitchViewOut(BaseModel):
    home: str
    away: str
    home_goals: int
    away_goals: int
    home_formation: str
    away_formation: str
    home_players: list[PlacedPlayerOut]
    away_players: list[PlacedPlayerOut]
    home_bench: list[BenchPlayerOut]
    away_bench: list[BenchPlayerOut]
    home_unavailable: list[UnavailablePlayerOut]
    away_unavailable: list[UnavailablePlayerOut]
    home_coach: str | None
    away_coach: str | None
    home_stats: TeamStatsOut | None = None
    away_stats: TeamStatsOut | None = None
    # Fil live du match (buts, cartons, remplacements...), chronologique -- vide pour un match sans événements.
    live: list[LiveEventOut] = []


class GroupOut(BaseModel):
    name: str
    is_complete: bool
    standings: list[StandingRow]
    current_matches: list[MatchOut]  # résultats de la dernière journée de poule jouée (vide si aucune encore)
    next_matches: list[MatchOut] = []  # matchs de la PROCHAINE journée (pas encore joués) : le bouton LIVE les simule puis les ouvre en direct


class GroupsStatusOut(BaseModel):
    groups: list[GroupOut]
    groups_matchday: int  # journées de poules déjà jouées
    groups_complete: bool
    knockout_started: bool
    # Ligue des Champions : la « poule » est la phase de ligue (36 clubs, 8 journées) ; `direct_spots` qualifiés directs en 8es,
    # `playoff_spots` en barrages (zones de qualification de l'UI). 0 pour les poules classiques (2 premiers qualifiés).
    league_phase: bool = False
    direct_spots: int = 0
    playoff_spots: int = 0


class TieOut(BaseModel):
    home: str
    away: str | None  # None uniquement pour une exemption ("bye")
    legs: list[MatchOut]  # chaque manche jouée (aller/retour), dans l'ordre -- vide si bye ou pas encore commencée
    home_goals: int | None  # score agrégé sur toutes les manches, une fois joué
    away_goals: int | None
    winner: str | None
    is_bye: bool
    decided_by_penalties: bool = False
    penalty_score: tuple[int, int] | None = None  # (vainqueur, perdant) -- voir Tie.penalty_score


class RoundOut(BaseModel):
    number: int
    ties: list[TieOut]
    played: bool
    label: str | None = None  # libellé imposé (« Barrages » de la Ligue des Champions) ; None : déduit du nombre de confrontations


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


class PlayerOut(BaseModel):
    id: int | None
    name: str
    poste: str
    poste_secondaire: list[str] = []
    postes_fm: str | None = None
    age: int
    note: float
    nationalite: str
    pied: str | None = None
    taille_fm: int | None = None
    weak_foot: float | None = None
    preferred_moves: str | None = None
    categorie: str | None = None
    valeur_marchande: float | None = None
    attributes: dict[str, int] | None = None
    photo_url: str | None = None


class RosterOut(BaseModel):
    club: str
    championnat: str
    color: str
    note: float
    age_moyen: float
    valeur_totale: float | None = None
    players: list[PlayerOut]

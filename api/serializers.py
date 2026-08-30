"""Conversion des objets du moteur (ligue1sim) vers les schémas Pydantic
exposés par l'API."""

from __future__ import annotations

from ligue1sim.custom_competition import CustomCompetition
from ligue1sim.groups import Group
from ligue1sim.knockout import Bracket, Tie
from ligue1sim.pitch_layout import PlacedPlayer, actual_formation_label, place_starting_xi
from ligue1sim.schedule import Match

from api.schemas import (
    BracketOut,
    CompetitionStatus,
    GroupOut,
    GroupsStatusOut,
    MatchOut,
    PitchViewOut,
    PlacedPlayerOut,
    RoundOut,
    StandingRow,
    TieOut,
)


def match_out(match: Match) -> MatchOut:
    return MatchOut(
        home=match.home,
        away=match.away,
        home_goals=match.home_goals,
        away_goals=match.away_goals,
        played=match.played,
    )


def _standings_rows(df, previous_ranks: dict[str, int]) -> list[StandingRow]:
    rows = []
    for rank, row in zip(df.index, df.to_dict("records")):
        club = row["Club"]
        prev = previous_ranks.get(club)
        rows.append(
            StandingRow(
                rank=int(rank),
                rank_change=(prev - int(rank)) if prev is not None else 0,
                club=club,
                played=int(row["J"]),
                won=int(row["G"]),
                drawn=int(row["N"]),
                lost=int(row["P"]),
                goals_for=int(row["BP"]),
                goals_against=int(row["BC"]),
                goal_diff=int(row["Diff"]),
                points=int(row["Pts"]),
            )
        )
    return rows


def standings(competition: CustomCompetition, previous_ranks: dict[str, int]) -> list[StandingRow]:
    return _standings_rows(competition.season.standings(), previous_ranks)


def _placed_player_out(placed: PlacedPlayer) -> PlacedPlayerOut:
    stat = placed.stat
    return PlacedPlayerOut(
        name=stat.player_name,
        poste=stat.poste,
        x=placed.x,
        y=placed.y,
        rating=stat.rating,
        goals=stat.goals,
        yellow_cards=stat.yellow_cards,
        red_card=stat.red_card_type is not None,
        started=stat.started,
    )


def pitch_view(match: Match) -> PitchViewOut:
    """Voir `pitch_layout.place_starting_xi` : domicile en haut du terrain
    (attaque vers le bas), extérieur en bas (attaque vers le haut)."""
    events = match.events
    home_starters = [s for s in events.home_lineup if s.started]
    away_starters = [s for s in events.away_lineup if s.started]
    return PitchViewOut(
        home=match.home,
        away=match.away,
        home_goals=match.home_goals,
        away_goals=match.away_goals,
        home_formation=actual_formation_label(home_starters),
        away_formation=actual_formation_label(away_starters),
        home_players=[_placed_player_out(p) for p in place_starting_xi(home_starters, attacking_up=False)],
        away_players=[_placed_player_out(p) for p in place_starting_xi(away_starters, attacking_up=True)],
    )


def group_out(group: Group) -> GroupOut:
    return GroupOut(name=group.name, is_complete=group.is_complete, standings=_standings_rows(group.standings(), {}))


def groups_status(competition: CustomCompetition) -> GroupsStatusOut:
    return GroupsStatusOut(
        groups=[group_out(g) for g in competition.groups],
        groups_matchday=competition.groups_matchday,
        groups_complete=competition.groups_complete,
        knockout_started=competition.bracket is not None,
    )


def tie_out(tie: Tie) -> TieOut:
    home_goals = away_goals = None
    if tie.played and not tie.is_bye:
        home_goals, away_goals = tie.aggregate()
    return TieOut(
        home=tie.home, away=tie.away, home_goals=home_goals, away_goals=away_goals, winner=tie.winner, is_bye=tie.is_bye
    )


def bracket_out(bracket: Bracket) -> BracketOut:
    return BracketOut(
        rounds=[RoundOut(number=r.number, ties=[tie_out(t) for t in r.ties], played=r.played) for r in bracket.rounds],
        is_complete=bracket.is_complete,
        champion=bracket.champion,
    )


def status(comp_id: str, competition: CustomCompetition) -> CompetitionStatus:
    season = competition.season
    return CompetitionStatus(
        id=comp_id,
        format=competition.format,
        championnat=competition.label or (season.championnat if season else None),
        is_over=competition.is_over,
        current_journee=season.current_journee_number if season else None,
        current_journee_played=season.current_journee.played if season else False,
        total_journees=season.total_journees if season else None,
        champion=competition.champion,
    )

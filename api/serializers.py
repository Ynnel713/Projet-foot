"""Conversion des objets du moteur (ligue1sim) vers les schémas Pydantic
exposés par l'API."""

from __future__ import annotations

from ligue1sim.champions_league import DIRECT_SPOTS, PLAYOFF_SPOTS
from ligue1sim.clubs import Club
from ligue1sim.coaches import coach_name
from ligue1sim.custom_competition import CustomCompetition
from ligue1sim.events import compute_leaderboards
from ligue1sim.faces import face_path
from ligue1sim.groups import Group
from ligue1sim.kits import primary_color
from ligue1sim.knockout import Bracket, Tie
from ligue1sim.match_stats import TeamMatchStats
from ligue1sim.pitch_layout import PlacedPlayer, actual_formation_label, place_starting_xi
from ligue1sim.players import Player
from ligue1sim.schedule import Match

import logging

from api.live_commentary import build_live_feed
from api.nlg_live import generate_nlg_feed
from api.schemas import (
    BenchPlayerOut,
    BracketOut,
    CompetitionStatus,
    GroupOut,
    GroupsStatusOut,
    LeaderboardRow,
    LeaderboardsOut,
    LiveEventOut,
    MatchOut,
    PitchViewOut,
    PlacedPlayerOut,
    PlayerOut,
    RosterOut,
    RoundOut,
    ScorerOut,
    StandingRow,
    TeamStatsOut,
    TextPartOut,
    TieOut,
    UnavailablePlayerOut,
)


def _match_summary(home_goals: int, away_goals: int) -> str:
    diff = abs(home_goals - away_goals)
    if diff == 0:
        return f"Match nul {home_goals}-{away_goals}"
    winner = "domicile" if home_goals > away_goals else "extérieur"
    if diff == 1:
        return f"Victoire serrée {home_goals}-{away_goals} ({winner})"
    if diff >= 3:
        return f"Large victoire {home_goals}-{away_goals} ({winner})"
    return f"Victoire {home_goals}-{away_goals} ({winner})"


def match_out(match: Match) -> MatchOut:
    summary = None
    scorers: list[ScorerOut] = []
    if match.played:
        summary = _match_summary(match.home_goals, match.away_goals)
        if match.events is not None:
            scorers = [
                ScorerOut(club=g.club_name, player=g.scorer, minute=g.minute, penalty=g.penalty)
                for g in sorted(match.events.goals, key=lambda g: g.minute)
            ]
    return MatchOut(
        home=match.home,
        away=match.away,
        home_goals=match.home_goals,
        away_goals=match.away_goals,
        played=match.played,
        summary=summary,
        scorers=scorers,
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


def _bench_player_out(stat, entered_minute: int | None) -> BenchPlayerOut:
    return BenchPlayerOut(name=stat.player_name, poste=stat.poste, rating=stat.rating, entered_minute=entered_minute)


def _unused_bench_player_out(player: Player) -> BenchPlayerOut:
    # Aucune PlayerMatchStat pour ce joueur (jamais entré en jeu ce match) --
    # pas de note de match, juste le profil de base.
    return BenchPlayerOut(name=player.name, poste=player.poste, rating=None, entered_minute=None)


def _unavailable_out(player: Player, reason: str) -> UnavailablePlayerOut:
    return UnavailablePlayerOut(name=player.name, poste=player.poste, reason=reason)


def _full_bench(club: Club, lineup_stats: list, substitutions: list, suspended: frozenset[str], injured: frozenset[str]) -> list[BenchPlayerOut]:
    """Banc complet pour l'écran terrain (28/09/2026) : les remplaçants
    RÉELLEMENT entrés en jeu ce match (avec leur minute d'entrée, pour le
    surlignage côté UI), PUIS le reste de l'effectif qui n'a pas joué --
    hors joueurs suspendus/blessés, déjà listés séparément (voir
    `_unavailable_out`)."""
    entered_minute_by_name = {s.player_on: s.minute for s in substitutions if s.club_name == club.name}
    appeared_names = {s.player_name for s in lineup_stats}
    by_name = {p.name: p for p in club.players}

    entered = sorted(
        (_bench_player_out(s, entered_minute_by_name.get(s.player_name)) for s in lineup_stats if not s.started),
        key=lambda b: b.entered_minute or 0,
    )
    unused_names = set(by_name) - appeared_names - suspended - injured
    unused = sorted((_unused_bench_player_out(by_name[name]) for name in unused_names), key=lambda b: b.name)
    return entered + unused


def _unavailable_list(club: Club, suspended: frozenset[str], injured: frozenset[str]) -> list[UnavailablePlayerOut]:
    by_name = {p.name: p for p in club.players}
    return sorted(
        (
            _unavailable_out(by_name[name], "blessure" if name in injured else "suspension")
            for name in (suspended | injured)
            if name in by_name
        ),
        key=lambda u: u.name,
    )


def _team_stats_out(stats: TeamMatchStats | None) -> TeamStatsOut | None:
    if stats is None:
        return None
    return TeamStatsOut(possession=stats.possession, shots=stats.shots, shots_on_target=stats.shots_on_target, xg=stats.xg)


logger = logging.getLogger(__name__)


def _live_feed(match: Match, home_club: Club, away_club: Club, label: str):
    """Fil live raconté par le NLG ; repli sur le fil à gabarits simples (buts, cartons, remplacements) si le NLG est indisponible."""
    try:
        return generate_nlg_feed(match, home_club, away_club, label)
    except Exception as exc:  # NlgUnavailable, mais aussi toute erreur de la chaîne : le fil ne doit jamais casser l'écran match
        logger.warning("Fil NLG indisponible pour %s - %s (%s) : repli sur les gabarits simples.", match.home, match.away, exc)
        return build_live_feed(match.events, match.home, match.away)


def pitch_view(match: Match, clubs_by_name: dict[str, Club], label: str = "") -> PitchViewOut:
    """Voir `pitch_layout.place_starting_xi` : domicile en haut du terrain
    (attaque vers le bas), extérieur en bas (attaque vers le haut).
    `clubs_by_name` : pour retrouver le RESTE de l'effectif (joueurs jamais
    apparus dans `events.home_lineup`/`away_lineup`, voir `_full_bench`) --
    ces listes ne contiennent que les titulaires et les remplaçants
    RÉELLEMENT entrés en jeu, jamais tout le banc (retour terrain du
    28/09/2026)."""
    events = match.events
    home_starters = [s for s in events.home_lineup if s.started]
    away_starters = [s for s in events.away_lineup if s.started]
    home_club, away_club = clubs_by_name[match.home], clubs_by_name[match.away]
    return PitchViewOut(
        home=match.home,
        away=match.away,
        home_goals=match.home_goals,
        away_goals=match.away_goals,
        home_formation=actual_formation_label(home_starters),
        away_formation=actual_formation_label(away_starters),
        home_players=[_placed_player_out(p) for p in place_starting_xi(home_starters, attacking_up=False)],
        away_players=[_placed_player_out(p) for p in place_starting_xi(away_starters, attacking_up=True)],
        home_bench=_full_bench(home_club, events.home_lineup, events.substitutions, events.home_suspended, events.home_injured),
        away_bench=_full_bench(away_club, events.away_lineup, events.substitutions, events.away_suspended, events.away_injured),
        home_unavailable=_unavailable_list(home_club, events.home_suspended, events.home_injured),
        away_unavailable=_unavailable_list(away_club, events.away_suspended, events.away_injured),
        home_coach=coach_name(match.home),
        away_coach=coach_name(match.away),
        home_stats=_team_stats_out(events.stats.home if events.stats else None),
        away_stats=_team_stats_out(events.stats.away if events.stats else None),
        live=[
            LiveEventOut(
                minute=e.minute, kind=e.kind, title=e.title, side=e.side, club=e.club,
                parts=[TextPartOut(text=t, player=is_player) for t, is_player in e.parts],
            )
            for e in _live_feed(match, home_club, away_club, label)
        ],
    )


def group_out(group: Group, last_played_matchday: int) -> GroupOut:
    """`last_played_matchday` : indice (0-based) de la dernière journée de
    poule jouée, -1 si aucune -- même compteur `groups_matchday` partagé par
    toutes les poules (voir `CustomCompetition.simulate_groups_matchday`)."""
    current_matches: list[MatchOut] = []
    if 0 <= last_played_matchday < len(group.calendar):
        current_matches = [match_out(m) for m in group.calendar[last_played_matchday].matches]
    next_index = last_played_matchday + 1
    next_matches = [match_out(m) for m in group.calendar[next_index].matches] if 0 <= next_index < len(group.calendar) else []
    return GroupOut(
        name=group.name,
        is_complete=group.is_complete,
        standings=_standings_rows(group.standings(), {}),
        current_matches=current_matches,
        next_matches=next_matches,
    )


def groups_status(competition: CustomCompetition) -> GroupsStatusOut:
    last_played_matchday = competition.groups_matchday - 1  # groups_matchday pointe déjà sur la PROCHAINE à jouer
    return GroupsStatusOut(
        groups=[group_out(g, last_played_matchday) for g in competition.groups],
        groups_matchday=competition.groups_matchday,
        groups_complete=competition.groups_complete,
        knockout_started=competition.bracket is not None,
        league_phase=competition.league_phase,
        direct_spots=DIRECT_SPOTS if competition.league_phase else 0,
        playoff_spots=PLAYOFF_SPOTS if competition.league_phase else 0,
    )


def tie_out(tie: Tie) -> TieOut:
    home_goals = away_goals = None
    if tie.played and not tie.is_bye:
        home_goals, away_goals = tie.aggregate()
    return TieOut(
        home=tie.home,
        away=tie.away,
        legs=[match_out(m) for m in tie.legs],
        home_goals=home_goals,
        away_goals=away_goals,
        winner=tie.winner,
        is_bye=tie.is_bye,
        decided_by_penalties=tie.decided_by_penalties,
        penalty_score=tie.penalty_score,
    )


def bracket_out(bracket: Bracket) -> BracketOut:
    return BracketOut(
        rounds=[RoundOut(number=r.number, ties=[tie_out(t) for t in r.ties], played=r.played, label=r.label) for r in bracket.rounds],
        is_complete=bracket.is_complete,
        champion=bracket.champion,
    )


def leaderboards_out(competition: CustomCompetition) -> LeaderboardsOut:
    buteurs, passeurs = compute_leaderboards(competition.all_matches)
    return LeaderboardsOut(
        scorers=[LeaderboardRow(player=r.Joueur, club=r.Club, count=r.Buts) for r in buteurs.itertuples()],
        assists=[LeaderboardRow(player=r.Joueur, club=r.Club, count=r.Passes) for r in passeurs.itertuples()],
    )


def player_out(player: Player) -> PlayerOut:
    return PlayerOut(
        id=player.id,
        name=player.name,
        poste=player.poste,
        poste_secondaire=list(player.poste_secondaire),
        postes_fm=player.postes_fm,
        age=player.age,
        note=player.note,
        nationalite=player.nationalite,
        pied=player.pied,
        taille_fm=player.taille_fm,
        weak_foot=player.weak_foot,
        preferred_moves=player.preferred_moves,
        categorie=player.categorie,
        valeur_marchande=player.valeur_marchande,
        attributes=player.attributes,
        photo_url=f"/media/faces/{player.id}.png" if face_path(player.id) is not None else None,
    )


def roster_out(club: Club) -> RosterOut:
    players = club.players
    note = sum(p.note for p in players) / len(players) if players else 0.0
    age_moyen = sum(p.age for p in players) / len(players) if players else 0.0
    valeurs = [p.valeur_marchande for p in players if p.valeur_marchande is not None]
    return RosterOut(
        club=club.name,
        championnat=players[0].championnat if players else "",
        color=primary_color(club.name),
        note=note,
        age_moyen=age_moyen,
        valeur_totale=sum(valeurs) if valeurs else None,
        players=[player_out(p) for p in players],
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

import random

from ligue1sim.clubs import Club
from ligue1sim.events import (
    AvailabilityTracker,
    RATING_MAX,
    RATING_MIN,
    compute_leaderboards,
    generate_match_events,
)
from ligue1sim.lineup import pick_best_formation
from ligue1sim.players import Player
from ligue1sim.schedule import Match


def _player(poste: str, note: float, name: str) -> Player:
    return Player(
        prenom=name,
        nom="",
        nationalite="France",
        age=25,
        poste=poste,
        note=note,
        club="Test FC",
        championnat="TEST",
    )


def _squad(club_name: str, size_per_group: int = 4) -> list[Player]:
    squad = [_player("GK", 70.0, f"{club_name}_gk{i}") for i in range(2)]
    squad += [_player("DC", 70.0, f"{club_name}_cb{i}") for i in range(size_per_group)]
    squad += [_player("LB", 70.0, f"{club_name}_lb{i}") for i in range(2)]
    squad += [_player("RB", 70.0, f"{club_name}_rb{i}") for i in range(2)]
    squad += [_player("MC", 70.0, f"{club_name}_cm{i}") for i in range(size_per_group)]
    squad += [_player("MOC", 70.0, f"{club_name}_am{i}") for i in range(2)]
    squad += [_player("AG", 70.0, f"{club_name}_lw{i}") for i in range(2)]
    squad += [_player("AD", 70.0, f"{club_name}_rw{i}") for i in range(2)]
    squad += [_player("BU", 70.0, f"{club_name}_cf{i}") for i in range(size_per_group)]
    return squad


def _clubs():
    home = Club(name="Home FC", players=_squad("home"))
    away = Club(name="Away FC", players=_squad("away"))
    return home, away


def test_generate_match_events_goal_count_matches_score():
    random.seed(42)
    home, away = _clubs()
    home_lineup = pick_best_formation(home)
    away_lineup = pick_best_formation(away)

    events = generate_match_events(home, away, home_lineup, away_lineup, home_goals=3, away_goals=1)

    home_goals_in_events = sum(1 for g in events.goals if g.club_name == "Home FC")
    away_goals_in_events = sum(1 for g in events.goals if g.club_name == "Away FC")
    assert home_goals_in_events == 3
    assert away_goals_in_events == 1


def test_goals_are_scored_by_players_from_the_correct_club_and_never_by_a_goalkeeper():
    random.seed(7)
    home, away = _clubs()
    home_lineup = pick_best_formation(home)
    away_lineup = pick_best_formation(away)
    home_names = {p.name for p in home_lineup.players} | {f"home_{s}" for s in []}

    events = generate_match_events(home, away, home_lineup, away_lineup, home_goals=4, away_goals=4)

    all_home_squad_names = {p.name for p in home.players}
    all_away_squad_names = {p.name for p in away.players}
    for g in events.goals:
        assert not g.scorer.startswith("home_gk") if g.club_name == "Home FC" else True
        assert not g.scorer.startswith("away_gk") if g.club_name == "Away FC" else True
        if g.club_name == "Home FC":
            assert g.scorer in all_home_squad_names
        else:
            assert g.scorer in all_away_squad_names


def test_zero_zero_match_produces_no_goals():
    home, away = _clubs()
    home_lineup = pick_best_formation(home)
    away_lineup = pick_best_formation(away)

    events = generate_match_events(home, away, home_lineup, away_lineup, home_goals=0, away_goals=0)

    assert events.goals == []


def test_lineups_include_starters_and_at_most_five_subs_per_side():
    home, away = _clubs()
    home_lineup = pick_best_formation(home)
    away_lineup = pick_best_formation(away)

    events = generate_match_events(home, away, home_lineup, away_lineup, home_goals=1, away_goals=1)

    home_subs = [s for s in events.home_lineup if not s.started]
    away_subs = [s for s in events.away_lineup if not s.started]
    assert len(home_subs) <= 5
    assert len(away_subs) <= 5
    assert len([s for s in events.home_lineup if s.started]) == 11


def test_unavailable_players_are_excluded_from_the_squad():
    home, away = _clubs()
    excluded = "home_cb0"
    home_lineup = pick_best_formation(home, unavailable=frozenset({excluded}))
    away_lineup = pick_best_formation(away)

    events = generate_match_events(
        home, away, home_lineup, away_lineup, home_goals=2, away_goals=0, unavailable_home=frozenset({excluded})
    )

    all_home_names_in_match = {s.player_name for s in events.home_lineup}
    assert excluded not in all_home_names_in_match


def test_ratings_are_within_bounds():
    random.seed(1)
    home, away = _clubs()
    home_lineup = pick_best_formation(home)
    away_lineup = pick_best_formation(away)

    events = generate_match_events(home, away, home_lineup, away_lineup, home_goals=5, away_goals=0)

    for stat in events.home_lineup + events.away_lineup:
        assert RATING_MIN <= stat.rating <= RATING_MAX


def test_compute_leaderboards_aggregates_goals_and_assists_across_matches():
    home, away = _clubs()
    home_lineup = pick_best_formation(home)
    away_lineup = pick_best_formation(away)

    match1 = Match("Home FC", "Away FC", 2, 0)
    match1.events = generate_match_events(home, away, home_lineup, away_lineup, 2, 0)
    match2 = Match("Home FC", "Away FC", 1, 0)
    match2.events = generate_match_events(home, away, home_lineup, away_lineup, 1, 0)
    match_no_events = Match("Home FC", "Away FC", 0, 0)  # events=None, doit être ignoré

    buteurs, passeurs = compute_leaderboards([match1, match2, match_no_events])

    assert buteurs["Buts"].sum() == 3
    assert set(buteurs.columns) == {"Joueur", "Club", "Buts"}
    assert set(passeurs.columns) == {"Joueur", "Club", "Passes"}
    if not buteurs.empty:
        assert buteurs["Buts"].is_monotonic_decreasing


class TestAvailabilityTracker:
    def test_new_ban_is_not_active_until_next_matchday(self):
        tracker = AvailabilityTracker()
        tracker.apply_new_ban("Club A", "Joueur X", 2)

        assert "Joueur X" in tracker.unavailable_players("Club A")

    def test_record_matchday_decrements_only_for_clubs_that_played(self):
        tracker = AvailabilityTracker()
        tracker.apply_new_ban("Club A", "Joueur X", 2)
        tracker.apply_new_ban("Club B", "Joueur Y", 1)

        tracker.record_matchday({"Club A"})  # Club B n'a pas joué cette journée

        assert "Joueur X" in tracker.unavailable_players("Club A")  # encore 1 match
        assert "Joueur Y" in tracker.unavailable_players("Club B")  # inchangé

    def test_ban_expires_after_serving_the_full_duration(self):
        tracker = AvailabilityTracker()
        tracker.apply_new_ban("Club A", "Joueur X", 2)

        tracker.record_matchday({"Club A"})
        assert "Joueur X" in tracker.unavailable_players("Club A")
        tracker.record_matchday({"Club A"})
        assert "Joueur X" not in tracker.unavailable_players("Club A")

    def test_full_sequence_new_ban_does_not_get_decremented_same_matchday(self):
        """Un rouge pris aujourd'hui ne doit pas compter comme un match déjà
        manqué : l'appelant doit décrémenter AVANT d'appliquer la nouvelle
        suspension du match qui vient d'avoir lieu."""
        tracker = AvailabilityTracker()
        tracker.record_matchday({"Club A"})  # rien à décrémenter encore
        tracker.apply_new_ban("Club A", "Joueur X", 2)

        assert "Joueur X" in tracker.unavailable_players("Club A")

    def test_two_tracker_instances_are_independent(self):
        tracker1 = AvailabilityTracker()
        tracker2 = AvailabilityTracker()
        tracker1.apply_new_ban("Club A", "Joueur X", 2)

        assert "Joueur X" not in tracker2.unavailable_players("Club A")

    def test_active_bans_lists_everything(self):
        tracker = AvailabilityTracker()
        tracker.apply_new_ban("Club A", "Joueur X", 2)
        tracker.apply_new_ban("Club B", "Joueur Y", 1)

        assert tracker.active_bans() == [("Club A", "Joueur X", 2), ("Club B", "Joueur Y", 1)]

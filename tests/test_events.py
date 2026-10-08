import random

import numpy as np

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
from ligue1sim.schedule import Journee, Match
from ligue1sim.simulation import LeagueContext, simulate_journee, simulate_match


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


# --- Raison des absences (suspension / blessure) : affichage seulement ---------
# `suspended_*`/`injured_*` ne servent qu'a AFFICHER pourquoi un joueur est absent ; la compo reste
# decidee par `unavailable_*` (ensemble fusionne) et le resultat sportif n'en depend pas.


def test_absence_reasons_default_to_empty_and_are_recorded_when_given():
    random.seed(5)
    home, away = _clubs()
    home_lineup, away_lineup = pick_best_formation(home), pick_best_formation(away)

    default = generate_match_events(home, away, home_lineup, away_lineup, home_goals=1, away_goals=0)
    assert default.home_suspended == default.home_injured == frozenset()
    assert default.away_suspended == default.away_injured == frozenset()

    shown = generate_match_events(
        home, away, home_lineup, away_lineup, home_goals=1, away_goals=0,
        suspended_home=frozenset({"home_cb0"}), injured_home=frozenset({"home_cm1"}),
        suspended_away=frozenset({"away_lb0"}), injured_away=frozenset({"away_cf2"}),
    )
    assert shown.home_suspended == frozenset({"home_cb0"})
    assert shown.home_injured == frozenset({"home_cm1"})
    assert shown.away_suspended == frozenset({"away_lb0"})
    assert shown.away_injured == frozenset({"away_cf2"})


def test_absence_reasons_do_not_change_the_match():
    """Meme graine, meme absent : avec ou sans raison (suspension ou blessure), meme score et memes buts."""
    home, away = _clubs()
    context = LeagueContext.from_clubs([home, away])
    absent = frozenset({"home_cb0"})

    def play(**reasons):
        random.seed(21)
        np.random.seed(21)
        return simulate_match(home, away, context, unavailable_home=absent, **reasons)

    home_goals, away_goals, plain = play()
    for reasons in ({"suspended_home": absent}, {"injured_home": absent}):
        hg, ag, events = play(**reasons)
        assert (hg, ag) == (home_goals, away_goals)
        assert events.goals == plain.goals
        assert [s.player_name for s in events.home_lineup] == [s.player_name for s in plain.home_lineup]
    assert plain.home_suspended == plain.home_injured == frozenset()


def test_simulate_journee_records_why_each_player_was_absent():
    home, away = _clubs()
    context = LeagueContext.from_clubs([home, away])
    suspensions, injuries = AvailabilityTracker(), AvailabilityTracker()
    suspensions.apply_new_ban("Home FC", "home_cb0", 2)
    injuries.apply_new_ban("Away FC", "away_lb0", 2)
    journee = Journee(1, [Match("Home FC", "Away FC")])

    random.seed(8)
    simulate_journee(journee, {"Home FC": home, "Away FC": away}, context, suspensions=suspensions, injuries=injuries)

    events = journee.matches[0].events
    assert events.home_suspended == frozenset({"home_cb0"}) and events.home_injured == frozenset()
    assert events.away_injured == frozenset({"away_lb0"}) and events.away_suspended == frozenset()
    assert "home_cb0" not in {s.player_name for s in events.home_lineup}  # absent de la compo, quelle que soit la raison


# --- Ticket 2 (08/10/2026) : cohérence cartons / remplacements --------------------------------
# Règle : un expulsé (rouge direct ou second jaune) quitte le terrain définitivement -- jamais
# remplacé, aucun but / passe / blessure / penalty manqué après sa minute d'expulsion ; un
# remplacé ne reçoit pas de carton après sa sortie ; un entrant n'a rien avant son entrée.

_RED_TYPES = ("direct", "second_yellow")


def _incoherences(events) -> list[str]:
    """Liste des violations de la règle ci-dessus dans `events` (vide = cohérent)."""
    problems = []
    expelled = {(c.club_name, c.player): c.minute for c in events.cards if c.card_type in _RED_TYPES}
    left = {(s.club_name, s.player_off): s.minute for s in events.substitutions}
    entered = {(s.club_name, s.player_on): s.minute for s in events.substitutions}
    for key in expelled:
        if key in left:
            problems.append(f"expulsé remplacé : {key}")
    for card in events.cards:
        key = (card.club_name, card.player)
        if key in left and card.minute > left[key]:
            problems.append(f"carton après sortie : {key}")

    def check(club: str, player: str, minute: int, what: str) -> None:
        key = (club, player)
        if key in expelled and minute > expelled[key]:
            problems.append(f"{what} après expulsion : {key}")
        if key in left and minute > left[key]:
            problems.append(f"{what} après remplacement : {key}")
        if key in entered and minute < entered[key]:
            problems.append(f"{what} avant entrée : {key}")

    for goal in events.goals:
        check(goal.club_name, goal.scorer, goal.minute, "but")
        if goal.assist:
            check(goal.club_name, goal.assist, goal.minute, "passe")
    for injury in events.injuries:
        check(injury.club_name, injury.player, injury.minute, "blessure")
    for missed in events.penalties_missed:
        check(missed.club_name, missed.player, missed.minute, "penalty manqué")
    return problems


def _seeded_match(seed: int):
    random.seed(seed)
    np.random.seed(seed)
    home, away = _clubs()
    context = LeagueContext.from_clubs([home, away])
    home_goals, away_goals, events = simulate_match(home, away, context)
    return events


def test_incoherence_detector_flags_an_expelled_player_who_is_substituted():
    # Garde-fou : le détecteur doit voir le défaut du ticket 2 (sinon les tests ci-dessous seraient vides).
    from ligue1sim.events import CardEvent, MatchEvents, SubstitutionEvent

    bad = MatchEvents(
        home_formation="4-3-3", away_formation="4-3-3", home_lineup=[], away_lineup=[],
        substitutions=[SubstitutionEvent("Home FC", player_off="a", player_on="b", minute=64)],
        cards=[CardEvent("Home FC", "a", minute=17, card_type="second_yellow")],
    )
    assert _incoherences(bad) == ["expulsé remplacé : ('Home FC', 'a')"]


def test_seed_11_match_never_substitutes_an_expelled_player():
    events = _seeded_match(11)
    assert _incoherences(events) == []


def test_hundred_seeded_matches_have_no_card_substitution_incoherence():
    total_reds = total_starters_replaced = 0
    for seed in range(1, 101):
        events = _seeded_match(seed)
        assert _incoherences(events) == [], f"graine {seed}"
        total_reds += sum(1 for c in events.cards if c.card_type in _RED_TYPES)
        total_starters_replaced += len(events.substitutions)
    assert total_reds > 0 and total_starters_replaced > 0  # le scénario à risque est bien exercé


def test_expelled_players_appear_in_no_later_event_even_when_forced(monkeypatch):
    # Expulsions FORCÉES (titulaires 1, 3, 5, entrant n° 12 de l'appel) : le cas du ticket 2 se produit
    # à coup sûr, pour 60 graines, quel que soit le tirage de remplacements.
    from ligue1sim import events as events_module

    for seed in range(1, 61):
        calls = {"n": 0}

        def forced_card():
            n = calls["n"]
            calls["n"] += 1
            return (0, "direct") if n in (1, 3, 5, 12) else (0, None)

        monkeypatch.setattr(events_module, "_draw_card", forced_card)
        random.seed(seed)
        np.random.seed(seed)
        home, away = _clubs()
        home_lineup, away_lineup = pick_best_formation(home), pick_best_formation(away)
        events = generate_match_events(home, away, home_lineup, away_lineup, home_goals=3, away_goals=2)

        expelled = {c.player: c.minute for c in events.cards if c.club_name == "Home FC" and c.card_type == "direct"}
        assert len(expelled) >= 3, f"graine {seed}"
        assert not {s.player_off for s in events.substitutions} & set(expelled), f"graine {seed}"
        assert _incoherences(events) == [], f"graine {seed}"

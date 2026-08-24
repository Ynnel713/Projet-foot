from ligue1sim.clubs import Club
from ligue1sim.events import AvailabilityTracker
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


def _squad(club_name: str) -> list[Player]:
    squad = [_player("Goalkeeper", 70.0, f"{club_name}_gk{i}") for i in range(2)]
    squad += [_player("Centre-Back", 70.0, f"{club_name}_cb{i}") for i in range(4)]
    squad += [_player("Left-Back", 70.0, f"{club_name}_lb{i}") for i in range(2)]
    squad += [_player("Right-Back", 70.0, f"{club_name}_rb{i}") for i in range(2)]
    squad += [_player("Central Midfield", 70.0, f"{club_name}_cm{i}") for i in range(4)]
    squad += [_player("Attacking Midfield", 70.0, f"{club_name}_am{i}") for i in range(2)]
    squad += [_player("Left Winger", 70.0, f"{club_name}_lw{i}") for i in range(2)]
    squad += [_player("Right Winger", 70.0, f"{club_name}_rw{i}") for i in range(2)]
    squad += [_player("Centre-Forward", 70.0, f"{club_name}_cf{i}") for i in range(4)]
    return squad


def test_simulate_match_without_rosters_produces_no_events():
    home, away = Club(name="A"), Club(name="B")
    context = LeagueContext.from_clubs([home, away])

    home_goals, away_goals, events = simulate_match(home, away, context)

    assert isinstance(home_goals, int) and isinstance(away_goals, int)
    assert events is None


def test_simulate_match_with_rosters_produces_events():
    home = Club(name="Home FC", players=_squad("home"))
    away = Club(name="Away FC", players=_squad("away"))
    context = LeagueContext.from_clubs([home, away])

    _, _, events = simulate_match(home, away, context)

    assert events is not None
    assert len(events.home_lineup) >= 11
    assert len(events.away_lineup) >= 11


def test_league_context_from_clubs_uses_player_based_strength():
    strong = Club(name="Strong FC", players=_squad("strong"))  # notes à 70
    weak_players = [
        Player(
            prenom=p.prenom, nom=p.nom, nationalite=p.nationalite, age=p.age,
            poste=p.poste, note=30.0, club="Weak FC", championnat="TEST",
        )
        for p in _squad("weak")
    ]
    weak = Club(name="Weak FC", players=weak_players)

    context = LeagueContext.from_clubs([strong, weak])

    assert 30.0 < context.avg_rating < 70.0


def test_suspended_player_is_excluded_from_the_next_journee_lineup():
    home = Club(name="Home FC", players=_squad("home"))
    away = Club(name="Away FC", players=_squad("away"))
    context = LeagueContext.from_clubs([home, away])
    clubs_by_name = {"Home FC": home, "Away FC": away}
    suspensions = AvailabilityTracker()

    # Journée 1 : simulée jusqu'à obtenir un rouge direct pour tester la
    # persistance, sinon on force artificiellement une suspension comme le
    # ferait le moteur -- ici on force directement pour un test déterministe.
    suspensions.apply_new_ban("Home FC", "home_cb0", 1)

    journee2 = Journee(2, [Match("Home FC", "Away FC")])
    simulate_journee(journee2, clubs_by_name, context, suspensions=suspensions)

    assert journee2.matches[0].events is not None
    names_in_lineup = {s.player_name for s in journee2.matches[0].events.home_lineup}
    assert "home_cb0" not in names_in_lineup


def test_suspension_persists_across_two_sequential_journees_sharing_a_tracker():
    home = Club(name="Home FC", players=_squad("home"))
    away = Club(name="Away FC", players=_squad("away"))
    context = LeagueContext.from_clubs([home, away])
    clubs_by_name = {"Home FC": home, "Away FC": away}
    suspensions = AvailabilityTracker()
    suspensions.apply_new_ban("Home FC", "home_cb0", 2)

    j1 = Journee(1, [Match("Home FC", "Away FC")])
    simulate_journee(j1, clubs_by_name, context, suspensions=suspensions)
    assert "home_cb0" not in {s.player_name for s in j1.matches[0].events.home_lineup}
    assert "home_cb0" in suspensions.unavailable_players("Home FC")  # encore 1 match à purger

    j2 = Journee(2, [Match("Home FC", "Away FC")])
    simulate_journee(j2, clubs_by_name, context, suspensions=suspensions)
    assert "home_cb0" not in {s.player_name for s in j2.matches[0].events.home_lineup}
    assert "home_cb0" not in suspensions.unavailable_players("Home FC")  # purgée


def test_ephemeral_tracker_is_used_when_none_is_passed():
    home = Club(name="Home FC", players=_squad("home"))
    away = Club(name="Away FC", players=_squad("away"))
    context = LeagueContext.from_clubs([home, away])
    clubs_by_name = {"Home FC": home, "Away FC": away}

    journee = Journee(1, [Match("Home FC", "Away FC")])
    simulate_journee(journee, clubs_by_name, context)  # ne doit pas lever

    assert journee.played

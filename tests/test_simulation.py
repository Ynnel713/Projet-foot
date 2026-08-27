from ligue1sim.clubs import Club
from ligue1sim.events import AvailabilityTracker
from ligue1sim.lineup import select_best_xi
from ligue1sim.players import Player
from ligue1sim.schedule import Journee, Match
from ligue1sim.simulation import (
    LeagueContext,
    _attack_strength,
    _defense_strength,
    _mid_modifier,
    simulate_journee,
    simulate_match,
)


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
    squad = [_player("GK", 70.0, f"{club_name}_gk{i}") for i in range(2)]
    squad += [_player("DC", 70.0, f"{club_name}_cb{i}") for i in range(4)]
    squad += [_player("LB", 70.0, f"{club_name}_lb{i}") for i in range(2)]
    squad += [_player("RB", 70.0, f"{club_name}_rb{i}") for i in range(2)]
    squad += [_player("MC", 70.0, f"{club_name}_cm{i}") for i in range(4)]
    squad += [_player("MOC", 70.0, f"{club_name}_am{i}") for i in range(2)]
    squad += [_player("AG", 70.0, f"{club_name}_lw{i}") for i in range(2)]
    squad += [_player("AD", 70.0, f"{club_name}_rw{i}") for i in range(2)]
    squad += [_player("BU", 70.0, f"{club_name}_cf{i}") for i in range(4)]
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


class TestSectorStrengths:
    def test_mid_modifier_boosts_a_squad_with_an_above_average_midfield(self):
        players = [_player("GK", 70.0, "gk0")]
        players += [_player("DC", 70.0, f"cb{i}") for i in range(2)]
        players += [_player("LB", 70.0, "lb0")]
        players += [_player("RB", 70.0, "rb0")]
        players += [_player("MC", 90.0, f"cm{i}") for i in range(2)]  # milieu nettement au-dessus du reste
        players += [_player("AG", 70.0, "lw0")]
        players += [_player("AD", 70.0, "rw0")]
        players += [_player("BU", 70.0, f"cf{i}") for i in range(2)]
        club = Club(name="Test FC", players=players)

        lineup = select_best_xi(club, "4-4-2")

        assert lineup.mid_rating > lineup.rating
        assert _mid_modifier(lineup) > 1.0

    def test_mid_modifier_penalizes_a_squad_with_a_below_average_midfield(self):
        players = [_player("GK", 90.0, "gk0")]
        players += [_player("DC", 90.0, f"cb{i}") for i in range(2)]
        players += [_player("LB", 90.0, "lb0")]
        players += [_player("RB", 90.0, "rb0")]
        players += [_player("MC", 60.0, f"cm{i}") for i in range(2)]  # milieu nettement en-dessous du reste
        players += [_player("AG", 90.0, "lw0")]
        players += [_player("AD", 90.0, "rw0")]
        players += [_player("BU", 90.0, f"cf{i}") for i in range(2)]
        club = Club(name="Test FC", players=players)

        lineup = select_best_xi(club, "4-4-2")

        assert lineup.mid_rating < lineup.rating
        assert _mid_modifier(lineup) < 1.0

    def test_attack_and_defense_strength_use_the_right_sectors_not_the_flat_average(self):
        players = [_player("GK", 50.0, "gk0")]
        players += [_player("DC", 50.0, f"cb{i}") for i in range(2)]
        players += [_player("LB", 50.0, "lb0")]
        players += [_player("RB", 50.0, "rb0")]
        players += [_player("MC", 50.0, f"cm{i}") for i in range(2)]
        players += [_player("AG", 95.0, "lw0")]
        players += [_player("AD", 95.0, "rw0")]
        players += [_player("BU", 95.0, f"cf{i}") for i in range(2)]
        club = Club(name="Test FC", players=players)

        lineup = select_best_xi(club, "4-4-2")
        flat_average = lineup.rating  # ~66 : ni la force d'attaque, ni la défensive ne doivent s'en approcher

        # Attaque forte (95) mais défense/gardien faibles (50) : la force
        # d'attaque doit refléter les attaquants, pas la moyenne plate.
        assert _attack_strength(lineup) > flat_average + 15
        assert _defense_strength(lineup) < flat_average - 15


def test_ephemeral_tracker_is_used_when_none_is_passed():
    home = Club(name="Home FC", players=_squad("home"))
    away = Club(name="Away FC", players=_squad("away"))
    context = LeagueContext.from_clubs([home, away])
    clubs_by_name = {"Home FC": home, "Away FC": away}

    journee = Journee(1, [Match("Home FC", "Away FC")])
    simulate_journee(journee, clubs_by_name, context)  # ne doit pas lever

    assert journee.played

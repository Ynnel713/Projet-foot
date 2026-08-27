import pytest

from ligue1sim.clubs import Club
from ligue1sim.events import AvailabilityTracker
from ligue1sim.lineup import select_best_xi
from ligue1sim.players import Player
from ligue1sim.schedule import Journee, Match
from ligue1sim.simulation import (
    HOME_ADVANTAGE,
    LEAGUE_AVG_GOALS,
    FormTracker,
    LeagueContext,
    _attack_strength,
    _defense_strength,
    _expected_goals,
    _form_modifier,
    _mid_modifier,
    _process_form_signal,
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


class TestExpectedGoalsRatioModel:
    """Le modèle ratio attaque/défense (voir ATTACK_DEFENSE_POWER), qui a
    remplacé l'ancien exposant brut appliqué à la moyenne plate -- voir la
    conversation de calibrage associée pour le détail des chiffres mesurés."""

    def _context(self, avg_attack=70.0, avg_defense=70.0, avg_rating=70.0):
        return LeagueContext(avg_rating=avg_rating, avg_attack=avg_attack, avg_defense=avg_defense)

    def test_average_team_against_average_team_gives_the_league_average_goals(self):
        context = self._context(avg_attack=70.0, avg_defense=70.0)
        lam = _expected_goals(70.0, 70.0, context, home_advantage=False)
        assert lam == pytest.approx(LEAGUE_AVG_GOALS)

    def test_stronger_attack_produces_more_expected_goals(self):
        context = self._context(avg_attack=70.0, avg_defense=70.0)
        weak_attack = _expected_goals(60.0, 70.0, context, home_advantage=False)
        strong_attack = _expected_goals(85.0, 70.0, context, home_advantage=False)
        assert strong_attack > weak_attack

    def test_stronger_opposing_defense_reduces_expected_goals(self):
        context = self._context(avg_attack=70.0, avg_defense=70.0)
        vs_weak_defense = _expected_goals(70.0, 55.0, context, home_advantage=False)
        vs_strong_defense = _expected_goals(70.0, 90.0, context, home_advantage=False)
        assert vs_strong_defense < vs_weak_defense

    def test_home_advantage_only_applies_when_requested(self):
        context = self._context()
        away_lam = _expected_goals(70.0, 70.0, context, home_advantage=False)
        home_lam = _expected_goals(70.0, 70.0, context, home_advantage=True)
        assert home_lam == pytest.approx(away_lam * HOME_ADVANTAGE)


class TestFormTracker:
    """Forme persistante offensive/défensive -- voir la section 'Forme' en
    tête de simulation.py pour la justification du plafonnage+rétrécissement
    du signal avant injection dans l'EMA."""

    def test_unknown_club_has_neutral_modifiers(self):
        form = FormTracker()
        assert form.offense_modifier("Inconnu FC") == 1.0
        assert form.defense_modifier("Inconnu FC") == 1.0

    def test_a_single_lucky_match_does_not_saturate_the_form_bound(self):
        # Un match avec un delta énorme (buts réels très supérieurs à
        # l'attendu) ne doit pas, à lui seul, pousser la forme jusqu'à sa
        # borne -- c'est exactement le risque signalé : transformer la
        # réussite aléatoire d'un match en une modification durable.
        form = FormTracker()
        form.record_match("Home FC", "Away FC", lambda_home=1.3, lambda_away=1.3, home_goals=6, away_goals=0)

        modifier = form.offense_modifier("Home FC")
        assert modifier < 1.10  # nettement en-dessous de la borne haute (1.15)

    def test_repeated_strong_performances_move_form_toward_the_bound_progressively(self):
        form = FormTracker()
        for _ in range(20):
            form.record_match("Home FC", "Away FC", lambda_home=1.3, lambda_away=1.3, home_goals=3, away_goals=0)
        # Après de nombreux matchs cohéremment au-dessus de l'attendu, la
        # forme doit s'être rapprochée de la borne haute (jamais dépassée).
        assert form.offense_modifier("Home FC") > 1.10

    def test_form_modifier_never_exceeds_its_bounds(self):
        assert _form_modifier(1000.0) == pytest.approx(1.15)
        assert _form_modifier(-1000.0) == pytest.approx(0.85)

    def test_process_form_signal_clips_before_shrinking(self):
        # Un écart énorme (buts - lambda = +10) doit être plafonné avant
        # d'être rétréci, pas rétréci puis laissé filer.
        huge = _process_form_signal(10.0)
        moderate = _process_form_signal(1.0)
        assert huge == moderate * 1.5  # 1.5 = plafond ; 1.0 < plafond, donc juste rétréci

    def test_record_match_updates_both_clubs_in_opposite_defensive_sense(self):
        form = FormTracker()
        # Home marque plus que prévu (bonne forme offensive) ET encaisse
        # moins que prévu pour Away (donc bonne forme défensive pour Home).
        form.record_match("Home FC", "Away FC", lambda_home=1.0, lambda_away=1.0, home_goals=3, away_goals=0)

        assert form.offense_modifier("Home FC") > 1.0  # a surperformé en attaque
        assert form.defense_modifier("Home FC") > 1.0  # a encaissé moins que prévu
        assert form.offense_modifier("Away FC") < 1.0  # a sous-performé en attaque
        assert form.defense_modifier("Away FC") < 1.0  # a encaissé plus que prévu


def test_simulate_match_applies_and_updates_form_when_provided():
    home = Club(name="Home FC", players=_squad("home"))
    away = Club(name="Away FC", players=_squad("away"))
    context = LeagueContext.from_clubs([home, away])
    form = FormTracker()

    simulate_match(home, away, context, form=form)

    # Le tracker doit avoir été rempli pour les deux clubs après le match.
    assert "Home FC" in form._forms
    assert "Away FC" in form._forms


def test_ephemeral_tracker_is_used_when_none_is_passed():
    home = Club(name="Home FC", players=_squad("home"))
    away = Club(name="Away FC", players=_squad("away"))
    context = LeagueContext.from_clubs([home, away])
    clubs_by_name = {"Home FC": home, "Away FC": away}

    journee = Journee(1, [Match("Home FC", "Away FC")])
    simulate_journee(journee, clubs_by_name, context)  # ne doit pas lever

    assert journee.played

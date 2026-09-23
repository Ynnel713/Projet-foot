"""Tests du moteur narratif (brief "narrative engine foundations" puis
"constraint priority", 23/09/2026) -- engine/narrative.py.

Brief "constraint priority" : les règles anti-répétition/écart minimum ne
gouvernent QUE les `generated_events` (occasions inventées, `event_type ==
OCCASION`) -- les `existing_events` (buts réels, `event_type == BUT`) sont
hors périmètre, insérés tels quels (voir PRIORITÉ DES CONTRAINTES en tête de
`engine/narrative.py`). Conséquence directe : `build_timeline` ne rejette
plus AUCUN match (`MinuteCollisionError`/`AntiRepetitionUnsatisfiableError`
retirées) -- les tests "1000 matchs" simulent donc directement 1000 matchs
réels et appellent `build_timeline` sur chacun sans gestion d'exception."""

import pytest

from ligue1sim.clubs import Club
from ligue1sim.events import GoalEvent, MatchEvents, PlayerMatchStat
from ligue1sim.lineup import pick_best_formation
from ligue1sim.players import Player
from ligue1sim.schedule import Match
from ligue1sim.simulation import LeagueContext, simulate_match

from narrative import (
    BUT,
    OCCASION,
    _MIN_MINUTE_GAP,
    _has_cyclic_pattern,
    build_timeline,
    match_result_from,
)

_N_MATCHES = 1000


def _player(poste: str, note: float, name: str) -> Player:
    return Player(prenom=name, nom="", nationalite="France", age=25, poste=poste, note=note, club="Test FC", championnat="TEST")


def _squad(club_name: str, note: float = 70.0) -> list[Player]:
    squad = [_player("GK", note, f"{club_name}_gk{i}") for i in range(2)]
    squad += [_player("DC", note, f"{club_name}_cb{i}") for i in range(4)]
    squad += [_player("LB", note, f"{club_name}_lb{i}") for i in range(2)]
    squad += [_player("RB", note, f"{club_name}_rb{i}") for i in range(2)]
    squad += [_player("MC", note, f"{club_name}_cm{i}") for i in range(4)]
    squad += [_player("MOC", note, f"{club_name}_am{i}") for i in range(2)]
    squad += [_player("AG", note, f"{club_name}_lw{i}") for i in range(2)]
    squad += [_player("AD", note, f"{club_name}_rw{i}") for i in range(2)]
    squad += [_player("BU", note, f"{club_name}_cf{i}") for i in range(4)]
    return squad


def _clubs(home_note: float = 70.0, away_note: float = 70.0) -> tuple[Club, Club]:
    home = Club(name="Home FC", players=_squad("home", home_note))
    away = Club(name="Away FC", players=_squad("away", away_note))
    return home, away


def _simulate_one(home, away, context, home_lineup, away_lineup, *, date: str):
    home_goals, away_goals, events = simulate_match(home, away, context)
    if events is None:
        return None
    match = Match(home=home.name, away=away.name, home_goals=home_goals, away_goals=away_goals, events=events)
    return match_result_from(match, events, home_lineup, away_lineup, date=date)


def _simulate_n(n: int, *, home_note: float = 70.0, away_note: float = 70.0) -> list:
    home, away = _clubs(home_note, away_note)
    context = LeagueContext.from_clubs([home, away])
    home_lineup, away_lineup = pick_best_formation(home), pick_best_formation(away)
    results = []
    i = 0
    while len(results) < n:
        result = _simulate_one(home, away, context, home_lineup, away_lineup, date=str(i))
        if result is not None:
            results.append(result)
        i += 1
    return results


def _synthetic_match_result(*, goals: list[GoalEvent], home_goals: int, away_goals: int, date: str = "synthetic"):
    """Construit un `MatchResult` avec des buts CHOISIS À LA MAIN (Tâche 2.1-
    2.3 : cas limites précis, pas de recherche aléatoire dans 1000 matchs)."""
    home, away = _clubs()
    home_lineup, away_lineup = pick_best_formation(home), pick_best_formation(away)
    home_squad = [PlayerMatchStat(player_name=p.name, club_name=home.name, poste=p.poste, started=True) for p in home.players]
    away_squad = [PlayerMatchStat(player_name=p.name, club_name=away.name, poste=p.poste, started=True) for p in away.players]
    events = MatchEvents(
        home_formation=home_lineup.formation, away_formation=away_lineup.formation,
        home_lineup=home_squad, away_lineup=away_squad, goals=goals,
    )
    match = Match(home=home.name, away=away.name, home_goals=home_goals, away_goals=away_goals, events=events)
    return match_result_from(match, events, home_lineup, away_lineup, date=date)


class TestDeterminism:
    def test_timeline_deterministic(self):
        [match] = _simulate_n(1)
        first = build_timeline(match)
        second = build_timeline(match)
        assert first == second  # egalite profonde (dataclasses frozen, comparaison structurelle)

    def test_timeline_seed_varies_between_matches(self):
        results = _simulate_n(2)
        timelines = [build_timeline(r) for r in results]
        assert timelines[0].seed != timelines[1].seed
        occasions_0 = [(e.gabarit, e.minute) for e in timelines[0].events if e.event_type != BUT]
        occasions_1 = [(e.gabarit, e.minute) for e in timelines[1].events if e.event_type != BUT]
        assert occasions_0 != occasions_1


@pytest.fixture(scope="module")
def timelines_1000():
    results = _simulate_n(_N_MATCHES)
    return [(m, build_timeline(m)) for m in results]


class TestScoreInvariant:
    def test_timeline_preserves_score(self, timelines_1000):
        violations = []
        for match, timeline in timelines_1000:
            real_goals = sorted((g.minute, g.scorer, g.club_name) for g in match.goals)
            timeline_goals = sorted(
                (e.minute, e.main_player, e.team) for e in timeline.events if e.event_type == BUT
            )
            if real_goals != timeline_goals:
                violations.append((timeline.match_id, "buts differents", real_goals, timeline_goals))
                continue

            non_goal_but_tagged = [e for e in timeline.events if e.event_type != BUT and e.outcome == "but"]
            if non_goal_but_tagged:
                violations.append((timeline.match_id, "occasion taguee but", non_goal_but_tagged))
                continue

            recomputed_home = sum(1 for e in timeline.events if e.event_type == BUT and e.team == match.home_team)
            recomputed_away = sum(1 for e in timeline.events if e.event_type == BUT and e.team == match.away_team)
            if (recomputed_home, recomputed_away) != (match.home_goals, match.away_goals):
                violations.append((timeline.match_id, "score recalcule different", recomputed_home, recomputed_away))

        taux = len(violations) / len(timelines_1000)
        assert not violations, f"{len(violations)}/{len(timelines_1000)} violations ({taux:.2%}) -- exemples: {violations[:3]}"

    def test_timeline_events_sorted_by_minute(self, timelines_1000):
        violations = []
        for _match, timeline in timelines_1000:
            minutes = [e.minute for e in timeline.events]
            if minutes != sorted(minutes):
                violations.append((timeline.match_id, minutes))
        taux = len(violations) / len(timelines_1000)
        assert not violations, f"{len(violations)}/{len(timelines_1000)} violations ({taux:.2%}) -- exemples: {violations[:3]}"


class TestRatingModulation:
    def test_timeline_occasion_share_tracks_rating(self):
        # Ecart de rating attaque delibere et large (80 vs 45) pour isoler
        # la variable testee -- chi2 d'homogeneite (implementation directe,
        # meme methode que tests/test_templates.py::_chi_square_homogeneity,
        # pas de scipy dans ce projet) sur la repartition des occasions
        # (buts + intercalees) home vs away, H0 = repartition 50/50.
        results = _simulate_n(_N_MATCHES, home_note=80.0, away_note=45.0)
        home_team, away_team = results[0].home_team, results[0].away_team

        home_count = away_count = 0
        for match in results:
            timeline = build_timeline(match)
            for event in timeline.events:
                if event.team == home_team:
                    home_count += 1
                elif event.team == away_team:
                    away_count += 1

        total = home_count + away_count
        expected = total / 2
        chi2 = ((home_count - expected) ** 2 / expected) + ((away_count - expected) ** 2 / expected)
        # ddl=1, seuil chi2 a p<0.001 = 10.828 -- barre volontairement haute
        # (pas juste p<0.05) puisqu'on teste sur 1000 matchs, un ecart reel
        # doit etre tres largement significatif, pas juste au-dessus du seuil.
        critical_chi2_p001 = 10.828
        assert home_count > away_count, f"home={home_count} away={away_count} -- l'equipe la mieux notee devrait produire plus d'occasions"
        assert chi2 > critical_chi2_p001, f"chi2={chi2:.2f} (seuil p<0.001={critical_chi2_p001}) -- home={home_count} away={away_count} sur {total}"


class TestCyclicPatternDetectionUnit:
    """Tests unitaires directs de `_has_cyclic_pattern`, indépendants des
    1000 matchs -- vérifie l'algorithme lui-même sur des cas construits."""

    def test_detects_period_2_alternation(self):
        assert _has_cyclic_pattern(["corner", "contre_attaque", "corner", "contre_attaque"])

    def test_detects_period_1_immediate_repeat(self):
        assert _has_cyclic_pattern(["corner", "corner"])

    def test_no_false_positive_on_varied_sequence(self):
        assert not _has_cyclic_pattern(["corner", "contre_attaque", "une_deux", "penalty", "but_gag"])

    def test_period_6_is_not_flagged_beyond_max_period_5(self):
        seq = ["a", "b", "c", "d", "e", "f", "a", "b", "c", "d", "e", "f"]
        assert not _has_cyclic_pattern(seq, max_period=5)


class TestConstraintPriority:
    """Brief "constraint priority" (23/09/2026), Tâche 2 -- cinq tests."""

    def test_two_goals_same_minute_accepted(self):
        goals = [
            GoalEvent(club_name="Home FC", scorer="home_cf0", assist=None, minute=30, penalty=False),
            GoalEvent(club_name="Away FC", scorer="away_cf0", assist=None, minute=30, penalty=False),
        ]
        match = _synthetic_match_result(goals=goals, home_goals=1, away_goals=1)

        timeline = build_timeline(match)  # ne doit lever aucune exception
        but_events = [e for e in timeline.events if e.event_type == BUT]
        assert len(but_events) == 2
        assert {e.main_player for e in but_events} == {"home_cf0", "away_cf0"}
        assert all(e.minute == 30 for e in but_events)

        # Determinisme a la relance : ordre stable (Tache 1.3, tri secondaire
        # = ordre d'apparition dans match.goals, jamais aleatoire).
        second = build_timeline(match)
        assert [e.main_player for e in timeline.events if e.event_type == BUT] == [
            e.main_player for e in second.events if e.event_type == BUT
        ]
        assert timeline == second

    def test_consecutive_goals_same_scorer_accepted(self):
        goals = [
            GoalEvent(club_name="Home FC", scorer="home_cf0", assist=None, minute=10, penalty=False),
            GoalEvent(club_name="Home FC", scorer="home_cf0", assist=None, minute=12, penalty=False),
        ]
        match = _synthetic_match_result(goals=goals, home_goals=2, away_goals=0)

        timeline = build_timeline(match)  # ne doit lever aucune exception
        but_events = sorted((e for e in timeline.events if e.event_type == BUT), key=lambda e: e.minute)
        assert [e.main_player for e in but_events] == ["home_cf0", "home_cf0"]  # repetition ACCEPTEE, c'est le reel

    def test_consecutive_penalties_accepted(self):
        goals = [
            GoalEvent(club_name="Home FC", scorer="home_cf0", assist=None, minute=20, penalty=True),
            GoalEvent(club_name="Home FC", scorer="home_cf1", assist=None, minute=25, penalty=True),
        ]
        match = _synthetic_match_result(goals=goals, home_goals=2, away_goals=0)

        timeline = build_timeline(match)  # ne doit lever aucune exception
        but_events = sorted((e for e in timeline.events if e.event_type == BUT), key=lambda e: e.minute)
        assert [e.gabarit for e in but_events] == ["penalty", "penalty"]  # repetition ACCEPTEE, c'est le reel

    def test_generated_events_respect_anti_repetition(self, timelines_1000):
        # Verifie les 4 regles UNIQUEMENT sur generated_events (event_type ==
        # OCCASION) -- pas de liste d'exclusion, verifie sur les 1000 matchs.
        pair_violations, player_violations, gap_violations, cyclic_violations = [], [], [], []
        for _match, timeline in timelines_1000:
            generated = [e for e in timeline.events if e.event_type == OCCASION]

            couples = [(e.gabarit, e.declinaison) for e in generated]
            if any(a == b for a, b in zip(couples, couples[1:])):
                pair_violations.append(timeline.match_id)

            players = [e.main_player for e in generated]
            if any(a == b for a, b in zip(players, players[1:])):
                player_violations.append(timeline.match_id)

            minutes = sorted(e.minute for e in generated)
            if any((b - a) < _MIN_MINUTE_GAP for a, b in zip(minutes, minutes[1:])):
                gap_violations.append(timeline.match_id)

            if _has_cyclic_pattern([e.gabarit for e in generated]):
                cyclic_violations.append(timeline.match_id)

        assert not pair_violations, f"{len(pair_violations)} violations (gabarit,declinaison) sur generated_events -- exemples: {pair_violations[:3]}"
        assert not player_violations, f"{len(player_violations)} violations joueur principal sur generated_events -- exemples: {player_violations[:3]}"
        assert not gap_violations, f"{len(gap_violations)} violations ecart minimum sur generated_events -- exemples: {gap_violations[:3]}"
        assert not cyclic_violations, f"{len(cyclic_violations)} patterns cycliques sur generated_events -- exemples: {cyclic_violations[:3]}"

    def test_audit_no_match_rejected(self):
        # Propriete structurelle qui remplace le contournement par rejet
        # (MinuteCollisionError/AntiRepetitionUnsatisfiableError retirees) :
        # build_timeline ne doit JAMAIS lever, y compris sur les cas limites
        # (collisions de minute, buteurs/penalties consecutifs -- voir les
        # 3 tests precedents pour ces cas precis construits a la main).
        results = _simulate_n(_N_MATCHES)
        n_built = 0
        for match in results:
            build_timeline(match)  # toute exception ici fait echouer le test
            n_built += 1
        assert n_built == _N_MATCHES

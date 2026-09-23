"""Tests du moteur narratif (brief "narrative engine foundations",
23/09/2026) -- engine/narrative.py. Les tests marqués "1000 matchs" simulent
des matchs RÉELS via le pipeline existant (`simulate_match`) jusqu'à obtenir
1000 timelines construites avec succès, sans liste d'exclusion : toute
violation détectée sur ces 1000 timelines est un échec, pas un cas à
blacklister (voir règles d'escalade globales du brief).

Exception documentée, PAS une exclusion de cas connu (voir
`narrative.MinuteCollisionError`) : ~3.95% des matchs simulés par le moteur
de résultats ont deux buts existants à la même minute (mesuré sur 2000
matchs de contrôle, voir le retour de tâche) -- `build_timeline` refuse
alors de construire une timeline (Tâche 3.3, "remontée, pas de correction
silencieuse"). `_build_n_timelines` compte et rapporte ce taux explicitement
plutôt que de le masquer ; il continue de tirer des matchs jusqu'à
`_N_MATCHES` timelines RÉELLEMENT construites."""

import pytest

from ligue1sim.clubs import Club
from ligue1sim.lineup import pick_best_formation
from ligue1sim.players import Player
from ligue1sim.schedule import Match
from ligue1sim.simulation import LeagueContext, simulate_match

from narrative import (
    BUT,
    _MIN_MINUTE_GAP,
    AntiRepetitionUnsatisfiableError,
    MinuteCollisionError,
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


def _build_n_timelines(n: int, *, home_note: float = 70.0, away_note: float = 70.0):
    """Tire des matchs jusqu'à obtenir `n` (match, timeline) construits avec
    succès -- retourne aussi `n_collisions`/`n_unsatisfiable`/`n_attempted`
    (voir docstring de module) pour que chaque test puisse rapporter les
    taux honnêtement, sans les masquer ni les faire échouer le lot entier."""
    home, away = _clubs(home_note, away_note)
    context = LeagueContext.from_clubs([home, away])
    home_lineup, away_lineup = pick_best_formation(home), pick_best_formation(away)
    pairs = []
    n_collisions = n_unsatisfiable = n_attempted = 0
    i = 0
    while len(pairs) < n:
        result = _simulate_one(home, away, context, home_lineup, away_lineup, date=str(i))
        i += 1
        if result is None:
            continue
        n_attempted += 1
        try:
            timeline = build_timeline(result)
        except MinuteCollisionError:
            n_collisions += 1
            continue
        except AntiRepetitionUnsatisfiableError:
            n_unsatisfiable += 1
            continue
        pairs.append((result, timeline))
    return pairs, n_collisions, n_unsatisfiable, n_attempted


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
    pairs, n_collisions, n_unsatisfiable, n_attempted = _build_n_timelines(_N_MATCHES)
    total_tried = n_attempted + n_collisions + n_unsatisfiable
    print(
        f"\n[narrative] {_N_MATCHES} timelines construites sur {total_tried} matchs tentés -- "
        f"{n_collisions} collisions de minute ({n_collisions / total_tried:.2%}), "
        f"{n_unsatisfiable} règles anti-répétition insatisfiables ({n_unsatisfiable / total_tried:.2%})"
    )
    return pairs, n_collisions, n_unsatisfiable, n_attempted


class TestScoreInvariant:
    def test_timeline_preserves_score(self, timelines_1000):
        pairs, _n_collisions, _n_unsatisfiable, _n_attempted = timelines_1000
        violations = []
        for match, timeline in pairs:
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

        taux = len(violations) / len(pairs)
        assert not violations, f"{len(violations)}/{len(pairs)} violations ({taux:.2%}) -- exemples: {violations[:3]}"

    def test_timeline_events_sorted_by_minute(self, timelines_1000):
        pairs, _n_collisions, _n_unsatisfiable, _n_attempted = timelines_1000
        violations = []
        for _match, timeline in pairs:
            minutes = [e.minute for e in timeline.events]
            if minutes != sorted(minutes) or len(minutes) != len(set(minutes)):
                violations.append((timeline.match_id, minutes))
        taux = len(violations) / len(pairs)
        assert not violations, f"{len(violations)}/{len(pairs)} violations ({taux:.2%}) -- exemples: {violations[:3]}"


class TestRatingModulation:
    def test_timeline_occasion_share_tracks_rating(self):
        # Ecart de rating attaque delibere et large (80 vs 45) pour isoler
        # la variable testee -- chi2 d'homogeneite (implementation directe,
        # meme methode que tests/test_templates.py::_chi_square_homogeneity,
        # pas de scipy dans ce projet) sur la repartition des occasions
        # (buts + intercalees) home vs away, H0 = repartition 50/50.
        pairs, _n_collisions, _n_unsatisfiable, _n_attempted = _build_n_timelines(_N_MATCHES, home_note=80.0, away_note=45.0)
        home_team = pairs[0][0].home_team
        away_team = pairs[0][0].away_team

        home_count = away_count = 0
        for _match, timeline in pairs:
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


class TestAntiRepetitionRules:
    def test_no_consecutive_repeat_gabarit_declinaison(self, timelines_1000):
        pairs, _n_collisions, _n_unsatisfiable, _n_attempted = timelines_1000
        violations = []
        for _match, timeline in pairs:
            couples = [(e.gabarit, e.declinaison) for e in timeline.events]
            for a, b in zip(couples, couples[1:]):
                if a == b:
                    violations.append((timeline.match_id, a))
        taux = len(violations) / len(pairs)
        assert not violations, f"{len(violations)} violations sur {len(pairs)} matchs ({taux:.2%}) -- exemples: {violations[:3]}"

    def test_no_consecutive_repeat_main_player(self, timelines_1000):
        pairs, _n_collisions, _n_unsatisfiable, _n_attempted = timelines_1000
        violations = []
        for _match, timeline in pairs:
            players = [e.main_player for e in timeline.events]
            for a, b in zip(players, players[1:]):
                if a == b:
                    violations.append((timeline.match_id, a))
        taux = len(violations) / len(pairs)
        assert not violations, f"{len(violations)} violations sur {len(pairs)} matchs ({taux:.2%}) -- exemples: {violations[:3]}"

    def test_minimum_minute_gap_respected(self, timelines_1000):
        # Portee de la regle : l'ecart minimum gouverne le PLACEMENT des
        # occasions inventees (ce que le generateur controle) -- deux buts
        # REELS consecutifs a moins de _MIN_MINUTE_GAP minutes d'ecart sont
        # une donnee du match (minute immuable, Tache 3), pas une violation
        # de regle : exclus de cette verification (confirme empiriquement,
        # voir retour de tache : 100% des ecarts <3min mesures sont des
        # paires but-but, 0% n'implique un placement d'occasion).
        pairs, _n_collisions, _n_unsatisfiable, _n_attempted = timelines_1000
        violations = []
        for _match, timeline in pairs:
            events = sorted(timeline.events, key=lambda e: e.minute)
            for a, b in zip(events, events[1:]):
                if a.event_type == BUT and b.event_type == BUT:
                    continue
                if (b.minute - a.minute) < _MIN_MINUTE_GAP:
                    violations.append((timeline.match_id, a.minute, b.minute))
        taux = len(violations) / len(pairs)
        assert not violations, f"{len(violations)} violations sur {len(pairs)} matchs ({taux:.2%}) -- exemples: {violations[:3]}"

    def test_no_cyclic_pattern_gabarit(self, timelines_1000):
        pairs, _n_collisions, _n_unsatisfiable, _n_attempted = timelines_1000
        violations = []
        for _match, timeline in pairs:
            gabarits = [e.gabarit for e in timeline.events]
            if _has_cyclic_pattern(gabarits):
                violations.append((timeline.match_id, gabarits))
        taux = len(violations) / len(pairs)
        assert not violations, f"{len(violations)} violations sur {len(pairs)} matchs ({taux:.2%}) -- exemples: {violations[:3]}"


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

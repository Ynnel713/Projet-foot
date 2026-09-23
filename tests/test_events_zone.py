"""Le champ `zone` ajouté à chaque événement (voir events.py, docs/
simulation_physique_archi.md) ne doit RIEN changer aux tirages existants
(score, buteur, minute, carton...) -- non-régression stricte vérifiée sur
1000 matchs contre un instantané pré-zone (voir TestNoRegression), en plus
des règles de zone par type d'événement.
"""

import json
import random
from pathlib import Path

import numpy as np

from ligue1sim.clubs import Club
from ligue1sim.events import PENALTY_SPOT_ZONE, generate_match_events
from ligue1sim.lineup import pick_best_formation
from ligue1sim.pitch_geometry import GRID_COLUMNS, GRID_ROWS
from ligue1sim.players import Player

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "event_regression_snapshot.json"


def _player(poste: str, note: float, name: str) -> Player:
    return Player(
        prenom=name, nom="", nationalite="France", age=25, poste=poste, note=note, club="Test FC", championnat="TEST"
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


def _play(seed: int, home_goals: int, away_goals: int, **kwargs):
    """Seede LES DEUX flux de randomness utilisés par le moteur (`random`
    ET `np.random`, via `_weighted_choice`) -- indispensable pour un match
    reproductible : `np.random` n'est réamorcé nulle part ailleurs dans le
    module, seul `random.seed` l'était jusqu'ici (voir TestNoRegression,
    qui a justement mis ce trou en évidence)."""
    random.seed(seed)
    np.random.seed(seed)
    home, away = _clubs()
    home_lineup = pick_best_formation(home)
    away_lineup = pick_best_formation(away)
    random.seed(seed)
    np.random.seed(seed)
    return generate_match_events(home, away, home_lineup, away_lineup, home_goals, away_goals, **kwargs)


def _many_events(nb_matches: int = 150, seed_offset: int = 10_000):
    """Rejoue `nb_matches` matchs à score élevé (beaucoup de buts/passes) et
    agrège tous les événements produits, pour disposer d'un échantillon
    assez large pour couvrir les événements rares (penalty manqué : 5% de
    chance par match, voir P_MATCH_HAS_MISSED_PENALTY)."""
    goals, cards, subs, injuries, penalties = [], [], [], [], []
    for i in range(nb_matches):
        events = _play(seed_offset + i, home_goals=4, away_goals=4)
        goals += events.goals
        cards += events.cards
        subs += events.substitutions
        injuries += events.injuries
        penalties += events.penalties_missed
    return goals, cards, subs, injuries, penalties


class TestNoRegression:
    def test_1000_matches_produce_identical_non_zone_events_before_and_after(self):
        """Rejoue les 1000 matchs de la fixture (générée par le code AVANT
        l'ajout du champ zone, avec le même double seed) et compare tout
        sauf zone/assist_zone -- la moindre différence prouverait que
        l'ajout des zones a perturbé un tirage existant."""
        with FIXTURE_PATH.open(encoding="utf-8") as f:
            snapshot = json.load(f)
        assert len(snapshot) == 1000

        mismatches = []
        for expected in snapshot:
            seed = expected["seed"]
            home_goals = seed % 6
            away_goals = (seed // 6) % 6
            events = _play(seed, home_goals, away_goals)

            actual = {
                "home_goals": home_goals,
                "away_goals": away_goals,
                "goals": [
                    {"club_name": g.club_name, "scorer": g.scorer, "assist": g.assist, "minute": g.minute, "penalty": g.penalty}
                    for g in events.goals
                ],
                "cards": [
                    {"club_name": c.club_name, "player": c.player, "minute": c.minute, "card_type": c.card_type}
                    for c in events.cards
                ],
                "substitutions": [
                    {"club_name": s.club_name, "player_off": s.player_off, "player_on": s.player_on, "minute": s.minute}
                    for s in events.substitutions
                ],
                "injuries": [
                    {"club_name": inj.club_name, "player": inj.player, "minute": inj.minute} for inj in events.injuries
                ],
                "penalties_missed": [
                    {"club_name": p.club_name, "player": p.player, "minute": p.minute} for p in events.penalties_missed
                ],
                "ratings": [
                    {"player_name": s.player_name, "rating": s.rating} for s in events.home_lineup + events.away_lineup
                ],
            }
            if actual != {key: expected[key] for key in actual}:
                mismatches.append(seed)

        assert not mismatches, f"{len(mismatches)}/1000 match(es) diffèrent du snapshot pré-zone (seeds: {mismatches[:10]}...)"


class TestZonePopulation:
    def test_every_event_carries_a_zone(self):
        goals, cards, subs, injuries, penalties = _many_events()
        assert goals and cards and subs and injuries and penalties  # échantillon suffisant, sinon les asserts suivants sont vides
        assert all(g.zone is not None for g in goals)
        assert all(c.zone is not None for c in cards)
        assert all(s.zone is not None for s in subs)
        assert all(i.zone is not None for i in injuries)
        assert all(p.zone is not None for p in penalties)

    def test_assist_zone_is_populated_if_and_only_if_there_is_an_assist(self):
        goals, *_ = _many_events()
        assert any(g.assist is not None for g in goals)
        assert any(g.assist is None for g in goals)
        for g in goals:
            if g.assist is None:
                assert g.assist_zone is None
            else:
                assert g.assist_zone is not None


class TestZoneRules:
    def test_non_penalty_goal_zone_is_close_to_the_opponents_box(self):
        goals, *_ = _many_events()
        open_play_goals = [g for g in goals if not g.penalty]
        assert open_play_goals
        for g in open_play_goals:
            assert g.zone.col >= GRID_COLUMNS - 3

    def test_assist_zone_is_further_from_goal_than_the_shot_it_creates(self):
        goals, *_ = _many_events()
        assisted_goals = [g for g in goals if g.assist_zone is not None]
        assert assisted_goals
        for g in assisted_goals:
            assert g.assist_zone.col < g.zone.col

    def test_penalty_goal_zone_is_always_the_penalty_spot(self):
        goals, *_ = _many_events()
        penalty_goals = [g for g in goals if g.penalty]
        assert penalty_goals
        for g in penalty_goals:
            assert g.zone == PENALTY_SPOT_ZONE

    def test_missed_penalty_zone_is_always_the_penalty_spot(self):
        *_, penalties = _many_events()
        assert penalties
        for p in penalties:
            assert p.zone == PENALTY_SPOT_ZONE

    def test_card_and_injury_zones_stay_within_the_grid(self):
        _, cards, _, injuries, _ = _many_events()
        for event in cards + injuries:
            assert 0 <= event.zone.col < GRID_COLUMNS
            assert 0 <= event.zone.row < GRID_ROWS

    def test_substitution_zone_sits_on_a_touchline(self):
        _, _, subs, _, _ = _many_events()
        for s in subs:
            assert s.zone.row in (0, GRID_ROWS - 1)


class TestDeterminism:
    def test_same_match_id_gives_identical_zones_across_two_independent_runs(self):
        events_a = _play(123, home_goals=3, away_goals=2, match_id="match-42")
        events_b = _play(123, home_goals=3, away_goals=2, match_id="match-42")

        assert [g.zone for g in events_a.goals] == [g.zone for g in events_b.goals]
        assert [c.zone for c in events_a.cards] == [c.zone for c in events_b.cards]
        assert events_a.goals  # sanity : au moins un but à comparer

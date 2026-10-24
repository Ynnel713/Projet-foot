"""Calibration de la décision du porteur (V2, ticket v2-cerveau-joueurs/01) : simule des matchs
complets entre clubs de Ligue 1 et mesure tirs par équipe et buts par match, à comparer aux
fourchettes validées (8 à 15 tirs par équipe, 2 à 3,5 buts par match).

Usage : uv run python -m scripts.measure_v2_decisions [nombre_de_matchs] [SHOT_WEIGHT=.. PASS_WEIGHT=.. DRIBBLE_WEIGHT=..]"""

from __future__ import annotations

import random
import statistics
import sys
from collections import Counter

from ligue1sim.clubs import load_clubs
from ligue1sim.season import CLUBS_PATH

import v2engine.decision as decision
import v2engine.match as match

AUDIT_SEED = 20260923


def main(n_matches: int) -> None:
    clubs = load_clubs(CLUBS_PATH, "Ligue 1")
    real_attempt_shot = match.attempt_shot
    actions: Counter[str] = Counter()
    real_choose = match.choose_action
    shots: Counter[str] = Counter()

    def counting_shot(shooter, *args):
        shots[shooter.team] += 1
        return real_attempt_shot(shooter, *args)

    def counting_choose(*args):
        action = real_choose(*args)
        actions[action.kind] += 1
        return action

    match.attempt_shot = counting_shot
    match.choose_action = counting_choose
    shots_per_team, goals_per_match = [], []
    for i in range(n_matches):
        random.seed(AUDIT_SEED + i)
        home, away = clubs[(2 * i) % len(clubs)], clubs[(2 * i + 1) % len(clubs)]
        shots.clear()
        trace = match.simulate_match(home, away)
        shots_per_team += [shots["home"], shots["away"]]
        goals_per_match.append(trace.home_goals + trace.away_goals)
        print(f"{home.name} {trace.home_goals}-{trace.away_goals} {away.name}  tirs {shots['home']}/{shots['away']}", flush=True)

    total = sum(actions.values())
    print(f"\nTirs par équipe : moyenne {statistics.mean(shots_per_team):.1f} (cible 8-15)")
    print(f"Buts par match  : moyenne {statistics.mean(goals_per_match):.2f} (cible 2-3,5)")
    print("Choix du porteur : " + ", ".join(f"{k} {v / total:.0%}" for k, v in actions.most_common()))


if __name__ == "__main__":
    for override in sys.argv[2:]:  # essai de poids de calibration sans modifier le code
        name, value = override.split("=")
        setattr(decision, name, float(value))
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 10)

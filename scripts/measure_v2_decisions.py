"""Calibration de la décision du porteur (V2, ticket v2-cerveau-joueurs/01) : simule des matchs
complets entre clubs de Ligue 1 et mesure tirs par équipe et buts par match, à comparer aux
fourchettes validées (8 à 15 tirs par équipe, 2 à 3,5 buts par match).

Usage : uv run python -m scripts.measure_v2_decisions [nombre_de_matchs] [SHOT_WEIGHT=.. PASS_WEIGHT=.. DRIBBLE_WEIGHT=..] [attr:Vision=90]

`attr:<Attribut>=<note>` force cette note pour TOUS les joueurs dans les décisions (comparaison note haute / basse
à situation égale, critère « écart mesuré en match » des tickets v2-cerveau-joueurs)."""

from __future__ import annotations

import random
import statistics
import sys
from collections import Counter

from ligue1sim.clubs import load_clubs
from ligue1sim.season import CLUBS_PATH

import v2engine.decision as decision
import v2engine.match as match
import v2engine.off_ball as off_ball

AUDIT_SEED = 20260923


def main(n_matches: int) -> None:
    clubs = load_clubs(CLUBS_PATH, "Ligue 1")
    real_attempt_shot = match.attempt_shot
    actions: Counter[str] = Counter()
    real_choose = match.choose_action
    shots: Counter[str] = Counter()
    pass_lengths: list[float] = []
    real_pass_velocity = match.pass_velocity

    spaces: list[float] = []  # distance à l'adversaire le plus proche des coéquipiers du porteur (Off the Ball)
    real_step_ball = match._step_ball
    calls = Counter()

    def sampling_step_ball(ball, dt, players, now_s=0.0):
        calls["n"] += 1
        if ball.holder is not None and calls["n"] % 10 == 0:
            holder = next((p for p in players if p.name == ball.holder), None)
            if holder is not None:
                opponents = [p for p in players if p.team != holder.team]
                for mate in players:
                    if mate.team == holder.team and mate is not holder and mate.poste != "GK":
                        spaces.append(min(mate.position.distance_to(o.position) for o in opponents))
        return real_step_ball(ball, dt, players, now_s)

    def counting_pass(passer, target):
        pass_lengths.append(passer.position.distance_to(target.position))
        return real_pass_velocity(passer, target)

    def counting_shot(shooter, *args):
        shots[shooter.team] += 1
        return real_attempt_shot(shooter, *args)

    def counting_choose(*args):
        action = real_choose(*args)
        actions[action.kind] += 1
        return action

    match.attempt_shot = counting_shot
    match.choose_action = counting_choose
    match.pass_velocity = counting_pass
    match._step_ball = sampling_step_ball
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
    long_share = sum(d > 25.0 for d in pass_lengths) / max(1, len(pass_lengths))
    print(f"Passes : {len(pass_lengths)}, dont {long_share:.1%} de plus de 25 m")
    print(f"Espace des coéquipiers du porteur : {statistics.mean(spaces):.2f} m de l'adversaire le plus proche")
    print("Choix du porteur : " + ", ".join(f"{k} {v / total:.0%}" for k, v in actions.most_common()))


if __name__ == "__main__":
    forced: dict[str, int] = {}
    for override in sys.argv[2:]:  # essai de poids de calibration sans modifier le code
        name, value = override.split("=")
        if name.startswith("attr:"):
            forced[name[5:]] = int(value)
        else:
            setattr(decision, name, float(value))
    if forced:
        real_attribute = decision.player_attribute
        forced_attribute = lambda player, name, default=60: forced.get(name, real_attribute(player, name, default))  # noqa: E731
        decision.player_attribute = forced_attribute
        off_ball.player_attribute = forced_attribute
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 10)

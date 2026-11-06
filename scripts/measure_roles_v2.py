"""Position moyenne en possession par rôle (ticket v2-realisme/02d) : N matchs, graines fixes (celles de
`measure_v2`), progression vers le but adverse (m, 0 = son but) et écart à l'axe (m), par rôle et par poste.

Usage : uv run python -m scripts.measure_roles_v2 [nombre_de_matchs] [--sans-role]
`--sans-role` : neutralise `ROLE_PLACE_WITH_BALL` (comportement d'avant 02d), pour comparer à graines égales."""

from __future__ import annotations

import argparse
import random
import statistics
from collections import defaultdict

from ligue1sim.clubs import load_clubs
from ligue1sim.season import CLUBS_PATH

import v2engine.bloc as bloc
import v2engine.match as match
from scripts.measure_v2 import AUDIT_SEED, TICK_S


def run(n_matches: int) -> dict[tuple[str, str], list[tuple[float, float]]]:
    clubs = load_clubs(CLUBS_PATH, "Ligue 1")
    samples: dict[tuple[str, str], list[tuple[float, float]]] = defaultdict(list)
    for i in range(n_matches):
        random.seed(AUDIT_SEED + i)
        home, away = clubs[(2 * i) % len(clubs)], clubs[(2 * i + 1) % len(clubs)]

        def observer(now_s, players, ball, scoring_team):
            holder = next((p for p in players if p.name == ball.holder), None) if ball.holder else None
            if holder is None:
                return
            for p in players:
                if p.team == holder.team and p.poste != "GK":
                    progress = p.position.x if p.team == "home" else 105.0 - p.position.x
                    samples[(p.role, p.poste)].append((progress, abs(p.position.y - 34.0)))
        match.simulate_match(home, away, tick_seconds=TICK_S, observer=observer)
    return samples


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("matches", nargs="?", type=int, default=20)
    parser.add_argument("--sans-role", action="store_true")
    args = parser.parse_args()
    if args.sans_role:
        bloc.ROLE_PLACE_WITH_BALL = {}
    samples = run(args.matches)
    print(f"{'rôle':<20}{'poste':<6}{'n joueurs-ticks':>16}{'progression (m)':>17}{'écart à l axe (m)':>19}")
    for (role, poste), pts in sorted(samples.items(), key=lambda kv: statistics.fmean(p[0] for p in kv[1])):
        print(f"{role or '-':<20}{poste:<6}{len(pts):>16}{statistics.fmean(p[0] for p in pts):>17.1f}"
              f"{statistics.fmean(p[1] for p in pts):>19.1f}")


if __name__ == "__main__":
    main()

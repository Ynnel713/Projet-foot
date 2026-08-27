"""Script de calibration du moteur de match : simule un grand nombre de
saisons via le pipeline RÉEL (`Season`, avec sa propre `FormTracker` et ses
propres indisponibilités -- pas une réimplémentation séparée des formules)
et rapporte les indicateurs statistiques utilisés pour valider chaque
réglage du moteur (voir `simulation.py` pour l'historique de calibrage).

Usage :
    uv run python scripts/calibrate_engine.py [championnat] [nb_saisons]

Exemple :
    uv run python scripts/calibrate_engine.py "Ligue 1" 50
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from ligue1sim.lineup import club_strength  # noqa: E402
from ligue1sim.season import CLUBS_PATH, Season  # noqa: E402
from ligue1sim.clubs import load_clubs  # noqa: E402


def run(championnat: str, n_seasons: int) -> None:
    clubs = load_clubs(CLUBS_PATH, championnat)
    ratings = {c.name: club_strength(c) for c in clubs}

    hg_all: list[int] = []
    ag_all: list[int] = []
    gap_all: list[float] = []
    champion_points: list[int] = []
    last_points: list[int] = []

    for _ in range(n_seasons):
        season = Season(championnat, load_clubs(CLUBS_PATH, championnat))
        points = {c.name: 0 for c in season.clubs}
        while not season.is_season_over:
            season.simulate_current_journee()
            for match in season.current_journee.matches:
                if match.played:
                    hg_all.append(match.home_goals)
                    ag_all.append(match.away_goals)
                    gap_all.append(ratings[match.home] - ratings[match.away])
                    if match.home_goals > match.away_goals:
                        points[match.home] += 3
                    elif match.home_goals < match.away_goals:
                        points[match.away] += 3
                    else:
                        points[match.home] += 1
                        points[match.away] += 1
            season.next_journee()

        standings = sorted(points.values(), reverse=True)
        champion_points.append(standings[0])
        last_points.append(standings[-1])

    hg = np.array(hg_all)
    ag = np.array(ag_all)
    diff = hg - ag
    total = hg + ag
    gap = np.array(gap_all)
    n = len(hg)

    print(f"\n{'=' * 70}\n{championnat} -- {n_seasons} saisons simulées ({n} matchs)\n{'=' * 70}")

    print("\n--- Distribution des résultats ---")
    print(f"Victoire domicile : {100 * (diff > 0).sum() / n:.1f}%")
    print(f"Nul               : {100 * (diff == 0).sum() / n:.1f}%")
    print(f"Victoire extérieur: {100 * (diff < 0).sum() / n:.1f}%")

    print("\n--- Distribution du nombre total de buts ---")
    counts = Counter(np.minimum(total, 6).tolist())
    for k in range(7):
        label = "6+" if k == 6 else str(k)
        print(f"{label} but(s): {100 * counts.get(k, 0) / n:.1f}%")
    print(f"Moyenne buts/match: {total.mean():.2f}")

    print("\n--- Matrice des scores (12 plus fréquents) ---")
    score_counts = Counter(zip(hg.tolist(), ag.tolist()))
    for (h, a), c in score_counts.most_common(12):
        print(f"{h}-{a}: {100 * c / n:.1f}%")

    print("\n--- Indicateurs ---")
    print(f"Taux de 0-0: {100 * score_counts.get((0, 0), 0) / n:.1f}%")
    print(f"Fréquence 5+ buts au total: {100 * (total >= 5).sum() / n:.1f}%")
    print(f"Fréquence écart >=3 buts: {100 * (np.abs(diff) >= 3).sum() / n:.1f}%")
    print(f"Clean sheets (au moins une équipe à 0): {100 * ((hg == 0) | (ag == 0)).sum() / n:.1f}%")

    print("\n--- Favori vs outsider par tranche d'écart de force ---")
    abs_gap = np.abs(gap)
    home_is_fav = gap > 0
    fav_diff = np.where(home_is_fav, diff, -diff)
    print(f"{'Écart':>10s} {'n':>6s} {'Fav. gagne':>10s} {'Nul':>6s} {'Fav. perd':>10s} {'Perd 2+':>8s} {'Perd 3+':>8s}")
    for lo, hi in ((0, 5), (5, 10), (10, 15), (15, 20), (20, 100)):
        mask = (abs_gap >= lo) & (abs_gap < hi)
        m = mask.sum()
        if m == 0:
            continue
        fd = fav_diff[mask]
        print(
            f"[{lo:2d}-{hi:3d}) {m:6d} {100 * (fd > 0).sum() / m:9.1f}% {100 * (fd == 0).sum() / m:5.1f}% "
            f"{100 * (fd < 0).sum() / m:9.1f}% {100 * (fd <= -2).sum() / m:7.1f}% {100 * (fd <= -3).sum() / m:7.1f}%"
        )

    print("\n--- Séparation du classement de saison ---")
    print(
        f"Champion: médiane={np.median(champion_points):.0f} "
        f"({min(champion_points)}-{max(champion_points)})   "
        f"Dernier: médiane={np.median(last_points):.0f}   "
        f"Écart 1er-dernier: médiane={np.median(np.array(champion_points) - np.array(last_points)):.0f}"
    )


if __name__ == "__main__":
    championnat = sys.argv[1] if len(sys.argv) > 1 else "Ligue 1"
    n_seasons = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    run(championnat, n_seasons)

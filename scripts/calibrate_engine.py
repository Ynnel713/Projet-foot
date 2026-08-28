"""Script de calibration du moteur de match : simule un grand nombre de
saisons via le pipeline RÉEL (`Season`, avec sa propre `FormTracker` et ses
propres indisponibilités -- pas une réimplémentation séparée des formules)
et rapporte les indicateurs statistiques utilisés pour valider chaque
réglage du moteur (voir `simulation.py` pour l'historique de calibrage).

Rapporte à la fois des stats MATCH PAR MATCH et, depuis le calibrage du
28/08/2026, la distribution du CLASSEMENT DE FIN DE SAISON par club (rang
moyen, présence en top 3 / dans le trio de relégation) -- le premier
calibrage (ATTACK_DEFENSE_POWER=1.8) ne vérifiait que les stats
match-par-match, qui restent quasi identiques à un réglage bien plus élevé
(2.6) alors que la corrélation force réelle <-> classement final, elle,
change nettement sur une saison entière. Toujours valider un futur réglage
sur les DEUX angles, pas seulement le premier.

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
    ranks: dict[str, list[int]] = {c.name: [] for c in clubs}

    for _ in range(n_seasons):
        season = Season(championnat, load_clubs(CLUBS_PATH, championnat))
        points = {c.name: 0 for c in season.clubs}
        goal_diff = {c.name: 0 for c in season.clubs}
        while not season.is_season_over:
            season.simulate_current_journee()
            for match in season.current_journee.matches:
                if match.played:
                    hg_all.append(match.home_goals)
                    ag_all.append(match.away_goals)
                    gap_all.append(ratings[match.home] - ratings[match.away])
                    gd = match.home_goals - match.away_goals
                    goal_diff[match.home] += gd
                    goal_diff[match.away] -= gd
                    if gd > 0:
                        points[match.home] += 3
                    elif gd < 0:
                        points[match.away] += 3
                    else:
                        points[match.home] += 1
                        points[match.away] += 1
            season.next_journee()

        # Classement de fin de saison : points puis différence de buts
        # (comme en vrai championnat), pour le rang de chaque club.
        order = sorted(points, key=lambda name: (-points[name], -goal_diff[name]))
        for rank, name in enumerate(order, start=1):
            ranks[name].append(rank)

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

    print("\n--- Rang de fin de saison par club (trié par note) ---")
    print("Vérifie que la force réelle d'un club se retrouve dans son classement sur")
    print("l'ensemble des saisons, pas seulement dans les stats match par match.")
    nb_clubs = len(clubs)
    print(f"{'Club':<28s}{'Note':>6s}{'Rang moy.':>10s}{'Top 3':>8s}{'Relég.':>8s}{'(min-max)':>12s}")
    for name, rating in sorted(ratings.items(), key=lambda kv: -kv[1]):
        rs = ranks[name]
        top3 = 100 * sum(1 for r in rs if r <= 3) / len(rs)
        relegation = 100 * sum(1 for r in rs if r > nb_clubs - 3) / len(rs)
        print(
            f"{name:<28s}{rating:6.1f}{np.mean(rs):10.2f}{top3:7.0f}%{relegation:7.0f}%"
            f"{'(' + str(min(rs)) + '-' + str(max(rs)) + ')':>12s}"
        )


if __name__ == "__main__":
    championnat = sys.argv[1] if len(sys.argv) > 1 else "Ligue 1"
    n_seasons = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    run(championnat, n_seasons)

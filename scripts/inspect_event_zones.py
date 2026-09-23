"""Heatmap texte des zones d'événements par type (but, passe décisive,
carton, remplacement, blessure, penalty manqué) -- vérification visuelle
rapide que la distribution des zones tirées par events.py (voir
docs/simulation_physique_archi.md) est plausible, avant de s'appuyer dessus
pour l'habillage visuel animé. Aucune dépendance graphique (matplotlib non
installé dans ce projet) : même convention texte-console que
scripts/calibrate_engine.py.

Usage :
    uv run python scripts/inspect_event_zones.py [nb_matchs]

Effectif synthétique auto-contenu (même squad que tests/test_events_zone.py)
-- aucune dépendance à data/joueurs.xlsx, donc aucun risque de verrou Excel.
"""

from __future__ import annotations

import random
import sys
from collections import Counter
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from ligue1sim.clubs import Club  # noqa: E402
from ligue1sim.events import MatchEvents, generate_match_events  # noqa: E402
from ligue1sim.lineup import pick_best_formation  # noqa: E402
from ligue1sim.pitch_geometry import GRID_COLUMNS, GRID_ROWS, Zone  # noqa: E402
from ligue1sim.players import Player  # noqa: E402


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


def _clubs() -> tuple[Club, Club]:
    return Club(name="Home FC", players=_squad("home")), Club(name="Away FC", players=_squad("away"))


def _collect(nb_matches: int) -> dict[str, list[Zone]]:
    """Rejoue `nb_matches` matchs (scores variés, dérivés du seed pour
    garantir des buts/passes dans chaque match) et regroupe toutes les
    zones tirées par type d'événement."""
    zones: dict[str, list[Zone]] = {
        "but (hors penalty)": [],
        "but sur penalty": [],
        "passe decisive": [],
        "carton": [],
        "remplacement": [],
        "blessure": [],
        "penalty manque": [],
    }
    for seed in range(nb_matches):
        random.seed(seed)
        np.random.seed(seed)
        home, away = _clubs()
        home_lineup = pick_best_formation(home)
        away_lineup = pick_best_formation(away)
        home_goals = 1 + seed % 4
        away_goals = 1 + (seed // 4) % 4
        random.seed(seed)  # reset des deux flux juste avant l'appel réel (voir tests/test_events_zone.py)
        np.random.seed(seed)
        events: MatchEvents = generate_match_events(home, away, home_lineup, away_lineup, home_goals, away_goals)

        for g in events.goals:
            zones["but sur penalty" if g.penalty else "but (hors penalty)"].append(g.zone)
            if g.assist_zone is not None:
                zones["passe decisive"].append(g.assist_zone)
        zones["carton"] += [c.zone for c in events.cards]
        zones["remplacement"] += [s.zone for s in events.substitutions]
        zones["blessure"] += [inj.zone for inj in events.injuries]
        zones["penalty manque"] += [p.zone for p in events.penalties_missed]
    return zones


def _print_heatmap(title: str, zone_list: list[Zone]) -> None:
    print(f"\n=== {title} ({len(zone_list)} echantillons) ===")
    if not zone_list:
        print("  (aucun echantillon -- augmenter nb_matchs pour un evenement rare)")
        return

    counts = Counter((z.col, z.row) for z in zone_list)
    print("  colonne 0 = but defendu, colonne 11 = but adverse ; tiers separes par |, ligne 0 = touche basse")
    for row in reversed(range(GRID_ROWS)):
        cells: list[str] = []
        for col in range(GRID_COLUMNS):
            if col in (GRID_COLUMNS // 3, 2 * GRID_COLUMNS // 3):
                cells.append("|")
            cells.append(f"{counts.get((col, row), 0):3d}")
        print("  " + " ".join(cells))
    print(f"  max par case: {max(counts.values())}")


def run(nb_matches: int) -> None:
    print(f"Zones collectees sur {nb_matches} matchs (effectifs synthetiques, sans data/joueurs.xlsx)")
    for title, zone_list in _collect(nb_matches).items():
        _print_heatmap(title, zone_list)


if __name__ == "__main__":
    run(int(sys.argv[1]) if len(sys.argv) > 1 else 200)

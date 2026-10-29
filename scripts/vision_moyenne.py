"""Vision moyenne des titulaires de Ligue 1 (ticket v2-collectif/23, deuxième passe, 28/10/2026).

C'est l'ancrage du seuil du passeur (`v2engine.offside.PASS_MARGIN_REFERENCE_VISION`) : un passeur de Vision
moyenne doit retrouver le seuil validé de 0,5 m. 55 est le milieu de l'échelle 11-99, pas la moyenne des
joueurs -- d'où l'écart mesuré le 28/10/2026 (4,45 hors-jeu par match au lieu de 3,65).

Usage : uv run python -m scripts.vision_moyenne

Lecture seule : ne modifie pas le jeu.
"""

from __future__ import annotations

from ligue1sim.clubs import load_clubs
from ligue1sim.lineup import pick_best_formation
from ligue1sim.season import CLUBS_PATH

from v2engine.attributes import player_attribute
from v2engine.offside import PASS_MARGIN_REFERENCE_VISION, pass_margin_m


def vision_moyenne_des_titulaires(competition: str = "Ligue 1") -> tuple[float, int]:
    """(Vision moyenne, nombre de titulaires) sur les onze de départ de toutes les équipes de la compétition."""
    values: list[int] = []
    for club in load_clubs(CLUBS_PATH, competition):
        values.extend(player_attribute(p, "Vision") for p in pick_best_formation(club).players)
    return sum(values) / len(values), len(values)


def main() -> None:
    mean, count = vision_moyenne_des_titulaires()
    print(f"titulaires : {count}")
    print(f"Vision moyenne : {mean:.2f}")
    print(f"reference codee (PASS_MARGIN_REFERENCE_VISION) : {PASS_MARGIN_REFERENCE_VISION}")
    print(f"seuil d'un passeur moyen : {pass_margin_m(mean):.3f} m (cible : 0,5 m)")


if __name__ == "__main__":
    main()

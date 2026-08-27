"""Entraîneurs et dispositifs tactiques imposés par club, sourcés depuis les
fiches Transfermarkt (voir data/entraineurs.xlsx : une ligne par club avec
son entraîneur actuel et sa "Formation préférentielle" telle qu'affichée sur
sa fiche profil).

Un club renseigné dans ce fichier, avec une formation préférentielle non
vide, DOIT jouer dans ce dispositif (voir `lineup.pick_best_formation`) --
quitte à devoir dépanner certains postes (voir `lineup.select_best_xi`). Un
club absent (championnat pas encore recherché, ou entraîneur/formation non
trouvés) retombe sur le choix adaptatif habituel (meilleur des 3 dispositifs
standards, voir `lineup.FORMATIONS`). Le nom de l'entraîneur, lui, est
purement informatif (affiché sur la feuille de match) : un club peut avoir un
entraîneur connu sans formation préférentielle renseignée, ou l'inverse.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import pandas as pd

CLUB_COLUMN = "Club"
COACH_COLUMN = "Entraîneur"
FORMATION_COLUMN = "Formation préférentielle"

# Un ou plusieurs fichiers, au fur et à mesure des championnats recherchés.
# Les fichiers absents sont ignorés silencieusement (voir `_load`).
COACHES_PATHS: tuple[str, ...] = ("data/entraineurs.xlsx",)


@dataclass(frozen=True)
class Coach:
    name: str
    preferred_formation: str | None


@lru_cache(maxsize=None)
def _load(paths: tuple[str, ...]) -> dict[str, Coach]:
    """{nom du club: Coach} pour tous les clubs ayant au moins un entraîneur
    renseigné dans les fichiers donnés. Résultat mis en cache (interrogé à
    chaque simulation de match) -- utiliser `clear_cache()` pour forcer un
    rechargement (tests, ou fichier modifié en cours de session)."""
    coaches: dict[str, Coach] = {}
    for path in paths:
        if not Path(path).exists():
            continue
        df = pd.read_excel(path)
        for _, row in df.iterrows():
            club = row.get(CLUB_COLUMN)
            name = row.get(COACH_COLUMN)
            if not (pd.notna(club) and pd.notna(name) and str(name).strip()):
                continue
            formation = row.get(FORMATION_COLUMN)
            preferred_formation = str(formation).strip() if pd.notna(formation) and str(formation).strip() else None
            coaches[str(club)] = Coach(name=str(name).strip(), preferred_formation=preferred_formation)
    return coaches


def coaches(paths: tuple[str, ...] = COACHES_PATHS) -> dict[str, Coach]:
    """{nom du club: Coach} -- voir `_load`."""
    return _load(paths)


def preferred_formations(paths: tuple[str, ...] = COACHES_PATHS) -> dict[str, str]:
    """{nom du club: formation préférentielle}, pour les clubs où elle est
    renseignée (sous-ensemble de `coaches`)."""
    return {club: coach.preferred_formation for club, coach in _load(paths).items() if coach.preferred_formation}


def coach_name(club_name: str, paths: tuple[str, ...] = COACHES_PATHS) -> str | None:
    """Nom de l'entraîneur du club, si connu."""
    coach = _load(paths).get(club_name)
    return coach.name if coach else None


def clear_cache() -> None:
    _load.cache_clear()

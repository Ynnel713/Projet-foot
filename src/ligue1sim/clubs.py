"""Chargement et validation des clubs depuis le fichier multi-championnats."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

CHAMPIONNAT_COLUMN = "Championnat"
CLUB_COLUMN = "Club"
RATING_COLUMN = "Note_globale"
REQUIRED_COLUMNS = [CHAMPIONNAT_COLUMN, CLUB_COLUMN, RATING_COLUMN]

# "Autres" regroupe des clubs hors des 5 grands championnats : on les ignore
# pour l'instant (pas de calendrier dédié).
EXCLUDED_CHAMPIONNATS = {"AUTRES"}


class ClubDataError(ValueError):
    """Levée quand le fichier de clubs est invalide ou incomplet."""


@dataclass(frozen=True)
class Club:
    name: str
    rating: float


@dataclass(frozen=True)
class ClubOption:
    """Un club du vivier complet (toutes compétitions), pour la Compétition Perso."""

    name: str
    rating: float
    championnat: str

    def as_club(self) -> Club:
        return Club(name=self.name, rating=self.rating)


def load_all_clubs(path: str | Path) -> list[ClubOption]:
    """Charge tous les clubs du fichier, tous championnats confondus (y
    compris "Autres"), pour un sélecteur libre de type Compétition Perso.
    """
    df = _read(path)
    _validate_columns(df)

    if df[REQUIRED_COLUMNS].isnull().any().any():
        raise ClubDataError("Valeurs manquantes dans le fichier de clubs.")

    out_of_range = df[(df[RATING_COLUMN] < 0) | (df[RATING_COLUMN] > 100)]
    if not out_of_range.empty:
        raise ClubDataError(
            f"Notes hors de la plage 0-100 pour : {out_of_range[CLUB_COLUMN].tolist()}"
        )

    options = [
        ClubOption(
            name=row[CLUB_COLUMN],
            rating=float(row[RATING_COLUMN]),
            championnat=row[CHAMPIONNAT_COLUMN],
        )
        for _, row in df.iterrows()
    ]
    return sorted(options, key=lambda o: (o.championnat, -o.rating))


def list_championnats(path: str | Path) -> list[str]:
    """Liste triée des championnats disponibles dans le fichier (hors "Autres")."""
    df = _read(path)
    _validate_columns(df)
    championnats = set(df[CHAMPIONNAT_COLUMN]) - EXCLUDED_CHAMPIONNATS
    return sorted(championnats)


def load_clubs(path: str | Path, championnat: str) -> list[Club]:
    """Charge et valide les clubs d'un championnat donné.

    Valide : colonnes présentes, aucune valeur manquante, ratings dans
    0-100, pas de club en double, et un nombre pair de clubs (nécessaire
    pour générer un calendrier aller-retour).
    """
    df = _read(path)
    _validate_columns(df)

    subset = df[df[CHAMPIONNAT_COLUMN] == championnat]
    _validate_subset(subset, championnat)

    return [
        Club(name=row[CLUB_COLUMN], rating=float(row[RATING_COLUMN]))
        for _, row in subset.iterrows()
    ]


def _read(path: str | Path) -> pd.DataFrame:
    return pd.read_excel(path)


def _validate_columns(df: pd.DataFrame) -> None:
    missing_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_columns:
        raise ClubDataError(f"Colonnes manquantes dans le fichier : {missing_columns}")


def _validate_subset(subset: pd.DataFrame, championnat: str) -> None:
    if subset.empty:
        raise ClubDataError(f"Aucun club trouvé pour le championnat '{championnat}'.")

    if subset[REQUIRED_COLUMNS].isnull().any().any():
        raise ClubDataError(f"Valeurs manquantes pour le championnat '{championnat}'.")

    duplicates = subset[CLUB_COLUMN][subset[CLUB_COLUMN].duplicated()].tolist()
    if duplicates:
        raise ClubDataError(f"Clubs en double pour '{championnat}' : {duplicates}")

    out_of_range = subset[(subset[RATING_COLUMN] < 0) | (subset[RATING_COLUMN] > 100)]
    if not out_of_range.empty:
        raise ClubDataError(
            f"Notes hors de la plage 0-100 pour '{championnat}' : "
            f"{out_of_range[CLUB_COLUMN].tolist()}"
        )

    if len(subset) < 2 or len(subset) % 2 != 0:
        raise ClubDataError(
            f"Le championnat '{championnat}' a {len(subset)} clubs : il en "
            "faut un nombre pair (au moins 2) pour générer un calendrier "
            "aller-retour."
        )

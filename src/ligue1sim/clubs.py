"""Chargement et validation des clubs depuis le fichier joueurs multi-championnats.

Le fichier source (data/joueurs.xlsx) a une ligne par joueur, pas par club :
`load_clubs`/`load_all_clubs` regroupent les joueurs par club. Il n'y a plus
de note de club stockée -- seuls les joueurs ont une note (voir players.py) ;
la force d'un club se calcule à la volée à partir de son effectif (voir
lineup.club_strength), jamais stockée ici.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

from ligue1sim.players import Player

CHAMPIONNAT_COLUMN = "Championnat"
CLUB_COLUMN = "Club"
PRENOM_COLUMN = "Prénom"
NOM_COLUMN = "Nom"
NATIONALITE_COLUMN = "Nationalité"
AGE_COLUMN = "Âge"
POSTE_COLUMN = "Poste"
NOTE_COLUMN = "Note /100"

REQUIRED_COLUMNS = [
    CHAMPIONNAT_COLUMN,
    CLUB_COLUMN,
    PRENOM_COLUMN,
    NATIONALITE_COLUMN,
    AGE_COLUMN,
    POSTE_COLUMN,
    NOTE_COLUMN,
]

# "Autres clubs" regroupe des clubs hors des 8 championnats simulables : pas
# de calendrier officiel dédié, mais toujours disponibles pour la Compétition
# Perso (voir load_all_clubs).
EXCLUDED_CHAMPIONNATS = {"Autres clubs"}

# Effectif minimum pour pouvoir aligner une équipe complète (11 titulaires).
MIN_SQUAD_SIZE = 11


class ClubDataError(ValueError):
    """Levée quand le fichier de joueurs est invalide ou incomplet."""


@dataclass(frozen=True)
class Club:
    name: str
    players: list[Player] = field(default_factory=list)


@dataclass(frozen=True)
class ClubOption:
    """Un club du vivier complet (toutes compétitions), pour la Compétition Perso."""

    name: str
    players: list[Player]
    championnat: str

    def as_club(self) -> Club:
        return Club(name=self.name, players=self.players)


def load_all_clubs(path: str | Path) -> list[ClubOption]:
    """Charge tous les clubs du fichier, tous championnats confondus (y
    compris "Autres clubs"), pour un sélecteur libre de type Compétition Perso.
    """
    df = _read(path)
    _validate_columns(df)
    _validate_no_missing_values(df, scope="le fichier de joueurs")

    options = []
    for (championnat, club_name), group in df.groupby([CHAMPIONNAT_COLUMN, CLUB_COLUMN], sort=False):
        options.append(
            ClubOption(name=club_name, players=_build_players(group), championnat=championnat)
        )
    return sorted(options, key=lambda o: (o.championnat, o.name))


def list_championnats(path: str | Path) -> list[str]:
    """Liste triée des championnats simulables (hors "Autres clubs")."""
    df = _read(path)
    _validate_columns(df)
    championnats = set(df[CHAMPIONNAT_COLUMN]) - EXCLUDED_CHAMPIONNATS
    return sorted(championnats)


def load_clubs(path: str | Path, championnat: str) -> list[Club]:
    """Charge et valide les clubs d'un championnat donné.

    Valide : colonnes présentes, aucune valeur manquante, notes dans 0-100,
    chaque club a au moins MIN_SQUAD_SIZE joueurs, et un nombre pair de clubs
    (nécessaire pour générer un calendrier aller-retour).
    """
    df = _read(path)
    _validate_columns(df)

    subset = df[df[CHAMPIONNAT_COLUMN] == championnat]
    _validate_subset(subset, championnat)

    clubs = [
        Club(name=club_name, players=_build_players(group))
        for club_name, group in subset.groupby(CLUB_COLUMN, sort=False)
    ]
    return sorted(clubs, key=lambda c: c.name)


def _build_players(group: pd.DataFrame) -> list[Player]:
    players = []
    for _, row in group.iterrows():
        nom = row[NOM_COLUMN] if pd.notna(row.get(NOM_COLUMN)) else ""
        players.append(
            Player(
                prenom=row[PRENOM_COLUMN],
                nom=nom,
                nationalite=row[NATIONALITE_COLUMN],
                age=int(row[AGE_COLUMN]),
                poste=row[POSTE_COLUMN],
                note=float(row[NOTE_COLUMN]),
                club=row[CLUB_COLUMN],
                championnat=row[CHAMPIONNAT_COLUMN],
            )
        )
    return players


def _read(path: str | Path) -> pd.DataFrame:
    return pd.read_excel(path)


def _validate_columns(df: pd.DataFrame) -> None:
    missing_columns = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_columns:
        raise ClubDataError(f"Colonnes manquantes dans le fichier : {missing_columns}")


def _validate_no_missing_values(df: pd.DataFrame, *, scope: str) -> None:
    # "Nom" peut être vide (joueurs à mononyme, ex. Vitinha) : exclu de la vérification.
    columns_to_check = [c for c in REQUIRED_COLUMNS if c != NOM_COLUMN]
    if df[columns_to_check].isnull().any().any():
        raise ClubDataError(f"Valeurs manquantes dans {scope}.")

    out_of_range = df[(df[NOTE_COLUMN] < 0) | (df[NOTE_COLUMN] > 100)]
    if not out_of_range.empty:
        raise ClubDataError(
            f"Notes hors de la plage 0-100 pour : {out_of_range[CLUB_COLUMN].unique().tolist()}"
        )


def _validate_subset(subset: pd.DataFrame, championnat: str) -> None:
    if subset.empty:
        raise ClubDataError(f"Aucun club trouvé pour le championnat '{championnat}'.")

    _validate_no_missing_values(subset, scope=f"le championnat '{championnat}'")

    club_counts = subset[CLUB_COLUMN].value_counts()
    understaffed = club_counts[club_counts < MIN_SQUAD_SIZE]
    if not understaffed.empty:
        raise ClubDataError(
            f"Effectif insuffisant (< {MIN_SQUAD_SIZE} joueurs) pour '{championnat}' : "
            f"{understaffed.index.tolist()}"
        )

    nb_clubs = subset[CLUB_COLUMN].nunique()
    if nb_clubs < 2 or nb_clubs % 2 != 0:
        raise ClubDataError(
            f"Le championnat '{championnat}' a {nb_clubs} clubs : il en faut "
            "un nombre pair (au moins 2) pour générer un calendrier aller-retour."
        )

"""Entraîneurs et sélectionneurs, sourcés depuis data/Coachs-Simulafoot.xlsx
(une ligne par club/sélection : nom, dispositif préférentiel, note sur 100,
et jusqu'à 5 styles de jeu marqués d'un "X" -- voir STYLE_COLUMNS).

Un club/sélection renseigné avec un dispositif préférentiel non vide DOIT
jouer dans ce dispositif (voir `lineup.pick_best_formation`) -- quitte à
devoir dépanner certains postes (voir `lineup.select_best_xi`). Un club
absent retombe sur le choix adaptatif habituel (meilleur des dispositifs
standards, voir `lineup.FORMATIONS`). Le nom de l'entraîneur est purement
informatif (affiché sur la feuille de match). Depuis 3c (décision D5,
07/10/2026), la note applique un modulateur d'influence coach (±3 %) sur les
lambdas de Poisson, et les styles un modulateur de ±15 % cumulés -- voir
COACH_INFLUENCE/STYLE_* dans simulation.py. Les styles alimentent aussi les
statistiques de match (voir `match_stats`).

Résolution des noms
--------------------
Le fichier écrit à la main mélange noms exacts ("LOSC Lille"), abréviations
courantes ("Paris SG", "Tottenham", "Nott Forest") et sélections préfixées
d'un code pays ("FR France", "BR Brésil"). `_resolve_name` relie chaque
ligne au nom canonique exact utilisé ailleurs dans le moteur (`Club.name` /
`ClubOption.name`), dans cet ordre : alias manuel -> nom de sélection (avec
ou sans préfixe code pays) -> nom de club exact -> nom de club abrégé
(correspondance normalisée non ambiguë dans le vivier complet, équipes
réserve/jeunes exclues) -> repli sur le nom brut tel quel (comportement
historique, notamment pour les clubs synthétiques des tests)."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import pandas as pd

from ligue1sim.clubs import load_all_clubs
from ligue1sim.nations import load_national_teams

CLUB_COLUMN = "Club"
COACH_COLUMN = "Entraineur"
FORMATION_COLUMN = "Formation"
NOTE_COLUMN = "Note /100"
STYLE_COLUMNS: tuple[str, ...] = ("Contre attaque", "Pressing", "Défensif", "Offensif", "Possession")

# Un ou plusieurs fichiers. Les fichiers absents sont ignorés silencieusement (voir `_load`).
COACHES_PATHS: tuple[str, ...] = ("data/Coachs-Simulafoot.xlsx",)
# Vivier utilisé pour résoudre les noms de club/sélection abrégés -- voir `_resolve_name`.
PLAYERS_PATH = "data/joueurs.xlsx"

# Nom EXACT tel qu'écrit dans data/Coachs-Simulafoot.xlsx -> nom canonique
# (`Club.name`/`ClubOption.name`), pour les abréviations qu'aucune
# correspondance automatique ne peut relier sans ambiguïté.
MANUAL_CLUB_ALIASES: dict[str, str] = {
    "Paris SG": "Paris Saint-Germain",
    "Nott Forest": "Nottingham Forest",
    "Atlético Madrid": "Atlético de Madrid",
    "Borussia M'gladbach": "Borussia Mönchengladbach",
}
# Idem, pour les sélections dont l'abréviation du nom de pays ne matche pas
# le nom FR complet utilisé par `nations.load_national_teams`.
MANUAL_NATION_ALIASES: dict[str, str] = {
    "CZ Rép. tchèque": "République tchèque",
}

_RESERVE_MARKERS = (" u21", " u19", " u23", " u20", " ii", " b", "primavera", "réserve")
_NATION_PREFIX = re.compile(r"^[A-Z]{2,3} (.+)$")


@dataclass(frozen=True)
class Coach:
    name: str
    preferred_formation: str | None
    note: float | None = None
    styles: frozenset[str] = field(default_factory=frozenset)


def _normalize(name: str) -> str:
    n = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", n.lower())


@lru_cache(maxsize=None)
def _club_universe(players_path: str) -> dict[str, str]:
    """{nom normalisé: nom canonique} pour tous les clubs du vivier complet
    (toutes compétitions confondues), équipes réserve/jeunes exclues."""
    out: dict[str, str] = {}
    for option in load_all_clubs(players_path):
        lname = option.name.lower()
        if any(marker in lname for marker in _RESERVE_MARKERS):
            continue
        out[_normalize(option.name)] = option.name
    return out


@lru_cache(maxsize=None)
def _nation_universe(players_path: str) -> dict[str, str]:
    """{nom FR sans drapeau: nom Club.name AVEC drapeau} pour les sélections
    complètes (23/23) -- voir nations.load_national_teams."""
    teams = load_national_teams(players_path, complete_only=True)
    return {(t.name.split(" ", 1)[1] if " " in t.name else t.name): t.name for t in teams}


def _resolve_name(raw: str, players_path: str) -> str:
    raw = raw.strip()

    if raw in MANUAL_CLUB_ALIASES:
        return MANUAL_CLUB_ALIASES[raw]

    nations = _nation_universe(players_path)
    if raw in MANUAL_NATION_ALIASES:
        return nations.get(MANUAL_NATION_ALIASES[raw], raw)
    if raw in nations:
        return nations[raw]
    m = _NATION_PREFIX.match(raw)
    if m and m.group(1) in nations:
        return nations[m.group(1)]

    clubs = _club_universe(players_path)
    if raw in clubs.values():
        return raw
    target = _normalize(raw)
    candidates = {canon for norm, canon in clubs.items() if target and (target in norm or norm in target)}
    if len(candidates) == 1:
        return next(iter(candidates))

    return raw  # repli : comportement historique (notamment clubs synthétiques des tests)


def _parse_styles(row: pd.Series) -> frozenset[str]:
    return frozenset(col for col in STYLE_COLUMNS if pd.notna(row.get(col)) and str(row.get(col)).strip())


@lru_cache(maxsize=None)
def _load(paths: tuple[str, ...], players_path: str = PLAYERS_PATH) -> dict[str, Coach]:
    """{nom canonique du club/sélection: Coach} pour toutes les lignes des
    fichiers donnés ayant au moins un entraîneur renseigné. Résultat mis en
    cache (interrogé à chaque simulation de match) -- utiliser
    `clear_cache()` pour forcer un rechargement (tests, ou fichier modifié
    en cours de session)."""
    coaches: dict[str, Coach] = {}
    for path in paths:
        if not Path(path).exists():
            continue
        df = pd.read_excel(path)
        for _, row in df.iterrows():
            raw_club = row.get(CLUB_COLUMN)
            name = row.get(COACH_COLUMN)
            if not (pd.notna(raw_club) and pd.notna(name) and str(name).strip()):
                continue
            canonical = _resolve_name(str(raw_club), players_path)
            formation = row.get(FORMATION_COLUMN)
            preferred_formation = str(formation).strip() if pd.notna(formation) and str(formation).strip() else None
            note_raw = row.get(NOTE_COLUMN)
            note = float(note_raw) if pd.notna(note_raw) else None
            coaches[canonical] = Coach(
                name=str(name).strip(),
                preferred_formation=preferred_formation,
                note=note,
                styles=_parse_styles(row),
            )
    return coaches


def coaches(paths: tuple[str, ...] = COACHES_PATHS) -> dict[str, Coach]:
    """{nom du club/sélection: Coach} -- voir `_load`."""
    return _load(paths)


def preferred_formations(paths: tuple[str, ...] = COACHES_PATHS) -> dict[str, str]:
    """{nom du club/sélection: formation préférentielle}, pour ceux où elle
    est renseignée (sous-ensemble de `coaches`)."""
    return {club: coach.preferred_formation for club, coach in _load(paths).items() if coach.preferred_formation}


def coach_name(club_name: str, paths: tuple[str, ...] = COACHES_PATHS) -> str | None:
    """Nom de l'entraîneur du club/sélection, si connu."""
    coach = _load(paths).get(club_name)
    return coach.name if coach else None


def coach_note(club_name: str, paths: tuple[str, ...] = COACHES_PATHS) -> float | None:
    """Note /100 de l'entraîneur du club/sélection, si connue (voir
    `simulation.COACH_INFLUENCE` pour son usage dans le moteur)."""
    coach = _load(paths).get(club_name)
    return coach.note if coach else None


def coach_styles(club_name: str, paths: tuple[str, ...] = COACHES_PATHS) -> frozenset[str]:
    """Styles de jeu marqués pour l'entraîneur du club/sélection (sous-
    ensemble de STYLE_COLUMNS), ensemble vide si inconnu."""
    coach = _load(paths).get(club_name)
    return coach.styles if coach else frozenset()


@lru_cache(maxsize=None)
def average_note(paths: tuple[str, ...] = COACHES_PATHS) -> float | None:
    """Moyenne des notes /100 connues, tous clubs/sélections confondus --
    référence utilisée par `simulation.COACH_INFLUENCE` pour juger un coach
    au-dessus ou en-dessous du lot plutôt que contre un seuil arbitraire
    fixe. None si aucune note n'est renseignée."""
    notes = [c.note for c in _load(paths).values() if c.note is not None]
    return sum(notes) / len(notes) if notes else None


def clear_cache() -> None:
    _load.cache_clear()
    _club_universe.cache_clear()
    _nation_universe.cache_clear()
    average_note.cache_clear()

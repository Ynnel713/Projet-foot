"""ETL joueurs : data/joueurs.xlsx (feuille "Infos principales") -> DuckDB
(analytics.duckdb, zone de staging/analytics) -> SQLite (simulafoot.db,
tables players + player_attributes).

Algorithme :
    1. Lire la feuille via pandas/openpyxl.
    2. Nettoyer chaque ligne en Python (jamais en SQL -- plus facile a
       tester unitairement sur des cas limites precis, voir _clean_str /
       _parse_market_value / _split_positions / _split_preferred_moves
       ci-dessous).
    3. Charger le resultat nettoye dans DuckDB (staging + requetable pour
       l'analytics -- voir scripts/export_analytics.py) puis dans SQLite
       (source de verite runtime) via un UPSERT sur `players.id` (l'ID
       Excel est stable : deux imports successifs mettent a jour les memes
       lignes plutot que d'en creer de nouvelles).
    4. Logger un compte de joueurs importes, d'attributs mappes, et la liste
       des colonnes Excel ignorees (ni identite, ni attribut FM26).

Aucune valeur n'est inventee : un champ absent/illisible devient None (ou
est omis de player_attributes), jamais une valeur de repli arbitraire.
"""

from __future__ import annotations

import logging
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd

from engine.db import get_duckdb, get_sqlite

logger = logging.getLogger(__name__)

SHEET_NAME = "Infos principales"

# Colonnes "identite" (1 valeur par joueur) -- cle = nom exact de colonne
# Excel, valeur = colonne SQLite cible. Verifie contre data/joueurs.xlsx le
# 28/09/2026 (68 colonnes au total sur cette feuille).
IDENTITY_COLUMNS: dict[str, str] = {
    "Prénom": "first_name",
    "Nom": "last_name",
    "Nationalité": "nationality",
    "Âge": "age",
    "Club": "club",
    "Championnat": "league",
    "Valeur marchande": "market_value",
    "Note transfermrkt": "average_rating",
    "Taille (cm)": "height_cm",
    "Statut": "status",
    "Catégorie": "role_category",
    "Pieds": "foot",
    "Moyenne joueur": "fm_rating",
    "Weak foot (/5)": "weak_foot",
    "Preferred moves": "preferred_moves",
}
# "Poste" et "Postes FM naturels" alimentent tous deux position/
# secondary_positions via _split_positions (voir plus bas) -- traites a
# part, pas dans IDENTITY_COLUMNS (mapping 2 colonnes -> 2 champs, pas 1:1).
POSITION_COLUMNS = ("Poste", "Postes FM naturels")
ID_COLUMN = "ID"

# Les 47 attributs FM26, groupes par categorie -- noms de colonnes exacts
# (voir scripts/scrape_fminside_attributes.py, meme liste, source de verite
# partagee : ne pas laisser diverger). Confirme colonne par colonne dans
# data/joueurs.xlsx le 28/09/2026 (colonnes 17 a 63).
FM26_ATTRIBUTES: dict[str, tuple[str, ...]] = {
    "technique": (
        "Crossing", "Dribbling", "Finishing", "First Touch", "Heading",
        "Long Shots", "Marking", "Passing", "Tackling", "Technique",
    ),
    "gardien": (
        "Aerial Reach", "Command of Area", "Communication", "Eccentricity",
        "Handling", "Kicking", "One on Ones", "Punching (Tendency)",
        "Reflexes", "Rushing Out (Tendency)", "Throwing",
    ),
    "mental": (
        "Aggression", "Anticipation", "Bravery", "Composure", "Concentration",
        "Decisions", "Determination", "Flair", "Leadership", "Off the Ball",
        "Positioning", "Teamwork", "Vision", "Work Rate",
    ),
    "physique": (
        "Acceleration", "Agility", "Balance", "Jumping Reach",
        "Natural Fitness", "Pace", "Stamina", "Strength",
    ),
    "coups_de_pied_arretes": (
        "Corners", "Free Kick Taking", "Long Throws", "Penalty Taking",
    ),
}
ATTRIBUTE_TO_CATEGORY: dict[str, str] = {
    name: category for category, names in FM26_ATTRIBUTES.items() for name in names
}

# Marqueurs de valeur absente rencontres dans le classeur (cellule vide,
# tiret simple, tiret cadratin) -- distincts d'un NaN pandas, traites de la
# meme facon : valeur absente, jamais convertie en 0 ou chaine vide.
_EMPTY_MARKERS = {"-", "—", "(aucun)"}
_MARKET_VALUE_RE = re.compile(r"€\s*([\d.,]+)\s*([km]?)", re.IGNORECASE)


@dataclass(frozen=True)
class ImportStats:
    """Resultat d'un import, pour le log CLI et les tests."""

    players_imported: int
    attributes_mapped: int
    columns_ignored: tuple[str, ...]


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and pd.isna(value):
        return True
    return isinstance(value, str) and value.strip() in _EMPTY_MARKERS


def _clean_str(value: Any) -> str | None:
    """Chaine nettoyee (espaces multiples ecrases, bords rognes), ou None si
    absente. Les accents/apostrophes/caracteres composes (O'Reilly, van der
    Berg) sont laisses tels quels -- aucune translitteration, la base est en
    UTF-8 de bout en bout (SQLite/DuckDB gerent nativement)."""
    if _is_missing(value):
        return None
    text = re.sub(r"\s+", " ", str(value)).strip()
    return text or None


def _parse_int(value: Any) -> int | None:
    if _is_missing(value):
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _parse_float(value: Any) -> float | None:
    if _is_missing(value):
        return None
    try:
        return float(str(value).replace(",", "."))
    except (TypeError, ValueError):
        return None


def _parse_market_value(value: Any) -> float | None:
    """"€30.00m" -> 30.0 (millions d'euros) ; "€500k" -> 0.5 ; "-"/"—"/vide
    -> None. Meme convention que src/ligue1sim/clubs.py::_parse_valeur_marchande
    (moteur principal) -- millions d'euros comme unite commune."""
    if _is_missing(value):
        return None
    match = _MARKET_VALUE_RE.search(str(value))
    if not match:
        return None
    amount = float(match.group(1).replace(",", "."))
    if match.group(2).lower() == "k":
        amount /= 1000
    return amount


def _split_positions(poste_raw: Any, postes_fm_raw: Any) -> tuple[str | None, tuple[str, ...]]:
    """(poste principal, postes secondaires) a partir de deux colonnes :
    - "Poste" (ex. "RB / DC", "RB") : le 1er token separe par "/" est le
      poste principal, les suivants s'ajoutent aux postes secondaires.
    - "Postes FM naturels" (ex. "DR, WBR", "DL, DC") : tokens separes par
      ",", tous ajoutes aux postes secondaires.
    Deduplique en preservant l'ordre, exclut le poste principal de la liste
    des secondaires (un poste n'est pas son propre "secours")."""
    poste_text = _clean_str(poste_raw)
    tokens = [t.strip() for t in (poste_text or "").split("/") if t.strip()]
    main = tokens[0] if tokens else None
    secondary: list[str] = list(tokens[1:])

    fm_text = _clean_str(postes_fm_raw)
    if fm_text:
        secondary.extend(t.strip() for t in fm_text.split(",") if t.strip())

    seen: set[str] = set()
    deduped: list[str] = []
    for poste in secondary:
        if poste != main and poste not in seen:
            seen.add(poste)
            deduped.append(poste)
    return main, tuple(deduped)


def _split_preferred_moves(value: Any) -> tuple[str, ...]:
    """"Move A ; Move B" -> ("Move A", "Move B"). "(aucun)"/vide -> ()."""
    text = _clean_str(value)
    if not text or text in _EMPTY_MARKERS:
        return ()
    return tuple(m.strip() for m in text.split(";") if m.strip())


def _row_to_player(row: pd.Series) -> dict[str, Any] | None:
    """Une ligne pandas -> dict pret pour `players` (colonnes SQLite), ou
    None si la ligne n'a pas d'ID exploitable (ligne vide en fin de feuille,
    par ex.)."""
    player_id = _parse_int(row.get(ID_COLUMN))
    if player_id is None:
        return None

    main_poste, secondary = _split_positions(row.get("Poste"), row.get("Postes FM naturels"))
    record: dict[str, Any] = {
        "id": player_id,
        "first_name": _clean_str(row.get("Prénom")) or "",
        "last_name": _clean_str(row.get("Nom")) or "",
        "nationality": _clean_str(row.get("Nationalité")),
        "age": _parse_int(row.get("Âge")),
        "position": main_poste,
        "secondary_positions": " / ".join(secondary) if secondary else None,
        "club": _clean_str(row.get("Club")),
        "league": _clean_str(row.get("Championnat")),
        "market_value": _parse_market_value(row.get("Valeur marchande")),
        "average_rating": _parse_float(row.get("Note transfermrkt")),
        "height_cm": _parse_int(row.get("Taille (cm)")),
        "status": _clean_str(row.get("Statut")),
        "role_category": _clean_str(row.get("Catégorie")),
        "foot": _clean_str(row.get("Pieds")),
        "fm_rating": _parse_float(row.get("Moyenne joueur")),
        "weak_foot": _parse_float(row.get("Weak foot (/5)")),
        "preferred_moves": " ; ".join(_split_preferred_moves(row.get("Preferred moves"))) or None,
    }
    return record


def _row_to_attributes(row: pd.Series, player_id: int) -> list[tuple[int, str, str, int]]:
    """Une ligne pandas -> liste de (player_id, attribute, category, value)
    pour `player_attributes` -- un attribut absent/illisible est OMIS (pas
    de ligne a value=0 : 0 est une vraie note possible, distincte d'une
    absence de donnee)."""
    rows: list[tuple[int, str, str, int]] = []
    for category, names in FM26_ATTRIBUTES.items():
        for name in names:
            value = _parse_int(row.get(name))
            if value is not None:
                rows.append((player_id, name, category, value))
    return rows


def _ignored_columns(columns: list[str]) -> tuple[str, ...]:
    known = {ID_COLUMN, *IDENTITY_COLUMNS, *POSITION_COLUMNS, *ATTRIBUTE_TO_CATEGORY}
    return tuple(c for c in columns if c not in known)


def _read_sheet(xlsx_path: Path) -> pd.DataFrame:
    if not xlsx_path.exists():
        raise FileNotFoundError(f"Fichier Excel introuvable : {xlsx_path}")
    try:
        return pd.read_excel(xlsx_path, sheet_name=SHEET_NAME, engine="openpyxl")
    except ValueError as exc:
        # pandas leve ValueError (pas KeyError) quand la feuille n'existe pas.
        raise ValueError(f'Feuille "{SHEET_NAME}" introuvable dans {xlsx_path}') from exc


def _stage_in_duckdb(
    duck: duckdb.DuckDBPyConnection, players: pd.DataFrame, attributes: pd.DataFrame
) -> None:
    """Charge les DataFrames nettoyes dans DuckDB (staging + analytics) --
    remplace la table a chaque import (source de verite = le classeur, pas
    un historique cumulatif cote DuckDB)."""
    duck.register("stg_players", players)
    duck.execute("CREATE OR REPLACE TABLE players AS SELECT * FROM stg_players")
    duck.unregister("stg_players")

    duck.register("stg_player_attributes", attributes)
    duck.execute("CREATE OR REPLACE TABLE player_attributes AS SELECT * FROM stg_player_attributes")
    duck.unregister("stg_player_attributes")


def _upsert_sqlite(
    conn: sqlite3.Connection, players: pd.DataFrame, attributes: pd.DataFrame
) -> None:
    """UPSERT dans SQLite -- `players.id` est stable (ID Excel), donc un
    re-import met a jour les lignes existantes au lieu d'en creer des
    doublons. `player_attributes` est entierement recree PAR JOUEUR touche
    (DELETE puis INSERT) : plus simple et plus sur qu'un upsert par attribut
    quand un attribut disparait d'un import a l'autre (ex. re-scraping)."""
    player_cols = list(players.columns)
    placeholders = ", ".join(f":{c}" for c in player_cols)
    updates = ", ".join(f"{c} = excluded.{c}" for c in player_cols if c != "id")
    conn.executemany(
        f"""
        INSERT INTO players ({", ".join(player_cols)})
        VALUES ({placeholders})
        ON CONFLICT(id) DO UPDATE SET {updates}
        """,
        players.to_dict(orient="records"),
    )

    touched_ids = players["id"].tolist()
    conn.executemany("DELETE FROM player_attributes WHERE player_id = ?", [(i,) for i in touched_ids])
    conn.executemany(
        "INSERT INTO player_attributes (player_id, attribute, category, value) VALUES (?, ?, ?, ?)",
        attributes.itertuples(index=False, name=None),
    )


def import_players(
    xlsx_path: str | Path,
    duckdb_path: str | Path,
    sqlite_path: str | Path,
) -> ImportStats:
    """Point d'entree de l'ETL -- voir docstring du module pour l'algorithme.
    Leve FileNotFoundError/ValueError avec un message explicite si le
    classeur ou la feuille sont introuvables (pas de fallback silencieux)."""
    xlsx_path = Path(xlsx_path)
    df = _read_sheet(xlsx_path)

    player_records: list[dict[str, Any]] = []
    attribute_rows: list[tuple[int, str, str, int]] = []
    for _, row in df.iterrows():
        record = _row_to_player(row)
        if record is None:
            continue
        player_records.append(record)
        attribute_rows.extend(_row_to_attributes(row, record["id"]))

    players_df = pd.DataFrame(player_records)
    attributes_df = pd.DataFrame(
        attribute_rows, columns=["player_id", "attribute", "category", "value"]
    )

    duck = get_duckdb(duckdb_path)
    try:
        _stage_in_duckdb(duck, players_df, attributes_df)
    finally:
        duck.close()

    conn = get_sqlite(sqlite_path)
    try:
        _upsert_sqlite(conn, players_df, attributes_df)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    ignored = _ignored_columns(list(df.columns))
    stats = ImportStats(
        players_imported=len(players_df),
        attributes_mapped=len(attributes_df),
        columns_ignored=ignored,
    )
    logger.info(
        "%d joueurs importés, %d attributs mappés, %d colonnes ignorées : %s",
        stats.players_imported,
        stats.attributes_mapped,
        len(stats.columns_ignored),
        ", ".join(stats.columns_ignored) or "(aucune)",
    )
    return stats

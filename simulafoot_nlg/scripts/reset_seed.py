"""Vide la banque de phrases et l'historique d'usage de data/simulafoot.db, en
GARDANT les joueurs (decisions D7 et D7bis du plan V2.1) : permet de reimporter
une banque modifiee (import_seed refuse un code de scenario deja present) sans
reimporter les 7563 joueurs ni leurs attributs.

DESTRUCTIF et irreversible : phrase_history et similarity_signatures sont
videes (D8rev : l'historique d'usage se conserve en l'exportant AVANT, voir
`cli.py export-analytics`). Exige `yes=True` (--yes en ligne de commande)."""

from __future__ import annotations

from pathlib import Path

from engine.db import get_sqlite, sqlite_transaction

# Les 11 tables du perimetre "seed" (tout schema.sql sauf players et
# player_attributes), enfants avant parents. Verrouille par
# tests/test_reset_seed.py : une table ajoutee au schema doit etre classee ici
# (seed) ou dans les tables preservees du test.
SEED_TABLES_DELETION_ORDER: tuple[str, ...] = (
    "similarity_signatures",
    "phrase_history",
    "phrase_tags",
    "phrase_cooldowns",
    "phrase_slots",
    "phrase_conditions",
    "slot_dictionaries",
    "tags",
    "phrases",
    "variants",
    "scenarios",
)


def reset_seed(sqlite_path: str | Path, *, yes: bool) -> dict[str, int]:
    """Supprime toutes les lignes des 11 tables seed et remet leurs compteurs
    AUTOINCREMENT a zero (sqlite_sequence), dans UNE transaction. Retourne le
    nombre de lignes supprimees par table. `players`/`player_attributes` (et
    leur compteur) ne sont jamais touchees.

    Leve ValueError, sans rien ecrire, si `yes` n'est pas True."""
    if not yes:
        raise ValueError(
            "reset_seed est destructif (banque de phrases ET historique d'usage) : "
            "confirmation requise (--yes). Pour conserver l'historique, exportez-le d'abord "
            "dans DuckDB : `python cli.py export-analytics`."
        )
    conn = get_sqlite(sqlite_path)
    try:
        deleted: dict[str, int] = {}
        with sqlite_transaction(conn):
            for table in SEED_TABLES_DELETION_ORDER:
                deleted[table] = conn.execute(f"DELETE FROM {table}").rowcount
            placeholders = ", ".join("?" for _ in SEED_TABLES_DELETION_ORDER)
            conn.execute(
                f"DELETE FROM sqlite_sequence WHERE name IN ({placeholders})", SEED_TABLES_DELETION_ORDER
            )
        return deleted
    finally:
        conn.close()

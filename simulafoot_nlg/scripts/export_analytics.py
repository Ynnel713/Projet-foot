"""SQLite (runtime) -> DuckDB (analytics.duckdb) : exporte les tables utiles
a l'analyse (usage de la banque, pas les joueurs -- deja dans DuckDB via
data/import/import_players.py) pour interrogation SQL libre (ex. "quelles
phrases sont le plus utilisees par scenario"), sans jamais requeter la base
runtime directement (WAL + lectures concurrentes, mais on evite de coupler
un usage analytique au chemin critique du moteur)."""

from __future__ import annotations

from pathlib import Path

from engine.db import get_duckdb, get_sqlite

# Tables copiees telles quelles -- toutes celles utiles a l'analytics
# d'usage de la banque (pas players/player_attributes, deja dans DuckDB).
EXPORTED_TABLES = (
    "scenarios",
    "variants",
    "phrases",
    "phrase_history",
    "phrase_cooldowns",
)


def export_analytics(sqlite_path: str | Path, duckdb_path: str | Path) -> dict[str, int]:
    """Recopie chaque table de EXPORTED_TABLES dans DuckDB. Retourne
    {nom_table: nombre_de_lignes} pour le log CLI. Une table runtime encore
    vide (ex. phrase_history avant tout usage) donne 0, pas une erreur."""
    sqlite_conn = get_sqlite(sqlite_path)
    duck = get_duckdb(duckdb_path)
    counts: dict[str, int] = {}
    try:
        for table in EXPORTED_TABLES:
            rows = sqlite_conn.execute(f"SELECT * FROM {table}").fetchall()
            columns = [d[0] for d in sqlite_conn.execute(f"SELECT * FROM {table} LIMIT 0").description]
            duck.execute(f"CREATE OR REPLACE TABLE {table} ({', '.join(f'{c} VARCHAR' for c in columns)})")
            if rows:
                duck.executemany(
                    f"INSERT INTO {table} VALUES ({', '.join('?' for _ in columns)})",
                    [tuple(row) for row in rows],
                )
            counts[table] = len(rows)
    finally:
        sqlite_conn.close()
        duck.close()
    return counts


if __name__ == "__main__":
    default_sqlite = Path(__file__).resolve().parent.parent / "data" / "simulafoot.db"
    default_duckdb = Path(__file__).resolve().parent.parent / "data" / "analytics.duckdb"
    result = export_analytics(default_sqlite, default_duckdb)
    for table, count in result.items():
        print(f"{table}: {count} lignes exportées")

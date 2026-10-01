"""Cas minimum du brief : fixture Excel minimale (3 joueurs) -> vérifie
count + attributs, plus les cas limites explicitement listés (attributs
manquants NaN/vide/"-", nom composé/particule/apostrophe, poste secondaire
multiple, preferred moves multiples ";", valeur marchande non numérique,
classeur/feuille absents)."""

from __future__ import annotations

import importlib
import sqlite3

import pandas as pd
import pytest

from scripts.init_db import init_db

# "import" est un mot-clé Python -- voir la note en tête de cli.py, même
# contournement ici (importlib.import_module prend une chaîne, pas
# l'identifiant réservé).
_import_players_module = importlib.import_module("data.import.import_players")
import_players = _import_players_module.import_players
_parse_market_value = _import_players_module._parse_market_value
_split_positions = _import_players_module._split_positions
_split_preferred_moves = _import_players_module._split_preferred_moves
_row_to_player = _import_players_module._row_to_player

COLUMNS = [
    "ID", "Colonne1", "Prénom", "Nom", "Nationalité", "Âge", "Poste", "Club", "Championnat",
    "Valeur marchande", "Note transfermrkt", "Taille (cm)", "Taille FM (cm)", "Statut", "Catégorie",
    "Pieds", "Moyenne joueur", "Pace", "Finishing", "Marking", "Postes FM naturels",
    "Weak foot (/5)", "Preferred moves",
]


def _row(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {c: None for c in COLUMNS}
    base.update(overrides)
    return base


@pytest.fixture
def sample_xlsx(tmp_path):
    """3 joueurs, chacun exerçant un ou plusieurs cas limites du brief."""
    rows = [
        _row(
            ID=1, Prénom="Kylian", Nom="Mbappé", Nationalité="France", Âge=26,
            Poste="BU / AG", **{"Postes FM naturels": "ST, AMR"},
            Club="Real Madrid", Championnat="LaLiga",
            **{"Valeur marchande": "€180.00m", "Note transfermrkt": 9.0},
            **{"Taille (cm)": 178}, Statut="star", Catégorie="ST_Poacher", Pieds="D",
            **{"Moyenne joueur": 91, "Pace": 95, "Finishing": 90},
            **{"Weak foot (/5)": 4, "Preferred moves": "Cuts Inside ; Runs With Ball Often"},
        ),
        _row(
            # Nom à apostrophe, valeur marchande non numérique ("-"),
            # attributs manquants (NaN pandas natif pour les cellules vides).
            ID=2, Prénom="Jake", Nom="O'Brien", Nationalité="Irlande", Âge=25,
            Poste="DC", Club="Lyon", Championnat="Ligue 1",
            **{"Valeur marchande": "-"}, Pieds="D",
            **{"Moyenne joueur": 77},
        ),
        _row(
            # Particule ("van Dijk"), tiret cadratin, preferred moves "(aucun)".
            ID=3, Prénom="Virgil", Nom="van Dijk", Nationalité="Pays-Bas", Âge=33,
            Poste="DC", Club="Liverpool", Championnat="Premier League",
            **{"Valeur marchande": "—"}, Pieds="D",
            **{"Moyenne joueur": 88, "Marking": 90},
            **{"Preferred moves": "(aucun)"},
        ),
    ]
    df = pd.DataFrame(rows, columns=COLUMNS)
    path = tmp_path / "joueurs.xlsx"
    df.to_excel(path, sheet_name="Infos principales", index=False)
    return path


def test_import_players_counts_and_writes_to_sqlite(sample_xlsx, tmp_path):
    sqlite_path = tmp_path / "simulafoot.db"
    duckdb_path = tmp_path / "analytics.duckdb"
    init_db(db_path=sqlite_path)

    stats = import_players(sample_xlsx, duckdb_path, sqlite_path)

    assert stats.players_imported == 3
    assert stats.attributes_mapped == 3  # Pace+Finishing (joueur 1) + Marking (joueur 3)
    assert "Colonne1" in stats.columns_ignored

    conn = sqlite3.connect(sqlite_path)
    conn.row_factory = sqlite3.Row
    try:
        count = conn.execute("SELECT COUNT(*) FROM players").fetchone()[0]
        assert count == 3

        obrien = conn.execute("SELECT * FROM players WHERE id = 2").fetchone()
        assert obrien["last_name"] == "O'Brien"  # apostrophe préservée, pas d'injection SQL cassée
        assert obrien["market_value"] is None  # "-" -> None, pas 0 ni une erreur

        van_dijk = conn.execute("SELECT * FROM players WHERE id = 3").fetchone()
        assert van_dijk["last_name"] == "van Dijk"  # particule préservée telle quelle
        assert van_dijk["market_value"] is None  # "—" -> None

        mbappe = conn.execute("SELECT * FROM players WHERE id = 1").fetchone()
        assert mbappe["market_value"] == pytest.approx(180.0)
        assert mbappe["secondary_positions"] == "AG / ST / AMR"
        assert mbappe["preferred_moves"] == "Cuts Inside ; Runs With Ball Often"

        pace = conn.execute(
            "SELECT value FROM player_attributes WHERE player_id = 1 AND attribute = 'Pace'"
        ).fetchone()
        assert pace["value"] == 95
    finally:
        conn.close()


def test_import_players_is_idempotent_on_id(sample_xlsx, tmp_path):
    sqlite_path = tmp_path / "simulafoot.db"
    duckdb_path = tmp_path / "analytics.duckdb"
    init_db(db_path=sqlite_path)

    import_players(sample_xlsx, duckdb_path, sqlite_path)
    stats_second_run = import_players(sample_xlsx, duckdb_path, sqlite_path)

    conn = sqlite3.connect(sqlite_path)
    try:
        count = conn.execute("SELECT COUNT(*) FROM players").fetchone()[0]
    finally:
        conn.close()
    assert count == 3  # pas 6 : upsert sur id, pas de doublon
    assert stats_second_run.players_imported == 3


def test_import_players_missing_file_raises_explicit_error(tmp_path):
    with pytest.raises(FileNotFoundError, match="introuvable"):
        import_players(tmp_path / "absent.xlsx", tmp_path / "a.duckdb", tmp_path / "a.db")


def test_import_players_missing_sheet_raises_explicit_error(tmp_path):
    path = tmp_path / "joueurs.xlsx"
    pd.DataFrame({"x": [1]}).to_excel(path, sheet_name="Autre Feuille", index=False)

    with pytest.raises(ValueError, match="Infos principales"):
        import_players(path, tmp_path / "a.duckdb", tmp_path / "a.db")


# --- fonctions de nettoyage, testées isolément (cas limites précis) --------

def test_parse_market_value_handles_millions_and_thousands():
    assert _parse_market_value("€30.00m") == pytest.approx(30.0)
    assert _parse_market_value("€500k") == pytest.approx(0.5)


@pytest.mark.parametrize("raw", ["-", "—", "", None, float("nan")])
def test_parse_market_value_treats_empty_markers_as_none(raw):
    assert _parse_market_value(raw) is None


def test_split_positions_combines_poste_slash_and_postes_fm_comma():
    main, secondary = _split_positions("RB / DC", "WBR, DR")
    assert main == "RB"
    assert secondary == ("DC", "WBR", "DR")


def test_split_positions_deduplicates_and_excludes_main():
    main, secondary = _split_positions("AD / AG", "AD, AG, ST")
    assert main == "AD"
    assert secondary == ("AG", "ST")  # "AD" ré-listé dans Postes FM naturels n'est pas dupliqué


def test_split_preferred_moves_splits_on_semicolon_and_trims():
    assert _split_preferred_moves("Move A ; Move B ;Move C") == ("Move A", "Move B", "Move C")


def test_split_preferred_moves_none_marker_gives_empty_tuple():
    assert _split_preferred_moves("(aucun)") == ()


# --- height_cm : priorite FM26 sur Transfermarkt, decision du 01/10/2026 ---
# Bug trouve le 30/09/2026 : cette ligne lisait "Taille (cm)" (Transfermarkt,
# 11.7% de couverture) au lieu de "Taille FM (cm)" (scrapee, 93%) -- deux
# colonnes differentes dans le classeur. Verifie avant bascule (01/10/2026) :
# sur les 93+84 joueurs portant une valeur sentinelle connue sur "Taille (cm)"
# (152.4cm/154.9cm, conversion pieds/pouces ratee), 91 et 82 respectivement
# ont une valeur FM coherente -- la bascule les corrige, elle ne les casse pas.

def test_height_cm_prefers_fm26_column_when_both_present():
    row = pd.Series(_row(ID=99, **{"Taille (cm)": 152.4, "Taille FM (cm)": 178}))
    player = _row_to_player(row)
    assert player is not None
    assert player["height_cm"] == 178  # pas la sentinelle Transfermarkt (152.4)


def test_height_cm_falls_back_to_transfermarkt_column_when_fm26_missing():
    row = pd.Series(_row(ID=99, **{"Taille (cm)": 184, "Taille FM (cm)": None}))
    player = _row_to_player(row)
    assert player is not None
    assert player["height_cm"] == 184


def test_height_cm_is_none_when_both_columns_missing():
    row = pd.Series(_row(ID=99))
    player = _row_to_player(row)
    assert player is not None
    assert player["height_cm"] is None
    assert _split_preferred_moves(None) == ()


# --- height_cm : sentinelles Transfermarkt sans source FM26 -> None ---
# Non-regression : sans _height_cm, ces joueurs gardaient 152/154 cm et
# matchaient `height_cm <= 172` (SURNOM "lutin") a tort.

@pytest.mark.parametrize("sentinelle", [152.4, 154.9])
def test_height_cm_sentinelle_transfermarkt_sans_source_fm_devient_none(sentinelle):
    row = pd.Series(_row(ID=99, **{"Taille (cm)": sentinelle, "Taille FM (cm)": None}))
    player = _row_to_player(row)
    assert player is not None
    assert player["height_cm"] is None


def test_height_cm_valeur_fm_est_conservee_meme_si_egale_a_une_sentinelle():
    row = pd.Series(_row(ID=99, **{"Taille (cm)": None, "Taille FM (cm)": 152}))
    player = _row_to_player(row)
    assert player is not None
    assert player["height_cm"] == 152


def test_base_reelle_ne_contient_aucune_sentinelle_height_cm():
    """Garde-fou sur la base locale (non versionnee) : un import qui
    laisserait 152/154 cm declencherait "lutin" a tort. Ignore si la base
    n'existe pas (CI, poste vierge)."""
    from pathlib import Path

    chemin = Path(__file__).resolve().parent.parent / "data" / "simulafoot.db"
    if not chemin.exists():
        pytest.skip("base locale absente")
    with sqlite3.connect(chemin) as conn:
        sentinelles = conn.execute(
            "SELECT id FROM players WHERE height_cm IN (152, 154)"
        ).fetchall()
    assert sentinelles == []

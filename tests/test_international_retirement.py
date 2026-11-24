"""Retraite internationale (ticket donnees-nouveaux-joueurs/08) : colonne écrite par
scripts/set_international_retirement.py, joueurs écartés par scripts/generate_national_teams.py."""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import openpyxl
from openpyxl.worksheet.filters import AutoFilter
from openpyxl.worksheet.table import Table

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import generate_national_teams as gnt
import set_international_retirement as sir

HEADERS = ["ID", "Prénom", "Nom", "Nationalité", "Club"]


def workbook(rows):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = sir.SHEET
    ws.append(HEADERS)
    for r in rows:
        ws.append(r)
    ref = f"A1:E{ws.max_row}"
    table = Table(displayName=sir.TABLE_NAME, ref=ref, autoFilter=AutoFilter(ref=ref))
    table._initialise_columns()
    ws.add_table(table)
    return wb, ws


ROWS = [[1, "Lionel", "Messi", "Argentine", "Inter Miami CF"], [2, "Julián", "Álvarez", "Argentine", "Atlético"],
        [3, "Neymar", None, "Brésil", "Santos FC"]]


def test_colonne_ajoutee_et_remplie(tmp_path):
    _, ws = workbook(ROWS)
    marked, missing, changed = sir.apply(ws, {1: "Lionel Messi", 3: "Neymar", 99: "Inconnu"})
    h = {c.value: c.column for c in ws[1]}
    assert h[sir.COLUMN] == 6 and ws.tables[sir.TABLE_NAME].ref == "A1:F4"
    assert [tc.name for tc in ws.tables[sir.TABLE_NAME].tableColumns][-1] == sir.COLUMN
    assert [ws.cell(r, 6).value for r in (2, 3, 4)] == ["oui", None, "oui"]
    assert [m[0] for m in marked] == [1, 3] and missing == [99] and changed == 2
    assert [[ws.cell(r, c).value for c in range(1, 6)] for r in (2, 3, 4)] == ROWS  # rien d'autre ne bouge
    again = sir.apply(ws, {1: "Lionel Messi", 3: "Neymar"})  # idempotent
    assert again[2] == 0 and ws.max_column == 6
    assert sir.apply(ws, {1: "Lionel Messi"})[2] == 1 and ws.cell(4, 6).value is None  # retiré de la liste


def test_lecture_de_la_liste(tmp_path):
    path = tmp_path / "r.csv"
    path.write_text("ID;Joueur\n7654;Lionel Messi\n;vide\nabc;texte\n2521;Neymar\n", encoding="utf-8")
    assert sir.read_list(path) == {7654: "Lionel Messi", 2521: "Neymar"}


def test_selections_ecartent_les_retraites(tmp_path, monkeypatch):
    wb, ws = workbook(ROWS)
    sir.apply(ws, {1: "Lionel Messi"})
    path = tmp_path / "joueurs.xlsx"
    wb.save(path)
    assert gnt._retired_ids(str(path)) == {1}
    players = [SimpleNamespace(id=pid, nationalite=nat) for pid, _, _, nat, _ in ROWS]
    monkeypatch.setattr(gnt, "load_all_clubs", lambda p: [SimpleNamespace(players=players)])
    monkeypatch.setattr(gnt, "_canonical_nationality", lambda tok, reg: tok if tok in reg else None)
    by_nat, _ = gnt._players_by_nationality(str(path), {"Argentine": ("", ""), "Brésil": ("", "")})
    assert [p.id for p in by_nat["Argentine"]] == [2] and [p.id for p in by_nat["Brésil"]] == [3]


def test_sans_colonne_personne_n_est_ecarte(tmp_path):
    wb, _ = workbook(ROWS)
    path = tmp_path / "joueurs.xlsx"
    wb.save(path)
    assert gnt._retired_ids(str(path)) == set()

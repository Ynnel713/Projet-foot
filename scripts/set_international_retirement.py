"""
Colonne « Retraite internationale » de data/joueurs.xlsx (ticket donnees-nouveaux-joueurs/08).

Source : data/retraites_internationales.csv (colonnes ID;Joueur), tenue par le propriétaire.
La colonne vaut « oui » pour les joueurs listés, vide pour les autres ; elle est ajoutée à droite
de « Infos principales » si absente (tableau Tableau8 étendu). Effet : scripts/generate_national_teams.py
écarte ces joueurs des sélections nationales ; en club, rien ne change.

Usage :
    uv run python scripts/set_international_retirement.py [--dry-run]
    uv run python scripts/generate_national_teams.py
Fermer joueurs.xlsx dans Excel avant.
"""
from __future__ import annotations

import argparse
import copy
import csv
import sys
from pathlib import Path

from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import TableColumn

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_EXCEL = ROOT / "data" / "joueurs.xlsx"
DEFAULT_LIST = ROOT / "data" / "retraites_internationales.csv"
SHEET = "Infos principales"
TABLE_NAME = "Tableau8"
COLUMN = "Retraite internationale"
YES = "oui"


def read_list(path: Path) -> dict[int, str]:
    """{ID: nom indicatif} depuis le CSV « ID;Joueur »."""
    with path.open(encoding="utf-8-sig") as f:
        return {int(r["ID"]): (r.get("Joueur") or "").strip()
                for r in csv.DictReader(f, delimiter=";") if (r.get("ID") or "").strip().isdigit()}


def ensure_column(ws) -> int:
    """Numéro de la colonne, ajoutée à droite (style et tableau Excel étendus) si absente."""
    headers = {c.value: c.column for c in ws[1] if c.value is not None}
    if COLUMN in headers:
        return headers[COLUMN]
    col = max(headers.values()) + 1
    ws.cell(1, col, COLUMN)._style = copy.copy(ws.cell(1, col - 1)._style)
    ws.column_dimensions[get_column_letter(col)].width = len(COLUMN) + 2
    if TABLE_NAME in ws.tables:
        t = ws.tables[TABLE_NAME]
        start, end = t.ref.split(":")
        t.ref = f"{start}:{get_column_letter(col)}{''.join(ch for ch in end if ch.isdigit())}"
        if t.autoFilter:
            t.autoFilter.ref = t.ref
        t.tableColumns.append(TableColumn(id=max(tc.id for tc in t.tableColumns) + 1, name=COLUMN))
    return col


def apply(ws, retired: dict[int, str]) -> tuple[list[tuple[int, str, str]], list[int], int]:
    """Écrit la colonne. Retourne (marqués [(ID, nom du classeur, nom de la liste)], ID absents
    du classeur, cellules changées)."""
    col = ensure_column(ws)
    headers = {c.value: c.column for c in ws[1] if c.value is not None}
    marked, seen, changed = [], set(), 0
    for r in range(2, ws.max_row + 1):
        pid = ws.cell(r, headers["ID"]).value
        if pid is None:
            continue
        value = YES if pid in retired else None
        if ws.cell(r, col).value != value:
            ws.cell(r, col).value = value
            changed += 1
        if pid in retired:
            seen.add(pid)
            name = f"{ws.cell(r, headers['Prénom']).value or ''} {ws.cell(r, headers['Nom']).value or ''}".strip()
            marked.append((pid, name, retired[pid]))
    return marked, sorted(set(retired) - seen), changed


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--excel", type=Path, default=DEFAULT_EXCEL)
    ap.add_argument("--list", type=Path, default=DEFAULT_LIST)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    import openpyxl
    wb = openpyxl.load_workbook(args.excel)
    ws = wb[SHEET]
    marked, missing, changed = apply(ws, read_list(args.list))
    for pid, name, listed in marked:
        print(f"  ID {pid} : {name} (liste : {listed})")
    if missing:
        print(f"! ID absents du classeur (ignorés) : {missing}")
    print(f"{len(marked)} joueurs en retraite internationale ; {changed} cellules modifiées.")
    if args.dry_run or not changed:
        print("Classeur non modifié.")
        return 0
    try:
        wb.save(args.excel)
    except PermissionError:
        sys.exit(f"Impossible d'écrire {args.excel.name} : ferme-le dans Excel puis relance.")
    print("Étape suivante : uv run python scripts/generate_national_teams.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

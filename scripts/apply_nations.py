"""
Nationalités des nouveaux joueurs (ticket donnees-nouveaux-joueurs/09).

Lit le fichier des nations rempli par le propriétaire (colonnes Nom, Prénom, Poste, Club, Nation,
voir add_fmsave_players.write_nations_excel), uniformise les noms de pays sur les libellés de
data/joueurs.xlsx (NATION_FIXES) et les reporte dans la colonne « Nationalité » des joueurs
retrouvés par (Nom, Prénom, Poste, Club). Seules les lignes encore « À renseigner » sont
modifiées ; rien d'autre ne change. Le fichier uniformisé est réécrit (--out).

Usage :
    uv run python scripts/apply_nations.py --nations <fichier rempli> [--dry-run]
    uv run python scripts/generate_national_teams.py
Fermer joueurs.xlsx dans Excel avant.
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_EXCEL = ROOT / "data" / "joueurs.xlsx"
DEFAULT_OUT = ROOT / "data" / "nouveaux_joueurs_nations.xlsx"
SHEET = "Infos principales"
PLACEHOLDER = "À renseigner"
HEADER = ["Nom", "Prénom", "Poste", "Club", "Nation"]

# Libellés du propriétaire -> libellés de la base (24/11/2026). Fautes de frappe et variantes
# d'écriture ; les autres libellés sont déjà ceux de la base.
NATION_FIXES = {
    "Bréso": "Brésil",
    "Danemarl": "Danemark",
    "Ecosse": "Écosse",
    "Egypte": "Égypte",
    "Etats Unis": "États-Unis",
    "Israel": "Israël",
    "Macédoine": "Macédoine du Nord",
    "Nigéria": "Nigeria",
    "Pays Bas": "Pays-Bas",
    "Tchéquie": "République tchèque",
    "Iles Feroé": "Îles Féroé",
}


def uniform(nation: str | None) -> str | None:
    if nation is None:
        return None
    n = " ".join(str(nation).split())
    return NATION_FIXES.get(n, n) or None


def key(nom, prenom, poste, club) -> tuple[str, str, str, str]:
    return tuple(str(v or "").strip() for v in (nom, prenom, poste, club))


def read_nations(path: Path) -> list[tuple[tuple[str, str, str, str], str | None]]:
    import openpyxl
    ws = openpyxl.load_workbook(path, read_only=True).active
    rows = list(ws.iter_rows(values_only=True))
    if [str(c or "").strip() for c in rows[0][:5]] != HEADER:
        raise SystemExit(f"En-tête inattendu dans {path.name} : {rows[0][:5]} (attendu {HEADER})")
    return [(key(*r[:4]), uniform(r[4])) for r in rows[1:] if any(r[:4])]


def apply(ws, nations: list[tuple[tuple, str | None]]) -> dict:
    """Écrit les nationalités. Retourne un bilan : appliqués, déjà renseignés (non touchés),
    introuvables, ambigus, vides."""
    h = {c.value: c.column for c in ws[1] if c.value is not None}
    rows_by_key: dict[tuple, list[int]] = {}
    for r in range(2, ws.max_row + 1):
        if ws.cell(r, h["ID"]).value is None:
            continue
        k = key(ws.cell(r, h["Nom"]).value, ws.cell(r, h["Prénom"]).value, ws.cell(r, h["Poste"]).value,
                ws.cell(r, h["Club"]).value)
        rows_by_key.setdefault(k, []).append(r)
    out = {"appliqués": [], "inchangés": 0, "déjà renseignés": [], "introuvables": [], "ambigus": [], "vides": []}
    for k, nation in nations:
        if not nation:
            out["vides"].append(k)
            continue
        candidates = [r for r in rows_by_key.get(k, [])
                      if ws.cell(r, h["Nationalité"]).value in (PLACEHOLDER, nation)]
        if not candidates:
            (out["déjà renseignés"] if k in rows_by_key else out["introuvables"]).append(k)
        elif len(candidates) > 1:
            out["ambigus"].append(k)
        elif ws.cell(candidates[0], h["Nationalité"]).value == nation:
            out["inchangés"] += 1
        else:
            ws.cell(candidates[0], h["Nationalité"]).value = nation
            out["appliqués"].append((ws.cell(candidates[0], h["ID"]).value, k, nation))
    return out


def write_uniform(path: Path, nations: list[tuple[tuple, str | None]]):
    import openpyxl
    from openpyxl.worksheet.table import Table
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Nouveaux joueurs"
    ws.append(HEADER)
    for k, nation in nations:
        ws.append([*k, nation])
    ws.freeze_panes = "A2"
    for col, width in zip("ABCDE", (24, 20, 16, 32, 20), strict=True):
        ws.column_dimensions[col].width = width
    if nations:
        ws.add_table(Table(displayName="NouveauxJoueurs", ref=f"A1:E{len(nations) + 1}"))
    wb.save(path)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--nations", type=Path, required=True, help="fichier des nations rempli")
    ap.add_argument("--excel", type=Path, default=DEFAULT_EXCEL)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT, help="fichier des nations uniformisé")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    import openpyxl
    nations = read_nations(args.nations)
    wb = openpyxl.load_workbook(args.excel)
    ws = wb[SHEET]
    nat_col = {c.value: c.column for c in ws[1] if c.value is not None}["Nationalité"]
    base = {ws.cell(r, nat_col).value for r in range(2, ws.max_row + 1)}  # avant écriture
    res = apply(ws, nations)
    labels = Counter(n for _, n in nations if n)
    unknown = sorted(n for n in labels if n not in base)
    print(f"{len(nations)} lignes lues ; {len(labels)} pays après uniformisation.")
    print(f"Appliqués {len(res['appliqués'])}, déjà à jour {res['inchangés']}, vides {len(res['vides'])}, "
          f"introuvables {len(res['introuvables'])}, ambigus {len(res['ambigus'])}, "
          f"déjà renseignés autrement {len(res['déjà renseignés'])}.")
    for name in ("introuvables", "ambigus", "déjà renseignés", "vides"):
        for k in res[name][:10]:
            print(f"  {name} : {' / '.join(k)}")
    if unknown:
        print("Pays absents de la base jusqu'ici (sans sélection si aucun onglet ne les connaît) : "
              + ", ".join(f"{n} ({labels[n]})" for n in unknown))
    if args.dry_run:
        print("Essai à blanc : rien n'est écrit.")
        return 0
    write_uniform(args.out, nations)
    if res["appliqués"]:
        try:
            wb.save(args.excel)
        except PermissionError:
            sys.exit(f"Impossible d'écrire {args.excel.name} : ferme-le dans Excel puis relance.")
    print(f"Fichier uniformisé : {args.out}. Étape suivante : uv run python scripts/generate_national_teams.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

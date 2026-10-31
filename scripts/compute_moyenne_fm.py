"""Calcule la colonne "Moyenne FM" de data/joueurs.xlsx, note qui fait foi dans la V1.

Décision du propriétaire (30/10/2026) : la V1 (moteur Poisson) est pilotée par une moyenne
issue des attributs FM, "Moyenne joueur" restant intacte à côté. Pour chaque joueur :
1. moyenne des attributs FM pondérée par leur importance pour son meilleur poste parmi ceux
   listés dans le groupe de son poste principal (players.fm_weighted_mean) ;
2. remise à l'échelle actuelle par rangs, au sein de sa famille de table (DC, Latéral, MDC, MC,
   MOC, Ailier, BU, GK ; players.fm_table_family) : le joueur reçoit la "Moyenne joueur" de même
   rang dans sa famille (notes par défaut < 30 exclues). Le classement suit FM, la distribution des notes (~35-91) reste celle sur laquelle
   le moteur est calibré -- la moyenne brute est deux fois plus resserrée (écart-type 6,3
   contre 12,7).
Joueur sans attributs FM : Moyenne FM = Moyenne joueur.

À relancer après toute mise à jour des attributs ou de Moyenne joueur, puis
scripts/generate_national_teams.py. Fermer joueurs.xlsx dans Excel avant.

Usage :
    uv run python scripts/compute_moyenne_fm.py [--path data/joueurs.xlsx] [--dry-run]
"""

from __future__ import annotations

import argparse
import copy
import sys
from pathlib import Path

import openpyxl
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import TableColumn

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from ligue1sim.clubs import NOTE_COLUMN  # noqa: E402
from ligue1sim.players import (  # noqa: E402
    FM_ATTRIBUTE_COLUMNS,
    fm_table_family,
    fm_weighted_mean,
    position_group,
)

SHEET = "Infos principales"
SOURCE_COLUMN = "Moyenne joueur"
# ~150 jeunes réservistes sans valeur marchande ont une Moyenne joueur par défaut (19 à 22) :
# exclues de l'échelle de référence, sinon le joueur le plus faible selon FM hérite de 19,5.
PLACEHOLDER_BELOW = 30


def rank_rescale(raw: dict[int, float], reference: list[float]) -> dict[int, float]:
    """{clé: valeur brute} -> {clé: valeur de `reference` au même rang} (ex aequo : même valeur)."""
    ref = sorted(reference)
    order = sorted(raw, key=raw.get)
    out, i = {}, 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and raw[order[j + 1]] == raw[order[i]]:
            j += 1
        mid = (i + j) / 2 * (len(ref) - 1) / max(1, len(order) - 1)
        lo = int(mid)
        value = ref[lo] + (ref[min(lo + 1, len(ref) - 1)] - ref[lo]) * (mid - lo)
        for k in order[i:j + 1]:
            out[k] = round(value * 2) / 2  # même pas que Moyenne joueur (0,5)
        i = j + 1
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--path", default="data/joueurs.xlsx")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    wb = openpyxl.load_workbook(args.path)
    ws = wb[SHEET]
    h = {c.value: c.column for c in ws[1] if c.value}
    target = h["Nom"] + 1  # demande du propriétaire : colonne juste après le nom du joueur
    if h.get(NOTE_COLUMN) != target:
        widths = {c: ws.column_dimensions[get_column_letter(c)].width for c in range(1, ws.max_column + 1)}
        order = [c for c in range(1, ws.max_column + 1) if c != h.get(NOTE_COLUMN)]
        if NOTE_COLUMN in h:
            ws.delete_cols(h[NOTE_COLUMN])
        ws.insert_cols(target)
        ws.cell(1, target, NOTE_COLUMN)._style = copy.copy(ws.cell(1, target - 1)._style)
        # openpyxl ne décale ni les largeurs de colonnes ni le tableau Excel : on les reporte
        order.insert(target - 1, None)
        for new, old in enumerate(order, 1):
            ws.column_dimensions[get_column_letter(new)].width = widths.get(old) or 12
        for t in ws.tables.values():
            start, end = t.ref.split(":")
            t.ref = f"{start}:{get_column_letter(ws.max_column)}{''.join(ch for ch in end if ch.isdigit())}"
            if t.autoFilter:
                t.autoFilter.ref = t.ref
            t.tableColumns = [TableColumn(id=i, name=str(c.value)) for i, c in enumerate(ws[1], 1)]
        h = {c.value: c.column for c in ws[1] if c.value}

    source, raw, families = {}, {}, {}
    for r in range(2, ws.max_row + 1):
        note = ws.cell(r, h[SOURCE_COLUMN]).value
        if note is None:
            continue
        source[r] = float(note)
        postes = [p.strip() for p in str(ws.cell(r, h["Poste"]).value).split("/")]
        group = position_group(postes[0])  # groupe du poste principal ("BU / AG" -> ATT)
        attrs = {a: v for a in FM_ATTRIBUTE_COLUMNS if isinstance(v := ws.cell(r, h[a]).value, (int, float))}
        # meilleur des postes listés du même groupe (Dembélé "BU / AD / AG" noté comme ailier)
        means = [(m, p) for p in postes if position_group(p) == group
                 if (m := fm_weighted_mean(attrs, p)) is not None]
        if means:
            raw[r], best = max(means)
            families[r] = fm_table_family(best) or (group,)

    # Recalage par famille de table (DC, Latéral, MDC...), pas par groupe : les tables DC et
    # Latéral ne donnent pas des notes brutes de même niveau, les classer ensemble descendait
    # les latéraux de ~3,7 points (revue expert du 31/10/2026, réserve A1).
    result = dict(source)
    for fam in set(families.values()):
        rows = [r for r in raw if families[r] == fam]
        reference = [source[r] for r in rows if source[r] >= PLACEHOLDER_BELOW]
        result.update(rank_rescale({r: raw[r] for r in rows}, reference))

    moved = sorted(((result[r] - source[r], r) for r in raw), reverse=True)
    name = lambda r: f"{ws.cell(r, h['Prénom']).value or ''} {ws.cell(r, h['Nom']).value or ''}".strip()
    print(f"{len(raw)} joueurs notés depuis FM, {len(source) - len(raw)} sans attributs (Moyenne joueur reprise)")
    print("plus fortes hausses :", ", ".join(f"{name(r)} {source[r]:g}->{result[r]:g}" for _, r in moved[:5]))
    print("plus fortes baisses :", ", ".join(f"{name(r)} {source[r]:g}->{result[r]:g}" for _, r in moved[-5:]))
    if args.dry_run:
        return 0
    for r, v in result.items():
        ws.cell(r, h[NOTE_COLUMN]).value = v
    wb.save(args.path)
    print(f"Colonne {NOTE_COLUMN!r} écrite dans {args.path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

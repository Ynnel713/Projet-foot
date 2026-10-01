"""Investigation 55 vs 48 moves -- 01/10/2026. Script d'audit ponctuel, PAS
un module moteur.

Verifie que le reservoir canonique de preferred moves (PREFERRED_MOVE_TRANSLATIONS,
scripts/make_phrase_template.py) et la feuille generee "Preferred moves" de
data/joueurs.xlsx sont identiques, puis croise avec les 56 conditions
preferred_moves reellement utilisees dans les 281 phrases (data/seed/scenarios.yml)
pour detecter tout move invente/mal orthographie qui serait hors reservoir.
"""

from __future__ import annotations

import re
import sys
from collections import Counter
from pathlib import Path

import openpyxl
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

ROOT = Path(__file__).resolve().parents[1]
MAKE_TEMPLATE_PATH = ROOT / "scripts" / "make_phrase_template.py"
JOUEURS_XLSX_PATH = ROOT.parent / "data" / "joueurs.xlsx"
SCENARIOS_PATH = ROOT / "data" / "seed" / "scenarios.yml"


def load_canon() -> dict[str, str]:
    src = MAKE_TEMPLATE_PATH.read_text(encoding="utf-8")
    m = re.search(r"PREFERRED_MOVE_TRANSLATIONS: dict\[str, str\] = \{(.*?)\n\}", src, re.DOTALL)
    assert m is not None, "PREFERRED_MOVE_TRANSLATIONS introuvable dans make_phrase_template.py"
    return dict(re.findall(r'"([^"]+)":\s*"([^"]+)"', m.group(1)))


def load_sheet_moves() -> set[str]:
    wb = openpyxl.load_workbook(JOUEURS_XLSX_PATH, read_only=True, data_only=True)
    ws = wb["Preferred moves"]
    rows = list(ws.iter_rows(values_only=True))
    return {str(r[0]) for r in rows[4:] if r[0]}


def load_used_moves() -> Counter[str]:
    with open(SCENARIOS_PATH, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    used: Counter[str] = Counter()
    for sc in data:
        for v in sc["variants"]:
            for p in v["phrases"]:
                for c in p.get("conditions", []):
                    if c["attribute"] == "preferred_moves":
                        used[c["value"]] += 1
    return used


def main() -> None:
    canon = load_canon()
    sheet = load_sheet_moves()
    used = load_used_moves()

    print(f"Canon (PREFERRED_MOVE_TRANSLATIONS) : {len(canon)} moves")
    print(f"Feuille generee (joueurs.xlsx)      : {len(sheet)} moves")
    print(f"Canon == Feuille                    : {set(canon) == sheet}")
    print(f"Moves utilises dans les 281 phrases  : {len(used)}")
    hors_canon = set(used) - set(canon)
    print(f"Utilises MAIS hors canon (invente/mal orthographie) : {hors_canon or 'AUCUN'}")
    print()

    inutilises = sorted(set(canon) - set(used))
    print(f"Moves canoniques jamais utilises dans la banque actuelle ({len(inutilises)}) :")
    for mv in inutilises:
        print(f"  - {mv} ({canon[mv]})")

    print()
    print("--- Liste complete des 55, usage dans les 281 phrases ---")
    for mv in sorted(canon):
        n = used.get(mv, 0)
        marker = "UTILISE  " if n else "inutilise"
        print(f"{n:2d}x [{marker}] {mv} -- {canon[mv]}")


if __name__ == "__main__":
    main()

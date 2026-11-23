"""
Import des attributs d'une sauvegarde Football Manager dans data/joueurs.xlsx.

Ticket .scratch/donnees-nouveaux-joueurs/issues/06a. Source : export « fmsave-list » d'une
sauvegarde FM (CSV : name, age, natural_positions, height_cm, left_foot, right_foot,
attributes_*). Le script met à jour les joueurs DÉJÀ présents dans le classeur ; il n'en
ajoute aucun (décision du propriétaire du 23/11/2026). La source contient aussi des joueuses :
elles ne peuvent pas entrer, seuls des joueurs de la base sont mis à jour.

Règles (décisions du propriétaire du 23/11/2026)
------------------------------------------------
- Correspondance : nom normalisé identique (Prénom + Nom du classeur / name de la sauvegarde)
  et âge à ±1 an, candidat unique ; refusée si un seul des deux est gardien, ou si aucun poste
  de la sauvegarde n'est à MAX_POSTE_DISTANCE crans ou moins d'un poste du classeur
  (players.poste_distance : un latéral devenu milieu défensif passe, un attaquant de la base
  n'est pas un défenseur central homonyme de la sauvegarde) ;
  une ligne de la sauvegarde réclamée par plusieurs joueurs de la base n'est utilisée pour aucun.
  Départage par le club (demande du propriétaire du 23/11/2026) : plusieurs homonymes dans la
  sauvegarde, ou plusieurs joueurs de la base pour une même ligne -> retenu seulement si un seul
  candidat a le même club (same_club) ; à défaut, seulement si un seul candidat a une valeur
  marchande du classeur (Transfermarkt) à moins d'un facteur VALUE_RATIO de celle de la
  sauvegarde (ex. Paulinho « SEP » 12,3 M€ = Palmeiras 9 M€, pas Académico de Viseu 0,3 M€) ;
  sinon rien n'est écrit pour eux.
- Échelle : la sauvegarde note de 1 à 20, le classeur de 5 à 99 (1-20 × 5, 20 -> 99 : 99,6 % des
  valeurs du classeur sont des multiples de 5, médiane du classeur = valeur de la sauvegarde × 5
  pour chaque valeur, mesuré le 23/11/2026). Conversion : v × 5, 20 -> 99.
- Attributs : remplacés par ceux de la sauvegarde, dans le jeu habituel de 36 attributs du
  métier (poste principal) : un joueur de champ n'a pas les 11 attributs de gardien, un gardien
  n'a pas les 11 attributs propres au jeu de champ.
- Pieds : D si pied droit > gauche, G si gauche > droit (égalité : valeur actuelle gardée).
- Weak foot (/5) : moins bon pied 1-4 -> 1, 5-8 -> 2, 9-12 -> 3, 13-20 -> 4 (échelle observée
  dans la base).
- Taille FM (cm) : remplie seulement si vide. Aucune autre colonne n'est touchée.

Usage
-----
    # essai à blanc (défaut) : rapport data/fmsave_import_report.csv, classeur intact
    uv run python scripts/import_fmsave_attributes.py
    # écriture (ticket 06b), puis recalcul des notes et des sélections :
    uv run python scripts/import_fmsave_attributes.py --write
    uv run python scripts/compute_moyenne_fm.py
    uv run python scripts/generate_national_teams.py
Fermer joueurs.xlsx dans Excel avant.
"""
from __future__ import annotations

import argparse
import csv
import shutil
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from fminside_new_players import fm_poste
from scrape_fminside_attributes import (
    ATTRIBUTES,
    CLUB_GENERIC,
    GOALKEEPING,
    SHEET,
    club_similarity,
    norm,
    norm_club,
)

from ligue1sim.players import poste_distance

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = ROOT / "data" / "fmsave-list.csv"
DEFAULT_EXCEL = ROOT / "data" / "joueurs.xlsx"

# Colonnes de la sauvegarde -> noms d'attributs du classeur (les autres suivent la règle
# "attributes_first_touch" -> "First Touch").
SPECIAL = {"attributes_off_the_ball": "Off the Ball", "attributes_one_on_ones": "One on Ones",
           "attributes_punching": "Punching (Tendency)", "attributes_rushing_out": "Rushing Out (Tendency)",
           "attributes_command_of_area": "Command of Area"}
# Jeux de 36 attributs observés dans le classeur (23/11/2026) : 6 290 joueurs de champ sans les
# attributs de gardien, 848 gardiens sans ces 11 attributs de jeu de champ.
OUTFIELD_ONLY = ["Corners", "Crossing", "Dribbling", "Finishing", "Free Kick Taking", "Heading", "Long Shots",
                 "Long Throws", "Marking", "Penalty Taking", "Tackling"]
FIELD_SET = [a for a in ATTRIBUTES if a not in GOALKEEPING]
GK_SET = [a for a in ATTRIBUTES if a not in OUTFIELD_ONLY]
AGE_TOLERANCE = 1
MAX_POSTE_DISTANCE = 2
VALUE_RATIO = 3.0
FOOT_COL, WEAK_COL, HEIGHT_COL = "Pieds", "Weak foot (/5)", "Taille FM (cm)"


def attribute_name(col: str) -> str:
    if col in SPECIAL:
        return SPECIAL[col]
    return " ".join(w.capitalize() for w in col.removeprefix("attributes_").split("_"))


def to_base_scale(v: int) -> int:
    """Attribut 1-20 de la sauvegarde -> échelle du classeur (× 5, 20 -> 99)."""
    return 99 if v >= 20 else v * 5


def weak_foot(left: int, right: int) -> int:
    """Moins bon pied (1-20) -> échelle /5 du classeur (1-4 -> 1, 5-8 -> 2, 9-12 -> 3, 13+ -> 4)."""
    w = min(left, right)
    return 1 if w <= 4 else 2 if w <= 8 else 3 if w <= 12 else 4


def strong_foot(left: int, right: int) -> str | None:
    return "D" if right > left else "G" if left > right else None


def to_float(v) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def parse_value(v) -> float | None:
    """Valeur marchande du classeur ("€9.00m", "€600k", "-") -> euros."""
    s = str(v or "").strip().replace("€", "").replace(",", ".").lower()
    mult = 1e6 if s.endswith("m") else 1e3 if s.endswith("k") else 1.0
    try:
        return float(s.rstrip("mk")) * mult
    except ValueError:
        return None


def close_value(base_value: float | None, save_value: float | None) -> bool:
    return bool(base_value and save_value) and 1 / VALUE_RATIO <= save_value / base_value <= VALUE_RATIO


def to_int(v) -> int | None:
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None


@dataclass
class SavePlayer:
    index: int
    name: str
    age: int | None
    positions: list[str]
    club: str
    height: int | None
    left: int | None
    right: int | None
    attrs: dict[str, int] = field(default_factory=dict)
    value: float | None = None  # valeur de transfert de la sauvegarde, en euros

    @property
    def is_gk(self) -> bool:
        return "GK" in self.positions

    @property
    def postes(self) -> list[str]:
        """Postes naturels de la sauvegarde au format du classeur ("STC AML" -> ["BU", "AG"])."""
        postes = fm_poste([p.replace("STC", "ST") for p in self.positions]) or ""
        return [p for p in postes.split(" / ") if p]


def postes_close(base_poste: str, save_postes: list[str]) -> bool:
    """Au moins un poste de la sauvegarde à MAX_POSTE_DISTANCE crans ou moins d'un poste du classeur."""
    base = [p.strip() for p in str(base_poste).split("/") if p.strip()]
    return any((d := poste_distance(b, s)) is not None and d <= MAX_POSTE_DISTANCE
               for b in base for s in save_postes)


def read_save(path: Path) -> list[SavePlayer]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        cols = [c for c in reader.fieldnames or [] if c.startswith("attributes_")]
        mapping = {c: attribute_name(c) for c in cols}
        unknown = sorted(set(mapping.values()) - set(ATTRIBUTES))
        missing = sorted(set(ATTRIBUTES) - set(mapping.values()))
        if unknown or missing:
            raise SystemExit(f"Colonnes d'attributs inattendues : inconnues {unknown}, absentes {missing}")
        out = []
        for i, row in enumerate(reader):
            out.append(SavePlayer(
                index=i, name=(row.get("name") or "").strip(), age=to_int(row.get("age")),
                positions=(row.get("natural_positions") or "").split(), club=(row.get("club_name") or "").strip(),
                height=to_int(row.get("height_cm")), left=to_int(row.get("left_foot")),
                right=to_int(row.get("right_foot")), value=to_float(row.get("transfer_value")),
                attrs={mapping[c]: v for c in cols if (v := to_int(row.get(c))) is not None}))
    return out


@dataclass
class Match:
    row: int
    pid: int
    name: str
    club: str
    poste: str
    status: str
    save: SavePlayer | None = None
    value: float | None = None  # valeur marchande du classeur, en euros
    detail: str = ""


def same_club(a: str, b: str) -> bool:
    """Même club malgré deux écritures : club_similarity >= 0,8, ou nom court entièrement contenu
    dans le nom long avec au moins un mot distinctif de 4 lettres ou plus ("US Lecce" /
    "Unione Sportiva Lecce", "FC Porto" / "Futebol Clube do Porto"). Ne sert qu'à départager des
    candidats qui ont déjà le même nom et le même âge."""
    if not a or not b:
        return False
    if club_similarity(a, b) >= 0.8:
        return True
    ta, tb = set(norm_club(a).split()), set(norm_club(b).split())
    short, long_ = (ta, tb) if len(ta) <= len(tb) else (tb, ta)
    return bool(short) and short <= long_ and any(len(t) >= 4 and t not in CLUB_GENERIC for t in short)


def match_players(ws, headers: dict, save: list[SavePlayer]) -> list[Match]:
    by_name: dict[str, list[SavePlayer]] = defaultdict(list)
    for sp in save:
        by_name[norm(sp.name)].append(sp)
    matches: list[Match] = []
    for r in range(2, ws.max_row + 1):
        pid = ws.cell(r, headers["ID"]).value
        if pid is None:
            continue
        def g(h, r=r):
            return ws.cell(r, headers[h]).value
        name = f"{g('Prénom') or ''} {g('Nom') or ''}".strip()
        poste = str(g("Poste") or "")
        value = parse_value(g("Valeur marchande")) if "Valeur marchande" in headers else None
        m = Match(r, int(pid), name, str(g("Club") or ""), poste, "ABSENT", value=value)
        age = to_int(g("Âge"))
        cands = [sp for sp in by_name.get(norm(name), [])
                 if age is None or sp.age is None or abs(sp.age - age) <= AGE_TOLERANCE]
        if len(cands) > 1:
            by_club = [c for c in cands if same_club(m.club, c.club)]
            by_value = [c for c in cands if close_value(m.value, c.value)]
            if len(by_club) == 1:
                cands, m.detail = by_club, "homonymes départagés par le club"
            elif not by_club and len(by_value) == 1:
                cands, m.detail = by_value, "homonymes départagés par la valeur marchande"
            else:
                m.status, m.detail = "HOMONYMES", " | ".join(f"{c.name} {c.age} {c.club}" for c in cands)
        if len(cands) == 1:
            sp = cands[0]
            base_gk = poste.split("/")[0].strip() == "GK"
            if base_gk != sp.is_gk or not postes_close(poste, sp.postes):
                m.status, m.detail = "POSTE_INCOMPATIBLE", f"classeur {poste} / sauvegarde {' '.join(sp.positions)}"
            else:
                m.status, m.save = "RETROUVÉ", sp
        matches.append(m)
    claims: dict[int, list[Match]] = defaultdict(list)
    for m in matches:
        if m.save:
            claims[m.save.index].append(m)
    for group in claims.values():
        if len(group) == 1:
            continue
        sp = group[0].save
        winners, how = [m for m in group if same_club(m.club, sp.club)], "le club"
        if not winners:
            winners, how = [m for m in group if close_value(m.value, sp.value)], "la valeur marchande"
        for m in group:
            if len(winners) == 1 and m is winners[0]:
                m.detail = f"conflit départagé par {how}"
                continue
            m.status, m.save = "CONFLIT", None
            m.detail = f"ligne de la sauvegarde ({sp.name}, {sp.club}) réclamée par plusieurs joueurs"
    return matches


def planned_changes(ws, headers: dict, m: Match) -> dict[str, tuple]:
    """{colonne: (avant, après)} pour un joueur retrouvé (seulement les cellules qui changent)."""
    sp = m.save
    def g(h):
        return ws.cell(m.row, headers[h]).value
    is_gk = m.poste.split("/")[0].strip() == "GK"
    changes = {}
    for a in (GK_SET if is_gk else FIELD_SET):
        new = to_base_scale(sp.attrs[a]) if a in sp.attrs else None
        if new is not None and g(a) != new:
            changes[a] = (g(a), new)
    if sp.left is not None and sp.right is not None:
        foot = strong_foot(sp.left, sp.right)
        if foot and g(FOOT_COL) != foot:
            changes[FOOT_COL] = (g(FOOT_COL), foot)
        wf = weak_foot(sp.left, sp.right)
        if g(WEAK_COL) != wf:
            changes[WEAK_COL] = (g(WEAK_COL), wf)
    if g(HEIGHT_COL) is None and sp.height:
        changes[HEIGHT_COL] = (None, sp.height)
    return changes


def run(ws, save: list[SavePlayer], write: bool = False) -> tuple[list[Match], dict[int, dict]]:
    headers = {str(c.value).strip(): c.column for c in ws[1] if c.value is not None}
    missing = [h for h in ["ID", "Prénom", "Nom", "Âge", "Poste", "Club", FOOT_COL, WEAK_COL, HEIGHT_COL,
                           *ATTRIBUTES] if h not in headers]
    if missing:
        raise SystemExit(f"Colonnes introuvables dans '{SHEET}' : {missing}")
    matches = match_players(ws, headers, save)
    plans = {m.row: planned_changes(ws, headers, m) for m in matches if m.save}
    if write:
        for row, changes in plans.items():
            for col, (_, new) in changes.items():
                ws.cell(row, headers[col]).value = new
    return matches, plans


def write_report(path: Path, matches: list[Match], plans: dict[int, dict]):
    attr_set = set(ATTRIBUTES)
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["ID", "joueur", "club", "poste", "statut", "nom_sauvegarde", "club_sauvegarde",
                    "attributs_changés", "écart_moyen_attributs", "pieds", "weak_foot", "taille_fm", "détail"])
        for m in matches:
            if m.status == "ABSENT":
                continue
            ch = plans.get(m.row, {})
            diffs = [new - old for a, (old, new) in ch.items() if a in attr_set and isinstance(old, int)]
            def fmt(c, ch=ch):
                return f"{ch[c][0]} -> {ch[c][1]}" if c in ch else ""
            w.writerow([m.pid, m.name, m.club, m.poste, m.status, m.save.name if m.save else "",
                        m.save.club if m.save else "", sum(1 for a in ch if a in attr_set),
                        round(sum(diffs) / len(diffs), 2) if diffs else "", fmt(FOOT_COL), fmt(WEAK_COL),
                        fmt(HEIGHT_COL), m.detail])


def summary(matches: list[Match], plans: dict[int, dict]) -> list[str]:
    status = Counter(m.status for m in matches)
    cols = Counter(c for ch in plans.values() for c in ch)
    attr_cells = sum(n for c, n in cols.items() if c in ATTRIBUTES)
    empty_before = sum(1 for ch in plans.values() if ch and all(old is None for a, (old, _) in ch.items()
                                                                    if a in ATTRIBUTES) and any(a in ATTRIBUTES for a in ch))
    modified = sum(1 for ch in plans.values() if ch)
    return [
        "Correspondance : " + ", ".join(f"{k} {v}" for k, v in sorted(status.items())),
        f"Joueurs modifiés : {modified} (dont {empty_before} qui n'avaient aucun attribut)",
        (f"Cellules d'attributs changées : {attr_cells} ; Pieds : {cols[FOOT_COL]} ; "
         f"Weak foot : {cols[WEAK_COL]} ; Taille FM remplie : {cols[HEIGHT_COL]}"),
    ]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    ap.add_argument("--excel", type=Path, default=DEFAULT_EXCEL)
    ap.add_argument("--write", action="store_true", help="écrit dans le classeur (sinon essai à blanc)")
    args = ap.parse_args()

    import openpyxl
    save = read_save(args.source)
    wb = openpyxl.load_workbook(args.excel)
    ws = wb[SHEET]
    matches, plans = run(ws, save, write=args.write)
    report = args.excel.parent / "fmsave_import_report.csv"
    write_report(report, matches, plans)
    print(f"Sauvegarde : {len(save)} lignes. Classeur : {len(matches)} joueurs.")
    for line in summary(matches, plans):
        print(line)
    print(f"Rapport : {report}")
    if not args.write:
        print("Essai à blanc : classeur non modifié (--write pour écrire).")
        return
    backup = args.excel.parent / f"{args.excel.stem}_backup_{datetime.now():%Y%m%d_%H%M%S}{args.excel.suffix}"  # noqa: DTZ005
    shutil.copy2(args.excel, backup)
    try:
        wb.save(args.excel)
    except PermissionError:
        sys.exit(f"Impossible d'écrire {args.excel.name} : ferme-le dans Excel puis relance.")
    print(f"Classeur écrit (sauvegarde : {backup.name}). Étapes suivantes : compute_moyenne_fm.py, "
          "generate_national_teams.py")


if __name__ == "__main__":
    main()

"""
Découverte de NOUVEAUX joueurs sur fminside.net (FM26) pour enrichir data/joueurs.xlsx.

Ticket .scratch/donnees-nouveaux-joueurs/issues/01. Décisions du propriétaire (22/11/2026) :
- clubs cibles : ceux des championnats simulables (hors "Autres clubs") ;
- quota égal par club, les mieux notés FM d'abord, effectif plafonné à MAX_SQUAD ;
- TARGET_TOTAL nouveaux joueurs au total.

Principe
--------
1. Pour chaque club cible, interroge le filtre "club" de la base joueurs fminside et garde les
   lignes dont le club correspond (club_similarity >= CLUB_MATCH).
2. Écarte les joueurs déjà dans la base : même URL FMInside, nom proche d'un joueur du même club,
   ou même nom qu'un joueur de la base avec au plus 1 an d'écart d'âge.
3. Sélection à tour de rôle : à chaque tour, chaque club non plafonné reçoit son meilleur
   candidat restant (note FM du badge fminside), les clubs aux plus petits effectifs d'abord.
4. Télécharge la fiche de chaque joueur retenu et ajoute une ligne : ID, Prénom, Nom, Nationalité,
   Âge (âge FM + 1, la base FM26 a un an de retard sur le classeur), Poste, Club, Championnat,
   attributs, URL, postes naturels, taille, weak foot (et preferred moves avec --cookie).
   Rien n'est inventé : Moyenne joueur, Valeur marchande, Note transfermrkt, Statut, Catégorie,
   Pieds restent vides. La "Moyenne FM" se calcule ensuite avec scripts/compute_moyenne_fm.py.

Fichiers (dans le dossier de joueurs.xlsx)
------------------------------------------
- fminside_new_players_report.csv : chaque candidat examiné et la décision prise
- fminside_new_clubs_report.csv   : chaque club cible (nom fminside, lignes trouvées, ajoutés)
- fminside_clubs.csv              : corrections manuelles, colonnes  Club;fminside
                                    (nom du club tel que fminside l'écrit)
- .fminside_cache.json            : cache partagé avec scrape_fminside_attributes.py

Exemples
--------
    # essai sur un club, sans télécharger les fiches ni écrire l'Excel
    uv run python scripts/fminside_new_players.py --clubs "Stade Rennais" --dry-run

    # toute la sélection, sans écrire (rapport seulement)
    uv run python scripts/fminside_new_players.py --dry-run

    # collecte réelle (environ 2 400 requêtes, ~1 h à 1 s d'intervalle)
    uv run python scripts/fminside_new_players.py

Puis : uv run python scripts/compute_moyenne_fm.py. Fermer joueurs.xlsx dans Excel avant.
"""
from __future__ import annotations

import argparse
import copy
import csv
import json
import re
import shutil
import signal
import sys
from collections import Counter, defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from scrape_fminside_attributes import (
    ATTRIBUTES,
    NATIONALITIES,
    SHEET,
    TABLE_NAME,
    URL_COL,
    Candidate,
    ExcelPlayer,
    FMInside,
    ProfileUnreadable,
    club_similarity,
    ensure_columns,
    load_players,
    name_similarity,
    norm,
    write_extras,
)

from ligue1sim.clubs import EXCLUDED_CHAMPIONNATS

# --- Réglages (décisions du propriétaire du 22/11/2026, voir le ticket) ----------------------
TARGET_TOTAL = 2000   # nouveaux joueurs au total
MAX_SQUAD = 40        # effectif maximal d'un club après ajout
CLUB_MATCH = 0.8      # club_similarity mini pour qu'une ligne fminside soit "du club" (= scoring)
SAME_CLUB_NAME = 0.80  # similarité de nom à partir de laquelle un candidat est déjà dans le club
AGE_OFFSET = 1        # base FM26 = saison 2025, le classeur a environ un an d'avance

# Postes FM -> postes du classeur (inverse de scrape_fminside_attributes.POSITIONS)
FM_TO_POSTE = {
    "GK": "GK", "DC": "DC", "DL": "LB", "WBL": "LB", "DR": "RB", "WBR": "RB", "DM": "MDC",
    "MC": "MC", "AMC": "MOC", "AML": "AG", "ML": "AG", "AMR": "AD", "MR": "AD", "ST": "BU",
}
# Ordre utilisé quand seule la liste (non ordonnée) des postes de la recherche est connue
FM_ORDER = ["GK", "DC", "DR", "DL", "WBR", "WBL", "DM", "MC", "MR", "ML", "AMC", "AMR", "AML", "ST"]

_REVERSE_NAT = {norm(alias): fr for fr, aliases in NATIONALITIES.items() for alias in aliases}


# --- Conversions ------------------------------------------------------------------------------
def expand_fm_position(tok: str) -> list[str]:
    """"AMC" -> ["AMC"] ; "AM (RL)" -> ["AMR", "AML"] ; "D (C)" -> ["DC"] ; "ST (C)" -> ["ST"]."""
    t = str(tok).strip().upper()
    m = re.fullmatch(r"([A-Z]+)\s*\(([RLC]+)\)", t)
    if not m:
        return [re.sub(r"[^A-Z]", "", t)]
    base, sides = m.groups()
    if base in ("GK", "ST", "DM"):
        return [base]
    return [base + s for s in sides]


def fm_poste(natural: list[str] | None, fallback: set[str] | None = None) -> str | None:
    """Postes FM (naturels en priorité, dans l'ordre de la fiche) -> "BU / AG"."""
    toks = list(natural or [])
    if not toks:
        toks = sorted(fallback or [], key=lambda p: FM_ORDER.index(p) if p in FM_ORDER else 99)
    out: list[str] = []
    for tok in toks:
        for p in expand_fm_position(tok):
            poste = FM_TO_POSTE.get(p)
            if poste and poste not in out:
                out.append(poste)
    return " / ".join(out) or None


def fr_nationality(fm_nat: str) -> tuple[str, bool]:
    """Libellé fminside (EN) -> libellé du classeur (FR). (libellé, connu ?)."""
    fr = _REVERSE_NAT.get(norm(fm_nat))
    return (fr, True) if fr else ((fm_nat or "").strip(), False)


def split_name(display: str) -> tuple[str, str | None]:
    """Nom affiché FM -> (Prénom, Nom). Nom d'usage seul ("Vitinha") : Prénom seul, Nom vide,
    comme les 249 lignes de ce type déjà dans le classeur."""
    parts = (display or "").split()
    if len(parts) <= 1:
        return (parts[0] if parts else ""), None
    return parts[0], " ".join(parts[1:])


def pool_order(cands: list[Candidate]) -> list[Candidate]:
    """Meilleure note FM d'abord ; ex aequo départagés par nom puis URL (déterministe)."""
    return sorted(cands, key=lambda c: (-(c.ability if c.ability is not None else -1), norm(c.name), c.url))


# --- Base existante ---------------------------------------------------------------------------
@dataclass
class TargetClub:
    name: str
    championnat: str
    size: int
    fm_name: str = ""


@dataclass
class BaseIndex:
    urls: set[str] = field(default_factory=set)
    by_club: dict[str, list[ExcelPlayer]] = field(default_factory=lambda: defaultdict(list))
    by_name: dict[str, list[ExcelPlayer]] = field(default_factory=lambda: defaultdict(list))

    def add(self, p: ExcelPlayer, url: str | None):
        if url:
            self.urls.add(url)
        self.by_club[p.club].append(p)
        full = norm(f"{p.first} {p.last}")
        if full:
            self.by_name[full].append(p)

    def known_reason(self, club: str, c: Candidate) -> str | None:
        """Raison pour laquelle le candidat est (probablement) déjà dans la base, sinon None."""
        if c.url in self.urls:
            return "déjà dans la base (URL)"
        for p in self.by_club.get(club, []):
            score, _ = name_similarity(p, c)
            if score >= SAME_CLUB_NAME:
                return f"nom proche d'un joueur du club : ID {p.id} ({score:.2f})"
        fm_age = c.age + AGE_OFFSET if c.age is not None else None
        for n in {norm(c.name), norm(c.full_name)} - {""}:
            for p in self.by_name.get(n, []):
                if p.age is None or fm_age is None or abs(p.age - fm_age) <= 1:
                    return f"même nom dans la base : ID {p.id} ({p.club})"
        return None


def read_base(ws, headers) -> tuple[BaseIndex, dict[str, TargetClub], int]:
    """Index des joueurs existants, clubs cibles, prochain ID libre."""
    _, players = load_players(ws)
    index = BaseIndex()
    sizes: Counter = Counter()
    champ: dict[str, str] = {}
    for p in players:
        index.add(p, ws.cell(p.row, headers[URL_COL]).value)
        ch = ws.cell(p.row, headers["Championnat"]).value
        if ch not in EXCLUDED_CHAMPIONNATS:
            sizes[p.club] += 1
            champ.setdefault(p.club, ch)
    clubs = {name: TargetClub(name, champ[name], n) for name, n in sorted(sizes.items())}
    next_id = max((p.id for p in players), default=0) + 1
    return index, clubs, next_id


def fm_names_from_cache(cache: dict, url_to_club: dict[str, str]) -> dict[str, str]:
    """Nom fminside de chaque club Simulafoot, déduit des recherches déjà en cache : le nom de club
    le plus fréquent sur les fiches déjà reliées aux joueurs de ce club."""
    fm_club = {}
    for rows in cache.get("search", {}).values():
        for d in rows:
            if d.get("url") and d.get("club"):
                fm_club.setdefault(d["url"], d["club"])
    votes: dict[str, Counter] = defaultdict(Counter)
    for url, club in url_to_club.items():
        if url in fm_club:
            votes[club][fm_club[url]] += 1
    return {club: max(sorted(v), key=v.get) for club, v in votes.items()}


def read_club_overrides(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8-sig") as f:
        return {(r.get("Club") or "").strip(): (r.get("fminside") or "").strip()
                for r in csv.DictReader(f, delimiter=";") if (r.get("Club") or "").strip()}


# --- Recherche par club -----------------------------------------------------------------------
class FilterIgnored(RuntimeError):
    """Le site a renvoyé des joueurs de nombreux clubs : le filtre club n'a pas été appliqué."""


def club_pool(api, club: TargetClub) -> tuple[str, list[Candidate], int, str]:
    """(statut, candidats du club, lignes renvoyées, détail)."""
    query = club.fm_name or club.name
    rows = api.search(club=query)
    names = {club.name, query}
    match = [c for c in rows if any(club_similarity(n, c.club) >= CLUB_MATCH for n in names)]
    if match:
        return "OK", match, len(rows), query
    if not rows:
        return "INTROUVABLE", [], 0, f"aucune ligne pour {query!r}"
    seen = Counter(c.club for c in rows)
    if len(seen) > 3:
        raise FilterIgnored(f"recherche {query!r} : {len(rows)} lignes de {len(seen)} clubs différents, "
                            "le filtre club de fminside n'a pas été appliqué (format du site changé ?). "
                            "Rien n'est écrit.")
    return "CLUB_DIFFÉRENT", [], len(rows), ("clubs renvoyés : " + ", ".join(sorted(seen))
                                            + " (à mettre dans fminside_clubs.csv si c'est le bon)")


def purge_club_searches(api):
    """Retire du cache les recherches par club : si le filtre club a été ignoré, elles contiennent
    des réponses non filtrées qu'une relance relirait. Le reste du cache (fiches) est gardé."""
    searches = getattr(api, "cache", {}).get("search", {})
    for key in [k for k in searches if len(json.loads(k)) > 4]:
        del searches[key]
    api.save_cache()


# --- Sélection --------------------------------------------------------------------------------
def select(pools: dict[str, list[Candidate]], sizes: dict[str, int], max_squad: int, target: int,
           accept: Callable[[str, Candidate], bool]) -> list[tuple[str, Candidate]]:
    """Sélection à tour de rôle. `pools` : candidats de chaque club, déjà triés (pool_order).
    À chaque tour, chaque club non plafonné et non épuisé (petits effectifs d'abord, puis nom)
    reçoit son meilleur candidat restant ; un candidat refusé par `accept` (fiche illisible,
    poste inconnu) laisse la place au suivant du même club, dans le même tour."""
    idx = {c: 0 for c in pools}
    cur = {c: sizes.get(c, 0) for c in pools}
    chosen: list[tuple[str, Candidate]] = []
    while len(chosen) < target:
        active = [c for c in pools if idx[c] < len(pools[c]) and cur[c] < max_squad]
        if not active:
            break
        for club in sorted(active, key=lambda k: (cur[k], k)):
            if len(chosen) >= target:
                break
            while idx[club] < len(pools[club]):
                cand = pools[club][idx[club]]
                idx[club] += 1
                if accept(club, cand):
                    chosen.append((club, cand))
                    cur[club] += 1
                    break
    return chosen


# --- Écriture ---------------------------------------------------------------------------------
def append_row(ws, headers: dict, values: dict) -> int:
    """Ajoute une ligne après la dernière (style recopié de la ligne du dessus) et étend le
    tableau Excel. Retourne le numéro de ligne."""
    r = ws.max_row + 1
    for col in range(1, ws.max_column + 1):
        ws.cell(r, col)._style = copy.copy(ws.cell(r - 1, col)._style)
    for name, v in values.items():
        ws.cell(r, headers[name]).value = v
    if TABLE_NAME in ws.tables:
        t = ws.tables[TABLE_NAME]
        start, end = t.ref.split(":")
        t.ref = f"{start}:{re.sub(r'[0-9]+', '', end)}{r}"
        if t.autoFilter:
            t.autoFilter.ref = t.ref
    return r


def row_values(pid: int, club: TargetClub, c: Candidate, attrs: dict, extras: dict | None) -> dict:
    first, last = split_name(c.name)
    nat, _ = fr_nationality(c.nat)
    values = {
        "ID": pid, "Prénom": first, "Nom": last, "Nationalité": nat,
        "Âge": c.age + AGE_OFFSET if c.age is not None else None,
        "Poste": fm_poste((extras or {}).get("natural"), c.positions),
        "Club": club.name, "Championnat": club.championnat, URL_COL: c.url,
    }
    values.update({a: attrs.get(a) for a in ATTRIBUTES})
    return values


# --- Orchestration ----------------------------------------------------------------------------
@dataclass
class Outcome:
    added: list[tuple[int, str, Candidate]] = field(default_factory=list)  # (ligne, club, candidat)
    players_report: list[list] = field(default_factory=list)
    clubs_report: list[list] = field(default_factory=list)
    unknown_nat: Counter = field(default_factory=Counter)
    error: str = ""  # erreur bloquante (Cloudflare, cookie...) : la collecte s'est arrêtée là


def discover(ws, api, target: int = TARGET_TOTAL, max_squad: int = MAX_SQUAD, dry_run: bool = False,
             only_clubs: set[str] | None = None, club_overrides: dict[str, str] | None = None,
             stop: Callable[[], bool] = lambda: False) -> Outcome:
    headers = {str(c.value).strip(): c.column for c in ws[1] if c.value is not None}
    headers = ensure_columns(ws, headers)
    index, clubs, next_id = read_base(ws, headers)
    if only_clubs:
        missing = only_clubs - set(clubs)
        if missing:
            raise SystemExit(f"Clubs inconnus (ou hors championnats simulables) : {sorted(missing)}")
        clubs = {k: v for k, v in clubs.items() if k in only_clubs}
    url_to_club = {ws.cell(p.row, headers[URL_COL]).value: p.club
                   for ps in index.by_club.values() for p in ps if ws.cell(p.row, headers[URL_COL]).value}
    cached = fm_names_from_cache(getattr(api, "cache", {}), url_to_club)
    for name, tc in clubs.items():
        tc.fm_name = (club_overrides or {}).get(name) or cached.get(name, "")

    out = Outcome()
    pools: dict[str, list[Candidate]] = {}
    club_stats: dict[str, list] = {}
    for name, tc in clubs.items():
        if stop():
            break
        try:
            status, cands, n_rows, detail = club_pool(api, tc)
        except FilterIgnored:
            purge_club_searches(api)
            raise
        fresh = []
        for c in pool_order(cands):
            why = index.known_reason(name, c)
            if why:
                out.players_report.append(["DÉJÀ_PRÉSENT", name, c.name, c.club, c.age, c.ability, c.url, why])
            else:
                fresh.append(c)
        pools[name] = fresh
        club_stats[name] = [name, tc.championnat, tc.size, status, detail, n_rows, len(cands), len(fresh)]
        print(f"{name} ({tc.championnat}) : {status}, {len(cands)} joueurs du club, {len(fresh)} nouveaux")
        api.save_cache()

    ids = iter(range(next_id, next_id + 10**6))

    def accept(club: str, c: Candidate) -> bool:
        if stop():
            return False
        tc = clubs[club]
        if c.url in index.urls:  # même fiche dans la réserve de deux clubs : une seule ligne
            out.players_report.append(["REFUSÉ", club, c.name, c.club, c.age, c.ability, c.url,
                                       "fiche déjà retenue pour un autre club"])
            return False
        if dry_run:
            if not fm_poste(None, c.positions):
                out.players_report.append(["REFUSÉ", club, c.name, c.club, c.age, c.ability, c.url, "poste inconnu"])
                return False
            out.players_report.append(["PRÉVU", club, c.name, c.club, c.age, c.ability, c.url, ""])
            out.added.append((0, club, c))
            index.urls.add(c.url)
            return True
        try:
            attrs = api.attributes(c.url)
            extras = api.extras(c.url)
        except ProfileUnreadable as e:  # fiche sans attributs : on passe au suivant du club
            out.players_report.append(["REFUSÉ", club, c.name, c.club, c.age, c.ability, c.url, str(e)])
            return False
        except RuntimeError:  # Cloudflare, cookie expiré... : bloquant, comme le script de base
            raise
        except Exception as e:  # noqa: BLE001 -- fiche illisible : on passe au suivant du club
            out.players_report.append(["REFUSÉ", club, c.name, c.club, c.age, c.ability, c.url, repr(e)])
            return False
        if not fm_poste((extras or {}).get("natural"), c.positions):
            out.players_report.append(["REFUSÉ", club, c.name, c.club, c.age, c.ability, c.url, "poste inconnu"])
            return False
        values = row_values(next(ids), tc, c, attrs, extras)
        index.urls.add(c.url)
        r = append_row(ws, headers, values)
        write_extras(ws, r, headers, extras)
        nat, known = fr_nationality(c.nat)
        if not known:
            out.unknown_nat[nat] += 1
        out.added.append((r, club, c))
        out.players_report.append(["AJOUTÉ", club, c.name, c.club, c.age, c.ability, c.url, f"ID {values['ID']}"])
        if len(out.added) % 25 == 0:
            api.save_cache()
            print(f"  {len(out.added)} joueurs ajoutés")
        return True

    sizes = {k: v.size for k, v in clubs.items()}
    try:
        select(pools, sizes, max_squad, target, accept)
    except RuntimeError as e:  # les lignes déjà ajoutées restent, le cache permet de reprendre
        out.error = str(e)
    finally:
        api.save_cache()
    added_by_club = Counter(club for _, club, _ in out.added)
    out.clubs_report = [s + [added_by_club.get(s[0], 0)] for s in club_stats.values()]
    return out


def write_reports(folder: Path, out: Outcome):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")  # noqa: DTZ005 -- horodatage local du rapport
    with (folder / "fminside_new_players_report.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["date", "statut", "club", "fm_nom", "fm_club", "fm_age", "note_fm", "url", "raison"])
        w.writerows([now] + row for row in out.players_report)
    with (folder / "fminside_new_clubs_report.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["date", "club", "championnat", "effectif_avant", "statut", "détail", "lignes_renvoyées",
                    "joueurs_du_club", "nouveaux_candidats", "ajoutés"])
        w.writerows([now] + row for row in out.clubs_report)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    default_excel = Path(__file__).resolve().parent.parent / "data" / "joueurs.xlsx"
    ap.add_argument("--excel", type=Path, default=default_excel)
    ap.add_argument("--target", type=int, default=TARGET_TOTAL, help=f"nouveaux joueurs (défaut {TARGET_TOTAL})")
    ap.add_argument("--max-squad", type=int, default=MAX_SQUAD, help=f"effectif maximal (défaut {MAX_SQUAD})")
    ap.add_argument("--clubs", default="", help="clubs Simulafoot à traiter, séparés par des virgules")
    ap.add_argument("--delay", type=float, default=1.0, help="secondes entre 2 requêtes (défaut 1)")
    ap.add_argument("--dry-run", action="store_true", help="recherches seulement : ni fiches, ni écriture")
    ap.add_argument("--no-cache", action="store_true", help="ignore le cache existant")
    ap.add_argument("--cookie", default="", help="cookie de session fminside (preferred moves), voir "
                    "scrape_fminside_attributes.py")
    args = ap.parse_args()

    import openpyxl
    xlsx: Path = args.excel
    folder = xlsx.parent
    api = FMInside(args.delay, folder / ".fminside_cache.json", use_cache=not args.no_cache, cookie=args.cookie)
    wb = openpyxl.load_workbook(xlsx)
    ws = wb[SHEET]
    flag = {"stop": False}
    signal.signal(signal.SIGINT, lambda *_: flag.update(stop=True) or print("\nArrêt demandé, on sauvegarde…"))
    only = {c.strip() for c in args.clubs.split(",") if c.strip()} or None
    try:
        out = discover(ws, api, args.target, args.max_squad, args.dry_run, only,
                       read_club_overrides(folder / "fminside_clubs.csv"), stop=lambda: flag["stop"])
    except FilterIgnored as e:  # cache des recherches par club déjà purgé ; rien d'écrit
        sys.exit(f"ARRÊT : {e}")
    except RuntimeError as e:  # Cloudflare pendant les recherches : rien d'écrit
        api.save_cache()
        sys.exit(f"ARRÊT : {e}")
    write_reports(folder, out)
    if out.error:
        print(f"ERREUR bloquante : {out.error}\nLes joueurs déjà ajoutés sont enregistrés ; relancer "
              "plus tard reprend grâce au cache et ne réajoute pas les mêmes (URL déjà dans la base).")
    counts = Counter(row[0] for row in out.players_report)
    print("\nBilan :", ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))
    if out.unknown_nat:
        print("Nationalités sans libellé français (gardées en anglais) :",
              ", ".join(f"{k} ({v})" for k, v in out.unknown_nat.most_common()))
    if args.dry_run:
        print(f"Dry-run : {len(out.added)} joueurs seraient ajoutés. Excel non modifié.")
        return
    if not out.added:
        print("Rien à écrire.")
        return
    n = sum(1 for r in range(2, ws.max_row + 1) if ws.cell(r, 1).value is not None)
    backup = folder / f"{xlsx.stem}_backup_{datetime.now():%Y%m%d_%H%M%S}{xlsx.suffix}"  # noqa: DTZ005
    shutil.copy2(xlsx, backup)
    try:
        wb.save(xlsx)
    except PermissionError:
        sys.exit(f"Impossible d'écrire {xlsx.name} : ferme-le dans Excel puis relance (le cache évite de tout refaire).")
    print(f"{len(out.added)} joueurs ajoutés, {n} lignes dans {xlsx.name} (sauvegarde : {backup.name}).")
    print("Étape suivante : uv run python scripts/compute_moyenne_fm.py")


if __name__ == "__main__":
    main()

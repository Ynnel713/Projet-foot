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

    # mode « top N » (ticket 05) : les 4 000 premiers joueurs de fminside, dans l'ordre par défaut
    # du site ; rangés dans leur club du classeur, ou dans un club créé en "Autres clubs" (sous son
    # nom FM). Même plafond de 40, mêmes exclusions. Rapports fminside_top_*_report.csv : chaque
    # club "Autres clubs" touché y est dit complet (jouable en Compétition Perso, voir
    # clubs.is_playable_squad) ou incomplet (sélections nationales seulement).
    uv run python scripts/fminside_new_players.py --top 4000 --dry-run

    # extraction seule, vers un Excel séparé (data/fminside_top4000.xlsx) : joueurs.xlsx intact,
    # la fusion se fait ensuite. Essai rapide d'abord sur 50 joueurs.
    uv run python scripts/fminside_new_players.py --top 50 --extract-only
    uv run python scripts/fminside_new_players.py --top 4000 --extract-only
    uv run python scripts/fminside_new_players.py --top 4000

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
    norm_club,
    write_extras,
)

from ligue1sim.clubs import EXCLUDED_CHAMPIONNATS, is_playable_squad
from ligue1sim.players import position_group

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


class RowWriter:
    """Ajout d'un candidat retenu : contrôle de doublon d'URL, fiche, poste, écriture de la ligne
    (ou simple prévision en dry-run). Commun aux modes « par club » et « top N »."""

    def __init__(self, ws, headers: dict, api, index: BaseIndex, next_id: int, out: Outcome, dry_run: bool):
        self.ws, self.headers, self.api, self.index, self.out, self.dry_run = ws, headers, api, index, out, dry_run
        self.ids = iter(range(next_id, next_id + 10**6))

    def report(self, status: str, club: str, c: Candidate, why: str = ""):
        self.out.players_report.append([status, club, c.name, c.club, c.age, c.ability, c.url, why])

    def add(self, tc: TargetClub, c: Candidate) -> bool:
        club, out = tc.name, self.out
        if c.url in self.index.urls:  # même fiche dans la réserve de deux clubs : une seule ligne
            self.report("REFUSÉ", club, c, "fiche déjà retenue pour un autre club")
            return False
        if self.dry_run:
            if not fm_poste(None, c.positions):
                self.report("REFUSÉ", club, c, "poste inconnu")
                return False
            self.report("PRÉVU", club, c)
            out.added.append((0, club, c))
            self.index.urls.add(c.url)
            return True
        try:
            attrs = self.api.attributes(c.url)
            extras = self.api.extras(c.url)
        except ProfileUnreadable as e:  # fiche sans attributs : on passe au suivant
            self.report("REFUSÉ", club, c, str(e))
            return False
        except RuntimeError:  # Cloudflare, cookie expiré... : bloquant, comme le script de base
            raise
        except Exception as e:  # noqa: BLE001 -- fiche illisible : on passe au suivant
            self.report("REFUSÉ", club, c, repr(e))
            return False
        if not fm_poste((extras or {}).get("natural"), c.positions):
            self.report("REFUSÉ", club, c, "poste inconnu")
            return False
        values = row_values(next(self.ids), tc, c, attrs, extras)
        self.index.urls.add(c.url)
        r = append_row(self.ws, self.headers, values)
        write_extras(self.ws, r, self.headers, extras)
        nat, known = fr_nationality(c.nat)
        if not known:
            out.unknown_nat[nat] += 1
        out.added.append((r, club, c))
        self.report("AJOUTÉ", club, c, f"ID {values['ID']}")
        if len(out.added) % 25 == 0:
            self.api.save_cache()
            print(f"  {len(out.added)} joueurs ajoutés")
        return True


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

    writer = RowWriter(ws, headers, api, index, next_id, out, dry_run)

    def accept(club: str, c: Candidate) -> bool:
        return not stop() and writer.add(clubs[club], c)

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


# --- Mode « top N » (ticket donnees-nouveaux-joueurs/05) -------------------------------------
OTHER_CLUBS = "Autres clubs"
FREE_AGENTS = "Sans club"


def read_all_clubs(ws, headers) -> dict[str, TargetClub]:
    """Tous les clubs du classeur, Autres clubs compris. Un nom porté par deux championnats (ligne
    isolée en Autres clubs + vrai club d'un championnat) désigne le club du championnat."""
    counts: Counter = Counter()
    for r in range(2, ws.max_row + 1):
        if ws.cell(r, headers["ID"]).value is None:
            continue
        counts[(ws.cell(r, headers["Club"]).value, ws.cell(r, headers["Championnat"]).value)] += 1
    total: Counter = Counter()
    for (name, _), n in counts.items():
        total[name] += n
    clubs: dict[str, TargetClub] = {}
    for (name, champ), _ in sorted(counts.items(), key=lambda kv: (kv[0][1] == OTHER_CLUBS, -kv[1], kv[0])):
        if name and name not in clubs:  # effectif compté sur toutes les lignes du nom (plafond)
            clubs[name] = TargetClub(name, champ, total[name])
    return clubs


class ClubResolver:
    """Club fminside -> club du classeur. Ordre : nom identique (normalisé), nom fminside appris du
    cache, puis meilleure club_similarity >= CLUB_MATCH ; à égalité, club d'un championnat avant
    Autres clubs, puis plus grand effectif. Aucun -> None (nouveau club en Autres clubs).
    Seuls les clubs déjà dans le classeur sont comparés de façon approchée (leurs noms diffèrent de
    ceux de FM) ; un club créé pendant l'exécution porte son nom FM exact et n'est retrouvé que
    par lui (`memo`), pour ne pas fusionner deux clubs FM aux noms voisins (Al Ahli / Al Ahly).
    """

    def __init__(self, clubs: dict[str, TargetClub], fm_names: dict[str, str] | None = None):
        self.clubs = clubs
        self.base_names = sorted(clubs)  # instantané : les clubs créés ensuite n'y entrent pas
        self.by_norm: dict[str, str] = {}
        for name in sorted(clubs, key=self._rank):
            self.by_norm.setdefault(norm_club(name), name)
        for name, fm in sorted((fm_names or {}).items()):
            if name in clubs:
                self.by_norm.setdefault(norm_club(fm), name)
        self.memo: dict[str, str | None] = {}

    def _rank(self, name: str):
        tc = self.clubs[name]
        return (tc.championnat == OTHER_CLUBS, -tc.size, name)

    def resolve(self, fm_club: str) -> str | None:
        if fm_club in self.memo:
            return self.memo[fm_club]
        hit = self.by_norm.get(norm_club(fm_club))
        if hit is None:
            scored = [(club_similarity(fm_club, name), name) for name in self.base_names]
            best = max((sc for sc, _ in scored), default=0.0)
            if best >= CLUB_MATCH:
                hit = min((name for sc, name in scored if sc == best), key=self._rank)
        self.memo[fm_club] = hit
        return hit


def squad_groups(ws, headers) -> dict[str, list[str]]:
    """Groupe (GK/DEF/MID/ATT) du poste principal de chaque joueur, par club."""
    out: dict[str, list[str]] = defaultdict(list)
    for r in range(2, ws.max_row + 1):
        if ws.cell(r, headers["ID"]).value is None:
            continue
        poste = str(ws.cell(r, headers["Poste"]).value or "").split("/")[0].strip()
        out[ws.cell(r, headers["Club"]).value].append(position_group(poste))
    return out


def discover_top(ws, api, n: int, max_squad: int = MAX_SQUAD, dry_run: bool = False,
                 stop: Callable[[], bool] = lambda: False) -> Outcome:
    """Les `n` premiers joueurs de fminside (ordre par défaut du site) absents du classeur, rangés
    dans leur club s'il existe, sinon dans un club créé en Autres clubs ; effectif plafonné."""
    headers = {str(c.value).strip(): c.column for c in ws[1] if c.value is not None}
    headers = ensure_columns(ws, headers)
    index, _, next_id = read_base(ws, headers)
    clubs = read_all_clubs(ws, headers)
    url_to_club = {ws.cell(p.row, headers[URL_COL]).value: p.club
                   for ps in index.by_club.values() for p in ps if ws.cell(p.row, headers[URL_COL]).value}
    resolver = ClubResolver(clubs, fm_names_from_cache(getattr(api, "cache", {}), url_to_club))
    before = {name: tc.championnat for name, tc in clubs.items()}
    playable_before = {name for name, groups in squad_groups(ws, headers).items()
                       if before.get(name) == OTHER_CLUBS and is_playable_squad(groups)}

    out = Outcome()
    writer = RowWriter(ws, headers, api, index, next_id, out, dry_run)
    try:
        rows = api.top(n)
        print(f"{len(rows)} lignes lues sur fminside (demandées : {n})")
        for c in rows:
            if stop():
                break
            name = resolver.resolve(c.club) if c.club else FREE_AGENTS
            if name is None:  # club inconnu du classeur : créé en Autres clubs sous son nom FM
                name = c.club.strip()
                clubs[name] = TargetClub(name, OTHER_CLUBS, 0)
                resolver.memo[c.club] = name
            tc = clubs.setdefault(name, TargetClub(name, OTHER_CLUBS, 0))
            why = index.known_reason(name, c)
            if why:
                writer.report("DÉJÀ_PRÉSENT", name, c, why)
                continue
            if tc.size >= max_squad:
                writer.report("CLUB_PLEIN", name, c, f"effectif à {tc.size}")
                continue
            if writer.add(tc, c):
                tc.size += 1
    except RuntimeError as e:  # les lignes déjà ajoutées restent, le cache permet de reprendre
        out.error = str(e)
    finally:
        api.save_cache()

    added = Counter(club for _, club, _ in out.added)
    groups = squad_groups(ws, headers)
    if dry_run:  # rien d'écrit : composition prévue = existants + postes de la recherche
        for _, club, c in out.added:
            groups[club].append(position_group(fm_poste(None, c.positions).split(" / ")[0]))
    for name in sorted(n for n, tc in clubs.items() if tc.championnat == OTHER_CLUBS and (n in added or n in playable_before)):
        if name == FREE_AGENTS:
            continue
        g = Counter(groups.get(name, []))
        status = "complet" if is_playable_squad(groups.get(name, [])) else "incomplet"
        out.clubs_report.append([name, OTHER_CLUBS, clubs[name].size - added.get(name, 0), status,
                                 "nouveau club" if name not in before else "", g["GK"], g["DEF"], g["MID"],
                                 g["ATT"], added.get(name, 0)])
    return out


# --- Extraction seule (ticket 05, option B du propriétaire du 23/11/2026) ---------------------
EXTRACT_SHEET = "Top fminside"
EXTRACT_COLUMNS = (["rang", "statut_fiche", "url", "nom", "nom_complet", "club_fminside", "nationalite_fm",
                    "nationalite_fr", "age_fm", "postes_liste", "postes_naturels", "poste_classeur", "note_fm",
                    "taille_cm", "weak_foot", "preferred_moves"] + ATTRIBUTES)


def extract_row(rank: int, c: Candidate, attrs: dict | None, extras: dict | None, status: str) -> list:
    """Une ligne de l'Excel d'extraction : la liste fminside + la fiche, sans rien décider."""
    ex = extras or {}
    nat_fr, known = fr_nationality(c.nat)
    moves = "" if ex.get("locked", True) else (" ; ".join(ex.get("moves") or []) or "(aucun)")
    return ([rank, status, c.url, c.name, c.full_name, c.club, c.nat, nat_fr if known else "", c.age,
             ", ".join(sorted(c.positions)), ", ".join(ex.get("natural") or []),
             fm_poste(ex.get("natural"), c.positions) or "", c.ability, ex.get("height"), ex.get("weak_foot"),
             moves]
            + [(attrs or {}).get(a) for a in ATTRIBUTES])


def extract_top(api, n: int, stop: Callable[[], bool] = lambda: False) -> tuple[list[list], str, int]:
    """Les `n` premiers joueurs de fminside avec leur fiche, dans l'ordre du site. Rien n'est écrit
    dans joueurs.xlsx. Une fiche illisible donne une ligne sans attributs (statut_fiche) ; une
    erreur bloquante (Cloudflare...) arrête la lecture et renvoie les lignes déjà lues + l'erreur.
    Les fiches vont dans le cache : une relance ne retélécharge que celles qui manquent.
    Renvoie (lignes, erreur, nombre de joueurs dans la liste du site)."""
    rows: list[list] = []
    listed = 0
    try:
        cands = api.top(n)
        listed = len(cands)
        print(f"{len(cands)} joueurs dans la liste (demandés : {n}). Premiers : "
              + ", ".join(f"{c.name} ({c.club})" for c in cands[:5]))
        for rank, c in enumerate(cands, 1):
            if stop():
                break
            try:
                rows.append(extract_row(rank, c, api.attributes(c.url), api.extras(c.url), "ok"))
            except ProfileUnreadable as e:
                rows.append(extract_row(rank, c, None, None, f"fiche illisible : {e}"))
            except RuntimeError:  # Cloudflare, cookie expiré... : bloquant
                raise
            except Exception as e:  # noqa: BLE001 -- fiche en 404, réponse inattendue : ligne sans attributs
                rows.append(extract_row(rank, c, None, None, f"fiche illisible : {e!r}"))
            if rank % 25 == 0:
                api.save_cache()
                print(f"  {rank}/{len(cands)} fiches lues")
    except RuntimeError as e:
        return rows, str(e), listed
    finally:
        api.save_cache()
    return rows, "", listed


def write_extract(path: Path, rows: list[list]):
    import openpyxl
    from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
    from openpyxl.utils import get_column_letter
    from openpyxl.worksheet.table import Table

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = EXTRACT_SHEET
    ws.append(EXTRACT_COLUMNS)
    for r in rows:  # caractères de contrôle refusés par Excel retirés, pour ne jamais perdre le fichier
        ws.append([ILLEGAL_CHARACTERS_RE.sub("", v) if isinstance(v, str) else v for v in r])
    ws.freeze_panes = "A2"
    if rows:
        ws.add_table(Table(displayName="TopFminside",
                           ref=f"A1:{get_column_letter(len(EXTRACT_COLUMNS))}{len(rows) + 1}"))
    wb.save(path)


CLUBS_HEADER = ["club", "championnat", "effectif_avant", "statut", "détail", "lignes_renvoyées",
                "joueurs_du_club", "nouveaux_candidats", "ajoutés"]
TOP_CLUBS_HEADER = ["club", "championnat", "effectif_avant", "statut", "détail", "GK", "DEF", "MID", "ATT",
                    "ajoutés"]


def write_reports(folder: Path, out: Outcome, prefix: str = "fminside_new", clubs_header=CLUBS_HEADER):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")  # noqa: DTZ005 -- horodatage local du rapport
    with (folder / f"{prefix}_players_report.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["date", "statut", "club", "fm_nom", "fm_club", "fm_age", "note_fm", "url", "raison"])
        w.writerows([now] + row for row in out.players_report)
    with (folder / f"{prefix}_clubs_report.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["date"] + clubs_header)
        w.writerows([now] + row for row in out.clubs_report)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    default_excel = Path(__file__).resolve().parent.parent / "data" / "joueurs.xlsx"
    ap.add_argument("--excel", type=Path, default=default_excel)
    ap.add_argument("--target", type=int, default=TARGET_TOTAL, help=f"nouveaux joueurs (défaut {TARGET_TOTAL})")
    ap.add_argument("--max-squad", type=int, default=MAX_SQUAD, help=f"effectif maximal (défaut {MAX_SQUAD})")
    ap.add_argument("--clubs", default="", help="clubs Simulafoot à traiter, séparés par des virgules")
    ap.add_argument("--top", type=int, default=0,
                    help="mode « top N » : les N premiers joueurs de fminside (ordre du site), "
                    "rangés dans leur club ou en Autres clubs (ex. --top 4000)")
    ap.add_argument("--extract-only", action="store_true",
                    help="avec --top : écrit seulement un Excel séparé (liste + fiches), sans toucher "
                    "à joueurs.xlsx ; la fusion se fait ensuite")
    ap.add_argument("--out", type=Path, default=None,
                    help="fichier de l'extraction (défaut : data/fminside_top<N>.xlsx)")
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
    if args.extract_only:
        if not args.top:
            sys.exit("--extract-only s'utilise avec --top N (ex. --top 4000 --extract-only)")
        out_path = args.out or folder / f"fminside_top{args.top}.xlsx"
        stop_flag = {"stop": False}
        signal.signal(signal.SIGINT,
                      lambda *_: stop_flag.update(stop=True) or print("\nArrêt demandé, on sauvegarde…"))
        rows, error, listed = extract_top(api, args.top, stop=lambda: stop_flag["stop"])
        try:
            write_extract(out_path, rows)
        except PermissionError:
            sys.exit(f"Impossible d'écrire {out_path.name} : ferme-le dans Excel puis relance (le cache évite de "
                     "tout refaire).")
        ok = sum(1 for r in rows if r[1] == "ok")
        print(f"{len(rows)} joueurs écrits dans {out_path} ({ok} avec leurs attributs). joueurs.xlsx non modifié.")
        if error or stop_flag["stop"] or len(rows) < listed:
            print((f"ERREUR bloquante : {error}\n" if error else "")
                  + "Extraction incomplète : relance la même commande, elle reprend grâce au cache.")
        elif listed < args.top:
            print(f"La liste du site s'arrête à {listed} joueurs (pas une interruption ; non mise en cache, "
                  "une relance la relira).")
        return
    wb = openpyxl.load_workbook(xlsx)
    ws = wb[SHEET]
    flag = {"stop": False}
    signal.signal(signal.SIGINT, lambda *_: flag.update(stop=True) or print("\nArrêt demandé, on sauvegarde…"))
    only = {c.strip() for c in args.clubs.split(",") if c.strip()} or None
    try:
        if args.top:
            out = discover_top(ws, api, args.top, args.max_squad, args.dry_run, stop=lambda: flag["stop"])
        else:
            out = discover(ws, api, args.target, args.max_squad, args.dry_run, only,
                           read_club_overrides(folder / "fminside_clubs.csv"), stop=lambda: flag["stop"])
    except FilterIgnored as e:  # cache des recherches par club déjà purgé ; rien d'écrit
        sys.exit(f"ARRÊT : {e}")
    except RuntimeError as e:  # Cloudflare pendant les recherches : rien d'écrit
        api.save_cache()
        sys.exit(f"ARRÊT : {e}")
    if args.top:
        write_reports(folder, out, "fminside_top", TOP_CLUBS_HEADER)
        status = Counter(row[3] for row in out.clubs_report)
        print(f"Autres clubs touchés : {status.get('complet', 0)} complets (jouables), "
              f"{status.get('incomplet', 0)} incomplets (sélections nationales) -- détail dans "
              "fminside_top_clubs_report.csv")
    else:
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

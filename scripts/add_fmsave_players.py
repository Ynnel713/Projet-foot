"""
Ajout de nouveaux joueurs depuis un export de sauvegarde Football Manager.

Ticket .scratch/donnees-nouveaux-joueurs/issues/07a. Source : export « fmsave-list » (joueurs
hommes, triés par note FM décroissante). Le script parcourt la liste dans l'ordre, saute les
joueurs déjà présents dans data/joueurs.xlsx et ajoute les N suivants (défaut 600) avec toutes
leurs caractéristiques. Décisions du propriétaire (23/11/2026) : chacun dans son vrai club
(sinon club créé en « Autres clubs »), plafond de 40 hors « Sans club », Nationalité
« À renseigner », Valeur marchande vide ; mêmes conversions que l'import du ticket 06a.

Joueur déjà présent (à ±1 an d'âge) :
- même club (nom de club de la sauvegarde traduit par la correspondance apprise, sinon
  rapprochement de nom) et nom proche (>= 0,75), même nom de famille et même initiale, ou nom
  d'usage seul du classeur contenu dans le nom complet (« Alexsandro » / « Alexsandro Ribeiro ») ;
- ou même nom normalisé, n'importe quel club ;
- ou nom très proche (>= 0,9), n'importe quel club.
Cas douteux (même club, un seul mot de 4 lettres ou plus en commun) : ni ajouté ni assimilé,
listé « À_VÉRIFIER » dans le rapport pour décision du propriétaire.
Club de la sauvegarde -> club du classeur, dans l'ordre :
1. correspondance validée par le propriétaire (data/fmsave_club_aliases.csv, colonnes
   club_sauvegarde;club_classeur ; club_classeur = « (créer) » force la création du club, contre
   un rapprochement de nom faux : « AS Aris Thessalonikis » n'est pas Iraklis) ;
   (doublons connus sous un surnom, validés par le propriétaire : data/fmsave_known_players.csv,
   colonnes nom_sauvegarde;club_sauvegarde;id_classeur, ex. « Pote » = Pedro Gonçalves)
2. correspondance apprise sûre : club du classeur le plus fréquent parmi les joueurs présents des
   deux côtés (même nom, même âge à ±1, hors « Sans club »), au moins 2 joueurs et 60 % des cas
   (« Parthenope » -> SSC Napoli, « Real Hispalis » -> Real Betis) ;
3. rapprochement de nom (sigles à points et « Fútbol » neutralisés : « Palermo F.C. » -> Palermo FC).
Correspondance apprise retenue (voir BaseMatcher._learn_alias) : au moins 2 joueurs communs et
60 %, ou un seul joueur commun avec des noms de clubs apparentés ; et le club du classeur n'est la
cible que du club de la sauvegarde qui a le plus de joueurs communs avec lui (un transfert isolé,
« Oviedo » -> Real Sociedad, ne suffit pas). Sinon le club est créé en « Autres clubs ». Le rapport liste les
correspondances apprises (retenues et écartées, avec leurs votes) et chaque club créé avec le club
existant le plus probable, pour décision du propriétaire (revue expert du 07a, passages 1 et 2).

Usage
-----
    # essai à blanc (défaut) : rapport data/fmsave_add_report.csv, classeur intact
    uv run python scripts/add_fmsave_players.py
    # écriture (ticket 07b) + fichier des nations à remplir :
    uv run python scripts/add_fmsave_players.py --write
    uv run python scripts/compute_moyenne_fm.py
    uv run python scripts/generate_national_teams.py
Fermer joueurs.xlsx dans Excel avant.
"""
from __future__ import annotations

import argparse
import csv
import re
import shutil
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
from fminside_new_players import (
    FREE_AGENTS,
    MAX_SQUAD,
    OTHER_CLUBS,
    ClubResolver,
    TargetClub,
    append_row,
    fm_poste,
    read_all_clubs,
    split_name,
    squad_groups,
)
from import_fmsave_attributes import (
    FIELD_SET,
    GK_SET,
    SavePlayer,
    read_save,
    strong_foot,
    to_base_scale,
    weak_foot,
)
from scrape_fminside_attributes import (
    CLUB_GENERIC,
    SHEET,
    Candidate,
    ExcelPlayer,
    club_similarity,
    ensure_columns,
    load_players,
    name_similarity,
    norm,
    norm_club,
)

from ligue1sim.clubs import is_playable_squad

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = ROOT / "data" / "fmsave-list-hommes.csv"
DEFAULT_EXCEL = ROOT / "data" / "joueurs.xlsx"
DEFAULT_COUNT = 600
NATION_PLACEHOLDER = "À renseigner"
AGE_TOLERANCE = 1
SAME_CLUB_NAME = 0.75  # name_similarity donne 0,70 à tout nom d'usage seul différent : exclu
ANY_CLUB_NAME = 0.9
ALIAS_MIN_PLAYERS = 2
ALIAS_MIN_SHARE = 0.6
NATIONS_HEADER = ["Nom", "Prénom", "Poste", "Club", "Nation"]
CREATE = "(créer)"  # dans fmsave_club_aliases.csv : forcer la création du club (revue expert 07a, passage 3)


def save_postes(sp: SavePlayer) -> str | None:
    """Postes naturels de la sauvegarde ("STC AML") -> format du classeur ("BU / AG")."""
    return fm_poste([p.replace("STC", "ST") for p in sp.positions])


def fm_natural(sp: SavePlayer) -> str | None:
    """Postes naturels au format de la colonne « Postes FM naturels » ("ST, AML")."""
    return ", ".join(p.replace("STC", "ST") for p in sp.positions) or None


def tokens(name: str) -> set[str]:
    return {t for t in norm(name).split() if len(t) >= 4}


class BaseMatcher:
    """Joueurs du classeur, correspondance de clubs apprise et détection des déjà présents."""

    def __init__(self, players: list[ExcelPlayer], clubs: dict[str, TargetClub], save: list[SavePlayer],
                 manual_alias: dict[str, str] | None = None, manual_known: dict[tuple[str, str], int] | None = None):
        self.players = players
        self.by_name: dict[str, list[ExcelPlayer]] = defaultdict(list)
        self.by_club: dict[str, list[ExcelPlayer]] = defaultdict(list)
        self.by_token: dict[str, list[ExcelPlayer]] = defaultdict(list)
        for p in players:
            self.add(p)
        self.resolver = ClubResolver(clubs)
        self.votes: dict[str, Counter] = {}
        self.alias, self.alias_rejected = self._learn_alias(save)
        self.manual_alias = {k: v for k, v in (manual_alias or {}).items() if v in clubs or v == CREATE}
        self.approx: dict[str, str] = {}  # rattachements par rapprochement de nom non identique
        ids = {p.id for p in players}
        self.manual_known = {k: v for k, v in (manual_known or {}).items() if v in ids}

    def add(self, p: ExcelPlayer):
        full = norm(f"{p.first} {p.last}")
        self.by_name[full].append(p)
        self.by_club[p.club].append(p)
        for t in set(full.split()):
            if len(t) >= 3:
                self.by_token[t].append(p)

    @staticmethod
    def _age_ok(p: ExcelPlayer, sp: SavePlayer) -> bool:
        return p.age is None or sp.age is None or abs(p.age - sp.age) <= AGE_TOLERANCE

    def _learn_alias(self, save: list[SavePlayer]) -> tuple[dict[str, str], dict[str, tuple[str, int, str]]]:
        """(alias retenus, alias écartés {club sauvegarde: (club classeur, votes, raison)}).
        Vote : un joueur présent des deux côtés (même nom, ±1 an), hors « Sans club » du classeur.
        Retenu si le club du classeur le plus voté a :
        - au moins 2 votes et 60 % des votes, ou 1 seul vote unanime ET des noms de clubs
          apparentés (« 1. FC Nürnberg » / « 1.FC Nuremberg ») : un vote isolé entre noms sans
          rapport est un transfert (« Oviedo » -> Real Sociedad) ;
        - et strictement plus de votes pour ce club que tout autre club de la sauvegarde
          (« Real Sociedad », 20 votes, l'emporte sur « Oviedo », 1 vote ; à égalité, aucun des
          deux n'est retenu et chacun retombe sur le rapprochement de nom) : un club du classeur
          n'est la cible que de son unique meilleur prétendant.
        Revue expert du 07a, passages 1 et 2."""
        votes: dict[str, Counter] = defaultdict(Counter)
        for sp in save:
            if not sp.club:
                continue
            for p in self.by_name.get(norm(sp.name), []):
                if self._age_ok(p, sp) and p.club != FREE_AGENTS:
                    votes[sp.club][p.club] += 1
        self.votes = votes
        claims: dict[str, list[tuple[int, str]]] = defaultdict(list)
        for sc, c in votes.items():
            for club, n in c.items():
                claims[club].append((n, sc))
        alias, rejected = {}, {}
        for save_club, c in sorted(votes.items()):
            (club, n), = sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))[:1]
            total = sum(c.values())
            if n == 1 and not (total == 1 and clubs_related(save_club, club)):
                rejected[save_club] = (club, n, "un seul joueur commun, noms de clubs sans rapport"
                                       if total == 1 else f"1 vote sur {total}")
            elif n >= 2 and n / total < ALIAS_MIN_SHARE:
                rejected[save_club] = (club, n, f"{n} votes sur {total}")
            elif (rival := max(((m, sc) for m, sc in claims[club] if sc != save_club and m >= n), default=None)):
                rejected[save_club] = (club, n, f"« {rival[1]} » a {rival[0]} votes pour {club}")
            else:
                alias[save_club] = club
        return alias, rejected

    def club_for(self, save_club: str) -> str | None:
        """Club du classeur pour un nom de club de la sauvegarde (None : inconnu). Ordre :
        correspondance manuelle, apprise retenue, rapprochement de nom (sigles à points et
        « Fútbol » neutralisés)."""
        if not save_club:
            return FREE_AGENTS
        if save_club in self.manual_alias:
            target = self.manual_alias[save_club]
            return None if target == CREATE else target
        if save_club in self.alias:
            return self.alias[save_club]
        found = self.resolver.resolve(clean_club_name(save_club))
        if found and norm_club(clean_club_name(save_club)) != norm_club(found):
            self.approx[save_club] = found
        return found

    def best_existing(self, save_club: str) -> tuple[str, str]:
        """Meilleur club existant pour un club créé (rapport, décision du propriétaire) : votes des
        joueurs communs, sinon nom le plus proche."""
        c = self.votes.get(save_club)
        if c:
            return ", ".join(f"{k} ({n})" for k, n in c.most_common(3)), "joueurs communs"
        cleaned = clean_club_name(save_club)
        name, score = max(((n, club_similarity(cleaned, n)) for n in self.resolver.base_names),
                          key=lambda x: (x[1], x[0]), default=("", 0.0))
        return (f"{name} ({score:.2f})" if score >= 0.5 else ""), "nom proche"

    def known(self, sp: SavePlayer) -> tuple[str, str] | None:
        """(statut, raison) si le joueur est déjà dans le classeur ou douteux, sinon None.
        DÉJÀ_PRÉSENT : même club et nom proche (>= 0,75), même nom de famille et même initiale, ou
        nom d'usage seul du classeur contenu dans le nom complet ;
        même nom normalisé ailleurs ; nom très proche (>= 0,9) ailleurs.
        À_VÉRIFIER : même club et un seul mot de 4 lettres ou plus en commun (Daniel James /
        James Justin, mais aussi Ez Abde / Abde Ezzalzouli) : ni ajouté ni assimilé, listé."""
        if (sp.name, sp.club) in self.manual_known:
            return "DÉJÀ_PRÉSENT", f"doublon validé par le propriétaire : ID {self.manual_known[(sp.name, sp.club)]}"
        cand = Candidate(url="", name=sp.name, full_name="", nat="", age=sp.age, club=sp.club,
                         positions=set(), ability=None)
        club = self.club_for(sp.club)
        mates = [p for p in (self.by_club.get(club, []) if club else []) if self._age_ok(p, sp)]
        scored = sorted(((name_similarity(p, cand)[0], p.id, p) for p in mates), key=lambda x: (-x[0], x[1]))
        for score, _, p in scored:
            if (score >= SAME_CLUB_NAME or same_surname(sp.name, f"{p.first} {p.last}")
                    or usage_name_in(p, sp.name)):
                return "DÉJÀ_PRÉSENT", f"même club : ID {p.id} {p.first} {p.last}".strip()
        for p in self.by_name.get(norm(sp.name), []):
            if self._age_ok(p, sp):
                return "DÉJÀ_PRÉSENT", f"même nom : ID {p.id} ({p.club})"
        seen = set()
        for t in sorted(set(norm(sp.name).split())):
            for p in self.by_token.get(t, []) if len(t) >= 3 else []:
                if id(p) in seen:
                    continue
                seen.add(id(p))
                if self._age_ok(p, sp) and name_similarity(p, cand)[0] >= ANY_CLUB_NAME:
                    return "DÉJÀ_PRÉSENT", f"nom très proche : ID {p.id} {p.first} {p.last} ({p.club})".strip()
        for _, _, p in scored:
            if tokens(sp.name) & tokens(f"{p.first} {p.last}"):
                return "À_VÉRIFIER", f"un mot en commun avec ID {p.id} {p.first} {p.last} ({p.club})".strip()
        return None


def clubs_related(a: str, b: str) -> bool:
    """Noms de clubs apparentés : un mot distinctif (4 lettres ou plus, hors mots génériques) en
    commun, ou rapprochement de nom >= 0,6, après nettoyage des sigles à points et de « Fútbol »."""
    ca, cb = clean_club_name(a), clean_club_name(b)
    ta = {t for t in norm_club(ca).split() if len(t) >= 4 and t not in CLUB_GENERIC}
    tb = {t for t in norm_club(cb).split() if len(t) >= 4 and t not in CLUB_GENERIC}
    return bool(ta & tb) or club_similarity(ca, cb) >= 0.6


def clean_club_name(name: str) -> str:
    """« Palermo F.C. » -> « Palermo FC » ; « Club de Fútbol Monterrey » -> « Club de Monterrey »
    (« Fútbol » n'est pas un mot générique du rapprochement partagé, « Futebol » l'est)."""
    name = re.sub(r"\b([A-Za-z])\.", r"\1", name)
    return re.sub(r"\bf[uú]tbol\b", " ", name, flags=re.IGNORECASE).strip()


def read_manual_alias(path: Path) -> dict[str, str]:
    """Correspondances validées par le propriétaire : CSV « club_sauvegarde;club_classeur »."""
    if not path.exists():
        return {}
    with path.open(encoding="utf-8-sig") as f:
        return {r["club_sauvegarde"].strip(): r["club_classeur"].strip()
                for r in csv.DictReader(f, delimiter=";") if (r.get("club_sauvegarde") or "").strip()}


def read_manual_known(path: Path) -> dict[tuple[str, str], int]:
    """Doublons validés par le propriétaire (surnoms) : CSV « nom_sauvegarde;club_sauvegarde;id_classeur »."""
    if not path.exists():
        return {}
    with path.open(encoding="utf-8-sig") as f:
        return {(r["nom_sauvegarde"].strip(), r["club_sauvegarde"].strip()): int(r["id_classeur"])
                for r in csv.DictReader(f, delimiter=";") if (r.get("id_classeur") or "").strip().isdigit()}


def usage_name_in(p: ExcelPlayer, full_name: str) -> bool:
    """Joueur du classeur connu par un nom d'usage seul (Nom vide), présent dans le nom complet
    de la sauvegarde : « Alexsandro » / « Alexsandro Ribeiro », « Gorby » / « Jean-Baptiste Gorby »."""
    usage = norm(p.first).split()
    return not (p.last or "").strip() and len(usage) == 1 and usage[0] in norm(full_name).split()


def same_surname(a: str, b: str) -> bool:
    """Même nom de famille (dernier mot) et même initiale de prénom : « Benjamin White » / « Ben
    White » oui, « Josep Martínez » / « Lautaro Martínez » non."""
    ta, tb = norm(a).split(), norm(b).split()
    return len(ta) >= 2 and len(tb) >= 2 and ta[-1] == tb[-1] and ta[0][0] == tb[0][0]


def new_row_values(pid: int, sp: SavePlayer, club: TargetClub) -> dict:
    first, last = split_name(sp.name)
    poste = save_postes(sp)
    is_gk = (poste or "").split(" / ")[0] == "GK"
    values = {
        "ID": pid, "Prénom": first, "Nom": last, "Nationalité": NATION_PLACEHOLDER, "Âge": sp.age,
        "Poste": poste, "Club": club.name, "Championnat": club.championnat,
        "Taille FM (cm)": sp.height, "Postes FM naturels": fm_natural(sp),
    }
    for a in (GK_SET if is_gk else FIELD_SET):
        if a in sp.attrs:
            values[a] = to_base_scale(sp.attrs[a])
    if sp.left is not None and sp.right is not None:
        values["Pieds"] = strong_foot(sp.left, sp.right)
        values["Weak foot (/5)"] = weak_foot(sp.left, sp.right)
    return values


@dataclass
class Added:
    row: int
    pid: int
    values: dict
    created_club: bool


def add_players(ws, save: list[SavePlayer], count: int = DEFAULT_COUNT, max_squad: int = MAX_SQUAD,
                write: bool = False, manual_alias: dict[str, str] | None = None,
                manual_known: dict[tuple[str, str], int] | None = None,
                ) -> tuple[list[Added], list[list], BaseMatcher, dict[str, TargetClub]]:
    headers = {str(c.value).strip(): c.column for c in ws[1] if c.value is not None}
    headers = ensure_columns(ws, headers)
    _, players = load_players(ws)
    clubs = read_all_clubs(ws, headers)
    matcher = BaseMatcher(players, clubs, save, manual_alias, manual_known)
    next_id = max((p.id for p in players), default=0) + 1
    added: list[Added] = []
    report: list[list] = []
    created: set[str] = set()
    for rank, sp in enumerate(save, 1):
        if len(added) >= count:
            break
        found = matcher.known(sp)
        if found:
            report.append([rank, found[0], sp.name, sp.age, sp.club, "", found[1]])
            continue
        poste = save_postes(sp)
        if not poste:
            report.append([rank, "POSTE_INCONNU", sp.name, sp.age, sp.club, "", " ".join(sp.positions)])
            continue
        name = matcher.club_for(sp.club)
        if name is None and sp.club in clubs and sp.club in created:
            name = sp.club  # club déjà créé pendant cette exécution (« (créer) » compris)
        if name is None:  # club absent du classeur : créé en Autres clubs sous son nom FM exact
            name = sp.club
            clubs[name] = TargetClub(name, OTHER_CLUBS, 0)
            matcher.resolver.memo[sp.club] = name
            created.add(name)
        tc = clubs.setdefault(name, TargetClub(name, OTHER_CLUBS, 0))
        if name != FREE_AGENTS and tc.size >= max_squad:
            report.append([rank, "CLUB_PLEIN", sp.name, sp.age, sp.club, name, f"effectif à {tc.size}"])
            continue
        values = new_row_values(next_id, sp, tc)
        row = append_row(ws, headers, values) if write else 0
        first, last = split_name(sp.name)
        matcher.add(ExcelPlayer(row=row, id=next_id, first=first, last=last or "", nat="", age=sp.age,
                                pos=poste, club=name, rating=None))
        added.append(Added(row, next_id, values, name in created))
        report.append([rank, "AJOUTÉ" if write else "PRÉVU", sp.name, sp.age, sp.club, name,
                       f"ID {next_id}" + (" (club créé)" if name in created else "")])
        tc.size += 1
        next_id += 1
    return added, report, matcher, clubs


def other_clubs_status(ws, added: list[Added], clubs: dict[str, TargetClub], write: bool) -> list[list]:
    """Clubs « Autres clubs » qui reçoivent des joueurs : complet (jouable) ou incomplet."""
    headers = {str(c.value).strip(): c.column for c in ws[1] if c.value is not None}
    groups = squad_groups(ws, headers)
    from ligue1sim.players import position_group
    if not write:
        for a in added:
            groups[a.values["Club"]].append(position_group(a.values["Poste"].split(" / ")[0]))
    per_club = Counter(a.values["Club"] for a in added)
    out = []
    for name in sorted(per_club):
        if clubs[name].championnat != OTHER_CLUBS or name == FREE_AGENTS:
            continue
        g = groups.get(name, [])
        c = Counter(g)
        out.append([name, "complet" if is_playable_squad(g) else "incomplet", len(g), per_club[name],
                    "oui" if any(a.created_club for a in added if a.values["Club"] == name) else "",
                    c["GK"], c["DEF"], c["MID"], c["ATT"]])
    return out


def write_nations_excel(path: Path, added: list[Added]):
    """Fichier à remplir par le propriétaire : Nom, Prénom, Poste, Club, Nation (vide)."""
    import openpyxl
    from openpyxl.worksheet.table import Table

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Nouveaux joueurs"
    ws.append(NATIONS_HEADER)
    for a in added:
        v = a.values
        ws.append([v["Nom"] or "", v["Prénom"], v["Poste"], v["Club"], None])
    ws.freeze_panes = "A2"
    for col, width in zip("ABCDE", (24, 20, 16, 32, 20), strict=True):
        ws.column_dimensions[col].width = width
    if added:
        ws.add_table(Table(displayName="NouveauxJoueurs", ref=f"A1:E{len(added) + 1}"))
    wb.save(path)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    ap.add_argument("--excel", type=Path, default=DEFAULT_EXCEL)
    ap.add_argument("--count", type=int, default=DEFAULT_COUNT, help=f"joueurs à ajouter (défaut {DEFAULT_COUNT})")
    ap.add_argument("--write", action="store_true", help="écrit dans le classeur (sinon essai à blanc)")
    ap.add_argument("--nations-out", type=Path, default=None,
                    help="fichier des nations à remplir (défaut : data/nouveaux_joueurs_nations.xlsx, avec --write)")
    args = ap.parse_args()

    import openpyxl
    save = read_save(args.source)
    wb = openpyxl.load_workbook(args.excel)
    ws = wb[SHEET]
    before = ws.max_row
    manual = read_manual_alias(args.excel.parent / "fmsave_club_aliases.csv")
    known = read_manual_known(args.excel.parent / "fmsave_known_players.csv")
    added, report, matcher, clubs = add_players(ws, save, args.count, write=args.write, manual_alias=manual,
                                                manual_known=known)
    status = other_clubs_status(ws, added, clubs, args.write)
    folder = args.excel.parent
    with (folder / "fmsave_add_report.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["rang", "statut", "nom", "âge", "club_sauvegarde", "club_classeur", "détail"])
        w.writerows(report)
        w.writerow([])
        w.writerow(["club Autres clubs", "statut", "effectif", "ajoutés", "créé", "GK", "DEF", "MID", "ATT"])
        w.writerows(status)
        w.writerow([])
        w.writerow(["correspondance apprise", "club du classeur", "votes", "retenue", "raison", "joueurs ajoutés"])
        prevu = Counter(r[4] for r in report if r[1] in ("PRÉVU", "AJOUTÉ"))
        for sc, club in sorted(matcher.alias.items()):
            w.writerow([sc, club, matcher.votes[sc][club], "oui", "", prevu.get(sc, 0)])
        for sc, (club, n, why) in sorted(matcher.alias_rejected.items()):
            w.writerow([sc, club, n, "non", why, prevu.get(sc, 0)])
        w.writerow([])
        w.writerow(["rattachement par nom proche", "club du classeur", "rapprochement", "joueurs ajoutés"])

        for sc, club in sorted(matcher.approx.items()):
            w.writerow([sc, club, f"{club_similarity(clean_club_name(sc), club):.2f}", prevu.get(sc, 0)])
        w.writerow([])
        w.writerow(["club créé", "joueurs ajoutés", "meilleur club existant", "selon"])
        created = Counter(a.values["Club"] for a in added if a.created_club)
        for name, n in sorted(created.items(), key=lambda kv: (-kv[1], kv[0])):
            w.writerow([name, n, *matcher.best_existing(name)])
    counts = Counter(r[1] for r in report)
    dest = Counter("Sans club" if a.values["Club"] == FREE_AGENTS else
                   ("club créé" if a.created_club else
                    ("Autres clubs" if a.values["Championnat"] == OTHER_CLUBS else "9 championnats"))
                   for a in added)
    print(f"Sauvegarde : {len(save)} lignes ; {len(matcher.alias)} noms de clubs traduits.")
    print("Lignes examinées : " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))
    print("Destination : " + ", ".join(f"{k} {v}" for k, v in sorted(dest.items())))
    st = Counter(s[1] for s in status)
    print(f"Clubs Autres clubs recevant des joueurs : {st['complet']} complets, {st['incomplet']} incomplets")
    print(f"Rapport : {folder / 'fmsave_add_report.csv'}")
    if not args.write:
        print("Essai à blanc : classeur non modifié (--write pour écrire).")
        return
    assert ws.max_row == before + len(added), "nombre de lignes inattendu"
    backup = folder / f"{args.excel.stem}_backup_{datetime.now():%Y%m%d_%H%M%S}{args.excel.suffix}"  # noqa: DTZ005
    shutil.copy2(args.excel, backup)
    try:
        wb.save(args.excel)
    except PermissionError:
        sys.exit(f"Impossible d'écrire {args.excel.name} : ferme-le dans Excel puis relance.")
    nations = args.nations_out or folder / "nouveaux_joueurs_nations.xlsx"
    write_nations_excel(nations, added)
    print(f"{len(added)} joueurs ajoutés (sauvegarde : {backup.name}). Fichier des nations : {nations}")
    print("Étapes suivantes : compute_moyenne_fm.py, generate_national_teams.py")


if __name__ == "__main__":
    main()

"""
Scrape des attributs FM26 sur fminside.net pour les joueurs de data/joueurs.xlsx.

Principe
--------
1. Lit la feuille "Infos principales" (ID, Prénom, Nom, Nationalité, Âge, Poste, Club, Moyenne joueur).
2. Pour chaque joueur, interroge le filtre de la base joueurs fminside (joueurs HOMMES uniquement),
   par nom + nationalité + tranche d'âge, avec des requêtes de repli si besoin.
3. Note chaque candidat (nom, nationalité, âge, club, poste, niveau) et n'accepte un match que si
   - le score dépasse un seuil ET
   - l'écart avec le 2e candidat est net (sinon => AMBIGU, rien n'est écrit).
   Une même fiche fminside attribuée à 2 lignes Excel => CONFLIT, rien n'est écrit.
4. Récupère les attributs sur la fiche du joueur et les écrit dans de NOUVELLES colonnes
   (les colonnes existantes ne sont jamais modifiées). Le tableau Excel "Tableau8" est étendu.
   + infos complémentaires de la fiche : postes naturels, taille, weak foot (/5) et preferred
   moves (ces derniers seulement avec un compte fminside connecté, voir --cookie). Écrit aussi
   "Ability (0-99)" (note générale fminside, indépendante de tout rôle) et "Note FM"
   (0,85 × Ability + 0,15 × Moyenne joueur). Pas de notes de rôle (retirées le 25/09/2026 :
   aucun code du moteur ne les lit, corrélation 0,90 avec Ability -- voir data/joueurs.xlsx).
5. Produit un rapport CSV de matching (à relire pour les AMBIGU / INTROUVABLE / CONFLIT) et
   accepte un fichier de corrections manuelles.

Fichiers (dans le même dossier que joueurs.xlsx)
------------------------------------------------
- fminside_matching_report.csv : décision pour chaque joueur traité + meilleur/2e candidat
- fminside_overrides.csv       : corrections manuelles, colonnes  ID;url
                                 url = lien fminside du bon joueur, ou SKIP pour l'ignorer
- .fminside_cache.json         : cache des recherches et fiches (relances rapides, reprise après arrêt)
- joueurs_backup_YYYYMMDD_HHMMSS.xlsx : sauvegarde avant chaque écriture

Installation
------------
    pip install openpyxl beautifulsoup4 curl_cffi
(curl_cffi imite un vrai Chrome, utile car le site est derrière Cloudflare ; sinon "requests" est utilisé.)

Exemples
--------
    # test sur 30 joueurs, sans écrire dans l'Excel (rapport seulement)
    python scripts/scrape_fminside_attributes.py --limit 30 --dry-run

    # joueurs précis
    python scripts/scrape_fminside_attributes.py --ids 3,4,1471,3851

    # tout le fichier, par lots de 500 (reprend où il s'est arrêté grâce au cache et à la colonne URL)
    python scripts/scrape_fminside_attributes.py --limit 500

    # compléter postes/taille/weak foot/rôles (et moves si --cookie) des joueurs déjà reliés
    python scripts/scrape_fminside_attributes.py --extras-only --cookie "COPIE_DU_COOKIE"

Cookie fminside (pour les preferred moves) : dans Chrome connecté à fminside, F12 > onglet Réseau >
recharger une fiche joueur > clic sur la 1re requête > En-têtes de requête > copier la valeur "cookie".
On peut aussi le mettre dans la variable d'environnement FMINSIDE_COOKIE. Ne le partage pas.

Fermer joueurs.xlsx dans Excel avant de lancer (sinon l'écriture échoue).
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import random
import re
import shutil
import signal
import sys
import time
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path

from bs4 import BeautifulSoup

BASE = "https://fminside.net"
DB_VERSION = "7"  # FM 26
FILTER_URL = BASE + "/resources/inc/ajax/update_filter.php"
TABLE_URL = BASE + "/beheer/modules/players/resources/inc/frontend/generate-player-table.php"

SHEET = "Infos principales"
TABLE_NAME = "Tableau8"
URL_COL = "FMInside URL"

# Ordre des colonnes ajoutées (noms exacts du site)
TECHNICAL = ["Crossing", "Dribbling", "Finishing", "First Touch", "Heading", "Long Shots",
             "Marking", "Passing", "Tackling", "Technique"]
GOALKEEPING = ["Aerial Reach", "Command of Area", "Communication", "Eccentricity", "Handling",
               "Kicking", "One on Ones", "Punching (Tendency)", "Reflexes",
               "Rushing Out (Tendency)", "Throwing"]
MENTAL = ["Aggression", "Anticipation", "Bravery", "Composure", "Concentration", "Decisions",
          "Determination", "Flair", "Leadership", "Off the Ball", "Positioning", "Teamwork",
          "Vision", "Work Rate"]
PHYSICAL = ["Acceleration", "Agility", "Balance", "Jumping Reach", "Natural Fitness", "Pace",
            "Stamina", "Strength"]
SET_PIECES = ["Corners", "Free Kick Taking", "Long Throws", "Penalty Taking"]
ATTRIBUTES = TECHNICAL + GOALKEEPING + MENTAL + PHYSICAL + SET_PIECES
# Infos complémentaires de la fiche (ajoutées à droite, après l'URL)
POS_COL, HEIGHT_COL, WF_COL = "Postes FM naturels", "Taille FM (cm)", "Weak foot (/5)"
MOVES_COL = "Preferred moves"
EXTRA_COLUMNS = [POS_COL, HEIGHT_COL, WF_COL, MOVES_COL]
# Rôles (possession/hors possession, 25/09/2026) : retirés -- aucun code du moteur
# (lineup.py/simulation.py/events.py) ne les lisait, corrélation 0,90 avec Ability
# (redondant), et les 16 colonnes au-delà du top 2 en possession n'étaient de toute
# façon récupérables que via une session navigateur manuelle, pas ce script. Voir
# data/joueurs_backup_20260925_234546.xlsx pour la dernière version qui les avait.
# Note FM (25/09/2026) : ability = note generale fminside (badge de recherche, deja
# calculee pour le scoring anti-homonymes -- Candidate.ability, criere "niveau" de
# score_candidate) -- jamais ecrite jusqu'ici. Note FM = combinaison avec Moyenne
# joueur, memes poids que la passe manuelle faite sur le lot n1 (497 joueurs).
ABILITY_COL = "Ability (0-99)"
NOTE_FM_COL = "Note FM"
NOTE_FM_WEIGHT_ABILITY = 0.85
NOTE_FM_WEIGHT_MOYENNE = 0.15
NEW_COLUMNS = ATTRIBUTES + [URL_COL] + EXTRA_COLUMNS + [ABILITY_COL, NOTE_FM_COL]

# --- Réglages du matching -----------------------------------------------------------------
MIN_SCORE = 16.0      # score mini pour accepter un candidat
MIN_MARGIN = 4.0      # écart mini avec le 2e candidat
MIN_NAME = 0.70       # similarité de nom mini pour qu'un candidat soit seulement envisagé
MAX_PAGES = 10        # pages de 50 lignes max par requête de recherche

# Nationalités Excel (FR) -> libellés fminside (EN). Le 1er sert au filtre serveur,
# tous servent à la comparaison. Pays absent => comparé tel quel.
NATIONALITIES = {
    "Afghanistan": ["Afghanistan"], "Afrique du Sud": ["South Africa"], "Albanie": ["Albania"],
    "Algérie": ["Algeria"], "Allemagne": ["Germany"], "Angleterre": ["England"],
    "Angola": ["Angola"], "Arabie saoudite": ["Saudi Arabia"], "Argentine": ["Argentina"],
    "Arménie": ["Armenia"], "Australie": ["Australia"], "Autriche": ["Austria"],
    "Azerbaïdjan": ["Azerbaijan"], "Barbados": ["Barbados"], "Belgique": ["Belgium"],
    "Biélorussie": ["Belarus"], "Bolivie": ["Bolivia"],
    "Bosnie-Herzégovine": ["Bosnia and Herzegovina", "Bosnia & Herzegovina"],
    "Brésil": ["Brazil"], "Bulgarie": ["Bulgaria"], "Burkina Faso": ["Burkina Faso"],
    "Burundi": ["Burundi"], "Bénin": ["Benin"], "Cameroun": ["Cameroon"], "Canada": ["Canada"],
    "Cap-Vert": ["Cape Verde Islands", "Cape Verde", "Cabo Verde"], "Chili": ["Chile"],
    "Chine": ["China PR", "China"], "Chypre": ["Cyprus"], "Colombie": ["Colombia"],
    "Comores": ["Comoros"], "Congo": ["Congo"],
    "Corée du Sud": ["South Korea", "Korea Republic"], "Costa Rica": ["Costa Rica"],
    "Croatie": ["Croatia"], "Curaçao": ["Curaçao"], "Côte d'Ivoire": ["Ivory Coast", "Côte d'Ivoire"],
    "Danemark": ["Denmark"], "Espagne": ["Spain"], "Estonie": ["Estonia"], "Finlande": ["Finland"],
    "France": ["France"], "Gabon": ["Gabon"], "Gambie": ["The Gambia", "Gambia"], "Ghana": ["Ghana"],
    "Grèce": ["Greece"], "Guadeloupe": ["Guadeloupe"], "Guinée": ["Guinea"],
    "Guinée équatoriale": ["Equatorial Guinea"], "Guinée-Bissau": ["Guinea-Bissau"],
    "Géorgie": ["Georgia"], "Haïti": ["Haiti"], "Honduras": ["Honduras"], "Hongrie": ["Hungary"],
    "Indonésie": ["Indonesia"], "Irak": ["Iraq"], "Iran": ["Iran", "IR Iran"],
    "Irlande": ["Republic of Ireland", "Ireland"], "Irlande du Nord": ["Northern Ireland"],
    "Islande": ["Iceland"], "Israël": ["Israel"], "Italie": ["Italy"], "Jamaïque": ["Jamaica"],
    "Japon": ["Japan"], "Jordanie": ["Jordan"], "Kazakhstan": ["Kazakhstan"], "Kenya": ["Kenya"],
    "Kosovo": ["Kosovo"], "Latvia": ["Latvia"], "Liban": ["Lebanon"], "Libye": ["Libya"],
    "Lituanie": ["Lithuania"], "Luxembourg": ["Luxembourg"], "Macédoine du Nord": ["North Macedonia"],
    "Madagascar": ["Madagascar"], "Malaisie": ["Malaysia"], "Mali": ["Mali"], "Maroc": ["Morocco"],
    "Martinique": ["Martinique"], "Mauritanie": ["Mauritania"], "Mexique": ["Mexico"],
    "Monténégro": ["Montenegro"], "Mozambique": ["Mozambique"], "Namibia": ["Namibia"],
    "Niger": ["Niger"], "Nigeria": ["Nigeria"], "Norvège": ["Norway"],
    "Nouvelle-Zélande": ["New Zealand"], "Ouzbékistan": ["Uzbekistan"], "Panama": ["Panama"],
    "Paraguay": ["Paraguay"], "Pays de Galles": ["Wales"], "Pays-Bas": ["Netherlands"],
    "Philippines": ["Philippines"], "Pologne": ["Poland"], "Porto Rico": ["Puerto Rico"],
    "Portugal": ["Portugal"], "Pérou": ["Peru"], "Qatar": ["Qatar"],
    "RD Congo": ["Democratic Republic of Congo", "DR Congo", "Congo DR"],
    "Roumanie": ["Romania"], "Russie": ["Russia"], "Rwanda": ["Rwanda"],
    "République centrafricaine": ["Central African Republic"],
    "République dominicaine": ["Dominican Republic"],
    "République tchèque": ["Czechia", "Czech Republic"], "Serbie": ["Serbia"],
    "Sierra Leone": ["Sierra Leone"], "Slovaquie": ["Slovakia"], "Slovénie": ["Slovenia"],
    "Soudan": ["Sudan"], "St. Lucia": ["St. Lucia", "St Lucia", "Saint Lucia"],
    "Suisse": ["Switzerland"], "Suriname": ["Suriname"], "Suède": ["Sweden"], "Syrie": ["Syria"],
    "Sénégal": ["Senegal"], "Tanzanie": ["Tanzania"], "Thaïlande": ["Thailand"], "Togo": ["Togo"],
    "Trinité-et-Tobago": ["Trinidad and Tobago", "Trinidad & Tobago"], "Tunisie": ["Tunisia"],
    "Turquie": ["Turkey", "Türkiye"], "Uganda": ["Uganda"], "Ukraine": ["Ukraine"],
    "Uruguay": ["Uruguay"], "Venezuela": ["Venezuela"], "Zambie": ["Zambia"],
    "Zimbabwe": ["Zimbabwe"], "Écosse": ["Scotland"], "Égypte": ["Egypt"],
    "Émirats arabes unis": ["United Arab Emirates"], "Équateur": ["Ecuador"],
    "Érythrée": ["Eritrea"], "États-Unis": ["United States", "USA"],
}

# Postes Excel -> postes FM compatibles
POSITIONS = {
    "GK": {"GK"}, "DC": {"DC"}, "LB": {"DL", "WBL"}, "RB": {"DR", "WBR"}, "MDC": {"DM"},
    "MC": {"MC"}, "MOC": {"AMC"}, "MO": {"AMC"}, "AG": {"AML", "ML"}, "AD": {"AMR", "MR"},
    "BU": {"ST"}, "SA": {"ST", "AMC"},
}

# Noms de clubs qui ne se ressemblent pas entre la base et FM (après normalisation)
CLUB_ALIASES = {
    "paris saint germain": "psg", "bayern munich": "bayern", "bayern munchen": "bayern",
    "internazionale": "inter", "inter milan": "inter", "atletico de madrid": "atletico madrid",
    "borussia monchengladbach": "gladbach", "manchester united": "man utd",
    "manchester city": "man city", "tottenham hotspur": "tottenham", "wolverhampton wanderers": "wolves",
    "brighton hove albion": "brighton", "nottingham forest": "nottm forest",
    "west ham united": "west ham", "newcastle united": "newcastle", "sporting cp": "sporting",
    "fc porto": "porto", "sl benfica": "benfica", "olympique de marseille": "marseille",
    "olympique lyonnais": "lyon", "as monaco": "monaco", "psv eindhoven": "psv",
}
CLUB_STOPWORDS = {"fc", "cf", "afc", "sc", "ac", "as", "ssc", "sv", "vfb", "vfl", "tsg", "rc",
                  "rcd", "cd", "ud", "sd", "ca", "club", "de", "fk", "sk", "bk", "if", "us", "ss",
                  "calcio", "the", "sad", "cp", "kv", "krc", "rsc", "osc", "ogc", "ea", "aj", "and"}

CLUB_GENERIC = {"city", "town", "united", "utd", "county", "athletic", "rovers", "wanderers", "albion",
                "hotspur", "cfc", "calcio", "club", "football", "futebol", "clube", "sporting", "1907",
                "1909", "1846", "04", "05", "fc", "sc", "ac"}

SPECIAL_CHARS = str.maketrans({"ø": "o", "Ø": "o", "æ": "ae", "Æ": "ae", "ß": "ss", "đ": "d",
                               "Đ": "d", "ł": "l", "Ł": "l", "ı": "i", "œ": "oe", "Œ": "oe",
                               "þ": "th", "ð": "d"})


# --- Normalisation ----------------------------------------------------------------------------
def norm(s) -> str:
    """minuscules, sans accents ni ponctuation, espaces simples."""
    if s is None:
        return ""
    s = str(s).translate(SPECIAL_CHARS)
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.lower().replace("&", " and ")
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def norm_club(s) -> str:
    n = norm(s)
    n = CLUB_ALIASES.get(n, n)
    toks = [t for t in n.split() if t not in CLUB_STOPWORDS and not t.isdigit()]
    n = " ".join(toks)
    return CLUB_ALIASES.get(n, n)


def club_similarity(a, b) -> float:
    a, b = norm_club(a), norm_club(b)
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    ta, tb = set(a.split()), set(b.split())
    # inclusion acceptée si le nom court a au moins 2 mots, ou si les mots en plus sont
    # génériques ("Coventry City" = "Coventry") — mais "Porto" ≠ "Porto Vitória", "Inter" ≠ "Inter Miami"
    if ta <= tb or tb <= ta:
        extra = (ta | tb) - (ta & tb)
        if min(len(ta), len(tb)) >= 2 or extra <= CLUB_GENERIC:
            return 0.9
    return SequenceMatcher(None, a, b).ratio()


def nat_aliases(fr: str | None) -> list[str]:
    if not fr:
        return []
    return NATIONALITIES.get(str(fr).strip(), [str(fr).strip()])


def excel_positions(p) -> set[str]:
    out = set()
    for tok in re.split(r"[/,]", str(p or "")):
        out |= POSITIONS.get(tok.strip().upper(), set())
    return out


def to_int(v):
    try:
        return int(float(str(v).replace(",", ".")))
    except (TypeError, ValueError):
        return None


# --- Modèles ----------------------------------------------------------------------------------
@dataclass
class ExcelPlayer:
    row: int
    id: int
    first: str
    last: str
    nat: str
    age: int | None
    pos: str
    club: str
    rating: float | None

    @property
    def label(self):
        return f"#{self.id} {self.first} {self.last}".strip()


@dataclass
class Candidate:
    url: str
    name: str
    full_name: str
    nat: str
    age: int | None
    club: str
    positions: set[str]
    ability: int | None
    score: float = 0.0
    name_score: float = 0.0
    details: list[str] = field(default_factory=list)

    def to_json(self):
        d = self.__dict__.copy()
        d["positions"] = sorted(self.positions)
        return d

    @staticmethod
    def from_json(d):
        d = dict(d)
        d["positions"] = set(d.get("positions", []))
        for k in ("score", "name_score", "details"):
            d.pop(k, None)
        return Candidate(**d)


# --- Parsing HTML -----------------------------------------------------------------------------
def parse_player_rows(html: str) -> list[Candidate]:
    soup = BeautifulSoup(html, "html.parser")
    out = []
    for ul in soup.select("ul.player.database-table-row"):
        a = ul.select_one('span.name a[href^="/players/"]')
        if not a:
            continue
        copy_btn = ul.select_one("button.player-name-copy")
        flag = ul.select_one("img.flag")
        club = ul.select_one('span.name a[href^="/clubs/"]')
        age = ul.select_one("li.age")
        rating = ul.select_one("li.rating span.card")
        pos = {s.get_text(strip=True).upper() for s in ul.select("span.desktop_positions span.position")}
        out.append(Candidate(
            url=BASE + a["href"],
            name=a.get_text(strip=True),
            full_name=(copy_btn.get("data-copy-player-name") if copy_btn else "") or "",
            nat=(flag.get("code") if flag else "") or "",
            age=to_int(age.get_text(strip=True)) if age else None,
            club=club.get_text(strip=True) if club else "",
            positions=pos,
            ability=to_int(rating.get_text(strip=True)) if rating else None,
        ))
    return out


def parse_attributes(html: str) -> dict[str, int | str]:
    soup = BeautifulSoup(html, "html.parser")
    attrs = {}
    for tr in soup.select("tr"):
        name_td, stat_td = tr.select_one("td.name"), tr.select_one("td.stat")
        if not name_td or not stat_td:
            continue
        btn = name_td.select_one("[data-player-stat-name]")
        name = btn["data-player-stat-name"] if btn else name_td.get_text(strip=True)
        raw = stat_td.get_text(strip=True)
        val = to_int(raw)
        attrs[name] = val if val is not None else raw
    return {k: v for k, v in attrs.items() if k in ATTRIBUTES}


def parse_extras(html: str) -> dict:
    """Postes naturels, taille, weak foot, preferred moves.
    Les preferred moves (et attributs cachés) ne sont visibles que connecté à un compte fminside."""
    soup = BeautifulSoup(html, "html.parser")
    info = {}
    for li in soup.select("#player-mobile-info li"):
        k = li.select_one(".key")
        if k:
            info[k.get_text(strip=True).rstrip(":").strip()] = li.select_one(".value")
    ex = {}
    pos = info.get("Positions")
    ex["natural"] = [s.get_text(strip=True) for s in pos.select(".position.natural")] if pos else []
    h = info.get("Height")
    ex["height"] = to_int(re.sub(r"\D", "", h.get_text())) if h else None
    wf = info.get("Weak foot")
    lab = wf.select_one("[aria-label]").get("aria-label", "") if wf and wf.select_one("[aria-label]") else ""
    m = re.search(r"([\d.]+) out of 5", lab)
    ex["weak_foot"] = float(m.group(1)) if m else None
    hid = soup.select_one("section.player-hidden-attributes")
    ex["locked"] = bool(hid and "locked" in " ".join(hid.get("class", [])))
    ex["moves"] = [s.get_text(strip=True) for s in soup.select("ul.player-preferred-moves .player-preferred-move-label")]
    ex["hidden"] = {}
    if hid and not ex["locked"]:
        for tr in hid.select("tr"):
            n, v = tr.select_one("[data-player-stat-name]"), tr.select_one("td.stat")
            if n and v:
                x = to_int(v.get_text(strip=True))
                ex["hidden"][n["data-player-stat-name"]] = x if x is not None else v.get_text(strip=True)
    return ex


def write_extras(ws, row: int, headers: dict, ex: dict | None):
    if not ex:
        return
    ws.cell(row, headers[POS_COL]).value = ", ".join(ex.get("natural") or []) or None
    ws.cell(row, headers[HEIGHT_COL]).value = ex.get("height")
    wf = ex.get("weak_foot")
    ws.cell(row, headers[WF_COL]).value = int(wf) if isinstance(wf, float) and wf.is_integer() else wf
    if not ex.get("locked"):  # sinon on ne sait pas : on laisse la cellule telle quelle
        ws.cell(row, headers[MOVES_COL]).value = " ; ".join(ex.get("moves") or []) or "(aucun)"


# --- Scoring ----------------------------------------------------------------------------------
def name_similarity(p: ExcelPlayer, c: Candidate) -> tuple[float, str]:
    e_full = norm(f"{p.first or ''} {p.last or ''}")
    e_first, e_last = norm(p.first), norm(p.last)
    f_disp, f_full = norm(c.name), norm(c.full_name)
    f_tokens = set(f_disp.split()) | set(f_full.split())
    if e_full and e_full in (f_disp, f_full):
        return 1.0, "nom identique"
    e_tokens = set(e_full.split())
    if len(e_tokens) == 1:
        # nom d'usage en un mot (Gabriel, Rodri, Pedri…) : il doit être LE nom affiché,
        # sinon "Gabriel" matcherait "Gabriel Jesus" / "Gabriel Martinelli"
        if e_full == f_disp:
            return 1.0, "nom identique"
        if e_tokens <= set(f_full.split()) and len(f_disp.split()) == 1:
            return 0.85, "nom d'usage présent dans le nom complet"
        return 0.70, "nom d'usage seul, nom affiché différent"
    if e_tokens and e_tokens <= f_tokens:
        return 0.95, "tous les mots du nom présents"
    fd = f_disp.split()
    if len(fd) == 1 and not set(f_full.split()) - set(fd):
        # FM n'a qu'un nom d'usage (Amad, Igor, Jair, Fermín, Thiago…)
        if fd[0] in e_last.split():
            return 0.80, "nom d'usage FM = nom de famille"
        if fd[0] == e_first:
            return 0.75, "nom d'usage FM = prénom"
    if e_last and set(e_last.split()) <= f_tokens:
        firsts = [t for t in (f_disp.split()[:1] + f_full.split()[:1])]
        if e_first and any(t.startswith(e_first[0]) for t in firsts):
            return 0.80, "nom + initiale du prénom"
        if not e_first:
            return 0.70, "nom de famille seul"
        # même nom de famille mais autre prénom (Harry Clarke ≠ Jack Clarke) : écarté
        return 0.55, "même nom de famille, prénom différent"
    ratio = max(SequenceMatcher(None, e_full, f_disp).ratio(),
                SequenceMatcher(None, e_full, f_full).ratio() if f_full else 0)
    return round(ratio * 0.9, 3), f"nom proche ({ratio:.2f})"


def score_candidate(p: ExcelPlayer, c: Candidate) -> Candidate:
    c.details = []
    c.name_score, why = name_similarity(p, c)
    s = 10 * c.name_score
    c.details.append(f"nom {c.name_score:.2f} ({why})")

    aliases = {norm(a) for a in nat_aliases(p.nat)}
    if aliases and c.nat:
        if norm(c.nat) in aliases:
            s += 4; c.details.append("nationalité OK +4")
        else:
            # -1 seulement : beaucoup de binationaux (FM n'affiche qu'une nationalité)
            s -= 1; c.details.append(f"nationalité {c.nat} ≠ {p.nat} -1")

    if p.age is not None and c.age is not None:
        d = p.age - c.age  # base FM26 = saison 2025, ta base est ~1 an plus tard
        if d == 1:
            s += 3; c.details.append("âge +1 an (attendu) +3")
        elif d in (0, 2):
            s += 2; c.details.append(f"âge écart {d:+d} +2")
        elif d in (-1, 3):
            c.details.append(f"âge écart {d:+d} 0")
        else:
            s -= 6; c.details.append(f"âge écart {d:+d} -6")

    cs = club_similarity(p.club, c.club)
    if cs >= 0.8:
        s += 4; c.details.append(f"club OK ({c.club}) +4")

    e_pos = excel_positions(p.pos)
    if e_pos and c.positions:
        if ("GK" in e_pos) != ("GK" in c.positions):
            s -= 8; c.details.append("gardien/joueur de champ incohérent -8")
        elif e_pos & c.positions:
            s += 1; c.details.append("poste compatible +1")

    # niveau : ta "Moyenne joueur" peut être volontairement ajustée (blessure, suspension…),
    # donc on ne pénalise pas un écart de niveau quand le club correspond déjà
    if p.rating is not None and c.ability is not None and not (cs >= 0.8 and abs(float(p.rating) - c.ability) > 7):
        gap = abs(float(p.rating) - c.ability)
        if gap <= 7:
            s += 1; c.details.append("niveau proche +1")
        elif gap > 30:
            s -= 4; c.details.append(f"niveau très différent ({c.ability} vs {p.rating}) -4")
        elif gap > 20:
            s -= 2; c.details.append(f"niveau différent ({c.ability} vs {p.rating}) -2")

    c.score = round(s, 2)
    return c


# --- Client HTTP ------------------------------------------------------------------------------
class FMInside:
    def __init__(self, delay: float, cache_path: Path, use_cache: bool = True, cookie: str = ""):
        self.delay = delay
        self.cache_path = cache_path
        self.cache = {"search": {}, "profile": {}}
        if use_cache and cache_path.exists():
            try:
                self.cache = json.loads(cache_path.read_text(encoding="utf-8"))
            except Exception:
                print("! cache illisible, on repart de zéro")
        try:
            from curl_cffi import requests as creq
            self.s = creq.Session(impersonate="chrome")
            self.engine = "curl_cffi"
        except ImportError:
            import requests
            self.s = requests.Session()
            self.s.headers["User-Agent"] = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                                            "(KHTML, like Gecko) Chrome/140.0 Safari/537.36")
            self.engine = "requests"
        self.s.headers.update({"Referer": BASE + "/players", "Accept-Language": "en-GB,en;q=0.9"})
        self.logged_in = bool(cookie)
        if cookie:  # session fminside (compte membre) pour les preferred moves
            self.s.headers["Cookie"] = cookie
        self.cache.setdefault("extra", {})
        self._warm = False
        self._last = 0.0

    def save_cache(self):
        tmp = self.cache_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.cache, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, self.cache_path)

    def _req(self, method, url, **kw):
        for attempt in range(5):
            wait = self.delay + random.uniform(0, self.delay * 0.5) - (time.time() - self._last)
            if wait > 0:
                time.sleep(wait)
            self._last = time.time()
            try:
                r = self.s.request(method, url, timeout=30, **kw)
            except Exception as e:  # réseau
                print(f"  ! erreur réseau ({e}), nouvel essai")
                time.sleep(5 * (attempt + 1))
                continue
            if r.status_code == 200:
                if "Just a moment" in r.text[:2000] and "cf-" in r.text[:5000]:
                    raise RuntimeError("Bloqué par Cloudflare. Installe curl_cffi (pip install curl_cffi) "
                                       "ou augmente --delay.")
                return r
            if r.status_code in (429, 500, 502, 503, 504):
                pause = 20 * (attempt + 1)
                print(f"  ! HTTP {r.status_code}, pause {pause}s")
                time.sleep(pause)
                continue
            if r.status_code == 403:
                raise RuntimeError("HTTP 403 : accès refusé (Cloudflare ?). Installe curl_cffi ou augmente --delay.")
            r.raise_for_status()
        raise RuntimeError(f"Échec après 5 essais : {url}")

    def warmup(self):
        if not self._warm:
            self._req("GET", BASE + "/players")
            self._warm = True

    def search(self, name="", nationality="", min_age=None, max_age=None) -> list[Candidate]:
        key = json.dumps([name, nationality, min_age, max_age], ensure_ascii=False)
        if key in self.cache["search"]:
            return [Candidate.from_json(d) for d in self.cache["search"][key]]
        self.warmup()
        form = {"page": "players", "database_version": DB_VERSION, "gender": "1",  # 1 = hommes
                "name": name, "uid": "", "club": "", "nationality": nationality, "league": "",
                "league_id": "", "min_age": "" if min_age is None else str(min_age),
                "max_age": "" if max_age is None else str(max_age), "max_value": "", "max_wage": "",
                "min_ability": "", "max_ability": "", "min_potential": "", "max_potential": "", "clause": ""}
        hdr = {"X-Requested-With": "XMLHttpRequest"}
        self._req("POST", FILTER_URL, data=form, headers=hdr)
        rows = parse_player_rows(self._req("GET", TABLE_URL, params={"ajax_request": "1"}, headers=hdr).text)
        page = 1
        while rows and len(rows) % 50 == 0 and page < MAX_PAGES:
            more = parse_player_rows(self._req("GET", TABLE_URL, params={"ajax_request": "1", "loadmore": "true"},
                                               headers=hdr).text)
            if not more:
                break
            rows += more
            page += 1
        seen, uniq = set(), []
        for c in rows:
            if c.url not in seen:
                seen.add(c.url); uniq.append(c)
        self.cache["search"][key] = [c.to_json() for c in uniq]
        return uniq

    def attributes(self, url: str) -> dict:
        self.profile(url)
        return self.cache["profile"][url]

    def extras(self, url: str) -> dict:
        self.profile(url)
        return self.cache["extra"].get(url)

    def profile(self, url: str):
        """Télécharge la fiche une seule fois pour les attributs ET les infos complémentaires.
        Si on est connecté et que les preferred moves étaient verrouillés en cache, on la retélécharge."""
        ex = self.cache["extra"].get(url)
        if url in self.cache["profile"] and ex and not (self.logged_in and ex.get("locked")):
            return
        html = self._req("GET", url).text
        attrs = parse_attributes(html)
        if not attrs:
            raise RuntimeError(f"Aucun attribut trouvé sur {url} (structure du site modifiée ?)")
        self.cache["profile"][url] = attrs
        ex = parse_extras(html)
        if self.logged_in and ex["locked"]:
            raise RuntimeError("Cookie fourni mais fiche verrouillée : session fminside expirée ? "
                               "Reprends le cookie dans ton navigateur connecté.")
        self.cache["extra"][url] = ex


# --- Matching ---------------------------------------------------------------------------------
def queries_for(p: ExcelPlayer):
    """Requêtes successives, de la plus précise à la plus large."""
    names = []
    if p.last:
        names.append(p.last)
    elif p.first:
        names.append(p.first)
    if p.first and p.last:
        names.append(p.first)            # repli : prénom (utile si le nom FM diffère : Ø, surnom…)
    ages = (p.age - 3, p.age + 1) if p.age else (None, None)
    nats = nat_aliases(p.nat)[:1] or [""]
    seen = set()
    for n in names:
        for nat in nats + [""]:
            for a in (ages, (None, None)):
                q = (n, nat, *a)
                if q not in seen:
                    seen.add(q)
                    yield q


def decide(p: ExcelPlayer, cands: list[Candidate]):
    ranked = sorted((c for c in cands if c.name_score >= MIN_NAME), key=lambda c: -c.score)
    best = ranked[0] if ranked else None
    second = ranked[1] if len(ranked) > 1 else None
    if not best:
        return "INTROUVABLE", None, None, "aucun candidat avec un nom proche"
    if best.score < MIN_SCORE:
        return "INTROUVABLE", best, second, f"meilleur score {best.score} < {MIN_SCORE}"
    if second and best.score - second.score < MIN_MARGIN:
        return "AMBIGU", best, second, f"écart {best.score - second.score:.1f} < {MIN_MARGIN} avec le 2e"
    return "OK", best, second, ""


def match_player(api: FMInside, p: ExcelPlayer):
    pool: dict[str, Candidate] = {}
    result = ("INTROUVABLE", None, None, "aucun résultat")
    for q in queries_for(p):
        for c in api.search(*q):
            pool.setdefault(c.url, c)
        for c in pool.values():
            score_candidate(p, c)
        result = decide(p, list(pool.values()))
        if result[0] == "OK":
            # contre-vérification : même nom, même tranche d'âge, TOUTES nationalités,
            # pour s'assurer qu'aucun homonyme étranger ne fait concurrence
            if q[1]:
                for c in api.search(q[0], "", q[2], q[3]):
                    if c.url not in pool:
                        pool[c.url] = score_candidate(p, c)
                result = decide(p, list(pool.values()))
            return result
    return result


# --- Excel ------------------------------------------------------------------------------------
def load_players(ws) -> tuple[dict, list[ExcelPlayer]]:
    headers = {str(c.value).strip(): c.column for c in ws[1] if c.value is not None}
    need = ["ID", "Prénom", "Nom", "Nationalité", "Âge", "Poste", "Club", "Moyenne joueur"]
    missing = [h for h in need if h not in headers]
    if missing:
        sys.exit(f"Colonnes introuvables dans '{SHEET}' : {missing}")
    players = []
    for r in range(2, ws.max_row + 1):
        pid = ws.cell(r, headers["ID"]).value
        if pid is None:
            continue
        g = lambda h: ws.cell(r, headers[h]).value
        rating = g("Moyenne joueur")
        players.append(ExcelPlayer(
            row=r, id=int(pid), first=(g("Prénom") or "").strip(), last=(g("Nom") or "").strip(),
            nat=(g("Nationalité") or "").strip(), age=to_int(g("Âge")), pos=g("Poste") or "",
            club=(g("Club") or "").strip(),
            rating=float(rating) if isinstance(rating, (int, float)) else None))
    return headers, players


def ensure_columns(ws, headers: dict) -> dict:
    """Ajoute les colonnes manquantes à droite (jamais au milieu) et étend le tableau Excel."""
    import copy
    from openpyxl.utils import get_column_letter
    from openpyxl.worksheet.table import TableColumn
    last = max(headers.values())
    style_src = ws.cell(1, last)
    for name in NEW_COLUMNS:
        if name not in headers:
            last += 1
            cell = ws.cell(1, last, name)
            cell._style = copy.copy(style_src._style)
            ws.column_dimensions[get_column_letter(last)].width = max(10, len(name) + 2)
            headers[name] = last
    if TABLE_NAME in ws.tables:
        t = ws.tables[TABLE_NAME]
        start, end = t.ref.split(":")
        end_row = int(re.sub(r"\D", "", end))
        t.ref = f"{start}:{get_column_letter(last)}{end_row}"
        t.autoFilter.ref = t.ref
        t.autoFilter.sortState = None
        t.sortState = None
        existing = {tc.name for tc in t.tableColumns}
        next_id = max(tc.id for tc in t.tableColumns) + 1
        for name in NEW_COLUMNS:
            if name not in existing:
                t.tableColumns.append(TableColumn(id=next_id, name=name)); next_id += 1
    return headers


def read_overrides(path: Path) -> dict[int, str]:
    if not path.exists():
        return {}
    out = {}
    with path.open(encoding="utf-8-sig") as f:
        sample = f.read(2048); f.seek(0)
        delim = ";" if sample.count(";") >= sample.count(",") else ","
        for row in csv.DictReader(f, delimiter=delim):
            pid, url = to_int(row.get("ID")), (row.get("url") or "").strip()
            if pid and url:
                out[pid] = url
    return out


# --- Main -------------------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    default_excel = Path(__file__).resolve().parent.parent / "data" / "joueurs.xlsx"
    ap.add_argument("--excel", type=Path, default=default_excel)
    ap.add_argument("--limit", type=int, default=0, help="nb max de joueurs à traiter (0 = tous)")
    ap.add_argument("--ids", default="", help="liste d'ID Excel séparés par des virgules")
    ap.add_argument("--delay", type=float, default=1.0, help="secondes entre 2 requêtes (défaut 1)")
    ap.add_argument("--dry-run", action="store_true", help="n'écrit pas l'Excel, produit seulement le rapport")
    ap.add_argument("--redo", action="store_true", help="retraite aussi les joueurs déjà remplis")
    ap.add_argument("--no-cache", action="store_true", help="ignore le cache existant")
    ap.add_argument("--extras-only", action="store_true",
                    help="complète seulement postes/taille/weak foot/rôles/moves des joueurs déjà reliés (URL)")
    ap.add_argument("--cookie", default=os.environ.get("FMINSIDE_COOKIE", ""),
                    help="cookie de session fminside (compte connecté) pour les preferred moves")
    args = ap.parse_args()

    import openpyxl
    xlsx: Path = args.excel
    folder = xlsx.parent
    report_path = folder / "fminside_matching_report.csv"
    overrides = read_overrides(folder / "fminside_overrides.csv")
    api = FMInside(args.delay, folder / ".fminside_cache.json", use_cache=not args.no_cache, cookie=args.cookie)
    print(f"Client HTTP : {api.engine} | overrides : {len(overrides)} | "
          f"connecté : {'oui' if api.logged_in else 'non (preferred moves non récupérés)'}")

    wb = openpyxl.load_workbook(xlsx)
    ws = wb[SHEET]
    headers, players = load_players(ws)
    headers = ensure_columns(ws, headers)
    url_col = headers[URL_COL]

    if args.extras_only:
        rows = [p for p in players if ws.cell(p.row, url_col).value]
        if args.ids:
            wanted = {int(x) for x in args.ids.split(",") if x.strip()}
            rows = [p for p in rows if p.id in wanted]
        elif not args.redo:  # ne refait que les lignes incomplètes
            rows = [p for p in rows if ws.cell(p.row, headers[POS_COL]).value is None
                    or (api.logged_in and ws.cell(p.row, headers[MOVES_COL]).value is None)]
        if args.limit:
            rows = rows[: args.limit]
        print(f"{len(rows)} joueurs à compléter")
        done = 0
        for i, p in enumerate(rows, 1):
            url = ws.cell(p.row, url_col).value
            try:
                write_extras(ws, p.row, headers, api.extras(url))
                done += 1
            except RuntimeError as e:
                print(f"ERREUR bloquante : {e}")
                break
            if i % 25 == 0:
                api.save_cache(); print(f"  {i}/{len(rows)}")
        api.save_cache()
        if not args.dry_run and done:
            backup = folder / f"{xlsx.stem}_backup_{datetime.now():%Y%m%d_%H%M%S}{xlsx.suffix}"
            shutil.copy2(xlsx, backup)
            wb.save(xlsx)
            print(f"{done} joueurs complétés (sauvegarde : {backup.name})")
        return

    if args.ids:
        wanted = {int(x) for x in args.ids.split(",") if x.strip()}
        players = [p for p in players if p.id in wanted]
    elif not args.redo:
        players = [p for p in players if not ws.cell(p.row, url_col).value]
    if args.limit:
        players = players[: args.limit]
    print(f"{len(players)} joueurs à traiter")

    # URLs déjà présentes dans l'Excel (pour détecter qu'une fiche est prise 2 fois)
    taken = {}
    for r in range(2, ws.max_row + 1):
        u = ws.cell(r, url_col).value
        if u:
            taken.setdefault(u, set()).add(ws.cell(r, headers["ID"]).value)

    results = []  # (player, status, best, second, reason)
    stop = {"flag": False}
    signal.signal(signal.SIGINT, lambda *_: stop.update(flag=True) or print("\nArrêt demandé, on sauvegarde…"))

    for i, p in enumerate(players, 1):
        if stop["flag"]:
            break
        try:
            if p.id in overrides:
                url = overrides[p.id]
                if url.upper() == "SKIP":
                    results.append((p, "SKIP", None, None, "override"))
                    continue
                best = Candidate(url=url, name="(override)", full_name="", nat="", age=None, club="",
                                 positions=set(), ability=None)
                results.append((p, "OVERRIDE", best, None, "lien fourni manuellement"))
            else:
                status, best, second, reason = match_player(api, p)
                results.append((p, status, best, second, reason))
            st, b = results[-1][1], results[-1][2]
            print(f"[{i}/{len(players)}] {p.label} ({p.club}) -> {st}"
                  + (f" : {b.name} / {b.club} / {b.age} ans  [{b.score}]" if b and st == "OK" else ""))
        except RuntimeError as e:
            print(f"ERREUR bloquante : {e}")
            break
        except Exception as e:
            results.append((p, "ERREUR", None, None, repr(e)))
            print(f"[{i}/{len(players)}] {p.label} -> ERREUR {e!r}")
        if i % 25 == 0:
            api.save_cache()

    # Conflits : une même fiche pour plusieurs lignes Excel
    by_url = {}
    for p, st, b, _, _ in results:
        if st in ("OK", "OVERRIDE"):
            by_url.setdefault(b.url, []).append(p.id)
    final = []
    for p, st, b, s2, why in results:
        if st == "OK":
            others = (set(by_url[b.url]) | taken.get(b.url, set())) - {p.id}
            if others:
                st, why = "CONFLIT", f"même fiche que ID {sorted(others)}"
        final.append((p, st, b, s2, why))

    # Attributs + écriture
    written = 0
    for p, st, b, _, _ in final:
        if st not in ("OK", "OVERRIDE") or stop["flag"] and b.url not in api.cache["profile"]:
            continue
        try:
            attrs = api.attributes(b.url)
        except RuntimeError as e:
            print(f"ERREUR fiche {b.url} : {e}")
            break
        for name in ATTRIBUTES:
            ws.cell(p.row, headers[name]).value = attrs.get(name)
        ws.cell(p.row, url_col).value = b.url
        write_extras(ws, p.row, headers, api.cache["extra"].get(b.url))
        ws.cell(p.row, headers[ABILITY_COL]).value = b.ability
        if p.rating is not None and b.ability is not None:
            note_fm = NOTE_FM_WEIGHT_ABILITY * b.ability + NOTE_FM_WEIGHT_MOYENNE * p.rating
            ws.cell(p.row, headers[NOTE_FM_COL]).value = round(note_fm, 1)
        written += 1
    api.save_cache()

    # Rapport (ajouté à l'existant, une ligne par joueur traité)
    new_file = not report_path.exists()
    with report_path.open("a", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        if new_file:
            w.writerow(["date", "ID", "Prénom", "Nom", "Club", "Nationalité", "Âge", "Poste", "statut", "raison",
                        "score", "url", "fm_nom", "fm_club", "fm_nat", "fm_age", "fm_postes", "détail",
                        "2e_score", "2e_url", "2e_nom", "2e_club", "2e_age"])
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        for p, st, b, s2, why in final:
            w.writerow([now, p.id, p.first, p.last, p.club, p.nat, p.age, p.pos, st, why,
                        b.score if b else "", b.url if b else "", b.name if b else "", b.club if b else "",
                        b.nat if b else "", b.age if b else "", " ".join(sorted(b.positions)) if b else "",
                        " | ".join(b.details) if b else "",
                        s2.score if s2 else "", s2.url if s2 else "", s2.name if s2 else "",
                        s2.club if s2 else "", s2.age if s2 else ""])

    counts = {}
    for _, st, *_ in final:
        counts[st] = counts.get(st, 0) + 1
    print("\nBilan :", ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))
    print(f"Rapport : {report_path}")

    if args.dry_run:
        print("Dry-run : Excel non modifié.")
        return
    if written == 0:
        print("Rien à écrire.")
        return
    backup = folder / f"{xlsx.stem}_backup_{datetime.now():%Y%m%d_%H%M%S}{xlsx.suffix}"
    shutil.copy2(xlsx, backup)
    try:
        wb.save(xlsx)
    except PermissionError:
        sys.exit(f"Impossible d'écrire {xlsx.name} : ferme-le dans Excel puis relance (le cache évite de tout refaire).")
    print(f"{written} joueurs écrits dans {xlsx.name} (sauvegarde : {backup.name})")


if __name__ == "__main__":
    main()

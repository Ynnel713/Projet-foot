"""Couleurs de maillot extraites des packs de kits FM Slovakia (chantier kits-maillots, ticket KM-01).

    uv run python -m scripts.extract_kit_colors <dossier des .zip> <sortie.json> [planche.png] [--module <fichier.py>]

Lit chaque archive `<Pays> - <Championnat>.zip` SANS l'extraire, retient pour chaque maillot (1 domicile, 2 extérieur,
3 troisième ; dossiers `alt` ignorés) deux couleurs : la principale (plus grande surface du maillot) et la secondaire
(plus grande surface nettement différente de la principale). Les images ne sont ni copiées ni versionnées : seules les
couleurs le seront (dans `ligue1sim/kits.py`, ticket KM-02). Le JSON associe chaque maillot à son club du jeu par la table
`CLUB_BY_STEM` (nom de fichier -> nom exact de la colonne « Club »).

Packs : « FC'12 kitpack » créés par einherjer83 pour FM Slovakia (crédit demandé par leur readme).

Méthode (déterministe, sans hasard) : maillot réduit à 140 px, pixels opaques seulement, palette médiane à 16 couleurs,
puis fusion des teintes proches (ombrage d'un même tissu, écart CIELAB < `MERGE_DE`) pondérée par la surface.
"""

from __future__ import annotations

import io
import json
import math
import re
import sys
import zipfile
from pathlib import Path

MERGE_DE = 22.0  # écart CIELAB (CIE76) sous lequel deux teintes sont le même tissu ombré
SECONDARY_DE = 30.0  # écart minimal entre principale et secondaire
SECONDARY_MIN_SHARE = 0.04  # surface minimale de la secondaire (part des pixels du maillot)
SAME_HUE_DEG = 25.0  # deux teintes à moins de 25° sont la même couleur...
SAME_HUE_DL = 35.0  # ... sauf écart de clarté d'au moins 35 (marine / ciel)
KIT_SLOTS = {"1": "home", "2": "away", "3": "third"}
_FILE = re.compile(r"^(?P<stem>.+?)_?(?P<slot>[123])\.png$", re.IGNORECASE)


def _lab(rgb: tuple[int, int, int]) -> tuple[float, float, float]:
    def lin(c: float) -> float:
        c /= 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (lin(c) for c in rgb)
    x = (0.4124 * r + 0.3576 * g + 0.1805 * b) / 0.95047
    y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    z = (0.0193 * r + 0.1192 * g + 0.9505 * b) / 1.08883

    def f(t: float) -> float:
        return t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116

    fx, fy, fz = f(x), f(y), f(z)
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)


def _de(a: tuple[int, int, int], b: tuple[int, int, int]) -> float:
    return math.dist(_lab(a), _lab(b))


def _hex(rgb: tuple[int, int, int]) -> str:
    return "#%02x%02x%02x" % rgb


_TEXT_CHUNKS = {b"tEXt", b"zTXt", b"iTXt"}


def _without_text(png: bytes) -> bytes:
    """PNG sans ses blocs de texte (métadonnées d'éditeur, parfois énormes, que Pillow refuse par sécurité) : les
    pixels ne sont pas touchés, et la limite de sécurité de Pillow reste en place."""
    if png[:8] != b"\x89PNG\r\n\x1a\n":
        return png
    out, pos = [png[:8]], 8
    while pos + 8 <= len(png):
        length = int.from_bytes(png[pos:pos + 4], "big")
        end = pos + 12 + length
        if png[pos + 4:pos + 8] not in _TEXT_CHUNKS:
            out.append(png[pos:end])
        pos = end
    return b"".join(out)


def kit_colors(png: bytes) -> tuple[str, str]:
    """(principale, secondaire) d'une image de maillot ; secondaire = principale si le maillot est uni."""
    from PIL import Image  # importé ici : le module se charge sans Pillow (génération du module, tests de données)

    im = Image.open(io.BytesIO(_without_text(png))).convert("RGBA")
    im.thumbnail((140, 140))
    pixels = [p[:3] for p in im.get_flattened_data() if p[3] > 200]
    strip = Image.new("RGB", (len(pixels), 1))
    strip.putdata(pixels)
    q = strip.quantize(colors=16, method=Image.Quantize.MEDIANCUT)
    palette = q.getpalette()
    total = len(pixels)
    swatches = [[c / total, tuple(palette[i * 3:i * 3 + 3])] for c, i in sorted(q.getcolors(), reverse=True)]
    groups: list[dict] = []  # {part, graine, teinte représentative}
    for share, rgb in swatches:
        for g in groups:
            if _de(g["seed"], rgb) < MERGE_DE:
                g["share"] += share
                g["members"].append((share, rgb))
                break
        else:
            groups.append({"share": share, "seed": rgb, "members": [(share, rgb)]})
    for g in groups:
        # teinte représentative : la plus franche (surface × saturation) plutôt que la moyenne, que l'ombrage du rendu
        # assombrit et que les motifs mêlés (fines rayures) délavent
        g["rgb"] = max(g["members"], key=lambda m: m[0] * (1 + _chroma(m[1]) / 40))[1]
    groups.sort(key=lambda g: -g["share"])
    primary = groups[0]["rgb"]
    secondary = next((g["rgb"] for g in groups[1:] if g["share"] >= SECONDARY_MIN_SHARE and _distinct(g["rgb"], primary)),
                     primary)
    return _hex(primary), _hex(secondary)


def _chroma(rgb: tuple[int, int, int]) -> float:
    _, a, b = _lab(rgb)
    return math.hypot(a, b)


def _distinct(cand: tuple[int, int, int], primary: tuple[int, int, int]) -> bool:
    """Vraie seconde couleur, pas un reflet de la principale : assez loin en CIELAB, et si les deux ont la même teinte
    (rouge et rose, par exemple), il faut un grand écart de clarté (bleu marine et bleu ciel)."""
    if _de(cand, primary) < SECONDARY_DE:
        return False
    (l1, a1, b1), (l2, a2, b2) = _lab(cand), _lab(primary)
    if math.hypot(a1, b1) > 15 and math.hypot(a2, b2) > 15:
        dh = abs(math.degrees(math.atan2(b1, a1) - math.atan2(b2, a2))) % 360
        if min(dh, 360 - dh) < SAME_HUE_DEG and abs(l1 - l2) < SAME_HUE_DL:
            return False
    return True


def read_packs(folder: Path) -> dict[str, dict[str, dict[str, list[str]]]]:
    """{pack: {nom de fichier: {home|away|third: [principale, secondaire]}}}, dans l'ordre alphabétique."""
    out: dict[str, dict[str, dict[str, list[str]]]] = {}
    for archive in sorted(folder.glob("*.zip")):
        kits: dict[str, dict[str, list[str]]] = {}
        with zipfile.ZipFile(archive) as z:
            for name in sorted(z.namelist()):
                parts = name.split("/")
                if len(parts) != 2:  # sous-dossiers (`alt`, `Alt`, `alternatives`) ignorés
                    continue
                m = _FILE.match(parts[1])
                if not m:
                    continue
                kits.setdefault(m["stem"].lower(), {})[KIT_SLOTS[m["slot"]]] = list(kit_colors(z.read(name)))
        out[archive.stem] = kits
    return out


def contact_sheet(folder: Path, packs: dict, target: Path) -> None:
    """Planche de contrôle locale (jamais versionnée : elle contient les images) : maillot domicile réduit, puis les
    pastilles extraites domicile / extérieur / troisième."""
    rows = [(pack, stem, kits) for pack, stems in packs.items() for stem, kits in stems.items()]
    from PIL import Image, ImageDraw

    cols, cell_w, cell_h = 6, 220, 96
    sheet = Image.new("RGB", (cols * cell_w, math.ceil(len(rows) / cols) * cell_h), "white")
    draw = ImageDraw.Draw(sheet)
    archives = {a.stem: zipfile.ZipFile(a) for a in folder.glob("*.zip")}
    for k, (pack, stem, kits) in enumerate(rows):
        x, y = (k % cols) * cell_w, (k // cols) * cell_h
        z = archives[pack]
        home = next((n for n in z.namelist() if n.count("/") == 1 and _FILE.match(n.split("/")[1])
                     and _FILE.match(n.split("/")[1])["stem"].lower() == stem
                     and _FILE.match(n.split("/")[1])["slot"] == "1"), None)
        if home:
            im = Image.open(io.BytesIO(_without_text(z.read(home)))).convert("RGBA")
            im.thumbnail((72, 72))
            sheet.paste(im, (x + 2, y + 2), im)
        for j, slot in enumerate(("home", "away", "third")):
            if slot in kits:
                for i, color in enumerate(kits[slot]):
                    draw.rectangle([x + 80 + j * 44 + i * 20, y + 10, x + 80 + j * 44 + i * 20 + 18, y + 50], fill=color,
                                   outline="#888888")
        draw.text((x + 80, y + 58), stem[:22], fill="black")
        draw.text((x + 80, y + 72), (", ".join(clubs_of(f"{pack}/{stem}")) or "?")[:22], fill="#555555")
    sheet.save(target)


def clubs_of(key: str) -> tuple[str, ...]:
    """Club(s) du jeu associés au maillot `<pack>/<stem>` (aucun si absent de la table)."""
    target = CLUB_BY_STEM.get(key, ())
    return (target,) if isinstance(target, str) else target


# Nom de fichier (`<pack>/<stem>`) -> club(s) du jeu (colonne « Club » de data/joueurs.xlsx) : correspondance automatique
# relue à la main (ticket KM-01). Absents des données, donc ignorés : cremonese, nac (NAC Breda), avs, oviedo, eyupspor,
# karagumruk. Heidenheim figure deux fois dans les données. Sélections : les 129 du jeu (ticket KM-03).
CLUB_BY_STEM: dict[str, str | tuple[str, ...]] = {
    # Belgium - Jupiler Pro League
    "Belgium_-_Jupiler_Pro_League/anderlecht": "RSC Anderlecht",
    "Belgium_-_Jupiler_Pro_League/antwerp": "Royal Antwerp",
    "Belgium_-_Jupiler_Pro_League/cercle_brugge": "Cercle Brugge",
    "Belgium_-_Jupiler_Pro_League/charleroi": "Royal Charleroi SC",
    "Belgium_-_Jupiler_Pro_League/club_brugge": "Club Brugge KV",
    "Belgium_-_Jupiler_Pro_League/dender": "FCV Dender EH",
    "Belgium_-_Jupiler_Pro_League/genk": "KRC Genk",
    "Belgium_-_Jupiler_Pro_League/gent": "KAA Gent",
    "Belgium_-_Jupiler_Pro_League/la_louviere": "RAAL La Louvière",
    "Belgium_-_Jupiler_Pro_League/mechelen": "KV Mechelen",
    "Belgium_-_Jupiler_Pro_League/oh_leuven": "Oud-Heverlee Leuven",
    "Belgium_-_Jupiler_Pro_League/standard_liege": "Standard Liège",
    "Belgium_-_Jupiler_Pro_League/stvv": "Saint Trond",
    "Belgium_-_Jupiler_Pro_League/unionsg": "Union Saint-Gilloise",
    "Belgium_-_Jupiler_Pro_League/westerlo": "KVC Westerlo",
    "Belgium_-_Jupiler_Pro_League/zulte_waregem": "Zulte Waregem",
    # England - Championship
    "England_-_Championship/birmingham": "Birmingham City",
    "England_-_Championship/blackburn": "Blackburn Rovers",
    "England_-_Championship/bristolcity": "Bristol City",
    "England_-_Championship/charlton": "Charlton Athletic",
    "England_-_Championship/coventry": "Coventry City",
    "England_-_Championship/derby": "Derby County",
    "England_-_Championship/hull": "Hull City",
    "England_-_Championship/ipswich": "Ipswich Town",
    "England_-_Championship/leicester": "Leicester City",
    "England_-_Championship/middlesbrough": "Middlesbrough FC",
    "England_-_Championship/millwall": "Millwall FC",
    "England_-_Championship/norwich": "Norwich City",
    "England_-_Championship/oxford": "Oxford United",
    "England_-_Championship/portsmouth": "Portsmouth FC",
    "England_-_Championship/preston": "Preston North End",
    "England_-_Championship/qpr": "Queens Park Rangers",
    "England_-_Championship/sheffieldutd": "Sheffield United",
    "England_-_Championship/sheffieldwed": "Sheffield Wednesday",
    "England_-_Championship/southampton": "Southampton FC",
    "England_-_Championship/stoke": "Stoke City",
    "England_-_Championship/swansea": "Swansea City",
    "England_-_Championship/watford": "Watford FC",
    "England_-_Championship/wba": "West Bromwich Albion",
    "England_-_Championship/wrexham": "Wrexham AFC",
    # England - Premier League
    "England_-_Premier_League/arsenal": "Arsenal FC",
    "England_-_Premier_League/aston_villa": "Aston Villa",
    "England_-_Premier_League/bournemouth": "AFC Bournemouth",
    "England_-_Premier_League/brentford": "Brentford FC",
    "England_-_Premier_League/brighton": "Brighton & Hove Albion",
    "England_-_Premier_League/burnley": "Burnley FC",
    "England_-_Premier_League/chelsea": "Chelsea FC",
    "England_-_Premier_League/crystal_palace": "Crystal Palace",
    "England_-_Premier_League/everton": "Everton FC",
    "England_-_Premier_League/forest": "Nottingham Forest",
    "England_-_Premier_League/fulham": "Fulham FC",
    "England_-_Premier_League/leeds": "Leeds United",
    "England_-_Premier_League/liverpool": "Liverpool FC",
    "England_-_Premier_League/man_city": "Manchester City",
    "England_-_Premier_League/manunited": "Manchester United",
    "England_-_Premier_League/newcastle": "Newcastle United",
    "England_-_Premier_League/sunderland": "Sunderland AFC",
    "England_-_Premier_League/tottenham": "Tottenham Hotspur",
    "England_-_Premier_League/west_ham": "West Ham United",
    "England_-_Premier_League/wolves": "Wolverhampton Wanderers",
    # France - Ligue 1
    "France_-_Ligue_1/angers": "Angers SCO",
    "France_-_Ligue_1/auxerre": "AJ Auxerre",
    "France_-_Ligue_1/brest": "Stade Brestois 29",
    "France_-_Ligue_1/havre": "Le Havre AC",
    "France_-_Ligue_1/lens": "RC Lens",
    "France_-_Ligue_1/lille": "LOSC Lille",
    "France_-_Ligue_1/lorient": "FC Lorient",
    "France_-_Ligue_1/lyon": "Olympique Lyon",
    "France_-_Ligue_1/metz": "FC Metz",
    "France_-_Ligue_1/monaco": "AS Monaco",
    "France_-_Ligue_1/nantes": "FC Nantes",
    "France_-_Ligue_1/nice": "OGC Nice",
    "France_-_Ligue_1/olympique_marseille": "Olympique Marseille",
    "France_-_Ligue_1/paris": "Paris FC",
    "France_-_Ligue_1/psg": "Paris Saint-Germain",
    "France_-_Ligue_1/rennes": "Stade Rennais FC",
    "France_-_Ligue_1/strasbourg": "RC Strasbourg Alsace",
    "France_-_Ligue_1/toulouse": "FC Toulouse",
    # Germany - Bundesliga
    "Germany_-_Bundesliga/augsburg": "FC Augsburg",
    "Germany_-_Bundesliga/bayern": "Bayern Munich",
    "Germany_-_Bundesliga/borussia_gladbach": "Borussia Mönchengladbach",
    "Germany_-_Bundesliga/dortmund": "Borussia Dortmund",
    "Germany_-_Bundesliga/eintracht_frankfurt": "Eintracht Frankfurt",
    "Germany_-_Bundesliga/freiburg": "SC Freiburg",
    "Germany_-_Bundesliga/heidenheim": ("1.FC Heidenheim 1846", "Heidenheim"),
    "Germany_-_Bundesliga/hoffenheim": "TSG 1899 Hoffenheim",
    "Germany_-_Bundesliga/hsv": "Hamburger SV",
    "Germany_-_Bundesliga/koln": "1.FC Köln",
    "Germany_-_Bundesliga/leverkusen": "Bayer 04 Leverkusen",
    "Germany_-_Bundesliga/mainz": "1.FSV Mainz 05",
    "Germany_-_Bundesliga/rb_leipzig": "RB Leipzig",
    "Germany_-_Bundesliga/st_pauli": "FC St. Pauli",
    "Germany_-_Bundesliga/stuttgart": "VfB Stuttgart",
    "Germany_-_Bundesliga/union_berlin": "1.FC Union Berlin",
    "Germany_-_Bundesliga/werder_bremen": "SV Werder Bremen",
    "Germany_-_Bundesliga/wolfsburg": "VfL Wolfsburg",
    # Italy - Serie A
    "Italy_-_Serie_A/atalanta_bergamasca": "Atalanta BC",
    "Italy_-_Serie_A/bologna": "Bologna FC 1909",
    "Italy_-_Serie_A/cagliari": "Cagliari Calcio",
    "Italy_-_Serie_A/como": "Como 1907",
    "Italy_-_Serie_A/fiorentina": "ACF Fiorentina",
    "Italy_-_Serie_A/genoa": "Genoa CFC",
    "Italy_-_Serie_A/hellas": "Hellas Verona",
    "Italy_-_Serie_A/internazionale_milano": "Inter Milan",
    "Italy_-_Serie_A/juventus": "Juventus FC",
    "Italy_-_Serie_A/lazio": "SS Lazio",
    "Italy_-_Serie_A/lecce": "US Lecce",
    "Italy_-_Serie_A/milan": "AC Milan",
    "Italy_-_Serie_A/napoli": "SSC Napoli",
    "Italy_-_Serie_A/parma": "Parma Calcio 1913",
    "Italy_-_Serie_A/pisa": "Pisa Sporting Club",
    "Italy_-_Serie_A/roma": "AS Roma",
    "Italy_-_Serie_A/sassuolo": "US Sassuolo",
    "Italy_-_Serie_A/torino": "Torino FC",
    "Italy_-_Serie_A/udinese": "Udinese Calcio",
    # Netherlands - Eredivisie
    "Netherlands_-_Eredivisie/ajax": "Ajax Amsterdam",
    "Netherlands_-_Eredivisie/az": "AZ Alkmaar",
    "Netherlands_-_Eredivisie/excelsior": "Excelsior Rotterdam",
    "Netherlands_-_Eredivisie/feyenoord": "Feyenoord Rotterdam",
    "Netherlands_-_Eredivisie/fortunasittard": "Fortuna Sittard",
    "Netherlands_-_Eredivisie/gaeagles": "Go Ahead Eagles",
    "Netherlands_-_Eredivisie/groningen": "FC Groningen",
    "Netherlands_-_Eredivisie/heerenveen": "SC Heerenveen",
    "Netherlands_-_Eredivisie/heracles": "Heracles Almelo",
    "Netherlands_-_Eredivisie/nec": "NEC Nijmegen",
    "Netherlands_-_Eredivisie/psv": "PSV Eindhoven",
    "Netherlands_-_Eredivisie/sparta_rotterdam": "Sparta Rotterdam",
    "Netherlands_-_Eredivisie/telstar": "SC Telstar",
    "Netherlands_-_Eredivisie/twente": "FC Twente Enschede",
    "Netherlands_-_Eredivisie/utrecht": "FC Utrecht",
    "Netherlands_-_Eredivisie/volendam": "FC Volendam",
    "Netherlands_-_Eredivisie/zwolle": "PEC Zwolle",
    # Portugal - Primeira Liga
    "Portugal_-_Primeira_Liga/alverca": "FC Alverca",
    "Portugal_-_Primeira_Liga/arouca": "FC Arouca",
    "Portugal_-_Primeira_Liga/benfica": "SL Benfica",
    "Portugal_-_Primeira_Liga/braga": "SC Braga",
    "Portugal_-_Primeira_Liga/casa_pia": "Casa Pia AC",
    "Portugal_-_Primeira_Liga/estoril": "GD Estoril Praia",
    "Portugal_-_Primeira_Liga/estrela_amadora": "CF Estrela Amadora",
    "Portugal_-_Primeira_Liga/famalicao": "FC Famalicão",
    "Portugal_-_Primeira_Liga/gilvicente": "Gil Vicente FC",
    "Portugal_-_Primeira_Liga/guimaraes": "Vitória Guimarães SC",
    "Portugal_-_Primeira_Liga/moreirense": "Moreirense FC",
    "Portugal_-_Primeira_Liga/nacional": "CD Nacional",
    "Portugal_-_Primeira_Liga/porto": "FC Porto",
    "Portugal_-_Primeira_Liga/rio_ave": "Rio Ave FC",
    "Portugal_-_Primeira_Liga/santa_clara": "CD Santa Clara",
    "Portugal_-_Primeira_Liga/sporting": "Sporting CP",
    "Portugal_-_Primeira_Liga/tondela": "CD Tondela",
    # Spain - La Liga
    "Spain_-_La_Liga/celta": "Celta de Vigo",
    "Spain_-_La_Liga/alaves": "Deportivo Alavés",
    "Spain_-_La_Liga/athletic_bilbao": "Athletic Bilbao",
    "Spain_-_La_Liga/atletico_madrid": "Atlético de Madrid",
    "Spain_-_La_Liga/barcelona": "FC Barcelona",
    "Spain_-_La_Liga/betis": "Real Betis Balompié",
    "Spain_-_La_Liga/elche": "Elche CF",
    "Spain_-_La_Liga/espanol": "RCD Espanyol Barcelona",
    "Spain_-_La_Liga/getafe": "Getafe CF",
    "Spain_-_La_Liga/girona": "Girona FC",
    "Spain_-_La_Liga/levante": "Levante UD",
    "Spain_-_La_Liga/mallorca": "RCD Mallorca",
    "Spain_-_La_Liga/osasuna": "CA Osasuna",
    "Spain_-_La_Liga/rayo_vallecano": "Rayo Vallecano",
    "Spain_-_La_Liga/real_madrid": "Real Madrid",
    "Spain_-_La_Liga/real_sociedad": "Real Sociedad",
    "Spain_-_La_Liga/sevilla": "Sevilla FC",
    "Spain_-_La_Liga/valencia": "Valencia CF",
    "Spain_-_La_Liga/villarreal": "Villarreal CF",
    # Turkey - Superlig
    "Turkey_-_Superlig/alanyaspor": "Alanyaspor",
    "Turkey_-_Superlig/antalyaspor": "Antalyaspor",
    "Turkey_-_Superlig/basaksehir": "Basaksehir FK",
    "Turkey_-_Superlig/besiktas": "Besiktas JK",
    "Turkey_-_Superlig/fenerbahce": "Fenerbahce",
    "Turkey_-_Superlig/galatasaray": "Galatasaray",
    "Turkey_-_Superlig/gaziantep": "Gaziantep FK",
    "Turkey_-_Superlig/genclerbirligi": "Genclerbirligi Ankara",
    "Turkey_-_Superlig/goztepe": "Göztepe",
    "Turkey_-_Superlig/kasimpasa": "Kasimpasa",
    "Turkey_-_Superlig/kayserispor": "Kayserispor",
    "Turkey_-_Superlig/kocaelispor": "Kocaelispor",
    "Turkey_-_Superlig/konyaspor": "Konyaspor",
    "Turkey_-_Superlig/rizespor": "Caykur Rizespor",
    "Turkey_-_Superlig/samsunspor": "Samsunspor",
    "Turkey_-_Superlig/trabzonspor": "Trabzonspor",
    # Sélections nationales (ticket KM-03) : nom français du jeu, drapeau compris
    "Nations_-_AFC/australia": "🇦🇺 Australie",
    "Nations_-_AFC/china": "🇨🇳 Chine",
    "Nations_-_AFC/indonesia": "🇮🇩 Indonésie",
    "Nations_-_AFC/iran": "🇮🇷 Iran",
    "Nations_-_AFC/iraq": "🇮🇶 Irak",
    "Nations_-_AFC/japan": "🇯🇵 Japon",
    "Nations_-_AFC/jordan": "🇯🇴 Jordanie",
    "Nations_-_AFC/lebanon": "🇱🇧 Liban",
    "Nations_-_AFC/malaysia": "🇲🇾 Malaisie",
    "Nations_-_AFC/philippines": "🇵🇭 Philippines",
    "Nations_-_AFC/qatar": "🇶🇦 Qatar",
    "Nations_-_AFC/saudi": "🇸🇦 Arabie saoudite",
    "Nations_-_AFC/southkorea": "🇰🇷 Corée du Sud",
    "Nations_-_AFC/syria": "🇸🇾 Syrie",
    "Nations_-_AFC/thailand": "🇹🇭 Thaïlande",
    "Nations_-_AFC/uae": "🇦🇪 Émirats arabes unis",
    "Nations_-_AFC/uzbekistan": "🇺🇿 Ouzbékistan",
    "Nations_-_CAF/algeria": "🇩🇿 Algérie",
    "Nations_-_CAF/angola": "🇦🇴 Angola",
    "Nations_-_CAF/benin": "🇧🇯 Bénin",
    "Nations_-_CAF/burkina_faso": "🇧🇫 Burkina Faso",
    "Nations_-_CAF/burundi": "🇧🇮 Burundi",
    "Nations_-_CAF/cameroon": "🇨🇲 Cameroun",
    "Nations_-_CAF/cape_verde": "🇨🇻 Cap-Vert",
    "Nations_-_CAF/central_african_republic": "🇨🇫 République centrafricaine",
    "Nations_-_CAF/comoros": "🇰🇲 Comores",
    "Nations_-_CAF/congo": "🇨🇬 Congo",
    "Nations_-_CAF/dr_congo": "🇨🇩 RD Congo",
    "Nations_-_CAF/egypt": "🇪🇬 Égypte",
    "Nations_-_CAF/equatorial_guinea": "🇬🇶 Guinée équatoriale",
    "Nations_-_CAF/eritrea": "🇪🇷 Érythrée",
    "Nations_-_CAF/gabon": "🇬🇦 Gabon",
    "Nations_-_CAF/gambia": "🇬🇲 Gambie",
    "Nations_-_CAF/ghana": "🇬🇭 Ghana",
    "Nations_-_CAF/guinea": "🇬🇳 Guinée",
    "Nations_-_CAF/guinea_bissau": "🇬🇼 Guinée-Bissau",
    "Nations_-_CAF/ivory_coast": "🇨🇮 Côte d'Ivoire",
    "Nations_-_CAF/kenya": "🇰🇪 Kenya",
    "Nations_-_CAF/libya": "🇱🇾 Libye",
    "Nations_-_CAF/madagascar": "🇲🇬 Madagascar",
    "Nations_-_CAF/mali": "🇲🇱 Mali",
    "Nations_-_CAF/mauritania": "🇲🇷 Mauritanie",
    "Nations_-_CAF/morocco": "🇲🇦 Maroc",
    "Nations_-_CAF/mozambique": "🇲🇿 Mozambique",
    "Nations_-_CAF/niger": "🇳🇪 Niger",
    "Nations_-_CAF/nigeria": "🇳🇬 Nigeria",
    "Nations_-_CAF/rwanda": "🇷🇼 Rwanda",
    "Nations_-_CAF/senegal": "🇸🇳 Sénégal",
    "Nations_-_CAF/sierra_leone": "🇸🇱 Sierra Leone",
    "Nations_-_CAF/south_africa": "🇿🇦 Afrique du Sud",
    "Nations_-_CAF/sudan": "🇸🇩 Soudan",
    "Nations_-_CAF/tanzania": "🇹🇿 Tanzanie",
    "Nations_-_CAF/togo": "🇹🇬 Togo",
    "Nations_-_CAF/tunisia": "🇹🇳 Tunisie",
    "Nations_-_CAF/zambia": "🇿🇲 Zambie",
    "Nations_-_CAF/zimbabwe": "🇿🇼 Zimbabwe",
    "Nations_-_CONCACAF/canada": "🇨🇦 Canada",
    "Nations_-_CONCACAF/costa_rica": "🇨🇷 Costa Rica",
    "Nations_-_CONCACAF/curacao": "🇨🇼 Curaçao",
    "Nations_-_CONCACAF/dominican_republic": "🇩🇴 République dominicaine",
    "Nations_-_CONCACAF/guadeloupe": "🇬🇵 Guadeloupe",
    "Nations_-_CONCACAF/haiti": "🇭🇹 Haïti",
    "Nations_-_CONCACAF/honduras": "🇭🇳 Honduras",
    "Nations_-_CONCACAF/jamaica": "🇯🇲 Jamaïque",
    "Nations_-_CONCACAF/martinique": "🇲🇶 Martinique",
    "Nations_-_CONCACAF/mexico": "🇲🇽 Mexique",
    "Nations_-_CONCACAF/panama": "🇵🇦 Panama",
    "Nations_-_CONCACAF/puertorico": "🇵🇷 Porto Rico",
    "Nations_-_CONCACAF/suriname": "🇸🇷 Suriname",
    "Nations_-_CONCACAF/trinidad": "🇹🇹 Trinité-et-Tobago",
    "Nations_-_CONCACAF/usa": "🇺🇸 États-Unis",
    "Nations_-_CONMEBOL/argentina": "🇦🇷 Argentine",
    "Nations_-_CONMEBOL/bolivia": "🇧🇴 Bolivie",
    "Nations_-_CONMEBOL/brazil": "🇧🇷 Brésil",
    "Nations_-_CONMEBOL/chile": "🇨🇱 Chili",
    "Nations_-_CONMEBOL/colombia": "🇨🇴 Colombie",
    "Nations_-_CONMEBOL/ecuador": "🇪🇨 Équateur",
    "Nations_-_CONMEBOL/paraguay": "🇵🇾 Paraguay",
    "Nations_-_CONMEBOL/peru": "🇵🇪 Pérou",
    "Nations_-_CONMEBOL/uruguay": "🇺🇾 Uruguay",
    "Nations_-_CONMEBOL/venezuela": "🇻🇪 Venezuela",
    "Nations_-_OFC/newzealand": "🇳🇿 Nouvelle-Zélande",
    "Nations_-_UEFA/albania": "🇦🇱 Albanie",
    "Nations_-_UEFA/armenia": "🇦🇲 Arménie",
    "Nations_-_UEFA/austria": "🇦🇹 Autriche",
    "Nations_-_UEFA/azerbaijan": "🇦🇿 Azerbaïdjan",
    "Nations_-_UEFA/belarus": "🇧🇾 Biélorussie",
    "Nations_-_UEFA/belgium": "🇧🇪 Belgique",
    "Nations_-_UEFA/bosnia": "🇧🇦 Bosnie-Herzégovine",
    "Nations_-_UEFA/bulgaria": "🇧🇬 Bulgarie",
    "Nations_-_UEFA/croatia": "🇭🇷 Croatie",
    "Nations_-_UEFA/cyprus": "🇨🇾 Chypre",
    "Nations_-_UEFA/czech": "🇨🇿 République tchèque",
    "Nations_-_UEFA/denmark": "🇩🇰 Danemark",
    "Nations_-_UEFA/england": "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Angleterre",
    "Nations_-_UEFA/estonia": "🇪🇪 Estonie",
    "Nations_-_UEFA/finland": "🇫🇮 Finlande",
    "Nations_-_UEFA/france": "🇫🇷 France",
    "Nations_-_UEFA/georgia": "🇬🇪 Géorgie",
    "Nations_-_UEFA/germany": "🇩🇪 Allemagne",
    "Nations_-_UEFA/greece": "🇬🇷 Grèce",
    "Nations_-_UEFA/hungary": "🇭🇺 Hongrie",
    "Nations_-_UEFA/iceland": "🇮🇸 Islande",
    "Nations_-_UEFA/ireland": "🇮🇪 Irlande",
    "Nations_-_UEFA/israel": "🇮🇱 Israël",
    "Nations_-_UEFA/italy": "🇮🇹 Italie",
    "Nations_-_UEFA/kazakhstan": "🇰🇿 Kazakhstan",
    "Nations_-_UEFA/kosovo": "🇽🇰 Kosovo",
    "Nations_-_UEFA/lithuania": "🇱🇹 Lituanie",
    "Nations_-_UEFA/luxembourg": "🇱🇺 Luxembourg",
    "Nations_-_UEFA/montenegro": "🇲🇪 Monténégro",
    "Nations_-_UEFA/netherlands": "🇳🇱 Pays-Bas",
    "Nations_-_UEFA/north_macedonia": "🇲🇰 Macédoine du Nord",
    "Nations_-_UEFA/northern_ireland": "🇬🇧 Irlande du Nord",
    "Nations_-_UEFA/norway": "🇳🇴 Norvège",
    "Nations_-_UEFA/poland": "🇵🇱 Pologne",
    "Nations_-_UEFA/portugal": "🇵🇹 Portugal",
    "Nations_-_UEFA/romania": "🇷🇴 Roumanie",
    "Nations_-_UEFA/russia": "🇷🇺 Russie",
    "Nations_-_UEFA/scotland": "🏴󠁧󠁢󠁳󠁣󠁴󠁿 Écosse",
    "Nations_-_UEFA/serbia": "🇷🇸 Serbie",
    "Nations_-_UEFA/slovakia": "🇸🇰 Slovaquie",
    "Nations_-_UEFA/slovenia": "🇸🇮 Slovénie",
    "Nations_-_UEFA/spain": "🇪🇸 Espagne",
    "Nations_-_UEFA/sweden": "🇸🇪 Suède",
    "Nations_-_UEFA/switzerland": "🇨🇭 Suisse",
    "Nations_-_UEFA/turkey": "🇹🇷 Turquie",
    "Nations_-_UEFA/ukraine": "🇺🇦 Ukraine",
    "Nations_-_UEFA/wales": "🏴󠁧󠁢󠁷󠁬󠁳󠁿 Pays de Galles",
}


MODULE_HEADER = '''"""Couleurs de maillot réelles 2025/26 des clubs couverts par les packs de kits FM Slovakia (« FC'12 kitpack » par
einherjer83). FICHIER GÉNÉRÉ par `scripts/extract_kit_colors.py --module` (chantier kits-maillots, KM-02) : ne pas
modifier à la main, régénérer. Club -> (domicile principale, domicile secondaire, extérieur principale, extérieur
secondaire) ; fusionné dans `kits.CLUB_KIT`.
"""

from __future__ import annotations

EXTRACTED_KITS: dict[str, tuple[str, str, str | None, str | None]] = {
'''


def write_module(clubs: dict[str, dict[str, list[str]]], target: Path) -> None:
    """Module Python des couleurs extraites (domicile et extérieur), trié par club, fins de ligne LF."""
    lines = []
    for club, kits in sorted(clubs.items()):
        home, away = kits["home"], kits.get("away")
        a = f'"{away[0]}", "{away[1]}"' if away else "None, None"
        lines.append(f'    {json.dumps(club, ensure_ascii=False)}: ("{home[0]}", "{home[1]}", {a}),')
    target.write_text(MODULE_HEADER + "\n".join(lines) + "\n}\n", encoding="utf-8", newline="\n")


def main(argv: list[str]) -> int:
    module = None
    if "--module" in argv:
        i = argv.index("--module")
        module = Path(argv[i + 1])
        argv = argv[:i] + argv[i + 2:]
    folder, target = Path(argv[0]), Path(argv[1])
    packs = read_packs(folder)
    clubs = {club: kits for p, stems in packs.items() for s, kits in stems.items() for club in clubs_of(f"{p}/{s}")}
    target.write_text(json.dumps({"packs": packs, "clubs": dict(sorted(clubs.items()))}, ensure_ascii=False, indent=1),
                      encoding="utf-8")
    if module:
        write_module(clubs, module)
    if len(argv) > 2:
        contact_sheet(folder, packs, Path(argv[2]))
    print(f"{sum(len(s) for s in packs.values())} maillots lus, {len(clubs)} clubs associés -> {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

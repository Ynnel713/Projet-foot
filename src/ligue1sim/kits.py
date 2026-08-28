"""Icônes de maillot (SVG inline, sans dépendance externe) pour représenter
chaque club dans la vue "stade" (`app.py`), à la place d'un simple rond de
couleur.

Volontairement générique : silhouette de maillot dessinée à la main (aucun
écusson, aucun logo d'équipementier ni de sponsor) coloriée avec un jeu de
couleurs approximant l'identité visuelle du club (couleurs seules, non
protégées) -- pas une reproduction d'un maillot officiel précis.

Tous les clubs des 8 championnats simulables (Ligue 1, Premier League,
Bundesliga, LaLiga, Serie A, Eredivisie, Jupiler Pro League, Liga Portugal)
ont un kit dédié, plus quelques clubs notables d'"Autres clubs" (Fenerbahce,
Galatasaray, Shakhtar Donetsk, FK Bodø/Glimt, et les 6 clubs de la Ligue des
Champions sans championnat repris). Tout club non couvert retombe sur
`_DEFAULT_KIT` (gris neutre).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Kit:
    primary: str
    secondary: str
    pattern: str  # voir _PATTERN_BUILDERS


_DEFAULT_KIT = Kit(primary="#6b7280", secondary="#d1d5db", pattern="trim")

# Couleurs approximatives d'identité de club (pas une reproduction du maillot
# exact d'une saison donnée), clés = valeur exacte de la colonne "Club".
CLUB_KIT: dict[str, Kit] = {
    "Angers SCO": Kit("#111111", "#ffffff", "vertical_stripes"),
    "AJ Auxerre": Kit("#ffffff", "#0033a0", "trim"),
    "Stade Brestois 29": Kit("#da291c", "#ffffff", "halves"),
    "RC Lens": Kit("#c8102e", "#ffd100", "horizontal_stripes"),
    "Le Havre AC": Kit("#001a4b", "#6cace4", "trim"),
    "Le Mans FC": Kit("#d91e36", "#ffd200", "diagonal_sash"),
    "LOSC Lille": Kit("#c8102e", "#002f6c", "halves"),
    "FC Lorient": Kit("#f47920", "#111111", "trim"),
    "Olympique Lyon": Kit("#ffffff", "#0f3b82", "vertical_stripes"),
    "Olympique Marseille": Kit("#ffffff", "#2aabe2", "trim"),
    "AS Monaco": Kit("#e2001a", "#ffffff", "diagonal_sash"),
    "OGC Nice": Kit("#111111", "#ed1c24", "halves"),
    "Paris FC": Kit("#0c2340", "#ffffff", "solid"),
    "Paris Saint-Germain": Kit("#0a1a4a", "#da1a35", "center_stripe"),
    "Stade Rennais FC": Kit("#e2001a", "#111111", "vertical_stripes"),
    "RC Strasbourg Alsace": Kit("#1c3f94", "#ffffff", "trim"),
    "FC Toulouse": Kit("#6a1b9a", "#ffffff", "solid"),
    "ESTAC Troyes": Kit("#002b5c", "#f7941d", "trim"),

    # ---------------- Premier League ----------------
    "AFC Bournemouth": Kit("#da291c", "#000000", "vertical_stripes"),
    "Arsenal FC": Kit("#ef0107", "#ffffff", "trim"),
    "Aston Villa": Kit("#670e36", "#95bfe5", "trim"),
    "Brentford FC": Kit("#e30613", "#ffffff", "vertical_stripes"),
    "Brighton & Hove Albion": Kit("#0057b8", "#ffffff", "vertical_stripes"),
    "Chelsea FC": Kit("#034694", "#ffffff", "solid"),
    "Coventry City": Kit("#78d0f1", "#000000", "solid"),
    "Crystal Palace": Kit("#c4122e", "#1b458f", "vertical_stripes"),
    "Everton FC": Kit("#003399", "#ffffff", "solid"),
    "Fulham FC": Kit("#ffffff", "#000000", "trim"),
    "Hull City": Kit("#f5a623", "#000000", "vertical_stripes"),
    "Ipswich Town": Kit("#0044a9", "#ffffff", "trim"),
    "Leeds United": Kit("#ffffff", "#ffcd00", "trim"),
    "Liverpool FC": Kit("#c8102e", "#00b2a9", "trim"),
    "Manchester City": Kit("#6cabdd", "#ffffff", "trim"),
    "Manchester United": Kit("#da291c", "#000000", "trim"),
    "Newcastle United": Kit("#241f20", "#ffffff", "vertical_stripes"),
    "Nottingham Forest": Kit("#dd0000", "#ffffff", "trim"),
    "Sunderland AFC": Kit("#eb172b", "#ffffff", "vertical_stripes"),
    "Tottenham Hotspur": Kit("#ffffff", "#132257", "trim"),

    # ---------------- Bundesliga ----------------
    "1.FC Köln": Kit("#ffffff", "#ed1c24", "trim"),
    "1.FC Union Berlin": Kit("#eb1923", "#ffffff", "halves"),
    "1.FSV Mainz 05": Kit("#c4122f", "#ffffff", "trim"),
    "Bayer 04 Leverkusen": Kit("#e32221", "#000000", "trim"),
    "Bayern Munich": Kit("#dc052d", "#0066b2", "trim"),
    "Borussia Dortmund": Kit("#fde100", "#000000", "horizontal_stripes"),
    "Borussia Mönchengladbach": Kit("#ffffff", "#000000", "vertical_stripes"),
    "Eintracht Frankfurt": Kit("#000000", "#e1000f", "trim"),
    "FC Augsburg": Kit("#ba3733", "#00893a", "trim"),
    "FC Schalke 04": Kit("#004c9b", "#ffffff", "vertical_stripes"),
    "Hamburger SV": Kit("#0f1e3d", "#ffffff", "trim"),
    "RB Leipzig": Kit("#ffffff", "#dd0741", "trim"),
    "SC Freiburg": Kit("#000000", "#e2001a", "trim"),
    "SC Paderborn 07": Kit("#003399", "#000000", "trim"),
    "SV 07 Elversberg": Kit("#000000", "#ffffff", "halves"),
    "SV Werder Bremen": Kit("#1d9053", "#ffffff", "vertical_stripes"),
    "TSG 1899 Hoffenheim": Kit("#1961b5", "#ffffff", "trim"),
    "VfB Stuttgart": Kit("#ffffff", "#e32219", "trim"),

    # ---------------- LaLiga ----------------
    "Athletic Bilbao": Kit("#ee2523", "#ffffff", "vertical_stripes"),
    "Atlético de Madrid": Kit("#cb3524", "#ffffff", "vertical_stripes"),
    "CA Osasuna": Kit("#d91a21", "#000080", "trim"),
    "Celta de Vigo": Kit("#8ac3ee", "#ffffff", "trim"),
    "Deportivo A Coruña": Kit("#0055a4", "#ffffff", "vertical_stripes"),
    "Deportivo Alavés": Kit("#0f4c9c", "#ffffff", "vertical_stripes"),
    "Elche CF": Kit("#006633", "#ffffff", "vertical_stripes"),
    "FC Barcelona": Kit("#a50044", "#004d98", "vertical_stripes"),
    "Getafe CF": Kit("#005ca9", "#ffffff", "trim"),
    "Levante UD": Kit("#12228c", "#c8102e", "halves"),
    "Málaga CF": Kit("#1560bd", "#ffffff", "trim"),
    "RCD Espanyol Barcelona": Kit("#0a4c93", "#ffffff", "vertical_stripes"),
    "Racing Santander": Kit("#01884c", "#ffffff", "vertical_stripes"),
    "Rayo Vallecano": Kit("#ffffff", "#e2001a", "diagonal_sash"),
    "Real Betis Balompié": Kit("#00954c", "#ffffff", "vertical_stripes"),
    "Real Madrid": Kit("#fefefe", "#ffd700", "trim"),
    "Real Sociedad": Kit("#0067b1", "#ffffff", "vertical_stripes"),
    "Sevilla FC": Kit("#ffffff", "#d4021d", "trim"),
    "Valencia CF": Kit("#ffffff", "#ee3524", "trim"),
    "Villarreal CF": Kit("#ffe667", "#005187", "trim"),

    # ---------------- Serie A ----------------
    "AC Milan": Kit("#fb090b", "#000000", "vertical_stripes"),
    "AC Monza": Kit("#d91a21", "#ffffff", "halves"),
    "ACF Fiorentina": Kit("#7c2a8d", "#ffffff", "solid"),
    "AS Roma": Kit("#8e1f2f", "#f0bc42", "trim"),
    "Atalanta BC": Kit("#1e71b8", "#000000", "vertical_stripes"),
    "Bologna FC 1909": Kit("#a61e22", "#1b3f8b", "vertical_stripes"),
    "Cagliari Calcio": Kit("#8b1e3f", "#002f6c", "vertical_stripes"),
    "Como 1907": Kit("#003d82", "#ffffff", "trim"),
    "Frosinone Calcio": Kit("#ffe100", "#003da5", "halves"),
    "Genoa CFC": Kit("#c8102e", "#002b5c", "vertical_stripes"),
    "Inter Milan": Kit("#0068a8", "#000000", "vertical_stripes"),
    "Juventus FC": Kit("#ffffff", "#000000", "vertical_stripes"),
    "Parma Calcio 1913": Kit("#ffe100", "#002f6c", "center_stripe"),
    "SS Lazio": Kit("#87ceeb", "#ffffff", "trim"),
    "SSC Napoli": Kit("#12a0d7", "#ffffff", "trim"),
    "Torino FC": Kit("#7b1e3a", "#ffffff", "trim"),
    "US Lecce": Kit("#ffe100", "#c8102e", "vertical_stripes"),
    "US Sassuolo": Kit("#00a650", "#000000", "vertical_stripes"),
    "Udinese Calcio": Kit("#000000", "#ffffff", "vertical_stripes"),
    "Venezia FC": Kit("#1b5e20", "#000000", "halves"),

    # ---------------- Eredivisie ----------------
    "ADO Den Haag": Kit("#ffd200", "#00843d", "halves"),
    "AZ Alkmaar": Kit("#d2122e", "#ffffff", "trim"),
    "Ajax Amsterdam": Kit("#ffffff", "#d2122e", "center_stripe"),
    "Excelsior Rotterdam": Kit("#c8102e", "#000000", "vertical_stripes"),
    "FC Groningen": Kit("#00a651", "#ffffff", "vertical_stripes"),
    "FC Twente Enschede": Kit("#d2122e", "#ffffff", "trim"),
    "FC Utrecht": Kit("#ed1c24", "#ffffff", "vertical_stripes"),
    "Feyenoord Rotterdam": Kit("#c8102e", "#ffffff", "halves"),
    "Fortuna Sittard": Kit("#ffe100", "#00843d", "halves"),
    "Go Ahead Eagles": Kit("#ed1c24", "#ffe100", "halves"),
    "NEC Nijmegen": Kit("#c8102e", "#000000", "halves"),
    "PEC Zwolle": Kit("#002f6c", "#ffffff", "trim"),
    "PSV Eindhoven": Kit("#ed1c24", "#ffffff", "trim"),
    "SC Cambuur": Kit("#005bac", "#ffffff", "trim"),
    "SC Heerenveen": Kit("#0033a0", "#ffffff", "trim"),
    "SC Telstar": Kit("#ffffff", "#000000", "trim"),
    "Sparta Rotterdam": Kit("#c8102e", "#ffffff", "halves"),
    "Willem II": Kit("#ed1c24", "#ffffff", "vertical_stripes"),

    # ---------------- Jupiler Pro League ----------------
    "Cercle Brugge": Kit("#00693e", "#000000", "vertical_stripes"),
    "Club Brugge KV": Kit("#0e1c3f", "#67aaf0", "vertical_stripes"),
    "KAA Gent": Kit("#002f6c", "#ffffff", "halves"),
    "KRC Genk": Kit("#0f5ca8", "#ffffff", "trim"),
    "KV Kortrijk": Kit("#ed1c24", "#ffffff", "halves"),
    "KV Mechelen": Kit("#ffe100", "#c8102e", "halves"),
    "KVC Westerlo": Kit("#ffe100", "#000000", "vertical_stripes"),
    "Lommel SK": Kit("#00539f", "#f47920", "trim"),
    "Oud-Heverlee Leuven": Kit("#003da5", "#ffe100", "trim"),
    "RAAL La Louvière": Kit("#5b2a86", "#000000", "trim"),
    "RSC Anderlecht": Kit("#4b2e83", "#ffffff", "trim"),
    "Royal Antwerp": Kit("#c8102e", "#ffffff", "vertical_stripes"),
    "Royal Charleroi SC": Kit("#000000", "#ffffff", "trim"),
    "SK Beveren": Kit("#ffe100", "#002f6c", "halves"),
    "Saint Trond": Kit("#c8102e", "#ffffff", "halves"),
    "Standard Liège": Kit("#d2122e", "#ffffff", "trim"),
    "Union Saint-Gilloise": Kit("#ffe100", "#002f6c", "trim"),
    "Zulte Waregem": Kit("#ffe100", "#000000", "trim"),

    # ---------------- Liga Portugal ----------------
    "Académico de Viseu": Kit("#00693e", "#ffffff", "trim"),
    "CD Nacional": Kit("#000000", "#c8102e", "trim"),
    "CD Santa Clara": Kit("#00693e", "#ffffff", "vertical_stripes"),
    "CF Estrela Amadora": Kit("#c8102e", "#ffffff", "trim"),
    "CS Marítimo": Kit("#00693e", "#c8102e", "halves"),
    "Casa Pia AC": Kit("#00693e", "#000000", "vertical_stripes"),
    "FC Alverca": Kit("#ffffff", "#002f6c", "trim"),
    "FC Arouca": Kit("#ffe100", "#000000", "halves"),
    "FC Famalicão": Kit("#ffffff", "#c8102e", "trim"),
    "FC Porto": Kit("#003da5", "#ffffff", "vertical_stripes"),
    "GD Estoril Praia": Kit("#ffe100", "#000000", "trim"),
    "Gil Vicente FC": Kit("#c8102e", "#ffffff", "vertical_stripes"),
    "Moreirense FC": Kit("#00693e", "#ffffff", "halves"),
    "Rio Ave FC": Kit("#00693e", "#ffffff", "vertical_stripes"),
    "SC Braga": Kit("#c8102e", "#ffffff", "trim"),
    "SL Benfica": Kit("#e30613", "#ffffff", "trim"),
    "Sporting CP": Kit("#00693e", "#ffffff", "halves"),
    "Vitória Guimarães SC": Kit("#ffffff", "#000000", "vertical_stripes"),

    # ---------------- Autres clubs notables (Ligue des Champions, etc.) ----------------
    "Fenerbahce": Kit("#ffe100", "#002157", "halves"),
    "Galatasaray": Kit("#a90432", "#fdb913", "vertical_stripes"),
    "Shakhtar Donetsk": Kit("#f47920", "#000000", "vertical_stripes"),
    "FK Bodø/Glimt": Kit("#ffe100", "#000000", "trim"),
    "Slavia Prague": Kit("#c8102e", "#ffffff", "trim"),
    "AEK Athens": Kit("#ffe100", "#000000", "halves"),
    "Slovan Bratislava": Kit("#6cace4", "#ffffff", "trim"),
    "LASK": Kit("#000000", "#ffffff", "halves"),
    "Viking Stavanger": Kit("#ffffff", "#002f6c", "trim"),
    "Sabah FK": Kit("#00693e", "#ffffff", "trim"),
}

# Silhouette de maillot (t-shirt sport stylisé, sans aucun élément de marque),
# dans un viewBox 0-100. Réutilisée comme remplissage principal et comme
# clip-path pour que tous les motifs restent dans les limites du maillot.
_SHIRT_PATH = (
    "M35,8 L45,2 L55,2 L65,8 L85,20 L78,38 L68,32 L68,90 "
    "L32,90 L32,32 L22,38 L15,20 Z"
)


def _pattern_overlay(kit: Kit, clip_id: str) -> str:
    sec = kit.secondary
    if kit.pattern == "solid":
        return ""
    if kit.pattern == "halves":
        return f'<rect x="0" y="0" width="50" height="100" fill="{sec}" clip-path="url(#{clip_id})"/>'
    if kit.pattern == "center_stripe":
        return f'<rect x="42" y="0" width="16" height="100" fill="{sec}" clip-path="url(#{clip_id})"/>'
    if kit.pattern == "vertical_stripes":
        bars = "".join(
            f'<rect x="{x}" y="0" width="9" height="100" fill="{sec}" clip-path="url(#{clip_id})"/>'
            for x in (15, 33, 51, 69)
        )
        return bars
    if kit.pattern == "horizontal_stripes":
        bars = "".join(
            f'<rect x="0" y="{y}" width="100" height="9" fill="{sec}" clip-path="url(#{clip_id})"/>'
            for y in (18, 36, 54, 72)
        )
        return bars
    if kit.pattern == "diagonal_sash":
        return (
            f'<rect x="-10" y="40" width="130" height="22" fill="{sec}" '
            f'transform="rotate(-28 50 50)" clip-path="url(#{clip_id})"/>'
        )
    if kit.pattern == "trim":
        return (
            f'<rect x="30" y="2" width="40" height="9" fill="{sec}" clip-path="url(#{clip_id})"/>'
            f'<rect x="12" y="18" width="14" height="9" fill="{sec}" clip-path="url(#{clip_id})"/>'
            f'<rect x="74" y="18" width="14" height="9" fill="{sec}" clip-path="url(#{clip_id})"/>'
        )
    return ""


def primary_color(club_name: str) -> str:
    """Couleur principale (hex) du kit de `club_name`, ou celle du kit par
    défaut si le club n'a pas d'entrée dédiée -- pour représenter un club
    par une simple pastille de couleur (ex. jeton joueur écran "stade")
    sans dépendre du rendu SVG complet du maillot."""
    return CLUB_KIT.get(club_name, _DEFAULT_KIT).primary


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _color_distance(hex_a: str, hex_b: str) -> float:
    ra, ga, ba = _hex_to_rgb(hex_a)
    rb, gb, bb = _hex_to_rgb(hex_b)
    return ((ra - rb) ** 2 + (ga - gb) ** 2 + (ba - bb) ** 2) ** 0.5

# Distance euclidienne RGB en dessous de laquelle deux couleurs primaires
# sont jugées trop proches pour se distinguer sur un jeton de 40px (ex. le
# rouge d'AS Monaco #e2001a et celui de Stade Brestois 29 #da291c).
_CLASH_THRESHOLD = 90.0


def match_kit_colors(home_club: str, away_club: str) -> tuple[tuple[str, str], tuple[str, str]]:
    """(fond, bordure) du jeton joueur pour chaque équipe d'un match --
    ((fond_domicile, bordure_domicile), (fond_exterieur, bordure_exterieur)).

    Si les couleurs primaires des deux clubs sont trop proches pour se
    distinguer sur le terrain (ex. deux maillots rouges), l'équipe
    extérieure bascule sur sa couleur secondaire -- exactement comme un
    vrai maillot extérieur change de couleur en cas de clash avec le
    domicile, plutôt que d'introduire une palette arbitraire déconnectée de
    l'identité du club."""
    home = CLUB_KIT.get(home_club, _DEFAULT_KIT)
    away = CLUB_KIT.get(away_club, _DEFAULT_KIT)
    if _color_distance(home.primary, away.primary) < _CLASH_THRESHOLD:
        away_colors = (away.secondary, away.primary)
    else:
        away_colors = (away.primary, away.secondary)
    return (home.primary, home.secondary), away_colors


def jersey_svg(club_name: str, *, size: int = 42, badge_id: str = "") -> str:
    """Icône SVG (chaîne autonome) du maillot d'un club, `size` px de côté.

    `badge_id` doit être unique dans la page si plusieurs maillots sont
    affichés en même temps (sert d'identifiant pour le `clipPath`, qui est
    sinon partagé par erreur entre toutes les icônes du DOM).
    """
    kit = CLUB_KIT.get(club_name, _DEFAULT_KIT)
    clip_id = f"shirt-clip-{badge_id}" if badge_id else "shirt-clip"
    overlay = _pattern_overlay(kit, clip_id)
    return (
        f'<svg width="{size}" height="{size}" viewBox="0 0 100 100" '
        f'xmlns="http://www.w3.org/2000/svg">'
        f"<defs><clipPath id=\"{clip_id}\"><path d=\"{_SHIRT_PATH}\"/></clipPath></defs>"
        f'<path d="{_SHIRT_PATH}" fill="{kit.primary}" '
        f'stroke="rgba(0,0,0,0.35)" stroke-width="2"/>'
        f"{overlay}"
        f"</svg>"
    )

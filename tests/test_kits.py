from ligue1sim.kits import CLUB_KIT, _DEFAULT_KIT, jersey_svg


def test_known_club_uses_its_own_colors():
    svg = jersey_svg("Paris Saint-Germain", badge_id="a")
    kit = CLUB_KIT["Paris Saint-Germain"]
    assert kit.primary in svg
    assert kit.secondary in svg


def test_unknown_club_falls_back_to_default_kit():
    svg = jersey_svg("Un Club Inconnu FC", badge_id="b")
    assert _DEFAULT_KIT.primary in svg
    assert _DEFAULT_KIT.secondary in svg


def test_solid_pattern_has_no_secondary_overlay_shape():
    # Paris FC : motif "solid" -> pas de forme secondaire dans le SVG, la
    # couleur secondaire ne doit apparaitre nulle part.
    svg = jersey_svg("Paris FC", badge_id="c")
    kit = CLUB_KIT["Paris FC"]
    assert kit.secondary not in svg


def test_every_ligue1_club_has_a_dedicated_kit():
    ligue1_clubs = [
        "Angers SCO", "AJ Auxerre", "Stade Brestois 29", "RC Lens", "Le Havre AC",
        "Le Mans FC", "LOSC Lille", "FC Lorient", "Olympique Lyon",
        "Olympique Marseille", "AS Monaco", "OGC Nice", "Paris FC",
        "Paris Saint-Germain", "Stade Rennais FC", "RC Strasbourg Alsace",
        "FC Toulouse", "ESTAC Troyes",
    ]
    for club in ligue1_clubs:
        assert club in CLUB_KIT, f"kit manquant pour {club}"


def test_every_club_of_every_simulable_championnat_has_a_dedicated_kit():
    """Les noms ci-dessous sont ceux exacts de la colonne "Club" (verifies via
    `ligue1sim.clubs.load_clubs` pour chaque championnat) : un desalignement
    ici retomberait silencieusement sur le kit gris par defaut dans l'appli."""
    premier_league = [
        "AFC Bournemouth", "Arsenal FC", "Aston Villa", "Brentford FC",
        "Brighton & Hove Albion", "Chelsea FC", "Coventry City", "Crystal Palace",
        "Everton FC", "Fulham FC", "Hull City", "Ipswich Town", "Leeds United",
        "Liverpool FC", "Manchester City", "Manchester United", "Newcastle United",
        "Nottingham Forest", "Sunderland AFC", "Tottenham Hotspur",
    ]
    bundesliga = [
        "1.FC Köln", "1.FC Union Berlin", "1.FSV Mainz 05", "Bayer 04 Leverkusen",
        "Bayern Munich", "Borussia Dortmund", "Borussia Mönchengladbach",
        "Eintracht Frankfurt", "FC Augsburg", "FC Schalke 04", "Hamburger SV",
        "RB Leipzig", "SC Freiburg", "SC Paderborn 07", "SV 07 Elversberg",
        "SV Werder Bremen", "TSG 1899 Hoffenheim", "VfB Stuttgart",
    ]
    laliga = [
        "Athletic Bilbao", "Atlético de Madrid", "CA Osasuna", "Celta de Vigo",
        "Deportivo A Coruña", "Deportivo Alavés", "Elche CF", "FC Barcelona",
        "Getafe CF", "Levante UD", "Málaga CF", "RCD Espanyol Barcelona",
        "Racing Santander", "Rayo Vallecano", "Real Betis Balompié", "Real Madrid",
        "Real Sociedad", "Sevilla FC", "Valencia CF", "Villarreal CF",
    ]
    serie_a = [
        "AC Milan", "AC Monza", "ACF Fiorentina", "AS Roma", "Atalanta BC",
        "Bologna FC 1909", "Cagliari Calcio", "Como 1907", "Frosinone Calcio",
        "Genoa CFC", "Inter Milan", "Juventus FC", "Parma Calcio 1913", "SS Lazio",
        "SSC Napoli", "Torino FC", "US Lecce", "US Sassuolo", "Udinese Calcio",
        "Venezia FC",
    ]
    eredivisie = [
        "ADO Den Haag", "AZ Alkmaar", "Ajax Amsterdam", "Excelsior Rotterdam",
        "FC Groningen", "FC Twente Enschede", "FC Utrecht", "Feyenoord Rotterdam",
        "Fortuna Sittard", "Go Ahead Eagles", "NEC Nijmegen", "PEC Zwolle",
        "PSV Eindhoven", "SC Cambuur", "SC Heerenveen", "SC Telstar",
        "Sparta Rotterdam", "Willem II",
    ]
    jupiler = [
        "Cercle Brugge", "Club Brugge KV", "KAA Gent", "KRC Genk", "KV Kortrijk",
        "KV Mechelen", "KVC Westerlo", "Lommel SK", "Oud-Heverlee Leuven",
        "RAAL La Louvière", "RSC Anderlecht", "Royal Antwerp", "Royal Charleroi SC",
        "SK Beveren", "Saint Trond", "Standard Liège", "Union Saint-Gilloise",
        "Zulte Waregem",
    ]
    liga_portugal = [
        "Académico de Viseu", "CD Nacional", "CD Santa Clara", "CF Estrela Amadora",
        "CS Marítimo", "Casa Pia AC", "FC Alverca", "FC Arouca", "FC Famalicão",
        "FC Porto", "GD Estoril Praia", "Gil Vicente FC", "Moreirense FC",
        "Rio Ave FC", "SC Braga", "SL Benfica", "Sporting CP", "Vitória Guimarães SC",
    ]
    for club in premier_league + bundesliga + laliga + serie_a + eredivisie + jupiler + liga_portugal:
        assert club in CLUB_KIT, f"kit manquant pour {club}"


def test_badge_id_keeps_clip_path_unique_per_icon():
    svg_a = jersey_svg("AS Monaco", badge_id="home-1")
    svg_b = jersey_svg("AS Monaco", badge_id="away-1")
    assert "shirt-clip-home-1" in svg_a
    assert "shirt-clip-away-1" in svg_b

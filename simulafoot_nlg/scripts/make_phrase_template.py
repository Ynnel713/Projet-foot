"""Genere le classeur Excel que l'utilisateur remplit a la main pour fournir
la banque de phrases (voir data/seed/scenarios.yml, slots.yml) -- ce script
n'est PAS relie a cli.py/import_seed.py : c'est un outil ponctuel pour
produire le template de saisie, pas une brique du pipeline d'import.

4 feuilles :
    "Instructions"              -- mode d'emploi en langage courant.
    "Phrases"                    -- 1 ligne = 1 phrase, colonnes minimales.
    "Dictionnaires de slots"     -- optionnel, valeurs piochees par {slot}.
    "Preferred moves disponibles" -- reference en lecture seule : tous les
        preferred moves reellement presents dans data/joueurs.xlsx, pour
        ecrire des conditions sans se tromper d'orthographe.

Volontairement PLUS SIMPLE que le schema SQLite complet (pas de colonnes
"is_default"/"mandatory"/"weight" par phrase a comprendre pour l'utilisateur) :
la conversion de ce classeur vers scenarios.yml/slots.yml sera faite par
Claude Code a la lecture, avec des regles de repli documentees dans la
feuille "Instructions" (ex. une seule variante par scenario -> is_default
automatique).

Design "scenario large + conditions" (retour utilisateur du 29/09/2026) :
plutot que de multiplier les scenarios pour chaque nuance (BUT_TETE,
BUT_DEBUT_MATCH, BUT_TETE_DEBUT_MATCH...), les scenarios restent PEU
NOMBREUX et LARGES (BUT, CARTON_ROUGE...) et les nuances se cumulent via la
colonne "Condition" d'une phrase -- plusieurs conditions sur une meme phrase
se combinent en ET logique (voir la feuille Instructions)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.worksheet import Worksheet

HEADER_FILL = PatternFill(start_color="1F2D3D", end_color="1F2D3D", fill_type="solid")
HEADER_FONT = Font(bold=True, color="FFFFFF")
EXAMPLE_FILL = PatternFill(start_color="FFF6D9", end_color="FFF6D9", fill_type="solid")
EXAMPLE_FONT = Font(italic=True, color="7A6A2E")
TITLE_FONT = Font(bold=True, size=14)
SUBTITLE_FONT = Font(bold=True, size=12)
WRAP = Alignment(wrap_text=True, vertical="top")

DEFAULT_PLAYERS_XLSX = Path(__file__).resolve().parent.parent.parent / "data" / "joueurs.xlsx"
_EMPTY_MOVE_MARKERS = {"(aucun)", "-", "—", ""}

# Traduction francaise des preferred moves FM26 -- pour que l'utilisateur du
# template sache de quoi il parle sans connaitre le jargon FM en anglais
# (retour du 29/09/2026). Traduction de sens (vocabulaire football courant),
# pas mot a mot. Cle = orthographe EXACTE telle que scrapee (voir
# scripts/scrape_fminside_attributes.py) -- une valeur absente de ce
# dictionnaire (base qui evolue) affiche un repli explicite plutot que de
# planter, voir _build_preferred_moves_sheet.
PREFERRED_MOVE_TRANSLATIONS: dict[str, str] = {
    "Argues With Officials": "Conteste les décisions de l'arbitre",
    "Arrives Late In Opposition Area": "Arrive tardivement dans la surface adverse",
    "Attempts Overhead Kicks": "Tente des retournées acrobatiques",
    "Avoids Using Weaker Foot": "Évite d'utiliser son pied faible",
    "Bring Ball Out of Defence": "Relance proprement depuis la défense",
    "Comes Deep To Get Ball": "Décroche pour venir chercher le ballon",
    "Crosses Early": "Centre tôt, sans attendre",
    "Curls Ball": "Enroule ses frappes et centres",
    "Cuts Inside From Both Wings": "Rentre à l'intérieur des deux côtés",
    "Cuts Inside From Left Wing": "Rentre à l'intérieur depuis la gauche",
    "Cuts Inside From Right Wing": "Rentre à l'intérieur depuis la droite",
    "Dictates Tempo": "Dicte le tempo du jeu",
    "Dives Into Tackles": "Se jette dans les tacles",
    "Does Not Dive Into Tackles": "Évite de se jeter dans les tacles",
    "Dwells On Ball": "Garde le ballon trop longtemps",
    "Gets Crowd Going": "Enflamme le public",
    "Gets Forward Whenever Possible": "Monte offensivement dès que possible",
    "Gets Into Opposition Area": "Fait des appels dans la surface adverse",
    "Hits Free Kicks With Power": "Frappe puissamment les coups francs",
    "Hugs Line": "Colle à la ligne de touche",
    "Knocks Ball Past Opponent": "Élimine l'adversaire en poussant le ballon devant lui",
    "Likes Ball Played Into Feet": "Aime recevoir le ballon dans les pieds",
    "Likes To Beat Opponent Repeatedly": "Aime éliminer le même adversaire plusieurs fois",
    "Likes To Lob Keeper": "Aime lober le gardien",
    "Likes To Round Keeper": "Aime dribbler le gardien",
    "Likes To Switch Ball To Wide Areas": "Aime changer le jeu vers les ailes",
    "Likes To Try To Break Offside Trap": "Cherche à casser le piège du hors-jeu",
    "Looks For Pass Rather Than Attempting To Score": "Privilégie la passe à la finition",
    "Moves Ball To Left Foot Before Dribble Attempt": "Bascule sur le pied gauche avant de dribbler",
    "Moves Ball To Right Foot Before Dribble Attempt": "Bascule sur le pied droit avant de dribbler",
    "Moves Into Channels": "Se déplace entre les lignes adverses",
    "Penalty Box Player": "Joueur de surface",
    "Places Shots": "Place ses frappes plutôt que de frapper fort",
    "Plays One-Twos": "Joue en une-deux",
    "Plays Short Simple Passes": "Joue des passes courtes et simples",
    "Plays With Back To Goal": "Joue dos au but",
    "Possesses Long Flat Throw": "Possède une longue touche tendue",
    "Refrains From Taking Long Shots": "Évite les frappes lointaines",
    "Runs With Ball Down Left": "Porte le ballon côté gauche",
    "Runs With Ball Down Right": "Porte le ballon côté droit",
    "Runs With Ball Often": "Porte souvent le ballon",
    "Runs With Ball Rarely": "Porte rarement le ballon",
    "Runs With Ball Through The Centre": "Porte le ballon dans l'axe",
    "Shoots From Distance": "Tire de loin",
    "Shoots With Power": "Frappe puissamment",
    "Stops Play": "Casse le rythme du jeu",
    "Tries First Time Shots": "Tente des frappes en une touche",
    "Tries Killer Balls Often": "Tente souvent des passes décisives tranchantes",
    "Tries Long Range Free Kicks": "Tente des coups francs lointains",
    "Tries Long Range Passes": "Tente des passes longues",
    "Tries To Play Way Out Of Trouble": "Cherche à sortir du pressing par le jeu",
    "Tries Tricks": "Tente des gestes techniques et dribbles",
    "Uses Long Throw To Start Counter Attacks": "Utilise sa longue touche pour lancer les contre-attaques",
    "Uses Outside Of Foot": "Utilise l'extérieur du pied",
    "Winds Up Opponents": "Provoque les adversaires",
}


def _style_header(ws: Worksheet, row: int, n_cols: int) -> None:
    for col in range(1, n_cols + 1):
        cell = ws.cell(row=row, column=col)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(vertical="center")


def _build_instructions(ws: Worksheet) -> None:
    ws.column_dimensions["A"].width = 104
    lines: list[tuple[str, Font | None]] = [
        ("Comment remplir ce classeur", TITLE_FONT),
        ("", None),
        ("Vous n'avez qu'une seule feuille à remplir : \"Phrases\".", Font(bold=True)),
        ("Les feuilles \"Dictionnaires de slots\" et \"Preferred moves disponibles\"", None),
        ("sont des aides optionnelles, pas à remplir vous-même (la 2e est déjà remplie).", None),
        ("", None),
        ("1. Un \"scénario\" = une GRANDE catégorie de temps fort (BUT, CARTON_ROUGE,", None),
        ("   PASSE_DECISIVE...). Gardez-en PEU -- ne créez pas un scénario par nuance", None),
        ("   (voir point 5, c'est le rôle de la colonne Condition). Code court en", None),
        ("   MAJUSCULES (ex. BUT) et un libellé en français.", None),
        ("", None),
        ("2. Pour un même scénario, écrivez autant de lignes que vous avez de phrases", None),
        ("   différentes -- répétez le même code de scénario sur chaque ligne. Plus il", None),
        ("   y a de phrases pour un scénario, moins elles se répéteront à l'usage.", None),
        ("", None),
        ("3. Dans le texte d'une phrase, mettez entre accolades {comme_ça} tout ce qui", None),
        ("   doit changer à chaque fois (le nom du joueur, une exclamation...).", None),
        ("   Exemples de noms de slot que vous pouvez utiliser : {joueur}, {club},", None),
        ("   {adversaire}, {minute}, {exclamation}.", None),
        ("", None),
        ("4. Si un {slot} doit piocher parmi plusieurs mots possibles (ex. {exclamation}", None),
        ("   peut être \"Quelle frappe !\" ou \"Magnifique !\"), ajoutez ces choix dans la", None),
        ("   feuille \"Dictionnaires de slots\". Sinon, ne remplissez rien pour ce slot :", None),
        ("   {joueur}, {club}, {adversaire}, {minute} sont déjà connus automatiquement.", None),
        ("", None),
        ("5. La colonne Condition réserve une phrase à une situation précise -- c'est ce", SUBTITLE_FONT),
        ("   qui remplace \"un scénario par nuance\". Une phrase SANS condition peut", None),
        ("   sortir à n'importe quel moment du scénario. Quatre types de condition :", None),
        ("", None),
        ("   • Sur le moment du match : minute <= 5   /   minute >= 80", None),
        ("   • Sur une caractéristique du joueur (0 à 99) : Dribbling >= 80", None),
        ("     (voir les noms exacts dans l'app : Crossing, Dribbling, Finishing,", None),
        ("     Heading, Passing, Tackling, Technique, Pace, Strength, Vision...)", None),
        ("   • Sur un preferred move du joueur : preferred_moves contient \"Tries", None),
        ("     Killer Balls Often\" (voir la liste exacte dans la feuille", None),
        ("     \"Preferred moves disponibles\" -- copiez-collez l'orthographe exacte).", None),
        ("   • Sur l'effet du but sur le score (pour \"égalise\", \"prend l'avantage\"...) :", None),
        ("     score_context == \"egalisation\". Valeurs possibles : ouverture_score", None),
        ("     (1er but du match), egalisation, prise_avantage, reduit_ecart,", None),
        ("     creuse_ecart. Ne s'applique qu'au scénario BUT.", None),
        ("", None),
        ("   Pour combiner plusieurs conditions sur UNE MÊME phrase (ex. \"de la tête\"", None),
        ("   ET \"en début de match\"), séparez-les par \" et \" dans la même cellule :", None),
        ("   Heading >= 75 et minute <= 5", None),
        ("", None),
        ("6. Les colonnes \"Variante\", \"Poids\" et \"Tags\" sont optionnelles -- laissez-les", None),
        ("   vides si vous ne savez pas quoi y mettre, une valeur par défaut sera", None),
        ("   utilisée.", None),
        ("", None),
        ("Une fois rempli, renvoyez ce fichier -- son import dans l'application ne", Font(bold=True)),
        ("nécessite aucune autre manipulation de votre part.", Font(bold=True)),
    ]
    for i, (text, font) in enumerate(lines, start=1):
        cell = ws.cell(row=i, column=1, value=text)
        if font:
            cell.font = font
        cell.alignment = WRAP


def _build_phrases_sheet(ws: Worksheet) -> None:
    headers = [
        "Code scénario",
        "Libellé scénario",
        "Variante (optionnel)",
        "Phrase",
        "Condition (optionnel)",
        "Poids (optionnel)",
        "Tags (optionnel, séparés par des virgules)",
    ]
    ws.append(headers)
    _style_header(ws, 1, len(headers))

    widths = [18, 24, 16, 62, 34, 12, 26]
    for col, width in zip("ABCDEFG", widths, strict=True):
        ws.column_dimensions[col].width = width

    examples = [
        (
            "BUT",
            "But marqué",
            "DEFAUT",
            "{joueur} ne s'est pas posé de question, {exclamation} !",
            "",
            1,
            "classique",
        ),
        (
            "BUT",
            "But marqué",
            "",
            "{joueur} ne laisse même pas le match s'installer : dès la première minute, "
            "il frappe et fait exploser les filets !",
            "minute <= 5",
            1,
            "explosif",
        ),
        (
            "BUT",
            "But marqué",
            "",
            "Un festival de dribbles : {joueur} a fait déjouer toute la défense de {adversaire} !",
            'preferred_moves contient "Likes To Try Tricks"',
            1,
            "dribble",
        ),
        (
            "BUT",
            "But marqué",
            "",
            "Détente phénoménale de {joueur}, le ballon file au fond des filets d'un coup de tête !",
            "Heading >= 75 et minute <= 5",
            1,
            "tête, explosif",
        ),
        (
            "BUT",
            "But marqué",
            "",
            "{joueur} remet les deux équipes à égalité et relance complètement ce match !",
            'score_context == "egalisation"',
            1,
            "égalisation",
        ),
        (
            "CARTON_ROUGE",
            "Carton rouge",
            "",
            "{joueur} voit rouge à la {minute}e minute, {club} devra finir à dix.",
            "",
            1,
            "dramatique",
        ),
    ]
    start_row = ws.max_row + 1
    for row in examples:
        ws.append(row)
    for r in range(start_row, start_row + len(examples)):
        for c in range(1, len(headers) + 1):
            cell = ws.cell(row=r, column=c)
            cell.fill = EXAMPLE_FILL
            cell.font = EXAMPLE_FONT
            cell.alignment = WRAP

    note_row = start_row + len(examples) + 1
    note = ws.cell(
        row=note_row,
        column=1,
        value="↑ Lignes d'exemple en jaune : à remplacer ou supprimer. Continuez juste en dessous.",
    )
    note.font = Font(italic=True, color="8A9BB0")
    ws.freeze_panes = "A2"


def _build_slot_dictionaries_sheet(ws: Worksheet) -> None:
    headers = ["Nom du dictionnaire (slot)", "Valeur possible", "Poids (optionnel)"]
    ws.append(headers)
    _style_header(ws, 1, len(headers))

    for col, width in zip("ABC", [26, 60, 14], strict=True):
        ws.column_dimensions[col].width = width

    examples = [
        ("exclamation", "quelle frappe !", 1),
        ("exclamation", "magnifique !", 1),
        ("exclamation", "personne ne s'y attendait !", 0.5),
    ]
    start_row = ws.max_row + 1
    for row in examples:
        ws.append(row)
    for r in range(start_row, start_row + len(examples)):
        for c in range(1, len(headers) + 1):
            cell = ws.cell(row=r, column=c)
            cell.fill = EXAMPLE_FILL
            cell.font = EXAMPLE_FONT

    note_row = start_row + len(examples) + 1
    note = ws.cell(
        row=note_row,
        column=1,
        value="↑ Exemple en jaune : à remplacer ou supprimer. Plusieurs lignes = plusieurs choix possibles.",
    )
    note.font = Font(italic=True, color="8A9BB0")
    ws.freeze_panes = "A2"


def _load_preferred_moves(players_xlsx: Path) -> list[tuple[str, int]]:
    """[(preferred move, nombre de joueurs qui l'ont)], trié alphabétiquement
    -- lu depuis le VRAI classeur joueurs (pas une liste figée à la main :
    reste juste si la base évolue). Liste vide (pas une erreur) si le
    classeur est introuvable OU verrouillé (ex. ouvert dans Excel -- Windows
    refuse parfois même la lecture) -- la feuille de référence est alors
    juste absente de contenu, avec une note explicative à la place plutôt
    qu'un crash. Passe par une copie temporaire en cas de verrou : une copie
    de fichier est généralement autorisée même quand l'ouverture directe ne
    l'est pas (sémantique de partage Windows différente)."""
    if not players_xlsx.exists():
        return []
    try:
        df = pd.read_excel(players_xlsx, sheet_name="Infos principales", engine="openpyxl")
    except PermissionError:
        import shutil
        import tempfile

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_copy = Path(tmp_dir) / players_xlsx.name
            try:
                shutil.copy2(players_xlsx, tmp_copy)
            except PermissionError:
                return []
            df = pd.read_excel(tmp_copy, sheet_name="Infos principales", engine="openpyxl")
    counts: dict[str, int] = {}
    for raw in df.get("Preferred moves", pd.Series(dtype=object)).dropna():
        text = str(raw).strip()
        if text in _EMPTY_MOVE_MARKERS:
            continue
        for move in text.split(";"):
            move = move.strip()
            if move:
                counts[move] = counts.get(move, 0) + 1
    return sorted(counts.items())


def _build_preferred_moves_sheet(ws: Worksheet, players_xlsx: Path) -> None:
    ws.cell(row=1, column=1, value="Preferred moves disponibles dans la base joueurs").font = TITLE_FONT
    ws.cell(
        row=2,
        column=1,
        value=(
            "Utilisez la colonne \"Traduction française\" pour comprendre -- mais copiez-collez "
            'l\'orthographe EXACTE de la colonne "Preferred move" (en anglais) dans une condition '
            '(ex. preferred_moves contient "...").'
        ),
    ).font = Font(italic=True, color="8A9BB0")

    headers = ["Preferred move", "Traduction française", "Nombre de joueurs"]
    header_row = 4
    for col, text in enumerate(headers, start=1):
        ws.cell(row=header_row, column=col, value=text)
    _style_header(ws, header_row, len(headers))
    ws.column_dimensions["A"].width = 52
    ws.column_dimensions["B"].width = 56
    ws.column_dimensions["C"].width = 20

    moves = _load_preferred_moves(players_xlsx)
    if not moves:
        ws.cell(
            row=header_row + 1,
            column=1,
            value=(
                f"(classeur joueurs introuvable ou verrouillé à la génération : {players_xlsx} "
                "-- fermez-le dans Excel et régénérez le template si besoin de cette liste)"
            ),
        ).font = Font(italic=True, color="8A9BB0")
        return

    for i, (move, count) in enumerate(moves, start=header_row + 1):
        ws.cell(row=i, column=1, value=move)
        translation = PREFERRED_MOVE_TRANSLATIONS.get(move)
        cell = ws.cell(row=i, column=2, value=translation or "(traduction à compléter)")
        if translation is None:
            cell.font = Font(italic=True, color="C0392B")
        ws.cell(row=i, column=3, value=count)
    ws.freeze_panes = f"A{header_row + 1}"


def build_template(path: str | Path, players_xlsx: Path = DEFAULT_PLAYERS_XLSX) -> None:
    wb = Workbook()

    # wb.active est typé Optional par openpyxl (une feuille peut en théorie
    # être détachée), mais un Workbook() fraîchement créé a toujours une
    # feuille active -- assert plutôt qu'un ignore, pour que mypy le vérifie
    # explicitement au lieu de faire confiance aveuglément.
    ws_instructions = wb.active
    assert ws_instructions is not None
    ws_instructions.title = "Instructions"
    _build_instructions(ws_instructions)

    ws_phrases = wb.create_sheet("Phrases")
    _build_phrases_sheet(ws_phrases)

    ws_slots = wb.create_sheet("Dictionnaires de slots")
    _build_slot_dictionaries_sheet(ws_slots)

    ws_moves = wb.create_sheet("Preferred moves disponibles")
    _build_preferred_moves_sheet(ws_moves, players_xlsx)

    wb.active = 1  # ouvre sur "Phrases" -- l'onglet que l'utilisateur remplit
    wb.save(path)


if __name__ == "__main__":
    import sys

    out_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("banque_de_phrases_simulafoot.xlsx")
    build_template(out_path)
    print(f"Template créé : {out_path}")

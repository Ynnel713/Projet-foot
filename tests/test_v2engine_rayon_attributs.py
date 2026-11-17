"""Rayon des attributs (ticket v2-collectif/18, règle anti double comptage de docs/CARTE_ATTRIBUTS_V2.md) : chaque
attribut n'est lu que dans les modules du moteur qui portent son rayon, et deux attributs ne se mélangent pas dans
un même calcul hors des dérogations listées. Ajouter un attribut ailleurs, c'est ajouter un effet : mettre d'abord à
jour la carte, puis cette liste. Analyse de l'arbre syntaxique (ast), pas du texte.

Limite connue : un mélange qui passe par des variables intermédiaires (a = A ; b = B ; a + b) n'est pas détecté ; la
grille de relecture de la carte le couvre."""

from __future__ import annotations

import ast
import pathlib
import re

import openpyxl

from ligue1sim.players import FM_ATTRIBUTE_COLUMNS
from v2engine.contextes import CONTEXTES

ENGINE = pathlib.Path(__file__).resolve().parents[1] / "v2engine"
PHYSICAL_FIELDS = {"pace": "Pace", "acceleration": "Acceleration", "stamina": "Stamina"}

# Lecture d'une note : la façade `condition.effective_rating` (jeu), `condition.intrinsic_rating` (chargement), ou
# `attributes.player_attribute` (réservé à la façade depuis le ticket v2-realisme/19a).
READERS = {"player_attribute", "effective_rating", "intrinsic_rating"}
# Registre des contextes (ADR 0002, ticket v2-attributs-contextes/01) : `contextes.contextual_rating` lit par la façade
# des noms venus du registre, non littéraux ; chaque attribut d'un contexte compte comme lu dans le module « contextes ».
# Adaptation minimale : la garde est refondue autour du registre au ticket v2-attributs-contextes/02.
REGISTRY = "contextes"

# Attribut -> modules où il peut être lu (rayon de docs/CARTE_ATTRIBUTS_V2.md). « match » : construction des joueurs
# (Pace, Acceleration, Stamina recopiés dans PlayerState) et déclenchement du tacle (Aggression). Les physiques lus
# en jeu sont des capacités (règle R5), lues par la façade depuis le 19a :
# defense : temps d'arrivée qui désigne le presseur et la couverture (ticket v2-collectif/07)
# decision : course du porteur contre les adversaires vers l'espace libre (ticket v2-collectif/33)
# occasion (ticket v2-collectif/28c) : temps pour atteindre un ballon libre, la même vitesse de pointe (R5), mesure seule
ALLOWED = {
    "Pace": {"match", "anticipation", "bloc", "defense", "decision", "occasion", "scan"},  # scan : vitesse relative (08c)
    "Acceleration": {"match", "defense"},
    "Stamina": {"match"},
    # vitesse de rotation du corps (ticket v2-realisme/07f) ; + délai de rotation avant la passe ou le tir, même
    # fonction à la décision et à l'exécution (07e) ; freinage 12a, virage 12b
    "Agility": {"movement", "decision"},
    # précision de la talonnade, geste difficile (07e) ; précision de la passe de première (possession, ticket
    # v2-collectif/31a) ; registre : porteur tête haute avec Dribbling (08c), idée de jouer de première avec First Touch (31a)
    "Technique": {"possession", REGISTRY},
    "Flair": {"decision"},  # penser à la talonnade (ticket v2-realisme/07e)
    "Strength": {"duel"},
    "Balance": {"duel"},
    "Aggression": {"duel", "match", "defense"},  # fréquence des tentatives et faute ; distance d'arrêt du presseur (08)
    "Tackling": {"duel"},
    # + drapeau du hors-jeu (23) ; ligne fermée au pressing (08) ; perception du porteur : prolonger la course des
    # adversaires pendant sa conduite (ticket v2-collectif/33)
    "Anticipation": {"anticipation", "match", "defense", "decision"},
    # restart : choix du receveur d'une remise en jeu (ticket 29) ; duel : renoncer au tacle par derrière hors urgence (11h)
    "Decisions": {"decision", "restart", "duel"},
    "Vision": {"decision", "off_ball", "scan"},  # + le coureur tente l'appel dans le dos si le porteur le voit (16) ; fréquence des scans (08c)
    "Off the Ball": {"off_ball", "offside"},  # + régler l'appel sur la ligne du hors-jeu (ticket 23)
    # tir sous pression par `shooting.shot_composure_factor`, courbe propre (ticket 28a) ; + perception sous pression (33)
    "Composure": {"possession", "decision", "shooting"},
    "Dribbling": {"decision", REGISTRY},  # (registre : porteur tête haute, cumul avec Technique, 08c) chance de garder le ballon en conduisant : valeur factuelle (ticket 33) et perte tirée (04a) ; vitesse balle au pied (04d)
    "First Touch": {"possession", REGISTRY},  # + registre : idée de jouer de première, avec Technique (ticket v2-collectif/31a)
    "Passing": {"possession", "off_ball"},  # + ... et s'il sait le servir (ticket v2-collectif/16)
    "Finishing": {"shooting"},  # dans la surface ; Long Shots en dehors (ticket 28a)
    "Long Shots": {"shooting"},
    "Reflexes": {"shooting"},
    "One on Ones": {"shooting"},
    "Handling": {"shooting"},
    # erreur de placement dans le bloc, reprise par la couverture et la compensation (tickets v2-collectif/04, 07 et 09)
    "Positioning": {"bloc"},
    # écart toléré avant de se replacer (04) ; quitter le bloc pour le ballon (07) ; accepter de compenser (09) ;
    # adopter le plan de passe de son passeur (14)
    "Teamwork": {"bloc", "defense", "decision"},
    "Work Rate": {"defense"},  # intensité et repos du presseur (ticket v2-collectif/08)
    "Marking": {"defense"},  # distance de marquage d'un attaquant dangereux (ticket v2-collectif/07)
}
# Mélanges de plusieurs attributs dans un même calcul tolérés (dérogations de la carte).
TOLERATED_MIXES = {
    frozenset({"Reflexes", "One on Ones", "Handling"}),  # A8 : note du gardien, jusqu'à la phase 9 (confirmée le 26/10/2026)
    # temps d'arrivée (`defense.arrival_time_s`) : course à vitesse de pointe + montée en régime, deux capacités
    # physiques additionnées en secondes (règle R5), pas une pondération de notes ; visible depuis que les champs
    # passent par la façade (ticket v2-realisme/19a)
    frozenset({"Pace", "Acceleration"}),
    # porteur tête haute (08c, A15) et idée de jouer de première (31a, A16) : passés au registre des contextes
    # (ticket v2-attributs-contextes/01), hors de cette liste
}


def _modules():
    for path in sorted(ENGINE.rglob("*.py")):
        yield path.relative_to(ENGINE).with_suffix("").as_posix().replace("/", "."), ast.parse(path.read_text(encoding="utf-8"))


def _attribute_calls(tree: ast.AST):
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, "id", getattr(node.func, "attr", None)) in READERS:
            yield node


def _name(call: ast.Call) -> str | None:
    arg = call.args[1] if len(call.args) > 1 else next((k.value for k in call.keywords if k.arg == "name"), None)
    return arg.value if isinstance(arg, ast.Constant) and isinstance(arg.value, str) else None


def _reads() -> dict[str, set[str]]:
    found: dict[str, set[str]] = {}
    for module, tree in _modules():
        for call in _attribute_calls(tree):
            found.setdefault(_name(call) or "<nom non littéral>", set()).add(module)
    for contexte in CONTEXTES.values():
        for attribute in contexte.attributs:
            found.setdefault(attribute, set()).add(REGISTRY)
    return found


def test_each_attribute_is_read_only_within_its_reach() -> None:
    reads = _reads()
    assert "<nom non littéral>" not in reads or reads["<nom non littéral>"] <= {"attributes", "condition", REGISTRY}, \
        f"player_attribute appelé avec un nom non littéral (rayon invérifiable) : {reads.get('<nom non littéral>')}"
    reads.pop("<nom non littéral>", None)
    outside = {attr: mods - ALLOWED.get(attr, set()) for attr, mods in reads.items() if mods - ALLOWED.get(attr, set())}
    assert not outside, f"attribut lu hors de son rayon (mettre à jour la carte puis ALLOWED) : {outside}"


def test_the_allowed_list_has_no_stale_entry() -> None:
    reads = _reads()
    stale = {attr: mods - reads.get(attr, set()) for attr, mods in ALLOWED.items() if mods - reads.get(attr, set())}
    assert not stale, f"entrée périmée dans ALLOWED (dérogation levée ou attribut retiré ?) : {stale}"


def test_raw_attribute_dicts_are_read_only_through_player_attribute() -> None:
    # Lire une note, c'est indexer `.attributes[...]` ou appeler `.attributes.get(...)` ; la recopie du dictionnaire
    # (`attributes=state.attributes`) n'en est pas une.
    copies = set()
    for module, tree in _modules():
        for node in ast.walk(tree):
            if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Attribute) and node.value.attr == "attributes":
                copies.add(module)
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "get"
                    and isinstance(node.func.value, ast.Attribute) and node.func.value.attr == "attributes"):
                copies.add(module)
    assert not (copies - {"attributes"}), f"note lue directement dans .attributes hors de attributes.py : {copies}"


def test_physical_fields_are_read_only_by_movement() -> None:
    # Depuis le ticket v2-realisme/19a, une capacité physique se lit par la façade (rayon vérifié par ALLOWED) ;
    # le champ (`.pace`…) ne se lit que dans le chemin chaud de `movement.step`.
    found: dict[str, set[str]] = {}
    for module, tree in _modules():
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr in PHYSICAL_FIELDS and isinstance(node.ctx, ast.Load):
                found.setdefault(PHYSICAL_FIELDS[node.attr], set()).add(module)
    outside = {attr: mods - {"movement"} for attr, mods in found.items() if mods - {"movement"}}
    assert not outside, f"capacité physique lue par son champ hors de movement (passer par la façade) : {outside}"


def _attrs_in(node: ast.AST) -> set[str]:
    return {name for call in _attribute_calls(node) if (name := _name(call))}


def test_no_weighted_mix_of_attributes_outside_listed_exceptions() -> None:
    # Règle R2 : un calcul arithmétique (+, -, *, /) qui combine des notes de plusieurs attributs est un mélange.
    offenders = {}
    for module, tree in _modules():
        for node in ast.walk(tree):
            if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
                attrs = _attrs_in(node)
                if len(attrs) > 1 and not any(attrs <= allowed for allowed in TOLERATED_MIXES):  # sous-calcul compris
                    offenders.setdefault(module, set()).add(frozenset(attrs))
    assert not offenders, f"mélange d'attributs hors dérogations (règle R2) : {offenders}"


def test_the_mix_detector_catches_the_old_tackle_formula() -> None:
    old = ast.parse('r = 0.8 * player_attribute(t, "Tackling") + 0.2 * player_attribute(t, "Aggression")')
    mixes = {frozenset(_attrs_in(n)) for n in ast.walk(old) if isinstance(n, ast.BinOp) and len(_attrs_in(n)) > 1}
    assert frozenset({"Tackling", "Aggression"}) in mixes and frozenset({"Tackling", "Aggression"}) not in TOLERATED_MIXES


def test_every_tolerated_mix_still_exists() -> None:
    present = {frozenset(_attrs_in(n)) for _, tree in _modules() for n in ast.walk(tree)
               if isinstance(n, ast.BinOp) and len(_attrs_in(n)) > 1}
    assert TOLERATED_MIXES <= present, f"dérogation levée : la retirer de TOLERATED_MIXES et de la carte : {TOLERATED_MIXES - present}"


# --- Garde de couverture (ticket v2-attributs-restants/08, liste d'exceptions validée par le propriétaire le
# 14/11/2026) : chaque caractéristique de la base est lue par `v2engine/`, ou figure ci-dessous avec le ticket qui la
# branchera. Une exception devenue inutile (caractéristique lue) fait aussi échouer : la liste se vide au fil des tickets.

BASE = ENGINE.parent / "data" / "joueurs.xlsx"
BASE_SHEET = "Infos principales"
# Colonnes hors des 47 attributs FM -> champ du joueur (`ligue1sim.players.Player`) qui la porte
PLAYER_FIELD_COLUMNS = {"Taille FM (cm)": "taille_fm", "Weak foot (/5)": "weak_foot", "Pieds": "pied",
                        "Preferred moves": "preferred_moves", "Postes FM naturels": "postes_fm"}
COVERAGE_EXCEPTIONS = {
    "Natural Fitness": "exception permanente pour un match isolé (D-V10) ; branchement aux compétitions",
    "Concentration": "v2-collectif/21",
    "Determination": "v2-collectif/21 ; v2-coach-et-gestion-de-match/02 et 04",
    "Bravery": "v2-realisme/17b",
    "Leadership": "v2-realisme/17c",
    "Jumping Reach": "v2-realisme/15b",
    "Taille FM (cm)": "v2-realisme/15b",
    "Heading": "v2-realisme/15c",
    "Crossing": "v2-attributs-restants/01 et 11",
    "Corners": "v2-realisme/16d",
    "Free Kick Taking": "v2-realisme/16e",
    "Long Throws": "v2-realisme/16f",
    "Penalty Taking": "v2-attributs-restants/02a",
    "Aerial Reach": "v2-attributs-restants/03a",
    "Command of Area": "v2-attributs-restants/03a",
    "Communication": "v2-attributs-restants/03a",
    "Punching (Tendency)": "v2-attributs-restants/03a",
    "Rushing Out (Tendency)": "v2-attributs-restants/03b",
    "Eccentricity": "v2-attributs-restants/03b",
    "Kicking": "v2-attributs-restants/03c",
    "Throwing": "v2-attributs-restants/03c",
    "Weak foot (/5)": "v2-attributs-restants/04a",
    "Pieds": "v2-attributs-restants/04a",
    "Postes FM naturels": "v2-attributs-restants/04b",
    "Preferred moves": "v2-attributs-restants/05",
}
TICKET = re.compile(r"(v2-[a-z-]+/\d+[a-z]?|D-V\d+)")


def _base_columns_and_rows() -> tuple[tuple[str, ...], list[tuple]]:
    workbook = openpyxl.load_workbook(BASE, read_only=True)
    try:
        rows = workbook[BASE_SHEET].iter_rows(values_only=True)
        header = tuple(next(rows))
        return header, list(rows)
    finally:
        workbook.close()


HEADER, ROWS = _base_columns_and_rows()
CHARACTERISTICS = tuple(FM_ATTRIBUTE_COLUMNS) + tuple(PLAYER_FIELD_COLUMNS)


def _field_reads() -> set[str]:
    """Champs du joueur lus (chargés) dans le moteur : `x.preferred_moves`, `x.pied`…"""
    fields = set(PLAYER_FIELD_COLUMNS.values())
    return {node.attr for _, tree in _modules() for node in ast.walk(tree)
            if isinstance(node, ast.Attribute) and node.attr in fields and isinstance(node.ctx, ast.Load)}


def read_characteristics(attribute_reads: set[str], field_reads: set[str]) -> set[str]:
    return ({c for c in FM_ATTRIBUTE_COLUMNS if c in attribute_reads}
            | {c for c, f in PLAYER_FIELD_COLUMNS.items() if f in field_reads})


def coverage_gaps(characteristics, read: set[str], exceptions: dict[str, str]) -> tuple[set[str], set[str]]:
    """(ni lues ni en exception, exceptions devenues inutiles)."""
    return {c for c in characteristics if c not in read and c not in exceptions}, set(exceptions) & read


def test_the_base_has_the_52_characteristics() -> None:
    assert len(CHARACTERISTICS) == 52 and set(CHARACTERISTICS) <= set(HEADER)


def test_every_characteristic_is_read_by_the_engine_or_listed_as_an_exception() -> None:
    missing, stale = coverage_gaps(CHARACTERISTICS, read_characteristics(set(_reads()), _field_reads()),
                                   COVERAGE_EXCEPTIONS)
    assert not missing, f"caractéristique de la base ni lue par v2engine/ ni en exception : {sorted(missing)}"
    assert not stale, f"exception devenue inutile (caractéristique lue) : la retirer de COVERAGE_EXCEPTIONS : {sorted(stale)}"


def test_every_exception_is_a_characteristic_and_cites_its_ticket() -> None:
    assert set(COVERAGE_EXCEPTIONS) <= set(CHARACTERISTICS)
    assert all(TICKET.search(why) for why in COVERAGE_EXCEPTIONS.values())


def test_the_coverage_guard_fails_on_a_fake_characteristic() -> None:
    read = read_characteristics(set(_reads()), _field_reads())
    assert coverage_gaps(("Bidon", "Pace"), read, {}) == ({"Bidon"}, set())
    assert coverage_gaps(("Pace",), read, {"Pace": "v2-x/1"}) == (set(), {"Pace"})


# --- Gestes préférés (repris du ticket v2-attributs-restants/05) : chaque valeur de la base est rattachée à un
# mécanisme et à son ticket porteur (grille du ticket 05) ; les paires contradictoires sont signalées, jamais additionnées.

MOVES_SEPARATOR = " ; "
_DRIBBLE = ("Conduite et dribble", "v2-collectif/19 ; v2-attributs-restants/07")
_PASS = ("Passe", "v2-collectif/19, 13, 14")
_RUN = ("Appels sans ballon", "v2-collectif/16, 23 ; 19 pour la conduite")
_SHOT = ("Tir", "v2-collectif/28a ; v2-attributs-restants/10a, 10b")
_AIR = ("Jeu aérien et centres", "v2-attributs-restants/01, 11")
_FOOT = ("Pied", "v2-attributs-restants/04")
_SET = ("Coups de pied arrêtés", "v2-attributs-restants/02")
_KEEPER = ("Gardien", "v2-attributs-restants/03")
_TACKLE = ("Tacle", "v2-attributs-restants/09a")
_DISCIPLINE = ("Discipline et ambiance", "v2-attributs-restants/09 ; v2-mise-en-scene/04")
PREFERRED_MOVES = {
    **dict.fromkeys(["Runs With Ball Often", "Runs With Ball Rarely", "Runs With Ball Down Left", "Runs With Ball Down Right",
                     "Runs With Ball Through The Centre", "Likes To Beat Opponent Repeatedly", "Knocks Ball Past Opponent",
                     "Tries Tricks", "Bring Ball Out of Defence", "Dwells On Ball", "Tries To Play Way Out Of Trouble",
                     "Cuts Inside From Left Wing", "Cuts Inside From Right Wing", "Cuts Inside From Both Wings"], _DRIBBLE),
    **dict.fromkeys(["Plays Short Simple Passes", "Plays No Through Balls", "Tries Killer Balls Often", "Tries Long Range Passes",
                     "Likes To Switch Ball To Wide Areas", "Plays One-Twos", "Dictates Tempo", "Stops Play",
                     "Looks For Pass Rather Than Attempting To Score", "Uses Outside Of Foot",
                     "Likes Ball Played Into Feet"], _PASS),  # aussi côté receveur (appels)
    **dict.fromkeys(["Gets Forward Whenever Possible", "Gets Into Opposition Area", "Arrives Late In Opposition Area",
                     "Moves Into Channels", "Comes Deep To Get Ball", "Plays With Back To Goal",
                     "Likes To Try To Break Offside Trap", "Stays Back At All Times", "Penalty Box Player", "Hugs Line"], _RUN),
    **dict.fromkeys(["Shoots From Distance", "Refrains From Taking Long Shots", "Places Shots", "Shoots With Power",
                     "Tries First Time Shots", "Likes To Round Keeper", "Likes To Lob Keeper",
                     "Curls Ball"], _SHOT),  # aussi centres et coups francs enroulés
    **dict.fromkeys(["Crosses Early", "Attempts Overhead Kicks"], _AIR),
    **dict.fromkeys(["Avoids Using Weaker Foot", "Moves Ball To Left Foot Before Dribble Attempt",
                     "Moves Ball To Right Foot Before Dribble Attempt"], _FOOT),
    **dict.fromkeys(["Hits Free Kicks With Power", "Tries Long Range Free Kicks", "Demands to Take Penalties",
                     "Possesses Long Flat Throw"], _SET),
    "Uses Long Throw To Start Counter Attacks": _KEEPER,
    **dict.fromkeys(["Dives Into Tackles", "Does Not Dive Into Tackles"], _TACKLE),
    **dict.fromkeys(["Argues With Officials", "Winds Up Opponents", "Gets Crowd Going"], _DISCIPLINE),
    "(aucun)": ("Aucun", "neutre"),
}
_CUTS_INSIDE = ("Cuts Inside From Left Wing", "Cuts Inside From Right Wing", "Cuts Inside From Both Wings")
CONTRADICTORY_PAIRS = [("Runs With Ball Often", "Runs With Ball Rarely"), ("Dives Into Tackles", "Does Not Dive Into Tackles"),
                       ("Shoots From Distance", "Refrains From Taking Long Shots"),
                       ("Gets Forward Whenever Possible", "Stays Back At All Times"), ("Places Shots", "Shoots With Power"),
                       *((cut, "Hugs Line") for cut in _CUTS_INSIDE)]
# Anomalie connue de la base, signalée et non corrigée (décision du propriétaire du 14/11/2026)
KNOWN_CONTRADICTIONS = {("Nicolò Cambiaghi", "Cuts Inside From Both Wings", "Hugs Line")}


def players_moves(header: tuple[str, ...], rows: list[tuple]) -> dict[str, list[str]]:
    first, last, moves = header.index("Prénom"), header.index("Nom"), header.index("Preferred moves")
    return {f"{r[first]} {r[last]}": [m.strip() for m in str(r[moves]).split(MOVES_SEPARATOR.strip()) if m.strip()]
            for r in rows if r[moves]}


def unknown_moves(moves: dict[str, list[str]]) -> set[str]:
    return {m for ms in moves.values() for m in ms} - set(PREFERRED_MOVES)


def contradictions(moves: dict[str, list[str]]) -> set[tuple[str, str, str]]:
    return {(name, a, b) for name, ms in moves.items() for a, b in CONTRADICTORY_PAIRS if a in ms and b in ms}


MOVES = players_moves(HEADER, ROWS)


def test_every_preferred_move_of_the_base_is_attached_to_a_mechanism_and_a_ticket() -> None:
    distinct = {m for ms in MOVES.values() for m in ms}
    assert len(distinct) == 59  # 58 gestes et « (aucun) », le 14/11/2026
    assert not unknown_moves(MOVES), f"geste de la base sans rattachement (grille du ticket 05) : {unknown_moves(MOVES)}"
    assert not set(PREFERRED_MOVES) - distinct, "geste de la grille absent de la base : grille à revoir"
    assert all(mechanism and ticket for mechanism, ticket in PREFERRED_MOVES.values())


def test_contradictory_moves_are_reported_not_added() -> None:
    assert contradictions(MOVES) == KNOWN_CONTRADICTIONS, "nouvelle paire contradictoire dans la base : la signaler"


def test_the_moves_guard_fails_on_fake_players() -> None:
    fake = {"A": ["Tries Tricks", "Does A Backflip"], "B": ["Runs With Ball Often", "Runs With Ball Rarely"]}
    assert unknown_moves(fake) == {"Does A Backflip"}
    assert contradictions(fake) == {("B", "Runs With Ball Often", "Runs With Ball Rarely")}

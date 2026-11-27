"""Rayon des attributs, garde du registre des contextes (ADR 0002, ticket v2-attributs-contextes/02 ; avant : liste
blanche de modules et refus des mélanges, ticket v2-collectif/18). Analyse de l'arbre syntaxique (ast), pas du texte.

Cinq vérifications, chacune avec un cas négatif synthétique :
1. chaque contexte du registre est documenté dans la section « Contextes » de docs/CARTE_ATTRIBUTS_V2.md (nom, effet,
   attributs et poids) ;
2. ses poids somment à 1 ;
3. aucune note n'est lue hors du registre et de la façade : `player_attribute` réservé à la façade, `intrinsic_rating`
   au chargement, nom non littéral seulement dans `contextes.contextual_rating`, et aucun calcul ne combine plusieurs
   attributs hors du registre, sauf les cumuls d'une autre forme listés (`CUMULS_HORS_REGISTRE` : A8, R5, A17) ;
4. un effet n'a qu'un contexte : identifiants d'effet distincts, et chaque contexte est lu par la seule fonction qui
   porte son effet (R1, « un effet, un calcul ») ;
5. chaque attribut non spécialiste lu par le moteur figure dans au moins deux contextes, sauf liste de transition datée
   (`TRANSITION`, chaque entrée liée à son ticket de branchement), qui se vide au fil des tickets.

Une lecture directe d'un seul attribut par la façade (`effective_rating(joueur, "Nom")`) reste permise partout : ce
n'est pas un mélange. Limite connue : un mélange qui passe par des variables intermédiaires (a = A ; b = B ; a + b) ou
par des fonctions séparées n'est pas détecté ; la grille de relecture de la carte le couvre."""

from __future__ import annotations

import ast
import math
import pathlib
import re
from types import SimpleNamespace

import openpyxl

import v2engine.contextes as contextes
from ligue1sim.players import FM_ATTRIBUTE_COLUMNS
from v2engine.contextes import CONTEXTES

ENGINE = pathlib.Path(__file__).resolve().parents[1] / "v2engine"
CARTE = ENGINE.parent / "docs" / "CARTE_ATTRIBUTS_V2.md"
PHYSICAL_FIELDS = {"pace": "Pace", "acceleration": "Acceleration", "stamina": "Stamina"}

# Lecture d'une note : la façade `condition.effective_rating` (jeu), `condition.intrinsic_rating` (chargement), ou
# `attributes.player_attribute` (réservé à la façade depuis le ticket v2-realisme/19a).
READERS = {"player_attribute", "effective_rating", "intrinsic_rating"}
REGISTRY = "contextes"  # module du registre : ses lectures sont celles de `contextual_rating`
CONTEXT_READER = "contextual_rating"
# Lecteur -> modules où il peut être appelé (R6)
READER_MODULES = {"player_attribute": {"attributes", "condition"}, "intrinsic_rating": {"condition", "match"}}

# Cumuls d'une autre forme qu'une somme pondérée de notes, hors du registre (carte, section « Contextes ») :
# attributs -> fonctions qui les lisent ensemble. Un mélange de ces attributs est toléré dans ces fonctions seulement.
CUMULS_HORS_REGISTRE = {
    # A8 : note du gardien, 0,5 Reflexes + 0,3 One on Ones + 0,2 Handling, jusqu'au ticket v2-attributs-restants/03b
    frozenset({"Reflexes", "One on Ones", "Handling"}): {"shooting._keeper_rating"},
    # R5 : temps d'arrivée, course à vitesse de pointe + montée en régime, deux capacités en secondes
    frozenset({"Pace", "Acceleration"}): {"defense.arrival_time_s"},
    # A17 : ballon dur à orienter, part First Touch x (1 - dureté x (1 - part Technique)), un produit par fonctions
    # séparées (invisible au détecteur de mélange, déclaré ici pour la traçabilité)
    frozenset({"First Touch", "Technique"}): {"possession.oriented_control_probability",
                                               "possession.hard_ball_technique_share"},
}

# Spécialités (ADR 0002, point 1) : peuvent rester dans un seul contexte.
SPECIALITES = {"Finishing", "Long Shots", "Penalty Taking", "Corners", "Free Kick Taking", "Long Throws", "Kicking",
               "Throwing"}
# Liste de transition (17/11/2026, ticket v2-attributs-contextes/02, choix du propriétaire : seuls les contextes du
# registre comptent) : attribut lu par le moteur, non spécialiste, dans moins de deux contextes -> (date, ticket qui
# le branchera). Une entrée devenue inutile fait échouer : la liste se vide au fil des tickets.
_REST = "v2-attributs-contextes/08"
TRANSITION = {
    # Work Rate : premier contexte « repli après la perte » au ticket v2-attributs-contextes/03 (réduit) ; le second,
    # sans effet sur les buts, au ticket 08 (décision du propriétaire du 17/11/2026, ticket 03m)
    "Work Rate": ("17/11/2026", _REST),
    # Vision : premier contexte « lecture du pressing » au ticket v2-collectif/15b1 ; Decisions et Anticipation en
    # sont sortis au ticket v2-attributs-contextes/04a (second contexte : « choix défensif »)
    "Positioning": ("17/11/2026", "v2-attributs-contextes/04b"),
    "Flair": ("17/11/2026", "v2-attributs-contextes/05"),
    "Balance": ("17/11/2026", "v2-attributs-contextes/06"),
    "Vision": ("17/11/2026", _REST),
    "Reflexes": ("17/11/2026", "v2-attributs-restants/03b"),
    # Jumping Reach : lu pour la hauteur atteinte en saut (ticket v2-hauteur-ballon/03a) ; second contexte au duel aérien
    "Jumping Reach": ("27/11/2026", "v2-realisme/15b"),
    "One on Ones": ("17/11/2026", "v2-attributs-restants/03b"),
    "Handling": ("17/11/2026", "v2-attributs-restants/03b"),
    **{attribute: ("17/11/2026", _REST) for attribute in (
        "Pace", "Acceleration", "Stamina", "Agility", "Strength", "Aggression", "Tackling", "Marking", "Teamwork",
        "Off the Ball", "Composure", "Passing", "Dribbling", "First Touch")},
}
TICKET = re.compile(r"(v2-[a-z-]+/\d+[a-z]?\d?|D-V\d+)")
DATE = re.compile(r"^\d{2}/\d{2}/\d{4}$")


def _modules():
    for path in sorted(ENGINE.rglob("*.py")):
        yield path.relative_to(ENGINE).with_suffix("").as_posix().replace("/", "."), ast.parse(path.read_text(encoding="utf-8"))


def _called(node: ast.Call) -> str | None:
    return getattr(node.func, "id", getattr(node.func, "attr", None))


def _attribute_calls(tree: ast.AST):
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and _called(node) in READERS:
            yield node


def _name(call: ast.Call) -> str | None:
    arg = call.args[1] if len(call.args) > 1 else next((k.value for k in call.keywords if k.arg == "name"), None)
    return arg.value if isinstance(arg, ast.Constant) and isinstance(arg.value, str) else None


def _enclosing(tree: ast.AST) -> dict[int, str]:
    """id(nœud) -> nom de la fonction la plus interne qui le contient (« <module> » au niveau du module)."""
    owner: dict[int, str] = {}

    def visit(node: ast.AST, current: str) -> None:
        for child in ast.iter_child_nodes(node):
            name = child.name if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) else current
            owner[id(child)] = name
            visit(child, name)
    visit(tree, "<module>")
    return owner


def _reads() -> dict[str, set[str]]:
    """Attribut -> modules qui le lisent (nom littéral ; chaque attribut d'un contexte compte comme lu par le
    registre). Sert à la garde de couverture."""
    found: dict[str, set[str]] = {}
    for module, tree in _modules():
        for call in _attribute_calls(tree):
            if (name := _name(call)) is not None:
                found.setdefault(name, set()).add(module)
    for contexte in CONTEXTES.values():
        for attribute in contexte.attributs:
            found.setdefault(attribute, set()).add(REGISTRY)
    return found


# --- 1. Chaque contexte est documenté dans la carte -----------------------------------------------------------------

WEIGHT_DECIMALS = 3  # la carte écrit un poids à trois décimales au plus (1/3 -> « 0,333 ») ; réserve A3, ticket 02b


def _documented_weight(row: str, attribute: str) -> float | None:
    """Poids écrit dans la ligne de carte après « Attribut » (« Dribbling 0,6 »), ou None."""
    found = re.search(rf"(?<!\w){re.escape(attribute)} (\d+(?:,\d+)?)", row)
    return float(found.group(1).replace(",", ".")) if found else None


def carte_contexts_section(text: str) -> str:
    start = text.index("## Contextes")
    return text[start:text.index("\n---", start)]


def undocumented_contexts(contexts, section: str) -> set[str]:
    """Contextes sans ligne de table qui porte leur nom, leur effet et chaque « Attribut poids », le poids écrit étant
    celui du registre arrondi à `WEIGHT_DECIMALS` décimales (comparaison numérique, pas textuelle)."""
    rows = [line for line in section.splitlines() if line.startswith("|")]
    return {c.nom for c in contexts
            if not any(c.nom in row and f"`{c.effet}`" in row
                       and all(_documented_weight(row, a) == round(w, WEIGHT_DECIMALS) for a, w in c.poids)
                       for row in rows)}


def test_every_context_is_documented_in_the_map() -> None:
    section = carte_contexts_section(CARTE.read_text(encoding="utf-8"))
    assert not undocumented_contexts(CONTEXTES.values(), section), \
        f"contexte absent de la section « Contextes » de la carte : {undocumented_contexts(CONTEXTES.values(), section)}"


def test_the_documentation_check_fails_on_a_fake_or_changed_context() -> None:
    section = carte_contexts_section(CARTE.read_text(encoding="utf-8"))
    fake = SimpleNamespace(nom="bidon", effet="scan.bidon", poids=(("Vision", 0.5), ("Decisions", 0.5)))
    changed = SimpleNamespace(nom="porteur tête haute", effet="scan.head_up_share",
                              poids=(("Dribbling", 0.5), ("Technique", 0.5)))  # poids différents de la carte
    assert undocumented_contexts([fake, changed], section) == {"bidon", "porteur tête haute"}


def test_the_documentation_check_compares_weights_as_numbers() -> None:
    # réserve A3 (ticket 02b) : un poids comme 1/3 s'écrit « 0,333 » dans la carte, pas « 0,333333 »
    third = SimpleNamespace(nom="tiers", effet="scan.f", poids=(("Vision", 1 / 3), ("Decisions", 2 / 3)))
    row = "| tiers | perception | Vision {} ; Decisions {} | `scan.f` | non trouvé | v2-x/1 |"
    assert not undocumented_contexts([third], row.format("0,333", "0,667"))
    assert undocumented_contexts([third], row.format("0,33", "0,67")) == {"tiers"}  # arrondi insuffisant
    assert undocumented_contexts([third], row.format("0,333", "0,6")) == {"tiers"}  # poids faux


# --- 2. Poids sommant à 1 -------------------------------------------------------------------------------------------

def bad_weight_sums(contexts) -> set[str]:
    return {c.nom for c in contexts if not math.isclose(sum(w for _, w in c.poids), 1.0, abs_tol=1e-12)}


def test_every_context_has_weights_summing_to_one() -> None:
    assert not bad_weight_sums(CONTEXTES.values())


def test_the_weight_check_fails_on_a_fake_context() -> None:
    # objet brut : le constructeur `Contexte` refuserait déjà ce cas (test_v2engine_contextes)
    fake = SimpleNamespace(nom="bidon", poids=(("Vision", 0.6), ("Decisions", 0.3)))
    assert bad_weight_sums([fake]) == {"bidon"}


# --- 3. Aucune lecture hors du registre et de la façade ------------------------------------------------------------

def reads_outside_facade(modules) -> set[tuple[str, str, str]]:
    """(module, fonction, motif) des lectures interdites : lecteur réservé appelé ailleurs, ou nom non littéral hors
    de `contextes.contextual_rating` (réserve A2 de l'expert, ticket 01)."""
    bad = set()
    for module, tree in modules:
        owner = _enclosing(tree)
        for call in _attribute_calls(tree):
            reader, where = _called(call), owner.get(id(call), "<module>")
            if module not in READER_MODULES.get(reader, {module}):
                bad.add((module, where, f"{reader} réservé"))
            if (_name(call) is None and module not in READER_MODULES["player_attribute"]
                    and (module, where) != (REGISTRY, CONTEXT_READER)):
                bad.add((module, where, "nom non littéral"))
    return bad


def _attrs_in(node: ast.AST) -> set[str]:
    return {name for call in _attribute_calls(node) if (name := _name(call))}


def mixes_outside_registry(modules, tolerated: dict[frozenset, set[str]]) -> set[tuple[str, frozenset]]:
    """(module.fonction, attributs) des calculs (+, -, *, /) qui combinent plusieurs notes hors du registre et hors
    des cumuls tolérés dans leur fonction."""
    bad = set()
    for module, tree in modules:
        owner = _enclosing(tree)
        for node in ast.walk(tree):
            if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
                attrs, where = frozenset(_attrs_in(node)), f"{module}.{owner.get(id(node), '<module>')}"
                if len(attrs) > 1 and not any(attrs <= cumul and where in places
                                              for cumul, places in tolerated.items()):
                    bad.add((where, attrs))
    return bad


def test_no_note_is_read_outside_the_registry_and_the_facade() -> None:
    assert not reads_outside_facade(_modules()), f"lecture hors façade et registre : {reads_outside_facade(_modules())}"
    mixes = mixes_outside_registry(_modules(), CUMULS_HORS_REGISTRE)
    assert not mixes, f"calcul qui combine des attributs hors du registre (déclarer un contexte) : {mixes}"


def _parse(source: str, module: str = "faux"):
    return [(module, ast.parse(source))]


def test_the_read_check_fails_on_fake_modules() -> None:
    old_tackle = 'def f(t):\n    return 0.8 * effective_rating(t, "Tackling") + 0.2 * effective_rating(t, "Aggression")'
    assert mixes_outside_registry(_parse(old_tackle, "duel"), CUMULS_HORS_REGISTRE) == {
        ("duel.f", frozenset({"Tackling", "Aggression"}))}
    # un cumul toléré ne l'est que dans sa fonction
    keeper = 'def g(k):\n    return effective_rating(k, "Reflexes") + effective_rating(k, "Handling")'
    assert mixes_outside_registry(_parse(keeper, "shooting"), CUMULS_HORS_REGISTRE)
    assert not mixes_outside_registry(_parse(keeper.replace("def g", "def _keeper_rating"), "shooting"),
                                      CUMULS_HORS_REGISTRE)
    sneaky = 'def h(p, name):\n    return effective_rating(p, name)'
    assert reads_outside_facade(_parse(sneaky, "decision")) == {("decision", "h", "nom non littéral")}
    assert reads_outside_facade(_parse(sneaky.replace("def h", "def autre"), REGISTRY)) == {
        (REGISTRY, "autre", "nom non littéral")}
    raw = 'def r(p):\n    return player_attribute(p, "Vision")'
    assert reads_outside_facade(_parse(raw, "decision")) == {("decision", "r", "player_attribute réservé")}


def test_every_out_of_registry_cumul_still_exists() -> None:
    owner_reads: dict[str, set[str]] = {}
    for module, tree in _modules():
        owner = _enclosing(tree)
        for call in _attribute_calls(tree):
            if (name := _name(call)) is not None:
                owner_reads.setdefault(f"{module}.{owner.get(id(call), '<module>')}", set()).add(name)
    stale = {cumul for cumul, places in CUMULS_HORS_REGISTRE.items()
             if not cumul <= set().union(*(owner_reads.get(p, set()) for p in places))}
    assert not stale, f"cumul hors registre levé : le retirer de CUMULS_HORS_REGISTRE et de la carte : {stale}"


# --- 4. Un effet, un contexte, un calcul ----------------------------------------------------------------------------

def _context_uses(modules) -> dict[str, set[str]]:
    """Nom de contexte -> fonctions (module.fonction) qui appellent `contextual_rating` avec lui."""
    by_constant = {name: value.nom for name, value in vars(contextes).items() if isinstance(value, contextes.Contexte)}
    uses: dict[str, set[str]] = {}
    for module, tree in modules:
        owner = _enclosing(tree)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and _called(node) == CONTEXT_READER:
                # positionnel ou nommé (`contexte=`, réserve A2, ticket 02b) ; absent : contexte inconnu, refusé
                arg = node.args[1] if len(node.args) > 1 else next(
                    (k.value for k in node.keywords if k.arg == "contexte"), None)
                key = (by_constant.get(getattr(arg, "id", getattr(arg, "attr", None)))
                       or (arg.value if isinstance(arg, ast.Constant) else "<contexte non littéral>"))
                uses.setdefault(key, set()).add(f"{module}.{owner.get(id(node), '<module>')}")
    return uses


def effect_conflicts(contexts, uses: dict[str, set[str]]) -> set[str]:
    """Effets déclarés par deux contextes, et contextes lus ailleurs que par la seule fonction de leur effet."""
    seen: dict[str, str] = {}
    bad = set()
    for c in contexts:
        if c.effet in seen:
            bad.add(f"effet {c.effet} : {seen[c.effet]} et {c.nom}")
        seen[c.effet] = c.nom
        if uses.get(c.nom, set()) != {c.effet}:
            bad.add(f"{c.nom} lu par {sorted(uses.get(c.nom, set()))} au lieu de {c.effet}")
    bad |= {f"contexte inconnu {name} lu par {sorted(where)}" for name, where in uses.items()
            if name not in {c.nom for c in contexts}}
    return bad


def test_each_effect_has_one_context_and_one_calculation() -> None:
    conflicts = effect_conflicts(CONTEXTES.values(), _context_uses(_modules()))
    assert not conflicts, f"règle R1 (un effet, un calcul) : {conflicts}"


def test_the_effect_check_fails_on_fake_contexts() -> None:
    a = SimpleNamespace(nom="a", effet="scan.f")
    b = SimpleNamespace(nom="b", effet="scan.f")  # même effet que a
    uses = {"a": {"scan.f"}, "b": {"scan.f", "decision.g"}}  # b relu dans une autre fonction
    assert effect_conflicts([a, b], uses) == {"effet scan.f : a et b",
                                             "b lu par ['decision.g', 'scan.f'] au lieu de scan.f"}
    assert effect_conflicts([a], {"a": {"scan.f"}, "c": {"x.y"}}) == {"contexte inconnu c lu par ['x.y']"}


def test_a_context_passed_by_keyword_is_counted() -> None:
    # réserve A2 (ticket 02b) : un appel `contextual_rating(p, contexte=X)` est vu comme une lecture de X
    source = "def g(p):\n    return contextual_rating(p, contexte=PORTEUR_TETE_HAUTE)"
    assert _context_uses(_parse(source, "decision")) == {"porteur tête haute": {"decision.g"}}
    assert _context_uses(_parse("def g(p, c):\n    return contextual_rating(p, contexte=c)", "decision")) == {
        "<contexte non littéral>": {"decision.g"}}


# --- 5. Chaque attribut non spécialiste dans au moins deux contextes ------------------------------------------------

def contexts_per_attribute(contexts) -> dict[str, int]:
    count: dict[str, int] = {}
    for c in contexts:
        for attribute in c.attributs:
            count[attribute] = count.get(attribute, 0) + 1
    return count


def reach_gaps(read: set[str], contexts, specialities: set[str], transition: dict) -> tuple[set[str], set[str]]:
    """(attributs non spécialistes lus dans moins de deux contextes et absents de la transition, entrées de transition
    devenues inutiles)."""
    count = contexts_per_attribute(contexts)
    short = {a for a in read - specialities if count.get(a, 0) < 2}
    return short - set(transition), set(transition) - short


def test_every_non_specialist_attribute_is_in_two_contexts_or_in_transition() -> None:
    missing, stale = reach_gaps(set(_reads()) & set(FM_ATTRIBUTE_COLUMNS), CONTEXTES.values(), SPECIALITES, TRANSITION)
    assert not missing, f"attribut dans moins de deux contextes, hors liste de transition : {sorted(missing)}"
    assert not stale, f"entrée de transition devenue inutile (ou attribut plus lu) : la retirer : {sorted(stale)}"


def test_every_transition_entry_is_dated_and_cites_its_ticket() -> None:
    assert all(DATE.match(date) and TICKET.search(ticket) for date, ticket in TRANSITION.values())
    assert not set(TRANSITION) & SPECIALITES


def test_the_reach_check_fails_on_fake_attributes() -> None:
    two = [SimpleNamespace(attributs=("Vision", "Decisions")), SimpleNamespace(attributs=("Vision", "Passing"))]
    assert reach_gaps({"Vision", "Decisions", "Finishing"}, two, {"Finishing"}, {}) == ({"Decisions"}, set())
    assert reach_gaps({"Vision", "Decisions"}, two, set(), {"Decisions": ("17/11/2026", "v2-x/1"),
                                                             "Vision": ("17/11/2026", "v2-x/2")}) == (set(), {"Vision"})


# --- Gardes conservées : dictionnaire brut, champs physiques ------------------------------------------------------

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
    # Depuis le ticket v2-realisme/19a, une capacité physique se lit par la façade ; le champ (`.pace`…) ne se lit que
    # dans le chemin chaud de `movement.step`.
    found: dict[str, set[str]] = {}
    for module, tree in _modules():
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr in PHYSICAL_FIELDS and isinstance(node.ctx, ast.Load):
                found.setdefault(PHYSICAL_FIELDS[node.attr], set()).add(module)
    outside = {attr: mods - {"movement"} for attr, mods in found.items() if mods - {"movement"}}
    assert not outside, f"capacité physique lue par son champ hors de movement (passer par la façade) : {outside}"


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

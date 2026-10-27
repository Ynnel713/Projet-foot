"""Rayon des attributs (ticket v2-collectif/18, règle anti double comptage de docs/CARTE_ATTRIBUTS_V2.md) : chaque
attribut n'est lu que dans les modules du moteur qui portent son rayon, et deux attributs ne se mélangent pas dans
un même calcul hors des dérogations listées. Ajouter un attribut ailleurs, c'est ajouter un effet : mettre d'abord à
jour la carte, puis cette liste. Analyse de l'arbre syntaxique (ast), pas du texte.

Limite connue : un mélange qui passe par des variables intermédiaires (a = A ; b = B ; a + b) n'est pas détecté ; la
grille de relecture de la carte le couvre."""

from __future__ import annotations

import ast
import pathlib

ENGINE = pathlib.Path(__file__).resolve().parents[1] / "v2engine"
PHYSICAL_FIELDS = {"pace": "Pace", "acceleration": "Acceleration", "stamina": "Stamina"}

# Attribut -> modules où il peut être lu (rayon de docs/CARTE_ATTRIBUTS_V2.md). « match » : construction des joueurs
# (Pace, Acceleration, Stamina recopiés dans PlayerState) et déclenchement du tacle (Aggression). Les physiques lus
# ensuite par leur champ (`.pace`…) sont des capacités (règle R5) : modules listés à part.
ALLOWED = {
    "Pace": {"match"},
    "Acceleration": {"match"},
    "Stamina": {"match"},
    "Strength": {"duel"},
    "Balance": {"duel"},
    "Aggression": {"duel", "match"},  # fréquence des tentatives et faute, jamais la réussite du tacle
    "Tackling": {"duel"},
    "Anticipation": {"anticipation"},
    "Decisions": {"decision"},
    "Vision": {"decision"},
    "Off the Ball": {"off_ball"},
    "Composure": {"possession", "shooting"},
    "First Touch": {"possession"},
    "Passing": {"possession"},
    "Finishing": {"shooting"},
    "Reflexes": {"shooting"},
    "One on Ones": {"shooting"},
    "Handling": {"shooting"},
    "Positioning": {"bloc"},  # erreur de placement dans le bloc (ticket v2-collectif/04)
    "Teamwork": {"bloc"},  # écart toléré avant de se replacer (ticket v2-collectif/04)
}
PHYSICAL_ALLOWED = {"Pace": {"movement", "anticipation"}, "Acceleration": {"movement"}, "Stamina": {"movement"}}
# Mélanges de plusieurs attributs dans un même calcul tolérés (dérogations de la carte).
TOLERATED_MIXES = {
    frozenset({"Finishing", "Composure"}),  # A2 : jusqu'au ticket du tir
    frozenset({"Strength", "Balance"}),  # A3 : jusqu'à l'étape duels
    frozenset({"Reflexes", "One on Ones", "Handling"}),  # A8 : note du gardien, jusqu'à la phase 9 (confirmée le 26/10/2026)
}


def _modules():
    for path in sorted(ENGINE.rglob("*.py")):
        yield path.relative_to(ENGINE).with_suffix("").as_posix().replace("/", "."), ast.parse(path.read_text(encoding="utf-8"))


def _attribute_calls(tree: ast.AST):
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, "id", getattr(node.func, "attr", None)) == "player_attribute":
            yield node


def _name(call: ast.Call) -> str | None:
    arg = call.args[1] if len(call.args) > 1 else next((k.value for k in call.keywords if k.arg == "name"), None)
    return arg.value if isinstance(arg, ast.Constant) and isinstance(arg.value, str) else None


def _reads() -> dict[str, set[str]]:
    found: dict[str, set[str]] = {}
    for module, tree in _modules():
        for call in _attribute_calls(tree):
            found.setdefault(_name(call) or "<nom non littéral>", set()).add(module)
    return found


def test_each_attribute_is_read_only_within_its_reach() -> None:
    reads = _reads()
    assert "<nom non littéral>" not in reads or reads["<nom non littéral>"] <= {"attributes"}, \
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


def test_physical_fields_are_read_only_where_a_capacity_is_needed() -> None:
    found: dict[str, set[str]] = {}
    for module, tree in _modules():
        for node in ast.walk(tree):
            if (isinstance(node, ast.Attribute) and node.attr in PHYSICAL_FIELDS and isinstance(node.ctx, ast.Load)
                    and module != "match"):
                found.setdefault(PHYSICAL_FIELDS[node.attr], set()).add(module)
    found = {attr: mods - {"movement"} if attr != "Pace" else mods for attr, mods in found.items()}
    # movement recopie les trois champs dans le nouvel état (`pace=state.pace`) : ce n'est pas un usage
    outside = {attr: mods - PHYSICAL_ALLOWED[attr] for attr, mods in found.items() if mods - PHYSICAL_ALLOWED[attr]}
    assert not outside, f"capacité physique lue hors des modules listés (règle R5) : {outside}"


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

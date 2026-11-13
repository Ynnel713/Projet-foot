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

# Lecture d'une note : la façade `condition.effective_rating` (jeu), `condition.intrinsic_rating` (chargement), ou
# `attributes.player_attribute` (réservé à la façade depuis le ticket v2-realisme/19a).
READERS = {"player_attribute", "effective_rating", "intrinsic_rating"}

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
    "Technique": {"possession", "scan"},  # précision de la talonnade, geste difficile (07e) ; porteur tête haute avec Dribbling (08c)
    "Flair": {"decision"},  # penser à la talonnade (ticket v2-realisme/07e)
    "Strength": {"duel"},
    "Balance": {"duel"},
    "Aggression": {"duel", "match", "defense"},  # fréquence des tentatives et faute ; distance d'arrêt du presseur (08)
    "Tackling": {"duel"},
    # + drapeau du hors-jeu (23) ; ligne fermée au pressing (08) ; perception du porteur : prolonger la course des
    # adversaires pendant sa conduite (ticket v2-collectif/33)
    "Anticipation": {"anticipation", "match", "defense", "decision"},
    "Decisions": {"decision", "restart"},  # restart : choix du receveur d'une remise en jeu (ticket 29)
    "Vision": {"decision", "off_ball", "scan"},  # + le coureur tente l'appel dans le dos si le porteur le voit (16) ; fréquence des scans (08c)
    "Off the Ball": {"off_ball", "offside"},  # + régler l'appel sur la ligne du hors-jeu (ticket 23)
    # tir sous pression par `shooting.shot_composure_factor`, courbe propre (ticket 28a) ; + perception sous pression (33)
    "Composure": {"possession", "decision", "shooting"},
    "Dribbling": {"decision", "scan"},  # (scan : porteur tête haute, cumul avec Technique, 08c) chance de garder le ballon en conduisant : valeur factuelle (ticket 33) et perte tirée (04a) ; vitesse balle au pied (04d)
    "First Touch": {"possession"},
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
    frozenset({"Strength", "Balance"}),  # A3 : jusqu'à l'étape duels
    frozenset({"Reflexes", "One on Ones", "Handling"}),  # A8 : note du gardien, jusqu'à la phase 9 (confirmée le 26/10/2026)
    # temps d'arrivée (`defense.arrival_time_s`) : course à vitesse de pointe + montée en régime, deux capacités
    # physiques additionnées en secondes (règle R5), pas une pondération de notes ; visible depuis que les champs
    # passent par la façade (ticket v2-realisme/19a)
    frozenset({"Pace", "Acceleration"}),
    # porteur tête haute (`scan.head_up_share`, ticket v2-realisme/08c) : Dribbling 0,6 + Technique 0,4, cumul voulu par le
    # propriétaire (règle R2 révisée du 13/11/2026, A15)
    frozenset({"Dribbling", "Technique"}),
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
    return found


def test_each_attribute_is_read_only_within_its_reach() -> None:
    reads = _reads()
    assert "<nom non littéral>" not in reads or reads["<nom non littéral>"] <= {"attributes", "condition"}, \
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

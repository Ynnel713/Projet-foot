"""Grammaire des conditions de phrase (colonne "Condition" du classeur
Excel de commentaire, voir scripts/convert_commentary_xlsx_to_yaml.py) :
deux usages distincts, deux fonctions distinctes.

    parse_condition_atoms : PARSE-TIME. Decoupe une condition en texte libre
        ("Aggression >= 85 et preferred_moves contient \"Dives Into Tackles\"")
        en plusieurs atomes structures (attribute, operator, value) -- un par
        `phrase_conditions` a inserer (voir scripts/import_seed.py, qui
        attend deja une LISTE de conditions par phrase, jamais une chaine
        combinee). Utilisee UNIQUEMENT par le script de conversion, jamais au
        runtime -- une fois importee, chaque atome vit comme une
        PhraseCondition independante en base.

    evaluate_condition : RUNTIME. Evalue UNE PhraseCondition (deja
        structuree, deja en base) contre un (Player, MatchContext) donnes --
        consommee par phrase_selector.select une fois implemente (voir
        l'etape 4 de son algorithme prevu : "filtrer les phrases dont une
        condition mandatory=True echoue").

Pas de eval() ni d'ast.literal_eval sur l'expression entiere (decision du
brief "commentaire live quali", D6) : le contexte des conditions est un
classeur Excel edite a la main, une regex + une table d'operateurs bornee
est la surface d'attaque la plus etroite possible pour ce besoin."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from engine.models import MatchContext, PhraseCondition, Player

# Champs lus directement sur Player (dataclass), PAS dans son dict
# `attributes` (FM26, EAV) -- decision D3 du brief : fusion dans un seul
# espace de noms cote evaluateur, mais Player structure les deux
# differemment (champs nommes vs dict), donc l'evaluateur doit savoir ou
# chercher chaque nom. Precedence Player > FM26 : un nom de PLAYER_FIELDS
# qui apparaitrait aussi (par accident futur) dans FM26_ATTRIBUTES serait lu
# ici en premier -- voir tests/commentary/test_namespaces_attributs.py qui
# verifie qu'aucune collision de ce genre n'existe aujourd'hui.
# fm_rating ajoute le 01/10/2026 : champ Player lu par les pilotes REMPLACEMENT
# (phrase 6, surnom joker) -- sans cela _resolve levait ValueError.
# position ajoute le 01/10/2026 (decision A, HORS-JEU) : poste principal
# (BU, AG, AD, SA, MOC, MC, MDC, DC, LB, RB, GK), renseigne a 100 % (7563/7563).
PLAYER_FIELDS = frozenset({"age", "height_cm", "weak_foot", "foot", "fm_rating", "position"})

# Champs lus directement sur MatchContext (dataclass).
# is_home ajoute le 01/10/2026 (decision D1 du plan Tier 2, AMBIANCE) : une
# phrase peut conditionner sur domicile/exterieur ("is_home == true").
# sortant/entrant ajoutes (decision D3, plan V2.1) : champs de type Player, donc
# seuls ==/!= ont un sens dessus (un operateur d'ordre leverait TypeError) ; le
# choix de variante selon le profil du remplacement releve du selecteur (option
# C, SPEC_ANTI_REPEAT.md section 5), pas de cette grammaire.
MATCH_CONTEXT_FIELDS = frozenset({"minute", "score_context", "is_home", "sortant", "entrant"})

_ATOME_RE = re.compile(
    r'^\s*(\w+)\s*(<=|>=|!=|==|=|<|>)\s*(.+?)\s*$'
    r'|^\s*(\w+)\s+in\s*\[(.+?)\]\s*$'
    r'|^\s*(\w+)\s+contient\s+"(.+?)"\s*$'  # francais, pas "contains" -- voir les 48 conditions du classeur
)


@dataclass(frozen=True)
class ConditionAtom:
    """Un atome de condition deja decoupe, forme attendue par
    phrase_conditions (attribute, operator, value) -- voir
    scripts/import_seed.py::_insert_scenarios."""

    attribute: str
    operator: str
    value: str


def parse_condition_atoms(condition: str) -> list[ConditionAtom]:
    """Decoupe une condition en texte libre (colonne Excel) en une liste
    d'atomes structures -- un par PhraseCondition a inserer. Decoupe sur
    " et " (conjonction uniquement, pas de "ou"/negation/parentheses, voir
    docstring du module). Chaine vide/blanche -> liste vide (aucune
    condition -- la phrase peut sortir n'importe quand, voir instructions du
    classeur).

    Leve ValueError (avec le fragment fautif) si un atome ne correspond a
    aucune des 3 formes reconnues -- une condition mal ecrite doit faire
    echouer l'IMPORT, jamais produire une PhraseCondition silencieusement
    inerte (une phrase qui ne sort jamais faute d'avoir compris sa propre
    condition est un bug invisible, voir brief)."""
    if not condition or not condition.strip():
        return []
    atomes: list[ConditionAtom] = []
    for fragment in condition.split(" et "):
        fragment = fragment.strip()
        m = _ATOME_RE.match(fragment)
        if m is None:
            raise ValueError(f"Atome de condition non reconnu : {fragment!r} (dans {condition!r})")

        attribut, operateur, valeur = m.group(1), m.group(2), m.group(3)
        if attribut is None:
            attribut, operateur, valeur = m.group(4), "in", m.group(5)
        if attribut is None:
            attribut, operateur, valeur = m.group(6), "contient", m.group(7)

        atomes.append(ConditionAtom(attribute=attribut, operator=operateur, value=valeur))
    return atomes


def _resolve(name: str, player: Player, context: MatchContext) -> Any:
    """Valeur de `name` pour ce (player, context) -- precedence Player >
    FM26 > MatchContext (voir PLAYER_FIELDS/MATCH_CONTEXT_FIELDS ci-dessus).
    Leve ValueError si `name` n'est reconnu nulle part : un attribut absent
    du contexte ne doit jamais faire matcher silencieusement une condition
    (meme raisonnement que parse_condition_atoms)."""
    if name in PLAYER_FIELDS:
        return getattr(player, name)
    if name in player.attributes:
        return player.attributes[name]
    if name in MATCH_CONTEXT_FIELDS:
        return getattr(context, name)
    if name == "preferred_moves":
        return player.preferred_moves
    raise ValueError(f"Attribut {name!r} inconnu (ni champ Player, ni attribut FM26, ni champ MatchContext)")


def _comparer(gauche: Any, operateur: str, droite_brute: str) -> bool:
    # Bug corrige (brief "commentaire live quali", point B) : une valeur
    # textuelle entre guillemets ("reduit_ecart") gardait ses guillemets
    # avant comparaison -- ne matchait alors JAMAIS la valeur sans
    # guillemets du contexte (echec silencieux). Retirer les guillemets
    # AVANT la tentative de cast numerique, pas apres.
    # Valeur inconnue (ex. is_home=None, minute=None) : une condition ne
    # matche jamais sur une information absente (sinon "is_home != true"
    # matcherait un contexte sans domicile/exterieur connu).
    if gauche is None:
        return False
    droite_brute = droite_brute.strip()
    if len(droite_brute) >= 2 and droite_brute[0] == droite_brute[-1] == '"':
        droite_brute = droite_brute[1:-1]

    droite: Any = droite_brute
    for cast in (int, float):
        try:
            droite = cast(droite_brute)
            break
        except ValueError:
            continue

    if isinstance(gauche, bool):
        # is_home est un bool : "true"/"vrai" doivent matcher True, pas rester
        # du texte (True == "true" est False en Python -- meme famille d'echec
        # silencieux que les guillemets ci-dessus).
        droite = {"true": True, "vrai": True, "false": False, "faux": False}.get(
            droite_brute.lower(), droite
        )

    ops: dict[str, Any] = {
        "<": lambda a, b: a < b,
        "<=": lambda a, b: a <= b,
        ">": lambda a, b: a > b,
        ">=": lambda a, b: a >= b,
        "=": lambda a, b: a == b,
        "==": lambda a, b: a == b,
        "!=": lambda a, b: a != b,
    }
    return bool(ops[operateur](gauche, droite))


def evaluate_condition(condition: PhraseCondition, player: Player, context: MatchContext) -> bool:
    """Evalue UNE PhraseCondition (deja en base, deja structuree) contre
    `player`/`context` -- voir docstring du module pour la distinction avec
    parse_condition_atoms (parse-time, texte libre -> plusieurs
    PhraseCondition)."""
    gauche = _resolve(condition.attribute, player, context)

    if condition.operator == "in":
        # Comparaison en texte des deux côtés (comme _comparer caste
        # `droite`, pas `gauche`) : `gauche` peut être un int (ex.
        # weak_foot=4) alors que `membres` vient toujours du texte de la
        # condition -- `4 in ["4", "5"]` est False en Python, bug trouvé par
        # test_in_operator_checks_membership avant livraison.
        membres = [v.strip().strip('"') for v in condition.value.split(",")]
        return str(gauche) in membres
    if condition.operator == "contient":
        return condition.value in gauche
    return _comparer(gauche, condition.operator, condition.value)

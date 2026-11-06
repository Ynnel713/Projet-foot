"""Rôle de chaque joueur (ticket v2-realisme/02c) : un rôle par défaut pour chaque poste, remplacé par un rôle
dédié quand la colonne « Catégorie » de la base le prévoit (mezzala, box to box, pivot...). Table de données
uniquement : le rôle est porté par `PlayerState`, écrit dans la trace, et n'a AUCUN effet sur le jeu ici (les effets
arrivent en 02d, 02e, 09). Le choix du rôle par le coach est le ticket 13i.

Intention footballistique de chaque rôle (`ROLES`). Un même rôle peut venir de plusieurs postes (une mezzala est
MDC, MC ou MOC dans la base) : le poste donne la hauteur de départ, le rôle donne le comportement.

Règles : la catégorie est lue sans tenir compte de la casse, des accents ni des espaces de fin (la base contient
« Mezzala » et « mezzala », « pivot » et « pivot  »). Une catégorie absente, ou non prévue pour ce poste (un DC dit
« lateral defensif », un BU dit « ailier inverse »), donne le rôle par défaut du poste. Les noms de rôles et la
table sont des choix produit proposés par Claude et validés par délégation du propriétaire (06/11/2026)."""

from __future__ import annotations

import unicodedata

# rôle -> intention footballistique (documentation, vérifiée par un test : chaque rôle utilisé y figure)
ROLES: dict[str, str] = {
    "gardien": "protège le but, relance derrière la défense",
    "défenseur central": "garde l'axe de la défense, couvre et intercepte",
    "latéral": "tient son couloir, monte en soutien quand le jeu le permet",
    "latéral défensif": "reste derrière le ballon, ne monte que si la défense est couverte",
    "piston": "occupe tout le couloir, monte très haut, centre",
    "sentinelle": "se tient devant la défense, récupère et distribue simplement",
    "récupérateur": "presse et récupère les ballons, joue court après la récupération",
    "regista": "organise depuis une position reculée, passes longues et changements d'aile",
    "milieu relayeur": "relie défense et attaque, va-et-vient équilibré dans l'axe",
    "box to box": "couvre tout le terrain, porte le ballon et arrive dans la surface",
    "mezzala": "décroche dans le demi-espace, se projette vers le but depuis le côté de l'axe",
    "meneur": "crée le jeu entre les lignes, dernière passe",
    "milieu offensif": "joue entre les lignes dans l'axe, soutient l'avant-centre",
    "ailier de couloir": "reste large, déborde et centre",
    "ailier intérieur": "part du côté et rentre vers l'axe, frappe ou combine",
    "meneur excentré": "crée le jeu depuis le côté, repique dans l'axe pour la dernière passe",
    "second attaquant": "décroche derrière l'avant-centre, combine et se projette",
    "avant-centre": "attaque la profondeur et finit les actions",
    "buteur axial": "reste dans la surface et sur la ligne du hors-jeu, cherche la finition",
    "pivot": "se fait remiser le ballon dos au but, fait jouer les autres",
}

# poste -> rôle par défaut (le rôle standard de ceux qui n'ont pas de catégorie)
DEFAULT_ROLE: dict[str, str] = {
    "GK": "gardien",
    "DC": "défenseur central",
    "LB": "latéral",
    "RB": "latéral",
    "MDC": "sentinelle",
    "MC": "milieu relayeur",
    "MOC": "milieu offensif",
    "AG": "ailier de couloir",
    "AD": "ailier de couloir",
    "SA": "second attaquant",
    "BU": "avant-centre",
    "ATT": "avant-centre",
}

# (poste, catégorie normalisée) -> rôle dédié. Hors de cette table : rôle par défaut du poste.
_CATEGORY_ROLE: dict[tuple[str, str], str] = {
    ("LB", "piston"): "piston", ("RB", "piston"): "piston",
    ("LB", "lateral defensif"): "latéral défensif", ("RB", "lateral defensif"): "latéral défensif",
    ("MDC", "milieu recuperateur"): "récupérateur", ("MC", "milieu recuperateur"): "récupérateur",
    ("MDC", "regista"): "regista", ("MC", "regista"): "regista",
    ("MDC", "mezzala"): "mezzala", ("MC", "mezzala"): "mezzala", ("MOC", "mezzala"): "mezzala",
    ("MDC", "box to box"): "box to box", ("MC", "box to box"): "box to box", ("MOC", "box to box"): "box to box",
    ("MC", "meneur"): "meneur", ("MOC", "meneur"): "meneur",
    ("MOC", "second attaquant"): "second attaquant",
    ("AG", "ailier inverse"): "ailier intérieur", ("AD", "ailier inverse"): "ailier intérieur",
    ("SA", "ailier inverse"): "ailier intérieur",
    ("AG", "meneur"): "meneur excentré", ("AD", "meneur"): "meneur excentré",
    ("AG", "piston"): "piston", ("AD", "piston"): "piston",
    ("AG", "second attaquant"): "second attaquant", ("AD", "second attaquant"): "second attaquant",
    ("SA", "second attaquant"): "second attaquant",
    ("BU", "buteur axial"): "buteur axial", ("ATT", "buteur axial"): "buteur axial",
    ("BU", "pivot"): "pivot", ("ATT", "pivot"): "pivot",
    ("BU", "second attaquant"): "second attaquant", ("ATT", "second attaquant"): "second attaquant",
}


def _normalize(categorie: str | None) -> str:
    """Catégorie sans casse, sans accents, sans espaces de fin ni doublons d'espaces ; « _ » vaut une espace."""
    if not categorie:
        return ""
    plain = unicodedata.normalize("NFKD", categorie).encode("ascii", "ignore").decode("ascii")
    return " ".join(plain.lower().replace("_", " ").split())


def role_of(poste: str, categorie: str | None = None) -> str:
    """Rôle du joueur : celui de sa catégorie si la table le prévoit pour ce poste, sinon le rôle par défaut du poste.
    Poste inconnu : chaîne vide (aucun rôle), jamais d'exception."""
    return _CATEGORY_ROLE.get((poste, _normalize(categorie))) or DEFAULT_ROLE.get(poste, "")

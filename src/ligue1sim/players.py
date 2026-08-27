"""Modèle de joueur et tables de correspondance par poste.

Les intitulés de poste sont les diminutifs définis dans l'onglet "Postes" du
fichier source (voir data/joueurs.xlsx) : GK, RB, LB, DC, MDC, MC, MOC, AD,
AG, SA, BU, ATT. Ce tagging est plus large que la nomenclature Transfermarkt
d'origine -- AD/AG regroupent aussi bien un milieu latéral qu'un ailier pur
(fusionnés en une seule catégorie côté données), et ATT (attaquant
polyvalent) est un poste sans équivalent Transfermarkt direct.
"""

from __future__ import annotations

from dataclasses import dataclass

# Regroupement en 4 grandes familles, utilisé pour les dispositifs tactiques
# (lineup.py) et comme repli quand un poste précis n'a pas de table dédiée.
GOALKEEPER = "GK"
DEFENDER = "DEF"
MIDFIELDER = "MID"
ATTACKER = "ATT"

POSITION_GROUP: dict[str, str] = {
    "GK": GOALKEEPER,
    "DC": DEFENDER,
    "LB": DEFENDER,
    "RB": DEFENDER,
    "MDC": MIDFIELDER,
    "MC": MIDFIELDER,
    "MOC": MIDFIELDER,
    "AG": ATTACKER,
    "AD": ATTACKER,
    "SA": ATTACKER,
    "BU": ATTACKER,
    "ATT": ATTACKER,
}
DEFAULT_POSITION_GROUP = MIDFIELDER

# Poids relatifs de tirage buteur/passeur par poste exact. Un gardien n'est
# jamais tiré au sort comme buteur/passeur (poids nul, exclu du tirage par le
# code appelant plutôt que par une probabilité résiduelle).
SCORER_WEIGHT: dict[str, float] = {
    "GK": 0.0,
    "DC": 0.6,
    "LB": 0.7,
    "RB": 0.7,
    "MDC": 0.8,
    "MC": 1.3,
    "MOC": 2.2,
    "AG": 2.5,
    "AD": 2.5,
    "SA": 3.0,
    "BU": 3.2,
    "ATT": 3.0,
}

ASSIST_WEIGHT: dict[str, float] = {
    "GK": 0.0,
    "DC": 0.3,
    "LB": 1.0,
    "RB": 1.0,
    "MDC": 1.2,
    "MC": 2.0,
    "MOC": 2.8,
    "AG": 2.6,
    "AD": 2.6,
    "SA": 1.4,
    "BU": 1.2,
    "ATT": 2.0,
}


def position_group(poste: str) -> str:
    return POSITION_GROUP.get(poste, DEFAULT_POSITION_GROUP)


# Postes tactiquement "voisins", utilisé quand un club doit dépanner un
# secteur qui manque de joueurs (dispositif imposé, effectif mince) : un
# latéral peut monter ailier, un ailier peut dépanner en pointe, etc. Le
# gardien n'a aucun voisin (jamais de joueur de champ en dépannage dans les
# buts, et inversement).
_POSTE_NEIGHBORS: dict[str, set[str]] = {
    "GK": set(),
    "DC": {"LB", "RB", "MDC"},
    "LB": {"DC", "AG"},
    "RB": {"DC", "AD"},
    "MDC": {"DC", "MC"},
    "MC": {"MDC", "MOC", "AG", "AD"},
    "MOC": {"MC", "SA", "AG", "AD"},
    "AG": {"LB", "MC", "MOC", "SA", "BU"},
    "AD": {"RB", "MC", "MOC", "SA", "BU"},
    "SA": {"MOC", "AG", "AD", "BU"},
    "BU": {"SA", "AG", "AD"},
    "ATT": {"SA", "BU", "AD", "AG"},
}


def poste_distance(from_poste: str, to_poste: str) -> int | None:
    """Distance (en nombre de postes intermédiaires) entre deux postes sur le
    graphe de proximité tactique ci-dessus, par parcours en largeur. `None`
    si aucun chemin n'existe (ex. gardien vers n'importe quel poste de champ)."""
    if from_poste == to_poste:
        return 0
    frontier = {from_poste}
    seen = {from_poste}
    distance = 0
    while frontier:
        distance += 1
        next_frontier: set[str] = set()
        for poste in frontier:
            for neighbor in _POSTE_NEIGHBORS.get(poste, ()):
                if neighbor == to_poste:
                    return distance
                if neighbor not in seen:
                    seen.add(neighbor)
                    next_frontier.add(neighbor)
        frontier = next_frontier
    return None


def nearest_distance_to_group(poste: str, group: str) -> int | None:
    """Distance minimale entre `poste` et le poste le plus proche appartenant
    à `group` (GK/DEF/MID/ATT). `None` si aucun poste de ce groupe n'est
    atteignable (ex. gardien vers un groupe de joueurs de champ)."""
    targets = [p for p, g in POSITION_GROUP.items() if g == group]
    distances = [d for t in targets if (d := poste_distance(poste, t)) is not None]
    return min(distances) if distances else None


def best_distance_to_group(postes: tuple[str, ...], group: str) -> int | None:
    """Distance minimale entre `group` et le plus proche des postes donnés
    (poste principal + poste(s) secondaire(s) éventuels) -- permet à un
    joueur de dépanner un secteur en manque via un poste secondaire déclaré,
    même quand son poste principal en est trop éloigné."""
    distances = [d for p in postes if (d := nearest_distance_to_group(p, group)) is not None]
    return min(distances) if distances else None


@dataclass(frozen=True)
class Player:
    prenom: str
    nom: str
    nationalite: str
    age: int
    poste: str
    note: float
    club: str
    championnat: str
    poste_secondaire: tuple[str, ...] = ()
    finition: float | None = None  # colonne "Finition" (0-100) ; voir events.SCORER_WEIGHT
    categorie: str | None = None  # colonne "Catégorie" (rôle/style, ex. "buteur_axial") ; absente pour la plupart

    @property
    def name(self) -> str:
        return f"{self.prenom} {self.nom}".strip()

    @property
    def group(self) -> str:
        return position_group(self.poste)

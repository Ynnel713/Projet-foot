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


# Attributs FM26 (26/09/2026, voir scripts/scrape_fminside_attributes.py) --
# mêmes 47 noms/catégories que le script de scraping (source de vérité
# partagée : ne pas faire diverger cette liste de celle du script). Absents
# pour la grande majorité des joueurs tant que l'enrichissement n'est pas
# terminé (497/7564 au 26/09/2026) -- toujours vérifier `player.attributes`
# avant de l'utiliser.
FM_ATTRIBUTE_CATEGORIES: dict[str, tuple[str, ...]] = {
    "Technique": ("Crossing", "Dribbling", "Finishing", "First Touch", "Heading", "Long Shots",
                  "Marking", "Passing", "Tackling", "Technique"),
    "Gardien": ("Aerial Reach", "Command of Area", "Communication", "Eccentricity", "Handling",
                "Kicking", "One on Ones", "Punching (Tendency)", "Reflexes",
                "Rushing Out (Tendency)", "Throwing"),
    "Mental": ("Aggression", "Anticipation", "Bravery", "Composure", "Concentration", "Decisions",
               "Determination", "Flair", "Leadership", "Off the Ball", "Positioning", "Teamwork",
               "Vision", "Work Rate"),
    "Physique": ("Acceleration", "Agility", "Balance", "Jumping Reach", "Natural Fitness", "Pace",
                 "Stamina", "Strength"),
    "Coups de pied arrêtés": ("Corners", "Free Kick Taking", "Long Throws", "Penalty Taking"),
}
FM_ATTRIBUTE_COLUMNS: tuple[str, ...] = tuple(
    name for names in FM_ATTRIBUTE_CATEGORIES.values() for name in names
)


# Importance par attribut x poste (28/09/2026, fournie par l'utilisateur --
# fm-importance-des-attributs-par-poste-2-=-fondamental-1-=-utile.xlsx).
# Remplace la table de coefficients 0-5 (version précédente) : celle-ci
# moyennait TOUS les attributs (même ceux jugés "hors sujet" à coeff 1),
# ce qui tirait encore trop la moyenne brute vers le bas et forçait des
# recalages excessifs (retour utilisateur : même en poussant les
# coefficients à l'extrême sur les points forts, la moyenne ne dépassait
# pas ~73 pour un ailier comme Gordon, loin de sa Moyenne joueur). Ici,
# seuls les attributs marqués comptent dans la moyenne -- 2 = compétence
# fondamentale, 1 = compétence utile, absent = "note annexe" (case vide
# dans le fichier source) : EXCLUE de la moyenne ET jamais recalée, rendue
# telle quelle. Colonnes du fichier source, dans l'ordre : DC, Latéral,
# Piston, MDC, MC, MOC, Ailier, BU. "Piston" n'a pas d'équivalent dans
# POSITION_GROUP/postes -- conservé pour référence mais non utilisé.
# "Bravery" absent de la feuille source (colonne manquante, comme dans la
# table de coefficients précédente) -- note annexe partout par défaut.
_IMPORTANCE_COLUMNS = ("DC", "Latéral", "Piston", "MDC", "MC", "MOC", "Ailier", "BU")
_RAW_IMPORTANCE: dict[str, tuple[int, ...]] = {
    "Crossing": (0, 1, 2, 0, 0, 0, 0, 0),
    "Dribbling": (0, 0, 1, 0, 0, 1, 2, 0),
    "Finishing": (0, 0, 0, 0, 0, 0, 0, 2),
    "First Touch": (0, 0, 0, 0, 1, 2, 1, 1),
    "Heading": (2, 0, 0, 0, 0, 0, 0, 0),
    "Long Shots": (0, 0, 0, 0, 0, 1, 0, 0),
    "Marking": (2, 1, 1, 1, 0, 0, 0, 0),
    "Passing": (0, 0, 0, 1, 2, 2, 0, 0),
    "Tackling": (2, 1, 1, 2, 0, 0, 0, 0),
    "Technique": (0, 0, 0, 0, 1, 2, 2, 0),
    "Aggression": (1, 0, 0, 1, 0, 0, 0, 0),
    "Anticipation": (1, 1, 0, 1, 1, 1, 1, 2),
    "Composure": (0, 0, 0, 0, 1, 2, 0, 2),
    "Concentration": (2, 1, 1, 2, 1, 0, 0, 1),
    "Decisions": (1, 1, 1, 2, 2, 2, 1, 1),
    "Determination": (1, 1, 1, 1, 1, 1, 1, 1),
    "Flair": (0, 0, 0, 0, 0, 2, 2, 0),
    "Leadership": (1, 0, 0, 1, 1, 0, 0, 0),
    "Off the Ball": (0, 0, 0, 0, 0, 1, 2, 2),
    "Positioning": (2, 1, 1, 2, 0, 0, 0, 0),
    "Teamwork": (1, 1, 1, 1, 2, 1, 0, 0),
    "Vision": (0, 0, 0, 1, 2, 2, 1, 0),
    "Work Rate": (0, 2, 2, 1, 1, 0, 1, 0),
    "Acceleration": (0, 1, 1, 0, 0, 0, 2, 1),
    "Agility": (0, 0, 0, 0, 0, 0, 1, 0),
    "Balance": (0, 0, 0, 0, 0, 0, 1, 1),
    "Jumping Reach": (2, 0, 0, 0, 0, 0, 0, 0),
    "Natural Fitness": (0, 0, 0, 0, 0, 0, 0, 0),
    "Pace": (0, 2, 2, 0, 0, 0, 2, 1),
    "Stamina": (0, 2, 2, 1, 2, 1, 1, 0),
    "Strength": (2, 0, 0, 1, 0, 0, 0, 1),
    "Corners": (0, 0, 0, 0, 0, 0, 0, 0),
    "Free Kick Taking": (0, 0, 0, 0, 0, 0, 0, 0),
    "Long Throws": (0, 0, 0, 0, 0, 0, 0, 0),
    "Penalty Taking": (0, 0, 0, 0, 0, 0, 0, 0),
}
_RAW_IMPORTANCE["Bravery"] = (0, 0, 0, 0, 0, 0, 0, 0)

# Poste exact -> libellé de colonne ci-dessus. SA/ATT n'ont pas de colonne
# dédiée -- moyenne (arrondie) de colonnes voisines (SA : profil à
# mi-chemin MOC/BU ; ATT, "attaquant polyvalent" sans équivalent
# Transfermarkt, voir le docstring du module : moyenne des 3 profils
# offensifs). "GK" absent volontairement : un gardien n'a que des attributs
# "Gardien", hors de cette table -- tous en "note annexe" (voir _importance).
_POSTE_COLUMN: dict[str, str] = {
    "DC": "DC", "LB": "Latéral", "RB": "Latéral", "MDC": "MDC", "MC": "MC",
    "MOC": "MOC", "AG": "Ailier", "AD": "Ailier", "BU": "BU",
}
_POSTE_BLEND: dict[str, tuple[str, ...]] = {
    "SA": ("MOC", "BU"),
    "ATT": ("Ailier", "MOC", "BU"),
}


def _importance(name: str, poste: str | None) -> float:
    """Niveau d'importance (0 = note annexe, 1 = utile, 2 = fondamentale) de
    l'attribut `name` pour `poste` (voir _RAW_IMPORTANCE) -- 0 si `poste` est
    absent/inconnu, ou si `name` n'est dans la table pour aucun poste (ex.
    attributs "Gardien")."""
    column = _POSTE_COLUMN.get(poste)
    if column:
        row = _RAW_IMPORTANCE.get(name)
        return float(row[_IMPORTANCE_COLUMNS.index(column)]) if row else 0.0
    blend = _POSTE_BLEND.get(poste)
    if blend:
        row = _RAW_IMPORTANCE.get(name)
        if not row:
            return 0.0
        indices = [_IMPORTANCE_COLUMNS.index(c) for c in blend]
        return sum(row[i] for i in indices) / len(indices)
    return 0.0


def weighted_attributes(attributes: dict[str, int], note: float, poste: str | None = None) -> dict[str, int]:
    """Recale les attributs FM26 bruts (scrapés sur fminside) sur la seule
    note qui fait foi dans le moteur, Moyenne joueur (décision du
    26/09/2026 : on abandonne toute note globale FM concurrente comme
    "Ability" -- voir l'historique de scripts/scrape_fminside_attributes.py).
    Moyenne joueur ne devient pas une note globale concurrente (elle reste la
    seule utilisée par le moteur, voir clubs.NOTE_COLUMN) -- elle sert
    seulement à recentrer le PROFIL (attributs affichés, radar/barres) sur le
    niveau réel du joueur plutôt que sur celui, potentiellement biaisé, que
    fminside lui attribue seul.

    Seuls les attributs jugés pertinents pour `poste` (importance 1 ou 2,
    voir _RAW_IMPORTANCE -- décision utilisateur du 28/09/2026) entrent dans
    la moyenne brute de référence ET sont recalés ; les autres ("notes
    annexes", importance 0 ou absente de la table) sont retournés TELS
    QUELS, jamais modifiés. `poste` omis/inconnu/sans aucun attribut marqué
    -> rien à recaler, tout est retourné inchangé.

    Le décalage nécessaire (note - moyenne pondérée des attributs
    pertinents) est réparti entre eux INVERSEMENT à leur importance
    (fondamental = 2x moins de correction qu'utile = 1x) plutôt
    qu'uniformément : un point ajouté à un attribut fondamental pèse déjà
    beaucoup plus dans la moyenne qu'un point ajouté à un attribut
    seulement utile, donc le corriger autant que les autres le pousserait
    hors de toute proportion (retour utilisateur du 28/09/2026). Chaque
    attribut recalé reste borné à [0, 99]."""
    if not attributes:
        return attributes

    weights = {name: _importance(name, poste) for name in attributes}
    relevant = {name: w for name, w in weights.items() if w > 0}
    if not relevant:
        return dict(attributes)

    total_weight = sum(relevant.values())
    weighted_mean = sum(weights[name] * value for name, value in attributes.items() if name in relevant) / total_weight
    total_gap = (note - weighted_mean) * total_weight
    correction_unit = total_gap / len(relevant)  # à répartir en /importance ci-dessous

    def rescale(name: str, value: int) -> int:
        weight = weights[name]
        if weight <= 0:
            return value  # note annexe -- jamais touchée
        return round(min(99, max(0, value + correction_unit / weight)))

    return {name: rescale(name, value) for name, value in attributes.items()}


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
    categorie: str | None = None  # colonne "Catégorie" (rôle/style, ex. "buteur_axial") ; absente pour la plupart
    id: int | None = None  # colonne "ID" ; sert à recroiser avec d'autres onglets (voir nations.py)
    attributes: dict[str, int] | None = None  # 47 attributs FM26 (voir FM_ATTRIBUTE_CATEGORIES) ; None si non enrichi -- décrivent le profil du joueur (rapide, bon finisseur...), n'entrent dans aucune note
    postes_fm: str | None = None  # colonne "Postes FM naturels" (ex. "DR, WBR") -- distinct du "Poste" Transfermarkt
    taille_fm: int | None = None  # colonne "Taille FM (cm)"
    weak_foot: float | None = None  # colonne "Weak foot (/5)"
    preferred_moves: str | None = None  # colonne "Preferred moves" -- vide pour la plupart : nécessite un scraping connecté (--cookie)
    valeur_marchande: float | None = None  # colonne "Valeur marchande" (originale, tous les joueurs), en millions d'euros
    pied: str | None = None  # colonne "Pieds" (originale, tous les joueurs) : "D" ou "G"

    @property
    def name(self) -> str:
        return f"{self.prenom} {self.nom}".strip()

    @property
    def group(self) -> str:
        return position_group(self.poste)

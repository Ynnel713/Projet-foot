"""Source unique des attributs FM26 cote moteur NLG (decision D16 et risque R11
du plan V2.1) : consommee par data/import/import_players.py (import des
joueurs) et par engine/conditions.py (distinction attribut inconnu / absent).

Aucun acces base ni fichier : constantes pures. scripts/scrape_fminside_attributes.py
(racine du depot, hors du paquet engine -- collision de nom, dette D15) garde sa
propre copie de la liste ; aucun test ne peut comparer les deux copies depuis ce
venv (risque R14, accepte), a modifier ensemble."""

from __future__ import annotations

# Les 47 attributs FM26, groupes par categorie -- noms de colonnes exacts
# (voir scripts/scrape_fminside_attributes.py, meme liste, source de verite
# partagee : ne pas laisser diverger). Confirme colonne par colonne dans
# data/joueurs.xlsx le 28/09/2026 (colonnes 17 a 63).
FM26_ATTRIBUTES: dict[str, tuple[str, ...]] = {
    "technique": (
        "Crossing", "Dribbling", "Finishing", "First Touch", "Heading",
        "Long Shots", "Marking", "Passing", "Tackling", "Technique",
    ),
    "gardien": (
        "Aerial Reach", "Command of Area", "Communication", "Eccentricity",
        "Handling", "Kicking", "One on Ones", "Punching (Tendency)",
        "Reflexes", "Rushing Out (Tendency)", "Throwing",
    ),
    "mental": (
        "Aggression", "Anticipation", "Bravery", "Composure", "Concentration",
        "Decisions", "Determination", "Flair", "Leadership", "Off the Ball",
        "Positioning", "Teamwork", "Vision", "Work Rate",
    ),
    "physique": (
        "Acceleration", "Agility", "Balance", "Jumping Reach",
        "Natural Fitness", "Pace", "Stamina", "Strength",
    ),
    "coups_de_pied_arretes": (
        "Corners", "Free Kick Taking", "Long Throws", "Penalty Taking",
    ),
}
ATTRIBUTE_TO_CATEGORY: dict[str, str] = {
    name: category for category, names in FM26_ATTRIBUTES.items() for name in names
}

# Ensemble aplati des noms d'attributs FM26 : "ce nom est-il connu du systeme ?"
# (engine/conditions.py -- un nom inconnu est une faute de frappe, un nom connu
# mais absent chez un joueur est un etat normal, voir D16).
FM26_ATTRIBUTES_KNOWN: frozenset[str] = frozenset(ATTRIBUTE_TO_CATEGORY)

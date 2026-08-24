"""Modèle de joueur et tables de correspondance par poste.

Les intitulés de poste sont ceux, exacts, fournis par la base Transfermarkt
(voir data/joueurs.xlsx). "Striker" est un intitulé isolé (un seul joueur
dans la base observée) traité comme un synonyme de "Centre-Forward".
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
    "Goalkeeper": GOALKEEPER,
    "Centre-Back": DEFENDER,
    "Left-Back": DEFENDER,
    "Right-Back": DEFENDER,
    "Defensive Midfield": MIDFIELDER,
    "Central Midfield": MIDFIELDER,
    "Attacking Midfield": MIDFIELDER,
    "Left Midfield": MIDFIELDER,
    "Right Midfield": MIDFIELDER,
    "Left Winger": ATTACKER,
    "Right Winger": ATTACKER,
    "Second Striker": ATTACKER,
    "Centre-Forward": ATTACKER,
    "Striker": ATTACKER,
}
DEFAULT_POSITION_GROUP = MIDFIELDER

# Poids relatifs de tirage buteur/passeur par poste exact. Un gardien n'est
# jamais tiré au sort comme buteur/passeur (poids nul, exclu du tirage par le
# code appelant plutôt que par une probabilité résiduelle).
SCORER_WEIGHT: dict[str, float] = {
    "Goalkeeper": 0.0,
    "Centre-Back": 0.6,
    "Left-Back": 0.7,
    "Right-Back": 0.7,
    "Defensive Midfield": 0.8,
    "Central Midfield": 1.3,
    "Attacking Midfield": 2.2,
    "Left Midfield": 1.5,
    "Right Midfield": 1.5,
    "Left Winger": 2.5,
    "Right Winger": 2.5,
    "Second Striker": 3.0,
    "Centre-Forward": 3.2,
    "Striker": 3.2,
}

ASSIST_WEIGHT: dict[str, float] = {
    "Goalkeeper": 0.0,
    "Centre-Back": 0.3,
    "Left-Back": 1.0,
    "Right-Back": 1.0,
    "Defensive Midfield": 1.2,
    "Central Midfield": 2.0,
    "Attacking Midfield": 2.8,
    "Left Midfield": 2.2,
    "Right Midfield": 2.2,
    "Left Winger": 2.6,
    "Right Winger": 2.6,
    "Second Striker": 1.4,
    "Centre-Forward": 1.2,
    "Striker": 1.2,
}


def position_group(poste: str) -> str:
    return POSITION_GROUP.get(poste, DEFAULT_POSITION_GROUP)


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

    @property
    def name(self) -> str:
        return f"{self.prenom} {self.nom}".strip()

    @property
    def group(self) -> str:
        return position_group(self.poste)

"""Performance momentanée : un seul point d'entrée pour lire une note (ticket v2-realisme/19a).

La note d'un attribut est **intrinsèque** : elle ne change jamais pendant un match. Ce qu'un joueur en **exprime**
à un instant donné pourra dépendre de son état : fatigue (20a, 20b), forme du jour (20f), coup reçu (20g). Tout
module de résolution ou de décision lit donc une note par `effective_rating`, jamais par `attributes.player_attribute`
ni par les champs `pace`, `acceleration`, `stamina` de `PlayerState` (garde : `tests/test_v2engine_condition.py`).
Un effet de la condition se branche ici, une fois, au lieu d'être recopié dans chaque module.

Dans ce ticket, la note exprimée est la note intrinsèque (identité exacte) et `PlayerCondition` est vide. Chaque
attribut a sa famille (`FAMILIES`, d'après `docs/CARTE_ATTRIBUTS_V2.md`) pour qu'un ticket puisse moduler une
famille sans toucher les autres."""

from __future__ import annotations

from dataclasses import dataclass

from v2engine.attributes import player_attribute

PHYSIQUE, MENTAL, TECHNIQUE, GARDIEN = "physique", "mental", "technique", "gardien"

# Familles de docs/CARTE_ATTRIBUTS_V2.md (sections A à D). Passing, First Touch et Technique sont aussi renseignés
# pour les gardiens : ils restent techniques.
FAMILIES: dict[str, str] = {
    **dict.fromkeys(("Pace", "Acceleration", "Agility", "Balance", "Strength", "Jumping Reach", "Stamina",
                     "Natural Fitness"), PHYSIQUE),
    **dict.fromkeys(("Work Rate", "Off the Ball", "Teamwork", "Decisions", "Vision", "Anticipation", "Concentration",
                     "Positioning", "Flair", "Composure", "Determination", "Aggression", "Bravery", "Leadership"),
                    MENTAL),
    **dict.fromkeys(("First Touch", "Passing", "Technique", "Dribbling", "Crossing", "Finishing", "Long Shots",
                     "Heading", "Tackling", "Marking", "Corners", "Free Kick Taking", "Long Throws",
                     "Penalty Taking"), TECHNIQUE),
    **dict.fromkeys(("Reflexes", "One on Ones", "Handling", "Aerial Reach", "Command of Area", "Communication",
                     "Kicking", "Throwing", "Rushing Out", "Punching", "Eccentricity"), GARDIEN),
}

# Physiques recopiés dans `PlayerState` à la construction (chemin chaud de `movement.step`) : lus par leur champ,
# qui peut différer de la fiche (profil forcé d'un banc).
_FIELDS = {"Pace": "pace", "Acceleration": "acceleration", "Stamina": "stamina"}


@dataclass(frozen=True)
class PlayerCondition:
    """État du joueur qui module l'expression de ses notes. Vide jusqu'aux tickets 20 (fatigue, forme, coup reçu)."""


def family(attribute: str) -> str:
    """Famille de `attribute` (physique, mental, technique, gardien) ; `KeyError` pour un nom inconnu."""
    return FAMILIES[attribute]


def intrinsic_rating(player, attribute: str) -> int:
    """Note intrinsèque de la fiche du joueur : réservée au chargement (construction de `PlayerState`)."""
    return player_attribute(player, attribute)


def effective_rating(player, attribute: str, context=None) -> float:
    """Note que `player` exprime à cet instant pour `attribute`. `context` : situation de l'action (minute, effort),
    lue par les tickets 20 ; sans effet ici. Aujourd'hui : la note intrinsèque, à l'identique."""
    field = _FIELDS.get(attribute)
    if field is not None and hasattr(player, field):
        return getattr(player, field)
    return player_attribute(player, attribute)

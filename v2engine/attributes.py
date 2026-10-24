"""Mécanisme partagé de pondération d'un attribut selon le poste (D-V07, docs/TRD_V2.md).

Ne concerne que les attributs utilisés dans une RÉSOLUTION PROBABILISTE (duel, décision) où
l'importance d'un attribut dépend du rôle -- ex. Tackling compte beaucoup pour un MDC, presque
rien pour un BU (voir Guide_attributs_joueurs.pdf, règle "l'importance dépend du poste"). Les
attributs purement physiques qui pilotent le mouvement d'UN joueur (Pace, Acceleration, Agility,
Stamina, voir `movement.py`) ne passent PAS par cette table : la vitesse d'un joueur est la même
quel que soit son poste, à note égale -- rien à pondérer.

Table peuplée au fur et à mesure des tickets qui en ont réellement besoin (Phase 3, duels, voir
docs/PLAN_V2.md), pas par anticipation -- vide pour l'instant (Phase 1 ne consomme aucun poids)."""

from __future__ import annotations

# Poids 0.0-2.0 (0 = sans importance, 1 = utile, 2 = fondamental) par (attribut, poste). Poste ou
# attribut absent de la table -> NEUTRAL_WEIGHT, jamais une erreur (même principe que les données
# manquantes côté joueur, voir `player_attribute`).
NEUTRAL_WEIGHT = 1.0

_WEIGHTS: dict[str, dict[str, float]] = {}


def poste_weight(attribute: str, poste: str) -> float:
    """Poids de `attribute` pour `poste` (voir `_WEIGHTS`/`register_weights`) -- `NEUTRAL_WEIGHT`
    si l'attribut ou le poste n'est pas encore renseigné."""
    return _WEIGHTS.get(attribute, {}).get(poste, NEUTRAL_WEIGHT)


def register_weights(attribute: str, weights: dict[str, float]) -> None:
    """Déclare les poids de `attribute` par poste -- appelé une fois par le module qui introduit
    cet attribut (ex. Phase 3 pour Tackling), jamais recopié ailleurs."""
    _WEIGHTS[attribute] = dict(weights)


def player_attribute(player, name: str, default: int = 60) -> int:
    """Valeur de l'attribut `name` pour `player`, ou `default` si absent. Un joueur sans
    attributs enrichis (`player.attributes is None`) ou avec cette seule colonne manquante se
    comporte normalement plutôt que de faire planter le moteur (même principe que la V1, US-11,
    docs/PRD_PRODUIT.md). `default=60` : proche de la moyenne réelle de la base (55-65, voir
    Guide_attributs_joueurs.pdf)."""
    if player.attributes is None:
        return default
    return player.attributes.get(name, default)

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


# Centre de la courbe (note moyenne réelle de la base, voir Guide_attributs_joueurs.pdf, §1) et
# demi-étendue utilisée pour centrer/normaliser une note avant de la passer à
# `success_probability` ci-dessous.
_CURVE_CENTER = 55.0
_CURVE_HALF_SPAN = 44.0  # note 99 -> t=1.0 ; note 11 -> t=-1.0


def success_probability(note: float, *, baseline: float = 0.6, amplitude: float = 0.35,
                         min_prob: float = 0.05, max_prob: float = 0.95) -> float:
    """Probabilité de réussite d'une action pilotée par un attribut noté `note` (0-99), en
    respectant deux des règles de conception du guide (§2, `Guide_attributs_joueurs.pdf`) :
    jamais binaire (bornée à [`min_prob`, `max_prob`], jamais 0 ni 1 même à note extrême) et
    courbe non linéaire (effet quasi neutre entre 45 et 55, amplifié vers les extrêmes -- via un
    terme cubique, dont la dérivée est nulle au centre et croît vers les bords). Mécanisme
    partagé (construit une fois, consommé par chaque action probabiliste future : First Touch
    ici, Passing/Tackling/Finishing... dans les phases suivantes) -- `baseline`/`amplitude`
    propres à chaque action, cette fonction ne fixe que la FORME de la courbe."""
    t = max(-1.0, min(1.0, (note - _CURVE_CENTER) / _CURVE_HALF_SPAN))
    shaped = t**3
    return max(min_prob, min(max_prob, baseline + shaped * amplitude))


def player_attribute(player, name: str, default: int = 60) -> int:
    """Valeur de l'attribut `name` pour `player`, ou `default` si absent. Un joueur sans
    attributs enrichis (`player.attributes is None`) ou avec cette seule colonne manquante se
    comporte normalement plutôt que de faire planter le moteur (même principe que la V1, US-11,
    docs/PRD_PRODUIT.md). `default=60` : proche de la moyenne réelle de la base (55-65, voir
    Guide_attributs_joueurs.pdf)."""
    if player.attributes is None:
        return default
    return player.attributes.get(name, default)

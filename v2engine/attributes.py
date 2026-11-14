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

import math

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


# Centre de la courbe : note médiane réelle de la base (ticket v2-realisme/24, mesuré le 14/11/2026 : 60 sur les 485
# joueurs de Ligue 1, 65 sur les titulaires ; 62 retenu), et demi-étendues utilisées pour centrer/normaliser une note
# avant de la passer à `success_probability` ci-dessous (55 et 44 de part et d'autre avant le ticket 24). Deux
# demi-étendues : les extrêmes validés de chaque action restent atteints aux mêmes notes (99 -> maximum, 11 -> minimum).
# Les repères « 99 -> X, 55 -> Y, 11 -> Z » des commentaires du moteur (écrits avant le ticket 24) restent vrais aux
# extrêmes ; leur point milieu Y, valeur de base de l'action, est désormais atteint à la note 62.
_CURVE_CENTER = 62.0
_CURVE_HALF_SPAN_ABOVE = 37.0  # note 99 -> t=1,0
_CURVE_HALF_SPAN_BELOW = 51.0  # note 11 -> t=-1,0

# Écart de note (points) au-delà duquel l'effet d'un duel est considéré au maximum -- voir
# `duel_probability`.
_DUEL_HALF_SPAN = 40.0

# Pente de la forme en S (ticket v2-realisme/24, validé le 14/11/2026) : action seule, k=2 (60 -> 70 : 35 % de l'écart
# 50 -> 99, 70 -> 80 : 24 %, contre 4 % et 14 % avec l'ancienne forme cubique) ; duel, k=1 (10 points d'écart : 62,9 %
# au tacle, contre 50,6 %).
_SUCCESS_SLOPE = 2.0
_DUEL_SLOPE = 1.0


def _s_curve(t: float, slope: float, baseline: float, amplitude: float, min_prob: float, max_prob: float) -> float:
    """Forme commune à `success_probability` et `duel_probability` (ticket v2-realisme/24) : `t` (-1 à 1) mappé en
    probabilité par une courbe en S, `tanh(slope·t) / tanh(slope)` -- pente maximale au centre (la note médiane, où
    sont la plupart des joueurs), aplatie vers les extrêmes ; `t = ±1` donne toujours `baseline ± amplitude`. Bornée à
    [min_prob, max_prob] (jamais 0 ni 1, règle "jamais binaire" du guide)."""
    clamped_t = max(-1.0, min(1.0, t))
    shaped = math.tanh(slope * clamped_t) / math.tanh(slope)
    return max(min_prob, min(max_prob, baseline + shaped * amplitude))


def success_probability(note: float, *, baseline: float = 0.6, amplitude: float = 0.35,
                         min_prob: float = 0.05, max_prob: float = 0.95) -> float:
    """Probabilité de réussite d'une action pilotée par un attribut noté `note` (0-99), en
    respectant deux des règles de conception du guide (§2, `Guide_attributs_joueurs.pdf`) :
    jamais binaire et courbe non linéaire (voir `_s_curve`). Mécanisme partagé (construit une
    fois, consommé par chaque action probabiliste future : First Touch ici, Passing/Finishing...
    dans les phases suivantes) -- `baseline`/`amplitude` propres à chaque action, cette fonction
    ne fixe que la FORME de la courbe."""
    t = (note - _CURVE_CENTER) / (_CURVE_HALF_SPAN_ABOVE if note >= _CURVE_CENTER else _CURVE_HALF_SPAN_BELOW)
    return _s_curve(t, _SUCCESS_SLOPE, baseline, amplitude, min_prob, max_prob)


def duel_probability(attacker_rating: float, defender_rating: float, *, baseline: float = 0.5,
                      amplitude: float = 0.4, min_prob: float = 0.05, max_prob: float = 0.95) -> float:
    """Probabilité que le camp `attacker_rating` l'emporte sur `defender_rating` dans un duel
    direct (ex. tacle, Phase 3) -- même forme que `success_probability` (voir `_s_curve`, pente propre au duel),
    mais centrée sur l'ÉCART entre les deux notes plutôt que sur une note isolée : 10 points d'écart comptent
    déjà (62,9 % au tacle), un gros écart devient nettement favorable, jamais une victoire garantie même à écart
    extrême. Symétrique : p(a, b) + p(b, a) = 1 (bornes symétriques autour de `baseline` = 0,5)."""
    t = (attacker_rating - defender_rating) / _DUEL_HALF_SPAN
    return _s_curve(t, _DUEL_SLOPE, baseline, amplitude, min_prob, max_prob)


def player_attribute(player, name: str, default: int = 60) -> int:
    """Valeur de l'attribut `name` pour `player`, ou `default` si absent. Un joueur sans
    attributs enrichis (`player.attributes is None`) ou avec cette seule colonne manquante se
    comporte normalement plutôt que de faire planter le moteur (même principe que la V1, US-11,
    docs/PRD_PRODUIT.md). `default=60` : proche de la moyenne réelle de la base (55-65, voir
    Guide_attributs_joueurs.pdf)."""
    if player.attributes is None:
        return default
    return player.attributes.get(name, default)

"""Duels et tacles (Phase 3, docs/PLAN_V2.md) : un adversaire à portée du porteur du ballon peut
tenter un tacle -- fréquence des tentatives et risque de faute pilotés par Aggression seule,
issue du duel pilotée par Tackling (tacleur) contre Strength/Balance (porteur, qui protège le
ballon). IA placeholder (D-V08) : dès qu'un adversaire est à portée, il peut tenter sa chance --
pas de lecture tactique de QUAND tacler, ça viendra en Phase 5+."""

from __future__ import annotations

import random
from dataclasses import dataclass

from v2engine.attributes import duel_probability, player_attribute, success_probability
from v2engine.movement import PlayerState

# Probabilité de BASE qu'un adversaire à portée tente un tacle ce tick plutôt que d'éviter le
# contact (guide, Aggression : "NOTE HAUTE : tacles plus tôt... NOTE BASSE : évite le contact").
_ATTEMPT_BASELINE = 0.5
_ATTEMPT_AMPLITUDE = 0.35

# Probabilité de BASE qu'un tacle raté se transforme en faute, modulée par Aggression seule --
# contrepartie du guide (plus de duels tentés, plus de fautes), indépendante de Tackling.
_FOUL_BASELINE = 0.15
_FOUL_AMPLITUDE = 0.25


def attempt_tackle_probability(aggression: float) -> float:
    """Probabilité qu'un adversaire à portée tente un tacle CE tick -- voir `_ATTEMPT_BASELINE`."""
    return success_probability(aggression, baseline=_ATTEMPT_BASELINE, amplitude=_ATTEMPT_AMPLITUDE)


def foul_probability(aggression: float) -> float:
    """Probabilité qu'un tacle raté devienne une faute -- voir `_FOUL_BASELINE`. Dépend
    uniquement d'Aggression, jamais de Tackling (le critère d'acceptation de cette phase compare
    les deux à Tackling égal, voir docs/PLAN_V2.md)."""
    return success_probability(aggression, baseline=_FOUL_BASELINE, amplitude=_FOUL_AMPLITUDE)


def tackle_success_probability(tackler: PlayerState, holder: PlayerState) -> float:
    """Probabilité que `tackler` gagne le ballon face à `holder` -- Tackling (dominant) et un peu
    d'Aggression côté tacleur, Strength/Balance côté porteur (guide : Strength "gagne les duels,
    protège le ballon dos au but" ; Balance "conduit le ballon en étant poussé")."""
    tackler_rating = 0.8 * player_attribute(tackler, "Tackling") + 0.2 * player_attribute(tackler, "Aggression")
    holder_resistance = (player_attribute(holder, "Strength") + player_attribute(holder, "Balance")) / 2.0
    return duel_probability(tackler_rating, holder_resistance)


def should_attempt_tackle(aggression: float) -> bool:
    return random.random() < attempt_tackle_probability(aggression)


@dataclass(frozen=True)
class TackleResult:
    won: bool  # le tacleur gagne le ballon
    foul: bool  # faute sifflée (uniquement évaluée sur un tacle raté, voir docs/PLAN_V2.md)


def resolve_tackle(tackler: PlayerState, holder: PlayerState) -> TackleResult:
    """Résout un tacle déjà tenté (voir `should_attempt_tackle`) : jamais une issue garantie,
    même à écart d'attributs extrême (règle "jamais binaire" du guide, voir `duel_probability`)."""
    won = random.random() < tackle_success_probability(tackler, holder)
    foul = (not won) and random.random() < foul_probability(player_attribute(tackler, "Aggression"))
    return TackleResult(won=won, foul=foul)

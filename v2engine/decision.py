"""Décision du porteur (Phase 5, ticket v2-cerveau-joueurs/01, docs/PLAN_V2.md) : remplace l'IA
placeholder D-V08 (« tire à moins de 20 m, sinon passe au plus proche »). Le porteur évalue trois
options -- tirer, passer, conduire -- d'après la situation réelle, puis Decisions règle la
probabilité de prendre la MEILLEURE (Guide_attributs_joueurs.pdf, Decisions) ; sinon il prend
l'une des autres. Seul le CHOIX est décidé ici : la réussite du tir, de la passe ou du duel reste
résolue par `shooting.py`/`possession.py`/`duel.py`."""

from __future__ import annotations

import random
from dataclasses import dataclass, replace

from v2engine.attributes import player_attribute, success_probability
from v2engine.geometry import Vec2
from v2engine.movement import PlayerState
from v2engine.offside import is_clearly_offside, pass_margin_m, perceived_defence_line
from v2engine.possession import pass_success_probability, pressure
from v2engine.shooting import SHOOTING_RANGE_M, shot_probability

# Constantes produit validées par le propriétaire (24/10/2026).
DECISION_INTERVAL_S = 0.5  # le porteur réévalue ses options deux fois par seconde
DRIBBLE_SPEED_FACTOR = 0.85  # part de sa vitesse max, balle au pied
# Decisions -> probabilité de prendre la meilleure option : 99 -> 95 %, 55 -> 70 %, 11 -> 45 %. Même FORME de courbe
# que le guide (quasi plate entre 45 et 55), mais centrée sur 70 % : un joueur moyen choisit bien la plupart du temps.
# Pas de poids par poste (`register_weights`) : bien choisir son action compte autant à tous les postes.
_BEST_CHOICE_BASELINE = 0.70
_BEST_CHOICE_AMPLITUDE = 0.25

# Poids de calibration (pas des constantes produit) : réglés pour que des matchs simulés tombent
# dans les fourchettes validées -- 8 à 15 tirs par équipe, 2 à 3,5 buts par match (voir
# scripts/measure_v2_decisions.py). Recalibré le 24/10/2026 après Vision (ticket 02), validé par le propriétaire :
# 6 matchs de Ligue 1, graine d'audit -> 13,0 tirs par équipe, 2,67 buts par match (avec SHOT 0,2 / DRIBBLE 0,06 :
# 21,8 tirs, 7,17 buts une fois Vision branchée).
SHOT_WEIGHT = 0.1
PASS_WEIGHT = 0.25
DRIBBLE_WEIGHT = 0.04
_PROGRESS_SCALE_M = 20.0  # une passe vers un coéquipier 20 m plus près du but vaut le maximum de progression

# Vision (ticket v2-cerveau-joueurs/02, constantes validées par le propriétaire le 24/10/2026) : QUELS coéquipiers le
# porteur envisage. Portée 99 -> 50 m, 55 -> 30 m, 11 -> 10 m ; une passe qui fait gagner au moins
# `_KEY_PASS_GAIN_M` vers le but n'est repérée qu'avec la probabilité 99 -> 90 %, 55 -> 50 %, 11 -> 10 %. Le
# coéquipier le plus proche est toujours vu. Même courbe partagée que les autres attributs (`success_probability`),
# bornes en mètres pour la portée. Pas de poids par poste : bien voir le jeu compte à tous les postes.
_VISION_RANGE_M = (30.0, 20.0, 10.0, 50.0)  # baseline, amplitude, min, max
_KEY_PASS_GAIN_M = 15.0
_KEY_PASS_SPOT = (0.5, 0.4)  # baseline, amplitude

# Transition défense-attaque (ticket v2-collectif/11, constantes validées par le propriétaire le 01/11/2026 ; part réelle
# des contre-attaques non trouvée). À la récupération, le porteur choisit entre contre-attaque et conservation. La
# contre-attaque est le bon choix si les adversaires de champ derrière le ballon ne dépassent pas de plus de
# `COUNTER_MAX_EXCESS` ses coéquipiers de champ devant lui.
# Decisions règle la probabilité de prendre le bon choix (même courbe que `choose_action`).
CONTRE_ATTAQUE, CONSERVATION = "contre-attaque", "conservation"
COUNTER_MAX_EXCESS = 2
# Valeur d'une passe : part fixe + part de progression. Hors transition 0,3 + 0,7 ; en contre-attaque, la progression
# seule, et une passe qui ne fait pas avancer n'est pas envisagée, sauf sous pression (adversaire à moins de 5 m) : il
# peut alors ressortir en retrait, avec la valeur de contre-attaque, donc après toute passe vers l'avant (réserve A2 de
# l'expert, variante validée par le propriétaire le 01/11/2026) ; en conservation, d'abord la sûreté pour sortir de la
# zone de pression.
_PASS_SHARES = {None: (0.3, 0.7), CONTRE_ATTAQUE: (0.0, 1.0), CONSERVATION: (0.7, 0.3)}
# En contre-attaque, conduite deux fois plus volontiers sans adversaire à 5 m (gêne nulle : `possession.PRESSURE_RADIUS_M`).
COUNTER_DRIBBLE_BOOST = 2.0


@dataclass(frozen=True)
class Action:
    kind: str  # "shot" | "pass" | "dribble"
    value: float
    target: PlayerState | None = None  # coéquipier visé, pour une passe
    considered: int = 1  # options envisagées à cette décision (journal des décisions, ADR 0001)
    best: bool = True  # meilleure option prise (Decisions)


def vision_range_m(vision: float) -> float:
    baseline, amplitude, low, high = _VISION_RANGE_M
    return success_probability(vision, baseline=baseline, amplitude=amplitude, min_prob=low, max_prob=high)


def key_pass_spot_probability(vision: float) -> float:
    baseline, amplitude = _KEY_PASS_SPOT
    return success_probability(vision, baseline=baseline, amplitude=amplitude)


def visible_teammates(holder: PlayerState, teammates: list[PlayerState], goal: Vec2) -> list[PlayerState]:
    """Coéquipiers que le porteur envisage pour une passe (Vision, voir `_VISION_RANGE_M`) : à portée, et pour une
    passe qui fait gagner beaucoup de terrain, seulement s'il la repère à cette décision-ci. Le plus proche est
    toujours vu, même à Vision très basse."""
    if not teammates:
        return []
    vision = player_attribute(holder, "Vision")
    reach = vision_range_m(vision)
    spot = key_pass_spot_probability(vision)
    holder_to_goal = holder.position.distance_to(goal)
    nearest = min(teammates, key=lambda p: holder.position.distance_to(p.position))
    seen = []
    for mate in teammates:
        if mate is not nearest:
            if holder.position.distance_to(mate.position) > reach:
                continue
            if holder_to_goal - mate.position.distance_to(goal) >= _KEY_PASS_GAIN_M and random.random() >= spot:
                continue
        seen.append(mate)
    return seen


def evaluate_options(holder: PlayerState, players: list[PlayerState], goal: Vec2, keeper: PlayerState | None,
                     mode: str | None = None) -> list[Action]:
    """Les options du porteur avec leur valeur (plus haut = meilleur). Tirer n'existe qu'à portée
    (`SHOOTING_RANGE_M`), passer seulement s'il a un coéquipier ; conduire est toujours possible. `mode` : choix de
    transition de son équipe, contre-attaque ou conservation (ticket v2-collectif/11), sinon `None`."""
    opponents = [p for p in players if p.team != holder.team]
    mates = [p for p in players if p.team == holder.team and p.name != holder.name]
    # Hors-jeu (ticket v2-collectif/23, deuxième passe du 28/10/2026) : le porteur ne sert pas un coéquipier qu'il
    # voit nettement au-delà de la ligne -- mais ce qu'il voit dépend de sa Vision. Trois leviers, tous sur la Vision
    # (docs/CARTE_ATTRIBUTS_V2.md, audit A12) : la portée (`visible_teammates`), le seuil de tolérance
    # (`pass_margin_m`, angle mort de 0,85 m à Vision 0 à 0,3 m à Vision 100) et l'erreur de lecture de la ligne (`perceived_defence_line`, 0,05 à 0,25 m).
    # Les deux derniers se composent en un seul seuil effectif, d'où les passes que l'arbitre siffle.
    vision = player_attribute(holder, "Vision")
    margin = pass_margin_m(vision)
    seen_line = perceived_defence_line(holder.team, opponents, vision)
    teammates = [p for p in visible_teammates(holder, mates, goal)
                 if not is_clearly_offside(holder.team, p.position, holder.position, opponents, margin, seen_line)]
    gene = pressure(holder, opponents)
    holder_to_goal = holder.position.distance_to(goal)
    if mode == CONTRE_ATTAQUE and gene == 0.0:  # seule une passe qui fait avancer compte (ticket v2-collectif/11)
        teammates = [p for p in teammates if p.position.distance_to(goal) < holder_to_goal]

    boost = COUNTER_DRIBBLE_BOOST if mode == CONTRE_ATTAQUE and gene == 0.0 else 1.0
    options = [Action("dribble", DRIBBLE_WEIGHT * (1.0 - gene) * boost)]
    if holder_to_goal <= SHOOTING_RANGE_M:
        chance = shot_probability(holder, keeper, holder_to_goal, goal.y)
        options.append(Action("shot", SHOT_WEIGHT * chance * (1.0 - 0.5 * gene)))
    if teammates:
        def pass_value(mate: PlayerState) -> float:
            gain = holder_to_goal - mate.position.distance_to(goal)
            progress = min(1.0, max(0.0, 0.5 + gain / (2.0 * _PROGRESS_SCALE_M)))
            openness = 1.0 - pressure(mate, opponents)
            success = pass_success_probability(holder, mate, opponents)  # difficulté de CETTE passe (v2-socle/04)
            fixed, progressive = _PASS_SHARES[mode]
            return PASS_WEIGHT * success * (fixed + progressive * progress) * openness

        best_mate = max(teammates, key=pass_value)
        options.append(Action("pass", pass_value(best_mate), best_mate))
    return options


def best_choice_probability(decisions: float) -> float:
    return success_probability(decisions, baseline=_BEST_CHOICE_BASELINE, amplitude=_BEST_CHOICE_AMPLITUDE)


def choose_action(holder: PlayerState, players: list[PlayerState], goal: Vec2, keeper: PlayerState | None,
                  mode: str | None = None) -> Action:
    """Prend la meilleure option avec la probabilité donnée par Decisions, sinon une autre au
    hasard -- jamais binaire, même à 99."""
    options = sorted(evaluate_options(holder, players, goal, keeper, mode), key=lambda a: a.value, reverse=True)
    if len(options) == 1 or random.random() < best_choice_probability(player_attribute(holder, "Decisions")):
        return replace(options[0], considered=len(options), best=True)
    return replace(random.choice(options[1:]), considered=len(options), best=False)


def counter_is_favorable(holder: PlayerState, players: list[PlayerState]) -> bool:
    """Contre-attaque jouable : adversaires de champ derrière le ballon (entre lui et le but visé) moins coéquipiers
    de champ devant lui, porteur exclu, au plus `COUNTER_MAX_EXCESS` (ticket v2-collectif/11)."""
    forward = 1.0 if holder.team == "home" else -1.0
    ahead = [p for p in players if p.poste != "GK" and p is not holder
             and forward * (p.position.x - holder.position.x) > 0.0]
    behind = sum(p.team != holder.team for p in ahead)
    return behind - (len(ahead) - behind) <= COUNTER_MAX_EXCESS


def choose_transition(holder: PlayerState, players: list[PlayerState]) -> str:
    """Choix du porteur qui vient de récupérer le ballon : le bon choix (contre-attaque si elle est jouable, sinon
    conservation) avec la probabilité donnée par Decisions, sinon l'autre."""
    best, other = (CONTRE_ATTAQUE, CONSERVATION) if counter_is_favorable(holder, players) else (CONSERVATION, CONTRE_ATTAQUE)
    return best if random.random() < best_choice_probability(player_attribute(holder, "Decisions")) else other

"""Décision du porteur (Phase 5, ticket v2-cerveau-joueurs/01, docs/PLAN_V2.md) : remplace l'IA
placeholder D-V08 (« tire à moins de 20 m, sinon passe au plus proche »). Le porteur évalue trois
options -- tirer, passer, conduire -- d'après la situation réelle, puis Decisions règle la
probabilité de prendre la MEILLEURE (Guide_attributs_joueurs.pdf, Decisions) ; sinon il prend
l'une des autres. Seul le CHOIX est décidé ici : la réussite du tir, de la passe ou du duel reste
résolue par `shooting.py`/`possession.py`/`duel.py`."""

from __future__ import annotations

import random
from dataclasses import dataclass

from v2engine.attributes import player_attribute, success_probability
from v2engine.geometry import Vec2
from v2engine.movement import PlayerState
from v2engine.possession import pass_accuracy
from v2engine.shooting import SHOOTING_RANGE_M, shot_probability

# Constantes produit validées par le propriétaire (24/10/2026).
DECISION_INTERVAL_S = 0.5  # le porteur réévalue ses options deux fois par seconde
PRESSURE_RADIUS_M = 5.0  # gêne maximale au contact, nulle à 5 m
DRIBBLE_SPEED_FACTOR = 0.85  # part de sa vitesse max, balle au pied
# Decisions -> probabilité de prendre la meilleure option : 99 -> 95 %, 55 -> 70 %, 11 -> 45 %. Même FORME de courbe
# que le guide (quasi plate entre 45 et 55), mais centrée sur 70 % : un joueur moyen choisit bien la plupart du temps.
# Pas de poids par poste (`register_weights`) : bien choisir son action compte autant à tous les postes.
_BEST_CHOICE_BASELINE = 0.70
_BEST_CHOICE_AMPLITUDE = 0.25

# Poids de calibration (pas des constantes produit) : réglés pour que des matchs simulés tombent
# dans les fourchettes validées -- 8 à 15 tirs par équipe, 2 à 3,5 buts par match (voir
# scripts/measure_v2_decisions.py). Mesure du 24/10/2026, 6 matchs de Ligue 1, graine d'audit :
# 11,0 tirs par équipe, 2,17 buts par match (avec SHOT 1,0 / DRIBBLE 0,12 : 50 tirs, 17,5 buts).
SHOT_WEIGHT = 0.2
PASS_WEIGHT = 0.25
DRIBBLE_WEIGHT = 0.06
_PROGRESS_SCALE_M = 20.0  # une passe vers un coéquipier 20 m plus près du but vaut le maximum de progression


@dataclass(frozen=True)
class Action:
    kind: str  # "shot" | "pass" | "dribble"
    value: float
    target: PlayerState | None = None  # coéquipier visé, pour une passe


def pressure(player: PlayerState, opponents: list[PlayerState]) -> float:
    """Gêne subie par `player` (0 à 1) : 1 au contact de l'adversaire le plus proche, 0 à
    `PRESSURE_RADIUS_M` ou au-delà."""
    if not opponents:
        return 0.0
    nearest = min(player.position.distance_to(o.position) for o in opponents)
    return max(0.0, 1.0 - nearest / PRESSURE_RADIUS_M)


def evaluate_options(holder: PlayerState, players: list[PlayerState], goal: Vec2, keeper: PlayerState | None) -> list[Action]:
    """Les options du porteur avec leur valeur (plus haut = meilleur). Tirer n'existe qu'à portée
    (`SHOOTING_RANGE_M`), passer seulement s'il a un coéquipier ; conduire est toujours possible."""
    opponents = [p for p in players if p.team != holder.team]
    teammates = [p for p in players if p.team == holder.team and p.name != holder.name]
    gene = pressure(holder, opponents)
    holder_to_goal = holder.position.distance_to(goal)

    options = [Action("dribble", DRIBBLE_WEIGHT * (1.0 - gene))]
    if holder_to_goal <= SHOOTING_RANGE_M:
        chance = shot_probability(holder, keeper, holder_to_goal, goal.y)
        options.append(Action("shot", SHOT_WEIGHT * chance * (1.0 - 0.5 * gene)))
    if teammates:
        accuracy = pass_accuracy(holder)

        def pass_value(mate: PlayerState) -> float:
            gain = holder_to_goal - mate.position.distance_to(goal)
            progress = min(1.0, max(0.0, 0.5 + gain / (2.0 * _PROGRESS_SCALE_M)))
            openness = 1.0 - pressure(mate, opponents)
            return PASS_WEIGHT * accuracy * (0.3 + 0.7 * progress) * openness

        best_mate = max(teammates, key=pass_value)
        options.append(Action("pass", pass_value(best_mate), best_mate))
    return options


def best_choice_probability(decisions: float) -> float:
    return success_probability(decisions, baseline=_BEST_CHOICE_BASELINE, amplitude=_BEST_CHOICE_AMPLITUDE)


def choose_action(holder: PlayerState, players: list[PlayerState], goal: Vec2, keeper: PlayerState | None) -> Action:
    """Prend la meilleure option avec la probabilité donnée par Decisions, sinon une autre au
    hasard -- jamais binaire, même à 99."""
    options = sorted(evaluate_options(holder, players, goal, keeper), key=lambda a: a.value, reverse=True)
    if len(options) == 1 or random.random() < best_choice_probability(player_attribute(holder, "Decisions")):
        return options[0]
    return random.choice(options[1:])

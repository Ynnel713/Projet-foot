"""Rôles défensifs (ticket v2-collectif/07) : quand l'adversaire a le ballon, l'équipe attribue des rôles une fois par
tick, au lieu de laisser tout joueur à moins de `cerveau.CHASE_RADIUS_M` foncer sur le porteur (essaim mesuré le
30/10/2026 : 2,95 défenseurs en moyenne à moins de 3 m du porteur, 86 tacles par match) :
- un **presseur** : celui qui arrive le premier sur le porteur (Pace et Acceleration, capacité seule, règle R5) ;
- une **couverture**, porteur dans sa moitié : le joueur qui arrive le premier sur le point situé à `COVER_DEPTH_M`
  derrière le porteur, sur la ligne porteur-but -- elle ferme aussi l'axe (pas de rôle séparé). Positioning règle la
  précision de ce placement (même erreur que dans le bloc, `Bloc.placement_error`) ;
- un **marqueur** par attaquant dangereux (hors porteur, à `DANGER_M` ou moins du but défendu) : le défenseur libre
  le plus proche, côté but, à une distance réglée par Marking.
Dans les 25 m, le marqueur défend côté but, sous la ligne du bloc s'il le faut, comme les défenseurs réels autour de
la surface : le piège du hors-jeu se joue plus haut (décision du propriétaire du 30/10/2026, après mesure de trois
versions ; « tenir la ligne » ne remontait le hors-jeu que de 0,3 à 0,5 par match et annulait l'effet de Marking).
Les autres tiennent le bloc (ticket 04), sauf l'indiscipliné qui le quitte pour aller au ballon (Teamwork, critère
reporté du ticket 04). Work Rate (envie de presser) est laissé au ticket 08 ; Anticipation agit déjà par le délai de
réaction à la situation de jeu.

Constantes validées par le propriétaire le 30/10/2026 (ordres de grandeur, ajustables ; valeurs réelles non trouvées) :
- couverture à 6 m derrière le porteur (guides d'entraînement : « 5 à 7 pas, en retrait et décalé ») ;
- attaquant dangereux à 25 m ou moins du but ;
- distance de marquage : Marking 99 -> 1 m, 55 -> 2,5 m, 11 -> 4 m ;
- quitter le bloc pour aller au ballon : Teamwork 99 -> 0 %, 55 -> 15 %, 11 -> 35 %, tiré toutes les 5 s ;
- presseur et couverture restent à leur titulaire, pour le même porteur, tant qu'un autre ne peut pas arriver au moins
  0,3 s avant lui (`HOLD_MARGIN_S`, réserve A1 de l'expert : sans mémoire, le presseur changeait de main puis revenait
  en moins de 1 s dans 14 % des changements ; avec, 0 %). Le marqueur n'a pas de mémoire : avec elle, le marqueur
  attitré décrochait de son attaquant et l'effet de Marking disparaissait (5,50 contre 5,32 m), sans elle le
  ping-pong du marqueur est déjà à 3,7 % (mesures du 30/10/2026, 4 matchs)."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from v2engine.attributes import player_attribute, success_probability
from v2engine.ball_state import BallState
from v2engine.bloc import POSITIONING_REDRAW_S, Bloc
from v2engine.geometry import PITCH_LENGTH_M, PITCH_WIDTH_M, Vec2, clamp_to_pitch
from v2engine.movement import PlayerState, accel_tau_s, max_speed_mps

PRESSEUR, COUVERTURE, MARQUAGE = "presseur", "couverture", "marquage"

COVER_DEPTH_M = 6.0
DANGER_M = 25.0
_MARKING_M = (2.5, 1.5, 1.0, 4.0)  # baseline, amplitude, min, max (inversés : bonne note = marquage serré)
_STAYS = (0.85, 0.2, 0.65, 1.0)  # Teamwork : probabilité de tenir le bloc (99 -> 100 %, 55 -> 85 %, 11 -> 65 %)
LEAVE_REDRAW_S = POSITIONING_REDRAW_S  # même rythme de tirage que l'erreur de placement
HOLD_MARGIN_S = 0.3


def own_goal(team: str) -> Vec2:
    """Centre du but défendu (domicile défend x = 0)."""
    return Vec2(0.0 if team == "home" else PITCH_LENGTH_M, PITCH_WIDTH_M / 2.0)


def arrival_time_s(player: PlayerState, point: Vec2) -> float:
    """Temps pour rejoindre `point` : distance à vitesse de pointe, plus le temps de montée en vitesse (capacité)."""
    return player.position.distance_to(point) / max_speed_mps(player.pace) + accel_tau_s(player.acceleration)


def marking_distance_m(player: PlayerState) -> float:
    baseline, amplitude, low, high = _MARKING_M
    return low + high - success_probability(player_attribute(player, "Marking"), baseline=baseline,
                                            amplitude=amplitude, min_prob=low, max_prob=high)


def leave_probability(player: PlayerState) -> float:
    baseline, amplitude, low, high = _STAYS
    return 1.0 - success_probability(player_attribute(player, "Teamwork"), baseline=baseline, amplitude=amplitude,
                                     min_prob=low, max_prob=high)


def _goal_side(point: Vec2, goal: Vec2, distance: float) -> Vec2:
    """Point à `distance` de `point`, vers le but (le point lui-même s'il est déjà dans le but)."""
    to_goal = goal - point
    return point if to_goal.length() < 1e-9 else clamp_to_pitch(point + to_goal.normalized() * min(distance, to_goal.length()))


@dataclass(frozen=True)
class Assignment:
    role: str
    target: Vec2
    mate: str  # porteur pressé ou couvert, attaquant marqué
    target_velocity: Vec2


@dataclass
class DefensiveRoles:
    """Rôles de l'équipe sans ballon (`update`, une fois par tick) et indiscipline de chaque joueur (`leaves_the_bloc`)."""
    assignments: dict[str, Assignment] = field(default_factory=dict)
    leaving: dict[str, tuple[bool, float]] = field(default_factory=dict)  # joueur -> (quitte le bloc, prochain tirage)
    # titulaires du tick précédent : (rôle, porteur) -> défenseur (`HOLD_MARGIN_S`)
    holders: dict[tuple[str, str], str] = field(default_factory=dict)

    def _keep(self, previous: dict[tuple[str, str], str], role: str, mate: str, free: list[PlayerState], point: Vec2,
              best: PlayerState) -> PlayerState:
        """`best`, sauf si le titulaire du rôle pour `mate` est encore libre et n'arrive pas 0,3 s plus tard que lui."""
        incumbent = next((p for p in free if p.name == previous.get((role, mate))), None)
        if incumbent is not None and arrival_time_s(incumbent, point) <= arrival_time_s(best, point) + HOLD_MARGIN_S:
            best = incumbent
        self.holders[(role, mate)] = best.name
        return best

    def update(self, players: list[PlayerState], ball: BallState, bloc: Bloc | None, now_s: float) -> None:
        self.assignments = {}
        holder = next((p for p in players if p.name == ball.holder), None) if ball.holder else None
        if holder is None:  # titulaires gardés : le même porteur peut récupérer le ballon après la passe
            return
        previous, self.holders = self.holders, {}
        team = "away" if holder.team == "home" else "home"
        goal = own_goal(team)
        free = [p for p in players if p.team == team and p.poste != "GK"]
        if not free:
            return
        presser = self._keep(previous, PRESSEUR, holder.name, free, holder.position,
                             min(free, key=lambda p: arrival_time_s(p, holder.position)))
        self.assignments[presser.name] = Assignment(PRESSEUR, holder.position, holder.name, holder.velocity)
        free.remove(presser)
        own_half = holder.position.distance_to(Vec2(goal.x, holder.position.y)) <= PITCH_LENGTH_M / 2.0
        if own_half and free and holder.position.distance_to(goal) > 1e-9:  # porteur dans le but : rien à couvrir
            spot = _goal_side(holder.position, goal, COVER_DEPTH_M)
            cover = self._keep(previous, COUVERTURE, holder.name, free, spot, min(free, key=lambda p: arrival_time_s(p, spot)))
            if bloc is not None:  # Positioning : précision du placement, comme dans le bloc
                spot = clamp_to_pitch(spot + bloc.placement_error(cover, now_s))
            self.assignments[cover.name] = Assignment(COUVERTURE, spot, holder.name, holder.velocity)
            free.remove(cover)
        # l'attaquant qui recule après un hors-jeu sifflé (ticket 23) n'est pas marqué
        dangerous = sorted((p for p in players if p.team == holder.team and p is not holder and p.poste != "GK"
                            and p.position.distance_to(goal) <= DANGER_M and ball.offside_out_until.get(p.name, 0.0) <= now_s),
                           key=lambda p: p.position.distance_to(goal))
        for attacker in dangerous:
            if not free:
                break
            marker = min(free, key=lambda p: p.position.distance_to(attacker.position))
            spot = _goal_side(attacker.position, goal, marking_distance_m(marker))
            self.assignments[marker.name] = Assignment(MARQUAGE, spot, attacker.name, attacker.velocity)
            free.remove(marker)

    def leaves_the_bloc(self, player: PlayerState, now_s: float) -> bool:
        """Sans rôle et près du ballon, quitte-t-il quand même le bloc pour y aller ? Tiré toutes les 5 s (Teamwork)."""
        leaves, next_s = self.leaving.get(player.name, (False, 0.0))
        if now_s >= next_s:
            leaves = random.random() < leave_probability(player)
            self.leaving[player.name] = (leaves, now_s + LEAVE_REDRAW_S)
        return leaves

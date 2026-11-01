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
  ping-pong du marqueur est déjà à 3,7 % (mesures du 30/10/2026, 4 matchs).

Pressing coordonné (ticket v2-collectif/08, constantes validées par le propriétaire le 31/10/2026 ; durées de repos,
décalage et parts non trouvés, ordres de grandeur ajustables) :
- intensité de course du presseur, Work Rate : 99 -> 100 %, 55 -> 80 %, 11 -> 55 % de sa vitesse max (socle 02) ;
- effort par à-coups : au plus `PRESS_BURST_S` = 5 s (fenêtre de 5 s des analyses StatsBomb), puis il souffle, Work
  Rate 99 -> 5 s, 55 -> 10 s, 11 -> 20 s ; le suivant qui arrive le premier prend le relais ;
- course orientée : il vise, à sa distance d'arrêt, le côté de la ligne de passe vers le receveur le plus dangereux
  (le plus proche du but défendu), décalé d'au plus `SHADOW_M` = 1,5 m de son approche directe ; Anticipation règle
  la part des bonnes lectures (99 -> 85 %, 55 -> 65 %, 11 -> 40 %, sinon un autre receveur), un tirage par porteur ;
- distance d'arrêt face au porteur, Aggression (engagement au contact) : 99 -> 0,8 m, 55 -> 1,2 m, 11 -> 1,6 m, au-delà
  du rayon de tacle (1,5 m) : il laisse le porteur se retourner ;
- déclencheurs collectifs (passe en retrait d'au moins `BACKWARD_PASS_M` = 3 m, réserve A2 de l'expert ; porteur qui
  reçoit en reculant vers son but ; contrôle raté) : pressing d'équipe pendant `TRIGGER_S` = 5 s ; chaque partenaire
  suit, Teamwork 99 -> 95 %, 55 -> 80 %, 11 -> 55 %, un tirage par déclenchement, et marque côté ballon, le plus libre
  d'abord, chaque receveur à moins de `FOLLOW_M` = 15 m du ballon."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from v2engine.attributes import player_attribute, success_probability
from v2engine.ball_state import BallState
from v2engine.bloc import POSITIONING_REDRAW_S, Bloc
from v2engine.geometry import PITCH_LENGTH_M, PITCH_WIDTH_M, Vec2, clamp_to_pitch
from v2engine.movement import PlayerState, accel_tau_s, max_speed_mps
from v2engine.possession import MISS_RETRY_S

PRESSEUR, COUVERTURE, MARQUAGE = "presseur", "couverture", "marquage"

COVER_DEPTH_M = 6.0
DANGER_M = 25.0
_MARKING_M = (2.5, 1.5, 1.0, 4.0)  # baseline, amplitude, min, max (inversés : bonne note = marquage serré)
_STAYS = (0.85, 0.2, 0.65, 1.0)  # Teamwork : probabilité de tenir le bloc (99 -> 100 %, 55 -> 85 %, 11 -> 65 %)
LEAVE_REDRAW_S = POSITIONING_REDRAW_S  # même rythme de tirage que l'erreur de placement
HOLD_MARGIN_S = 0.3
# Pressing coordonné (ticket 08) : (baseline, amplitude, min, max) sur la courbe partagée
_PRESS_INTENSITY = (0.8, 0.25, 0.55, 1.0)  # Work Rate
_PRESS_REST_S = (10.0, -10.0, 5.0, 20.0)  # Work Rate (amplitude négative : bonne note = repos court)
_GOOD_LANE = (0.65, 0.25, 0.40, 0.85)  # Anticipation
_STOP_M = (1.2, -0.4, 0.8, 1.6)  # Aggression
_FOLLOWS = (0.8, 0.25, 0.55, 0.95)  # Teamwork
PRESS_BURST_S = 5.0
SHADOW_M = 1.5
TRIGGER_S = 5.0
FOLLOW_M = 15.0
OPTION_RANGE_M = 40.0  # receveurs considérés par le presseur (même portée que l'indicateur des solutions de passe)
BACKWARD_MPS = 0.5  # porteur qui reçoit en reculant vers son but : vitesse vers son but au-delà de 0,5 m/s
BACKWARD_PASS_M = 3.0  # passe en retrait : le receveur est au moins 3 m plus près de son but (réserve A2 de l'expert)
MISS_FRESH_S = 0.25  # un contrôle raté déclenche s'il date de moins de 0,25 s


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


def _curve(note: float, curve: tuple[float, float, float, float]) -> float:
    baseline, amplitude, low, high = curve
    return success_probability(note, baseline=baseline, amplitude=amplitude, min_prob=low, max_prob=high)


def press_intensity(player: PlayerState) -> float:
    return _curve(player_attribute(player, "Work Rate"), _PRESS_INTENSITY)


def press_rest_s(player: PlayerState) -> float:
    return _curve(player_attribute(player, "Work Rate"), _PRESS_REST_S)


def good_lane_probability(player: PlayerState) -> float:
    return _curve(player_attribute(player, "Anticipation"), _GOOD_LANE)


def stop_distance_m(player: PlayerState) -> float:
    return _curve(player_attribute(player, "Aggression"), _STOP_M)


def follow_probability(player: PlayerState) -> float:
    return _curve(player_attribute(player, "Teamwork"), _FOLLOWS)


def press_point(presser: PlayerState, holder: PlayerState, receiver: PlayerState | None) -> Vec2:
    """Où le presseur se présente : à sa distance d'arrêt (Aggression) du porteur, du côté de la ligne de passe vers
    `receiver`, à au plus `SHADOW_M` de son approche directe."""
    distance = stop_distance_m(presser)
    approach = presser.position - holder.position
    if approach.length() < 1e-9 or receiver is None or receiver.position.distance_to(holder.position) < 1e-9:
        return clamp_to_pitch(holder.position + approach.normalized() * distance if approach.length() > 1e-9
                              else holder.position)
    # il tourne autour du porteur, de son approche directe vers la ligne de passe, d'un arc de corde SHADOW_M au plus
    start = math.atan2(approach.y, approach.x)
    lane = receiver.position - holder.position
    turn = (math.atan2(lane.y, lane.x) - start + math.pi) % (2.0 * math.pi) - math.pi
    limit = 2.0 * math.asin(min(1.0, SHADOW_M / (2.0 * distance)))
    angle = start + max(-limit, min(limit, turn))
    return clamp_to_pitch(holder.position + Vec2(math.cos(angle), math.sin(angle)) * distance)


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
    intensity: float = 1.0  # part de la vitesse max (presseur : Work Rate, ticket 08)


@dataclass
class DefensiveRoles:
    """Rôles de l'équipe sans ballon (`update`, une fois par tick) et indiscipline de chaque joueur (`leaves_the_bloc`)."""
    assignments: dict[str, Assignment] = field(default_factory=dict)
    leaving: dict[str, tuple[bool, float]] = field(default_factory=dict)  # joueur -> (quitte le bloc, prochain tirage)
    # titulaires du tick précédent : (rôle, porteur) -> défenseur (`HOLD_MARGIN_S`)
    holders: dict[tuple[str, str], str] = field(default_factory=dict)
    # pressing coordonné (ticket 08)
    # presseur -> (porteur, début de l'effort) ; gardé s'il revient sur le même porteur (réserve A4 de l'expert)
    burst: dict[str, tuple[str, float]] = field(default_factory=dict)
    rest_until: dict[str, float] = field(default_factory=dict)  # presseur qui souffle -> fin du repos
    lanes: dict[tuple[str, str], str | None] = field(default_factory=dict)  # (presseur, porteur) -> receveur fermé
    trigger_until: dict[str, float] = field(default_factory=dict)  # équipe -> fin du pressing d'équipe
    follows: dict[str, bool] = field(default_factory=dict)  # partenaire -> suit le pressing d'équipe en cours
    followed: dict[str, str] = field(default_factory=dict)  # partenaire qui suit -> receveur qu'il ferme
    last_holder: tuple[str, str, float] | None = None  # (nom, équipe, progression) du porteur précédent
    seen_misses: set[tuple[str, float]] = field(default_factory=set)

    def resting(self, player: PlayerState, now_s: float) -> bool:
        return self.rest_until.get(player.name, 0.0) > now_s

    def start_team_press(self, team: str, players: list[PlayerState], now_s: float) -> None:
        self.trigger_until[team] = now_s + TRIGGER_S
        self.followed = {}
        for p in players:
            if p.team == team:
                self.follows[p.name] = random.random() < follow_probability(p)

    def _watch_triggers(self, players: list[PlayerState], ball: BallState, holder: PlayerState | None,
                        now_s: float) -> None:
        """Déclencheurs du pressing d'équipe : passe en retrait, réception en reculant vers son but, contrôle raté."""
        self.seen_misses = {m for m in self.seen_misses if m[1] > now_s}  # échus : oubliés (A4 de l'expert, passage 2)
        for name, until in ball.control_ban_until_s.items():
            if until > now_s and (name, until) not in self.seen_misses:
                self.seen_misses.add((name, until))
                missed = next((p for p in players if p.name == name), None)
                if missed is not None and until - now_s >= MISS_RETRY_S - MISS_FRESH_S:
                    self.start_team_press("away" if missed.team == "home" else "home", players, now_s)
        if holder is None:
            return
        goal = own_goal(holder.team)
        progress = abs(holder.position.x - goal.x)
        previous, self.last_holder = self.last_holder, (holder.name, holder.team, progress)
        if previous is None or previous[0] == holder.name or previous[1] != holder.team:
            return
        backward = holder.velocity.x * (1.0 if goal.x > holder.position.x else -1.0) > BACKWARD_MPS
        if progress < previous[2] - BACKWARD_PASS_M or backward:
            self.start_team_press("away" if holder.team == "home" else "home", players, now_s)

    def _lane(self, presser: PlayerState, holder: PlayerState, players: list[PlayerState],
              goal: Vec2) -> PlayerState | None:
        """Receveur dont le presseur ferme la ligne : le plus dangereux s'il lit bien (Anticipation), sinon un autre."""
        key = (presser.name, holder.name)
        if key not in self.lanes:
            options = sorted((p for p in players if p.team == holder.team and p is not holder and p.poste != "GK"
                              and p.position.distance_to(holder.position) <= OPTION_RANGE_M),
                             key=lambda p: p.position.distance_to(goal))
            if not options:
                self.lanes[key] = None
            elif len(options) == 1 or random.random() < good_lane_probability(presser):
                self.lanes[key] = options[0].name
            else:
                self.lanes[key] = random.choice(options[1:]).name
        return next((p for p in players if p.name == self.lanes[key]), None)

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
        self._watch_triggers(players, ball, holder, now_s)
        if holder is None:  # titulaires gardés : le même porteur peut récupérer le ballon après la passe
            return
        previous, self.holders = self.holders, {}
        # effort et ligne lue valent pour la détention en cours : oubliés quand le porteur change (A1 et A2 de l'expert,
        # passage 2 ; sans cela, un presseur retrouvant plus tard ce porteur était mis au repos après un effort quasi nul)
        self.burst = {k: v for k, v in self.burst.items() if v[0] == holder.name}
        self.lanes = {k: v for k, v in self.lanes.items() if k[1] == holder.name}
        team = "away" if holder.team == "home" else "home"
        goal = own_goal(team)
        free = [p for p in players if p.team == team and p.poste != "GK"]
        if not free:
            return
        fresh = [p for p in free if not self.resting(p, now_s)] or free  # celui qui souffle ne presse pas
        presser = self._keep(previous, PRESSEUR, holder.name, fresh, holder.position,
                             min(fresh, key=lambda p: arrival_time_s(p, holder.position)))
        start = self.burst.get(presser.name)
        if start is None or start[0] != holder.name:
            self.burst[presser.name] = (holder.name, now_s)
        elif now_s - start[1] >= PRESS_BURST_S and len(fresh) > 1:  # effort fini : il souffle, un autre prend le relais
            self.rest_until[presser.name] = now_s + press_rest_s(presser)
            del self.burst[presser.name]  # reposé, il repartira pour un nouvel effort
            fresh.remove(presser)
            presser = min(fresh, key=lambda p: arrival_time_s(p, holder.position))
            self.holders[(PRESSEUR, holder.name)] = presser.name
            self.burst[presser.name] = (holder.name, now_s)
        target = press_point(presser, holder, self._lane(presser, holder, players, goal))
        self.assignments[presser.name] = Assignment(PRESSEUR, target, holder.name, holder.velocity,
                                                    press_intensity(presser))
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
        if self.trigger_until.get(team, 0.0) > now_s:  # pressing d'équipe : les partenaires proches suivent (Teamwork)
            marked = {a.mate for a in self.assignments.values()}
            defenders = [p for p in players if p.team == team]
            # le plus libre d'abord : le plus loin de tout défenseur
            near = sorted((p for p in players if p.team == holder.team and p is not holder and p.poste != "GK"
                           and p.name not in marked and p.position.distance_to(holder.position) <= FOLLOW_M),
                          key=lambda p: -min(d.position.distance_to(p.position) for d in defenders))
            # chacun garde son receveur jusqu'à la fin du pressing d'équipe (sans quoi il change de cible en courant)
            near.sort(key=lambda p: p.name not in self.followed.values())
            for receiver in near:
                followers = [p for p in free if self.follows.get(p.name)]
                if not followers:
                    break
                marker = next((p for p in followers if self.followed.get(p.name) == receiver.name), None) or min(
                    [p for p in followers if self.followed.get(p.name) not in {r.name for r in near}] or followers,
                    key=lambda p: p.position.distance_to(receiver.position))
                self.followed[marker.name] = receiver.name
                # côté ballon, sur la ligne de passe : il ferme la solution plutôt que de couvrir son but
                spot = _goal_side(receiver.position, holder.position, marking_distance_m(marker))
                self.assignments[marker.name] = Assignment(MARQUAGE, spot, receiver.name, receiver.velocity)
                free.remove(marker)

    def leaves_the_bloc(self, player: PlayerState, now_s: float) -> bool:
        """Sans rôle et près du ballon, quitte-t-il quand même le bloc pour y aller ? Tiré toutes les 5 s (Teamwork)."""
        leaves, next_s = self.leaving.get(player.name, (False, 0.0))
        if now_s >= next_s:
            leaves = random.random() < leave_probability(player)
            self.leaving[player.name] = (leaves, now_s + LEAVE_REDRAW_S)
        return leaves

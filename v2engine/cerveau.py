"""Cerveau du joueur (ADR 0001, ticket v2-collectif/02) : à chaque tick, chaque joueur passe par quatre temps --
perception (ce qu'il détecte), interprétation (son rôle), décision (action, cible, intensité), puis exécution
(le mouvement et les gestes, résolus hors d'ici : `movement.step`, `possession`, `shooting`, `duel`). La sortie
est une `Intention`, seule chose que l'exécution lit, et qui est enregistrée dans la trace pour la relecture.

Premier passage : reprend à l'identique les règles de déplacement d'avant le ticket (même ordre de tirages
aléatoires, donc mêmes matchs). Les tickets suivants ajoutent des rôles et des raisons ici, pas dans la boucle
de match."""

from __future__ import annotations

import random
from dataclasses import dataclass, replace
from functools import partial

from v2engine.anticipation import loose_ball_target, meeting_point
from v2engine.ball_state import BallState
from v2engine.bloc import Bloc
from v2engine.decision import CONTRE_ATTAQUE, DRIBBLE_SPEED_FACTOR
from v2engine.defense import COMPENSATION, COUVERTURE, MARQUAGE, PRESSEUR, DefensiveRoles, leave_probability
from v2engine.geometry import PITCH_LENGTH_M, PITCH_WIDTH_M, Vec2
from v2engine.movement import PlayerState
from v2engine.off_ball import COUNTER_RUN_DEPTH_M, RUN_INTERVAL_S, SPACE_HOLD_MAX_S, SPACE_REACHED_M, choose_space
from v2engine.offside import HESITATION_INTENSITY, clamp_to_onside, offside_line, respects_the_line
from v2engine.possession import BALL_FRICTION_PER_S, RECEPTION_SPEED_FACTOR
from v2engine.situation import POSSESSION_INSTALLEE, TRANSITION_OFFENSIVE
from v2engine.transition import TransitionPlay

GOAL_CENTER_Y = PITCH_WIDTH_M / 2.0
OPPONENT_GOAL = {"home": Vec2(PITCH_LENGTH_M, GOAL_CENTER_Y), "away": Vec2(0.0, GOAL_CENTER_Y)}
# Distance en dessous de laquelle un joueur va vers le ballon plutôt que vers sa position de
# formation -- IA placeholder (D-V08), pas une vraie prise de décision.
CHASE_RADIUS_M = 15.0
# Joueurs de champ qui restent derrière le ballon en possession installée (validé le 30/10/2026, ticket v2-collectif/06).
REST_DEFENDERS = 2

# Rôles (GLOSSARY.md) et actions.
# Rôles défensifs (presseur, couverture, marquage) : `defense.py` (ticket v2-collectif/07).
PORTEUR, APPEL, SOUTIEN, RECEVEUR, LECTURE, BALLON_LIBRE, REPLACEMENT = (
    "porteur", "appel", "soutien", "receveur visé", "lecture de passe", "ballon libre", "replacement")
# Hors-jeu sifflé : l'attaquant fautif recule le temps de la remise en jeu (ticket v2-collectif/23).
HORS_JEU = "hors-jeu"


@dataclass(frozen=True)
class Intention:
    role: str
    action: str  # "contrôler", "conduire", "se démarquer", "venir au ballon", "couper la passe", "aller au ballon", "se replacer"
    target: Vec2
    intensity: float = 1.0  # part de la vitesse max
    mate: str | None = None  # joueur visé, le cas échéant (porteur pressé, passeur dont on coupe la passe…)
    reason: str = ""  # raison lisible, sans chiffre (stable tant que le rôle dure)
    distance_m: float | None = None  # distance utile à la raison (au ballon, au point d'interception…)
    situation: str | None = None  # situation de jeu de son équipe telle qu'il la perçoit (ticket v2-collectif/03)
    # vitesse de la cible quand elle bouge (le porteur qu'il presse ou soutient) : la loi d'arrivée de
    # `movement.step` porte alors sur la vitesse de rapprochement (ticket v2-collectif/25)
    target_velocity: Vec2 = Vec2(0.0, 0.0)

    def explain(self) -> str:
        """Raison lisible avec sa distance (formatée à la lecture seulement : le match n'en paie pas le coût)."""
        return f"{self.reason} ({self.distance_m:.0f} m)" if self.distance_m is not None else self.reason


@dataclass(frozen=True)
class Perception:
    """Ce que le joueur détecte à cet instant."""
    holder: PlayerState | None  # porteur du ballon, s'il y en a un
    is_receiver: bool  # receveur visé de la passe en cours
    read_point: Vec2 | None  # point où couper la passe en cours, s'il l'a lue (Anticipation, `pass_readers`)
    ball_distance: float


def perceive(player: PlayerState, ball: BallState, players: list[PlayerState]) -> Perception:
    loose = ball.holder is None
    return Perception(
        holder=None if loose else next((p for p in players if p.name == ball.holder), None),
        is_receiver=loose and player.name == ball.receiver,
        read_point=ball.readers.get(player.name) if loose else None,
        ball_distance=ball.position.distance_to(player.position),
    )


def nearest_of_team(player: PlayerState, ball: BallState, players: list[PlayerState]) -> bool:
    """Sur un ballon libre, le plus proche de chaque équipe y va toujours, même au-delà de CHASE_RADIUS_M.
    Calculé seulement quand le rôle en dépend (coût : une boucle sur l'équipe)."""
    return ball.holder is None and player is min(
        (p for p in players or [player] if p.team == player.team), key=lambda p: p.position.distance_to(ball.position))


def interpret(player: PlayerState, ball: BallState, seen: Perception, runs_enabled: bool,
              players: list[PlayerState], defense: DefensiveRoles | None = None, now_s: float = 0.0) -> str:
    """Rôle du joueur à cet instant. Avec `defense` (ticket v2-collectif/07), le joueur de champ dont l'adversaire a le
    ballon prend le rôle que son équipe lui a attribué ; sans rôle, il tient le bloc, sauf s'il le quitte (Teamwork)."""
    if player.name == ball.holder:
        return PORTEUR
    if runs_enabled and seen.holder is not None and seen.holder.team == player.team and player.poste != "GK":
        return APPEL
    if seen.is_receiver:
        return RECEVEUR
    if runs_enabled and ball.holder is None and ball.receiver is not None and ball.last_pass_team == player.team \
            and player.poste != "GK":
        return APPEL  # passe de son équipe en l'air : il poursuit son appel, sans courir au ballon (ticket 06)
    if seen.read_point is not None:
        return LECTURE
    # passe adverse en vol : il garde le rôle attribué comme si le receveur avait le ballon (réserve A2, ticket 09)
    if defense is not None and ball.holder is None and ball.receiver is not None and player.poste != "GK" \
            and ball.last_pass_team not in (None, player.team) and player.name in defense.assignments:
        return defense.assignments[player.name].role
    if defense is not None and seen.holder is not None and seen.holder.team != player.team and player.poste != "GK":
        assigned = defense.assignments.get(player.name)
        if assigned is not None:
            return assigned.role
        if (seen.ball_distance < CHASE_RADIUS_M and not defense.resting(player, now_s)  # il souffle (ticket 08)
                and defense.leaves_the_bloc(player, now_s)):
            return PRESSEUR
        return REPLACEMENT
    if seen.ball_distance >= CHASE_RADIUS_M and not nearest_of_team(player, ball, players):
        return REPLACEMENT
    if ball.holder is None:
        return BALLON_LIBRE
    # porteur proche : un adversaire le presse ; un coéquipier sans appel (le gardien, par exemple) vient en soutien
    return SOUTIEN if seen.holder is not None and seen.holder.team == player.team else PRESSEUR


def stays_behind(player: PlayerState) -> bool:
    """Le défenseur d'équilibre dont l'appel le mènerait devant le ballon reste-t-il derrière ? Teamwork (ticket 06)."""
    return random.random() >= leave_probability(player)


def _rest_defenders(team: list[PlayerState], holder: PlayerState, forward: float) -> list[PlayerState]:
    """Les `REST_DEFENDERS` joueurs de champ les plus reculés de l'équipe, porteur exclu (ticket v2-collectif/06)."""
    field_players = [p for p in team if p is not holder and p.poste != "GK"]
    return sorted(field_players, key=lambda p: forward * p.position.x)[:REST_DEFENDERS]


def decide(player: PlayerState, role: str, ball: BallState, seen: Perception, players: list[PlayerState],
           minute: float, runs: dict[str, tuple[Vec2, float]] | None, situation: str | None = None,
           bloc: Bloc | None = None, defense: DefensiveRoles | None = None,
           transition: TransitionPlay | None = None) -> Intention:
    """Action, cible et intensité selon le rôle (règles d'avant le ticket v2-collectif/02 ; avec `bloc`, le
    replacement et les appels partent de la place du joueur dans le bloc, ticket v2-collectif/04 ; avec `transition`,
    l'appel dans la profondeur d'une contre-attaque, ticket v2-collectif/11)."""
    make = partial(Intention, situation=situation)  # situation perçue, portée par l'intention (ticket 03)
    if role == PORTEUR:
        if ball.receiving:  # pendant sa réception, il avance au pas de contrôle (v2-socle/06)
            return make(role, "contrôler", OPPONENT_GOAL[player.team], RECEPTION_SPEED_FACTOR,
                             reason="temps de réception, il lève la tête")
        return make(role, "conduire", OPPONENT_GOAL[player.team], DRIBBLE_SPEED_FACTOR, reason="conduite vers le but")
    if role == APPEL:
        now_s = minute * 60.0
        target, next_s = runs.get(player.name, (None, 0.0))
        forward = 1.0 if player.team == "home" else -1.0
        # Contre-attaque (ticket v2-collectif/11) : dès qu'il a perçu la récupération (Anticipation, délai de réaction),
        # le coéquipier devant le ballon lance un nouvel appel, dans la profondeur.
        counter = transition is not None and transition.mode.get(player.team) == CONTRE_ATTAQUE \
            and situation == TRANSITION_OFFENSIVE and forward * (player.position.x - ball.position.x) > 0.0
        launch = counter and player.name not in transition.launched
        # Il garde son espace jusqu'à y être (au moins RUN_INTERVAL_S), au plus SPACE_HOLD_MAX_S (ticket v2-collectif/06).
        reached = target is not None and player.position.distance_to(target) <= SPACE_REACHED_M \
            and now_s >= next_s - SPACE_HOLD_MAX_S + RUN_INTERVAL_S
        if target is None or now_s >= next_s or reached or launch:
            opponents = [p for p in players if p.team != player.team]
            anchor = bloc.reference(player, ball.position, situation, now_s) if bloc and situation else None
            if counter:
                transition.launched.add(player.name)
                anchor = (player.home_target if anchor is None else anchor) + Vec2(forward * COUNTER_RUN_DEPTH_M, 0.0)
            mates = [p for p in players if p.team == player.team and p is not player]
            # positions des coéquipiers et espaces qu'ils visent en ce moment (appel encore en cours)
            spots = [m.position for m in mates] + [runs[m.name][0] for m in mates
                                                   if m.name in runs and runs[m.name][1] > now_s]
            target = choose_space(player, opponents, forward, anchor, seen.holder, spots)
            # Équilibre (ticket v2-collectif/06) : en possession installée, les deux joueurs de champ les plus reculés
            # restent derrière le ballon, sauf l'indiscipliné qui monte quand même (Teamwork, courbe du ticket 07).
            if situation == POSSESSION_INSTALLEE and forward * (target.x - ball.position.x) > 0.0 \
                    and player in _rest_defenders(mates + [player], seen.holder, forward) \
                    and stays_behind(player):
                target = Vec2(ball.position.x, target.y)
            # Hors-jeu (ticket 23) : l'attaquant règle son appel sur la ligne, d'autant plus qu'il a de l'Off the
            # Ball. Un joueur à faible Off the Ball part au-delà et se fait prendre. Un seul tirage par appel.
            line = offside_line(player.team, ball.position, opponents)
            if line is not None and respects_the_line(player):
                target = clamp_to_onside(player.team, target, line)
            runs[player.name] = (target, now_s + SPACE_HOLD_MAX_S)
        mate = seen.holder.name if seen.holder is not None else ball.receiver  # passe en l'air : le receveur
        return make(role, "se démarquer", target, mate=mate, reason="appel vers un espace libre")
    if role == RECEVEUR:
        point = meeting_point(player, ball.position, ball.velocity, BALL_FRICTION_PER_S)
        return make(role, "venir au ballon", point, reason="passe pour lui, il va à sa rencontre")
    if role == LECTURE:
        return make(role, "couper la passe", seen.read_point, reason="passe lue, il court l'intercepter",
                         distance_m=player.position.distance_to(seen.read_point))
    if role == REPLACEMENT:
        if bloc is None or situation is None:  # sans bloc (tests unitaires) : sa place de départ
            return make(role, "se replacer", player.home_target, reason="loin du ballon, il rejoint sa place")
        place = bloc.replacement(player, ball.position, situation, minute * 60.0)  # ticket v2-collectif/04
        if place is None:
            return make(role, "tenir sa place", player.position, reason="loin du ballon, il tient sa place dans le bloc")
        return make(role, "se replacer", place, reason="loin du ballon, il rejoint sa place dans le bloc",
                    distance_m=player.position.distance_to(place))
    if role == BALLON_LIBRE:
        point = loose_ball_target(player, ball.position, ball.velocity, BALL_FRICTION_PER_S)
        return make(role, "aller au ballon", point, reason="ballon libre, il va le chercher",
                         distance_m=seen.ball_distance)
    if role == SOUTIEN:
        return make(role, "aller au ballon", ball.position, mate=ball.holder, reason="soutien de son porteur",
                         distance_m=seen.ball_distance, target_velocity=seen.holder.velocity)
    assigned = defense.assignments.get(player.name) if defense is not None else None
    if role in (COUVERTURE, MARQUAGE):
        why = "couvre son presseur, entre le porteur et le but" if role == COUVERTURE else "marque un attaquant dangereux, côté but"
        return make(role, "couvrir" if role == COUVERTURE else "marquer", assigned.target, mate=assigned.mate,
                    reason=why, distance_m=player.position.distance_to(assigned.target),
                    target_velocity=assigned.target_velocity)
    if role == COMPENSATION:  # ticket v2-collectif/09
        return make(role, "compenser", assigned.target, mate=assigned.mate,
                    reason="comble la place laissée par un coéquipier",
                    distance_m=player.position.distance_to(assigned.target))
    if role == PRESSEUR and assigned is not None:  # course orientée, à l'intensité de son Work Rate (ticket 08)
        return make(role, "presser", assigned.target, assigned.intensity, mate=assigned.mate,
                    reason="presse le porteur adverse", distance_m=seen.ball_distance,
                    target_velocity=assigned.target_velocity)
    if defense is not None and seen.holder is not None and assigned is None and player.poste != "GK":
        why = "quitte le bloc pour aller au ballon"  # indiscipline (Teamwork, ticket v2-collectif/07)
    else:
        why = "presse le porteur adverse" if seen.holder is not None else "va au porteur"
    moving = seen.holder.velocity if seen.holder is not None else Vec2(0.0, 0.0)
    return make(role, "aller au ballon", ball.position, mate=ball.holder, reason=why, distance_m=seen.ball_distance,
                target_velocity=moving)


def think(player: PlayerState, ball: BallState, players: list[PlayerState], minute: float,
          runs: dict[str, tuple[Vec2, float]] | None, situation: str | None = None, bloc: Bloc | None = None,
          defense: DefensiveRoles | None = None, transition: TransitionPlay | None = None) -> Intention:
    """Perception, interprétation, décision : l'intention du joueur à cet instant. `situation` : situation de jeu
    perçue (ticket v2-collectif/03) ; avec `bloc`, elle donne la forme du bloc où il se replace (ticket 04) ; avec
    `defense`, les rôles défensifs attribués par son équipe (ticket 07)."""
    now_s = minute * 60.0
    if now_s < ball.offside_out_until.get(player.name, 0.0):
        # Hors-jeu sifflé (ticket v2-collectif/23) : l'attaquant fautif recule le temps que la défense se replace.
        return Intention(HORS_JEU, "reculer", player.home_target, HESITATION_INTENSITY,
                         reason="hors-jeu sifflé, il recule vers sa place", situation=situation)
    seen = perceive(player, ball, players)
    role = interpret(player, ball, seen, runs is not None, players, defense, now_s)
    intention = decide(player, role, ball, seen, players, minute, runs, situation, bloc, defense, transition)
    if now_s < ball.hesitation.get(player.name, 0.0):
        # « Play the whistle » : le défenseur qui a vu le drapeau lève la main et attend, sans s'arrêter de jouer.
        return replace(intention, intensity=min(intention.intensity, HESITATION_INTENSITY),
                       reason="il lève la main, il attend le sifflet")
    return intention

"""Cerveau du joueur (ADR 0001, ticket v2-collectif/02) : à chaque tick, chaque joueur passe par quatre temps --
perception (ce qu'il détecte), interprétation (son rôle), décision (action, cible, intensité), puis exécution
(le mouvement et les gestes, résolus hors d'ici : `movement.step`, `possession`, `shooting`, `duel`). La sortie
est une `Intention`, seule chose que l'exécution lit, et qui est enregistrée dans la trace pour la relecture.

Premier passage : reprend à l'identique les règles de déplacement d'avant le ticket (même ordre de tirages
aléatoires, donc mêmes matchs). Les tickets suivants ajoutent des rôles et des raisons ici, pas dans la boucle
de match."""

from __future__ import annotations

from dataclasses import dataclass

from v2engine.anticipation import loose_ball_target, meeting_point
from v2engine.ball_state import BallState
from v2engine.decision import DRIBBLE_SPEED_FACTOR
from v2engine.geometry import PITCH_LENGTH_M, PITCH_WIDTH_M, Vec2
from v2engine.movement import PlayerState
from v2engine.off_ball import RUN_INTERVAL_S, choose_space
from v2engine.possession import BALL_FRICTION_PER_S, RECEPTION_SPEED_FACTOR

GOAL_CENTER_Y = PITCH_WIDTH_M / 2.0
OPPONENT_GOAL = {"home": Vec2(PITCH_LENGTH_M, GOAL_CENTER_Y), "away": Vec2(0.0, GOAL_CENTER_Y)}
# Distance en dessous de laquelle un joueur va vers le ballon plutôt que vers sa position de
# formation -- IA placeholder (D-V08), pas une vraie prise de décision.
CHASE_RADIUS_M = 15.0

# Rôles (GLOSSARY.md) et actions.
PORTEUR, APPEL, SOUTIEN, RECEVEUR, LECTURE, BALLON_LIBRE, PRESSEUR, REPLACEMENT = (
    "porteur", "appel", "soutien", "receveur visé", "lecture de passe", "ballon libre", "presseur", "replacement")


@dataclass(frozen=True)
class Intention:
    role: str
    action: str  # "contrôler", "conduire", "se démarquer", "venir au ballon", "couper la passe", "aller au ballon", "se replacer"
    target: Vec2
    intensity: float = 1.0  # part de la vitesse max
    mate: str | None = None  # joueur visé, le cas échéant (porteur pressé, passeur dont on coupe la passe…)
    reason: str = ""  # raison lisible, sans chiffre (stable tant que le rôle dure)
    distance_m: float | None = None  # distance utile à la raison (au ballon, au point d'interception…)

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
              players: list[PlayerState]) -> str:
    """Rôle du joueur à cet instant."""
    if player.name == ball.holder:
        return PORTEUR
    if runs_enabled and seen.holder is not None and seen.holder.team == player.team and player.poste != "GK":
        return APPEL
    if seen.is_receiver:
        return RECEVEUR
    if seen.read_point is not None:
        return LECTURE
    if seen.ball_distance >= CHASE_RADIUS_M and not nearest_of_team(player, ball, players):
        return REPLACEMENT
    if ball.holder is None:
        return BALLON_LIBRE
    # porteur proche : un adversaire le presse ; un coéquipier sans appel (le gardien, par exemple) vient en soutien
    return SOUTIEN if seen.holder is not None and seen.holder.team == player.team else PRESSEUR


def decide(player: PlayerState, role: str, ball: BallState, seen: Perception, players: list[PlayerState],
           minute: float, runs: dict[str, tuple[Vec2, float]] | None) -> Intention:
    """Action, cible et intensité selon le rôle (règles d'avant le ticket v2-collectif/02, inchangées)."""
    if role == PORTEUR:
        if ball.receiving:  # pendant sa réception, il avance au pas de contrôle (v2-socle/06)
            return Intention(role, "contrôler", OPPONENT_GOAL[player.team], RECEPTION_SPEED_FACTOR,
                             reason="temps de réception, il lève la tête")
        return Intention(role, "conduire", OPPONENT_GOAL[player.team], DRIBBLE_SPEED_FACTOR, reason="conduite vers le but")
    if role == APPEL:
        now_s = minute * 60.0
        target, next_s = runs.get(player.name, (None, 0.0))
        if target is None or now_s >= next_s:
            opponents = [p for p in players if p.team != player.team]
            target = choose_space(player, opponents, 1.0 if player.team == "home" else -1.0)
            runs[player.name] = (target, now_s + RUN_INTERVAL_S)
        return Intention(role, "se démarquer", target, mate=seen.holder.name, reason="appel vers un espace libre")
    if role == RECEVEUR:
        point = meeting_point(player, ball.position, ball.velocity, BALL_FRICTION_PER_S)
        return Intention(role, "venir au ballon", point, reason="passe pour lui, il va à sa rencontre")
    if role == LECTURE:
        return Intention(role, "couper la passe", seen.read_point, reason="passe lue, il court l'intercepter",
                         distance_m=player.position.distance_to(seen.read_point))
    if role == REPLACEMENT:
        return Intention(role, "se replacer", player.home_target, reason="loin du ballon, il rejoint sa place")
    if role == BALLON_LIBRE:
        point = loose_ball_target(player, ball.position, ball.velocity, BALL_FRICTION_PER_S)
        return Intention(role, "aller au ballon", point, reason="ballon libre, il va le chercher",
                         distance_m=seen.ball_distance)
    if role == SOUTIEN:
        return Intention(role, "aller au ballon", ball.position, mate=ball.holder, reason="soutien de son porteur",
                         distance_m=seen.ball_distance)
    why = "presse le porteur adverse" if seen.holder is not None else "va au porteur"
    return Intention(role, "aller au ballon", ball.position, mate=ball.holder, reason=why, distance_m=seen.ball_distance)


def think(player: PlayerState, ball: BallState, players: list[PlayerState], minute: float,
          runs: dict[str, tuple[Vec2, float]] | None) -> Intention:
    """Perception, interprétation, décision : l'intention du joueur à cet instant."""
    seen = perceive(player, ball, players)
    role = interpret(player, ball, seen, runs is not None, players)
    return decide(player, role, ball, seen, players, minute, runs)

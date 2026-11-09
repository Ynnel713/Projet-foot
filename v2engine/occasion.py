"""Danger de la situation et grosses occasions (ticket v2-collectif/28c). Lecture seule : aucun tirage aléatoire,
aucune écriture sur les joueurs ou le ballon ; le jeu est le même avec ou sans ce calcul.

- **Danger** d'une équipe à un instant : la meilleure occasion potentielle de ses joueurs de champ (qualité de
  l'occasion du ticket 28a, `shooting.occasion_quality` : « s'il touchait le ballon ici »), pondérée par la chance que
  le ballon leur parvienne. Ballon tenu par l'équipe : 1 pour le porteur, la réussite de la passe pour un coéquipier
  (`possession.pass_success_probability`, hors-jeu exclus). Ballon libre (passe, centre, rebond) : course au ballon sur
  sa trajectoire freinée, voir `reach_probability` ; sur une passe adverse en vol, seuls les joueurs qui l'ont lue
  (`BallState.readers`) la disputent. Ballon mort ou tir en vol : pas de danger.
- **Grosse occasion** : séquence dont le pic de danger atteint `BIG_CHANCE_DANGER`, quelle que soit l'issue (tir,
  tacle, interception, dégagement, ballon non repris...). Une séquence s'ouvre quand le danger d'une équipe atteint
  `SEQUENCE_FLOOR` et se ferme quand il retombe en dessous, ou au tir ; seules les grosses occasions sont tracées."""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass, replace

from v2engine.ball_state import BallState
from v2engine.cerveau import OPPONENT_GOAL
from v2engine.geometry import Vec2
from v2engine.movement import PlayerState, max_speed_mps
from v2engine.offside import offside_at_pass
from v2engine.possession import BALL_FRICTION_PER_S, BALL_STOPPED_MPS, pass_success_probability
from v2engine.shooting import FLYING, SHOOTING_RANGE_M, occasion_quality
from v2engine.trace import ChanceEvent, ShotEvent

# Seuil de grosse occasion (ticket 28c, proposé le 08/11/2026, validé par délégation du propriétaire) : voir le ticket
# pour le nombre par match. Plancher de séquence : moitié du seuil (une séquence ne se coupe pas au moindre creux).
BIG_CHANCE_DANGER = 0.20
SEQUENCE_FLOOR = BIG_CHANCE_DANGER / 2.0
# Course au ballon libre (ordres de grandeur, réels non trouvés) : trajectoire suivie `REACH_HORIZON_S` par pas de
# `REACH_STEP_S` ; un attaquant en retard de r secondes sur le ballon garde exp(-r / `REACH_LATE_S`) de chance de le
# toucher (0,1 s de retard, le ballon qui passe à un mètre : 61 % ; 0,4 s : 14 %).
REACH_HORIZON_S = 3.0
REACH_STEP_S = 0.1
REACH_LATE_S = 0.2
TOUCH_M = 0.41  # portée du contact au ballon, la même que `match.CONTROL_RADIUS_M` (test)

_TEAMS = ("home", "away")


def _ball_path(ball: BallState) -> list[tuple[float, float, Vec2]]:
    """Points (instant, distance parcourue, position) de la trajectoire freinée du ballon ; arrêté : sa position."""
    log_f = math.log(BALL_FRICTION_PER_S)
    if ball.velocity.length() < BALL_STOPPED_MPS:
        return [(0.0, 0.0, ball.position)]
    path, t = [], 0.0
    while t <= REACH_HORIZON_S + 1e-9:
        travelled = (BALL_FRICTION_PER_S ** t - 1.0) / log_f
        path.append((t, travelled * ball.velocity.length(), ball.position + ball.velocity * travelled))
        t += REACH_STEP_S
    return path


def _arrival_s(player: PlayerState, point: Vec2) -> float:
    """Temps pour toucher le ballon en `point`, à sa vitesse max, sans temps de réaction (`anticipation.meeting_point`)."""
    return max(0.0, player.position.distance_to(point) - TOUCH_M) / max_speed_mps(player.pace)


def reach_probability(player: PlayerState, ball: BallState, opponents: list[PlayerState]) -> tuple[float, Vec2 | None]:
    """Chance que `player` touche le ballon libre avant un adversaire, et le point de contact. 1 s'il peut être sur sa
    trajectoire à temps avant le premier adversaire qui le peut (premier point atteint) ; sinon exp(-retard /
    `REACH_LATE_S`), au point de plus petit retard sur la portion de trajectoire que le ballon parcourt avant ce premier
    adversaire. Ballon en l'air : seulement après son point de chute. Ballon arrêté : course au ballon, l'adversaire le
    plus rapide fixe l'échéance."""
    path = [(t, point) for t, travelled, point in _ball_path(ball) if travelled >= ball.aerial_left_m]
    if not path:
        return 0.0, None
    if len(path) == 1:
        point = path[0][1]
        late = _arrival_s(player, point) - min((_arrival_s(o, point) for o in opponents), default=math.inf)
    else:
        cut = next((t for t, point in path if any(_arrival_s(o, point) <= t for o in opponents)), path[-1][0])
        lates = [(_arrival_s(player, point) - t, point) for t, point in path if t <= cut]
        late, point = next(((lt, pt) for lt, pt in lates if lt <= 0.0), min(lates, key=lambda e: e[0]))
    return (1.0 if late <= 0.0 else math.exp(-late / REACH_LATE_S)), point


def situation_danger(team: str, ball: BallState, players: list[PlayerState]) -> tuple[float, PlayerState | None]:
    """Danger de `team` à cet instant et joueur qui le porte (meilleure occasion pondérée), ou (0, None)."""
    if ball.restart is not None or ball.shot_in_flight:
        return 0.0, None
    by_name = {p.name: p for p in players}
    holder = by_name.get(ball.holder) if ball.holder is not None else None
    if holder is not None and holder.team != team:
        return 0.0, None
    goal = OPPONENT_GOAL[team]
    opponents = [p for p in players if p.team != team]
    keeper = next((p for p in opponents if p.poste == "GK"), None)
    near = [p for p in players if p.team == team and p.poste != "GK"
            and p.position.distance_to(goal) <= SHOOTING_RANGE_M]
    if holder is not None:
        offside = offside_at_pass(team, ball.position, near, opponents)

        def reach(p: PlayerState) -> tuple[float, Vec2 | None]:
            if p.name == holder.name:
                return 1.0, p.position
            return (0.0 if p.name in offside else pass_success_probability(holder, p, opponents)), p.position
    else:
        # passe adverse en vol : seuls ceux qui l'ont lue (Anticipation, `anticipation.pass_readers`) courent la couper
        their_pass = ball.receiver is not None and ball.last_pass_team not in (None, team)

        def reach(p: PlayerState) -> tuple[float, Vec2 | None]:
            if p.name in ball.offside_watch or (their_pass and p.name not in ball.readers):
                return 0.0, None
            return reach_probability(p, ball, opponents)
    best, who = 0.0, None
    for p in near:
        r, point = reach(p)
        if r <= best or point is None:
            continue  # la qualité ne dépasse jamais 1 : il ne peut pas faire mieux
        at = p if point == p.position else replace(p, position=point)  # là où il toucherait le ballon
        value = r * occasion_quality(at, goal, keeper, opponents)
        if value > best:
            best, who = value, at
    return best, who


@dataclass
class _Open:
    start: float
    peak: float = 0.0
    peak_minute: float = 0.0
    player: str = ""
    x: float = 0.0
    y: float = 0.0
    origin: str = ""


class ChanceTracker:
    """Suit le danger des deux équipes et trace les grosses occasions (`ChanceEvent`) dans `chances`. Appelé après
    chaque pas du ballon ; `origin_of(joueur)` dit comment la situation est née (même vocabulaire que le tir)."""

    def __init__(self, chances: list[ChanceEvent]) -> None:
        self.chances = chances
        self.open: dict[str, _Open] = {}
        self.seen_shots = 0
        self.holder_team: str | None = None
        self.flying: dict[str, int] = {}  # tir en vol par équipe (rang dans la trace) : issue connue plus tard (05b)

    def update(self, minute: float, ball: BallState, players: list[PlayerState], shots: list[ShotEvent],
               origin_of: Callable[[PlayerState], str]) -> None:
        first, self.seen_shots = self.seen_shots, len(shots)
        new_shots = shots[first:]
        holder = next((p for p in players if p.name == ball.holder), None) if ball.holder is not None else None
        for team in _TEAMS:
            rank = next((first + i for i in range(len(new_shots) - 1, -1, -1) if new_shots[i].team == team), None)
            shot = shots[rank] if rank is not None else None
            danger, who = situation_danger(team, ball, players)
            state = self.open.get(team)
            if state is None and max(danger, shot.quality if shot else 0.0) >= SEQUENCE_FLOOR:
                state = self.open[team] = _Open(start=minute)
            if state is None:
                continue
            if who is not None and danger > state.peak:
                state.peak, state.peak_minute, state.player = danger, minute, who.name
                state.x, state.y, state.origin = who.position.x, who.position.y, origin_of(who)
            if shot is not None:
                if shot.quality > state.peak:  # tir d'une première intention : sa qualité au départ
                    state.peak, state.peak_minute, state.player = shot.quality, minute, shot.player
                    state.x, state.y, state.origin = shot.x, shot.y, shot.origin
                if shot.outcome == FLYING:
                    self.flying[team] = rank  # tir en vol (ticket v2-realisme/05a) : on attend son issue
                else:
                    self._close(team, minute, "tir : " + shot.outcome, shot=True)
            elif team in self.flying:
                # issue lue sur la trajectoire ; tir sans issue (sifflet pendant le vol, ballon mort avant la ligne) : « en
                # vol » (réserve A3 du 05b)
                outcome = shots[self.flying[team]].outcome
                if outcome != FLYING or ball.shot_flight is None:
                    self._close(team, minute, "tir : " + outcome, shot=True)
            elif danger < SEQUENCE_FLOOR:
                self._close(team, minute, self._outcome(team, ball, holder, players))
        self.holder_team = holder.team if holder is not None else None

    def _outcome(self, team: str, ball: BallState, holder: PlayerState | None, players: list[PlayerState]) -> str:
        """Comment finit une séquence sans tir."""
        if ball.restart is not None:
            return "ballon mort : " + ball.restart.kind
        if holder is not None and holder.team != team:
            if self.holder_team == team:
                return "tacle"
            return "gardien" if holder.poste == "GK" else "interception"
        if holder is not None:
            return "danger retombé"
        toucher = next((p for p in players if p.name == ball.last_toucher), None)
        return "dégagement" if toucher is not None and toucher.team != team else "ballon non repris"

    def _close(self, team: str, minute: float, outcome: str, shot: bool = False) -> None:
        self.flying.pop(team, None)
        state = self.open.pop(team)
        if state.peak >= BIG_CHANCE_DANGER:
            self.chances.append(ChanceEvent(state.start, state.peak_minute, minute, team, state.player, state.x,
                                            state.y, state.peak, outcome, state.origin, shot))

    def close_all(self, minute: float, outcome: str = "fin de période") -> None:
        self.flying = {}
        for team in list(self.open):
            self._close(team, minute, outcome)
        self.holder_team = None

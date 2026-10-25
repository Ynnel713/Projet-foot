"""Orchestration d'un match V2, Phase 1 (déplacement, docs/PLAN_V2.md) : place les 22 titulaires
réels d'un match sur un terrain 2D et les fait bouger -- vers leur position de formation, ou vers
le ballon s'ils en sont proches (IA placeholder volontairement simpliste, D-V08 ; la vraie prise
de décision vient en Phase 5+). Calcule une trace complète du match une fois (voir `trace.py`,
D-V04) ; un rendu, pas encore construit, la rejouera ensuite. Une seule fonction pour le mode
"regardé" et le mode "tout simuler sans regarder" (D-V05) : seul le rendu, en aval, est optionnel
-- rien ici ne dépend de si le match sera affiché."""

from __future__ import annotations

from ligue1sim.clubs import Club
from ligue1sim.lineup import Lineup, pick_best_formation

from v2engine.attributes import player_attribute
from v2engine.anticipation import loose_ball_target, meeting_point, pass_readers
from v2engine.ball_state import BallState
from v2engine.duel import resolve_tackle, should_attempt_tackle
from v2engine.formation import initial_positions
from v2engine.geometry import PITCH_LENGTH_M, PITCH_WIDTH_M, Vec2, clamp_to_pitch
from v2engine.movement import PlayerState, step
from v2engine.off_ball import RUN_INTERVAL_S, choose_space
from v2engine.decision import DECISION_INTERVAL_S, DRIBBLE_SPEED_FACTOR, choose_action
from v2engine.possession import BALL_FRICTION_PER_S, BALL_STOPPED_MPS, RECEPTION_SPEED_FACTOR, attempt_control, pass_velocity, reception_delay_s
from v2engine.shooting import attempt_shot
from v2engine.trace import BallSnapshot, MatchTrace, PlayerSnapshot

GOAL_CENTER_Y = PITCH_WIDTH_M / 2.0
# But adverse d'une équipe, par convention de ce moteur (voir `formation.initial_positions`,
# D-V03 : domicile attaque vers x=PITCH_LENGTH_M, extérieur vers x=0).
_OPPONENT_GOAL = {"home": Vec2(PITCH_LENGTH_M, GOAL_CENTER_Y), "away": Vec2(0.0, GOAL_CENTER_Y)}

BALL_RADIUS_M = 0.11
PLAYER_RADIUS_M = 0.3
# Distance de contact ballon-joueur (Phase 2) : somme des deux rayons -- en dessous, un joueur
# peut tenter de contrôler le ballon (voir `possession.attempt_control`).
CONTROL_RADIUS_M = BALL_RADIUS_M + PLAYER_RADIUS_M
# Distance de contact direct (Phase 3) : en dessous, un adversaire du porteur peut tenter un
# tacle (voir `duel.should_attempt_tackle`) -- plus large que CONTROL_RADIUS_M (contact entre
# deux joueurs, pas entre un joueur et le ballon seul).
TACKLE_RADIUS_M = 1.5
# Distance en dessous de laquelle un joueur va vers le ballon plutôt que vers sa position de
# formation -- IA placeholder (D-V08), pas une vraie prise de décision.
CHASE_RADIUS_M = 15.0
# ponytail : décroissance exponentielle simple (par seconde), pas un vrai coefficient de
# frottement calibré -- à affiner si le rendu le justifie.


def _build_players(lineup: Lineup, team: str, positions: dict[str, Vec2]) -> list[PlayerState]:
    center = Vec2(PITCH_LENGTH_M / 2.0, PITCH_WIDTH_M / 2.0)
    states = []
    for player in lineup.players:
        pos = positions.get(player.name, center)
        states.append(
            PlayerState(
                name=player.name,
                team=team,
                poste=player.poste,
                position=pos,
                velocity=Vec2(0.0, 0.0),
                pace=player_attribute(player, "Pace"),
                acceleration=player_attribute(player, "Acceleration"),
                stamina=player_attribute(player, "Stamina"),
                home_target=pos,
                radius_m=PLAYER_RADIUS_M,
                attributes=player.attributes,
            )
        )
    return states


def _resolve_player_collisions(players: list[PlayerState]) -> None:
    """Écarte deux joueurs qui se chevauchent -- correction de position pure, pas de vitesse
    (suffisant pour éviter un chevauchement durable, voir critère d'acceptation Phase 1,
    docs/PLAN_V2.md). ponytail : boucle O(n²) (22 joueurs -> 231 paires/tick) ; à optimiser (grille
    spatiale) si la performance du mode batch (NFR-V01) le justifie plus tard."""
    for i in range(len(players)):
        for j in range(i + 1, len(players)):
            a, b = players[i], players[j]
            delta = b.position - a.position
            dist = delta.length()
            min_dist = a.radius_m + b.radius_m
            if 0.0 < dist < min_dist:
                push = delta.normalized() * ((min_dist - dist) / 2.0)
                a.position = clamp_to_pitch(a.position - push)
                b.position = clamp_to_pitch(b.position + push)


def _nearest_opponent_in_range(holder: PlayerState, players: list[PlayerState], radius_m: float) -> PlayerState | None:
    opponents_in_range = [
        p for p in players if p.team != holder.team and holder.position.distance_to(p.position) < radius_m
    ]
    if not opponents_in_range:
        return None
    return min(opponents_in_range, key=lambda p: holder.position.distance_to(p.position))


def _goalkeeper(team: str, players: list[PlayerState]) -> PlayerState | None:
    """Gardien de `team`, ou `None` si l'effectif n'en compte aucun (cas synthétique sans
    gardien, voir docs/PLAN_V2.md Phase 1) -- `shooting.shot_probability` s'en accommode (repli
    neutre, jamais une erreur)."""
    return next((p for p in players if p.team == team and p.poste == "GK"), None)


def _step_ball(ball: BallState, dt: float, players: list[PlayerState], now_s: float = 0.0) -> str | None:
    """Avance le ballon d'un tick (mutation en place) : si un joueur le contrôle déjà, un
    adversaire à portée directe peut d'abord tenter un tacle (Phase 3, Tackling/Strength/
    Balance/Aggression) ; sinon, après son temps de réception (`possession.reception_delay_s`, v2-socle/06)
    puis toutes les `DECISION_INTERVAL_S`, il choisit de tirer, passer ou
    conduire (Phase 5, `decision.choose_action`, Decisions) -- tir résolu par Finishing/Composure
    contre le gardien (Phase 4), passe par Passing/Technique (Phase 2), conduite = il garde le
    ballon et avance (voir `simulate_match`). Loin de tout porteur, trajectoire physique simple,
    et tout joueur à son contact tente de contrôler le ballon (First Touch) -- un contrôle raté
    le fait partir dans une direction imprévisible plutôt que d'être proprement reçu (interaction
    passive, comme en Phase 1, pas un rebond volontaire). Retourne l'équipe qui vient de marquer
    ("home"/"away"), ou `None`."""
    if ball.holder is not None:
        holder = next((p for p in players if p.name == ball.holder), None)
        if holder is None:
            ball.holder = None  # détenteur introuvable (ne devrait pas arriver hors test) -- ballon relâché
            return None
        ball.position = holder.position

        challenger = _nearest_opponent_in_range(holder, players, TACKLE_RADIUS_M)
        if challenger is not None and should_attempt_tackle(player_attribute(challenger, "Aggression"), dt):
            result = resolve_tackle(challenger, holder)
            if result.won:
                ball.holder = challenger.name
                # nouveau porteur : contrôle et lève la tête avant de décider (v2-socle/06)
                ball.next_decision_s = now_s + reception_delay_s(challenger, [p for p in players if p.team != challenger.team])
                ball.receiving = True
                ball.velocity = Vec2(0.0, 0.0)
            # Tacle raté (faute ou non) : le porteur garde le ballon ce tick, rien d'autre ne
            # change -- la faute en elle-même n'a pas encore de conséquence de jeu (coup franc,
            # Phase 5+, voir docs/PLAN_V2.md).
            return None

        if now_s < ball.next_decision_s:
            return None  # conduite en cours : le porteur garde le ballon jusqu'à sa prochaine réévaluation
        ball.next_decision_s = now_s + DECISION_INTERVAL_S
        ball.receiving = False

        opponent_team = "away" if holder.team == "home" else "home"
        goal = _OPPONENT_GOAL[holder.team]
        keeper = _goalkeeper(opponent_team, players)
        action = choose_action(holder, players, goal, keeper)
        if action.kind == "shot":
            scored = attempt_shot(holder, keeper, holder.position.distance_to(goal), GOAL_CENTER_Y)
            if scored:
                ball.holder = None
                ball.position = Vec2(PITCH_LENGTH_M / 2.0, PITCH_WIDTH_M / 2.0)  # remise en jeu au centre
                ball.velocity = Vec2(0.0, 0.0)
                return holder.team
            # Tir non converti (arrêté ou cadré sans but) : le gardien adverse récupère le ballon
            # -- repli simple (pas de sortie de but/corner modélisée, Phase 5+), voir
            # docs/PLAN_V2.md. Sans gardien identifiable (effectif synthétique), le ballon reste
            # simplement libre là où le tir a été tenté.
            if keeper is not None:
                ball.holder = keeper.name
                ball.next_decision_s = now_s + reception_delay_s(keeper, [p for p in players if p.team != keeper.team])
                ball.receiving = True
                ball.position = keeper.position
            else:
                ball.holder = None
                ball.velocity = Vec2(0.0, 0.0)
            return None

        if action.kind == "pass":
            ball.velocity = pass_velocity(holder, action.target, [p for p in players if p.team != holder.team])
            ball.holder = None
            ball.last_pass_team = holder.team
            ball.receiver = action.target.name
            opponents = [p for p in players if p.team != holder.team]
            ball.readers = pass_readers(holder.position, ball.velocity, action.target.position, opponents)
        else:
            ball.velocity = Vec2(0.0, 0.0)  # conduite : le ballon suit le porteur (voir `simulate_match`)
        return None

    ball.position = clamp_to_pitch(ball.position + ball.velocity * dt)
    ball.velocity = ball.velocity * (BALL_FRICTION_PER_S**dt)
    if ball.velocity.length() < BALL_STOPPED_MPS:
        ball.receiver = None  # passe morte : ballon libre pour tous, plus de receveur désigné

    for player in players:
        if ball.position.distance_to(player.position) >= CONTROL_RADIUS_M:
            continue
        if attempt_control(player, ball.velocity, [p for p in players if p.team != player.team]):
            ball.holder = player.name
            ball.readers = {}
            ball.receiver = None
            ball.next_decision_s = now_s + reception_delay_s(player, [p for p in players if p.team != player.team])
            ball.receiving = True
            ball.velocity = Vec2(0.0, 0.0)
        else:
            ball.receiver = None  # contrôle raté : le ballon n'est plus « pour » personne
            away = ball.position - player.position
            # Ballon et joueur exactement superposés (direction de séparation indéfinie) : repart
            # dans le sens de course du joueur, ou une direction fixe à défaut de vitesse.
            direction = away.normalized() if away.length() > 1e-9 else (
                player.velocity.normalized() if player.velocity.length() > 1e-9 else Vec2(1.0, 0.0)
            )
            ball.velocity = player.velocity if player.velocity.length() > 0.1 else direction * 1.0
            ball.position = clamp_to_pitch(player.position + direction * CONTROL_RADIUS_M)
        break


def _step_player(
    player: PlayerState,
    ball: BallState,
    dt: float,
    minute: float,
    players: list[PlayerState] | None = None,
    runs: dict[str, tuple[Vec2, float]] | None = None,
) -> PlayerState:
    """Le porteur avance vers le but adverse : au pas de contrôle pendant sa réception (`RECEPTION_SPEED_FACTOR`,
    v2-socle/06), puis en conduite, un peu moins vite qu'en course (`DRIBBLE_SPEED_FACTOR`) ;
    ses coéquipiers (hors gardien) cherchent un espace libre (Off the Ball, `off_ball.choose_space`,
    réévalué toutes les `RUN_INTERVAL_S`, mémorisé dans `runs`) ; le receveur visé d'une passe court au-devant
    du ballon (`anticipation.meeting_point`, v2-socle/01) ; un adversaire qui a lu la passe court la
    couper (Anticipation, `ball.readers`) ; les autres vont au ballon s'il est proche -- ballon libre : vers
    son point d'arrêt selon Anticipation --, sinon à leur position de formation (IA placeholder, D-V08)."""
    if player.name == ball.holder:
        # pendant sa réception, il avance au pas de contrôle ; ensuite, en conduite (v2-socle/06)
        speed = RECEPTION_SPEED_FACTOR if ball.receiving else DRIBBLE_SPEED_FACTOR
        return step(player, dt, _OPPONENT_GOAL[player.team], minute, speed)
    holder = next((p for p in players or [] if p.name == ball.holder), None)
    if runs is not None and holder is not None and holder.team == player.team and player.poste != "GK":
        now_s = minute * 60.0
        target, next_s = runs.get(player.name, (None, 0.0))
        if target is None or now_s >= next_s:
            opponents = [p for p in players if p.team != player.team]
            target = choose_space(player, opponents, 1.0 if player.team == "home" else -1.0)
            runs[player.name] = (target, now_s + RUN_INTERVAL_S)
        return step(player, dt, target, minute)
    if ball.holder is None and player.name == ball.receiver:  # vient au-devant de la passe (v2-socle/01)
        return step(player, dt, meeting_point(player, ball.position, ball.velocity, BALL_FRICTION_PER_S), minute)
    if ball.holder is None and player.name in ball.readers:
        return step(player, dt, ball.readers[player.name], minute)  # a lu la passe : court la couper
    nearest_of_team = ball.holder is None and player is min(
        (p for p in players or [player] if p.team == player.team), key=lambda p: p.position.distance_to(ball.position)
    )  # sur un ballon libre, le plus proche de chaque équipe y va toujours, même au-delà de CHASE_RADIUS_M
    if ball.position.distance_to(player.position) >= CHASE_RADIUS_M and not nearest_of_team:
        return step(player, dt, player.home_target, minute)
    if ball.holder is None:  # ballon libre : vise où il va s'arrêter, selon Anticipation
        return step(player, dt, loose_ball_target(player, ball.position, ball.velocity, BALL_FRICTION_PER_S), minute)
    return step(player, dt, ball.position, minute)


def simulate_match(
    home_club: Club,
    away_club: Club,
    *,
    duration_minutes: float = 90.0,
    tick_seconds: float = 0.1,
    record_every: int = 10,
) -> MatchTrace:
    """Simule un match de bout en bout (Phase 1 : déplacement seul, pas encore de score) et
    retourne sa trace complète (voir `trace.py`). `record_every` : un tick sur N est conservé dans
    la trace (sous-échantillonnage du rendu, le calcul physique tourne à `tick_seconds` quoi qu'il
    arrive)."""
    home_lineup = pick_best_formation(home_club)
    away_lineup = pick_best_formation(away_club)

    home_positions = initial_positions(home_lineup, attacking_right=True)
    away_positions = initial_positions(away_lineup, attacking_right=False)

    players = _build_players(home_lineup, "home", home_positions) + _build_players(away_lineup, "away", away_positions)
    ball = BallState(position=Vec2(PITCH_LENGTH_M / 2.0, PITCH_WIDTH_M / 2.0), velocity=Vec2(0.0, 0.0))

    trace = MatchTrace(home=home_club.name, away=away_club.name, tick_seconds=tick_seconds * record_every)

    runs: dict[str, tuple[Vec2, float]] = {}  # espace visé par chaque joueur sans ballon (Off the Ball)
    n_ticks = int(duration_minutes * 60.0 / tick_seconds)
    for i in range(n_ticks):
        minute = i * tick_seconds / 60.0
        players = [_step_player(p, ball, tick_seconds, minute, players, runs) for p in players]
        _resolve_player_collisions(players)
        scoring_team = _step_ball(ball, tick_seconds, players, i * tick_seconds)
        if scoring_team is not None:
            trace.record_goal(scoring_team, minute)

        if i % record_every == 0:
            trace.record(
                minute,
                [PlayerSnapshot(name=p.name, team=p.team, poste=p.poste, position=p.position) for p in players],
                BallSnapshot(position=ball.position),
            )

    return trace

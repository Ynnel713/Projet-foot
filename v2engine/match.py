"""Orchestration d'un match V2, Phase 1 (déplacement, docs/PLAN_V2.md) : place les 22 titulaires
réels d'un match sur un terrain 2D et les fait bouger -- vers leur position de formation, ou vers
le ballon s'ils en sont proches (IA placeholder volontairement simpliste, D-V08 ; la vraie prise
de décision vient en Phase 5+). Calcule une trace complète du match une fois (voir `trace.py`,
D-V04) ; un rendu, pas encore construit, la rejouera ensuite. Une seule fonction pour le mode
"regardé" et le mode "tout simuler sans regarder" (D-V05) : seul le rendu, en aval, est optionnel
-- rien ici ne dépend de si le match sera affiché."""

from __future__ import annotations

from collections.abc import Callable

from ligue1sim.clubs import Club
from ligue1sim.lineup import Lineup, pick_best_formation

from v2engine.attributes import player_attribute
from v2engine.anticipation import pass_readers, reaction_delay_s
from v2engine.ball_state import BallState
from v2engine.bloc import Bloc
from v2engine.duel import resolve_tackle, should_attempt_tackle
from v2engine.formation import initial_positions
from v2engine.geometry import PITCH_LENGTH_M, PITCH_WIDTH_M, Vec2, clamp_to_pitch
from v2engine.movement import PlayerState, step
from v2engine.cerveau import GOAL_CENTER_Y, OPPONENT_GOAL, Intention, think
from v2engine.decision import DECISION_INTERVAL_S, choose_action
from v2engine.possession import BALL_FRICTION_PER_S, BALL_STOPPED_MPS, attempt_control, pass_velocity, reception_delay_s
from v2engine.shooting import attempt_shot
from v2engine.situation import SituationTracker
from v2engine.trace import BallSnapshot, DecisionRecord, MatchTrace, PlayerSnapshot, SituationRecord

# But adverse d'une équipe, par convention de ce moteur (voir `formation.initial_positions`,
# D-V03 : domicile attaque vers x=PITCH_LENGTH_M, extérieur vers x=0).
_OPPONENT_GOAL = OPPONENT_GOAL

BALL_RADIUS_M = 0.11
PLAYER_RADIUS_M = 0.3
# Distance de contact ballon-joueur (Phase 2) : somme des deux rayons -- en dessous, un joueur
# peut tenter de contrôler le ballon (voir `possession.attempt_control`).
CONTROL_RADIUS_M = BALL_RADIUS_M + PLAYER_RADIUS_M
# Distance de contact direct (Phase 3) : en dessous, un adversaire du porteur peut tenter un
# tacle (voir `duel.should_attempt_tackle`) -- plus large que CONTROL_RADIUS_M (contact entre
# deux joueurs, pas entre un joueur et le ballon seul).
TACKLE_RADIUS_M = 1.5
# Un duel par confrontation (v2-socle/03, validé le 25/10/2026) : un défenseur tente au plus un tacle
# tant qu'il reste à moins de CONFRONTATION_END_M du même porteur ; un tacle raté l'élimine
# FAILED_TACKLE_RECOVERY_S (temps pour se relever et se replacer). Durée réelle non trouvée : ordre de grandeur.
CONFRONTATION_END_M = 3.0
FAILED_TACKLE_RECOVERY_S = 1.5
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


def _step_ball(ball: BallState, dt: float, players: list[PlayerState], now_s: float = 0.0,
               decisions: list[DecisionRecord] | None = None) -> str | None:
    """Avance le ballon d'un tick (mutation en place) : si un joueur le contrôle déjà, un
    adversaire à portée directe peut d'abord tenter un tacle (Phase 3, Tackling/Strength/
    Balance/Aggression ; au plus un par confrontation, v2-socle/03) ; sinon, après son temps de réception (`possession.reception_delay_s`, v2-socle/06)
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

        if ball.engaged_holder != holder.name:  # nouveau porteur : nouvelles confrontations
            ball.engaged, ball.engaged_holder = set(), holder.name
        ball.engaged = {n for n in ball.engaged
                        if any(p.name == n and p.position.distance_to(holder.position) < CONFRONTATION_END_M for p in players)}
        candidates = [p for p in players
                      if p.name not in ball.engaged and ball.tackle_ban_until_s.get(p.name, 0.0) <= now_s]
        challenger = _nearest_opponent_in_range(holder, candidates, TACKLE_RADIUS_M)
        if challenger is not None and should_attempt_tackle(player_attribute(challenger, "Aggression"), dt):
            ball.engaged.add(challenger.name)
            result = resolve_tackle(challenger, holder)
            if not result.won:
                ball.tackle_ban_until_s[challenger.name] = now_s + FAILED_TACKLE_RECOVERY_S
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
        if decisions is not None:
            target = getattr(action, "target", None)
            decisions.append(DecisionRecord(now_s / 60.0, holder.name, holder.team, action.kind,
                                            target.name if target is not None else None,
                                            getattr(action, "considered", 1), getattr(action, "best", True)))
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

    ball.engaged_holder = None  # ballon libre : les confrontations en cours sont finies (v2-socle/03)
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
    intentions: dict[str, Intention] | None = None,
    situations: SituationTracker | None = None,
    bloc: Bloc | None = None,
) -> PlayerState:
    """Un tick d'un joueur : son cerveau (`cerveau.think` : perception, interprétation, décision) donne son
    intention, puis l'exécution le déplace vers la cible, à l'intensité voulue (ADR 0001). `runs` : espaces visés
    par les coéquipiers du porteur (Off the Ball) ; `intentions` : si fourni, reçoit l'intention du joueur ; `bloc` :
    bloc de référence de chaque équipe (ticket v2-collectif/04), où il se replace et d'où partent ses appels."""
    perceived = situations.perceived(player, minute * 60.0) if situations is not None else None
    intention = think(player, ball, players or [], minute, runs, perceived, bloc)
    if intentions is not None:
        intentions[player.name] = intention
    return step(player, dt, intention.target, minute, intention.intensity)


def simulate_match(
    home_club: Club,
    away_club: Club,
    *,
    duration_minutes: float = 90.0,
    tick_seconds: float = 0.1,
    record_every: int = 10,
    observer: Callable[[float, list[PlayerState], BallState, str | None], None] | None = None,
) -> MatchTrace:
    """Simule un match de bout en bout (Phase 1 : déplacement seul, pas encore de score) et
    retourne sa trace complète (voir `trace.py`). `record_every` : un tick sur N est conservé dans
    la trace (sous-échantillonnage du rendu, le calcul physique tourne à `tick_seconds` quoi qu'il
    arrive). `observer` : appelé à chaque tick avec (instant en s, joueurs, ballon, équipe qui vient de
    marquer ou None) -- lecture seule, pour les mesures (`scripts/measure_v2.py`), sans effet sur le jeu."""
    home_lineup = pick_best_formation(home_club)
    away_lineup = pick_best_formation(away_club)

    home_positions = initial_positions(home_lineup, attacking_right=True)
    away_positions = initial_positions(away_lineup, attacking_right=False)

    players = _build_players(home_lineup, "home", home_positions) + _build_players(away_lineup, "away", away_positions)
    ball = BallState(position=Vec2(PITCH_LENGTH_M / 2.0, PITCH_WIDTH_M / 2.0), velocity=Vec2(0.0, 0.0))

    trace = MatchTrace(home=home_club.name, away=away_club.name, tick_seconds=tick_seconds * record_every)

    runs: dict[str, tuple[Vec2, float]] = {}  # espace visé par chaque joueur sans ballon (Off the Ball)
    intentions: dict[str, Intention] = {}  # intention de chaque joueur au dernier tick (ADR 0001)
    trace.reaction_delays_s = {p.name: reaction_delay_s(p) for p in players}
    situations = SituationTracker(delays_s=dict(trace.reaction_delays_s))  # situation de jeu (ticket v2-collectif/03)
    bloc = Bloc.from_players(players)  # bloc de référence dynamique (ticket v2-collectif/04)
    scoring_team = None
    n_ticks = int(duration_minutes * 60.0 / tick_seconds)
    for i in range(n_ticks):
        minute = i * tick_seconds / 60.0
        before = dict(situations.current)
        for team, situation in situations.update(i * tick_seconds, ball, players, scoring_team).items():
            if situation != before[team] or i == 0:
                trace.situations.append(SituationRecord(minute, team, situation))
        players = [_step_player(p, ball, tick_seconds, minute, players, runs, intentions, situations, bloc) for p in players]
        _resolve_player_collisions(players)
        scoring_team = _step_ball(ball, tick_seconds, players, i * tick_seconds, trace.decisions)
        if scoring_team is not None:
            trace.record_goal(scoring_team, minute)
        if observer is not None:
            observer(i * tick_seconds, players, ball, scoring_team)

        if i % record_every == 0:
            trace.record(
                minute,
                [PlayerSnapshot(name=p.name, team=p.team, poste=p.poste, position=p.position, intention=intentions.get(p.name))
                 for p in players],
                BallSnapshot(position=ball.position),
            )

    return trace

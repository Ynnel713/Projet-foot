"""Orchestration d'un match V2, Phase 1 (déplacement, docs/PLAN_V2.md) : place les 22 titulaires
réels d'un match sur un terrain 2D et les fait bouger -- vers leur position de formation, ou vers
le ballon s'ils en sont proches (IA placeholder volontairement simpliste, D-V08 ; la vraie prise
de décision vient en Phase 5+). Calcule une trace complète du match une fois (voir `trace.py`,
D-V04) ; un rendu, pas encore construit, la rejouera ensuite. Une seule fonction pour le mode
"regardé" et le mode "tout simuler sans regarder" (D-V05) : seul le rendu, en aval, est optionnel
-- rien ici ne dépend de si le match sera affiché."""

from __future__ import annotations

import math
import random
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
from v2engine.defense import DefensiveRoles
from v2engine.offside import HESITATION_S, OFFSIDE_OUT_S, offside_at_pass, sees_the_flag_probability
from v2engine.possession import (BALL_FRICTION_PER_S, BALL_STOPPED_MPS, MISS_RETRY_S, attempt_control, missed_control_velocity,
                                 pass_velocity, reception_delay_s)
from v2engine.shooting import attempt_shot
from v2engine.situation import SituationTracker
from v2engine.transition import TransitionPlay
from v2engine.trace import BallSnapshot, DecisionRecord, MatchTrace, OffsideEvent, PlayerSnapshot, SituationRecord

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
# Pas de calcul du produit (validé le 29/10/2026, ticket v2-collectif/25) : le même pour l'écran (`api/routers/v2.py`)
# et pour le banc (`scripts/measure_v2.py`), pour que les chiffres mesurés décrivent le match regardé.
TICK_SECONDS = 0.1
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


def _clear_offside(ball: BallState) -> None:
    """Efface le signalement de la passe en cours. Le flottement des défenseurs (`hesitation`) n'est PAS effacé :
    celui qui a levé la main attend le sifflet, ou la fin du flottement, même si la passe est morte entre-temps
    (« play the whistle », directive du 28/10/2026). Il expire tout seul à `now_s + HESITATION_S`."""
    ball.offside_watch = set()


def _award_offside_free_kick(ball: BallState, offender: PlayerState, players: list[PlayerState], now_s: float) -> None:
    """Coup franc indirect simplifié (ticket v2-collectif/23) : le ballon va au défenseur de champ le plus proche
    de l'endroit de la faute -- jamais au gardien, pour ne pas fabriquer une passe en retrait catastrophique. Le
    fautif est écarté de l'action `OFFSIDE_OUT_S` secondes, le temps qu'il recule (directive du propriétaire,
    28/10/2026). Pas de barrière ni de sortie de balle : le moteur n'a pas encore de coups de pied arrêtés."""
    defenders = [p for p in players if p.team != offender.team and p.poste != "GK"]
    if not defenders:  # effectif synthétique sans joueur de champ adverse : tout le monde peut tirer
        defenders = [p for p in players if p.team != offender.team]
    _clear_offside(ball)
    ball.hesitation = {}  # le sifflet tombe : plus personne n'attend, le jeu repart
    ball.receiver = None
    ball.readers = {}
    ball.velocity = Vec2(0.0, 0.0)
    ball.offside_out_until[offender.name] = now_s + OFFSIDE_OUT_S
    if not defenders:
        ball.holder = None
        return
    where = ball.position  # lieu de la faute, à quelques dizaines de centimètres du fautif
    taker = min(defenders, key=lambda p: p.position.distance_to(where))
    ball.position = taker.position
    ball.holder = taker.name
    ball.receiving = True
    ball.engaged, ball.engaged_holder = set(), taker.name
    ball.next_decision_s = now_s + reception_delay_s(taker, [p for p in players if p.team == offender.team])


def _step_ball(ball: BallState, dt: float, players: list[PlayerState], now_s: float = 0.0,
               decisions: list[DecisionRecord] | None = None,
               offsides: list[OffsideEvent] | None = None, modes: dict[str, str] | None = None) -> str | None:
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
        ball.released_by = None  # ballon tenu : plus de passe en cours (sa passe, s'il en fait une, le redéfinit)

        if ball.engaged_holder != holder.name:  # nouveau porteur : nouvelles confrontations
            ball.engaged, ball.engaged_holder = set(), holder.name
        # un défenseur battu resté à moins de 3 m retente une fois relevé (réserve A4 du ticket 25, traitée au ticket 08)
        ball.engaged = {n for n in ball.engaged if ball.tackle_ban_until_s.get(n, 0.0) > now_s
                        and any(p.name == n and p.position.distance_to(holder.position) < CONFRONTATION_END_M for p in players)}
        candidates = [p for p in players
                      if p.name not in ball.engaged and ball.tackle_ban_until_s.get(p.name, 0.0) <= now_s
                      and ball.offside_out_until.get(p.name, 0.0) <= now_s]  # le fautif recule, il ne défend pas
        challenger = _nearest_opponent_in_range(holder, candidates, TACKLE_RADIUS_M)
        if challenger is not None and should_attempt_tackle(player_attribute(challenger, "Aggression"), dt):
            ball.engaged.add(challenger.name)
            result = resolve_tackle(challenger, holder)
            if not result.won:
                ball.tackle_ban_until_s[challenger.name] = now_s + FAILED_TACKLE_RECOVERY_S
            if result.won:
                ball.holder = challenger.name
                ball.hesitation.pop(challenger.name, None)  # il a le ballon : il joue, il n'attend plus
                # nouveau porteur : contrôle et lève la tête avant de décider (v2-socle/06)
                ball.next_decision_s = now_s + reception_delay_s(challenger, [p for p in players if p.team != challenger.team])
                ball.receiving = True
                ball.velocity = Vec2(0.0, 0.0)
                _clear_offside(ball)  # nouveau porteur : la passe signalée est terminée
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
        action = choose_action(holder, players, goal, keeper, (modes or {}).get(holder.team))  # ticket v2-collectif/11
        if decisions is not None:
            target = getattr(action, "target", None)
            decisions.append(DecisionRecord(now_s / 60.0, holder.name, holder.team, action.kind,
                                            target.name if target is not None else None,
                                            getattr(action, "considered", 1), getattr(action, "best", True)))
        if action.kind == "shot":
            _clear_offside(ball)  # la passe signalée est morte : le ballon est tiré
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
            ball.released_by = holder.name
            ball.last_pass_team = holder.team
            ball.receiver = action.target.name
            opponents = [p for p in players if p.team != holder.team]
            ball.readers = pass_readers(holder.position, ball.velocity, action.target.position, opponents)
            # Hors-jeu (ticket v2-collectif/23) : jugement AU DÉPART, sur les positions réelles. Le signalement ne
            # vaut coup franc que si l'un de ces joueurs touche ensuite le ballon.
            mates = [p for p in players if p.team == holder.team and p.name != holder.name]
            _clear_offside(ball)
            flagged = offside_at_pass(holder.team, ball.position, mates, opponents)
            if flagged:
                ball.offside_watch = set(flagged)
                # « Play the whistle » : les défenseurs qui voient le drapeau lèvent la main et attendent (ils ne
                # s'arrêtent pas : le moteur ne siffle qu'au contact du ballon).
                for opponent in opponents:
                    if random.random() < sees_the_flag_probability(player_attribute(opponent, "Anticipation")):
                        ball.hesitation[opponent.name] = now_s + HESITATION_S
        else:
            ball.velocity = Vec2(0.0, 0.0)  # conduite : le ballon suit le porteur (voir `simulate_match`)
        return None

    ball.engaged_holder = None  # ballon libre : les confrontations en cours sont finies (v2-socle/03)
    start = ball.position
    ball.position = clamp_to_pitch(ball.position + ball.velocity * dt)
    ball.velocity = ball.velocity * (BALL_FRICTION_PER_S**dt)
    if ball.velocity.length() < BALL_STOPPED_MPS:
        ball.receiver = None  # passe morte : ballon libre pour tous, plus de receveur désigné
        ball.readers = {}  # plus de passe à couper (ticket v2-collectif/25)
        _clear_offside(ball)  # plus de passe en cours : plus de hors-jeu à siffler

    # Contact sur le trajet (ticket v2-collectif/25) : le ballon touche tout joueur qu'il frôle PENDANT le pas, pas
    # seulement au point d'arrivée ; le premier atteint tente le premier, quelle que soit son équipe.
    for _, _, player in _contacts(start, ball.position, dt, players, ball.released_by):
        if now_s < ball.offside_out_until.get(player.name, 0.0):
            continue  # écarté de l'action après un coup franc : il recule, il ne joue pas ce ballon
        if now_s < ball.control_ban_until_s.get(player.name, 0.0):
            continue  # il vient de rater son contrôle : le ballon lui échappe
        if player.name in ball.offside_watch:
            # Il touche le ballon en position de hors-jeu : coup franc indirect, même si le contrôle échoue
            # (« s'il le touche, c'est sifflé, point barre », directive du 28/10/2026).
            if offsides is not None:
                offsides.append(OffsideEvent(minute=now_s / 60.0, team=player.team, player=player.name,
                                             x=ball.position.x, y=ball.position.y))
            _award_offside_free_kick(ball, player, players, now_s)
            return None
        opponents = [p for p in players if p.team != player.team]
        ball.readers = {}  # la passe est finie, contrôlée ou non : personne ne court plus la couper
        ball.receiver = None
        ball.released_by = None  # quelqu'un d'autre a touché le ballon : le passeur peut de nouveau le jouer
        _clear_offside(ball)
        if attempt_control(player, ball.velocity, opponents):
            ball.holder = player.name
            ball.hesitation.pop(player.name, None)  # il a le ballon : il joue, il n'attend plus
            ball.position = player.position
            ball.next_decision_s = now_s + reception_delay_s(player, opponents)
            ball.receiving = True
            ball.velocity = Vec2(0.0, 0.0)
        else:
            # Contrôle raté : le ballon s'échappe vraiment (déviation, moitié de sa vitesse) et le même joueur ne peut
            # retenter qu'après `MISS_RETRY_S` ; il repart du bord du joueur, jamais superposé.
            ball.velocity = missed_control_velocity(player, ball.velocity, opponents)
            ball.position = clamp_to_pitch(player.position + ball.velocity.normalized() * CONTROL_RADIUS_M)
            ball.control_ban_until_s[player.name] = now_s + MISS_RETRY_S
        break
    return None


def _contacts(start: Vec2, end: Vec2, dt: float, players: list[PlayerState],
              released_by: str | None = None) -> list[tuple[float, float, PlayerState]]:
    """Joueurs que le ballon frôle à moins de `CONTROL_RADIUS_M` pendant le pas, de `start` à `end`, triés par
    instant de contact (0 = début du pas). Mouvement relatif : le joueur a lui aussi bougé pendant ce pas (sa
    position de début est estimée par sa vitesse). `released_by` : passeur du ballon, qui ne touche pas sa passe
    tant qu'elle s'éloigne de lui."""
    hits = []
    for player in players:
        r0 = start - (player.position - player.velocity * dt)  # ballon vu du joueur, en début de pas
        r1 = end - player.position  # et en fin de pas
        seg = r1 - r0
        length2 = seg.x * seg.x + seg.y * seg.y
        # Sa propre passe qui part de ses pieds : il ne la touche pas en la lâchant. « Elle s'éloigne » se juge sur la
        # distance, pas sur la direction de r0 : au départ r0 est presque nul et sa direction n'est que l'erreur
        # d'estimation de sa position de début de pas (ticket v2-collectif/26).
        if (player.name == released_by and length2 >= 1e-12 and r0.length() < CONTROL_RADIUS_M
                and r1.length() >= r0.length()):
            continue
        s = 0.0 if length2 < 1e-12 else min(1.0, max(0.0, -(r0.x * seg.x + r0.y * seg.y) / length2))
        closest = r0 + seg * s
        if closest.length() < CONTROL_RADIUS_M:
            # instant d'entrée dans le rayon (pas seulement du point le plus proche) : le premier atteint tente
            # le premier
            if length2 < 1e-12 or r0.length() < CONTROL_RADIUS_M:
                entry = 0.0
            else:
                back = math.sqrt(max(0.0, CONTROL_RADIUS_M**2 - closest.length() ** 2) / length2)
                entry = max(0.0, s - back)
            hits.append((entry, closest.length(), player))
    hits.sort(key=lambda hit: (hit[0], hit[1]))  # à égalité (déjà au contact), le plus proche d'abord
    return hits


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
    defense: DefensiveRoles | None = None,
    transition: TransitionPlay | None = None,
) -> PlayerState:
    """Un tick d'un joueur : son cerveau (`cerveau.think` : perception, interprétation, décision) donne son
    intention, puis l'exécution le déplace vers la cible, à l'intensité voulue (ADR 0001). `runs` : espaces visés
    par les coéquipiers du porteur (Off the Ball) ; `intentions` : si fourni, reçoit l'intention du joueur ; `bloc` :
    bloc de référence de chaque équipe (ticket v2-collectif/04), où il se replace et d'où partent ses appels ;
    `defense` : rôles défensifs de l'équipe sans ballon (ticket v2-collectif/07)."""
    perceived = situations.perceived(player, minute * 60.0) if situations is not None else None
    intention = think(player, ball, players or [], minute, runs, perceived, bloc, defense, transition)
    if intentions is not None:
        intentions[player.name] = intention
    return step(player, dt, intention.target, minute, intention.intensity, intention.target_velocity)


def simulate_match(
    home_club: Club,
    away_club: Club,
    *,
    duration_minutes: float = 90.0,
    tick_seconds: float = TICK_SECONDS,
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
    defense = DefensiveRoles()  # rôles défensifs (ticket v2-collectif/07)
    transition = TransitionPlay()  # contre-attaque ou conservation après une récupération (ticket v2-collectif/11)
    scoring_team = None
    n_ticks = int(duration_minutes * 60.0 / tick_seconds)
    for i in range(n_ticks):
        minute = i * tick_seconds / 60.0
        before = dict(situations.current)
        for team, situation in situations.update(i * tick_seconds, ball, players, scoring_team).items():
            if situation != before[team] or i == 0:
                trace.situations.append(SituationRecord(minute, team, situation))
        transition.update(situations, ball, players, i * tick_seconds)
        bloc.update(players, ball, i * tick_seconds)  # hauteur de ligne sans ballon (tickets 05 et 23)
        defense.update(players, ball, bloc, i * tick_seconds)
        players = [_step_player(p, ball, tick_seconds, minute, players, runs, intentions, situations, bloc, defense,
                                transition) for p in players]
        _resolve_player_collisions(players)
        scoring_team = _step_ball(ball, tick_seconds, players, i * tick_seconds, trace.decisions, trace.offsides,
                                  transition.mode)
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

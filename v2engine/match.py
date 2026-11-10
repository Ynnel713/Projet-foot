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
from dataclasses import dataclass, replace

from ligue1sim.clubs import Club
from ligue1sim.lineup import Lineup, pick_best_formation
from ligue1sim.pitch_geometry import GOAL_HEIGHT_M, GOAL_WIDTH_M

from v2engine.condition import effective_rating, intrinsic_rating
from v2engine.anticipation import pass_readers, reaction_delay_s
from v2engine.ball_state import BallState, ShotFlight
from v2engine.bloc import Bloc
from v2engine.danger import danger
from v2engine.duel import foul_severity, resolve_tackle, should_attempt_tackle
from v2engine.flux import ARBITRAGE, PERCEPTION, TIR, seed_streams
from v2engine.formation import initial_positions
from v2engine.geometry import PITCH_LENGTH_M, PITCH_WIDTH_M, Vec2, clamp_to_pitch, in_penalty_area
from v2engine.movement import PlayerState, step
from v2engine.cerveau import GOAL_CENTER_Y, OPPONENT_GOAL, Intention, think
from v2engine.decision import DECISION_INTERVAL_S, choose_action, dribble_lost, lost_carry_outcome
from v2engine.defense import DefensiveRoles
from v2engine.occasion import ChanceTracker
from v2engine.offside import HESITATION_S, OFFSIDE_OUT_S, offside_at_pass, sees_the_flag_probability
from v2engine.possession import (BALL_FRICTION_PER_S, BALL_STOPPED_MPS, MAX_PASS_MPS, MISS_RETRY_S, attempt_control, deflect,
                                 missed_control_velocity, pass_velocity, reception_delay_s)
from v2engine.added_time import GRACE_S, HARD_STOP_S, added_minutes, played_minute
from v2engine.roles import role_of
from v2engine.restart import (AERIAL_LANDING_M, AERIEN, CORNER, FREE_KICK, LONG_RESTART_M, PENALTY, PENALTY_CONVERSION, SOL,
                              award, exit_point, foul_restart, is_aerial, kickoff, restart_target)
from v2engine.shooting import (BLOCK_CHANCE, BLOCK_WIDTH_M, FLYING, HELD, OVER, PARRIED, SHANKED, SHOT_AIM_HEIGHT_M, WIDE,
                               block_reach_m, draw_shot_error, keeper_reach_m, neutral_xg, occasion_quality, parry_velocity,
                               post_shot_xg, save_outcome, shank_velocity, shot_probability)
from v2engine.situation import SituationTracker
from v2engine.transition import TransitionPlay
from v2engine.trace import (BallSnapshot, DecisionRecord, FoulEvent, MatchTrace, OffsideEvent, PlayerSnapshot, ShotEvent,
                            RestartEvent, SituationRecord)

# But adverse d'une équipe, par convention de ce moteur (voir `formation.initial_positions`,
# D-V03 : domicile attaque vers x=PITCH_LENGTH_M, extérieur vers x=0).
_OPPONENT_GOAL = OPPONENT_GOAL
# Vitesse d'un tir : celle de la passe la plus appuyée (pas de constante nouvelle), soit 30 m/s, 1 s pour 30 m.
SHOT_SPEED_MPS = MAX_PASS_MPS
# Tir en vol (ticket v2-realisme/05a, validé par délégation le 08/11/2026) : le ballon part vers son point d'arrivée
# (axe du but + écart d'exécution du 35b) et l'issue se lit sur son trajet : arrêt si le gardien l'atteint (05b), but
# entre les poteaux et sous la barre, sortie de but sinon. Seul chemin du tir en jeu depuis le 05h (plus de tirage du but
# au départ) ; le penalty garde sa conversion provisoire (`_play_penalty`).
# Origine d'un tir (ticket v2-collectif/28b, trace seulement, sans effet sur le jeu ; ordres de grandeur validés par
# délégation) : le tireur a « dribblé » s'il a porté le ballon plus de `DRIBBLE_ORIGIN_M` depuis son contrôle ; une
# passe reçue est « en profondeur » si elle a fait gagner au moins `DEEP_ORIGIN_M` vers le but, « en retrait » si elle
# en a fait perdre, « centre » si elle est arrivée en l'air.
DRIBBLE_ORIGIN_M = 5.0
DEEP_ORIGIN_M = 10.0

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
# Avantage (ticket v2-collectif/30, validé le 04/11/2026) : l'arbitre laisse jouer si l'équipe fautée garde le ballon
# là où il vaut au moins ADVANTAGE_DANGER_MIN sur la carte du danger (`danger.danger`, environ 60 m de son propre but
# et au-delà) ; il revient à la faute si elle le perd dans les ADVANTAGE_S secondes (« quelques secondes », loi 12 ;
# part réelle des avantages non trouvée).
ADVANTAGE_DANGER_MIN = 0.02
ADVANTAGE_S = 3.0
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
                pace=intrinsic_rating(player, "Pace"),
                acceleration=intrinsic_rating(player, "Acceleration"),
                stamina=intrinsic_rating(player, "Stamina"),
                home_target=pos,
                radius_m=PLAYER_RADIUS_M,
                attributes=player.attributes,
                role=role_of(player.poste, player.categorie),
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
            min_dist = a.radius_m + b.radius_m
            pa, pb = a.position, b.position
            # rejet rapide sans allouer : si un écart d'axe atteint déjà `min_dist`, la distance aussi (la quasi-totalité des paires)
            if abs(pb.x - pa.x) >= min_dist or abs(pb.y - pa.y) >= min_dist:
                continue
            delta = pb - pa
            dist = delta.length()
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


@dataclass
class LateSetPiece:
    """Fin de période (ticket v2-coach-et-gestion-de-match/03) : l'arbitre ne siffle pas tant qu'un corner, un coup
    franc ou un penalty accordé n'est pas joué ; l'action qui en découle va à son terme (prochain ballon mort ou
    changement de possession), `GRACE_S` au plus ; butoir `hard_stop_s` contre une chaîne de corners sans fin."""
    hard_stop_s: float = float("inf")
    team: str | None = None  # équipe du dernier coup de pied arrêté attendu
    grace_until_s: float | None = None

    def whistle(self, ball: BallState, players: list[PlayerState], now_s: float) -> bool:
        if now_s >= self.hard_stop_s:
            return True
        r = ball.restart
        if r is not None and r.kind in (CORNER, FREE_KICK, PENALTY):
            self.team, self.grace_until_s = r.team, None
            return False
        if self.team is None or r is not None:
            return True
        if self.grace_until_s is None:
            self.grace_until_s = now_s + GRACE_S
        holder_team = next((p.team for p in players if p.name == ball.holder), None)
        return now_s >= self.grace_until_s or holder_team not in (None, self.team)


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


def _whistle(ball: BallState, event: FoulEvent, players: list[PlayerState], now_s: float,
             fouls: list[FoulEvent] | None) -> None:
    """Faute sifflée (ticket v2-collectif/30) : ballon mort au lieu de la faute, coup franc ou penalty pour l'équipe
    fautée ; la passe, le tir ou la conduite en cours s'arrêtent."""
    victim_team = "away" if event.team == "home" else "home"
    ball.restart = foul_restart(victim_team, Vec2(event.x, event.y), players, now_s)
    ball.advantage, ball.set_piece = None, None
    ball.holder, ball.velocity, ball.shot_for, ball.dribble = None, Vec2(0.0, 0.0), None, None
    ball.shot_flight = None
    ball.receiver, ball.readers, ball.released_by, ball.plan = None, {}, None, None
    ball.mode, ball.aerial_left_m = SOL, 0.0
    ball.pass_from, ball.rebound, ball.shot_wide = None, False, False
    ball.hesitation = {}
    _clear_offside(ball)
    if fouls is not None:
        fouls.append(replace(event, outcome=ball.restart.kind))


def _settle_advantage(ball: BallState, fouls: list[FoulEvent] | None) -> None:
    """L'avantage est acquis : la faute n'est plus sifflée (elle reste tracée, pour les cartons du ticket 09a)."""
    if ball.advantage is not None and fouls is not None:
        fouls.append(ball.advantage[0])
    ball.advantage = None


def _foul(ball: BallState, fouler: PlayerState, victim: PlayerState, players: list[PlayerState], now_s: float,
          fouls: list[FoulEvent] | None) -> None:
    """Faute de `fouler` sur `victim`, porteur du ballon (ticket v2-collectif/30) : avantage si son équipe garde le
    ballon dans une zone qui vaut le coup (`ADVANTAGE_DANGER_MIN`), sinon coup de sifflet immédiat. Une faute pendant
    un avantage met fin au premier (acquis) et se juge à son tour."""
    _settle_advantage(ball, fouls)
    event = FoulEvent(now_s / 60.0, fouler.team, fouler.name, victim.name, victim.position.x, victim.position.y,
                      foul_severity(), "avantage")
    if danger(victim.position, victim.team) >= ADVANTAGE_DANGER_MIN:
        ball.advantage = (event, now_s + ADVANTAGE_S)
    else:
        _whistle(ball, event, players, now_s, fouls)


def _check_advantage(ball: BallState, players: list[PlayerState], now_s: float,
                     fouls: list[FoulEvent] | None) -> bool:
    """Avantage en cours : l'arbitre revient à la faute si l'équipe fautée a perdu le ballon (retourne True) ; il est
    acquis au bout de `ADVANTAGE_S`. Un ballon libre (passe, contrôle raté) n'est pas encore perdu."""
    if ball.advantage is None:
        return False
    event, until_s = ball.advantage
    holder = next((p for p in players if p.name == ball.holder), None)
    if holder is not None and holder.team == event.team:
        _whistle(ball, event, players, now_s, fouls)
        return True
    if now_s >= until_s:
        _settle_advantage(ball, fouls)
    return False


def _received_as(ball: BallState, player: PlayerState, aerial: bool) -> str:
    """Comment `player` reçoit le ballon qu'il touche (origine d'un tir, ticket v2-collectif/28b)."""
    if ball.rebound:
        return "rebond"
    if ball.pass_from is None or ball.last_pass_team != player.team:
        return "récupération"
    if aerial:
        return "centre"
    return _pass_kind(ball.pass_from, player)


def _pass_kind(start: Vec2, player: PlayerState) -> str:
    """Passe partie de `start` vers `player` : en retrait, en profondeur (gain d'au moins `DEEP_ORIGIN_M`) ou au sol."""
    gain = (player.position.x - start.x) * (1.0 if player.team == "home" else -1.0)
    return "passe en retrait" if gain < 0.0 else "passe en profondeur" if gain >= DEEP_ORIGIN_M else "passe au sol"


def _danger_origin(ball: BallState, player: PlayerState) -> str:
    """Comment est née la situation dangereuse de `player` (ticket v2-collectif/28c), vocabulaire du tir : porteur,
    l'origine de son tir s'il tirait ; coéquipier du porteur, la passe à venir ; ballon libre, la façon dont il le
    recevrait."""
    if ball.holder == player.name:
        return _shot_origin(ball, player, ball.set_piece is not None and ball.set_piece.taker == player.name)
    if ball.holder is not None:
        return _pass_kind(ball.position, player)
    return _received_as(ball, player, ball.mode == AERIEN)


def _shot_origin(ball: BallState, shooter: PlayerState, set_piece: bool) -> str:
    """Comment le tireur a eu le ballon : coup franc, récupération (tacle, ballon perdu adverse), dribble au-delà de
    `DRIBBLE_ORIGIN_M` depuis son contrôle, sinon la façon dont il l'a reçu (`_received_as`)."""
    if set_piece:
        return "coup franc"
    came = ball.came_from
    if came is None or came[0] != shooter.name:
        return "récupération"
    return "dribble" if shooter.position.distance_to(came[2]) > DRIBBLE_ORIGIN_M else came[1]


def _shank(ball: BallState, shooter: PlayerState, goal: Vec2, now_s: float) -> None:
    """Tir dévissé (ticket v2-collectif/35b) : ballon lent, très écarté, libre ; le tireur ne le rejoue pas aussitôt, et
    c'est lui le dernier toucheur si le ballon sort."""
    ball.holder = None
    ball.velocity = shank_velocity(shooter, goal, SHOT_SPEED_MPS)
    ball.position = clamp_to_pitch(shooter.position + ball.velocity.normalized() * CONTROL_RADIUS_M)
    ball.last_toucher = shooter.name
    ball.control_ban_until_s[shooter.name] = now_s + MISS_RETRY_S
    ball.released_by, ball.receiver, ball.readers, ball.last_pass_team = None, None, {}, shooter.team


def _keeper_reaches(ball: BallState, flight: ShotFlight, start: Vec2, end: Vec2, dt: float, players: list[PlayerState],
                    now_s: float, shots: list[ShotEvent] | None) -> bool:
    """Arrêt par portée (ticket v2-realisme/05b) : quand le ballon passe au plus près du gardien pendant ce pas, il
    l'atteint si l'écart tient dans sa portée à cet instant (`shooting.keeper_reach_m`). Jugé une fois par tir ; le temps
    de vol et l'écart sont tracés. Atteint : arrêt avec l'issue du ticket 28b. Retourne vrai si le gardien a touché."""
    done = flight.origin.distance_to(start)
    step = start.distance_to(end)
    if done + step < flight.keeper_at_m:
        return False
    share = min(1.0, max(0.0, (flight.keeper_at_m - done) / step)) if step > 1e-9 else 0.0
    elapsed = flight.elapsed_s + share * dt
    point = start + (end - start) * share
    flight.keeper_at_m = None
    keeper = _goalkeeper("away" if flight.team == "home" else "home", players)
    if keeper is None:
        return False
    gap = keeper.position.distance_to(point)
    rank = flight.rank if shots is not None else -1
    if rank >= 0:
        shots[rank] = replace(shots[rank], keeper_time_s=elapsed, keeper_gap_m=gap,
                              keeper_speed_mps=ball.velocity.length(),  # vitesse au début du pas (réserve A4, 05h)
                              post_shot_xg=post_shot_xg(gap, elapsed))  # ticket 06a
    if gap > keeper_reach_m(elapsed):
        return False
    goal = _OPPONENT_GOAL[flight.team]
    outcome = save_outcome(flight.chance, flight.origin, goal)
    if outcome == HELD and not in_penalty_area(flight.team, keeper.position):
        outcome = PARRIED  # hors de sa surface, jamais à la main (ticket v2-realisme/03d)
    if rank >= 0:
        shots[rank] = replace(shots[rank], outcome=outcome)
    ball.shot_flight = None
    _keeper_save(ball, keeper, outcome, flight.origin, goal, flight.team, players, now_s, point)
    return True


def _blocked(ball: BallState, flight: ShotFlight, start: Vec2, end: Vec2, dt: float, players: list[PlayerState],
             now_s: float, shots: list[ShotEvent] | None) -> bool:
    """Contre physique (ticket v2-realisme/05c) : le tir en vol touche le premier défenseur de champ adverse qu'il frôle à
    sa portée (`shooting.block_reach_m`, selon le temps écoulé depuis la frappe) ; chacun tente une fois par tir et contre
    avec la chance `BLOCK_CHANCE`. Contré : le ballon touche sa portée au point où il y entre (réserve A1 de l'expert, 05c)
    et repart de ce point, libre, dévié selon l'endroit de l'impact (`possession.deflect`, ticket 05d) ; point de contact
    et angle de sortie tracés. Retourne vrai si contré."""
    defenders = [p for p in players if p.team != flight.team and p.poste != "GK" and p.name not in flight.tried]
    for entry, gap, player in _contacts(start, end, dt, defenders, radius=BLOCK_WIDTH_M):
        if gap > block_reach_m(flight.elapsed_s + entry * dt):
            continue  # pas encore à sa portée : il peut encore le toucher plus loin
        flight.tried.add(player.name)
        if TIR.random() >= BLOCK_CHANCE:
            continue  # au contact, le ballon passe quand même
        reach = block_reach_m(flight.elapsed_s + entry * dt)
        seg = end - start
        shot = seg.normalized()
        # sa place à l'instant du contact (réserve A1 de l'expert, ticket 05d, repris au 05g) : il a bougé pendant le pas
        body = player.position - player.velocity * (dt * (1.0 - entry))
        along = (body.x - start.x) * shot.x + (body.y - start.y) * shot.y
        closest = start + shot * min(max(along, 0.0), seg.length())  # passage au plus près du corps
        back = math.sqrt(max(0.0, reach * reach - gap * gap))
        point = start + shot * max(0.0, min(max(along, 0.0), seg.length()) - back)  # entrée dans sa portée
        out = deflect(ball.velocity, closest, body, reach, TIR)
        exit_deg = math.degrees(math.acos(max(-1.0, min(1.0, out.normalized().x * shot.x + out.normalized().y * shot.y))))
        if shots is not None and flight.rank >= 0:
            shots[flight.rank] = replace(shots[flight.rank], outcome="contré", block_x=point.x, block_y=point.y,
                                         block_exit_deg=exit_deg, post_shot_xg=None)
        ball.velocity = out
        ball.position = clamp_to_pitch(point + out.normalized() * CONTROL_RADIUS_M)
        ball.shot_flight, ball.shot_wide, ball.rebound = None, False, True
        ball.last_toucher = player.name
        ball.control_ban_until_s[player.name] = now_s + MISS_RETRY_S
        ball.released_by, ball.receiver, ball.readers, ball.last_pass_team = None, None, {}, flight.team
        return True
    return False


def _keeper_save(ball: BallState, keeper: PlayerState, outcome: str, origin: Vec2, goal: Vec2, shooter_team: str,
                 players: list[PlayerState], now_s: float, at: Vec2) -> None:
    """Suite d'un arrêt (ticket v2-collectif/28b) au point de contact `at` (réserve A2 du 05b) : capté, le gardien a le
    ballon, amené à ce point (ponytail : pas de plongeon animé) ; repoussé ou claqué, le ballon repart de ce point, libre."""
    if outcome == HELD:
        keeper.position = clamp_to_pitch(at)
        ball.holder = keeper.name
        ball.next_decision_s = now_s + reception_delay_s(keeper, [p for p in players if p.team == shooter_team])
        ball.receiving = True
        ball.position = keeper.position
        ball.velocity = Vec2(0.0, 0.0)
        return
    ball.holder = None
    ball.velocity = parry_velocity(origin, goal, at, outcome, SHOT_SPEED_MPS)
    ball.position = clamp_to_pitch(at + ball.velocity.normalized() * CONTROL_RADIUS_M)
    ball.last_toucher = keeper.name
    ball.control_ban_until_s[keeper.name] = now_s + MISS_RETRY_S
    ball.released_by, ball.receiver, ball.readers, ball.last_pass_team = None, None, {}, shooter_team
    ball.rebound = True


def _play_penalty(ball: BallState, taker: PlayerState, players: list[PlayerState],
                  shots: list[ShotEvent] | None = None, minute: float = 0.0) -> None:
    """Penalty provisoire (ticket v2-collectif/30, remplacé par `v2-attributs-restants/02a`) : conversion neutre
    `PENALTY_CONVERSION` ; raté, le gardien garde le ballon (ponytail : ni poteau ni ballon repoussé avant le 02a)."""
    ball.last_toucher = taker.name
    goal = _OPPONENT_GOAL[taker.team]
    scored = TIR.random() < PENALTY_CONVERSION
    if shots is not None:
        shots.append(ShotEvent(minute, taker.team, taker.name, taker.position.x, taker.position.y,
                               PENALTY_CONVERSION, "but" if scored else HELD, "penalty"))
    if scored:
        ball.velocity = (goal - ball.position).normalized() * SHOT_SPEED_MPS
        ball.shot_for = taker.team
        return
    keeper = _goalkeeper("away" if taker.team == "home" else "home", players)
    if keeper is not None:
        ball.holder, ball.position = keeper.name, keeper.position
        ball.receiving = True


def _play_restart(ball: BallState, players: list[PlayerState], now_s: float,
                  restarts: list[RestartEvent] | None, shots: list[ShotEvent] | None = None) -> None:
    """Ballon mort (ticket v2-collectif/29) : posé au point de remise jusqu'à la reprise, puis joué par le preneur, par
    une passe vers le receveur de `restart.restart_target`. Pas de hors-jeu sur une remise en jeu. Coup franc (ticket
    v2-collectif/30) : le preneur a le ballon et décide aussitôt comme dans le jeu, frapper ou passer (hors-jeu
    compris) ; penalty provisoire : `_play_penalty`."""
    r = ball.restart
    ball.position, ball.velocity = r.spot, Vec2(0.0, 0.0)
    if now_s < r.until_s:
        return
    ball.restart = None
    taker = next((p for p in players if p.name == r.taker), None)
    if taker is None:
        return  # effectif synthétique sans preneur : ballon libre au point de remise
    taker.position = r.spot  # ponytail : un preneur en retard est posé au point ; à animer si la relecture le montre
    if r.kind == PENALTY:
        if restarts is not None:
            restarts.append(RestartEvent(r.minute, r.kind, r.team, r.spot.x, r.spot.y, r.last_toucher,
                                         now_s - r.minute * 60.0, False, None, True))
        _play_penalty(ball, taker, players, shots, now_s / 60.0)
        return
    if r.kind == FREE_KICK:  # événement tracé à sa décision, quand on sait s'il frappe
        ball.holder, ball.set_piece = taker.name, r
        ball.receiving, ball.next_decision_s = False, now_s
        return
    target = restart_target(taker, r.kind, players)
    if restarts is not None:
        restarts.append(RestartEvent(r.minute, r.kind, r.team, r.spot.x, r.spot.y, r.last_toucher,
                                     now_s - r.minute * 60.0, target is not None
                                     and taker.position.distance_to(target.position) > LONG_RESTART_M,
                                     target.name if target is not None else None))
    opponents = [p for p in players if p.team != taker.team]
    if target is None:  # personne à servir : il garde le ballon et joue
        ball.holder = taker.name
        ball.receiving = True
        ball.next_decision_s = now_s + reception_delay_s(taker, opponents)
        return
    ball.velocity = pass_velocity(taker, target, opponents)
    ball.pass_from, ball.rebound, ball.shot_wide = taker.position, False, False
    ball.last_toucher = ball.released_by = taker.name
    ball.last_pass_team = taker.team
    ball.receiver = target.name
    ball.plan = None
    _clear_offside(ball)
    if is_aerial(r.kind, taker, target):  # ballon en l'air : on ne le touche qu'à son point de chute
        ball.mode, ball.readers = AERIEN, {}
        ball.aerial_left_m = taker.position.distance_to(target.position) - AERIAL_LANDING_M
    else:
        ball.readers = pass_readers(taker.position, ball.velocity, target.position, opponents)


def _step_ball(ball: BallState, dt: float, players: list[PlayerState], now_s: float = 0.0,
               decisions: list[DecisionRecord] | None = None,
               offsides: list[OffsideEvent] | None = None, modes: dict[str, str] | None = None,
               restarts: list[RestartEvent] | None = None, fouls: list[FoulEvent] | None = None,
               shots: list[ShotEvent] | None = None) -> str | None:
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
    ("home"/"away"), ou `None`. Ballon sorti : remise en jeu (ticket v2-collectif/29). Fautes et avantage : ticket
    v2-collectif/30."""
    if _check_advantage(ball, players, now_s, fouls):
        return None
    if ball.restart is not None:
        _play_restart(ball, players, now_s, restarts, shots)
        return None
    if ball.holder is not None:
        holder = next((p for p in players if p.name == ball.holder), None)
        if holder is None:
            ball.holder = None  # détenteur introuvable (ne devrait pas arriver hors test) -- ballon relâché
            return None
        ball.position = holder.position
        ball.last_toucher = holder.name
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
        if challenger is not None and should_attempt_tackle(effective_rating(challenger, "Aggression"), dt):
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
            elif getattr(result, "foul", False):  # faute : avantage ou coup de sifflet (ticket v2-collectif/30)
                _foul(ball, challenger, holder, players, now_s, fouls)
            # Tacle raté sans faute, ou avantage : le porteur garde le ballon ce tick
            return None

        if now_s < ball.next_decision_s:
            return None  # conduite en cours : le porteur garde le ballon jusqu'à sa prochaine réévaluation
        ball.next_decision_s = now_s + DECISION_INTERVAL_S
        ball.receiving = False

        opponent_team = "away" if holder.team == "home" else "home"
        goal = _OPPONENT_GOAL[holder.team]
        keeper = _goalkeeper(opponent_team, players)
        # plan de passe (ticket v2-collectif/14) : lu par son receveur à sa première décision, effacé à toute décision
        planned = ball.plan[1] if ball.plan is not None and ball.plan[0] == holder.name else None
        ball.plan = None
        # erreur sur les directions de conduite gardée pendant sa possession (ticket 33, A4) ; nouveau porteur, nouvelle
        # idée de l'espace -- ponytail: un joueur qui reperd puis reprend le ballon sans autre porteur entre-temps la garde
        if ball.felt is None or ball.felt[0] != holder.name:
            ball.felt = (holder.name, {})
        # coup franc (ticket v2-collectif/30) : il frappe ou passe, jamais ne conduit
        set_piece = ball.set_piece is not None and ball.set_piece.taker == holder.name
        ball.pass_from, ball.rebound, ball.shot_wide = None, False, False  # nouvelle action : l'origine d'un tir à venir repart de lui
        action = choose_action(holder, players, goal, keeper, (modes or {}).get(holder.team), planned,  # ticket 11
                               ball.felt[1], set_piece)
        if set_piece:
            r, ball.set_piece = ball.set_piece, None
            if restarts is not None:
                target = getattr(action, "target", None)
                restarts.append(RestartEvent(r.minute, r.kind, r.team, r.spot.x, r.spot.y, r.last_toucher,
                                             now_s - r.minute * 60.0, target is not None
                                             and holder.position.distance_to(target.position) > LONG_RESTART_M,
                                             target.name if target is not None else None, action.kind == "shot"))
        if decisions is not None:
            target = getattr(action, "target", None)
            decisions.append(DecisionRecord(now_s / 60.0, holder.name, holder.team, action.kind,
                                            target.name if target is not None else None,
                                            getattr(action, "considered", 1), getattr(action, "best", True),
                                            getattr(action, "best_kind", None), getattr(action, "gap", 0.0)))
        point = getattr(action, "point", None)
        ball.dribble = (holder.name, point) if action.kind == "dribble" and point is not None else None
        rivals = [p for p in players if p.team != holder.team]
        if action.kind == "dribble" and dribble_lost(holder, rivals):
            # Ballon perdu en conduite (ticket v2-realisme/04a), même risque que celui de l'évaluation. Où il va (ticket
            # 04b) : à l'adversaire au contact, comme un tacle gagné, ou libre devant le porteur (touche trop longue).
            ball.dribble = None
            heading = (point - holder.position) if point is not None else holder.velocity
            if heading.length() < 1e-9:
                heading = goal - holder.position
            taker, ball.velocity = lost_carry_outcome(holder, rivals, heading)
            if taker is not None:
                ball.holder = taker.name
                ball.hesitation.pop(taker.name, None)
                ball.next_decision_s = now_s + reception_delay_s(taker, [p for p in players if p.team != taker.team])
                ball.receiving = True
                ball.velocity = Vec2(0.0, 0.0)
                _clear_offside(ball)
                return None
            ball.holder = None
            ball.position = clamp_to_pitch(holder.position + ball.velocity.normalized() * CONTROL_RADIUS_M)
            ball.control_ban_until_s[holder.name] = now_s + MISS_RETRY_S
            ball.last_toucher, ball.released_by, ball.receiver, ball.readers = holder.name, None, None, {}
            return None
        if action.kind == "shot":
            _settle_advantage(ball, fouls)  # un tir réalise l'avantage (loi 12 ; réserve A1 de l'expert, ticket 30)
            _clear_offside(ball)  # la passe signalée est morte : le ballon est tiré
            opponents = [p for p in players if p.team != holder.team]
            shot_at = holder.position

            def record(outcome: str) -> None:  # tir tracé avec son issue (ticket v2-collectif/28b)
                if shots is not None:
                    shots.append(ShotEvent(now_s / 60.0, holder.team, holder.name, shot_at.x, shot_at.y,
                                           occasion_quality(holder, goal, keeper, opponents), outcome,
                                           _shot_origin(ball, holder, set_piece),
                                           xg=neutral_xg(holder, goal, keeper, opponents),
                                           post_shot_xg=0.0 if outcome == SHANKED else None))
            error = draw_shot_error(holder, goal, opponents)
            if error is None:
                record(SHANKED)  # dévissé (ticket v2-collectif/35b)
                _shank(ball, holder, goal, now_s)
                return None
            # Tir en vol (tickets v2-realisme/05a et 05b, allumé au 05h) : aucun tirage du but ni du contre ici, l'issue se
            # lit sur son trajet : contre si un défenseur le touche (05c), arrêt si le gardien l'atteint, but ou sortie de
            # but sur la ligne.
            record(FLYING)
            axis = (goal - holder.position).normalized()
            c, s = math.cos(error[0]), math.sin(error[0])
            heading = Vec2(axis.x * c - axis.y * s, axis.x * s + axis.y * c)
            ball.holder = None
            ball.velocity = heading * SHOT_SPEED_MPS
            flight = ShotFlight(holder.team, shot_at, math.tan(error[1]), len(shots) - 1 if shots is not None else -1,
                                shot_probability(holder, goal, keeper, opponents))
            # Point d'arrivée sur la ligne et passage au plus près du gardien (ticket v2-realisme/05b) : il ne va que sur
            # un tir qui finira dans le cadre.
            to_line = (goal.x - shot_at.x) / heading.x if abs(heading.x) > 1e-9 else -1.0
            arrival = shot_at + heading * to_line
            flight.on_target = (to_line > 0.0 and abs(arrival.y - GOAL_CENTER_Y) < GOAL_WIDTH_M / 2.0
                                and SHOT_AIM_HEIGHT_M + to_line * flight.slope < GOAL_HEIGHT_M)
            if keeper is not None:
                flight.keeper_from = keeper.position
            if shots is not None and (not flight.on_target or keeper is None):  # xG après frappe (06a) : hors cadre 0
                shots[-1] = replace(shots[-1], post_shot_xg=1.0 if flight.on_target else 0.0)
            if flight.on_target and keeper is not None:
                along = (keeper.position.x - shot_at.x) * heading.x + (keeper.position.y - shot_at.y) * heading.y
                flight.keeper_at_m = min(max(along, 0.0), to_line)
            ball.shot_flight = flight
            ball.shot_wide = not flight.on_target  # hors du cadre (ticket v2-realisme/03k)
            ball.last_toucher = ball.released_by = holder.name
            ball.receiver, ball.readers, ball.last_pass_team = None, {}, holder.team
            return None

        if action.kind == "pass":
            ball.velocity = pass_velocity(holder, action.target, [p for p in players if p.team != holder.team])
            ball.pass_from = holder.position
            ball.holder = None
            ball.released_by = holder.name
            ball.last_pass_team = holder.team
            ball.receiver = action.target.name
            follow = getattr(action, "follow", None)
            ball.plan = (action.target.name, follow, now_s) if follow is not None else None
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
                    if PERCEPTION.random() < sees_the_flag_probability(effective_rating(opponent, "Anticipation")):
                        ball.hesitation[opponent.name] = now_s + HESITATION_S
        else:
            ball.velocity = Vec2(0.0, 0.0)  # conduite : le ballon suit le porteur (voir `simulate_match`)
        return None

    ball.engaged_holder = None  # ballon libre : les confrontations en cours sont finies (v2-socle/03)
    if ball.shot_for is not None:
        # tir cadré en route : personne ne le touche (le gardien est battu d'avance), il avance en ligne droite jusqu'à
        # la ligne de but, où le but est compté et l'équipe qui a encaissé engage (ticket v2-collectif/29)
        if ball.position.distance_to(_OPPONENT_GOAL[ball.shot_for]) > ball.velocity.length() * dt:
            ball.position = ball.position + ball.velocity * dt
            return None
        team, ball.shot_for = ball.shot_for, None
        _settle_advantage(ball, fouls)  # but pendant l'avantage : acquis
        ball.velocity = Vec2(0.0, 0.0)
        ball.restart = kickoff("away" if team == "home" else "home", players, now_s)
        return team
    start = ball.position
    end = ball.position + ball.velocity * dt
    out = exit_point(start, end)
    flight = ball.shot_flight
    # ponytail : contre jugé avant le gardien dans un même pas (3 m à 30 m/s) ; un défenseur derrière le gardien est rare
    if flight is not None and _blocked(ball, flight, start, end, dt, players, now_s, shots):
        return None
    if flight is not None and flight.keeper_at_m is not None and _keeper_reaches(ball, flight, start, end, dt, players,
                                                                                     now_s, shots):
        return None
    if flight is not None and out is not None:
        # Tir en vol sur la ligne (ticket v2-realisme/05a) : but s'il passe entre les poteaux et sous la barre, à la
        # hauteur prise depuis le départ (visée + pente) ; sinon il sort comme tout ballon (sortie de but).
        team, origin, slope, rank = flight.team, flight.origin, flight.slope, flight.rank
        ball.shot_flight = None
        line, point = out
        height = SHOT_AIM_HEIGHT_M + origin.distance_to(point) * slope
        between = line == "but" and abs(point.y - GOAL_CENTER_Y) < GOAL_WIDTH_M / 2.0
        scored = between and height < GOAL_HEIGHT_M
        if shots is not None and rank >= 0:
            shots[rank] = replace(shots[rank], outcome="but" if scored else OVER if between else WIDE)
        if scored:
            _settle_advantage(ball, fouls)
            ball.position, ball.velocity = point, Vec2(0.0, 0.0)
            ball.restart = kickoff("away" if team == "home" else "home", players, now_s)
            return team
    if out is not None:  # ballon sorti (ticket v2-collectif/29) : mort, remise en jeu pour l'adversaire du dernier toucheur
        line, point = out
        toucher = next((p for p in players if p.name == ball.last_toucher), None)
        if ball.advantage is not None and toucher is not None and toucher.team != ball.advantage[0].team:
            _whistle(ball, ball.advantage[0], players, now_s, fouls)  # sortie perdue pendant l'avantage : on y revient
            return None
        _settle_advantage(ball, fouls)
        ball.restart = award(line, point, toucher, players, now_s)
        ball.position, ball.velocity = point, Vec2(0.0, 0.0)
        ball.receiver, ball.readers, ball.released_by, ball.plan = None, {}, None, None
        ball.mode, ball.aerial_left_m = SOL, 0.0
        ball.pass_from, ball.rebound, ball.shot_wide = None, False, False
        _clear_offside(ball)
        return None
    ball.position = end
    ball.velocity = ball.velocity * (BALL_FRICTION_PER_S**dt)
    if flight is not None:
        flight.elapsed_s += dt
    if ball.aerial_left_m > 0.0:  # ballon en l'air (ticket v2-collectif/29) : il retombe à son point de chute
        ball.aerial_left_m -= start.distance_to(end)
    if ball.velocity.length() < BALL_STOPPED_MPS:
        ball.receiver = None  # passe morte : ballon libre pour tous, plus de receveur désigné
        ball.readers = {}  # plus de passe à couper (ticket v2-collectif/25)
        _clear_offside(ball)  # plus de passe en cours : plus de hors-jeu à siffler
        ball.aerial_left_m = 0.0
    if ball.aerial_left_m > 0.0:
        return None  # en l'air : personne ne le touche sur son trajet
    if ball.shot_flight is not None:
        if ball.velocity.length() >= BALL_STOPPED_MPS:
            return None  # tir en vol : personne ne le touche avant la ligne (05b et 05c)
        # ponytail : tir mort avant la ligne (60 m de course à 30 m/s), rendu au jeu, issue « en vol » ; plus un tir à côté
        # en vol non plus (réserve A5 de l'expert, 05h)
        ball.shot_flight, ball.shot_wide = None, False
    aerial = ball.mode == AERIEN  # ballon qui retombe d'une passe en l'air : un centre, pour l'origine d'un tir
    ball.mode = SOL

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
        ball.last_toucher = player.name  # contrôlé ou non, il l'a touché (ticket v2-collectif/29)
        received = _received_as(ball, player, aerial)
        ball.pass_from, ball.rebound, ball.shot_wide = None, False, False
        opponents = [p for p in players if p.team != player.team]
        ball.readers = {}  # la passe est finie, contrôlée ou non : personne ne court plus la couper
        ball.receiver = None
        ball.released_by = None  # quelqu'un d'autre a touché le ballon : le passeur peut de nouveau le jouer
        _clear_offside(ball)
        if attempt_control(player, ball.velocity, opponents):
            ball.holder = player.name
            ball.came_from = (player.name, received, player.position)
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
              released_by: str | None = None, radius: float = CONTROL_RADIUS_M) -> list[tuple[float, float, PlayerState]]:
    """Joueurs que le ballon frôle à moins de `radius` (par défaut `CONTROL_RADIUS_M`) pendant le pas, de `start` à `end`, triés par
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
        if closest.length() < radius:
            # instant d'entrée dans le rayon (pas seulement du point le plus proche) : le premier atteint tente
            # le premier
            if length2 < 1e-12 or r0.length() < radius:
                entry = 0.0
            else:
                back = math.sqrt(max(0.0, radius**2 - closest.length() ** 2) / length2)
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
    played_minute: float | None = None,
) -> PlayerState:
    """Un tick d'un joueur : son cerveau (`cerveau.think` : perception, interprétation, décision) donne son
    intention, puis l'exécution le déplace vers la cible, à l'intensité voulue (ADR 0001). `runs` : espaces visés
    par les coéquipiers du porteur (Off the Ball) ; `intentions` : si fourni, reçoit l'intention du joueur ; `bloc` :
    bloc de référence de chaque équipe (ticket v2-collectif/04), où il se replace et d'où partent ses appels ;
    `defense` : rôles défensifs de l'équipe sans ballon (ticket v2-collectif/07)."""
    perceived = situations.perceived(player, minute * 60.0) if situations is not None else None
    previous = intentions.get(player.name) if intentions is not None else None  # réaction à la perte (ticket 10)
    intention = think(player, ball, players or [], minute, runs, perceived, bloc, defense, transition, previous)
    if intentions is not None:
        intentions[player.name] = intention
    # Fatigue sur le temps de jeu (`played_minute`, temps additionnel de la 1re période retiré en 2e) et non sur
    # l'horloge du moteur (ticket v2-coach-et-gestion-de-match/03, réserve A1 du passage 2 de l'expert).
    return step(player, dt, intention.target, minute if played_minute is None else played_minute, intention.intensity,
                intention.target_velocity)


def simulate_match(
    home_club: Club,
    away_club: Club,
    *,
    duration_minutes: float = 90.0,
    tick_seconds: float = TICK_SECONDS,
    record_every: int = 10,
    observer: Callable[[float, list[PlayerState], BallState, str | None], None] | None = None,
    on_start: Callable[[MatchTrace], None] | None = None,
) -> MatchTrace:
    """Simule un match de bout en bout (Phase 1 : déplacement seul, pas encore de score) et
    retourne sa trace complète (voir `trace.py`). `record_every` : un tick sur N est conservé dans
    la trace (sous-échantillonnage du rendu, le calcul physique tourne à `tick_seconds` quoi qu'il
    arrive). `observer` : appelé à chaque tick avec (instant en s, joueurs, ballon, équipe qui vient de
    marquer ou None) -- lecture seule, pour les mesures (`scripts/measure_v2.py`), sans effet sur le jeu. `on_start` :
    reçoit la trace dès sa création, avant le premier tick : l'API la lit pendant qu'elle se remplit (rejeu en direct)."""
    # Flux aléatoires par sous-système (ticket v2-realisme/01a, D-V13) : un seul tirage du module `random` donne
    # la base du match ; chaque sous-système en dérive sa propre suite (01b).
    seed_streams(random.getrandbits(64))
    home_lineup = pick_best_formation(home_club)
    away_lineup = pick_best_formation(away_club)

    home_positions = initial_positions(home_lineup, attacking_right=True)
    away_positions = initial_positions(away_lineup, attacking_right=False)

    players = _build_players(home_lineup, "home", home_positions) + _build_players(away_lineup, "away", away_positions)
    ball = BallState(position=Vec2(PITCH_LENGTH_M / 2.0, PITCH_WIDTH_M / 2.0), velocity=Vec2(0.0, 0.0))
    # Coup d'envoi du match (ticket v2-collectif/29) par l'équipe tirée au sort (Loi 8) ; l'autre engage la 2e période
    # (ticket v2-coach-et-gestion-de-match/07).
    first = "home" if ARBITRAGE.random() < 0.5 else "away"
    ball.restart = kickoff(first, players, 0.0, dead_s=0.0)

    trace = MatchTrace(home=home_club.name, away=away_club.name, tick_seconds=tick_seconds * record_every)

    runs: dict[str, tuple[Vec2, float]] = {}  # espace visé par chaque joueur sans ballon (Off the Ball)
    intentions: dict[str, Intention] = {}  # intention de chaque joueur au dernier tick (ADR 0001)
    trace.reaction_delays_s = {p.name: reaction_delay_s(p) for p in players}
    if on_start is not None:
        on_start(trace)
    situations = SituationTracker(delays_s=dict(trace.reaction_delays_s))  # situation de jeu (ticket v2-collectif/03)
    bloc = Bloc.from_players(players)  # bloc de référence dynamique (ticket v2-collectif/04)
    defense = DefensiveRoles()  # rôles défensifs (ticket v2-collectif/07)
    transition = TransitionPlay()  # contre-attaque ou conservation après une récupération (ticket v2-collectif/11)
    chances = ChanceTracker(trace.chances)  # danger et grosses occasions, lecture seule (ticket v2-collectif/28c)
    scoring_team = None
    n_ticks = int(duration_minutes * 60.0 / tick_seconds)
    half_tick = n_ticks // 2
    # Temps additionnel (ticket v2-coach-et-gestion-de-match/03) : annoncé à la fin du temps réglementaire de chaque
    # période, puis la période se termine à la fin annoncée, sauf coup de pied arrêté déjà accordé (voir `LateSetPiece.whistle`).
    period, period_start_tick, regular_end_tick = 1, 0, half_tick
    end_tick: int | None = None
    last_situation: dict[str, str] = {}  # dernière situation tracée par équipe
    late = LateSetPiece()
    i = 0
    while True:
        minute = i * tick_seconds / 60.0
        if end_tick is None and i >= regular_end_tick:
            start_min = period_start_tick * tick_seconds / 60.0
            n = added_minutes(period, duration_minutes / 2.0,
                              sum(1 for g in trace.goals if g.minute >= start_min),
                              sum(1 for f in trace.fouls if f.outcome == PENALTY and f.minute >= start_min),
                              f"{home_club.name}|{away_club.name}",
                              fouls=sum(1 for f in trace.fouls if f.minute >= start_min),
                              restarts=sum(1 for r in trace.restarts if r.minute >= start_min))
            trace.added_minutes.append(n)
            end_tick = i + round(n * 60.0 / tick_seconds)
            late = LateSetPiece(hard_stop_s=end_tick * tick_seconds + HARD_STOP_S)
        if end_tick is not None and i >= end_tick and late.whistle(ball, players, i * tick_seconds):
            chances.close_all(minute)
            if period == 2:
                break
            period, period_start_tick, end_tick = 2, i, None
            regular_end_tick = i + (n_ticks - half_tick)
        if i == period_start_tick and period == 2:
            # Mi-temps (ticket v2-coach-et-gestion-de-match/07) : l'action en cours s'arrête (passe ou tir en vol,
            # hors-jeu signalé, remise en attente), chacun reprend sa place de départ et l'autre équipe engage.
            # Même sens de jeu qu'en 1re période : l'écran retourne la scène (terrain symétrique, rien n'y dépend du
            # côté). Le replacement est immédiat : la pause n'est pas jouée, l'écran la cache derrière un bandeau.
            for p in players:
                p.position, p.velocity = p.home_target, Vec2(0.0, 0.0)
            ball = BallState(position=Vec2(PITCH_LENGTH_M / 2.0, PITCH_WIDTH_M / 2.0), velocity=Vec2(0.0, 0.0))
            ball.restart = kickoff("away" if first == "home" else "home", players, i * tick_seconds, dead_s=0.0)
            situations = SituationTracker(delays_s=dict(trace.reaction_delays_s))
            bloc, defense, transition = Bloc.from_players(players), DefensiveRoles(), TransitionPlay()
            runs.clear()
            intentions.clear()
            scoring_team = None
            trace.second_half_start_minute = minute
        # Trace des seuls changements, d'une période à l'autre aussi (le suivi est remis à neuf à la mi-temps).
        for team, situation in situations.update(i * tick_seconds, ball, players, scoring_team).items():
            if situation != last_situation.get(team):
                last_situation[team] = situation
                trace.situations.append(SituationRecord(minute, team, situation))
        transition.update(situations, ball, players, i * tick_seconds)
        bloc.update(players, ball, i * tick_seconds)  # hauteur de ligne sans ballon (tickets 05 et 23)
        defense.update(players, ball, bloc, i * tick_seconds, situations.current)  # contre-pressing (ticket 10)
        played = played_minute(minute, trace.second_half_start_minute, half_tick * tick_seconds / 60.0)
        players = [_step_player(p, ball, tick_seconds, minute, players, runs, intentions, situations, bloc, defense,
                                transition, played_minute=played) for p in players]
        _resolve_player_collisions(players)
        scoring_team = _step_ball(ball, tick_seconds, players, i * tick_seconds, trace.decisions, trace.offsides,
                                  transition.mode, trace.restarts, trace.fouls,
                                  trace.shots)
        if scoring_team is not None:
            trace.record_goal(scoring_team, minute)
        chances.update(minute, ball, players, trace.shots, lambda p: _danger_origin(ball, p))
        if observer is not None:
            observer(i * tick_seconds, players, ball, scoring_team)

        if i % record_every == 0:
            trace.record(
                minute,
                [PlayerSnapshot(name=p.name, team=p.team, poste=p.poste, position=p.position,
                                intention=intentions.get(p.name), role=p.role)
                 for p in players],
                BallSnapshot(position=ball.position, holder=ball.holder, mode=ball.mode, dead=ball.restart is not None),
            )
        i += 1

    return trace

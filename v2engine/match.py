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
from v2engine.formation import initial_positions
from v2engine.geometry import PITCH_LENGTH_M, PITCH_WIDTH_M, Vec2, clamp_to_pitch
from v2engine.movement import PlayerState, step
from v2engine.trace import BallSnapshot, MatchTrace, PlayerSnapshot

BALL_RADIUS_M = 0.11
PLAYER_RADIUS_M = 0.3
# Distance en dessous de laquelle un joueur va vers le ballon plutôt que vers sa position de
# formation -- IA placeholder (D-V08), pas une vraie prise de décision.
CHASE_RADIUS_M = 15.0
# ponytail : décroissance exponentielle simple (par seconde), pas un vrai coefficient de
# frottement calibré -- à affiner si le rendu le justifie.
BALL_FRICTION_PER_S = 0.6


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


def _step_ball(position: Vec2, velocity: Vec2, dt: float, players: list[PlayerState]) -> tuple[Vec2, Vec2]:
    """Avance le ballon et le fait rebondir sur tout joueur qu'il touche -- interaction passive
    (le ballon prend la vitesse du joueur traversé), pas encore un vrai contrôle volontaire
    (Phase 2, First Touch/Passing)."""
    new_position = clamp_to_pitch(position + velocity * dt)
    new_velocity = velocity * (BALL_FRICTION_PER_S**dt)
    for player in players:
        if new_position.distance_to(player.position) < BALL_RADIUS_M + player.radius_m:
            away = new_position - player.position
            # Ballon et joueur exactement superposés (direction de séparation indéfinie) : repart
            # dans le sens de course du joueur, ou une direction fixe à défaut de vitesse.
            direction = away.normalized() if away.length() > 1e-9 else (
                player.velocity.normalized() if player.velocity.length() > 1e-9 else Vec2(1.0, 0.0)
            )
            new_velocity = player.velocity if player.velocity.length() > 0.1 else direction * 1.0
            new_position = clamp_to_pitch(player.position + direction * (BALL_RADIUS_M + player.radius_m))
    return new_position, new_velocity


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
    ball_position = Vec2(PITCH_LENGTH_M / 2.0, PITCH_WIDTH_M / 2.0)
    ball_velocity = Vec2(0.0, 0.0)

    trace = MatchTrace(home=home_club.name, away=away_club.name, tick_seconds=tick_seconds * record_every)

    n_ticks = int(duration_minutes * 60.0 / tick_seconds)
    for i in range(n_ticks):
        minute = i * tick_seconds / 60.0
        players = [
            step(
                p,
                tick_seconds,
                ball_position if ball_position.distance_to(p.position) < CHASE_RADIUS_M else p.home_target,
                minute,
            )
            for p in players
        ]
        _resolve_player_collisions(players)
        ball_position, ball_velocity = _step_ball(ball_position, ball_velocity, tick_seconds, players)

        if i % record_every == 0:
            trace.record(
                minute,
                [PlayerSnapshot(name=p.name, team=p.team, poste=p.poste, position=p.position) for p in players],
                BallSnapshot(position=ball_position),
            )

    return trace

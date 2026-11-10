"""Ballon mort et remises en jeu (ticket v2-collectif/29) : un ballon qui franchit une ligne sort ; l'adversaire du
dernier toucheur remet en jeu (touche, corner ou sortie de but) ; après un but, l'équipe qui a encaissé engage. Le
ballon reste mort `DEAD_S` secondes, le temps que chacun se replace, puis le preneur le joue par une passe (jamais un
tir ni une conduite) choisie comme toute passe : réussite, receveur libre, progression, puis Decisions. Le jeu court ou
long n'est donc jamais tiré au sort : sous pressing, les solutions courtes sont prises et le preneur joue long.

Constantes validées le 03/11/2026 (chiffres réels sourcés dans le ticket) :
- `DEAD_S` : temps de ballon mort réel médian (touche 13-16 s, sortie de but 24-30 s, corner 28-34 s) ; engagement
  45 s, célébration comprise (la vraie célébration vient de `v2-mise-en-scene/04`) ;
- `RESTART_DISTANCE_M` : Lois du jeu (9,15 m ; 2 m sur une touche) ;
- `THROW_MAX_M` : portée d'une touche lancée à la main (la touche longue de Long Throws : `v2-attributs-restants/02`) ;
- `LONG_RESTART_M` : au-delà, la remise est jouée long et le ballon est aérien ;
- `AERIAL_LANDING_M` : un ballon aérien ne se touche qu'à moins de 3 m de son point de chute (moteur à plat, D-V03) ;
- `REPLACING_INTENSITY` : on se replace en trottinant (moitié de la vitesse max).

Pas de vitesse propre à la touche : le ballon suit la loi de passe (`possession.pass_velocity`), comme toute passe."""

from __future__ import annotations

from dataclasses import dataclass

from ligue1sim.pitch_geometry import PENALTY_SPOT_DISTANCE_M

from v2engine.condition import effective_rating
from v2engine.decision import best_choice_probability
from v2engine.flux import DECISION
from v2engine.geometry import PITCH_LENGTH_M, PITCH_WIDTH_M, Vec2, in_penalty_area
from v2engine.movement import PlayerState
from v2engine.possession import pass_success_probability, pressure

THROW_IN, GOAL_KICK, CORNER, KICKOFF = "touche", "sortie de but", "corner", "engagement"
FREE_KICK, PENALTY = "coup franc", "penalty"  # ticket v2-collectif/30
# Coup franc : 33 s, délai moyen réel avant de le jouer (theanalyst.com, Premier League) ; penalty provisoire : 60 s,
# non sourcé. Validés le 04/11/2026 (ticket v2-collectif/30).
DEAD_S = {THROW_IN: 15.0, GOAL_KICK: 25.0, CORNER: 30.0, KICKOFF: 45.0, FREE_KICK: 33.0, PENALTY: 60.0}
RESTART_DISTANCE_M = {THROW_IN: 2.0, GOAL_KICK: 9.15, CORNER: 9.15, KICKOFF: 9.15, FREE_KICK: 9.15, PENALTY: 9.15}
# Penalty provisoire (ticket v2-collectif/30, en attendant `v2-attributs-restants/02a`) : conversion neutre, sans
# attribut ; réel 76-82 % (Ligue 1 2023-24 : 81 %, ligue1.com ; CIES depuis 2020 : 82,2 %), validée le 04/11/2026.
PENALTY_CONVERSION = 0.78
GOAL_AREA_DEPTH_M = 5.5
GOAL_AREA_HALF_WIDTH_M = 9.16
THROW_MAX_M = 25.0
LONG_RESTART_M = 25.0
AERIAL_LANDING_M = 3.0
REPLACING_INTENSITY = 0.5
SOL, AERIEN = "sol", "aérien"
_FULLBACKS = ("LB", "RB", "LWB", "RWB")
_CENTER = Vec2(PITCH_LENGTH_M / 2.0, PITCH_WIDTH_M / 2.0)
_PROGRESS_SCALE_M = 20.0  # même échelle que la progression d'une passe dans le jeu (`decision`)


@dataclass(frozen=True)
class Restart:
    kind: str
    team: str  # équipe qui remet en jeu
    spot: Vec2
    taker: str | None
    until_s: float  # instant de la reprise du jeu
    minute: float  # minute de la sortie (ou du but)
    last_toucher: str | None = None


def _other(team: str) -> str:
    return "away" if team == "home" else "home"


def _defends_low_x(team: str) -> bool:
    return team == "home"  # convention du moteur : domicile défend x=0 (D-V03)


def exit_point(start: Vec2, end: Vec2) -> tuple[str, Vec2] | None:
    """Ligne franchie entre `start` (dans le terrain) et `end` : ("touche" ou "but", point de sortie), ou None."""
    if 0.0 <= end.x <= PITCH_LENGTH_M and 0.0 <= end.y <= PITCH_WIDTH_M:
        return None
    d = end - start
    crossings = []
    if end.x < 0.0 or end.x > PITCH_LENGTH_M:
        bound = 0.0 if end.x < 0.0 else PITCH_LENGTH_M
        crossings.append(((bound - start.x) / d.x, "but"))
    if end.y < 0.0 or end.y > PITCH_WIDTH_M:
        bound = 0.0 if end.y < 0.0 else PITCH_WIDTH_M
        crossings.append(((bound - start.y) / d.y, "touche"))
    t, line = min(crossings)
    p = start + d * max(0.0, min(1.0, t))
    return line, Vec2(min(max(p.x, 0.0), PITCH_LENGTH_M), min(max(p.y, 0.0), PITCH_WIDTH_M))


def _taker(kind: str, team: str, spot: Vec2, players: list[PlayerState]) -> PlayerState | None:
    """Preneur, par proximité et rôle : gardien sur une sortie de but ; touche : le plus proche, un latéral à distance
    à peu près égale (même tranche de 5 m) ; corner : le joueur offensif le plus proche (ni gardien ni défenseur
    central) ; engagement : le joueur de champ le plus proche du centre ; coup franc : le gardien dans sa propre
    surface, sinon le joueur de champ le plus proche ; penalty provisoire : le joueur de champ le plus proche (le
    tireur désigné viendra avec le ticket `v2-attributs-restants/02a`)."""
    mates = [p for p in players if p.team == team]
    if kind == GOAL_KICK or (kind == FREE_KICK and in_penalty_area(_other(team), spot)):
        keeper = next((p for p in mates if p.poste == "GK"), None)
        if keeper is not None:
            return keeper
    field = [p for p in mates if p.poste != "GK"] or mates
    if kind == CORNER:
        field = [p for p in field if p.poste != "DC"] or field
    if not field:
        return None
    if kind == THROW_IN:
        return min(field, key=lambda p: (int(p.position.distance_to(spot) // 5.0), p.poste not in _FULLBACKS,
                                         p.position.distance_to(spot)))
    return min(field, key=lambda p: p.position.distance_to(spot))


def award(line: str, point: Vec2, last_toucher: PlayerState | None, players: list[PlayerState],
          now_s: float) -> Restart:
    """Remise en jeu après une sortie par `line` au point `point` (règles simplifiées des Lois du jeu)."""
    last_team = last_toucher.team if last_toucher is not None else "home"
    name = last_toucher.name if last_toucher is not None else None
    if line == "touche":
        kind, team, spot = THROW_IN, _other(last_team), point
    else:
        defending = "home" if point.x <= 0.0 else "away"  # équipe dont c'est la ligne de but
        side_y = PITCH_WIDTH_M if point.y > PITCH_WIDTH_M / 2.0 else 0.0
        if last_team == defending:
            kind, team, spot = CORNER, _other(defending), Vec2(point.x, side_y)
        else:
            x = GOAL_AREA_DEPTH_M if _defends_low_x(defending) else PITCH_LENGTH_M - GOAL_AREA_DEPTH_M
            y = PITCH_WIDTH_M / 2.0 + (GOAL_AREA_HALF_WIDTH_M if side_y else -GOAL_AREA_HALF_WIDTH_M)
            kind, team, spot = GOAL_KICK, defending, Vec2(x, y)
    taker = _taker(kind, team, spot, players)
    return Restart(kind, team, spot, taker.name if taker else None, now_s + DEAD_S[kind], now_s / 60.0, name)


def foul_restart(victim_team: str, spot: Vec2, players: list[PlayerState], now_s: float) -> Restart:
    """Faute sifflée (ticket v2-collectif/30) : coup franc à l'équipe victime au lieu de la faute, ou penalty
    provisoire si la faute a lieu dans la surface que cette équipe attaque."""
    if in_penalty_area(victim_team, spot):
        x = PITCH_LENGTH_M - PENALTY_SPOT_DISTANCE_M if victim_team == "home" else PENALTY_SPOT_DISTANCE_M
        kind, spot = PENALTY, Vec2(x, PITCH_WIDTH_M / 2.0)
    else:
        kind = FREE_KICK
    taker = _taker(kind, victim_team, spot, players)
    return Restart(kind, victim_team, spot, taker.name if taker else None, now_s + DEAD_S[kind], now_s / 60.0)


def kickoff(team: str, players: list[PlayerState], now_s: float, dead_s: float = DEAD_S[KICKOFF]) -> Restart:
    taker = _taker(KICKOFF, team, _CENTER, players)
    return Restart(KICKOFF, team, _CENTER, taker.name if taker else None, now_s + dead_s, now_s / 60.0)


def place(player: PlayerState, restart: Restart, wanted: Vec2) -> Vec2:
    """Où se tient `player` pendant le ballon mort : le preneur au point de remise ; les autres à `wanted` (leur place
    dans le bloc ; à l'engagement, leur place de départ, dans leur camp), les adversaires du preneur à la distance
    réglementaire du ballon."""
    if player.name == restart.taker:
        return restart.spot
    target = wanted
    if restart.kind == KICKOFF:  # chacun dans son camp
        half = PITCH_LENGTH_M / 2.0
        target = Vec2(min(target.x, half - 0.5) if _defends_low_x(player.team) else max(target.x, half + 0.5), target.y)
    if player.team != restart.team and not (restart.kind == PENALTY and player.poste == "GK"):  # le gardien reste
        gap = target - restart.spot
        distance = RESTART_DISTANCE_M[restart.kind]
        if gap.length() < distance:
            away = gap.normalized() if gap.length() > 1e-6 else (_CENTER - restart.spot).normalized()
            target = restart.spot + away * distance
    return Vec2(min(max(target.x, 0.0), PITCH_LENGTH_M), min(max(target.y, 0.0), PITCH_WIDTH_M))


def restart_target(taker: PlayerState, kind: str, players: list[PlayerState]) -> PlayerState | None:
    """Receveur de la remise : chaque coéquipier vaut réussite de la passe x liberté du receveur x progression (même
    échelle que dans le jeu) ; la meilleure est prise avec la probabilité donnée par Decisions, sinon une autre."""
    opponents = [p for p in players if p.team != taker.team]
    mates = [p for p in players if p.team == taker.team and p is not taker]
    if kind == THROW_IN:
        mates = [p for p in mates if taker.position.distance_to(p.position) <= THROW_MAX_M]
    if not mates:
        return None
    goal_x = PITCH_LENGTH_M if taker.team == "home" else 0.0
    goal = Vec2(goal_x, PITCH_WIDTH_M / 2.0)
    to_goal = taker.position.distance_to(goal)

    def value(mate: PlayerState) -> float:
        progress = min(1.0, max(0.0, 0.5 + (to_goal - mate.position.distance_to(goal)) / (2.0 * _PROGRESS_SCALE_M)))
        return pass_success_probability(taker, mate, opponents) * (1.0 - pressure(mate, opponents)) * progress

    ranked = sorted(mates, key=value, reverse=True)
    if len(ranked) == 1 or DECISION.random() < best_choice_probability(effective_rating(taker, "Decisions")):
        return ranked[0]
    return DECISION.choice(ranked[1:])


def is_aerial(kind: str, taker: PlayerState, target: PlayerState) -> bool:
    """Remise jouée en l'air : longue (au-delà de `LONG_RESTART_M`) ou corner centré dans la surface."""
    return taker.position.distance_to(target.position) > LONG_RESTART_M or (
        kind == CORNER and in_penalty_area(taker.team, target.position))

"""Anticipation (Phase 5, ticket v2-cerveau-joueurs/04) : réagir AVANT l'action. Deux effets
(Guide_attributs_joueurs.pdf, Anticipation) : un adversaire proche de la trajectoire d'une passe peut la
« lire » et courir vers le point où il la coupe ; sur un ballon libre, un joueur vise l'endroit où le
ballon va s'arrêter plutôt que sa position actuelle. L'interception elle-même reste un contrôle du ballon
(First Touch, `possession.attempt_control`)."""

from __future__ import annotations

from v2engine import freinage, hauteur
from v2engine.attributes import success_probability
from v2engine.condition import effective_rating
from v2engine.flux import PERCEPTION
from v2engine.geometry import Vec2, clamp_to_pitch
from v2engine.movement import PlayerState, max_speed_mps
from v2engine.portee import first_reachable_s, player_body_ceiling_m, player_ceiling_m

# Constantes produit validées par le propriétaire (24/10/2026), courbe partagée du guide.
_READ_PASS = (0.40, 0.40, 0.10, 0.80)  # baseline, amplitude, min, max : 99 -> 80 %, 55 -> 40 %, 11 -> 10 %
READING_LANE_M = 8.0  # seuls les adversaires à moins de 8 m de la trajectoire peuvent lire la passe
_LOOSE_BALL_LEAD = (0.5, 0.5, 0.0, 1.0)  # part du chemin vers le point d'arrêt : 99 -> 100 %, 55 -> 50 %, 11 -> 0 %


def _curve(note: float, params: tuple[float, float, float, float]) -> float:
    baseline, amplitude, low, high = params
    return success_probability(note, baseline=baseline, amplitude=amplitude, min_prob=low, max_prob=high)


# Délai de réaction à un changement de situation (ticket v2-collectif/03, validé le 26/10/2026) : 99 -> 0,4 s,
# 55 -> 0,7 s, 11 -> 1,0 s. Réf. : 0,7 s, temps de réaction par défaut du modèle de pression Unravel Sports (tracking).
_REACTION_S = (0.7, 0.3, 0.4, 1.0)  # baseline, amplitude, min, max (inversé : bonne note = délai court)
MAX_REACTION_S = _REACTION_S[3]


def reaction_delay_s(player: PlayerState) -> float:
    """Temps pour qu'un joueur se rende compte d'un changement de situation de son équipe (perte, récupération)."""
    _, _, low, high = _REACTION_S
    return low + high - _curve(effective_rating(player, "Anticipation"), _REACTION_S)


def read_pass_probability(anticipation: float) -> float:
    return _curve(anticipation, _READ_PASS)


def loose_ball_lead(anticipation: float) -> float:
    return _curve(anticipation, _LOOSE_BALL_LEAD)


def pass_readers(start: Vec2, velocity: Vec2, aim: Vec2, opponents: list[PlayerState]) -> dict[str, Vec2]:
    """Adversaires qui lisent une passe partant de `start` vers `aim` à `velocity`, avec le point de la
    trajectoire où chacun court la couper. Il faut être dans le couloir (`READING_LANE_M`), pouvoir y être
    avant le ballon (vitesse de pointe, ballon supposé à vitesse constante -- critère strict), et la lire
    (tirage piloté par Anticipation)."""
    path = aim - start
    length = path.length()
    speed = velocity.length()
    if length < 1e-9 or speed < 1e-9:
        return {}
    direction = path * (1.0 / length)
    readers = {}
    for opponent in opponents:
        rel = opponent.position - start
        along = min(length, max(0.0, rel.x * direction.x + rel.y * direction.y))
        point = start + direction * along
        if opponent.position.distance_to(point) > READING_LANE_M:
            continue
        if opponent.position.distance_to(point) / max_speed_mps(effective_rating(opponent, "Pace")) > along / speed:
            continue
        if PERCEPTION.random() < read_pass_probability(effective_rating(opponent, "Anticipation")):
            readers[opponent.name] = point
    return readers


def loose_ball_target(player: PlayerState, ball_position: Vec2, ball_velocity: Vec2) -> Vec2:
    """Point visé sur un ballon libre : entre sa position actuelle et son point d'arrêt (`freinage.stop_position`),
    selon Anticipation."""
    stop = freinage.stop_position(ball_position, ball_velocity)
    # borné au terrain : au-delà de la ligne, le ballon est sorti (ticket v2-collectif/29)
    return clamp_to_pitch(ball_position + (stop - ball_position) * loose_ball_lead(effective_rating(player, "Anticipation")))


def meeting_point(player: PlayerState, ball_position: Vec2, ball_velocity: Vec2) -> Vec2:
    """Point de la trajectoire RÉELLE du ballon (freinée, `freinage.position_after`) que `player` peut
    atteindre le plus tôt, à sa vitesse de pointe -- là où un receveur vient couper le ballon (ticket
    v2-socle/01). S'il ne peut l'atteindre nulle part en route, son point d'arrêt."""
    speed = max_speed_mps(effective_rating(player, "Pace"))
    horizon = freinage.time_to_slow(ball_velocity.length(), 0.0)  # jusqu'à l'arrêt réel (ticket v2-realisme/14a2a)
    t = 0.0
    while t < horizon:
        point = freinage.position_after(ball_position, ball_velocity, t)
        if player.position.distance_to(point) <= speed * t:
            return clamp_to_pitch(point)  # borné au terrain (ticket v2-collectif/29)
        t += 0.1
    return clamp_to_pitch(freinage.stop_position(ball_position, ball_velocity))


# Point d'attaque d'un ballon aérien (ticket v2-realisme/15a1). Constantes validées au ticket 15a (27/11/2026) : marge
# d'arrivée 0 s, critère strict comme `pass_readers` ; `ARRIVAL_EPSILON_S` est une tolérance de calcul flottant, pas une
# constante produit.
AERIAL_SAMPLE_S = 0.1  # pas d'échantillonnage de la trajectoire, celui de `meeting_point`
ARRIVAL_EPSILON_S = 1e-6


def aerial_attack_point(player: PlayerState, position: Vec2, velocity: Vec2, z: float, vz: float,
                        ceiling: float | None = None) -> Vec2:
    """Point du premier vol d'un ballon en l'air (`z`, `vz`, convention de `hauteur`) où `player` peut le jouer : le
    premier instant où le bas du ballon passe sous `ceiling` (par défaut son plafond, la tête en saut :
    `portee.player_ceiling_m`) et où il peut être, à sa vitesse de pointe, au plus tard quand le ballon y passe. Horizontal : traînée seule (`freinage.distance_after(...,
    airborne=True)`, ticket 14a2b) ; vertical : chute libre jusqu'au sol. Aucun point atteignable : le point de chute."""
    flight = hauteur.time_to_ground(z, vz)
    speed, direction = velocity.length(), velocity.normalized()
    ceiling = player_ceiling_m(player) if ceiling is None else ceiling
    pace = max_speed_mps(effective_rating(player, "Pace"))

    def at(t: float) -> Vec2:
        return position + direction * freinage.distance_after(speed, t, airborne=True)

    times = [i * AERIAL_SAMPLE_S for i in range(int(flight / AERIAL_SAMPLE_S) + 1)]
    back_under = first_reachable_s(z, vz, ceiling, 0.0, flight)  # instant exact où il repasse sous le plafond
    times = sorted(set(times + ([back_under] if back_under is not None else []) + [flight]))
    for t in times:
        if hauteur.height_at(z, vz, t)[0] > ceiling:
            continue  # au-dessus de lui : le ballon passe
        point = at(t)
        if player.position.distance_to(point) / pace <= t + ARRIVAL_EPSILON_S:
            return clamp_to_pitch(point)  # borné au terrain (ticket v2-collectif/29)
    return clamp_to_pitch(at(flight))


def receiving_point(player: PlayerState, ball) -> Vec2:
    """Point où le receveur va chercher la passe : sur le premier vol d'un ballon en l'air, son point d'attaque aérien
    (`aerial_attack_point`, ticket v2-realisme/15a1) à hauteur de poitrine (`portee.player_body_ceiling_m` : le receveur
    que personne ne conteste amortit le ballon plutôt que de le jouer de la tête, décision du propriétaire du
    27/11/2026 ; le point sous la tête sert au ballon disputé, ticket 15a2 ; centre de coup de pied arrêté dans la
    surface, `ball.set_piece_cross` : sous la tête, option 2 du propriétaire du 28/11/2026) ; sinon `meeting_point`
    (ballon au sol, ou après son premier contact au sol : `ball.landed`, ticket v2-hauteur-ballon/02c). Lu par le
    receveur et par la défense."""
    if not ball.landed and hauteur.time_to_ground(ball.z, ball.vz) > 0.0:
        ceiling = player_ceiling_m(player) if ball.set_piece_cross else player_body_ceiling_m(player)
        return aerial_attack_point(player, ball.position, ball.velocity, ball.z, ball.vz, ceiling)
    return meeting_point(player, ball.position, ball.velocity)

"""Contrôle et passe (Phase 2, docs/PLAN_V2.md ; refonte ticket v2-socle/04) : chaque passe et chaque
contrôle ont une DIFFICULTÉ, calculée sur la situation réelle, sur la même échelle que les attributs ; la
réussite compare la note (Passing, First Touch) à cette difficulté -- quasi certaine sur une action facile
pour tout le monde, décidée par la note sur une action difficile (docs/REVUE_ATTRIBUTS_V2.md). Le DOSAGE
d'une passe réussie (vitesse d'arrivée, passe dans la course) dépend de Passing et rend le contrôle du
receveur plus ou moins difficile. Composure réduit la part de difficulté due à la pression, et elle seule."""

from __future__ import annotations

import math
import random
from collections.abc import Sequence

from v2engine.attributes import duel_probability, success_probability
from v2engine.condition import effective_rating
from v2engine.flux import PASSE
from v2engine.geometry import Vec2
from v2engine.movement import PlayerState

PRESSURE_RADIUS_M = 5.0  # gêne maximale au contact, nulle à 5 m (validé, ticket v2-cerveau-joueurs/01)
BALL_FRICTION_PER_S = 0.6  # freinage du ballon par seconde (partagé avec `match.py`)
BALL_STOPPED_MPS = 0.5  # en dessous, une passe est considérée morte (ballon quasi arrêté)

# --- Constantes validées par le propriétaire (25/10/2026, ticket v2-socle/04) ---------------------------------
_BASE_DIFFICULTY = 10.0  # passe ou contrôle le plus facile
_EASY_DISTANCE_M = 10.0
_DIFFICULTY_PER_M = 1.8  # au-delà de 10 m : 25 m -> 37, 35 m -> 55, 45 m -> 73
_PRESSURE_DIFFICULTY = 15.0  # adversaire au contact du joueur, nulle à `PRESSURE_RADIUS_M`
_MARKED_DIFFICULTY = 10.0  # receveur avec un adversaire à moins de `_MARKED_RADIUS_M`
_MARKED_RADIUS_M = 2.0
_CONTROL_DIFFICULTY_PER_MPS = 1.0  # contrôle : +1 par m/s d'écart à la vitesse d'arrivée idéale
# Réussite = note contre difficulté (courbe partagée) : à égalité 50 %, 40 points d'avance ou plus ~97 %.
_SUCCESS = dict(baseline=0.5, amplitude=0.47, min_prob=0.05, max_prob=0.98)
# passe ratée : déviation de 25 à 50 % de la longueur de la passe (ticket v2-realisme/18h, validé le 12/11/2026 ; 10 à 25 %
# auparavant : la passe ratée restait chez son équipe presque 2 fois sur 3 et Passing pesait peu sur l'issue réelle)
_MISS_SHARE = (0.25, 0.50)
IDEAL_ARRIVAL_MPS = 6.0  # dosage : vitesse du ballon en arrivant au receveur
MAX_PASS_MPS = 30.0
_DOSAGE_ERROR = (0.30, 0.05)  # erreur de vitesse : +/- 30 % à Passing 11, +/- 5 % à 99
# Contrôle raté (ticket v2-collectif/25, validé le 29/10/2026 ; données réelles : non trouvé) : le ballon s'échappe
# dans sa direction, dévié de +/- 20° (contrôle facile) à +/- 60° (le plus difficile), à la moitié de sa vitesse, et
# le même joueur ne peut retenter qu'après `MISS_RETRY_S`.
MISS_DEVIATION_MIN_DEG = 20.0
MISS_DEVIATION_MAX_DEG = 60.0
MISS_SPEED_SHARE = 0.5
MISS_RETRY_S = 0.5
# difficulté du contrôle le plus dur : ballon à la vitesse max d'une passe, adversaire au contact, Composure 11
_HARDEST_CONTROL = _BASE_DIFFICULTY + _CONTROL_DIFFICULTY_PER_MPS * (MAX_PASS_MPS - IDEAL_ARRIVAL_MPS) + _PRESSURE_DIFFICULTY

# --- Coupe en vol dans la chance évaluée (ticket v2-realisme/18g, constantes validées le 12/11/2026) ---------------------
# La coupe d'une passe n'est pas tirée à part : elle se joue physiquement (adversaires qui touchent le ballon en vol,
# lecteurs d'`anticipation.pass_readers`). La chance ÉVALUÉE en tient compte avec une table mesurée sur le moteur (26
# matchs, 23 187 passes ; vérifiée sur 24 autres, pire écart 4,3 points par tranche) : chance qu'un adversaire touche le
# ballon le premier, selon sa distance à la trajectoire, près du passeur (avancée jusqu'à `_NEAR_PASSER_M`) ou sur le
# trajet. Données réelles : non trouvé (la table décrit le moteur ; à remesurer si le mouvement change, indicateur de
# calibration de `scripts/v2_indicators.py`). Remplace le terme de couloir (`_LANE_DIFFICULTY`, + 12 par adversaire),
# qui sous-comptait la coupe (évaluée 0,96, reçue 0,56 avec un adversaire dans le couloir). Remesurée au ticket 18j
# (portée du défenseur qui lit la passe, `match.READER_REACH_M`) : 50 matchs, ajustement sur 27 220 passes, contrôle sur
# 24 945 (écart prévu / non perdue + 0,1 point au total ; `.scratch/v2-realisme/mesures/18j-ajustement.txt`), validé par
# délégation du propriétaire le 12/11/2026.
_NEAR_PASSER_M = 3.0
_CUT_NEAR_PASSER = ((0.5, 0.82), (1.0, 0.21), (6.0, 0.02))  # (distance max à la trajectoire en m, chance de coupe)
_CUT_ON_PATH = ((1.0, 0.43), (2.0, 0.25), (3.0, 0.12), (4.0, 0.07), (5.0, 0.03), (6.0, 0.02))
# passe précise : adversaires qui croisent la trajectoire sans y être au départ (0,05 au 18g, 0,01 au 18i, validé le
# 12/11/2026 : mesurée 0,007 à 0,009 sur 50 matchs ; l'ancien terme comptait surtout le ballon passé à côté du receveur ;
# 0,014 au 18j, gardée)
UNFORESEEN_CUT = 0.01
# passe imprécise (25 à 50 % de sa longueur) non perdue, hors coupe de la table, selon la longueur de la passe (ticket
# v2-realisme/18h : 50 matchs, sortie ou coup de sifflet pour l'adversaire compté perdu ; remesurée au 18i avec la portée
# du receveur, 0,78 / 0,64 -> 0,85 / 0,68, validé le 12/11/2026 ; au 18j avec la portée du lecteur, 0,85 / 0,69)
_MISS_NOT_LOST = ((10.0, 0.85), (math.inf, 0.69))  # (longueur max en m, part non perdue)


def pressure(player: PlayerState, opponents: Sequence[PlayerState]) -> float:
    """Gêne subie par `player` (0 à 1) : 1 au contact de l'adversaire le plus proche, 0 à `PRESSURE_RADIUS_M`."""
    if not opponents:
        return 0.0
    nearest = min(player.position.distance_to(o.position) for o in opponents)
    return max(0.0, 1.0 - nearest / PRESSURE_RADIUS_M)


def composure_factor(player: PlayerState) -> float:
    """Part de la difficulté due à la pression qui reste après Composure : 99 -> 0,5, 55 -> 0,75, 11 -> 1."""
    return 1.5 - success_probability(effective_rating(player, "Composure"), baseline=0.75, amplitude=0.25,
                                     min_prob=0.5, max_prob=1.0)


def dosage_quality(passer: PlayerState) -> float:
    """Qualité du dosage (0 à 1) selon Passing : 99 -> 1 (passe dans la course), 11 -> 0 (dans les pieds)."""
    return success_probability(effective_rating(passer, "Passing"), baseline=0.5, amplitude=0.5, min_prob=0.0, max_prob=1.0)


def _cut_chance(start: Vec2, end: Vec2, opponent: PlayerState) -> float:
    """Chance (table du 18g) que `opponent` touche le premier une passe de `start` vers `end`."""
    path = end - start
    length = path.length()
    if length < 1e-9:
        return 0.0
    direction = path * (1.0 / length)
    rel = opponent.position - start
    along = rel.x * direction.x + rel.y * direction.y
    if not 0.0 < along < length:
        return 0.0
    gap = opponent.position.distance_to(start + direction * along)
    table = _CUT_NEAR_PASSER if along <= _NEAR_PASSER_M else _CUT_ON_PATH
    return next((chance for limit, chance in table if gap < limit), 0.0)


def pass_difficulty(passer: PlayerState, receiver: PlayerState, opponents: Sequence[PlayerState]) -> float:
    """Difficulté de l'EXÉCUTION de la passe (distance, pression sur le passeur, receveur marqué). La coupe en vol par
    les adversaires n'en fait plus partie (ticket v2-realisme/18g) : elle se joue physiquement et compte dans
    `pass_success_probability`."""
    distance = passer.position.distance_to(receiver.position)
    difficulty = _BASE_DIFFICULTY + _DIFFICULTY_PER_M * max(0.0, distance - _EASY_DISTANCE_M)
    difficulty += _PRESSURE_DIFFICULTY * pressure(passer, opponents) * composure_factor(passer)
    if any(receiver.position.distance_to(o.position) < _MARKED_RADIUS_M for o in opponents):
        difficulty += _MARKED_DIFFICULTY
    return difficulty


def pass_accuracy_probability(passer: PlayerState, receiver: PlayerState, opponents: Sequence[PlayerState]) -> float:
    """Chance que la passe parte où le passeur la destine (sinon déviée, `pass_aim`) : Passing contre la difficulté de
    CETTE passe."""
    return duel_probability(effective_rating(passer, "Passing"), pass_difficulty(passer, receiver, opponents), **_SUCCESS)


def pass_success_probability(passer: PlayerState, receiver: PlayerState, opponents: Sequence[PlayerState]) -> float:
    """Chance que la passe ne soit pas perdue (tickets v2-realisme/18g et 18h) : aucun adversaire ne touche le ballon le
    premier, et le ballon ne sort pas (ni n'est sifflé) avec remise pour l'adversaire ; même risque que celui que la passe
    court en jeu. C'est le sens que lui donne la décision (`decision.option_value` :
    garder, sinon perdre le ballon), comme le risque de perte de la conduite (04a). Coupe par adversaire : table du 18g ;
    précise, `UNFORESEEN_CUT` en plus ; imprécise, `_MISS_NOT_LOST` selon la longueur. Le contrôle du receveur n'y entre
    pas : raté, le ballon reste libre près de lui, ce n'est pas une perte."""
    keep = 1.0
    for opponent in opponents:
        keep *= 1.0 - _cut_chance(passer.position, receiver.position, opponent)
    accurate = pass_accuracy_probability(passer, receiver, opponents)
    length = passer.position.distance_to(receiver.position)
    not_lost = next(share for limit, share in _MISS_NOT_LOST if length < limit)
    return keep * (accurate * (1.0 - UNFORESEEN_CUT) + (1.0 - accurate) * not_lost)


def control_difficulty(player: PlayerState, ball_velocity: Vec2, opponents: Sequence[PlayerState]) -> float:
    difficulty = _BASE_DIFFICULTY + _CONTROL_DIFFICULTY_PER_MPS * abs(ball_velocity.length() - IDEAL_ARRIVAL_MPS)
    return difficulty + _PRESSURE_DIFFICULTY * pressure(player, opponents) * composure_factor(player)


def attempt_control(player: PlayerState, ball_velocity: Vec2 = Vec2(0.0, 0.0),
                    opponents: Sequence[PlayerState] = ()) -> bool:
    """Un joueur au contact du ballon tente de le contrôler : First Touch contre la difficulté du ballon reçu
    (vitesse par rapport au ballon idéal, pression). Jamais garanti (règle « jamais binaire » du guide)."""
    difficulty = control_difficulty(player, ball_velocity, opponents)
    return PASSE.random() < duel_probability(effective_rating(player, "First Touch"), difficulty, **_SUCCESS)


def missed_control_velocity(player: PlayerState, ball_velocity: Vec2, opponents: Sequence[PlayerState] = ()) -> Vec2:
    """Vitesse du ballon après un contrôle raté : il continue dans sa direction, dévié d'un angle d'autant plus
    grand que le contrôle était difficile, à `MISS_SPEED_SHARE` de sa vitesse. Un ballon quasi arrêté que le
    joueur percute en courant part devant lui."""
    base = ball_velocity if ball_velocity.length() >= BALL_STOPPED_MPS else player.velocity
    if base.length() < 1e-9:
        base = Vec2(1.0, 0.0)  # ni ballon ni joueur en mouvement : direction fixe
    hardness = (control_difficulty(player, ball_velocity, opponents) - _BASE_DIFFICULTY) / (_HARDEST_CONTROL - _BASE_DIFFICULTY)
    limit = MISS_DEVIATION_MIN_DEG + (MISS_DEVIATION_MAX_DEG - MISS_DEVIATION_MIN_DEG) * min(1.0, max(0.0, hardness))
    angle = math.radians(PASSE.uniform(-limit, limit))
    speed = max(MISS_SPEED_SHARE * base.length(), 1.0)  # jamais collé au pied : au moins 1 m/s
    direction = base.normalized()
    cos_a, sin_a = math.cos(angle), math.sin(angle)
    return Vec2(direction.x * cos_a - direction.y * sin_a, direction.x * sin_a + direction.y * cos_a) * speed


def _launch_speed(distance_m: float) -> float:
    """Vitesse de départ pour que le ballon, freiné, arrive à `IDEAL_ARRIVAL_MPS` après `distance_m`."""
    return min(MAX_PASS_MPS, IDEAL_ARRIVAL_MPS - distance_m * math.log(BALL_FRICTION_PER_S))


def pass_aim(passer: PlayerState, target: PlayerState, opponents: Sequence[PlayerState] = ()) -> Vec2:
    """Point visé par une passe de `passer` vers `target`. Réussie (Passing contre difficulté) : là où le receveur
    VA être, d'autant plus précisément que le dosage est bon. Ratée : déviée de 25 à 50 % de sa longueur (18h)."""
    distance = passer.position.distance_to(target.position)
    speed = _launch_speed(distance)
    log_f = math.log(BALL_FRICTION_PER_S)
    arrival = max(BALL_STOPPED_MPS, speed + distance * log_f)  # < 6 m/s si la vitesse est plafonnée (passe > ~47 m)
    travel_s = math.log(arrival / speed) / log_f
    aim = target.position + target.velocity * (travel_s * dosage_quality(passer))  # dans la course, selon le dosage
    if PASSE.random() >= pass_accuracy_probability(passer, target, opponents):
        angle = PASSE.uniform(0.0, 2.0 * math.pi)
        miss = PASSE.uniform(*_MISS_SHARE) * distance
        aim = aim + Vec2(miss * math.cos(angle), miss * math.sin(angle))
    return aim


def pass_velocity(passer: PlayerState, target: PlayerState, opponents: Sequence[PlayerState] = ()) -> Vec2:
    """Vitesse du ballon au départ d'une passe vers `pass_aim` : de quoi y arriver à ~6 m/s (plafond 30 m/s),
    avec une erreur de vitesse selon le dosage (+/- 30 % à Passing 11, +/- 5 % à 99)."""
    aim = pass_aim(passer, target, opponents)
    quality = dosage_quality(passer)
    error = _DOSAGE_ERROR[0] + (_DOSAGE_ERROR[1] - _DOSAGE_ERROR[0]) * quality
    speed = min(MAX_PASS_MPS, _launch_speed(passer.position.distance_to(aim)) * (1.0 + PASSE.uniform(-error, error)))
    return (aim - passer.position).normalized() * speed


# --- Rythme : temps entre la réception et la première décision (ticket v2-socle/06, validé le 25/10/2026) -----
# Réel : 2,49 s en moyenne par possession de joueur, 4,61 s pour un gardien (arXiv 2308.05460). First Touch
# règle ce temps (contrôle orienté qui fait gagner du temps : 99 -> 1,7 s, 55 -> 2,3 s, 11 -> 2,9 s, niveau
# calé sur 20 matchs le 25/10/2026, fourchette validée 1,7-2,5 s pour 55) ; la pression le réduit jusqu'à moitié
# au contact ; un gardien sans pression ne joue jamais avant 3,5 s.
_RECEPTION_S = (2.3, 0.6, 1.7, 2.9)  # baseline, amplitude, min, max (inversé : bonne note = temps court)
_KEEPER_MIN_RECEPTION_S = 3.5
# Pendant ce temps, il avance à 40 % de sa vitesse max (~3 m/s pour un joueur moyen) : réel ~2,9 m/s à la
# réception, Ligue 1 (UCLan, eprint 12267) ; validé le 25/10/2026.
RECEPTION_SPEED_FACTOR = 0.4


def reception_delay_s(player: PlayerState, opponents: Sequence[PlayerState] = ()) -> float:
    baseline, amplitude, low, high = _RECEPTION_S
    calm = low + high - success_probability(effective_rating(player, "First Touch"), baseline=baseline,
                                                amplitude=amplitude, min_prob=low, max_prob=high)
    if player.poste == "GK":
        calm = max(calm, _KEEPER_MIN_RECEPTION_S)
    return calm * (1.0 - 0.5 * pressure(player, opponents))


# Déviation au contact d'un corps (ticket v2-realisme/05d, proposé le 09/11/2026, validé par délégation du propriétaire).
# Le corps (ou la jambe tendue) est un cylindre vertical de rayon `radius_m` : le ballon le touche au point où il entre
# dans ce rayon ; la normale en ce point dépend du décalage latéral du ballon par rapport au centre. La composante
# normale de la vitesse est renvoyée avec le coefficient de restitution `DEFLECTION_RESTITUTION`, la composante
# tangentielle est gardée (ballon effleuré : presque pas dévié) ; puis un écart tiré dans ±`DEFLECTION_NOISE_DEG`
# (surface du corps irrégulière, rotation du ballon absente avant le 14c). Restitution ballon contre corps humain : non
# trouvée (ordre de grandeur 0,3 à 0,5, corps mou et jambe qui amortit) ; écart : ordre de grandeur.
DEFLECTION_RESTITUTION = 0.4
DEFLECTION_NOISE_DEG = 15.0


def deflect(velocity: Vec2, ball_at: Vec2, body_at: Vec2, radius_m: float, rng: random.Random) -> Vec2:
    """Vitesse du ballon après le contact d'un corps centré en `body_at` (portée `radius_m`), le ballon allant à
    `velocity` et passant en `ball_at` au plus près du corps. Contact dans l'axe : renvoyé vers d'où il vient, à
    `DEFLECTION_RESTITUTION` de sa vitesse ; contact excentré : dévié du côté de l'impact, d'autant moins qu'il est
    effleuré. `rng` : flux du geste qui dévie (tir, passe...)."""
    speed = velocity.length()
    if speed < 1e-9:
        return velocity
    d = velocity * (1.0 / speed)
    offset = ball_at - body_at
    side = offset - d * (offset.x * d.x + offset.y * d.y)  # décalage latéral du ballon, perpendiculaire à sa course
    u = min(1.0, side.length() / radius_m) if radius_m > 1e-9 else 0.0
    perp = side.normalized() if side.length() > 1e-9 else Vec2(0.0, 0.0)
    normal = perp * u - d * math.sqrt(max(0.0, 1.0 - u * u))  # du centre du corps vers le point d'impact
    along = velocity.x * normal.x + velocity.y * normal.y  # négatif : le ballon rentre dans le corps
    out = velocity - normal * ((1.0 + DEFLECTION_RESTITUTION) * along) if along < 0.0 else velocity
    turn = math.radians(rng.uniform(-DEFLECTION_NOISE_DEG, DEFLECTION_NOISE_DEG))
    c, s = math.cos(turn), math.sin(turn)
    return Vec2(out.x * c - out.y * s, out.x * s + out.y * c)

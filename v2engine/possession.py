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
from v2engine.reception import DE_FACE, DE_PROFIL, DOS_AU_JEU
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
# Talonnade (ticket v2-realisme/07e, constantes recommandées et validées par délégation du propriétaire, 13/11/2026) :
# passe courte vers un coéquipier dans le dos, sans se retourner. Geste difficile : Technique remplace Passing dans la
# loi de précision (docs/CARTE_ATTRIBUTS_V2.md : Technique = gestes difficiles), la difficulté du geste s'ajoute à
# celle de la passe. Portée : au plus `BACKHEEL_MAX_M` (StatsBomb, 80 matchs des cinq grands championnats 2015-16 :
# passes « Other », ni pied ni tête, borne haute des talonnades, longueur médiane 7,8 m, réussite 83 %).
BACKHEEL_MAX_M = 10.0
BACKHEEL_DIFFICULTY = 20.0
# Passe de première (ticket v2-collectif/31a, valeurs proposées et validées par le propriétaire le 13/11/2026) : sans
# contrôle, la chance que la passe parte juste est multipliée par une précision du geste selon Technique (0,85 à 11,
# 0,93 à 55, 0,98 à 99 ; chiffre réel non trouvé). La pression gêne déjà toute passe (`pass_difficulty`) : rien de plus
# ici. La difficulté selon l'arrivée du ballon (fort, de côté, de dos) est au ticket 36a.
_ONE_TOUCH_PRECISION_POINTS: tuple[tuple[float, float], ...] = ((11.0, 0.85), (55.0, 0.93), (99.0, 0.98))


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


def pass_difficulty(passer: PlayerState, receiver: PlayerState, opponents: Sequence[PlayerState],
                    backheel: bool = False) -> float:
    """Difficulté de l'EXÉCUTION de la passe (distance, pression sur le passeur, receveur marqué ; talonnade,
    `BACKHEEL_DIFFICULTY`, ticket v2-realisme/07e). La coupe en vol par les adversaires n'en fait plus partie (ticket
    v2-realisme/18g) : elle se joue physiquement et compte dans `pass_success_probability`."""
    distance = passer.position.distance_to(receiver.position)
    difficulty = _BASE_DIFFICULTY + _DIFFICULTY_PER_M * max(0.0, distance - _EASY_DISTANCE_M)
    difficulty += _PRESSURE_DIFFICULTY * pressure(passer, opponents) * composure_factor(passer)
    if any(receiver.position.distance_to(o.position) < _MARKED_RADIUS_M for o in opponents):
        difficulty += _MARKED_DIFFICULTY
    return difficulty + (BACKHEEL_DIFFICULTY if backheel else 0.0)


def one_touch_precision(passer: PlayerState) -> float:
    """Part de la précision gardée par une passe jouée de première, selon Technique (ticket v2-collectif/31a)."""
    note = min(max(effective_rating(passer, "Technique"), _ONE_TOUCH_PRECISION_POINTS[0][0]),
               _ONE_TOUCH_PRECISION_POINTS[-1][0])
    for (n0, v0), (n1, v1) in zip(_ONE_TOUCH_PRECISION_POINTS, _ONE_TOUCH_PRECISION_POINTS[1:]):
        if note <= n1:
            return v0 + (note - n0) / (n1 - n0) * (v1 - v0)
    return _ONE_TOUCH_PRECISION_POINTS[-1][1]


def pass_accuracy_probability(passer: PlayerState, receiver: PlayerState, opponents: Sequence[PlayerState],
                              backheel: bool = False, one_touch: bool = False) -> float:
    """Chance que la passe parte où le passeur la destine (sinon déviée, `pass_aim`) : Passing contre la difficulté de
    CETTE passe ; Technique pour une talonnade (ticket v2-realisme/07e) ; jouée de première, précision du geste en plus
    (`one_touch_precision`, ticket v2-collectif/31a)."""
    skill = effective_rating(passer, "Technique") if backheel else effective_rating(passer, "Passing")
    accurate = duel_probability(skill, pass_difficulty(passer, receiver, opponents, backheel), **_SUCCESS)
    return accurate * one_touch_precision(passer) if one_touch else accurate


def pass_success_probability(passer: PlayerState, receiver: PlayerState, opponents: Sequence[PlayerState],
                             backheel: bool = False, one_touch: bool = False) -> float:
    """Chance que la passe ne soit pas perdue (tickets v2-realisme/18g et 18h) : aucun adversaire ne touche le ballon le
    premier, et le ballon ne sort pas (ni n'est sifflé) avec remise pour l'adversaire ; même risque que celui que la passe
    court en jeu. C'est le sens que lui donne la décision (`decision.option_value` :
    garder, sinon perdre le ballon), comme le risque de perte de la conduite (04a). Coupe par adversaire : table du 18g ;
    précise, `UNFORESEEN_CUT` en plus ; imprécise, `_MISS_NOT_LOST` selon la longueur. Le contrôle du receveur n'y entre
    pas : raté, le ballon reste libre près de lui, ce n'est pas une perte."""
    keep = 1.0
    for opponent in opponents:
        keep *= 1.0 - _cut_chance(passer.position, receiver.position, opponent)
    accurate = pass_accuracy_probability(passer, receiver, opponents, backheel, one_touch)
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


def pass_aim(passer: PlayerState, target: PlayerState, opponents: Sequence[PlayerState] = (),
             backheel: bool = False, one_touch: bool = False) -> Vec2:
    """Point visé par une passe de `passer` vers `target`. Réussie (Passing contre difficulté) : là où le receveur
    VA être, d'autant plus précisément que le dosage est bon. Ratée : déviée de 25 à 50 % de sa longueur (18h)."""
    distance = passer.position.distance_to(target.position)
    speed = _launch_speed(distance)
    log_f = math.log(BALL_FRICTION_PER_S)
    arrival = max(BALL_STOPPED_MPS, speed + distance * log_f)  # < 6 m/s si la vitesse est plafonnée (passe > ~47 m)
    travel_s = math.log(arrival / speed) / log_f
    aim = target.position + target.velocity * (travel_s * dosage_quality(passer))  # dans la course, selon le dosage
    if PASSE.random() >= pass_accuracy_probability(passer, target, opponents, backheel, one_touch):
        angle = PASSE.uniform(0.0, 2.0 * math.pi)
        miss = PASSE.uniform(*_MISS_SHARE) * distance
        aim = aim + Vec2(miss * math.cos(angle), miss * math.sin(angle))
    return aim


def pass_velocity(passer: PlayerState, target: PlayerState, opponents: Sequence[PlayerState] = (),
                  backheel: bool = False, one_touch: bool = False) -> Vec2:
    """Vitesse du ballon au départ d'une passe vers `pass_aim` : de quoi y arriver à ~6 m/s (plafond 30 m/s),
    avec une erreur de vitesse selon le dosage (+/- 30 % à Passing 11, +/- 5 % à 99)."""
    aim = pass_aim(passer, target, opponents, backheel, one_touch)
    quality = dosage_quality(passer)
    error = _DOSAGE_ERROR[0] + (_DOSAGE_ERROR[1] - _DOSAGE_ERROR[0]) * quality
    speed = min(MAX_PASS_MPS, _launch_speed(passer.position.distance_to(aim)) * (1.0 + PASSE.uniform(-error, error)))
    return (aim - passer.position).normalized() * speed


# --- Rythme : temps entre la réception et la première décision (ticket v2-socle/06, validé le 25/10/2026) -----
# Réel : 2,49 s en moyenne par possession de joueur, 4,61 s pour un gardien (arXiv 2308.05460). Jusqu'au ticket
# v2-collectif/31b, First Touch réglait ce temps directement (99 -> 1,7 s, 55 -> 2,3 s, 11 -> 2,9 s, niveau
# calé sur 20 matchs le 25/10/2026, fourchette validée 1,7-2,5 s pour 55) ; la pression le réduit jusqu'à moitié
# au contact ; un gardien sans pression ne joue jamais avant 3,5 s.
# Contrôle orienté (ticket v2-collectif/31b, valeurs proposées et validées par le propriétaire le 13/11/2026) : First
# Touch ne règle plus directement ce temps mais la chance d'orienter son contrôle (25 % à 11, 50 % à 55, 75 % à 99,
# linéaire) ; orienté, le temps de base est x 0,6 (le premier contact place le ballon et le corps vers le jeu), sinon
# x 1,4. Moyenne attendue : 2,76 s à 11, 2,3 s à 55, 1,84 s à 99, proche des repères d'avant (2,9 / 2,3 / 1,7 s) : le rythme
# calé reste le même, le temps devient bimodal. Chiffres réels (part des contrôles orientés, durée selon l'orientation) :
# non trouvés. Technique et vitesse du ballon : ticket 31c ; orientation du corps à la réception : `v2-realisme/07d`.
RECEPTION_CALM_S = 2.3
ORIENTED_FACTOR = 0.6
UNORIENTED_FACTOR = 1.4
_ORIENTED_POINTS: tuple[tuple[float, float], ...] = ((11.0, 0.25), (55.0, 0.50), (99.0, 0.75))
# Ballon dur à orienter (ticket v2-collectif/31c, loi proposée et validée par le propriétaire le 13/11/2026) : la chance
# d'orienter baisse avec la dureté du ballon reçu, (vitesse - 6) / (30 - 6) bornée à [0, 1] (`IDEAL_ARRIVAL_MPS`,
# `MAX_PASS_MPS`) ; Technique (geste difficile, contrôle en pleine course) en compense une part : 0,2 à 11, 0,5 à 55,
# 0,8 à 99 (linéaire, non trouvée). Ballon à 6 m/s ou moins : rien ne change. Cumul First Touch x Technique (A17).
_HARD_BALL_TECHNIQUE_POINTS: tuple[tuple[float, float], ...] = ((11.0, 0.2), (55.0, 0.5), (99.0, 0.8))
# Orientation du corps au contact (ticket v2-realisme/07d, facteurs proposés et validés par le propriétaire le
# 13/11/2026) : un contrôle NON orienté dure plus ou moins selon le type de réception (07c) ; de profil, corps ouvert,
# x 0,85 ; de face (corps vers le but adverse, ballon souvent reçu de dos), x 0,95 ; dos au jeu, x 1,35. Facteur moyen
# pondéré 1,01 sur la répartition mesurée (60 % de face, 19 % de profil, 21 % dos au jeu, 4 matchs) : rythme gardé.
# Un contrôle orienté (31b) est le geste qui se retourne : il n'en dépend pas (pas de double comptage). Ballon reçu dans
# le dos d'un joueur non lancé (contrôle à l'aveugle, `reception.blind_reception`) : compté dos au jeu, sans renormaliser
# (option validée le 13/11/2026 : moyenne attendue d'environ 1,11). Chiffres réels : non trouvés.
RECEPTION_KIND_FACTORS: dict[str, float] = {DE_PROFIL: 0.85, DE_FACE: 0.95, DOS_AU_JEU: 1.35}
_KEEPER_MIN_RECEPTION_S = 3.5
# Pendant ce temps, il avance à 40 % de sa vitesse max (~3 m/s pour un joueur moyen) : réel ~2,9 m/s à la
# réception, Ligue 1 (UCLan, eprint 12267) ; validé le 25/10/2026.
RECEPTION_SPEED_FACTOR = 0.4


def _linear(note: float, points: tuple[tuple[float, float], ...]) -> float:
    note = min(max(note, points[0][0]), points[-1][0])
    for (n0, v0), (n1, v1) in zip(points, points[1:]):
        if note <= n1:
            return v0 + (note - n0) / (n1 - n0) * (v1 - v0)
    return points[-1][1]


def hard_ball_share(ball_velocity: Vec2) -> float:
    """Dureté du ballon reçu (ticket v2-collectif/31c) : 0 jusqu'à `IDEAL_ARRIVAL_MPS`, 1 à `MAX_PASS_MPS`."""
    return min(1.0, max(0.0, (ball_velocity.length() - IDEAL_ARRIVAL_MPS) / (MAX_PASS_MPS - IDEAL_ARRIVAL_MPS)))


def hard_ball_technique_share(player: PlayerState) -> float:
    """Part de la gêne d'un ballon dur que Technique compense (ticket v2-collectif/31c)."""
    return _linear(effective_rating(player, "Technique"), _HARD_BALL_TECHNIQUE_POINTS)


def oriented_control_probability(player: PlayerState, ball_velocity: Vec2 = Vec2(0.0, 0.0)) -> float:
    """Chance que son contrôle soit orienté (ticket v2-collectif/31b) : First Touch, moins la gêne d'un ballon dur que
    Technique ne compense pas (ticket 31c)."""
    base = _linear(effective_rating(player, "First Touch"), _ORIENTED_POINTS)
    return base * (1.0 - hard_ball_share(ball_velocity) * (1.0 - hard_ball_technique_share(player)))


def orients_control(player: PlayerState, ball_velocity: Vec2 = Vec2(0.0, 0.0)) -> bool:
    """Tirage (flux passe, contrôle) : son contrôle est-il orienté (tickets v2-collectif/31b et 31c) ?"""
    return PASSE.random() < oriented_control_probability(player, ball_velocity)


def reception_delay_s(player: PlayerState, opponents: Sequence[PlayerState] = (), oriented: bool | None = None,
                      kind: str | None = None) -> float:
    """Temps entre la prise du ballon et la première décision (v2-socle/06) : orienté ou non (ticket v2-collectif/31b) ;
    `None` (ballon gagné au tacle, remise en jeu, gardien...) : sa moyenne attendue, sans tirage. Non orienté, selon le
    type de réception au contact `kind` (ticket v2-realisme/07d). La pression le réduit jusqu'à moitié au contact ; un
    gardien sans pression ne joue jamais avant 3,5 s."""
    if oriented is None:
        share = oriented_control_probability(player)
        factor = share * ORIENTED_FACTOR + (1.0 - share) * UNORIENTED_FACTOR
    elif oriented:
        factor = ORIENTED_FACTOR
    else:
        factor = UNORIENTED_FACTOR * (RECEPTION_KIND_FACTORS[kind] if kind is not None else 1.0)
    calm = RECEPTION_CALM_S * factor
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

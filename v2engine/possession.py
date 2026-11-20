"""Contrôle et passe (Phase 2, docs/PLAN_V2.md ; refonte ticket v2-socle/04). Le contrôle a une DIFFICULTÉ, calculée
sur la situation réelle, sur la même échelle que les attributs ; la réussite compare First Touch à cette difficulté. La
passe (ticket v2-realisme/23a) n'est plus réussie ou ratée au tirage : le ballon part avec une erreur d'exécution
continue (angle et vitesse gaussiens, plus larges quand Passing est bas et sous pression, Composure comprise) et la
passe réussit ou non par la physique. Le DOSAGE (vitesse d'arrivée, passe dans la course) dépend de Passing et rend le
contrôle du receveur plus ou moins difficile."""

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
_BASE_DIFFICULTY = 10.0  # contrôle le plus facile
# Au-delà de `LONG_PASS_M`, une passe peut partir en l'air (ticket v2-collectif/15a ; même seuil que les remises jouées
# long, `restart.LONG_RESTART_M`).
LONG_PASS_M = 25.0
_PRESSURE_DIFFICULTY = 15.0  # adversaire au contact du joueur, nulle à `PRESSURE_RADIUS_M`
_CONTROL_DIFFICULTY_PER_MPS = 1.0  # contrôle : +1 par m/s d'écart à la vitesse d'arrivée idéale
# Réussite = note contre difficulté (courbe partagée) : à égalité 50 %, 40 points d'avance ou plus ~97 %.
_SUCCESS = dict(baseline=0.5, amplitude=0.47, min_prob=0.05, max_prob=0.98)
IDEAL_ARRIVAL_MPS = 6.0  # dosage : vitesse du ballon en arrivant au receveur
MAX_PASS_MPS = 30.0
# --- Erreur d'exécution continue de la passe (ticket v2-realisme/23a, constantes proposées et validées par délégation du
# propriétaire le 19/11/2026) --------------------------------------------------------------------------------------------
# Plus de passe réussie ou ratée en tout ou rien : la direction du ballon s'écarte de la passe idéale d'un angle gaussien,
# sa vitesse de départ d'une part gaussienne ; la passe réussit ou non par la physique (le ballon arrive, ou non, dans la
# portée du receveur avant un adversaire). Écart-type de l'angle sans pression selon Passing (Technique pour une
# talonnade), linéaire entre les points ; donnée réelle : non trouvée (ordre de grandeur : à 20 m, 1 m d'écart latéral
# vaut 2,9°). Un écart angulaire fixe fait déjà croître l'erreur latérale avec la longueur : la longueur n'élargit pas
# l'angle. Ni l'adversaire dans la ligne ni le receveur marqué n'élargissent l'écart : ils agissent par la physique
# (interception, receveur devancé ; réserve A2 de l'expert, 10/11/2026).
PASS_SIGMA_DEG_POINTS: tuple[tuple[float, float], ...] = ((11.0, 6.0), (55.0, 3.0), (99.0, 1.5))
# Pression sur le passeur : écart multiplié par 1 + gain x pression x part laissée par Composure (même forme que le tir,
# `shooting.SHOT_ERROR_PRESSURE_GAIN`) ; au contact, Composure moyenne : x 1,75.
PASS_PRESSURE_SIGMA_GAIN = 1.0
# Écart de la vitesse de départ (part de la vitesse idéale) : écart-type de l'erreur uniforme d'avant (+/- 30 % à
# Passing 11, +/- 5 % à 99, divisé par racine de 3), selon le dosage ; bornée à [0 ; `MAX_PASS_MPS`].
PASS_SPEED_SIGMA = (0.30 / math.sqrt(3.0), 0.05 / math.sqrt(3.0))
# Passe « précise » pour la chance évaluée (`pass_accuracy_probability`) : écart latéral à l'arrivée sous
# `ON_TARGET_M`, la portée du receveur (`match.RECEIVER_REACH_M`, 1 m ; grille de 1 à 2,5 m, ajustement ci-dessous) ;
# passe longue en l'air (ticket v2-collectif/15a) : sous
# `LOFTED_ON_TARGET_M`, le receveur attaque un ballon qui retombe (à 50 m, Passing 55 : 66 % de passes précises, 69 % au
# 15a). Au sol, la part non perdue dépend de l'ampleur de l'écart (`_LATERAL_NOT_LOST`).
ON_TARGET_M = 1.0
LOFTED_ON_TARGET_M = 2.5
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
# ballon le premier, selon sa distance à la trajectoire, près du passeur (avancée jusqu'à 3 m) ou sur le
# trajet. Données réelles : non trouvé (la table décrit le moteur ; à remesurer si le mouvement change, indicateur de
# calibration de `scripts/v2_indicators.py`). Remplace le terme de couloir (`_LANE_DIFFICULTY`, + 12 par adversaire),
# qui sous-comptait la coupe (évaluée 0,96, reçue 0,56 avec un adversaire dans le couloir). Remesurée au ticket 18j
# (portée du défenseur qui lit la passe, `match.READER_REACH_M`) : 50 matchs, ajustement sur 27 220 passes, contrôle sur
# 24 945 (écart prévu / non perdue + 0,1 point au total ; `.scratch/v2-realisme/mesures/18j-ajustement.txt`), validé par
# délégation du propriétaire le 12/11/2026.
# Remplacée au ticket v2-realisme/18n (constantes validées par le propriétaire le 20/11/2026) : la table du 18g ne
# dépendait que de la distance à la trajectoire (près du passeur, puis sur le trajet). Or, à distance égale, la coupe
# dépend du TEMPS que met le ballon à arriver au niveau de l'adversaire (une passe courte part lentement : 8,6 m/s à
# 5 m, 21 m/s à 30 m) ; à temps égal, passes courtes et longues sont coupées au même taux. D'où un biais selon la
# longueur (+ 3,3 points sous 8 m, − 1,0 de 15 à 30 m, 48 matchs). Table à deux entrées : distance à la trajectoire, temps
# du ballon (parti à la vitesse de la passe idéale, `_launch_speed`, freiné) jusqu'au point le plus proche de
# l'adversaire. Part des adversaires ATTEINTS par le ballon (aucun adversaire plus près du passeur ne l'a touché avant)
# qui le touchent les premiers : estimateur séquentiel, le 18g sous-comptait les adversaires du fond. Mesurée sur 24
# matchs (graines 2200 à 2223, moteur du commit 52bd2ec, 30 703 passes au sol) ; contrôle hors ligne sur 48 (graines 2300
# à 2347) : pire tranche 4,2 -> 1,4 points, longueur sous 8 m + 0,5. Données réelles : non trouvé (la table décrit le
# moteur, à remesurer si le mouvement change). Mesures : `.scratch/v2-realisme/mesures/18n-*`.
_CUT_TIME_S = (0.05, 0.1, 0.15, 0.2, 0.3, 0.45, 0.7, 1.0, math.inf)  # bornes hautes des colonnes (s)
_CUT_TABLE = (  # (distance max à la trajectoire en m, chance de coupe par colonne de temps)
    (0.5, (0.77, 0.91, 0.90, 0.80, 0.63, 0.77, 0.71, 0.56, 0.29)),
    (1.0, (0.03, 0.27, 0.59, 0.65, 0.74, 0.55, 0.64, 0.51, 0.31)),
    (2.0, (0.0, 0.01, 0.09, 0.18, 0.26, 0.42, 0.44, 0.39, 0.30)),
    (3.0, (0.0, 0.0, 0.0, 0.01, 0.02, 0.07, 0.19, 0.29, 0.24)),
    (4.0, (0.0, 0.0, 0.0, 0.0, 0.01, 0.03, 0.08, 0.19, 0.18)),
    (6.0, (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.02, 0.07, 0.10)),
)
# Passe au sol (ticket v2-realisme/23a, réserve A2 de l'expert à la clôture) : part non perdue hors coupe de la table,
# selon l'écart latéral à l'arrivée tiré par la loi d'écart (`pass_error_sigma_rad`) ; la chance de chaque bande sort de
# la même gaussienne, donc de Passing, de la pression et de la longueur. Bande sous `ON_TARGET_M` : passe précise
# (adversaires imprévus qui croisent la trajectoire compris, l'ancien `UNFORESEEN_CUT`). Ajustée par moindres carrés sur
# les tranches de chance évaluée (mêmes 24 matchs ; parts brutes par bande d'écart réalisé 0,992 / 0,984 / 0,970 / 0,922),
# parts plafonnées à 0,99 (garde du 19c : une passe facile garde au moins 1 % d'échec ; 1,0 / 1,0 / 0,94 / 0,70 sans
# plafond). Contrôle hors échantillon sur 48 matchs (graines 400 à 447, joués avec les parts non plafonnées, chance
# recalculée hors ligne) : moyenne − 0,2 point, pire écart 3,3 points en 7 tranches. Critère du propriétaire (20/11/2026) :
# au plus 4 points par tranche d'au moins 500 passes, moyenne à 0,5 point près. Réajustées au ticket v2-realisme/18n avec
# la table de coupe à deux entrées (moindres carrés, mêmes 24 matchs : 0,996 / 0,988 / 0,984 / 0,797 bruts, plafonnés à
# 0,99, arrondis ; 23a : 0,99 / 0,98 / 0,98 / 0,70 ; validées par le propriétaire le 20/11/2026).
_LATERAL_NOT_LOST = ((ON_TARGET_M, 0.99), (2.0, 0.99), (4.0, 0.98), (math.inf, 0.80))  # (écart max en m, part)
# passe longue en l'air imprécise (au-delà de `LOFTED_ON_TARGET_M`) non perdue : la valeur du 18j, gardée (249 passes en
# l'air sur 50 matchs au 23a, trop peu pour l'ajuster ; mesurées 0,54 imprécises contre 0,65 précises)
LOFTED_MISS_NOT_LOST = 0.69
# Talonnade (ticket v2-realisme/07e, constantes recommandées et validées par délégation du propriétaire, 13/11/2026) :
# passe courte vers un coéquipier dans le dos, sans se retourner. Geste difficile : Technique remplace Passing dans la
# loi d'écart (docs/CARTE_ATTRIBUTS_V2.md : Technique = gestes difficiles) ; le geste multiplie l'écart par
# `BACKHEEL_SIGMA_FACTOR` (ticket v2-realisme/23a ; il ajoutait 20 points de difficulté auparavant). Portée : au plus `BACKHEEL_MAX_M` (StatsBomb, 80 matchs des cinq grands championnats 2015-16 :
# passes « Other », ni pied ni tête, borne haute des talonnades, longueur médiane 7,8 m, réussite 83 %).
BACKHEEL_MAX_M = 10.0
BACKHEEL_SIGMA_FACTOR = 2.0
# Passe de première (ticket v2-collectif/31a, valeurs proposées et validées par le propriétaire le 13/11/2026) : sans
# contrôle, l'écart de la passe est divisé par une précision du geste selon Technique (0,85 à 11, 0,93 à 55, 0,98 à 99 ;
# chiffre réel non trouvé ; elle multipliait la chance de passe précise avant le ticket v2-realisme/23a). La pression
# gêne déjà toute passe (`pass_error_sigma_rad`) : rien de plus ici. La difficulté selon l'arrivée du ballon (fort, de côté, de dos) est au ticket 36a.
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
    """Chance (table du 18n) que `opponent` touche le premier une passe de `start` vers `end`, s'il est atteint par le
    ballon : selon sa distance à la trajectoire et le temps que met le ballon à arriver à son niveau."""
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
    row = next((chances for limit, chances in _CUT_TABLE if gap < limit), None)
    if row is None:
        return 0.0
    log_f = math.log(BALL_FRICTION_PER_S)
    speed = _launch_speed(length)
    at = max(BALL_STOPPED_MPS, speed + along * log_f)  # vitesse au niveau de l'adversaire (freinage linéaire en distance)
    travel = math.log(at / speed) / log_f
    return next(chance for limit, chance in zip(_CUT_TIME_S, row) if travel < limit)


def one_touch_precision(passer: PlayerState) -> float:
    """Part de la précision gardée par une passe jouée de première, selon Technique (ticket v2-collectif/31a)."""
    return _linear(effective_rating(passer, "Technique"), _ONE_TOUCH_PRECISION_POINTS)


def pass_error_sigma_rad(passer: PlayerState, opponents: Sequence[PlayerState], backheel: bool = False,
                         one_touch: bool = False) -> float:
    """Écart-type (rad) de l'angle entre la passe jouée et la passe idéale (ticket v2-realisme/23a) : Passing (Technique
    pour une talonnade), élargi par la pression sur le passeur (Composure comprise), par la talonnade et par la passe de
    première. Ni la longueur, ni l'adversaire dans la ligne, ni le receveur marqué n'y entrent (réserve A2)."""
    skill = effective_rating(passer, "Technique") if backheel else effective_rating(passer, "Passing")
    sigma = math.radians(_linear(skill, PASS_SIGMA_DEG_POINTS))
    sigma *= 1.0 + PASS_PRESSURE_SIGMA_GAIN * pressure(passer, opponents) * composure_factor(passer)
    if backheel:
        sigma *= BACKHEEL_SIGMA_FACTOR
    return sigma / one_touch_precision(passer) if one_touch else sigma


def pass_speed_sigma(passer: PlayerState) -> float:
    """Écart-type de l'erreur de vitesse de départ, en part de la vitesse idéale, selon le dosage (ticket 23a)."""
    return PASS_SPEED_SIGMA[0] + (PASS_SPEED_SIGMA[1] - PASS_SPEED_SIGMA[0]) * dosage_quality(passer)


def _receiver_travel_s(passer: PlayerState, target: PlayerState) -> float:
    """Temps de vol (s) d'une passe dosée pour arriver à `IDEAL_ARRIVAL_MPS` au receveur (plafond `MAX_PASS_MPS`)."""
    distance = passer.position.distance_to(target.position)
    speed = _launch_speed(distance)
    log_f = math.log(BALL_FRICTION_PER_S)
    arrival = max(BALL_STOPPED_MPS, speed + distance * log_f)  # < 6 m/s si la vitesse est plafonnée (passe > ~47 m)
    return math.log(arrival / speed) / log_f


def dosage_gap(passer: PlayerState, receiver: PlayerState) -> tuple[float, float]:
    """Écart (m) entre le point visé par la passe idéale (`pass_aim`) et la position future du receveur, qui court à sa
    vitesse pendant le vol : la part de sa course que le dosage ne joue pas (ticket v2-realisme/23a, piste b de la
    clôture : un passeur faible joue dans les pieds d'un receveur lancé). Rendu en (composante dans l'axe de la passe,
    composante en travers), dans le repère passeur -> point visé."""
    gap = receiver.velocity * (_receiver_travel_s(passer, receiver) * (1.0 - dosage_quality(passer)))
    axis = pass_aim(passer, receiver) - passer.position
    if axis.length() < 1e-9:
        return gap.length(), 0.0
    axis = axis.normalized()
    return gap.x * axis.x + gap.y * axis.y, axis.x * gap.y - axis.y * gap.x


def _aim_distance(passer: PlayerState, receiver: PlayerState) -> float:
    """Distance (m) du passeur au point visé par la passe idéale : là où l'écart d'angle se lit en mètres (au moins
    `ON_TARGET_M`)."""
    return max(passer.position.distance_to(pass_aim(passer, receiver)), ON_TARGET_M)


def _within(limit: float, along: float, across: float, length: float, sigma: float) -> float:
    """Chance que le ballon passe à moins de `limit` de la position future du receveur : écart du dosage (`along`,
    `across`) plus l'écart latéral de la loi d'angle (gaussienne d'écart-type `sigma` rad, lu à `length`, la distance du
    point visé)."""
    if math.isinf(limit):
        return 1.0
    if abs(along) >= limit:
        return 0.0
    half = math.sqrt(limit * limit - along * along)  # demi-largeur de la tranche de passage autour du receveur
    scale = sigma * math.sqrt(2.0)
    return 0.5 * (math.erf(math.atan((half - across) / length) / scale)
                  + math.erf(math.atan((half + across) / length) / scale))


def pass_accuracy_probability(passer: PlayerState, receiver: PlayerState, opponents: Sequence[PlayerState],
                              backheel: bool = False, one_touch: bool = False, lofted: bool = False) -> float:
    """Chance que la passe arrive précise (ticket v2-realisme/23a) : au sol, le ballon passe à moins de `ON_TARGET_M` de
    la position future du receveur (écart du dosage, `dosage_gap`, plus l'écart latéral tiré par la loi d'angle,
    `pass_error_sigma_rad`) ; en l'air, son écart latéral reste sous `LOFTED_ON_TARGET_M`. Une seule loi, lue par la
    décision et par la résolution."""
    tolerance = LOFTED_ON_TARGET_M if lofted else ON_TARGET_M
    sigma = pass_error_sigma_rad(passer, opponents, backheel, one_touch)
    if lofted:
        length = max(passer.position.distance_to(receiver.position), tolerance)
        return math.erf(math.atan(tolerance / length) / (sigma * math.sqrt(2.0)))
    along, across = dosage_gap(passer, receiver)
    return _within(tolerance, along, across, _aim_distance(passer, receiver), sigma)


def pass_success_probability(passer: PlayerState, receiver: PlayerState, opponents: Sequence[PlayerState],
                             backheel: bool = False, one_touch: bool = False, lofted: bool = False) -> float:
    """Chance que la passe ne soit pas perdue (tickets v2-realisme/18g et 18h) : aucun adversaire ne touche le ballon le
    premier, et le ballon ne sort pas (ni n'est sifflé) avec remise pour l'adversaire ; même risque que celui que la passe
    court en jeu. C'est le sens que lui donne la décision (`decision.option_value` :
    garder, sinon perdre le ballon), comme le risque de perte de la conduite (04a). Coupe par adversaire : table du 18n (distance, temps du ballon) ;
    au sol, part non perdue selon l'écart à l'arrivée à la position future du receveur (`_LATERAL_NOT_LOST`, bandes de la
    loi d'écart et du dosage, ticket v2-realisme/23a). Le contrôle du receveur n'y entre
    pas : raté, le ballon reste libre près de lui, ce n'est pas une perte. `lofted` : passe longue en l'air (ticket
    v2-collectif/15a), que personne ne touche en vol : ni coupe ni coupe imprévue, seule la précision compte ; la
    retombée disputée n'y entre pas (`decision.LONG_BALL_WON`)."""
    if lofted:
        accurate = pass_accuracy_probability(passer, receiver, opponents, lofted=True)
        return accurate + (1.0 - accurate) * LOFTED_MISS_NOT_LOST
    length = _aim_distance(passer, receiver)
    keep = 1.0
    for opponent in opponents:
        keep *= 1.0 - _cut_chance(passer.position, receiver.position, opponent)
    sigma = pass_error_sigma_rad(passer, opponents, backheel, one_touch)
    along, across = dosage_gap(passer, receiver)
    not_lost, below = 0.0, 0.0
    for limit, share in _LATERAL_NOT_LOST:
        within = _within(limit, along, across, length, sigma)
        not_lost += (within - below) * share
        below = within
    return keep * not_lost


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


def max_pass_reach_m() -> float:
    """Distance la plus longue qu'une passe frappée au plafond (`MAX_PASS_MPS`) parcourt avant d'être morte
    (`BALL_STOPPED_MPS`) : environ 58 m."""
    return (MAX_PASS_MPS - BALL_STOPPED_MPS) / -math.log(BALL_FRICTION_PER_S)


def pass_aim(passer: PlayerState, target: PlayerState) -> Vec2:
    """Point visé par la passe IDÉALE de `passer` vers `target` : là où le receveur VA être, d'autant plus précisément que
    le dosage est bon (lecture du jeu, pas une erreur d'exécution ; ticket v2-realisme/23a). L'erreur d'exécution est
    tirée par `pass_velocity`."""
    lead_s = _receiver_travel_s(passer, target) * dosage_quality(passer)
    return target.position + target.velocity * lead_s  # dans la course, selon le dosage


def pass_velocity(passer: PlayerState, target: PlayerState, opponents: Sequence[PlayerState] = (),
                  backheel: bool = False, one_touch: bool = False, lofted: bool = False) -> Vec2:
    """Vitesse du ballon au départ d'une passe (ticket v2-realisme/23a) : vers la passe idéale (`pass_aim`), de quoi y
    arriver à ~6 m/s (plafond 30 m/s), écartée d'un angle gaussien (`pass_error_sigma_rad`) et d'une erreur de vitesse
    gaussienne (`pass_speed_sigma`), vitesse bornée à [0 ; `MAX_PASS_MPS`]. `lofted` ne change pas l'écart : la passe
    longue en l'air n'a de propre que sa tolérance d'arrivée (`LOFTED_ON_TARGET_M`)."""
    aim = pass_aim(passer, target)
    direction = (aim - passer.position).normalized()
    if direction.length() < 1e-9:
        direction = Vec2(1.0, 0.0)  # receveur sur le passeur : direction fixe
    angle = PASSE.gauss(0.0, pass_error_sigma_rad(passer, opponents, backheel, one_touch))
    cos_a, sin_a = math.cos(angle), math.sin(angle)
    heading = Vec2(direction.x * cos_a - direction.y * sin_a, direction.x * sin_a + direction.y * cos_a)
    ideal = _launch_speed(passer.position.distance_to(aim))
    speed = min(MAX_PASS_MPS, max(0.0, ideal * (1.0 + PASSE.gauss(0.0, pass_speed_sigma(passer)))))
    return heading * speed


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

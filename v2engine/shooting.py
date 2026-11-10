"""Tirs et gardien (Phase 4, docs/PLAN_V2.md) : un porteur du ballon proche du but adverse tente
sa chance -- qualité de l'occasion (angle entre les poteaux, distance, défenseurs dans le cône, position du
gardien, pression, ticket v2-collectif/28a), exécution par Finishing (surface) ou Long Shots (dehors) contre
Reflexes/One on Ones/Handling (gardien), voir `shot_probability`. Jalon
du premier plan (US-29) : à la fin de cette phase, un score émerge entièrement du moteur, plus
aucun résultat décidé à l'avance (IA de décision placeholder, D-V08 : un porteur à portée tente
toujours sa chance, pas de lecture tactique de quand tirer)."""

from __future__ import annotations

import math
from dataclasses import replace
from types import MappingProxyType

from ligue1sim.pitch_geometry import GOAL_HEIGHT_M, GOAL_WIDTH_M

from v2engine.attributes import duel_probability, success_probability
from v2engine.condition import effective_rating
from v2engine.flux import TIR
from v2engine.geometry import Vec2, in_penalty_area
from v2engine.movement import PlayerState
from v2engine.possession import BALL_FRICTION_PER_S, MAX_PASS_MPS

# Distance de tir maximale (m) : au-delà, l'option « tirer » n'existe pas pour le porteur (voir
# `decision.py`, qui choisit QUAND tirer). Constante validée par le propriétaire (24/10/2026,
# ticket v2-cerveau-joueurs/01, 20 m auparavant).
SHOOTING_RANGE_M = 30.0
# Qualité de l'occasion (ticket v2-collectif/28a, révisé le 05/11/2026 après la recherche du propriétaire, validé par
# délégation) : chance de but d'un tir non contré, tireur et gardien moyens, gardien bien placé. Forme classique d'un
# modèle xG (logit en angle entre les poteaux, distance au centre du but et distance au carré), ajustée sur la table
# cible du propriétaire (6 m 0,33-0,40 ; 11 m 0,15-0,20 ; 16 m 0,08-0,11 ; 20 m 0,04-0,06 ; 25 m 0,025-0,04 ; 30 m
# 0,015-0,025 ; angle très fermé à 8-10 m 0,03-0,08). La moyenne des deux modèles publiés de Soccermatics (Wyscout PL
# 2017-18) donnait 0,127 en angle fermé, et aucune repondération des deux ne tenait toute la table. Face au but :
# 37 % à 6 m, 15 % à 11 m, 9 % à 16 m, 6 % à 20 m, 3 % à 25 m, 2 % à 30 m ; 7 % à 2 m de la ligne et 8 m du centre.
_XG_LOGIT = (-3.3608, 2.5068, 0.0303, -0.0023)  # constante, x angle (rad), x distance (m), x distance²

_MIN_SHOT_PROBABILITY = 0.01
_MAX_SHOT_PROBABILITY = 0.9

# Pression sur le tir (ticket 28a, révisé le 05/11/2026 ; StatsBomb, « Closing down: how defensive pressure impacts
# shots », environ 65 % des tirs sous pression) : un défenseur de champ ne gêne le tir que dans le rayon
# 0,15 x distance au but + 0,85 m (au plus `SHOT_PRESSURE_RADIUS_MAX_M`). Part de la chance perdue selon la distance du
# plus proche : `SHOT_PRESSURE_TIERS` ; moitié s'il est dans le dos du tireur (non trouvé : ordre de grandeur). Le
# défenseur dans l'axe du tir compte déjà dans le contre : les paliers ne dépendent pas de l'axe (pas de double
# comptage). Composure (`shot_composure_factor`, courbe propre au tir) : 99 récupère un tiers de la pénalité.
SHOT_PRESSURE_RADIUS = (0.15, 0.85)
SHOT_PRESSURE_RADIUS_MAX_M = 4.5
SHOT_PRESSURE_TIERS = ((1.0, 0.40), (2.0, 0.25), (3.5, 0.10))
SHOT_PRESSURE_BEHIND = 0.5

# Exécution (ticket 28a, révisé le 05/11/2026) : rapport d'environ 1,3 entre un tireur à 99 et un tireur moyen
# (repère : Messi, +21 % sur sa carrière, arXiv 2301.13052, un maximum) : racine du duel contre un gardien neutre.
# La part du gardien (A8) reste celle du duel, à part, inchangée jusqu'au ticket v2-attributs-restants/03b.
SHOOTER_SKILL_EXPONENT = 0.5

# Gardien (ticket 28a, portée réelle non trouvée, ordre de grandeur) : il couvre `KEEPER_REACH_M` de part et d'autre
# de lui. Placé à `KEEPER_REFERENCE_M` devant sa ligne dans l'axe du tir, il donne la chance du modèle publié ; avancé,
# il ferme l'angle et la chance baisse ; hors de position, elle monte (part du but qu'il laisse ouverte). Même en
# couvrant tout l'angle (tir en angle fermé, gardien au premier poteau), sa position seule n'arrête que
# `KEEPER_COVER_MAX` des tirs (réel non trouvé) : sans cette limite, un but vide en angle fermé valait l'infini.
# Un but laissé vide vaut au plus `KEEPER_OPEN_GOAL_MAX` fois la chance de base (propriétaire : 2 à 3 fois).
KEEPER_REACH_M = 1.5
KEEPER_REFERENCE_M = 1.0
KEEPER_COVER_MAX = 0.8
KEEPER_OPEN_GOAL_MAX = 2.5

# Tir contré (ticket v2-collectif/33, cône au ticket 28a ; validé par délégation du propriétaire) : un défenseur de champ
# entre le tireur et le but cache la part du but que couvre son corps, `BLOCK_WIDTH_M` de part et d'autre (jambe tendue
# plus ballon) ; il contre le tir avec la chance `BLOCK_CHANCE` x cette part (le tir vise un point du but au hasard).
# Chaque défenseur tire sa chance, du plus proche du tireur au plus loin. Même règle pour décider et pour résoudre.
# Réel : 20 à 28 % des tirs contrés (ordre de grandeur, ticket 28) ; 22,5 % en Bundesliga 2015-16 (189 sur 840).
BLOCK_WIDTH_M = 1.0
BLOCK_CHANCE = 0.6
# Contre physique (ticket v2-realisme/05c, proposé le 09/11/2026, validé par délégation du propriétaire) : le tir en vol
# touche un défenseur de champ qui passe à sa portée ; avant `BLOCK_REACTION_S` après la frappe, il n'a pas le temps de
# tendre la jambe et seul son corps compte (`BLOCK_BODY_M`, la portée du contact ballon-joueur) ; ensuite, jambe tendue,
# `BLOCK_WIDTH_M`. Au contact, il contre avec la chance `BLOCK_CHANCE` (sinon le ballon passe : entre les jambes, jambe
# trop courte). Le cône de la décision (`block_probability`) reste l'estimateur jusqu'au 05e. Temps de réaction d'un
# défenseur sur un tir : non trouvé ; 0,25 s d'abord (ordre du gardien) donnait 12,5 % de tirs contrés sur 50 matchs,
# 0,10 s (il fait face au tireur, lit la frappe et engage la jambe tôt) est recalé hors ligne sur 1 074 tirs de 24 matchs
# vers le repère réel de 22,5 % (21 % estimé).
BLOCK_BODY_M = 0.41
BLOCK_REACTION_S = 0.10

# Repli neutre (gardien absent -- effectif synthétique sans gardien, voir docs/PLAN_V2.md
# Phase 1) : proche de la moyenne réelle de la base (voir `attributes.player_attribute`).
_NEUTRAL_KEEPER_RATING = 60.0


def _keeper_rating(keeper: PlayerState | None) -> float:
    if keeper is None:
        return _NEUTRAL_KEEPER_RATING
    return (
        0.5 * effective_rating(keeper, "Reflexes")
        + 0.3 * effective_rating(keeper, "One on Ones")
        + 0.2 * effective_rating(keeper, "Handling")
    )


def _relative(origin: Vec2, axis: Vec2, point: Vec2) -> float:
    """Angle (rad) de `point` vu depuis `origin`, relatif à la direction `axis`."""
    offset = point - origin
    return math.atan2(axis.x * offset.y - axis.y * offset.x, axis.x * offset.x + axis.y * offset.y)


def _goal_angle(origin: Vec2, goal: Vec2) -> tuple[float, float, Vec2]:
    """Bornes de l'angle sous lequel `origin` voit le but entre les poteaux, relatives à l'axe vers le centre du but,
    et cet axe."""
    axis = (goal - origin).normalized()
    posts = (Vec2(goal.x, goal.y - GOAL_WIDTH_M / 2.0), Vec2(goal.x, goal.y + GOAL_WIDTH_M / 2.0))
    low, high = sorted(_relative(origin, axis, post) for post in posts)
    return low, high, axis


def _covered_share(origin: Vec2, goal: Vec2, body: Vec2, half_width_m: float) -> float:
    """Part de l'angle du but cachée par un corps en `body` (`half_width_m` de part et d'autre), vue depuis `origin` ;
    0 s'il n'est pas entre `origin` et le but."""
    low, high, axis = _goal_angle(origin, goal)
    offset = body - origin
    along = offset.x * axis.x + offset.y * axis.y
    if high <= low or not 0.0 < along < origin.distance_to(goal):
        return 0.0
    centre, half = _relative(origin, axis, body), math.atan(half_width_m / offset.length())
    return max(0.0, min(high, centre + half) - max(low, centre - half)) / (high - low)


def base_chance(origin: Vec2, goal: Vec2) -> float:
    """Chance de but d'un tir non contré depuis `origin`, tireur et gardien moyens, gardien bien placé."""
    low, high, _ = _goal_angle(origin, goal)
    distance = origin.distance_to(goal)
    logit = _XG_LOGIT[0] + _XG_LOGIT[1] * (high - low) + _XG_LOGIT[2] * distance + _XG_LOGIT[3] * distance ** 2
    return 1.0 / (1.0 + math.exp(-logit))


def keeper_position_factor(origin: Vec2, goal: Vec2, keeper: PlayerState | None) -> float:
    """Part du but laissée ouverte par le gardien, rapportée à celle d'un gardien bien placé (`KEEPER_REFERENCE_M`).
    Sans gardien identifiable (effectif synthétique) : 1, repli neutre."""
    if keeper is None:
        return 1.0
    # ponytail: la position du gardien est une part d'angle couverte, sans temps de réaction ni plongeon ; arrêts et
    # sorties du gardien aux tickets 28b et v2-attributs-restants/03b
    reference = goal + (origin - goal).normalized() * KEEPER_REFERENCE_M
    open_now = 1.0 - KEEPER_COVER_MAX * _covered_share(origin, goal, keeper.position, KEEPER_REACH_M)
    open_ref = 1.0 - KEEPER_COVER_MAX * _covered_share(origin, goal, reference, KEEPER_REACH_M)
    return min(KEEPER_OPEN_GOAL_MAX, open_now / open_ref)


def shot_composure_factor(shooter: PlayerState) -> float:
    """Part de la pénalité de pression qui reste après Composure, courbe propre au tir : 99 -> 2/3, 55 -> 5/6, 11 -> 1."""
    return 5.0 / 3.0 - success_probability(effective_rating(shooter, "Composure"), baseline=5.0 / 6.0,
                                           amplitude=1.0 / 6.0, min_prob=2.0 / 3.0, max_prob=1.0)


def shot_pressure(shooter: PlayerState, goal: Vec2, opponents: list[PlayerState]) -> float:
    """Part de la chance perdue sous la pression du défenseur de champ le plus proche, avant Composure (0 à 0,4)."""
    field = [o for o in opponents if o.poste != "GK"]
    if not field:
        return 0.0
    nearest = min(field, key=lambda o: shooter.position.distance_to(o.position))
    gap = shooter.position.distance_to(nearest.position)
    radius = min(SHOT_PRESSURE_RADIUS_MAX_M,
                 SHOT_PRESSURE_RADIUS[0] * shooter.position.distance_to(goal) + SHOT_PRESSURE_RADIUS[1])
    if gap > radius:
        return 0.0
    penalty = next((loss for limit, loss in SHOT_PRESSURE_TIERS if gap < limit), 0.0)
    toward_goal, toward_marker = goal - shooter.position, nearest.position - shooter.position
    if toward_goal.x * toward_marker.x + toward_goal.y * toward_marker.y < 0.0:
        penalty *= SHOT_PRESSURE_BEHIND
    return penalty


def shooting_note(shooter: PlayerState) -> int:
    """Exécution du tir (ticket 28a) : Finishing dans la surface de réparation, Long Shots en dehors, jamais les deux."""
    if in_penalty_area(shooter.team, shooter.position):
        return effective_rating(shooter, "Finishing")
    return effective_rating(shooter, "Long Shots")


def shot_probability(shooter: PlayerState, goal: Vec2, keeper: PlayerState | None,
                     opponents: list[PlayerState]) -> float:
    """Chance qu'un tir de `shooter` vers `goal` (centre du but) devienne un but s'il n'est pas contré (ticket 28a) :
    chance de l'endroit, exécution du tireur (Finishing ou Long Shots) contre le gardien (A8), position du gardien,
    pression subie (amortie par Composure seulement). Jamais garantie, jamais nulle."""
    skill = (duel_probability(shooting_note(shooter), _NEUTRAL_KEEPER_RATING) / 0.5) ** SHOOTER_SKILL_EXPONENT
    skill *= duel_probability(_NEUTRAL_KEEPER_RATING, _keeper_rating(keeper)) / 0.5
    pressed = 1.0 - shot_pressure(shooter, goal, opponents) * shot_composure_factor(shooter)
    chance = base_chance(shooter.position, goal) * skill * keeper_position_factor(shooter.position, goal, keeper)
    return max(_MIN_SHOT_PROBABILITY, min(_MAX_SHOT_PROBABILITY, chance * pressed))


def occasion_quality(player: PlayerState, goal: Vec2, keeper: PlayerState | None,
                     opponents: list[PlayerState]) -> float:
    """« S'il touchait le ballon ici, quelle serait sa chance de marquer ? » (ticket 28a) : chance de but d'un tir
    depuis sa position, contres compris. Vaut pour un joueur qui ne tire pas.
    Depuis le ticket v2-realisme/05e, calculée avec les lois de la résolution physique (`_flight_shares`), plus avec la
    formule analytique et le cône."""
    # but et contre se jugent ensemble, écart par écart : un défenseur dans l'axe contre surtout des tirs qui allaient au
    # but, un défenseur devant le gardien surtout des tirs que le gardien aurait arrêtés
    return (1.0 - _shank_share(player, goal, opponents)) * _flight_shares(player, goal, keeper, opponents)[2]


def attempt_shot(shooter: PlayerState, goal: Vec2, keeper: PlayerState | None, opponents: list[PlayerState]) -> bool:
    """`True` si le tir (non contré) devient un but."""
    return TIR.random() < shot_probability(shooter, goal, keeper, opponents)


def _blockers(shooter: PlayerState, goal: Vec2, opponents: list[PlayerState]) -> list[tuple[PlayerState, float]]:
    """Défenseurs de champ dans le cône de tir et leur chance de contrer, du plus proche du tireur au plus loin."""
    found = []
    for opponent in opponents:
        if opponent.poste == "GK":
            continue
        share = _covered_share(shooter.position, goal, opponent.position, BLOCK_WIDTH_M)
        if share > 0.0:
            found.append((shooter.position.distance_to(opponent.position), opponent, BLOCK_CHANCE * share))
    return [(o, c) for _, o, c in sorted(found, key=lambda t: t[0])]


def block_probability(shooter: PlayerState, goal: Vec2, opponents: list[PlayerState]) -> float:
    """Chance que le tir soit contré par au moins un défenseur de la ligne de tir."""
    through = 1.0
    for _, chance in _blockers(shooter, goal, opponents):
        through *= 1.0 - chance
    return 1.0 - through


def block_reach_m(elapsed_s: float) -> float:
    """Portée d'un défenseur sur un tir en vol (ticket v2-realisme/05c), `elapsed_s` après la frappe : son corps avant
    `BLOCK_REACTION_S`, jambe tendue ensuite."""
    return BLOCK_BODY_M if elapsed_s < BLOCK_REACTION_S else BLOCK_WIDTH_M


# Cadrage du tir (ticket v2-collectif/35b, constantes proposées le 08/11/2026, validées par délégation du propriétaire).
# Le tireur vise le centre du but, à `SHOT_AIM_HEIGHT_M` du sol ; le ballon s'en écarte d'un angle gaussien (écart-type
# `SHOT_ERROR_SIGMA_RAD`, le même en largeur et en hauteur) : il est cadré s'il reste entre les poteaux et sous la barre,
# à la distance du tir. Ce ticket ne change PAS la chance de but (`shot_probability`, déjà portée par Finishing ou Long Shots
# et la pression) : il décompose le tir non converti en cadré (arrêté), à côté, au-dessus ou dévissé, avec
# P(but) = P(cadré) x P(but | cadré). La note et la pression jouent donc une seule fois sur le but ; elles règlent ici
# l'écart du ballon, donc la part de tirs ratés. Réel : 37,6 % des tirs cadrés en moyenne (CIES Football Observatory,
# données InStat 2018-19), précision plus faible à grande distance ; part de tirs cadrés par distance, écart d'angle
# du tireur et part de dévissés : non trouvés. Écart d'angle réglé sur le repère de 30 à 35 % de tirs cadrés (28b) : 0,18 rad (10°) donne 32,2 % sur 798 tirs
# de 16 matchs, 26 % à côté, 21 % au-dessus, 2,4 % dévissés (grille de 0,08 à 0,24 rad et 0,6 à 1,22 m de hauteur de visée
# dans `.scratch/v2-collectif/mesures/35b-calib.py`) ;
# pression : écart augmenté de `SHOT_ERROR_PRESSURE_GAIN` x la pénalité de pression (0 à 0,4, Composure comprise) ;
# dévissé : `SHANK_SHARE` des tirs ratés pour un tireur moyen sans pression, proportionnel au carré de l'écart (donc
# plus fréquent à note basse et sous pression, jamais nul), ballon à `SHANK_SPEED_SHARE` de la vitesse du tir, parti
# à `SHANK_ANGLE_DEG` de l'axe du but d'un côté tiré au hasard (parfois en touche). Les tirs au-dessus ne prennent leur
# vraie trajectoire qu'avec `v2-hauteur-ballon/02a` : l'issue est tracée, rejouée à plat comme un tir à côté.
CADRE, WIDE, OVER, SHANKED = "cadré", "à côté", "au-dessus", "dévissé"
SHOT_ERROR_SIGMA_RAD = 0.18
SHOT_AIM_HEIGHT_M = 1.0  # visée à 1 m du sol (coins bas, ballon rasant ; hauteur de visée réelle non trouvée)
SHOT_ERROR_PRESSURE_GAIN = 1.0
SHANK_SHARE = 0.04
SHANK_SPEED_SHARE = 0.4
SHANK_ANGLE_DEG = (40.0, 90.0)


def shot_error_sigma(shooter: PlayerState, goal: Vec2, opponents: list[PlayerState]) -> float:
    """Écart-type (rad) de l'écart du ballon à la visée : plus petit pour une bonne note, plus grand sous pression."""
    skill = (duel_probability(shooting_note(shooter), _NEUTRAL_KEEPER_RATING) / 0.5) ** SHOOTER_SKILL_EXPONENT
    pressure = shot_pressure(shooter, goal, opponents) * shot_composure_factor(shooter)
    return SHOT_ERROR_SIGMA_RAD * (1.0 + SHOT_ERROR_PRESSURE_GAIN * pressure) / skill


def _inside(half_angle: float, sigma: float) -> float:
    """Chance qu'un écart gaussien d'écart-type `sigma` reste dans ±`half_angle`."""
    return math.erf(half_angle / (sigma * math.sqrt(2.0)))


def on_target_axes(shooter: PlayerState, goal: Vec2, opponents: list[PlayerState]) -> tuple[float, float]:
    """Chance de rester entre les poteaux et chance de rester sous la barre (visée au centre du but, à `SHOT_AIM_HEIGHT_M`).
    Vers le bas, le sol ne fait pas rater le cadre : seul l'écart vers le haut compte pour la hauteur."""
    low, high, _ = _goal_angle(shooter.position, goal)
    sigma = shot_error_sigma(shooter, goal, opponents)
    height = math.atan2(GOAL_HEIGHT_M - SHOT_AIM_HEIGHT_M, shooter.position.distance_to(goal))
    return _inside((high - low) / 2.0, sigma), 0.5 * (1.0 + _inside(height, sigma))


def classify_unscored(shooter: PlayerState, goal: Vec2, keeper: PlayerState | None,
                      opponents: list[PlayerState]) -> str:
    """Issue d'un tir non contré qui n'a pas marqué : `CADRE` (le gardien l'arrête), `WIDE`, `OVER` ou `SHANKED`. Tirage
    conditionnel au non-but : P(cadré sans but) = (cadré - but) / (1 - but)."""
    chance = shot_probability(shooter, goal, keeper, opponents)
    wide, high = on_target_axes(shooter, goal, opponents)
    on_target = max(wide * high, chance)
    if TIR.random() < (on_target - chance) / (1.0 - chance):
        return CADRE
    sigma_ratio = shot_error_sigma(shooter, goal, opponents) / SHOT_ERROR_SIGMA_RAD
    if TIR.random() < SHANK_SHARE * sigma_ratio ** 2:
        return SHANKED
    # ponytail: ballon raté en largeur ou en hauteur, part des deux axes supposée indépendante ; vraie hauteur avec
    # v2-hauteur-ballon/02a
    over_share = (1.0 - high) / max(1e-9, (1.0 - wide) + (1.0 - high))
    return OVER if TIR.random() < over_share else WIDE


FLYING = "en vol"  # issue provisoire d'un tir en vol dans la trace, remplacée quand il est arrêté ou franchit la ligne

# Arrêt par portée (ticket v2-realisme/05b, constantes proposées le 08/11/2026, validées par délégation du propriétaire ;
# gardien neutre, ses notes viennent au v2-attributs-restants/03b). Quand le ballon passe au plus près de lui, le gardien
# l'atteint si l'écart est dans sa portée à cet instant : `KEEPER_STANDING_REACH_M` sans plonger (corps et bras), puis,
# après `KEEPER_REACTION_S`, il gagne `KEEPER_DIVE_MPS` jusqu'à `KEEPER_DIVE_REACH_M`. Ordres de grandeur, chiffres réels
# non trouvés (temps de réaction d'un gardien sur tir, portée et durée d'un plongeon). Réglage du 05h (09/11/2026,
# validé par délégation) : réaction 0,25 -> 0,30 s et plongeon 4,0 -> 3,0 m/s, recalés hors ligne sur 1 103 tirs de 24
# matchs (temps de vol et écart au gardien tracés) vers le repère d'environ 70 % d'arrêts des tirs cadrés (77 à 80 %
# avant) ; à reprendre avec la puissance de frappe (`v2-collectif/35a`), qui rendra les tirs plus rapides.
KEEPER_REACTION_S = 0.30
KEEPER_STANDING_REACH_M = 1.0
KEEPER_DIVE_REACH_M = 2.8
KEEPER_DIVE_MPS = 3.0


def keeper_reach_m(elapsed_s: float) -> float:
    """Portée latérale du gardien (m) `elapsed_s` après la frappe."""
    dive = KEEPER_DIVE_MPS * max(0.0, elapsed_s - KEEPER_REACTION_S)
    return min(KEEPER_DIVE_REACH_M, KEEPER_STANDING_REACH_M + dive)


_ENGINE_TICK_S = 0.1  # pas de la boucle de match (`match.TICK_SECONDS`, égalité gardée par un test)


def _flight_time_s(distance_m: float) -> float:
    """Temps (s) que met un tir à parcourir `distance_m` dans la boucle de match : le ballon avance de sa vitesse à
    chaque pas, puis freine (`BALL_FRICTION_PER_S`) ; l'infini s'il s'arrête avant."""
    q = BALL_FRICTION_PER_S ** _ENGINE_TICK_S
    rest = 1.0 - distance_m * (1.0 - q) / (MAX_PASS_MPS * _ENGINE_TICK_S)
    return math.inf if rest <= 0.0 else _ENGINE_TICK_S * math.log(rest) / math.log(q)


def _flight_distance_m(elapsed_s: float) -> float:
    """Distance (m) parcourue par un tir au bout de `elapsed_s`, pas entiers de la boucle de match (inverse de
    `_flight_time_s`)."""
    q = BALL_FRICTION_PER_S ** _ENGINE_TICK_S
    return MAX_PASS_MPS * _ENGINE_TICK_S * (1.0 - q ** (elapsed_s / _ENGINE_TICK_S)) / (1.0 - q)


def _keeper_cover(origin: Vec2, goal: Vec2, axis: Vec2, keeper_at: Vec2) -> tuple[float, float] | tuple[()] | None:
    """Angles (relatifs à `axis`) des tirs que le gardien atteint : ceux qui traversent sa portée avant la ligne de but,
    soit le disque de portée coupé par la ligne, vu du tireur (`match._keeper_reaches` mesure l'écart au plus près du
    gardien, ou sur la ligne si le ballon la franchit avant). Chaque bord a sa portée, au temps de vol jusqu'au point
    de passage (tangence ou ligne de but). `()` : aucun ; `None` : tous (tireur dans sa portée)."""
    offset = keeper_at - origin
    distance, along = offset.length(), offset.x * axis.x + offset.y * axis.y
    if distance <= keeper_reach_m(0.0):
        return None
    if along <= 0.0:
        return ()  # gardien derrière le tireur, hors de portée : le ballon s'éloigne de lui
    side = 1.0 if origin.x > goal.x else -1.0  # côté terrain de la ligne de but
    centre, depth = _relative(origin, axis, keeper_at), keeper_at.x - goal.x
    angles = []
    for sign in (-1.0, 1.0):
        reach = keeper_reach_m(_flight_time_s(distance))
        for _ in range(3):  # portée au temps de vol jusqu'au point de tangence (point fixe, converge vite)
            reach = keeper_reach_m(_flight_time_s(math.sqrt(max(0.0, distance * distance - reach * reach))))
        if reach >= distance:
            return None
        turn = centre + sign * math.asin(reach / distance)
        heading = Vec2(axis.x * math.cos(turn) - axis.y * math.sin(turn), axis.x * math.sin(turn) + axis.y * math.cos(turn))
        if (origin.x + heading.x * math.sqrt(distance * distance - reach * reach) - goal.x) * side >= 0.0:
            angles.append(turn)  # tangence encore devant la ligne
        reach = keeper_reach_m(_flight_time_s(distance))
        for _ in range(3):  # bord de la portée sur la ligne de but, au temps de vol jusqu'à lui
            if abs(depth) >= reach:
                break
            point = Vec2(goal.x, keeper_at.y + sign * math.sqrt(reach * reach - depth * depth))
            reach = keeper_reach_m(_flight_time_s(origin.distance_to(point)))
        if abs(depth) < reach:
            angles.append(_relative(origin, axis, Vec2(goal.x, keeper_at.y + sign * math.sqrt(reach * reach - depth * depth))))
    return (min(angles), max(angles)) if angles else ()


def _shank_share(shooter: PlayerState, goal: Vec2, opponents: list[PlayerState]) -> float:
    """Part des tirs dévissés (`draw_shot_error`) : ils ne partent pas en vol, ni contrés ni cadrés."""
    wide, under = on_target_axes(shooter, goal, opponents)
    return SHANK_SHARE * (shot_error_sigma(shooter, goal, opponents) / SHOT_ERROR_SIGMA_RAD) ** 2 * (1.0 - wide * under)


def _block_covers(shooter: PlayerState, goal: Vec2, opponents: list[PlayerState]) -> list[tuple[float, float]]:
    """Écarts de tir (angles relatifs à l'axe vers le centre du but) qui passent à la portée de chaque défenseur de champ
    devant le tireur (contre physique, `match._blocked`) : à sa place quand le ballon arrive à lui (il garde sa vitesse),
    portée `block_reach_m` au temps de vol ; tout l'angle s'il est déjà au contact du tireur. Approximation : la portée
    est prise sur la ligne joueur-tireur."""
    axis = (goal - shooter.position).normalized()
    to_goal = shooter.position.distance_to(goal)
    covers = []
    for opponent in opponents:
        if opponent.poste == "GK":
            continue
        at = opponent.position
        elapsed = math.inf
        for _ in range(2):  # temps jusqu'à sa place à l'arrivée du ballon
            elapsed = _flight_time_s(shooter.position.distance_to(at))
            if math.isinf(elapsed):
                break
            at = opponent.position + opponent.velocity * elapsed
        if math.isinf(elapsed):
            continue
        offset = at - shooter.position
        along, gap = offset.x * axis.x + offset.y * axis.y, offset.length()
        reach = block_reach_m(elapsed)
        if gap <= reach:
            covers.append((-math.inf, math.inf))
        elif 0.0 < along <= to_goal:  # devant le tireur, avant le but
            centre, half = _relative(shooter.position, axis, at), math.asin(reach / gap)
            if elapsed < BLOCK_REACTION_S:
                # la boucle de match juge le contact pas par pas : au premier pas où il tend la jambe, le ballon déjà passé
                # peut encore être à sa portée (`BLOCK_WIDTH_M`) ; écarts qui l'y mettent, à la distance parcourue alors
                ready = _flight_distance_m(math.ceil(BLOCK_REACTION_S / _ENGINE_TICK_S - 1e-9) * _ENGINE_TICK_S)
                cosine = (ready * ready + gap * gap - BLOCK_WIDTH_M * BLOCK_WIDTH_M) / (2.0 * ready * gap)
                if cosine < 1.0:
                    half = max(half, math.acos(max(-1.0, cosine)))
            covers.append((centre - half, centre + half))
    return covers


def _goal_angles(shooter: PlayerState, goal: Vec2, keeper: PlayerState | None) -> list[tuple[float, float]]:
    """Écarts de tir qui donnent un but en largeur : l'angle du but privé de l'angle que couvre le gardien
    (`_keeper_cover`). Sans gardien identifiable (effectif synthétique), repli neutre comme `keeper_position_factor` :
    gardien bien placé, à `KEEPER_REFERENCE_M` de sa ligne sur l'axe du tir."""
    low, high, axis = _goal_angle(shooter.position, goal)
    keeper_at = keeper.position if keeper is not None else goal + (shooter.position - goal).normalized() * KEEPER_REFERENCE_M
    covered = _keeper_cover(shooter.position, goal, axis, keeper_at)
    if covered is None:
        return []  # le ballon passe forcément à sa portée
    if not covered or covered[1] <= low or covered[0] >= high:
        return [(low, high)]
    return [(lo, hi) for lo, hi in ((low, covered[0]), (covered[1], high)) if hi > lo]


def _flight_shares(shooter: PlayerState, goal: Vec2, keeper: PlayerState | None,
                   opponents: list[PlayerState]) -> tuple[float, float, float]:
    """Tir en vol (non dévissé), écart en largeur gaussien (`shot_error_sigma`) : (chance de but sans les contres, chance
    d'être contré, chance de but et de ne pas être contré). Les écarts sont découpés aux bords du but, de la portée du
    gardien et de celle de chaque défenseur ; sur chaque tranche, un ballon contré par l'un n'atteint pas les suivants
    (`BLOCK_CHANCE` par défenseur touché). La hauteur (sous la barre) ne joue que sur le but."""
    sigma = shot_error_sigma(shooter, goal, opponents)
    _, under = on_target_axes(shooter, goal, opponents)
    scoring, covers = _goal_angles(shooter, goal, keeper), _block_covers(shooter, goal, opponents)

    def below(angle: float) -> float:
        return 0.5 * (1.0 + math.erf(angle / (sigma * math.sqrt(2.0))))

    cuts = sorted({-math.inf, math.inf, *(c for span in scoring + covers for c in span)})
    goal_share = blocked = goal_unblocked = 0.0
    for lo, hi in zip(cuts, cuts[1:]):
        mass = below(hi) - below(lo)
        through = (1.0 - BLOCK_CHANCE) ** sum(1 for c_lo, c_hi in covers if c_lo <= lo and hi <= c_hi)
        blocked += mass * (1.0 - through)
        if any(g_lo <= lo and hi <= g_hi for g_lo, g_hi in scoring):
            goal_share += mass * under
            goal_unblocked += mass * under * through
    return goal_share, blocked, goal_unblocked


def physical_shot_chance(shooter: PlayerState, goal: Vec2, keeper: PlayerState | None,
                         opponents: list[PlayerState]) -> float:
    """Chance de but d'un tir non contré, calculée avec les lois de sa résolution (ticket v2-realisme/05e) : écart du
    ballon gaussien (`shot_error_sigma`, note, pression et Composure comprises), dévissé (`draw_shot_error`), cadre
    (entre les poteaux, sous la barre), arrêt si le ballon passe à la portée du gardien (`keeper_reach_m`) au temps de
    vol jusqu'à lui ; gardien immobile pendant le vol (réserve A1 du 05h). Quelques `erf`, aucune constante nouvelle.
    Approximation : largeur et hauteur supposées indépendantes, comme au 35b. Toute modification de la résolution
    (gardien, cadrage, contre, vitesse du tir) se reporte ici ; contrôle : `scripts/shot_calibration.py`."""
    return (1.0 - _shank_share(shooter, goal, opponents)) * _flight_shares(shooter, goal, keeper, opponents)[0]


def physical_block_probability(shooter: PlayerState, goal: Vec2, opponents: list[PlayerState]) -> float:
    """Chance que le tir soit contré, avec les lois du contre physique (ticket v2-realisme/05e, `_flight_shares`). Le
    cône `block_probability` (tir visant un point du but au hasard) reste la règle du gardien (`gardien.py`)."""
    return (1.0 - _shank_share(shooter, goal, opponents)) * _flight_shares(shooter, goal, None, opponents)[1]


# xG (ticket v2-realisme/06a, proposé le 09/11/2026, validé par délégation du propriétaire ; décision D-V12). xG neutre :
# chance de but d'un tireur moyen face à un gardien moyen, à la même place, dans la même situation (adversaires, position
# du gardien, contre compris) : `occasion_quality` avec les notes neutres. xG après frappe : chance qu'un gardien moyen,
# placé où est le vrai gardien, n'atteigne pas un ballon passant à cet écart après ce temps de vol (portée du 05b), avec
# une incertitude de portée de `PSXG_SPREAD_M` (logistique) ; 0 pour un tir hors du cadre. Dispersion de la portée d'un
# gardien : non trouvée, ordre de grandeur. Étalement ramené de 0,3 à 0,15 m (ticket v2-realisme/06b, réserve A1 du 06a,
# validé par délégation du propriétaire) : sur 50 matchs, xG après frappe moins buts des tirs cadrés jugés passe de
# + 0,33 ± 0,12 à + 0,02 ± 0,09 par match.
PSXG_SPREAD_M = 0.15
# Attributs d'une copie neutre (ticket v2-realisme/06b, réserve A1 de l'expert) : vide, donc chaque note vaut la valeur par
# défaut de `player_attribute` comme pour `attributes=None` ; reconnaissable par son identité (un profil forcé du banc,
# `scripts/measure_v2._force_attribute`, ne la force pas).
NEUTRAL_ATTRIBUTES = MappingProxyType({})


def _neutralised(shooter: PlayerState, keeper: PlayerState | None, opponents: list[PlayerState]):
    """Copies du tireur et du gardien aux notes neutres (`NEUTRAL_ATTRIBUTES`), et les adversaires avec ce gardien."""
    neutral = replace(shooter, attributes=NEUTRAL_ATTRIBUTES)
    neutral_keeper = replace(keeper, attributes=NEUTRAL_ATTRIBUTES) if keeper is not None else None
    return neutral, neutral_keeper, [neutral_keeper if keeper is not None and o is keeper else o for o in opponents]


def neutral_xg(shooter: PlayerState, goal: Vec2, keeper: PlayerState | None, opponents: list[PlayerState]) -> float:
    """xG neutre d'un tir de `shooter` : indépendant des notes du tireur et du gardien (`NEUTRAL_ATTRIBUTES`)."""
    neutral, neutral_keeper, rivals = _neutralised(shooter, keeper, opponents)
    return occasion_quality(neutral, goal, neutral_keeper, rivals)


def neutral_open_chance(shooter: PlayerState, goal: Vec2, keeper: PlayerState | None,
                        opponents: list[PlayerState]) -> float:
    """Chance neutre hors contre (tickets v2-realisme/06c et 05e) : l'xG neutre sans les contres, pour découper l'écart
    buts moins xG en contre, exécution et gardien."""
    neutral, neutral_keeper, rivals = _neutralised(shooter, keeper, opponents)
    return physical_shot_chance(neutral, goal, neutral_keeper, rivals)


def post_shot_xg(gap_m: float, elapsed_s: float) -> float:
    """xG après frappe d'un tir cadré qui passe à `gap_m` du gardien `elapsed_s` après la frappe."""
    return 1.0 / (1.0 + math.exp(-(gap_m - keeper_reach_m(elapsed_s)) / PSXG_SPREAD_M))


def draw_shot_error(shooter: PlayerState, goal: Vec2, opponents: list[PlayerState]) -> tuple[float, float] | None:
    """Tir en vol (ticket v2-realisme/05a) : écarts d'angle tirés au départ, en largeur (rad, autour de l'axe vers le centre
    du but) et en hauteur (rad, autour de la visée à `SHOT_AIM_HEIGHT_M`) ; `None` pour un tir dévissé. Mêmes lois que
    `classify_unscored` (35b), sans tirage du but : l'issue se lit sur la ligne. Dévissé : `SHANK_SHARE` x (écart
    relatif)² des tirs hors du cadre, soit la même part des tirs ratés qu'au 35b."""
    sigma = shot_error_sigma(shooter, goal, opponents)
    wide, high = on_target_axes(shooter, goal, opponents)
    if TIR.random() < SHANK_SHARE * (sigma / SHOT_ERROR_SIGMA_RAD) ** 2 * (1.0 - wide * high):
        return None
    return TIR.gauss(0.0, sigma), TIR.gauss(0.0, sigma)


def shank_velocity(shooter: PlayerState, goal: Vec2, shot_speed: float) -> Vec2:
    """Vitesse d'un tir dévissé : lente, tournée de `SHANK_ANGLE_DEG` de l'axe du but, d'un côté tiré au hasard."""
    turn = math.radians(TIR.uniform(*SHANK_ANGLE_DEG)) * (1.0 if TIR.random() < 0.5 else -1.0)
    axis = (goal - shooter.position).normalized()
    return Vec2(axis.x * math.cos(turn) - axis.y * math.sin(turn),
                axis.x * math.sin(turn) + axis.y * math.cos(turn)) * (shot_speed * SHANK_SPEED_SHARE)


# Issue d'un tir cadré arrêté (ticket v2-collectif/28b, constantes proposées le 05/11/2026, validées par délégation du
# propriétaire). Opta classe les arrêts (capté, repoussé, du bout des gants...) sans publier de répartition ; aucune
# étude publique sur les seconds ballons : ordres de grandeur. Repère : environ 20 % des corners viennent d'un arrêt
# (relevé de 200 matchs PL et Championship, sans méthode publiée). Gardien neutre (A8) jusqu'au ticket
# v2-attributs-restants/03b : ni Handling ni Reflexes ici. Ni la force ni la hauteur du tir n'existent encore
# (v2-hauteur-ballon/02a, v2-attributs-restants/10a) : la difficulté passe par la chance de but et l'excentrement.
HELD, PARRIED, TIPPED = "capté", "repoussé", "claqué"
SAVE_DIFFICULTY_REF = 0.30  # chance de but au-delà de laquelle l'arrêt est le plus difficile possible
SAVE_HELD_SHARE = (0.70, 0.25)  # part captée : tir facile, tir le plus difficile (interpolation linéaire)
SAVE_OUT_SHARE = (0.25, 0.60)  # parmi les non captés, part claquée hors du terrain : tir central, tir le plus excentré
SAVE_EXCENTRIC_REF_M = 20.0  # écart latéral du tireur au centre du but qui fait un tir « le plus excentré »
PARRY_SPEED_SHARE = (0.25, 0.50)  # vitesse du ballon repoussé ou claqué, en part de la vitesse du tir
PARRY_ANGLE_DEG = (25.0, 80.0)  # repoussé : angle avec la ligne de but, du côté où file le tir
TIP_WIDE_M = (0.5, 3.0)  # claqué : point de sortie derrière la ligne, au-delà du poteau (ordre de grandeur)
_CENTRAL_SHOT = 0.1  # excentrement en dessous duquel le côté de la repoussée est tiré au hasard


def excentricity(origin: Vec2, goal: Vec2) -> float:
    """0 pour un tir face au but, 1 pour un tir parti à `SAVE_EXCENTRIC_REF_M` ou plus de l'axe."""
    return min(1.0, abs(origin.y - goal.y) / SAVE_EXCENTRIC_REF_M)


def save_shares(chance: float, origin: Vec2, goal: Vec2) -> tuple[float, float, float]:
    """Parts (capté, repoussé, claqué) d'un arrêt, selon la chance de but du tir (`shot_probability`) et son
    excentrement : un tir dangereux est moins souvent capté, un tir excentré plus souvent claqué en corner."""
    difficulty = min(1.0, chance / SAVE_DIFFICULTY_REF)
    held = SAVE_HELD_SHARE[0] + (SAVE_HELD_SHARE[1] - SAVE_HELD_SHARE[0]) * difficulty
    out = SAVE_OUT_SHARE[0] + (SAVE_OUT_SHARE[1] - SAVE_OUT_SHARE[0]) * excentricity(origin, goal)
    return held, (1.0 - held) * (1.0 - out), (1.0 - held) * out


def save_outcome(chance: float, origin: Vec2, goal: Vec2) -> str:
    """Tire l'issue d'un arrêt : `HELD`, `PARRIED` ou `TIPPED` (un tirage)."""
    held, parried, _ = save_shares(chance, origin, goal)
    r = TIR.random()
    return HELD if r < held else PARRIED if r < held + parried else TIPPED


def _shot_side(origin: Vec2, goal: Vec2) -> float:
    """Côté (+1 ou -1 en y) vers lequel file le tir prolongé ; tir central : au hasard."""
    if excentricity(origin, goal) < _CENTRAL_SHOT:
        return 1.0 if TIR.random() < 0.5 else -1.0
    return 1.0 if goal.y > origin.y else -1.0


def parry_velocity(origin: Vec2, goal: Vec2, keeper_at: Vec2, outcome: str, shot_speed: float) -> Vec2:
    """Vitesse du ballon après une parade (`PARRIED` ou `TIPPED`), depuis le gardien en `keeper_at`. Repoussé : vers le
    terrain, du côté où file le tir, à `PARRY_ANGLE_DEG` de la ligne de but (tir central : jusqu'à l'axe). Claqué : vers
    un point derrière la ligne de but, au-delà du poteau de ce côté (corner : le gardien touche en dernier). Le gardien
    étant devant sa ligne, le ballon claqué la franchit parfois entre les poteaux : vu de dessus, sans hauteur, c'est un
    ballon claqué au-dessus de la barre, corner aussi (réserve A2 de l'expert, 05/11/2026 ; vraie hauteur avec
    `v2-hauteur-ballon/02a`)."""
    side = _shot_side(origin, goal)
    speed = shot_speed * TIR.uniform(*PARRY_SPEED_SHARE)
    into_pitch = 1.0 if origin.x > goal.x else -1.0
    if outcome == TIPPED:
        aim = Vec2(goal.x - into_pitch * 2.0, goal.y + side * (GOAL_WIDTH_M / 2.0 + TIR.uniform(*TIP_WIDE_M)))
        return (aim - keeper_at).normalized() * speed
    high = 90.0 if excentricity(origin, goal) < _CENTRAL_SHOT else PARRY_ANGLE_DEG[1]
    angle = math.radians(TIR.uniform(PARRY_ANGLE_DEG[0], high))
    return Vec2(into_pitch * math.sin(angle), side * math.cos(angle)) * speed

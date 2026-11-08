"""Décision du porteur (Phase 5, ticket v2-cerveau-joueurs/01 ; refondue au ticket v2-collectif/33). Deux étages :
- valeur FACTUELLE de chaque option (tirer, passer à chaque coéquipier envisagé, conduire dans cinq directions),
  calculée avec les vraies capacités du porteur dans une monnaie commune, le danger attendu (`danger.py`) ;
- PERCEPTION : le porteur prend l'option qu'il croit la meilleure. Sa perception des valeurs est brouillée par
  Decisions (ampleur de l'erreur), Composure (sous pression seulement) et Anticipation (part du déplacement des
  défenseurs qu'il prolonge) ; Vision filtre les coéquipiers envisagés. Exécution dans la valeur, mental dans la
  perception, sans double comptage (docs/CARTE_ATTRIBUTS_V2.md).
Seul le CHOIX est décidé ici : la réussite du tir, de la passe ou du duel reste résolue par
`shooting.py`/`possession.py`/`duel.py`."""

from __future__ import annotations

import math
from dataclasses import dataclass, replace

from v2engine.attributes import player_attribute, success_probability
from v2engine.danger import danger, loss_cost
from v2engine.flux import DECISION, DUEL, PERCEPTION
from v2engine.geometry import PITCH_LENGTH_M, PITCH_WIDTH_M, Vec2
from v2engine.movement import PlayerState, max_speed_mps
from v2engine.off_ball import OPEN_LANE_PROBABILITY
from v2engine.offside import is_clearly_offside, pass_margin_m, perceived_defence_line
from v2engine.possession import BALL_FRICTION_PER_S, BALL_STOPPED_MPS, pass_success_probability, pressure
from v2engine.shooting import SHOOTING_RANGE_M, occasion_quality

# Constantes produit validées par le propriétaire (24/10/2026).
DECISION_INTERVAL_S = 0.5  # le porteur réévalue ses options deux fois par seconde
DRIBBLE_SPEED_FACTOR = 0.85  # part de sa vitesse max, balle au pied
# Decisions -> probabilité de prendre la meilleure option : 99 -> 95 %, 55 -> 70 %, 11 -> 45 %. Même FORME de courbe
# que le guide (quasi plate entre 45 et 55), mais centrée sur 70 % : un joueur moyen choisit bien la plupart du temps.
# Pas de poids par poste (`register_weights`) : bien choisir son action compte autant à tous les postes.
_BEST_CHOICE_BASELINE = 0.70
_BEST_CHOICE_AMPLITUDE = 0.25

# Monnaie commune (ticket v2-collectif/33, constantes validées le 03/11/2026 par délégation du propriétaire) : valeur
# d'une option = chance de garder le ballon x danger de l'endroit atteint - chance de le perdre x danger qu'y aurait
# l'adversaire. Les anciens poids de volume (tir 0,1, passe 0,25, conduite 0,04) ont disparu.
# Conduite : cinq directions (droit au but, diagonales, côtés ; le retrait passe par la passe), espace libre testé
# tous les 2 m jusqu'à 10 m : un point est libre si le porteur, balle au pied, y arrive au moins 0,3 s avant tout
# adversaire. Course d'un adversaire (corrigée le 04/11/2026 après la revue de l'expert, modèle à temps de réaction
# type Spearman 2018) : il garde son élan pendant `REACTION_S`, puis court droit au point à sa vitesse max, sans
# montée en vitesse ; jamais plus vite que sa vitesse max, et un défenseur lancé vers le point y arrive avant un
# défenseur arrêté. Chance de garder le ballon : courbe Dribbling 99 -> 95 %, 55 -> 83 %,
# 11 -> 71 % au contact ; sans adversaire à 5 m, seule une mauvaise touche le fait perdre, un dixième de ce risque
# (`FREE_TOUCH_SHARE`, ajouté le 04/11/2026 : sans lui, une conduite dans le vide perdait le ballon 17 fois sur 100).
# Ticket v2-realisme/04a : cette chance est celle d'une conduite de `DRIBBLE_REFERENCE_S` ; la même fonction sert à
# l'évaluation (`keep_ball_probability`) et à la résolution (`dribble_lost`, un tirage par intervalle de décision). La
# part perdue sous pression que la passe et le tir gardent (`PRESSURE_KEEP_SHARE`) n'en fait plus partie : la
# pression qui prend le ballon à un porteur est le tacle, qui reste tiré à part dans `match` (pas de double compte).
DRIBBLE_DIRECTIONS_DEG = (0.0, 45.0, -45.0, 90.0, -90.0)
DRIBBLE_STEP_M, DRIBBLE_REACH_M, DRIBBLE_MARGIN_S = 2.0, 10.0, 0.3
REACTION_S = 0.3
_KEEP_BALL = (0.83, 0.12)  # baseline, amplitude (Dribbling)
PRESSURE_KEEP_SHARE = 0.5  # part de la chance de garder perdue au contact d'un adversaire (passe ; plus la conduite, 04a)
FREE_TOUCH_SHARE = 0.1
# Durée d'une conduite évaluée (ticket v2-realisme/04a, proposée le 08/11/2026, validée d'office) : la chance de garder
# le ballon vaut pour une conduite de cette durée ; la perte tirée à chaque intervalle s'en déduit :
# 1 - garde^(intervalle / durée). 1,5 s : la conduite évaluée va jusqu'à 10 m (`DRIBBLE_REACH_M`) à 85 % de la vitesse
# d'un joueur moyen (environ 7 m/s), soit 1,4 s ; au-delà de 10 m, le porteur réévalue (`DECISION_INTERVAL_S`).
DRIBBLE_REFERENCE_S = 1.5
# Où va le ballon perdu en conduite (ticket v2-realisme/04b, constantes proposées le 08/11/2026, validées d'office ;
# chiffres réels : non trouvés). Un adversaire à moins de `DISPOSSESSION_RADIUS_M` (la portée du tacle, `match.TACKLE_RADIUS_M`)
# prend le ballon avec la probabilité de la gêne (70 % à 1,5 m, 100 % au contact) ; sinon, ou si le ballon lui échappe, c'est
# une touche trop longue : il s'arrête devant le porteur à une distance tirée dans `LONG_TOUCH_M`, dans un angle de
# +/- `LONG_TOUCH_DEG` autour de sa direction de conduite. Sans adversaire au contact, jamais de dépossession.
DISPOSSESSION_RADIUS_M = 1.5
LONG_TOUCH_M = (1.5, 4.0)
LONG_TOUCH_DEG = 30.0
# Valeur future d'une passe (ticket v2-collectif/13, validé par le propriétaire le 01/11/2026) : part de la valeur qui
# vient de la meilleure passe suivante du receveur (réussite x danger atteint, ticket 33), le reste du danger au
# receveur. La suite vaut au moins la position atteinte (il garde le ballon) : sans
# meilleure suite, la passe garde sa valeur d'avant. Pas de suite en contre-attaque (décisions du 01/11/2026).
_FOLLOW_UP_SHARE = 0.4
# Plan de passe (ticket v2-collectif/14, validé par le propriétaire le 02/11/2026) : la suite prévue par le passeur est
# transmise au receveur. À sa première décision, il l'adopte selon son Teamwork (même courbe que tenir le bloc,
# `defense._STAYS` : 99 -> 100 %, 55 -> 85 %, 11 -> 65 %), puis la tient si la passe reste jouable (réussite au moins
# `OPEN_LANE_PROBABILITY`) et que sa Vision la voit : sa valeur est alors majorée de `PLAN_BONUS`. Sinon il l'abandonne.
PLAN_BONUS = 0.3
_ADOPT_PLAN = (0.85, 0.2, 0.65, 1.0)  # baseline, amplitude, min, max
PLAN_HELD, PLAN_DROPPED, PLAN_UNSEEN, PLAN_REFUSED = "tenu", "abandonné", "non vu", "refusé"

# Vision (ticket v2-cerveau-joueurs/02, constantes validées par le propriétaire le 24/10/2026) : QUELS coéquipiers le
# porteur envisage. Portée 99 -> 50 m, 55 -> 30 m, 11 -> 10 m ; une passe qui fait gagner au moins
# `_KEY_PASS_GAIN_M` vers le but n'est repérée qu'avec la probabilité 99 -> 90 %, 55 -> 50 %, 11 -> 10 %. Le
# coéquipier le plus proche est toujours vu. Même courbe partagée que les autres attributs (`success_probability`),
# bornes en mètres pour la portée. Pas de poids par poste : bien voir le jeu compte à tous les postes.
_VISION_RANGE_M = (30.0, 20.0, 10.0, 50.0)  # baseline, amplitude, min, max
_KEY_PASS_GAIN_M = 15.0
_KEY_PASS_SPOT = (0.5, 0.4)  # baseline, amplitude

# Transition défense-attaque (ticket v2-collectif/11, constantes validées par le propriétaire le 01/11/2026 ; part réelle
# des contre-attaques non trouvée). À la récupération, le porteur choisit entre contre-attaque et conservation. La
# contre-attaque est le bon choix si les adversaires de champ derrière le ballon ne dépassent pas de plus de
# `COUNTER_MAX_EXCESS` ses coéquipiers de champ devant lui.
# Decisions règle la probabilité de prendre le bon choix (même courbe que `choose_action`).
CONTRE_ATTAQUE, CONSERVATION = "contre-attaque", "conservation"
COUNTER_MAX_EXCESS = 2
# Dans la nouvelle monnaie (ticket 33), même sens : en contre-attaque, le gain de danger pèse plus et la perte moins ;
# en conservation, l'inverse. (gain, perte) ; le tir n'en dépend pas.
_TRANSITION_WEIGHTS = {None: (1.0, 1.0), CONTRE_ATTAQUE: (1.3, 0.7), CONSERVATION: (0.7, 1.3)}

# Perception (ticket 33). Decisions : écart-type de l'erreur sur chaque valeur perçue, en part de la meilleure valeur
# réelle, linéaire entre les repères de `_ERROR_POINTS`, réglé le 04/11/2026 pour que le taux de meilleur choix suivi,
# en moyenne sur un match, suive la courbe validée (`best_choice_probability` : 95 / 70 / 45 %), mesuré par
# `scripts/measure_v2_meilleur_choix.py`. Composure : erreur multipliée par 1 + gêne x k, k 99 -> 0,2, 55 -> 0,6,
# 11 -> 1 (rien sans adversaire à moins de 5 m). Anticipation : part de l'élan des adversaires (pendant leur temps de
# réaction) qu'il prolonge en jugeant l'espace libre (99 -> 100 %, 55 -> 65 %, 11 -> 30 %).
_ERROR_POINTS = ((11.0, 1.1), (40.0, 0.42), (55.0, 0.36), (75.0, 0.26), (99.0, 0.08))  # (Decisions, part de la meilleure valeur)
# Meilleur choix suivi : choix qui perd moins de 10 % de la valeur du meilleur (« erreur légère » du panneau) ; entre
# deux options presque équivalentes, prendre l'une ou l'autre n'est pas une erreur (validé le 04/11/2026).
BEST_CHOICE_TOLERANCE = 0.1
# Choix en deux temps (revue de l'expert, A4, 04/11/2026). 1) La direction de conduite : son erreur sur chaque
# direction est tirée une fois pendant sa possession et gardée (il se fait une idée de l'espace et s'y tient ; tirée
# toutes les 0,5 s, elle le faisait zigzaguer entre directions de valeur égale, 80 % des directions étant bloquées :
# 45 % des conduites consécutives changeaient de cap de 90° ou plus). 2) Conduire, passer à tel coéquipier ou tirer :
# une erreur par option, retirée à chaque décision ; la conduite y compte pour UNE option (sa direction retenue), et
# non cinq, qui lui donnaient cinq chances de paraître la meilleure.
_COMPOSURE_K = (0.6, -0.4)
_ANTICIPATION_SHARE = (0.65, 0.35)


@dataclass(frozen=True)
class Action:
    kind: str  # "shot" | "pass" | "dribble"
    value: float
    target: PlayerState | None = None  # coéquipier visé, pour une passe
    considered: int = 1  # options envisagées à cette décision (journal des décisions, ADR 0001)
    best: bool = True  # meilleure option prise (Decisions)
    follow: str | None = None  # suite prévue pour le receveur d'une passe, s'il en a une meilleure (ticket 14)
    plan: str | None = None  # sort du plan reçu : PLAN_HELD, _DROPPED, _UNSEEN ou _REFUSED (ticket 14)
    point: Vec2 | None = None  # cible de conduite, tenue jusqu'à la décision suivante (ticket 33)
    best_kind: str | None = None  # meilleur choix factuel de cette décision (ticket 33)
    gap: float = 0.0  # valeur réelle perdue par rapport au meilleur choix factuel, en part de celui-ci (ticket 33)


def adopt_plan_probability(player: PlayerState) -> float:
    baseline, amplitude, low, high = _ADOPT_PLAN
    return success_probability(player_attribute(player, "Teamwork"), baseline=baseline, amplitude=amplitude,
                               min_prob=low, max_prob=high)


def vision_range_m(vision: float) -> float:
    baseline, amplitude, low, high = _VISION_RANGE_M
    return success_probability(vision, baseline=baseline, amplitude=amplitude, min_prob=low, max_prob=high)


def key_pass_spot_probability(vision: float) -> float:
    baseline, amplitude = _KEY_PASS_SPOT
    return success_probability(vision, baseline=baseline, amplitude=amplitude)


def visible_teammates(holder: PlayerState, teammates: list[PlayerState], goal: Vec2) -> list[PlayerState]:
    """Coéquipiers que le porteur envisage pour une passe (Vision, voir `_VISION_RANGE_M`) : à portée, et pour une
    passe qui fait gagner beaucoup de terrain, seulement s'il la repère à cette décision-ci. Le plus proche est
    toujours vu, même à Vision très basse."""
    if not teammates:
        return []
    vision = player_attribute(holder, "Vision")
    reach = vision_range_m(vision)
    spot = key_pass_spot_probability(vision)
    holder_to_goal = holder.position.distance_to(goal)
    nearest = min(teammates, key=lambda p: holder.position.distance_to(p.position))
    seen = []
    for mate in teammates:
        if mate is not nearest:
            if holder.position.distance_to(mate.position) > reach:
                continue
            if holder_to_goal - mate.position.distance_to(goal) >= _KEY_PASS_GAIN_M and PERCEPTION.random() >= spot:
                continue
        seen.append(mate)
    return seen


def evaluate_options(holder: PlayerState, players: list[PlayerState], goal: Vec2, keeper: PlayerState | None,
                     mode: str | None = None, planned: str | None = None) -> list[Action]:
    """Les options du porteur avec leur valeur FACTUELLE (ticket v2-collectif/33 : danger attendu, vraies capacités),
    de la meilleure à la moins bonne : un tir à portée (`SHOOTING_RANGE_M`), une passe par coéquipier envisagé (Vision),
    une conduite par direction (`DRIBBLE_DIRECTIONS_DEG`). `mode` : choix de
    transition de son équipe, contre-attaque ou conservation (ticket v2-collectif/11), sinon `None`. `planned` :
    coéquipier que son passeur a prévu pour la suite (plan de passe, ticket v2-collectif/14)."""
    opponents = [p for p in players if p.team != holder.team]
    mates = [p for p in players if p.team == holder.team and p.name != holder.name]
    # Hors-jeu (ticket v2-collectif/23, deuxième passe du 28/10/2026) : le porteur ne sert pas un coéquipier qu'il
    # voit nettement au-delà de la ligne -- mais ce qu'il voit dépend de sa Vision. Trois leviers, tous sur la Vision
    # (docs/CARTE_ATTRIBUTS_V2.md, audit A12) : la portée (`visible_teammates`), le seuil de tolérance
    # (`pass_margin_m`, angle mort de 0,85 m à Vision 0 à 0,3 m à Vision 100) et l'erreur de lecture de la ligne (`perceived_defence_line`, 0,05 à 0,25 m).
    # Les deux derniers se composent en un seul seuil effectif, d'où les passes que l'arbitre siffle.
    vision = player_attribute(holder, "Vision")
    margin = pass_margin_m(vision)
    seen_line = perceived_defence_line(holder.team, opponents, vision)
    teammates = [p for p in visible_teammates(holder, mates, goal)
                 if not is_clearly_offside(holder.team, p.position, holder.position, opponents, margin, seen_line)]
    gene = pressure(holder, opponents)
    holder_to_goal = holder.position.distance_to(goal)
    seen_full = teammates  # suites possibles du receveur (ticket 13)
    if mode == CONTRE_ATTAQUE and gene == 0.0:  # seule une passe qui fait avancer compte (ticket v2-collectif/11)
        teammates = [p for p in teammates if p.position.distance_to(goal) < holder_to_goal]

    # Plan reçu (ticket 14) : adopté selon Teamwork (un tirage), jamais en contre-attaque.
    held = planned if planned is not None and mode != CONTRE_ATTAQUE \
        and DECISION.random() < adopt_plan_probability(holder) else None

    team = holder.team
    options = dribble_options(holder, opponents, gene, mode, projection=1.0)
    if holder_to_goal <= SHOOTING_RANGE_M:
        # qualité de l'occasion (ticket 28a) : chance de but, sauf s'il est contré dans le cône de tir (même règle qu'à
        # la résolution) ; un tir manqué ne coûte rien (sortie de but ou corner) ; les issues viennent au ticket 28b
        options.append(Action("shot", occasion_quality(holder, goal, keeper, opponents)))
    # suite du receveur (ticket 13) : meilleure passe suivante vers un coéquipier que le porteur voit lui-même ; le
    # passeur n'en fait pas partie (pas d'aller-retour) ; pas de suite en contre-attaque (on joue vite vers l'avant)
    share = 0.0 if mode == CONTRE_ATTAQUE else _FOLLOW_UP_SHARE
    for mate in teammates:
        success = pass_success_probability(holder, mate, opponents)  # le ballon arrive (v2-socle/04)
        # temps disponible : il garde le ballon assez longtemps pour jouer (A9 reclassé au ticket 13)
        keep = success * (1.0 - PRESSURE_KEEP_SHARE * pressure(mate, opponents))
        now = danger(mate.position, team)
        future, follow = now, None
        if share:
            best_next, nxt = max(((pass_success_probability(mate, n, opponents) * danger(n.position, team), n.name)
                                  for n in seen_full if n is not mate
                                  and not is_clearly_offside(team, n.position, mate.position, opponents, margin,
                                                             seen_line)),
                                 key=lambda vn: vn[0], default=(0.0, None))
            if best_next > now:  # la suite vaut au moins la position atteinte (il garde le ballon)
                future, follow = best_next, nxt
        reached = (1.0 - share) * now + share * future
        if mate.name == held and success >= OPEN_LANE_PROBABILITY:  # plan tenu, encore jouable (ticket 14)
            reached *= 1.0 + PLAN_BONUS
        midway = Vec2((holder.position.x + mate.position.x) / 2.0, (holder.position.y + mate.position.y) / 2.0)
        options.append(Action("pass", option_value(holder, mode, keep, reached, midway), mate, follow=follow))
    if planned is not None and mode != CONTRE_ATTAQUE:  # sort du plan, pour la mesure (ticket 14)
        # abandonné : la cible est vue mais la ligne s'est fermée ; non vu : hors de sa Vision ou hors-jeu évident
        target = next((m for m in teammates if m.name == held), None)
        state = PLAN_REFUSED if held is None else PLAN_UNSEEN if target is None \
            else PLAN_HELD if pass_success_probability(holder, target, opponents) >= OPEN_LANE_PROBABILITY \
            else PLAN_DROPPED
        options = [replace(o, plan=state) for o in options]
    return sorted(options, key=lambda a: a.value, reverse=True)


def option_value(holder: PlayerState, mode: str | None, keep: float, reached: float, lost_at: Vec2) -> float:
    """Monnaie commune (ticket 33) : s'il garde le ballon, le danger d'ici plus le gain (pondéré par la transition) ;
    s'il le perd, le danger qu'aurait l'adversaire là où il le perd (pondéré aussi)."""
    here = danger(holder.position, holder.team)
    gain_weight, loss_weight = _TRANSITION_WEIGHTS[mode]
    return keep * (here + gain_weight * (reached - here)) - (1.0 - keep) * loss_weight * loss_cost(lost_at, holder.team)


def keep_ball_probability(holder: PlayerState, gene: float) -> float:
    """Chance de garder le ballon en conduisant pendant `DRIBBLE_REFERENCE_S` (tickets 33 et v2-realisme/04a) : Dribbling
    compte d'autant plus qu'un adversaire est proche, un dixième de ce risque sans adversaire à 5 m. Seule fonction de
    ce risque : l'évaluation de l'option et le tirage de la perte (`dribble_lost`) l'appellent."""
    baseline, amplitude = _KEEP_BALL
    skill = success_probability(player_attribute(holder, "Dribbling"), baseline=baseline, amplitude=amplitude)
    contested = FREE_TOUCH_SHARE + (1.0 - FREE_TOUCH_SHARE) * gene  # 0,1 sans adversaire à 5 m, 1 au contact
    return 1.0 - (1.0 - skill) * contested


def dribble_loss_probability(holder: PlayerState, gene: float, duration_s: float) -> float:
    """Chance de perdre le ballon en conduisant `duration_s` secondes sous la gêne `gene` : la chance de garder de
    `keep_ball_probability`, rapportée à la durée (événement par unité de temps, indépendant du pas)."""
    return 1.0 - keep_ball_probability(holder, gene) ** (duration_s / DRIBBLE_REFERENCE_S)


def dribble_lost(holder: PlayerState, opponents: list[PlayerState], duration_s: float = DECISION_INTERVAL_S) -> bool:
    """Tirage de la perte du ballon sur un intervalle de décision de conduite (ticket v2-realisme/04a)."""
    return DUEL.random() < dribble_loss_probability(holder, pressure(holder, opponents), duration_s)


def lost_carry_outcome(holder: PlayerState, opponents: list[PlayerState],
                       heading: Vec2) -> tuple[PlayerState | None, Vec2 | None]:
    """Où va le ballon perdu en conduite (ticket v2-realisme/04b) : `(adversaire, None)` s'il est dépossédé, sinon
    `(None, vitesse du ballon)` pour une touche trop longue dans la direction `heading` (vitesse de départ pour que le
    ballon, freiné, s'arrête à la distance tirée). Aucun attribut lu : le tirage est celui de la perte (flux DUEL)."""
    near = [o for o in opponents if holder.position.distance_to(o.position) < DISPOSSESSION_RADIUS_M]
    if near and DUEL.random() < pressure(holder, opponents):
        return min(near, key=lambda o: holder.position.distance_to(o.position)), None
    distance = DUEL.uniform(*LONG_TOUCH_M)
    angle = math.radians(DUEL.uniform(-LONG_TOUCH_DEG, LONG_TOUCH_DEG))
    d = heading.normalized()
    direction = Vec2(d.x * math.cos(angle) - d.y * math.sin(angle), d.x * math.sin(angle) + d.y * math.cos(angle))
    return None, direction * (BALL_STOPPED_MPS - distance * math.log(BALL_FRICTION_PER_S))


def arrival_s(opponent: PlayerState, point: Vec2, projection: float = 1.0) -> float:
    """Temps pour qu'un adversaire atteigne `point` : il garde son élan pendant `REACTION_S` (la part `projection`
    de cet élan, telle que le porteur la voit), puis court droit au point à sa vitesse max."""
    # ponytail: pas de montée en vitesse ni de trajectoire courbe ; jamais plus rapide que la vitesse max depuis t = 0
    start = opponent.position + opponent.velocity * (projection * REACTION_S)
    return REACTION_S + start.distance_to(point) / max_speed_mps(opponent.pace)


def free_point(holder: PlayerState, opponents: list[PlayerState], heading: Vec2, projection: float) -> Vec2 | None:
    """Dernier point libre dans la direction `heading` (tous les `DRIBBLE_STEP_M` jusqu'à `DRIBBLE_REACH_M`) : le
    porteur, balle au pied, y arrive `DRIBBLE_MARGIN_S` avant tout adversaire, dont il prolonge le déplacement pour
    la part `projection` (1 : le vrai ; moins : ce que son Anticipation lui fait voir, `arrival_s`). `None` : rien
    de libre."""
    speed = max_speed_mps(holder.pace) * DRIBBLE_SPEED_FACTOR
    reached = None
    for step in range(1, int(DRIBBLE_REACH_M / DRIBBLE_STEP_M) + 1):
        point = holder.position + heading * (step * DRIBBLE_STEP_M)
        if not (0.0 <= point.x <= PITCH_LENGTH_M and 0.0 <= point.y <= PITCH_WIDTH_M):
            break
        run_s = step * DRIBBLE_STEP_M / speed
        if any(arrival_s(o, point, projection) < run_s + DRIBBLE_MARGIN_S for o in opponents):
            break
        reached = point
    return reached


def dribble_options(holder: PlayerState, opponents: list[PlayerState], gene: float, mode: str | None,
                    projection: float) -> list[Action]:
    """Une conduite par direction (`DRIBBLE_DIRECTIONS_DEG`). Sans espace libre dans une direction, il y va quand
    même au duel, sans gain (valeur de garder le ballon sur place). Toujours cinq options, dans le même ordre."""
    forward = 1.0 if holder.team == "home" else -1.0
    keep = keep_ball_probability(holder, gene)
    options = []
    for angle in DRIBBLE_DIRECTIONS_DEG:
        rad = math.radians(angle)
        heading = Vec2(forward * math.cos(rad), math.sin(rad))
        reached = free_point(holder, opponents, heading, projection)
        value = option_value(holder, mode, keep, danger(reached or holder.position, holder.team), holder.position)
        options.append(Action("dribble", value, point=reached or holder.position + heading * DRIBBLE_STEP_M))
    return options


def best_choice_probability(decisions: float) -> float:
    return success_probability(decisions, baseline=_BEST_CHOICE_BASELINE, amplitude=_BEST_CHOICE_AMPLITUDE)


def _curve(note: float, shape: tuple[float, float]) -> float:
    baseline, amplitude = shape
    return success_probability(note, baseline=baseline, amplitude=amplitude, min_prob=0.0, max_prob=2.0)


def perception_error(holder: PlayerState, gene: float) -> float:
    """Écart-type de l'erreur de perception, en part de la meilleure valeur réelle : Decisions, puis Composure sous
    pression seulement (ticket 33)."""
    note = min(max(player_attribute(holder, "Decisions"), _ERROR_POINTS[0][0]), _ERROR_POINTS[-1][0])
    (n0, e0), (n1, e1) = next(pair for pair in zip(_ERROR_POINTS, _ERROR_POINTS[1:]) if note <= pair[1][0])
    error = e0 + (note - n0) / (n1 - n0) * (e1 - e0)
    return error * (1.0 + gene * _curve(player_attribute(holder, "Composure"), _COMPOSURE_K))


def anticipation_share(holder: PlayerState) -> float:
    """Part du déplacement des adversaires que le porteur prolonge pendant sa conduite (ticket 33)."""
    return min(1.0, _curve(player_attribute(holder, "Anticipation"), _ANTICIPATION_SHARE))


def choose_action(holder: PlayerState, players: list[PlayerState], goal: Vec2, keeper: PlayerState | None,
                  mode: str | None = None, planned: str | None = None,
                  felt: dict[int, float] | None = None, set_piece: bool = False) -> Action:
    """Prend l'option qu'il CROIT la meilleure (ticket 33) : valeur réelle brouillée par sa perception (Decisions,
    Composure sous pression), conduites jugées avec son Anticipation. Deux options proches font hésiter même un très
    bon joueur ; un joueur faible se trompe surtout entre options voisines. `planned` : ticket v2-collectif/14.
    `felt` : son erreur sur chaque direction de conduite (en écarts-types), gardée pendant sa possession ; complétée
    ici si besoin. `set_piece` : coup franc (ticket v2-collectif/30), il frappe ou passe, la conduite n'est pas une
    option."""
    options = evaluate_options(holder, players, goal, keeper, mode, planned)
    if set_piece:
        options = [o for o in options if o.kind != "dribble"] or options
    best = options[0]
    tagged = dict(considered=len(options), best_kind=best.kind)
    if len(options) == 1:
        return replace(best, best=True, **tagged)
    opponents = [p for p in players if p.team != holder.team]
    gene = pressure(holder, opponents)
    # conduites telles qu'il les voit : même direction, espace jugé avec son Anticipation (dans l'ordre des directions)
    share = anticipation_share(holder)
    # la valeur RÉELLE d'une conduite vue autrement reste celle de la vraie direction (il s'arrête où l'espace
    # s'arrête) ; une direction se reconnaît à son point réel, distinct d'une direction à l'autre
    real_dribbles = dribble_options(holder, opponents, gene, mode, 1.0)
    direction = {real.point: i for i, real in enumerate(real_dribbles)}
    seen_as = {} if share >= 1.0 else {
        real.point: seen for real, seen in zip(real_dribbles, dribble_options(holder, opponents, gene, mode, share))}
    felt = {} if felt is None else felt
    sigma = perception_error(holder, gene) * max(abs(best.value), 1e-3)
    for index in range(len(real_dribbles)):
        if index not in felt:
            felt[index] = PERCEPTION.gauss(0.0, 1.0)
    # 1) direction qu'il retient : la meilleure à ses yeux, avec son erreur gardée sur chaque direction
    drive = max((o for o in options if o.kind == "dribble"), default=None,
                key=lambda o: seen_as.get(o.point, o).value + felt[direction[o.point]] * sigma)
    # 2) cette conduite contre chaque passe et le tir, une erreur fraîche par option
    perceived = []
    for option in ([drive] if drive is not None else []) + [o for o in options if o.kind != "dribble"]:
        seen = seen_as.get(option.point, option) if option.kind == "dribble" else option
        perceived.append((seen.value + PERCEPTION.gauss(0.0, sigma), option, seen.point))
    _, chosen, point = max(perceived, key=lambda t: t[0])
    # valeur perdue, en part de la meilleure ; une option presque équivalente compte comme le meilleur choix
    gap = (best.value - chosen.value) / max(abs(best.value), 1e-9)
    return replace(chosen, point=point, best=gap < BEST_CHOICE_TOLERANCE, gap=gap, **tagged)


def counter_is_favorable(holder: PlayerState, players: list[PlayerState]) -> bool:
    """Contre-attaque jouable : adversaires de champ derrière le ballon (entre lui et le but visé) moins coéquipiers
    de champ devant lui, porteur exclu, au plus `COUNTER_MAX_EXCESS` (ticket v2-collectif/11)."""
    forward = 1.0 if holder.team == "home" else -1.0
    ahead = [p for p in players if p.poste != "GK" and p is not holder
             and forward * (p.position.x - holder.position.x) > 0.0]
    behind = sum(p.team != holder.team for p in ahead)
    return behind - (len(ahead) - behind) <= COUNTER_MAX_EXCESS


def choose_transition(holder: PlayerState, players: list[PlayerState]) -> str:
    """Choix du porteur qui vient de récupérer le ballon : le bon choix (contre-attaque si elle est jouable, sinon
    conservation) avec la probabilité donnée par Decisions, sinon l'autre."""
    best, other = (CONTRE_ATTAQUE, CONSERVATION) if counter_is_favorable(holder, players) else (CONSERVATION, CONTRE_ATTAQUE)
    return best if DECISION.random() < best_choice_probability(player_attribute(holder, "Decisions")) else other

"""Indicateurs de mesure du moteur V2 (ticket v2-collectif/01). Définitions, unités et sources :
`docs/INDICATEURS_V2.md`. Deux parties :

- fonctions pures sur une image du match (positions à un instant) : géométrie d'équipe, lignes,
  compacité, supériorité locale, défense préventive, couverture du presseur, solutions de passe ;
- `Collector`, nourri tick par tick (`simulate_match(observer=...)`) et par les événements du moteur
  (passes, tirs, tacles, choix du porteur), qui accumule les indicateurs classiques et tactiques,
  découpés par zone du ballon, score et tranche de 15 minutes.

Lecture seule : rien ici ne modifie le jeu."""

from __future__ import annotations

import math
import statistics
from collections import Counter, defaultdict
from collections.abc import Sequence
from dataclasses import dataclass, field, replace

import v2engine.cerveau as cerveau
from v2engine.cerveau import APPEL, BALLON_LIBRE, CHASE_RADIUS_M, OPPONENT_GOAL, TENIR, nearest_of_team
from v2engine.attributes import player_attribute
from v2engine.decision import DECISION_INTERVAL_S, dribble_loss_probability
from v2engine.defense import arrival_time_s
from v2engine.gardien import (BALL_DISTANCE_M, BISECTOR_TOLERANCE_M, FACE_A_FACE, FACE_RANGE_M, FACE_STOPPED_MPS, PLACEMENT,
                              RELANCE, SORTIE, bisector_direction, bisector_point, face_depth, face_to_face, own_goal, race)
from v2engine.geometry import PITCH_LENGTH_M, PITCH_WIDTH_M, Vec2, in_penalty_area
from v2engine.movement import PlayerState
from v2engine.offside import offside_line
from v2engine.possession import BALL_FRICTION_PER_S, MAX_PASS_MPS as SHOT_SPEED_MPS, pass_success_probability, pressure
from v2engine.restart import CORNER, GOAL_KICK, KICKOFF
from v2engine.shooting import (base_chance, keeper_reach_m, neutral_open_chance, shot_pressure, shot_probability,
                               shooting_note)
from v2engine.situation import POSSESSION_INSTALLEE, TRANSITION_DEFENSIVE, TRANSITION_OFFENSIVE, SituationTracker
from v2engine.trace import BUT, CONTROLE_RATE, PASSE, PERTE, REMISE

from scripts.v2_tranches import MinuteProfile

KMH = 1.0 / 3.6
# Seuils de mesure (docs/INDICATEURS_V2.md, section « Seuils de mesure ») -- ils ne changent pas le jeu.
OPTION_RANGE_M = 40.0
OPTION_PROBABILITY = 0.7  # même seuil que le jeu (`off_ball.OPEN_LANE_PROBABILITY`, ticket 06)
EASY_OPTION_PROBABILITY = 0.8  # solution « facile » (ticket 08, validé le 31/10/2026) : le seuil de 0,5 ne voit pas la pression
PRESS_RADIUS_M = 3.0
COVER_BEHIND_M, COVER_AHEAD_M, COVER_HALF_WIDTH_M = 3.0, 9.0, 4.0
LOCAL_RADIUS_M = 10.0
LOCAL_DEFENDERS = 5
RUN_SPEED_MPS, RUN_MIN_S, RUN_SAME_ZONE_M = 15.0 * KMH, 0.7, 5.0
ON_THE_LINE_M, NEAR_THE_LINE_M = 2.0, 5.0  # appel dans le dos ; jeu sur la ligne à la passe (ticket 16)
TRANSITION_LOSS_S = 5.0
COUNTER_WINDOW_S = 15.0
RETREAT_SPEED_MPS, RETREAT_WINDOW_S = 1.0, 10.0
# Repli (ticket v2-collectif/10) : vitesse vers son but, 1,5 s après la perte, des joueurs qui étaient devant le ballon
CHOICE_AFTER_S = 1.5
RECOVERY_CLASSES = ((5.0, "0-5 s"), (12.0, "5-12 s"), (15.0, "12-15 s"), (math.inf, "plus de 15 s"))
LONG_PASS_M = 32.0
# Taux d'arrêt des tirs cadrés par tranche (ticket v2-realisme/05h) : distance du tir au but, vitesse du ballon quand il
# passe au gardien (vitesse du tir freinée, `possession.BALL_FRICTION_PER_S`). Tranches de lecture, sans effet sur le jeu.
SAVE_DISTANCE_BANDS = ((11.0, "moins de 11 m"), (18.0, "11-18 m"), (25.0, "18-25 m"), (math.inf, "25 m et plus"))
SAVE_SPEED_BANDS = ((18.0, "moins de 18 m/s"), (24.0, "18-24 m/s"), (math.inf, "24 m/s et plus"))
# Sortie d'un tir contré par rapport à la direction du tir (ticket v2-realisme/05d) : effleuré (il continue), dévié,
# renvoyé de côté, renvoyé vers le tireur.
BLOCK_EXIT_BANDS = ((45.0, "0-45°"), (90.0, "45-90°"), (135.0, "90-135°"), (math.inf, "135-180°"))
SHOT_CLOSE_RANGE_M = 16.0  # tir « de près » : demande du propriétaire (28/10/2026) pour mesurer l'exposition du gardien
FREE_PASSER_M = 9.0  # porteur libre : défenseur le plus proche à 9 m ou plus (pressé : PRESS_RADIUS_M), ticket 05
SPRINT_MPS, HIGH_INTENSITY_MPS = 25.0 * KMH, 19.8 * KMH
SPRINT_MIN_S = 1.0  # sprint : au-dessus de SPRINT_MPS pendant au moins 1 s (ticket v2-realisme/01d)
MATCH_90_S = 90 * 60.0  # appels ramenés à 90 min, comme la source (CIES n° 88, ticket v2-realisme/01d)
# Structure (ticket v2-realisme/02h, seuils proposés, acceptés d'office) : un passage APPEL / TENIR qui met fin à un état
# de moins de 1,5 s est une alternance (même seuil que le diagnostic du 02g) ; côté de l'axe de chaque poste latéral, vu
# de son propre but (-1 = gauche, +1 = droite, convention de `formation._LANE`).
SHORT_SWITCH_S = 1.5
LATERAL_SIDE = {"LB": -1.0, "AG": -1.0, "RB": 1.0, "AD": 1.0}
# Gardien (ticket v2-realisme/03g, seuils proposés, acceptés d'office) : zones du ballon, par distance à son but (bornes de
# `BALL_DISTANCE_M` et de `FACE_RANGE_M`) ; sortie « disputée » quand l'adversaire de champ le plus rapide arrive au point
# visé au plus 2,0 s après le gardien.
KEEPER_ZONES_M = (BALL_DISTANCE_M[0], FACE_RANGE_M, BALL_DISTANCE_M[1])
DISPUTED_WINDOW_S = 2.0
TIGHT_WINDOW_S = 1.0  # sortie « très disputée » : l'adversaire arrive au plus 1,0 s après lui (la fenêtre de 2,0 s en couvre 95 %)
LEAD_CAP_S = 10.0  # avance du gardien sur l'adversaire, plafonnée (aucun adversaire de champ : infinie)
# Saut de cible (ticket v2-realisme/03h, seuils proposés, acceptés d'office) : changement de point visé de plus de 1,0 m entre
# deux instants en placement ; gardien « en course » en placement au-dessus de 5,0 m/s.
BIG_JUMP_M = 1.0
PLACEMENT_RUN_MPS = 5.0
# Issue d'une sortie, par ballon (ticket v2-realisme/03i, seuils du ticket) : qui a le ballon 3 s après la première sortie du
# gardien sur un ballon libre, et tir adverse dans les 5 s après cette sortie.
HELD_AFTER_EXIT_S = 3.0
SHOT_AFTER_EXIT_S = 5.0
# État du ballon à la sortie (ticket v2-realisme/03j, définitions proposées, acceptées d'office) : le tir tracé de l'adversaire
# dans les 5 s qui précèdent la sortie (`SHOT_AFTER_EXIT_S`, plus un tick de retard de lecture) donne l'état par son issue ;
# à défaut, les drapeaux du ballon (`rebound`, `receiver`).
SHOT_MATCH_LAG_S = 0.15
# Calibration de la conduite (ticket v2-realisme/04c, tranches proposées le 08/11/2026, acceptées d'office) : bornes basses
# des tranches de gêne du porteur (0 : aucun adversaire à 5 m ; 1 : au contact) et de Dribbling. Mesure seule.
CARRY_PRESSURE_BINS = (0.0, 0.1, 0.3, 0.5, 0.7, 0.9)
CARRY_DRIBBLING_BINS = (0, 40, 55, 70)
CARRY_PREFIX = "calibration conduite, "
# Calibration de la passe (ticket v2-realisme/18g) : chance évaluée au lancement (`possession.pass_success_probability`,
# celle que lit la décision) contre issue au premier contact : perdue si un adversaire touche le ballon le premier, ou si
# le ballon sort ou est sifflé avec remise pour l'adversaire sans contact (ticket 18h) ; reçue
# par le receveur visé, pour information. Bornes basses des tranches de chance évaluée ; passes de jeu seulement.
PASS_CHANCE_BINS = (0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9)
PASS_PREFIX = "calibration passe, "
# Décomposition du tir (ticket v2-realisme/06b, tranches proposées le 09/11/2026, acceptées d'office) : mêmes bornes que
# Dribbling au 04c ; étalements de l'xG après frappe essayés pour sa calibration (réserve A1 du 06a), en m.
SHOT_NOTE_BINS = CARRY_DRIBBLING_BINS
SHOT_PREFIX = "décomposition du tir, "
PSXG_SPREADS_M = (0.05, 0.1, 0.15, 0.2, 0.3)
SAVE_OUTCOMES = ("but", "capté", "repoussé", "claqué")  # tir cadré jugé par le gardien
# Calibration de l'xG neutre (ticket v2-realisme/06c, tranches posées le 09/11/2026, mesure seule) : bornes basses des
# tranches d'xG neutre ; tireurs « moyens » : note de tir dans [55 ; 70[, autour de la note neutre 60 ; bornes basses de
# l'écart (m) entre le passage du ballon au gardien et sa portée (réserve A2 du 06b).
CALIBRATION_PREFIX = "calibration xG neutre, "
XG_BINS = (0.0, 0.03, 0.06, 0.1, 0.2, 0.35, 0.5)
AVERAGE_NOTE = (55, 70)
REACH_GAP_BINS = (-math.inf, -0.3, -0.15, 0.0, 0.15, 0.3)
KEEPER_GAP_PREFIX = "gardien par écart à la portée, "
STAGES = ("contre", "exécution", "gardien")
Z_95 = 1.96


def wilson(successes: float, n: float, z: float = Z_95) -> tuple[float, float]:
    """Intervalle de Wilson d'une proportion (`successes` sur `n` essais)."""
    p, d = successes / n, 1.0 + z * z / n
    centre, half = (p + z * z / (2.0 * n)) / d, z * math.sqrt(p * (1.0 - p) / n + z * z / (4.0 * n * n)) / d
    return max(0.0, centre - half), min(1.0, centre + half)


def carry_tranche(kind: str, value: float, bins: tuple) -> str:
    """Tranche de `value` parmi les bornes basses `bins` : `kind` suivi de `[bas ; haut[` (la dernière est ouverte)."""
    low = max(b for b in bins if b <= value)
    high = next((b for b in bins if b > low), None)
    return f"{kind} [{low:g} ; {'+' if high is None else format(high, 'g')}["


def shot_decomposition(k: Counter, n_matches: int) -> dict[str, float]:
    """Indicateurs du 06b tirés des comptes de `Collector._decompose_shot` : par tranche, effectifs, xG neutre moyen par
    tir (l'occasion), gain d'exécution et gain du gardien par tir non contré ; calibration de l'xG après frappe par match."""
    out: dict[str, float] = {}
    for key in sorted(k):
        if key.startswith(SHOT_PREFIX) and key.endswith(" : tirs"):
            band = key.removesuffix(" : tirs")
            open_ = max(1, k[band + " : tirs non contrés"])
            out[band + " : tirs (effectif)"] = k[key]
            out[band + " : tirs non contrés (effectif)"] = k[band + " : tirs non contrés"]
            out[band + " : occasion, xG neutre moyen par tir"] = k[band + " : xG neutre"] / k[key]
            out[band + " : exécution, gain par tir non contré"] = (  # contre la chance hors contre (réserve A1 du 06b)
                k[band + " : xG après frappe"] - k[band + " : xG neutre hors contre, non contrés"]) / open_
            out[band + " : gardien, gain par tir non contré"] = (k[band + " : xG après frappe"] - k[band + " : buts"]) / open_
    calibration = "calibration xG après frappe, tirs cadrés jugés"
    for key in sorted(k):
        if key.startswith(calibration + " : xG après frappe"):
            out[key.replace(" : xG après frappe", " : xG après frappe moins buts") + ", par match"] = (
                k[key] - k[calibration + " : buts"]) / max(1, n_matches)
    return out


def xg_calibration(k: Counter, n_matches: int) -> dict[str, float]:
    """Courbe de calibration de l'xG neutre (ticket v2-realisme/06c), tirée des comptes de `Collector._decompose_shot` :
    par groupe de tireurs et tranche d'xG, effectif, xG moyen, taux de buts et son intervalle de Wilson à 95 %, buts
    moins xG par match et ses trois étages (contre + exécution + gardien) ; xG après frappe moins buts par tranche
    d'écart à la portée du gardien (réserve A2 du 06b)."""
    out: dict[str, float] = {}
    per_match = 1.0 / max(1, n_matches)
    for key in sorted(k):
        if key.startswith(CALIBRATION_PREFIX) and key.endswith(" : tirs"):
            band, n = key.removesuffix(" : tirs"), k[key]
            low, high = wilson(k[band + " : buts"], n)
            out[band + " : tirs (effectif)"] = n
            out[band + " : xG neutre moyen"] = k[band + " : xG"] / n
            out[band + " : taux de buts"] = k[band + " : buts"] / n
            out[band + " : taux de buts, IC95 bas"], out[band + " : taux de buts, IC95 haut"] = low, high
            out[band + " : buts moins xG, par match"] = (k[band + " : buts"] - k[band + " : xG"]) * per_match
            for stage in STAGES:
                out[f"{band} : étage {stage}, par match"] = k[f"{band} : étage {stage}"] * per_match
        elif key.startswith(KEEPER_GAP_PREFIX) and key.endswith(" : tirs"):
            band, n = key.removesuffix(" : tirs"), k[key]
            out[band + " : tirs (effectif)"] = n
            out[band + " : xG après frappe moyen"] = k[band + " : xG après frappe"] / n
            out[band + " : taux de buts"] = k[band + " : buts"] / n
            out[band + " : xG après frappe moins buts, par match"] = (
                k[band + " : xG après frappe"] - k[band + " : buts"]) * per_match
    return out


EXIT_STATES = ("tir : but", "tir : à côté", "tir : au-dessus", "tir : dévissé","tir : contré", "tir : repoussé", "tir : claqué", "tir : capté",
               "rebond sans tir récent", "passe ou centre", "autre")
TRANSITIONS = (TRANSITION_OFFENSIVE, TRANSITION_DEFENSIVE)
CROWDED_M = 5.0  # regroupement : coéquipier à moins de 5 m, hors duel (ticket 06)
# Combinaisons (ticket v2-collectif/14, validé le 02/11/2026) : passe « sans gain » sous 5 m vers le but ; passe qui
# fait avancer : elle casse une ligne adverse ou gagne au moins 10 m ; retour au passeur dans les 3 s ; une-deux si le
# passeur a avancé d'au moins 5 m entre sa passe et le retour ; triangle : deux coéquipiers à 30 m au plus, trois
# passes toutes au moins à 0,7 et un angle de 20 à 160 degrés au porteur.
NO_GAIN_M = 5.0
PROGRESSIVE_GAIN_M = 10.0
RETURN_WINDOW_S = 3.0
ONE_TWO_MIN_GAIN_M = 5.0
TRIANGLE_RANGE_M = 30.0
TRIANGLE_ANGLES_DEG = (20.0, 160.0)


def forward(team: str) -> float:
    """+1 si l'équipe attaque vers x croissant (domicile), -1 sinon."""
    return 1.0 if team == "home" else -1.0


def progress(team: str, x: float) -> float:
    """Distance (m) depuis le but de `team` : 0 sur sa ligne de but, PITCH_LENGTH_M sur la ligne adverse."""
    return x if team == "home" else PITCH_LENGTH_M - x


def zone(team: str, x: float) -> str:
    third = progress(team, x) / (PITCH_LENGTH_M / 3.0)
    return ("tiers défensif", "tiers médian", "tiers offensif")[min(2, max(0, int(third)))]


def outfield(players: Sequence[PlayerState], team: str) -> list[PlayerState]:
    return [p for p in players if p.team == team and p.poste != "GK"]


# --- Géométrie d'une équipe ---------------------------------------------------------------------------------------
def length_width(points: Sequence[Vec2]) -> tuple[float, float]:
    xs, ys = [p.x for p in points], [p.y for p in points]
    return max(xs) - min(xs), max(ys) - min(ys)


def hull_area(points: Sequence[Vec2]) -> float:
    """Aire (m²) de l'enveloppe convexe (chaîne monotone d'Andrew, puis formule du lacet)."""
    pts = sorted(set((p.x, p.y) for p in points))
    if len(pts) < 3:
        return 0.0

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lower, upper = [], []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    hull = lower[:-1] + upper[:-1]
    return abs(sum(hull[i][0] * hull[i - 1][1] - hull[i - 1][0] * hull[i][1] for i in range(len(hull)))) / 2.0


def stretch_index(points: Sequence[Vec2]) -> float:
    """Distance moyenne (m) des joueurs au centre de l'équipe."""
    cx, cy = statistics.fmean(p.x for p in points), statistics.fmean(p.y for p in points)
    return statistics.fmean(math.hypot(p.x - cx, p.y - cy) for p in points)


def lines(team: str, points: Sequence[Vec2]) -> list[list[float]]:
    """Trois lignes (défense, milieu, attaque) : progressions triées, coupées aux deux plus grands écarts."""
    xs = sorted(progress(team, p.x) for p in points)
    if len(xs) < 3:
        return [xs]
    gaps = sorted(range(1, len(xs)), key=lambda i: xs[i] - xs[i - 1], reverse=True)[:2]
    a, b = sorted(gaps)
    return [xs[:a], xs[a:b], xs[b:]]


def line_gaps(team: str, points: Sequence[Vec2]) -> tuple[float, float] | None:
    """(défense-milieu, milieu-attaque) en m, entre les positions moyennes des lignes."""
    ls = lines(team, points)
    if len(ls) != 3:
        return None
    means = [statistics.fmean(line) for line in ls]
    return means[1] - means[0], means[2] - means[1]


def breaks_a_line(team: str, start: Vec2, end: Vec2, players: Sequence[PlayerState]) -> bool:
    """Passe qui casse une ligne : la position moyenne d'une ligne adverse (`lines`) est entre le passeur et la cible."""
    rivals = [p.position for p in outfield(players, "away" if team == "home" else "home")]
    a, b = progress(team, start.x), progress(team, end.x)
    return any(a < statistics.fmean(line) < b for line in lines(team, rivals) if line)


def triangle(holder: PlayerState, mates: Sequence[PlayerState], opponents: Sequence[PlayerState]) -> bool:
    """Au moins un triangle de passes autour du porteur (définition du ticket v2-collectif/14)."""
    near = [m for m in mates if m is not holder and holder.position.distance_to(m.position) <= TRIANGLE_RANGE_M
            and pass_success_probability(holder, m, opponents) >= OPTION_PROBABILITY]
    low, high = TRIANGLE_ANGLES_DEG
    for i, a in enumerate(near):
        for b in near[i + 1:]:
            u, v = a.position - holder.position, b.position - holder.position
            cos = (u.x * v.x + u.y * v.y) / max(1e-9, u.length() * v.length())
            if low <= math.degrees(math.acos(max(-1.0, min(1.0, cos)))) <= high \
                    and pass_success_probability(a, b, opponents) >= OPTION_PROBABILITY:
                return True
    return False


def is_deep_pass(team: str, target: Vec2, players: Sequence[PlayerState]) -> bool:
    """Passe en profondeur : sa cible est plus près du but adverse que le dernier défenseur de champ adverse."""
    rivals = outfield(players, "away" if team == "home" else "home")
    last = max((progress(team, p.position.x) for p in rivals), default=None)
    return last is not None and progress(team, target.x) > last


def opponent_goal_center(team: str) -> Vec2:
    """Centre du but que `team` attaque (domicile : x = 105), à la même source que le moteur (`cerveau`)."""
    return OPPONENT_GOAL[team]


def slope(pairs: Sequence[tuple[float, float]]) -> float:
    """Pente de la droite des moindres carrés de y en fonction de x (0 si x ne varie pas)."""
    xs, ys = [a for a, _ in pairs], [b for _, b in pairs]
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    var = sum((x - mx) ** 2 for x in xs)
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / var if var > 0 else 0.0


def block_height(team: str, points: Sequence[Vec2]) -> float:
    """Position moyenne (m) de la ligne défensive depuis son propre but."""
    return statistics.fmean(lines(team, points)[0])


# --- Autour du ballon ---------------------------------------------------------------------------------------------
def local_compactness(ball: Vec2, defenders: Sequence[PlayerState]) -> float:
    """Distance moyenne au ballon (m) des LOCAL_DEFENDERS défenseurs les plus proches."""
    d = sorted(p.position.distance_to(ball) for p in defenders)[:LOCAL_DEFENDERS]
    return statistics.fmean(d) if d else 0.0


def local_superiority(ball: Vec2, defenders: Sequence[PlayerState], attackers: Sequence[PlayerState]) -> int:
    """Défenseurs moins attaquants à moins de LOCAL_RADIUS_M du ballon."""
    near = lambda ps: sum(1 for p in ps if p.position.distance_to(ball) < LOCAL_RADIUS_M)
    return near(defenders) - near(attackers)


def preventive(team: str, ball: Vec2, own: Sequence[PlayerState], opponents: Sequence[PlayerState]) -> tuple[int, int]:
    """(joueurs de `team` derrière le ballon, adversaires dans cette zone) -- défense préventive."""
    line = progress(team, ball.x)
    behind = sum(1 for p in own if progress(team, p.position.x) < line)
    threats = sum(1 for p in opponents if progress(team, p.position.x) < line)
    return behind, threats


def crowded(own: Sequence[PlayerState], opponents: Sequence[PlayerState], holder: str | None = None) -> float | None:
    """Part des joueurs de `own` hors duel (aucun adversaire à moins de PRESS_RADIUS_M) qui ont un coéquipier à
    moins de CROWDED_M -- regroupement (ticket 06). Le porteur `holder` est exclu : se montrer près de lui est du
    soutien, pas du regroupement (critère validé le 31/10/2026). None si tous sont en duel."""
    own = [p for p in own if p.name != holder]
    free = [p for p in own if all(p.position.distance_to(o.position) >= PRESS_RADIUS_M for o in opponents)]
    if not free:
        return None
    return sum(1 for p in free if any(m is not p and p.position.distance_to(m.position) < CROWDED_M for m in own)) / len(free)


def in_cover_zone(holder: Vec2, defended_goal: Vec2, point: Vec2) -> bool:
    """Ellipse de couverture orientée du porteur vers le but défendu : de COVER_BEHIND_M derrière le
    porteur à COVER_AHEAD_M devant lui (côté but), demi-largeur COVER_HALF_WIDTH_M."""
    axis = (defended_goal - holder).normalized()
    rel = point - holder
    along = rel.x * axis.x + rel.y * axis.y
    across = -rel.x * axis.y + rel.y * axis.x
    centre = (COVER_AHEAD_M - COVER_BEHIND_M) / 2.0
    semi = (COVER_AHEAD_M + COVER_BEHIND_M) / 2.0
    return ((along - centre) / semi) ** 2 + (across / COVER_HALF_WIDTH_M) ** 2 <= 1.0


def pressing_cover(holder: PlayerState, defenders: Sequence[PlayerState], defended_goal: Vec2) -> bool | None:
    """None si personne ne presse le porteur ; sinon, un second défenseur est-il dans la zone de couverture ?"""
    pressers = [d for d in defenders if d.position.distance_to(holder.position) < PRESS_RADIUS_M]
    if not pressers:
        return None
    presser = min(pressers, key=lambda d: d.position.distance_to(holder.position))
    return any(d is not presser and in_cover_zone(holder.position, defended_goal, d.position) for d in defenders)


def pass_chances(holder: PlayerState, mates: Sequence[PlayerState], opponents: Sequence[PlayerState]) -> list[float]:
    """Chance de réussite (modèle du moteur) de la passe vers chaque coéquipier à moins de OPTION_RANGE_M."""
    return [pass_success_probability(holder, m, opponents) for m in mates
            if m is not holder and holder.position.distance_to(m.position) <= OPTION_RANGE_M]


def open_options(holder: PlayerState, mates: Sequence[PlayerState], opponents: Sequence[PlayerState],
                 threshold: float = OPTION_PROBABILITY) -> int:
    """Coéquipiers à moins de OPTION_RANGE_M dont la passe arriverait (modèle du moteur) avec au moins `threshold`."""
    return sum(1 for chance in pass_chances(holder, mates, opponents) if chance >= threshold)


# --- Accumulation -------------------------------------------------------------------------------------------------
@dataclass
class Stat:
    """Valeurs d'un indicateur, avec leur découpage (zone, score, minute)."""
    values: list[float] = field(default_factory=list)
    by: dict[tuple[str, str], list[float]] = field(default_factory=lambda: defaultdict(list))

    def add(self, value: float, **keys: str) -> None:
        self.values.append(value)
        for k, v in keys.items():
            self.by[(k, v)].append(value)


def _score_state(goals: Counter, team: str) -> str:
    other = "away" if team == "home" else "home"
    return "mène" if goals[team] > goals[other] else ("menée" if goals[team] < goals[other] else "égalité")


@dataclass
class _Run:
    start_s: float
    last: Vec2
    role: str = ""  # rôle du joueur au départ de la course (ticket v2-realisme/02h)


class Collector:
    """Accumule les indicateurs d'un ou plusieurs matchs. Brancher `on_tick` sur `simulate_match(observer=...)`
    et les `on_*` sur les fonctions du moteur (voir `scripts/measure_v2.py`). Appeler `end_match()` après
    chaque match."""

    def __init__(self, geometry_every_s: float = 1.0) -> None:
        self.every = geometry_every_s
        self.stats: dict[str, Stat] = defaultdict(Stat)
        self.count: Counter = Counter()
        self.peak: dict[str, float] = defaultdict(float)  # maxima sur tous les matchs (ticket v2-realisme/08b)
        self.km: dict[str, list[float]] = defaultdict(list)
        self.matches = 0
        self.minutes = MinuteProfile()  # rendement par tranche de 15 minutes (ticket v2-realisme/19d)
        self._reset_match()

    def _reset_match(self) -> None:
        self.goals: Counter = Counter()
        self.situations = SituationTracker()  # même lecture que le moteur (ticket v2-collectif/03)
        self.dist: Counter = Counter()
        self.hi_by: Counter = Counter()  # course au-dessus de 19,8 km/h par joueur (m)
        self.levels: dict[str, str] = {}  # joueur -> niveau du profil testé ("haut"/"bas"), voir measure_v2
        self.poste: dict[str, str] = {}
        self.sprint = self.hi = self.total = 0.0
        self.hi_time = self.sprint_time = self.time = 0.0
        self.sprint_run: Counter = Counter()  # durée de la course en cours au-dessus de SPRINT_MPS, par joueur (s)
        self.sprints: Counter = Counter()  # sprints d'au moins SPRINT_MIN_S, par joueur (ticket v2-realisme/01d)
        self.hi_first = self.hi_last = 0.0
        self.holder: str | None = None
        self.holder_since = 0.0
        self.team: str | None = None  # équipe en possession (dernier porteur)
        self.team_since = 0.0
        self.team_passes = 0
        self.last_sample = -math.inf
        self.pending_pass: tuple[str, str, float, bool] | None = None  # (équipe, receveur visé, longueur, en profondeur)
        self.players: list[PlayerState] = []  # joueurs au dernier tick (lecture des passes en profondeur)
        self.recoveries: list[tuple[float, str, str, Vec2, bool]] = []  # (instant, équipe, zone, lieu, close)
        self.relost: list[tuple[str, bool]] = []  # par récupération : (zone, reperdu en moins de 5 s)
        self.retreat_done: list[dict] = []
        self.length_out: dict[str, list[float]] = defaultdict(list)  # longueur sans ballon, par équipe
        self.loss_open: dict[str, float] = {}  # équipe qui a perdu -> instant de la perte
        self.retreat: list[dict] = []
        self.runs: dict[str, _Run] = {}
        self.last_call_role: dict[str, str] = {}  # dernier rôle APPEL / TENIR du joueur (ticket 02g)
        self.role_switches: Counter = Counter()  # passages APPEL <-> TENIR, par joueur
        # structure (ticket v2-realisme/02h)
        self.roles: dict[str, str] = {}  # dernier rôle de chaque joueur (Intention.role)
        self.keeper_state: dict[str, str] = {}  # dernier état de chaque gardien (ticket v2-realisme/03d)
        self.shot_chasers: dict[str, bool] = {}  # joueur de champ en course vers un tir en vol (ticket v2-realisme/03k)
        self.call_episodes: Counter = Counter()  # épisodes APPEL (rôle APPEL après un autre rôle), par joueur
        self.call_state: dict[str, tuple[str, float, tuple]] = {}  # joueur -> (APPEL / TENIR, depuis, possession)
        self.possession_switches: Counter = Counter()  # passages APPEL <-> TENIR dans une même possession, par joueur
        self.max_callers: dict[str, int] = {}  # situation -> plus d'appelants simultanés d'une équipe en possession
        self.place_acc: dict[tuple[str, str], list[float]] = {}  # (joueur, phase) -> [échantillons, profondeur, côté]
        # joueur latéral -> [échantillons, du bon côté, échantillons hors transition, du bon côté hors transition]
        self.side_time: dict[str, list[int]] = {}
        # gardien (ticket v2-realisme/03a) : par gardien, distance maximale, somme et nombre d'échantillons (m à son but)
        self.keeper_dist: dict[str, list[float]] = {}
        self.keeper_disputed: dict[str, bool] = {}  # gardien -> sortie en cours disputée (ticket v2-realisme/03g)
        self.keeper_masked: dict[str, str | None] = {}  # gardien -> course gagnante masquée en cours (03g)
        self.keeper_target: dict[str, Vec2 | None] = {}  # gardien -> point visé en placement ou face-à-face (03h)
        # gardien en placement (03h) : [instants, sauts mesurés, somme des sauts, grands sauts, plus grand saut, instants en course]
        self.keeper_place: dict[str, list[float]] = {}
        # ballon libre (03i) : épisode en cours (ni porteur ni ballon mort) avec ses courses masquées et sa première sortie
        self.free_ball: dict | None = None
        self.last_shot: dict[str, float] = {}  # équipe -> instant de son dernier tir (03i)
        self.shot_log: list[tuple[float, str, str]] = []  # tirs tracés du match : (instant en s, équipe, issue) (03j)
        self.shot_notes: dict[tuple[float, str], tuple] = {}  # (minute, tireur) -> (notes, chance neutre hors contre, tireur moyen), 06b, 06c, 05e
        self.exit_log: list[dict] = []  # ballons avec sortie suivis 5 s, à classer par état en fin de match (03j)
        self.exits: list[dict] = []  # premières sorties par ballon encore suivies (3 s puis 5 s) : t, équipe, gardien, tir, issue
        self.run_log: list[tuple[str, float, float, Vec2]] = []  # (joueur, début, fin, position finale)
        self.deep_runs: Counter = Counter()  # appels finis à ON_THE_LINE_M ou moins de la ligne, par joueur (16)
        self.follow: dict[str, list[tuple[float, float]]] = defaultdict(list)  # axe -> (ballon, centre d'équipe)
        self.profile_gaps: dict[str, list[float]] = defaultdict(list)  # niveau -> distances défense-milieu
        self.press_open: tuple[str, float] | None = None  # pressing en cours (ticket 08) : (équipe qui presse, début)
        self.now = 0.0  # instant du dernier tick
        self.carry_open: dict[str, tuple[float, tuple[str, ...]]] = {}  # porteur -> (instant du tirage, tranches), ticket 04c
        # passe en vol mesurée (18g) : équipe, cible, tranche, chance, talonnade (07e)
        self.pass_open: tuple[str, str, str, float, bool] | None = None
        self.planned: str | None = None  # suite prévue par la dernière décision (plan de passe, ticket 14)
        # passes du match (ticket 14) : instant, équipe, passeur, cible, gain (m), avance, suite prévue, réussie
        self.pass_log: list[dict] = []

    # --- événements du moteur ---
    def on_pass(self, passer: PlayerState, target: PlayerState, opponents=None, restart: bool = False,
                backheel: bool = False) -> None:
        self._close_pass_calibration(lost=False, received=False)  # précédente passe sans contact : non perdue
        if opponents is not None and not restart:  # ticket v2-realisme/18g ; talonnade, 07e
            chance = pass_success_probability(passer, target, opponents, backheel)
            self.pass_open = (passer.team, target.name, carry_tranche("chance évaluée", chance, PASS_CHANCE_BINS), chance,
                              backheel)
        length = passer.position.distance_to(target.position)
        self.count["passes"] += 1
        self.count["passes longues"] += length > LONG_PASS_M
        deep = is_deep_pass(passer.team, target.position, self.players)
        self.count["passes en profondeur"] += deep
        self.pending_pass = (passer.team, target.name, length, deep)
        self._line_at_pass(passer)
        self.team_passes += 1
        goal = opponent_goal_center(passer.team)
        gain = passer.position.distance_to(goal) - target.position.distance_to(goal)
        self.pass_log.append({"t": self.now, "team": passer.team, "passer": passer.name, "target": target.name,
                              "gain": gain, "start": passer.position, "end": target.position,
                              "progressive": gain >= PROGRESSIVE_GAIN_M
                              or breaks_a_line(passer.team, passer.position, target.position, self.players),
                              "follow": self.planned, "done": False})

    def _line_at_pass(self, passer: PlayerState) -> None:
        """Jeu sur la ligne (ticket 16) : distance de l'attaquant le plus avancé à la ligne du hors-jeu, à la passe."""
        line = offside_line(passer.team, passer.position, [p for p in self.players if p.team != passer.team])
        mates = [progress(passer.team, p.position.x) for p in self.players
                 if p.team == passer.team and p.poste != "GK" and p.name != passer.name]
        if line is None or not mates:
            return
        gap = line - max(mates)
        self.stats["attaquant le plus avancé à la passe : distance à la ligne (m)"].add(gap)
        self.stats["attaquant le plus avancé à la passe : 2 m ou moins de la ligne (part)"].add(1.0 if gap <= ON_THE_LINE_M else 0.0)
        self.stats["attaquant le plus avancé à la passe : 5 m ou moins de la ligne (part)"].add(1.0 if gap <= NEAR_THE_LINE_M else 0.0)

    def on_shot(self, shooter: PlayerState, now_s: float) -> None:
        self.count["tirs"] += 1
        self.last_shot[shooter.team] = now_s
        for exit_ in self.exits:  # ticket v2-realisme/03i : tir de l'adversaire du gardien dans les 5 s après sa sortie
            exit_["shot"] |= shooter.team != exit_["team"] and 0.0 <= now_s - exit_["t"] <= SHOT_AFTER_EXIT_S + 1e-9
        distance = shooter.position.distance_to(opponent_goal_center(shooter.team))
        self.count["tirs de près"] += distance <= SHOT_CLOSE_RANGE_M
        last = self.recoveries[-1] if self.recoveries else None
        if last is not None and last[1] == shooter.team and now_s - last[0] <= COUNTER_WINDOW_S:
            camp = "camp adverse" if progress(shooter.team, last[3].x) > PITCH_LENGTH_M / 2.0 else "propre camp"
            self.count["tirs de contre, récupération " + camp] += 1

    def on_shot_context(self, shooter: PlayerState, goal: Vec2, keeper: PlayerState | None, opponents) -> None:
        """Au tir (ticket v2-realisme/03b) : chance du tir (`shot_probability`) et position du gardien adverse, à l'écart de la
        bissectrice de l'angle ballon-poteaux et de son point visé (`gardien.placement`). Lecture seule."""
        self.stats["chance du tir (shot_probability)"].add(shot_probability(shooter, goal, keeper, opponents))
        if keeper is None:
            return
        # ticket v2-realisme/03h : le même tir avec le gardien à son point visé, puis sur la bissectrice sans ligne (03b)
        aim = self.keeper_target.get(keeper.name)
        self.stats["gardien au tir : en placement ou face-à-face (part)"].add(0.0 if aim is None else 1.0)
        self.stats["chance du tir : gardien à son point visé"].add(
            shot_probability(shooter, goal, keeper if aim is None else replace(keeper, position=aim), opponents))
        self.stats["chance du tir : gardien sur la bissectrice sans ligne (03b)"].add(shot_probability(
            shooter, goal, replace(keeper, position=bisector_point(keeper, shooter.position)), opponents))
        self.stats["tir : chance de l'endroit (base_chance)"].add(base_chance(shooter.position, goal))
        self.stats["tir : distance au but (m)"].add(shooter.position.distance_to(goal))
        if aim is not None:
            self.stats["gardien au tir : écart à son point visé réel (m)"].add(keeper.position.distance_to(aim))
        direction = bisector_direction(shooter.position, goal)
        offset = keeper.position - shooter.position
        off_line = abs(offset.x * direction.y - offset.y * direction.x)  # distance du gardien à la droite bissectrice
        self.stats["gardien au tir : écart à la bissectrice (m)"].add(off_line)
        self.stats["gardien au tir : écart à la bissectrice sous le seuil (part)"].add(
            1.0 if off_line <= BISECTOR_TOLERANCE_M else 0.0)
        self.stats["gardien au tir : écart au point visé (m)"].add(
            keeper.position.distance_to(bisector_point(keeper, shooter.position)))
        if face_to_face(keeper, shooter, opponents):  # ticket v2-realisme/03e : tir en face-à-face, gardien à cet instant
            speed = keeper.velocity.length()
            self.count["face-à-face : tirs"] += 1
            self.stats["face-à-face : chance du tir"].add(shot_probability(shooter, goal, keeper, opponents))
            self.stats["face-à-face : gardien au tir, vitesse (m/s)"].add(speed)
            self.stats["face-à-face : gardien arrêté au tir (part)"].add(1.0 if speed < FACE_STOPPED_MPS else 0.0)
            self.stats["face-à-face : gardien au tir, distance à sa ligne (m)"].add(abs(keeper.position.x - goal.x))
            self.stats["face-à-face : tireur au tir, distance au but (m)"].add(shooter.position.distance_to(goal))
            # ticket v2-realisme/03g (réserve A2 du 03e) : écart à la profondeur visée pour cette distance de tir
            self.stats["face-à-face : gardien au tir, écart à la profondeur visée (m)"].add(
                abs(abs(keeper.position.x - goal.x) - face_depth(shooter.position.distance_to(goal))))

    def on_keeper(self, keeper: PlayerState, intention, ball=None, players=None) -> None:
        """État du gardien à ce tick (ticket v2-realisme/03d, lu dans la raison de son intention) : sorties (épisodes),
        sorties réussies (de la sortie à la relance : il a le ballon), distance du point visé à son but, part hors de sa
        surface, ballons libres à sa portée qu'il laisse (il reste en placement : adversaire plus rapide ou trop loin).
        Avec le ballon et les joueurs (ticket v2-realisme/03g) : sorties disputées et leur issue, courses gagnantes que le
        filtre de portée lui fait laisser."""
        state = intention.reason.split(" :", 1)[0]
        if state == PLACEMENT and "garde sa place" in intention.reason:
            state = "placement, tir en vol" if "tir en vol" in intention.reason else "placement, ballon libre laissé"  # 03k
        previous = self.keeper_state.get(keeper.name)
        self.keeper_state[keeper.name] = state
        placed = state.startswith(PLACEMENT)
        last_target = self.keeper_target.get(keeper.name)
        if placed:  # ticket v2-realisme/03h : saut du point visé entre deux instants en placement, et course
            acc = self.keeper_place.setdefault(keeper.name, [0.0] * 6)
            acc[0] += 1
            acc[5] += keeper.velocity.length() > PLACEMENT_RUN_MPS
            if previous is not None and previous.startswith(PLACEMENT) and last_target is not None:
                jump = intention.target.distance_to(last_target)
                acc[1] += 1
                acc[2] += jump
                acc[3] += jump > BIG_JUMP_M
                acc[4] = max(acc[4], jump)
        self.keeper_target[keeper.name] = intention.target if placed or state == FACE_A_FACE else None
        if state == FACE_A_FACE and previous != FACE_A_FACE:  # ticket v2-realisme/03e : épisodes de face-à-face
            self.count["gardien : face-à-face"] += 1
        if state == SORTIE and previous != SORTIE:
            opponent = "away" if keeper.team == "home" else "home"
            self.count["gardien : sorties"] += 1
            self.stats["gardien : sortie, point visé à son but (m)"].add(intention.target.distance_to(own_goal(keeper.team)))
            self.count["gardien : sorties hors de sa surface"] += not in_penalty_area(opponent, intention.target)
            if ball is not None and players is not None:  # ticket v2-realisme/03g : un adversaire arrive-t-il aussi ?
                lead = race(keeper, ball, players)
                self.keeper_disputed[keeper.name] = lead.rival_s - lead.keeper_s <= DISPUTED_WINDOW_S
                self.count["gardien : sorties disputées"] += self.keeper_disputed[keeper.name]
                self.count["gardien : sorties très disputées"] += lead.rival_s - lead.keeper_s <= TIGHT_WINDOW_S
                self.stats["gardien : sortie, avance sur l'adversaire (s)"].add(
                    min(LEAD_CAP_S, lead.rival_s - lead.keeper_s))
        elif previous == SORTIE and state == RELANCE:
            self.count["gardien : sorties réussies"] += 1
            if self.keeper_disputed.pop(keeper.name, False):
                self.count["gardien : sorties disputées gagnées"] += 1
        elif state == "placement, tir en vol" and previous != state:  # ticket v2-realisme/03k : épisodes, les deux gardiens
            self.count["gardien : placements sur tir en vol"] += 1
        elif state == "placement, ballon libre laissé" and previous != state:
            self.count["gardien : ballons libres laissés"] += 1
        if ball is not None and state == SORTIE:  # ticket v2-realisme/03i : la première sortie de ce ballon libre
            free = self._free_ball(ball)
            if free is not None and free["exit"] is None:
                since = [self.now - t for team, t in self.last_shot.items() if team != keeper.team]
                free["exit"] = {"t": self.now, "team": keeper.team, "keeper": keeper.name, "shot": False, "held": None,
                                "from_shot": any(0.0 <= s <= SHOT_AFTER_EXIT_S for s in since),  # le ballon est un tir adverse
                                "rebound": bool(ball.rebound), "receiver": ball.receiver is not None}  # état du ballon (03j)
                self.exits.append(free["exit"])
        if ball is not None and players is not None:
            self._masked_race(keeper, ball, players, state)

    def on_dribble(self, holder: PlayerState, opponents, lost: bool) -> None:
        """Ticket v2-realisme/04a : un tirage de perte de conduite (un par intervalle de décision), selon la gêne du porteur
        (0 : aucun adversaire à 5 m ; 1 : au contact)."""
        gene = pressure(holder, opponents)
        classes = ["conduite"] + (["conduite libre"] if gene < 0.1 else []) + (["conduite serrée"] if gene >= 0.5 else [])
        for name in classes:
            self.count[name + " : intervalles"] += 1
            self.count[name + " : pertes"] += bool(lost)
        # ticket v2-realisme/04c : risque évalué (la fonction que lit l'évaluation de l'option) contre perte tirée, par tranche
        expected = dribble_loss_probability(holder, gene, DECISION_INTERVAL_S)
        tranches = (carry_tranche("gêne", gene, CARRY_PRESSURE_BINS),
                    carry_tranche("Dribbling", player_attribute(holder, "Dribbling"), CARRY_DRIBBLING_BINS))
        for tranche in tranches:
            self.count[f"{CARRY_PREFIX}{tranche} : intervalles"] += 1
            self.count[f"{CARRY_PREFIX}{tranche} : risque évalué (somme)"] += expected
            self.count[f"{CARRY_PREFIX}{tranche} : pertes"] += bool(lost)
        if lost:
            self.carry_open.pop(holder.name, None)
        else:
            self.carry_open[holder.name] = (self.now, tranches)  # intervalle ouvert : un tacle gagné avant le suivant le ferme

    def on_contact(self, player: PlayerState, controlled: bool) -> None:
        """Ticket v2-realisme/18g : premier joueur qui touche une passe en vol ; ferme la mesure de calibration ouverte."""
        if self.pass_open is not None:
            team, target, _, _, _ = self.pass_open
            self._close_pass_calibration(lost=player.team != team, received=player.name == target and controlled)

    def _close_pass_calibration(self, lost: bool, received: bool) -> None:
        if self.pass_open is None:
            return
        _, _, tranche, chance, backheel = self.pass_open
        if backheel:  # talonnades (ticket v2-realisme/07e)
            self.count["talonnades"] += 1
            self.count["talonnades : chance évaluée (somme)"] += chance
            self.count["talonnades : non perdues"] += not lost
            self.count["talonnades : reçues par le receveur visé"] += received
        for group in ("toutes", tranche):
            base = f"{PASS_PREFIX}{group} : "
            self.count[base + "passes"] += 1
            self.count[base + "chance évaluée (somme)"] += chance
            self.count[base + "non perdues"] += not lost
            self.count[base + "reçues par le receveur visé"] += received
        self.pass_open = None

    def on_tackle_won(self, holder: PlayerState, tackler: PlayerState | None = None) -> None:
        """Ticket v2-realisme/04c : tacle gagné sur un porteur en conduite, pendant l'intervalle qui suit son tirage (le tacle
        est tiré à part du risque de conduite, 04a). Compté dans les tranches de cet intervalle."""
        self.minutes.count(self.now / 60.0, "tacles gagnés", actor=tackler.name if tackler else None)  # 19d
        opened = self.carry_open.pop(holder.name, None)
        if opened is not None and self.now - opened[0] < DECISION_INTERVAL_S - 1e-9:
            for tranche in opened[1]:
                self.count[f"{CARRY_PREFIX}{tranche} : pertes par tacle"] += 1

    def on_lost_carry(self, dispossessed: bool) -> None:
        """Ticket v2-realisme/04b : issue d'un ballon perdu en conduite, dépossession par l'adversaire ou touche trop longue."""
        self.count["conduite : dépossessions" if dispossessed else "conduite : touches trop longues"] += 1

    def on_shot_chaser(self, player: PlayerState, intention, ball) -> None:
        """Ticket v2-realisme/03k : joueurs de champ en rôle `BALLON_LIBRE` (ils courent vers le ballon) pendant un tir en vol,
        en épisodes par joueur et par tir. Mesure seule : le ticket ne les modifie pas."""
        chasing = intention.role == BALLON_LIBRE and ball.shot_in_flight
        if chasing and not self.shot_chasers.get(player.name):
            kind = "tir à côté" if ball.shot_wide else "tir qui entre"
            self.count[f"{kind} en vol : joueurs de champ en course vers le ballon"] += 1
        self.shot_chasers[player.name] = chasing

    def _free_ball(self, ball) -> dict | None:
        """Épisode de ballon libre en cours (ticket v2-realisme/03i) : de la perte du porteur à la prise du ballon par un
        joueur ou à l'arrêt du jeu. Un ballon dont l'état du gardien clignote reste un seul ballon. `None` si le ballon est
        tenu ou mort."""
        if ball.holder is not None or ball.restart is not None:
            return None
        if self.free_ball is None:
            self.free_ball = {"masked": set(), "exit": None}
        return self.free_ball

    def _close_free_ball(self) -> None:
        """Fin de l'épisode : les courses gagnantes masquées sont comptées une fois par ballon et par catégorie."""
        for kind in self.free_ball["masked"] if self.free_ball else ():
            self.count["gardien : ballons avec course gagnante masquée, " + kind] += 1
        self.free_ball = None

    def _follow_exits(self, ball, by_name) -> None:
        """Suit les premières sorties par ballon : issue à `HELD_AFTER_EXIT_S`, comptage à `SHOT_AFTER_EXIT_S`."""
        if self.free_ball is not None and self._free_ball(ball) is None:
            self._close_free_ball()
        for exit_ in list(self.exits):
            age = self.now - exit_["t"]
            if exit_["held"] is None and age >= HELD_AFTER_EXIT_S - 1e-9:
                holder = by_name.get(ball.holder)
                exit_["held"] = ("arrêt : " + (ball.restart.kind if ball.restart.kind in (GOAL_KICK, CORNER, KICKOFF) else "autre")
                                 if ball.restart is not None else "libre" if holder is None
                                 else "gardien" if holder.name == exit_["keeper"]
                                 else "coéquipier" if holder.team == exit_["team"] else "adversaire")
            if age >= SHOT_AFTER_EXIT_S - 1e-9:
                self.exits.remove(exit_)
                self._count_exit(exit_)

    def _exit_state(self, exit_: dict) -> str:
        """État du ballon à la première sortie (ticket v2-realisme/03j) : issue du dernier tir de l'adversaire dans les 5 s qui
        précèdent, sinon drapeaux du ballon (rebond, passe) ; `autre` : dégagement, déviation, ballon perdu."""
        shots = [(t, outcome) for t, team, outcome in self.shot_log
                 if team != exit_["team"] and -SHOT_MATCH_LAG_S <= exit_["t"] - t <= SHOT_AFTER_EXIT_S]
        if shots:
            return "tir : " + max(shots)[1]
        return "rebond sans tir récent" if exit_["rebound"] else "passe ou centre" if exit_["receiver"] else "autre"

    def _classify_exits(self) -> None:
        for exit_ in self.exit_log:
            state = self._exit_state(exit_)
            self.count["gardien : ballons avec sortie, état : " + state] += 1
            self.count[f"gardien : ballons avec sortie, état : {state}, ballon à 3 s : " + exit_["held"]] += 1
            if not exit_["from_shot"]:  # croisement avec le « hors tir » du 03i (réserve A1 du 03i, critère 4 du 03j)
                self.count["gardien : ballons avec sortie hors tir du 03i, état : " + state] += 1
                self.count[f"gardien : ballons avec sortie hors tir du 03i, état : {state}, corner"] += exit_["held"] == "arrêt : corner"
        self.exit_log = []

    def _count_exit(self, exit_: dict) -> None:
        self.exit_log.append(exit_)
        self.count["gardien : ballons avec sortie"] += 1
        self.count["gardien : ballons avec sortie, ballon à 3 s : " + exit_["held"]] += 1
        self.count["gardien : ballons avec sortie, tir adverse dans les 5 s"] += exit_["shot"]
        self.count["gardien : ballons avec sortie, tir adverse dans les 5 s avant"] += exit_["from_shot"]
        if not exit_["from_shot"]:  # les ballons qui ne sont pas des tirs (passe en profondeur, rebond, dégagement)
            self.count["gardien : ballons avec sortie hors tir"] += 1
            self.count["gardien : ballons avec sortie hors tir, ballon à 3 s : " + exit_["held"]] += 1

    def _masked_race(self, keeper: PlayerState, ball, players, state: str) -> None:
        """Ticket v2-realisme/03g (réserve A1 du 03d) : ballon libre (pas une passe de son équipe) que le gardien gagnerait
        face aux adversaires mais qu'il laisse parce qu'il est à `CHASE_RADIUS_M` ou plus et que ce n'est pas le plus
        proche de son équipe (filtre de portée). Épisodes ; `coéquipier` : le plus proche de son équipe arrive avant
        l'adversaire le plus rapide (le filtre a raison), `battu` : il arrive après (course perdue pour l'équipe)."""
        own_pass = ball.receiver is not None and ball.last_pass_team == keeper.team
        outside = (ball.holder is None and not own_pass and state.startswith(PLACEMENT)
                   and keeper.position.distance_to(ball.position) >= CHASE_RADIUS_M
                   and not nearest_of_team(keeper, ball, players))
        kind = None
        if outside:
            lead = race(keeper, ball, players)
            if lead.rush:
                mates = [arrival_time_s(p, lead.point) for p in players if p.team == keeper.team and p is not keeper]
                kind = "coéquipier" if min(mates, default=math.inf) <= lead.rival_s else "battu"
        if kind is not None and self.keeper_masked.get(keeper.name) != kind:
            self.count["gardien : course gagnante masquée, " + kind] += 1
        free = self._free_ball(ball) if kind is not None else None
        if free is not None:  # ticket v2-realisme/03i : la même course, comptée une fois par ballon
            free["masked"].add(kind)
        self.keeper_masked[keeper.name] = kind

    def on_trigger(self) -> None:
        self.count["pressings d'équipe déclenchés"] += 1

    def on_tackle(self, tackler: PlayerState | None = None) -> None:
        self.count["tacles"] += 1
        self.minutes.count(self.now / 60.0, "tacles", actor=tackler.name if tackler else None)  # ticket v2-realisme/19d

    def on_decisions(self, decisions) -> None:
        """Rotation avant la passe ou le tir (ticket v2-realisme/07e) : décisions avec rotation et sa durée."""
        for d in decisions:
            # champ de vision du porteur à la décision (ticket v2-realisme/08a)
            self.count["vision : décisions"] += 1
            self.count["vision : adversaires non vus (somme)"] += d.unseen_opponents
            self.count["vision : adversaires non vus à 5 m (somme)"] += d.unseen_near
            self.count["vision : décisions avec un adversaire non vu à 5 m"] += d.unseen_near > 0
            if d.unseen_opponents > 0:  # mémoire du porteur sur ceux qu'il ne voit pas (ticket v2-realisme/08b)
                self.count["mémoire : décisions avec un adversaire non vu"] += 1
                self.count["mémoire : âge de la dernière vue (somme, s)"] += d.memory_age_s
                self.count["mémoire : erreur moyenne (somme, m)"] += d.memory_error_mean_m
                self.peak["mémoire : erreur maximale du porteur (m)"] = max(
                    self.peak["mémoire : erreur maximale du porteur (m)"], d.memory_error_max_m)
            if d.action in ("pass", "shot"):
                kind = "passes" if d.action == "pass" else "tirs"
                self.count[f"rotation : {kind} décidés"] += 1
                if d.rotation_s > 0.0:
                    self.count[f"rotation : {kind} décidés avec rotation"] += 1
                    self.count[f"rotation : {kind}, durée (somme, s)"] += d.rotation_s

    def on_receptions(self, receptions) -> None:
        """Mémoire du receveur sur les adversaires qu'il ne voit pas à la réception (ticket v2-realisme/08b) ; un joueur
        qui les voit tous ne compte pas (âge nul)."""
        for r in receptions:
            self.count["mémoire : réceptions"] += 1
            if r.memory_age_s > 0.0:
                self.count["mémoire : réceptions avec un adversaire non vu"] += 1
                self.count["mémoire : âge à la réception (somme, s)"] += r.memory_age_s
                self.count["mémoire : erreur à la réception (somme, m)"] += r.memory_error_mean_m
                self.peak["mémoire : erreur maximale du receveur (m)"] = max(
                    self.peak["mémoire : erreur maximale du receveur (m)"], r.memory_error_max_m)

    def on_events(self, events) -> None:
        """Journal du match (`MatchTrace.events`, ticket v2-realisme/19b) : contrôles ratés et buteurs par tranche,
        attribués au joueur (19d). Ticket 19f (réserve A2 de l'expert sur le 19d) : un contrôle raté n'est compté comme
        tel que sur une passe ou une remise de son équipe qui le vise ; tout autre contact raté (interception manquée,
        ballon libre, passe visant un coéquipier) est compté à part. Un but contre son camp n'est pas un but personnel
        (réserve A3)."""
        for event in events:
            if event.kind == PERTE and event.detail == "rotation":  # ticket v2-realisme/07e
                self.count["rotation : ballons perdus en se retournant"] += 1
            if event.kind == CONTROLE_RATE:
                cause = events[event.cause] if event.cause is not None else None
                aimed = (cause is not None and cause.kind in (PASSE, REMISE) and cause.team == event.team
                         and cause.other == event.player)
                self.minutes.count(event.minute, "contrôles ratés" if aimed else "contacts ratés", actor=event.player)
            elif event.kind == BUT and event.player is not None and self.minutes.team(event.player) == event.team:
                self.minutes.count(event.minute, "buts personnels", actor=event.player)

    def on_choice(self, kind: str, follow: str | None = None, plan: str | None = None) -> None:
        self.count["choix " + kind] += 1
        self.planned = follow
        if plan is not None:  # sort du plan reçu (ticket 14)
            self.count["plans reçus"] += 1
            self.count["plan " + plan] += 1
        holder = next((p for p in self.players if p.name == self.holder), None)
        if holder is not None:  # triangles autour du porteur, à chaque décision (ticket 14)
            mates = [p for p in self.players if p.team == holder.team]
            rivals = [p for p in self.players if p.team != holder.team]
            self.stats["décisions avec au moins un triangle (part)"].add(1.0 if triangle(holder, mates, rivals) else 0.0)

    def on_balance(self, player: PlayerState, stays: bool) -> None:
        """Défenseur d'équilibre dont l'appel le mènerait devant le ballon : y va-t-il quand même ? (ticket 06)"""
        key = "équilibre : appels devant le ballon maintenus (part)"
        level = self.levels.get(player.name)
        self.stats[f"profil {level} : {key}" if level else key].add(0.0 if stays else 1.0)

    def on_role(self, name: str, role: str) -> None:
        """Rôle d'un joueur à ce tick : compte les passages APPEL <-> TENIR (ticket v2-realisme/02g, réserve A2), puis, au
        ticket v2-realisme/02h, les épisodes APPEL et les passages APPEL <-> TENIR à l'intérieur d'une même possession
        (deux rôles qui se suivent sans autre rôle entre eux ; `self.now` retarde d'un tick, les durées n'en pâtissent pas)."""
        previous = self.roles.get(name)
        self.roles[name] = role
        if role == APPEL and previous != APPEL:
            self.call_episodes[name] += 1
        if role in (APPEL, TENIR):
            if self.last_call_role.get(name, role) != role:
                self.role_switches[name] += 1
            self.last_call_role[name] = role
        possession = (self.team, self.team_since)
        state = self.call_state.get(name)
        if role not in (APPEL, TENIR):
            self.call_state.pop(name, None)
        elif state is None or state[2] != possession:
            self.call_state[name] = (role, self.now, possession)
        elif state[0] != role:
            short = self.now - state[1] < SHORT_SWITCH_S
            self.possession_switches[name] += 1
            self.count["passages APPEL / TENIR dans une possession"] += 1
            self.count["passages APPEL / TENIR dans une possession, état de moins de 1,5 s"] += short
            if state[0] == APPEL:  # un appel qui s'arrête : le vrai clignotement (TENIR -> APPEL est le délai d'Off the Ball)
                self.count["appels arrêtés dans une possession"] += 1
                self.count["appels arrêtés dans une possession, en moins de 1,5 s"] += short
            self.call_state[name] = (role, self.now, possession)

    def on_offside(self, event) -> None:
        """Hors-jeu sifflé (ticket v2-collectif/23) ; `event` : `v2engine.trace.OffsideEvent`."""
        self.count["hors-jeu"] += 1
        self.count["hors-jeu " + event.team] += 1

    def on_restart(self, event) -> None:
        """Remise en jeu jouée (ticket v2-collectif/29) ; `event` : `v2engine.trace.RestartEvent`."""
        self.count["remises : " + event.kind] += 1
        self.count["remises jouées long : " + event.kind] += event.long
        self.count["temps de ballon mort (s)"] += event.dead_s
        if event.kind == "coup franc" and _final_third(event.team, event.x):
            self.count["coups francs du dernier tiers"] += 1
            self.count["coups francs du dernier tiers frappés"] += event.shot

    def on_shot_event(self, event) -> None:
        """Tir tracé avec son issue et son origine (ticket v2-collectif/28b) ; `event` : `v2engine.trace.ShotEvent`."""
        self.count["tirs tracés"] += 1
        self.minutes.on_shot(event.minute, event.outcome, actor=getattr(event, "player", None))  # ticket v2-realisme/19d
        self.shot_log.append((event.minute * 60.0, event.team, event.outcome))  # ticket v2-realisme/03j
        self.count["tirs : " + event.outcome] += 1
        self.count["tirs, origine : " + event.origin] += 1
        self.count["qualité des occasions (somme)"] += event.quality
        if event.outcome == "but" and in_penalty_area(event.team, Vec2(event.x, event.y)):
            self.count["buts dans la surface"] += 1
        for key, name in (("xG neutre", "xg"), ("xG après frappe", "post_shot_xg")):  # ticket v2-realisme/06a
            value = getattr(event, name, None)
            if value is not None:
                self.count[key + " (somme)"] += value
                self.count[key + " (tirs)"] += 1
        self._decompose_shot(event)
        exit_deg = getattr(event, "block_exit_deg", None)
        if exit_deg is not None:  # direction de sortie des tirs contrés (ticket v2-realisme/05d)
            band = next(label for limit, label in BLOCK_EXIT_BANDS if exit_deg < limit)
            self.count["tirs contrés, sortie " + band] += 1
        keeper_s = getattr(event, "keeper_time_s", None)  # événement construit à la main dans les tests : sans ce champ
        if keeper_s is not None and event.outcome in ("but", "capté", "repoussé", "claqué"):
            # tir cadré jugé par le gardien (ticket v2-realisme/05h) : arrêté ou non, par distance et par vitesse au gardien
            distance = Vec2(event.x, event.y).distance_to(OPPONENT_GOAL[event.team])
            speed = getattr(event, "keeper_speed_mps", None)  # tracée depuis le 05c (réserve A4 du 05h)
            if speed is None:
                speed = SHOT_SPEED_MPS * BALL_FRICTION_PER_S ** keeper_s
            for kind, value, bands in (("distance", distance, SAVE_DISTANCE_BANDS), ("vitesse", speed, SAVE_SPEED_BANDS)):
                band = next(label for limit, label in bands if value < limit)
                self.count[f"tirs cadrés jugés, {kind} {band}"] += 1
                self.count[f"tirs cadrés arrêtés, {kind} {band}"] += event.outcome != "but"

    def on_shot_notes(self, minute: float, shooter: PlayerState, keeper: PlayerState | None, opponents) -> None:
        """Au tir (ticket v2-realisme/06b) : tranches de notes qui jouent sur ce tir, lues au moment de la frappe ; le tir
        tracé (`on_shot_event`) les retrouve par sa minute et son tireur."""
        surface = in_penalty_area(shooter.team, shooter.position)
        kind = "Finishing (surface)" if surface else "Long Shots (hors surface)"
        notes = ["tous", carry_tranche(kind, shooting_note(shooter), SHOT_NOTE_BINS)]
        if shot_pressure(shooter, OPPONENT_GOAL[shooter.team], opponents) > 0.0:
            notes.append(carry_tranche("Composure sous pression", player_attribute(shooter, "Composure"), SHOT_NOTE_BINS))
        if keeper is not None:
            notes.append(carry_tranche("Reflexes du gardien", player_attribute(keeper, "Reflexes"), SHOT_NOTE_BINS))
        # ticket 06c : chance neutre hors contre (celle de l'xG neutre sans les contres ; ticket 05e) et tireur « moyen »
        open_chance = neutral_open_chance(shooter, OPPONENT_GOAL[shooter.team], keeper, opponents)
        average = AVERAGE_NOTE[0] <= shooting_note(shooter) < AVERAGE_NOTE[1]
        self.shot_notes[(minute, shooter.name)] = (notes, open_chance, average)

    def _decompose_shot(self, event) -> None:
        """Occasion, exécution, gardien (ticket v2-realisme/06b) : xG neutre (l'occasion), xG après frappe moins xG neutre
        (l'exécution, tirs non contrés), xG après frappe moins buts (le gardien), par tranche de notes ; calibration de
        l'xG après frappe sur les tirs cadrés jugés (réserve A1 du 06a). Penaltys exclus (pas d'xG neutre)."""
        xg, psxg = getattr(event, "xg", None), getattr(event, "post_shot_xg", None)
        if xg is None:
            return
        goal = event.outcome == "but"
        notes, open_chance, average = self.shot_notes.get((event.minute, event.player), (["tous"], None, False))
        open_xg = xg if open_chance is None else open_chance  # chance neutre hors contre (réserve A1 du 06b, ticket 05e)
        for note in notes:
            key = SHOT_PREFIX + note
            self.count[key + " : tirs"] += 1
            self.count[key + " : xG neutre"] += xg
            if psxg is not None:
                self.count[key + " : tirs non contrés"] += 1
                self.count[key + " : xG neutre hors contre, non contrés"] += open_xg
                self.count[key + " : xG après frappe"] += psxg
                self.count[key + " : buts"] += goal
        # ticket 06c : buts moins xG = contre + exécution + gardien, tir par tir
        stages = ({"contre": goal - xg} if psxg is None else
                  {"contre": open_xg - xg, "exécution": psxg - open_xg, "gardien": goal - psxg})
        band = carry_tranche("xG", xg, XG_BINS)
        for group in ("tous les tireurs", "tireurs moyens") if average else ("tous les tireurs",):
            for tranche in (band, "toutes tranches"):
                key = f"{CALIBRATION_PREFIX}{group}, {tranche}"
                self.count[key + " : tirs"] += 1
                self.count[key + " : xG"] += xg
                self.count[key + " : buts"] += goal
                for stage, value in stages.items():
                    self.count[f"{key} : étage {stage}"] += value
        if psxg is None or event.outcome not in SAVE_OUTCOMES:
            return
        calibration = "calibration xG après frappe, tirs cadrés jugés"
        self.count[calibration + " : tirs"] += 1
        self.count[calibration + " : buts"] += goal
        self.count[calibration + " : xG après frappe"] += psxg
        gap, elapsed = getattr(event, "keeper_gap_m", None), getattr(event, "keeper_time_s", None)
        for spread in PSXG_SPREADS_M:  # même formule que `shooting.post_shot_xg`, à un autre étalement
            z = 0.0 if gap is None else max(-50.0, min(50.0, (gap - keeper_reach_m(elapsed)) / spread))
            value = psxg if gap is None else 1.0 / (1.0 + math.exp(-z))
            self.count[f"{calibration} : xG après frappe à l'étalement {spread:g} m"] += value
        if gap is not None:  # réserve A2 du 06b : le gain du gardien par écart à sa portée
            key = KEEPER_GAP_PREFIX + carry_tranche("écart (m)", gap - keeper_reach_m(elapsed), REACH_GAP_BINS)
            self.count[key + " : tirs"] += 1
            self.count[key + " : xG après frappe"] += psxg
            self.count[key + " : buts"] += goal

    def on_chance(self, event) -> None:
        """Grosse occasion, avec ou sans tir (ticket v2-collectif/28c) ; `event` : `v2engine.trace.ChanceEvent`."""
        self.count["grosses occasions"] += 1
        self.count["grosses occasions sans tir"] += not event.shot
        self.count["grosses occasions : danger au pic (somme)"] += event.danger
        self.count["grosses occasions, issue : " + event.outcome] += 1
        self.count["grosses occasions, origine : " + event.origin] += 1

    def on_foul(self, event) -> None:
        """Faute (ticket v2-collectif/30) ; `event` : `v2engine.trace.FoulEvent`."""
        self.count["fautes"] += 1
        self.count["fautes : " + event.outcome] += 1
        self.count["fautes : gravité " + event.severity] += 1
        level = self.levels.get(event.player)
        if level:
            self.count[f"profil {level} : fautes"] += 1

    # --- tick ---
    def on_tick(self, now_s: float, players: list[PlayerState], ball, scoring_team: str | None, dt: float = 0.1) -> None:
        minute = now_s / 60.0
        self.now = now_s
        by_name = {p.name: p for p in players}
        self.players = players
        if self.pass_open is not None and ball.holder is None and ball.receiver is None:
            # sans contact : sortie ou sifflée avec remise adverse, perdue (18h) ; morte ou remise pour soi, non perdue (18g)
            restart = getattr(ball, "restart", None)
            self._close_pass_calibration(lost=restart is not None and restart.team != self.pass_open[0], received=False)
        self._speeds(players, minute, dt)
        if scoring_team is not None:  # but : la possession se clôt, l'engagement n'est pas une perte de balle
            self.goals[scoring_team] += 1
            self.count["buts"] += 1
            self.minutes.on_goal(minute, scoring_team,  # ticket v2-realisme/19d
                                 [(p.name, p.team) for p in players if p.poste != "GK"])
            self._close_possession(now_s)
        current = self.situations.update(now_s, ball, players, scoring_team)
        for team, situation in current.items():
            self.count["temps en " + situation] += dt
        self._possession(now_s, ball, by_name)
        self._follow_exits(ball, by_name)
        if self.team is not None:
            self._callers(players)
            self._runs(now_s, players, ball)
        self._retreat(now_s, players, ball)
        self._pressing(now_s, players, ball, by_name, dt)
        if now_s - self.last_sample >= self.every - 1e-9:
            self.last_sample = now_s
            self._geometry(now_s, players, ball, by_name)

    def _speeds(self, players, minute, dt):
        for p in players:
            self.poste[p.name] = p.poste
            if p.poste == "GK":
                far = p.position.distance_to(opponent_goal_center("away" if p.team == "home" else "home"))
                acc = self.keeper_dist.setdefault(p.name, [0.0, 0.0, 0])
                acc[0], acc[1], acc[2] = max(acc[0], far), acc[1] + far, acc[2] + 1
                continue
            v = p.velocity.length()
            depth = progress(p.team, p.position.x) if self.team is not None and self.team != p.team else None
            self.minutes.on_player(minute, p.name, p.poste, p.stamina, v, dt, depth, p.team)  # tickets 19d et 19f
            self.dist[p.name] += v * dt
            self.total += v * dt
            self.time += dt
            if v > SPRINT_MPS:
                self.sprint += v * dt
                self.sprint_time += dt
                self.sprint_run[p.name] += dt
            else:
                self._close_sprint(p.name)
            if v > HIGH_INTENSITY_MPS:
                self.hi += v * dt
                self.hi_by[p.name] += v * dt
                self.hi_time += dt
                if minute < 15.0:
                    self.hi_first += v * dt
                elif minute >= 75.0:
                    self.hi_last += v * dt

    def _close_sprint(self, name: str) -> None:
        if self.sprint_run.pop(name, 0.0) >= SPRINT_MIN_S - 1e-9:
            self.sprints[name] += 1

    def _close_possession(self, now_s):
        if self.holder is not None:
            self.stats["temps par possession de joueur (s)"].add(now_s - self.holder_since)
        if self.team is not None:
            self.stats["possession d'équipe (s)"].add(now_s - self.team_since)
            self.stats["passes par possession"].add(self.team_passes)
            self._close_recovery(now_s, relost=False)
        self.holder = self.team = self.pending_pass = None
        self.loss_open.clear()
        self.retreat_done.extend(self.retreat)
        self.retreat = []

    def _close_recovery(self, now_s, relost: bool):
        """Clôt la dernière récupération de l'équipe en possession : reperdue en moins de 5 s ou non."""
        if self.recoveries and self.recoveries[-1][1] == self.team and not self.recoveries[-1][4]:
            t, team, rz, where, _ = self.recoveries[-1]
            self.recoveries[-1] = (t, team, rz, where, True)
            self.relost.append((rz, relost and now_s - t < TRANSITION_LOSS_S))

    def _possession(self, now_s, ball, by_name):
        holder = ball.holder
        if holder == self.holder:
            return
        if self.holder is not None:
            self.stats["temps par possession de joueur (s)"].add(now_s - self.holder_since)
        self.holder, self.holder_since = holder, now_s
        if holder is None:
            return
        team = by_name[holder].team
        if self.pending_pass is not None:
            pass_team, target, length, deep = self.pending_pass
            self.count["passes en profondeur réussies"] += team == pass_team and deep
            self.count["passes réussies"] += team == pass_team
            self.count["passes longues réussies"] += team == pass_team and length > LONG_PASS_M
            self.count["passes chez l'adversaire"] += team != pass_team
            self.count["receveur visé"] += holder == target
            if holder == target and self.pass_log:
                self.pass_log[-1]["done"] = True
            self.pending_pass = None
        if team == self.team:
            return
        if self.team is not None:  # changement d'équipe en possession : perte pour self.team
            self.stats["possession d'équipe (s)"].add(now_s - self.team_since)
            self.stats["passes par possession"].add(self.team_passes)
            lost = self.team
            z = zone(team, by_name[holder].position.x)
            self._close_recovery(now_s, relost=True)
            self.recoveries.append((now_s, team, z, by_name[holder].position, False))
            if team in self.loss_open:  # l'équipe qui récupère avait perdu le ballon : temps de récupération
                waited = now_s - self.loss_open.pop(team)
                label = next(name for limit, name in RECOVERY_CLASSES if waited < limit)
                self.count["récupération " + label] += 1
                self.count["récupérations"] += 1
            self.loss_open[lost] = now_s
            self.retreat.append({"team": lost, "start": now_s, "latency": None, "speeds": [], "lengths": [],
                                 "behind": None, "length0": None, "choice": None})
            self.count["pertes de balle"] += 1
        self.team, self.team_since, self.team_passes = team, now_s, 0

    def _callers(self, players) -> None:
        """Appelants simultanés de l'équipe en possession (rôle APPEL), par situation de jeu (ticket v2-realisme/02h)."""
        situation = self.situations.current[self.team]
        callers = sum(1 for p in players if p.team == self.team and self.roles.get(p.name) == APPEL)
        self.max_callers[situation] = max(self.max_callers.get(situation, 0), callers)
        self.count["appelants simultanés, somme : " + situation] += callers
        self.count["appelants simultanés, instants : " + situation] += 1
        cap = cerveau.CALLER_CAP.get(situation)  # plafond du moteur (lu à l'appel : `--sans-tenir` le vide)
        if cap is not None and callers > cap:
            self.count["appelants simultanés au-dessus du plafond, instants : " + situation] += 1

    def _log_run(self, name: str, run: _Run, end_s: float, where: Vec2) -> None:
        """Un appel du banc est compté ; on garde le rôle que le joueur avait au départ de la course (02h, réserve A1 du
        02g : un joueur qui tient sa place et rejoint sa position à pleine vitesse est compté par le banc)."""
        self.run_log.append((name, run.start_s, end_s, where))
        self.count["appels du banc, rôle au départ : " + (run.role or "inconnu")] += 1

    def _runs(self, now_s, players, ball):
        for p in players:
            if p.name == ball.holder and p.name in self.runs:  # appel conclu par la réception : il compte
                run = self.runs.pop(p.name)
                if now_s - run.start_s >= RUN_MIN_S:
                    self._log_run(p.name, run, now_s, p.position)
                    self._deep_run(p.name, p.team, p.position, players, ball)
                continue
            if p.team != self.team or p.poste == "GK" or p.name == ball.holder:
                self.runs.pop(p.name, None)  # ponytail: appel interrompu par une perte de balle, non compté
                continue
            if p.velocity.length() > RUN_SPEED_MPS:
                run = self.runs.get(p.name)
                if run is None:
                    run = self.runs[p.name] = _Run(now_s, p.position, self.roles.get(p.name, ""))
                run.last = p.position
            elif p.name in self.runs:
                run = self.runs.pop(p.name)
                if now_s - run.start_s >= RUN_MIN_S and self._creates_option(p, players, ball):
                    self._log_run(p.name, run, now_s, run.last)
                    self._deep_run(p.name, p.team, run.last, players, ball)

    def _deep_run(self, name: str, team: str, end: Vec2, players, ball) -> None:
        line = offside_line(team, ball.position, [p for p in players if p.team != team])
        if line is not None and progress(team, end.x) >= line - ON_THE_LINE_M:
            self.deep_runs[name] += 1

    def _creates_option(self, runner: PlayerState, players, ball) -> bool:
        """Un appel compte s'il crée une option de passe : receveur visé d'une passe en cours, ou solution
        ouverte pour le porteur à la fin de la course (même seuil que `open_options`)."""
        if ball.holder is None:
            return runner.name == ball.receiver
        holder = next((p for p in players if p.name == ball.holder), None)
        if holder is None or holder.team != runner.team:
            return False
        opponents = [p for p in players if p.team != runner.team]
        return (holder.position.distance_to(runner.position) <= OPTION_RANGE_M
                and pass_success_probability(holder, runner, opponents) >= OPTION_PROBABILITY)

    def _retreat(self, now_s, players, ball=None):
        """Repli après une perte, suivi RETREAT_WINDOW_S : latence, vitesse de recul, longueur d'équipe."""
        still = []
        for r in self.retreat:
            elapsed = now_s - r["start"]
            if elapsed > RETREAT_WINDOW_S or self.team == r["team"]:  # fenêtre finie ou ballon récupéré
                self.retreat_done.append(r)
                continue
            own = outfield(players, r["team"])
            back = -forward(r["team"]) * statistics.fmean(p.velocity.x for p in own)  # centre vers son but
            if r["latency"] is None and back > RETREAT_SPEED_MPS:
                r["latency"] = elapsed
            r["speeds"].append(back)
            length = length_width([p.position for p in own])[0]
            if r["length0"] is None:
                r["length0"] = length
            r["lengths"].append((elapsed, length))
            if r["choice"] is None and ball is not None:  # joueurs devant le ballon à la perte (ticket 10)
                r["choice"] = {p.name for p in own if forward(r["team"]) * (p.position.x - ball.position.x) > 0.0}
            elif r["choice"] and elapsed >= CHOICE_AFTER_S:
                self._retreat_speeds(r, own)
                r["choice"] = set()
            if r["behind"] is None and elapsed >= 1.0 and ball is not None:  # 1 s après la perte (au tick près)
                r["behind"], _ = preventive(r["team"], ball.position, own, ())
                self.stats["4 joueurs ou plus derrière le ballon 1 s après la perte (part)"].add(
                    1.0 if r["behind"] >= 4 else 0.0)
            still.append(r)
        self.retreat = still

    def _retreat_speeds(self, r, own):
        """Ticket 10 : 1,5 s après la perte, vitesse vers son but des joueurs qui étaient devant le ballon (profils
        Work Rate)."""
        for p in own:
            if p.name in r["choice"]:
                back = -forward(r["team"]) * p.velocity.x
                self.stats["repli : vitesse des joueurs devant le ballon à 1,5 s (m/s)"].add(back)
                level = self.levels.get(p.name)
                if level:
                    self.stats[f"profil {level} : vitesse de repli à 1,5 s (m/s)"].add(back)

    def _pressing(self, now_s, players, ball, by_name, dt):
        """Ticket 08 : pressings (un défenseur passe à moins de PRESS_RADIUS_M du porteur) suivis d'une récupération
        de l'équipe qui presse dans les 5 s ; profils : temps passé à presser et distance presseur-porteur."""
        holder = by_name.get(ball.holder) if ball.holder else None
        if self.press_open is not None and self.team == self.press_open[0]:
            self.count["pressings suivis d'une récupération en 5 s"] += now_s - self.press_open[1] <= 5.0
            self.press_open = None
        if self.press_open is not None and now_s - self.press_open[1] > 5.0:
            self.press_open = None
        if holder is None:
            return
        rivals = [p for p in players if p.team != holder.team and p.poste != "GK"]
        presser = min(rivals, key=lambda p: p.position.distance_to(holder.position), default=None)
        if presser is None or presser.position.distance_to(holder.position) >= PRESS_RADIUS_M:
            return
        if self.press_open is None:
            self.press_open = (presser.team, now_s)
            self.count["pressings"] += 1
        level = self.levels.get(presser.name)
        if level:
            self.count[f"profil {level} : temps de pressing (s)"] += dt
            self.stats[f"profil {level} : distance presseur-porteur (m)"].add(presser.position.distance_to(holder.position))

    def _place(self, team: str, own: Sequence[PlayerState], phase: str) -> None:
        """Place de chaque joueur de champ, vue de son propre but : profondeur (m depuis sa ligne de but) et côté (m depuis
        l'axe, négatif = gauche de l'équipe, positif = droite) ; et, pour les postes latéraux, part du temps passée du côté
        de leur poste, au total et hors transition (ticket v2-realisme/02h). Un échantillon par appel à `_geometry`."""
        sign = forward(team)
        transition = self.situations.current[team] in TRANSITIONS
        for p in own:
            lateral = sign * (p.position.y - PITCH_WIDTH_M / 2.0)
            acc = self.place_acc.setdefault((p.name, phase), [0, 0.0, 0.0])
            acc[0] += 1
            acc[1] += progress(team, p.position.x)
            acc[2] += lateral
            side = LATERAL_SIDE.get(p.poste)
            if side is not None:
                ok = lateral * side > 0.0
                t = self.side_time.setdefault(p.name, [0, 0, 0, 0])
                t[0] += 1
                t[1] += ok
                if not transition:
                    t[2] += 1
                    t[3] += ok

    def _keeper_behind_line(self, team: str, players, ball, height: float) -> None:
        """Ticket v2-realisme/03c : ballon à `BALL_DISTANCE_M[1]` ou plus du but de `team`, distance (m) de son gardien à sa
        ligne de but et écart à la ligne défensive réelle (hauteur moyenne de sa dernière ligne), par tranche de ligne."""
        keeper = next((p for p in players if p.team == team and p.poste == "GK"), None)
        if keeper is None or progress(team, ball.position.x) < BALL_DISTANCE_M[1]:
            return
        band = "ligne < 25 m" if height < 25.0 else "ligne 25-35 m" if height < 35.0 else "ligne >= 35 m"
        depth = progress(team, keeper.position.x)
        self.stats[f"gardien, ballon loin : distance à sa ligne, {band} (m)"].add(depth)
        self.stats[f"gardien, ballon loin : écart à la ligne défensive, {band} (m)"].add(height - depth)

    def _keeper_by_zone(self, team: str, players, ball) -> None:
        """Ticket v2-realisme/03g : distance (m) du gardien de `team` à sa ligne de but, par zone du ballon (distance du ballon
        à son but : moins de 12 m, 12 à 25 m, 25 à 40 m, 40 m et plus)."""
        keeper = next((p for p in players if p.team == team and p.poste == "GK"), None)
        if keeper is None:
            return
        far = ball.position.distance_to(own_goal(team))
        low, mid, high = KEEPER_ZONES_M
        zone_name = (f"moins de {low:.0f} m" if far < low else f"{low:.0f} à {mid:.0f} m" if far < mid
                     else f"{mid:.0f} à {high:.0f} m" if far < high else f"{high:.0f} m et plus")
        self.stats[f"gardien, ballon à {zone_name} : distance à sa ligne (m)"].add(progress(team, keeper.position.x))

    def _geometry(self, now_s, players, ball, by_name):
        minute = now_s / 60.0
        sl = f"{int(minute // 15) * 15}-{int(minute // 15) * 15 + 15} min"
        for team in ("home", "away"):
            own = outfield(players, team)
            pts = [p.position for p in own]
            if len(pts) < 3:
                continue
            phase = "avec ballon" if team == self.team else "sans ballon"
            self._place(team, own, phase)
            seen = zone(self.team, ball.position.x) if self.team else "sans possession"  # vue de l'équipe en possession
            keys = {"zone": seen, "score": _score_state(self.goals, team), "minute": sl,
                    "situation": self.situations.current[team]}
            length, width = length_width(pts)
            self.stats[f"longueur {phase} (m)"].add(length, **keys)
            if phase == "sans ballon":
                self.length_out[team].append(length)
            self.stats[f"largeur {phase} (m)"].add(width, **keys)
            self.stats[f"surface {phase} (m²)"].add(hull_area(pts), **keys)
            self.stats[f"stretch index {phase} (m)"].add(stretch_index(pts), **keys)
            gaps = line_gaps(team, pts)
            if gaps:
                self.stats[f"distance défense-milieu {phase} (m)"].add(gaps[0], **keys)
                self.stats[f"distance milieu-attaque {phase} (m)"].add(gaps[1], **keys)
            height = block_height(team, pts)
            self.stats[f"hauteur du bloc {phase} (m)"].add(height, **keys)
            if phase == "sans ballon":
                self.minutes.on_block(minute, height)  # par tranche de temps joué (ticket v2-realisme/19f)
            self._keeper_behind_line(team, players, ball, height)
            self._keeper_by_zone(team, players, ball)
            holder = by_name.get(ball.holder) if ball.holder else None
            if phase == "sans ballon":  # ticket 05 : ligne et ballon, pression sur le porteur
                self.stats["écart ligne-ballon sans ballon (m)"].add(progress(team, ball.position.x) - height, **keys)
                if holder is not None and holder.team != team:
                    gap = min(p.position.distance_to(holder.position) for p in own)
                    if gap < PRESS_RADIUS_M or gap >= FREE_PASSER_M:
                        state = "pressé" if gap < PRESS_RADIUS_M else "libre"
                        self.stats[f"hauteur du bloc sans ballon, porteur {state} (m)"].add(height, **keys)
                        self.stats[f"écart ligne-ballon sans ballon, porteur {state} (m)"].add(
                            progress(team, ball.position.x) - height, **keys)  # à position du ballon comparable
            self.follow["longueur"].append((ball.position.x, statistics.fmean(p.x for p in pts)))
            self.follow["largeur"].append((ball.position.y, statistics.fmean(p.y for p in pts)))
            packed = crowded(own, outfield(players, "away" if team == "home" else "home"), self.holder)
            if packed is not None:
                self.stats[f"regroupement {phase} : coéquipiers à moins de 5 m hors duel (part)"].add(packed, **keys)
            level = self.levels.get(own[0].name)
            if level:  # profils : compacité de l'équipe haute contre l'équipe basse
                self.stats[f"profil {level} : stretch index (m)"].add(stretch_index(pts))
                self.stats[f"profil {level} : longueur (m)"].add(length)
                if phase == "sans ballon":
                    self.stats[f"profil {level} : hauteur du bloc sans ballon (m)"].add(height)
                if gaps:
                    self.profile_gaps[level].append(gaps[0])
        if self.team is None:
            return
        att, dfd = self.team, ("away" if self.team == "home" else "home")
        keys = {"zone": zone(att, ball.position.x), "score": _score_state(self.goals, att), "minute": sl,
                "situation": self.situations.current[dfd]}  # vue de l'équipe qui défend : ces indicateurs la décrivent
        defenders, attackers = outfield(players, dfd), outfield(players, att)
        self.stats["compacité autour du ballon (m)"].add(local_compactness(ball.position, defenders), **keys)
        self.stats["supériorité locale des défenseurs (nombre)"].add(local_superiority(ball.position, defenders, attackers), **keys)
        behind, threats = preventive(att, ball.position, attackers, outfield(players, dfd))
        self.stats["défense préventive : joueurs derrière le ballon"].add(behind, **keys)
        self.stats["défense préventive : adversaires dans cette zone"].add(threats, **keys)
        level = self.levels.get(attackers[0].name) if attackers else None
        if self.situations.current[att] == POSSESSION_INSTALLEE:  # équilibre derrière le ballon (ticket 06)
            self.stats["possession installée : au moins 1 joueur derrière le ballon (part)"].add(1.0 if behind >= 1 else 0.0, **keys)
            if level:
                self.stats[f"profil {level} : possession installée, 2 joueurs ou plus derrière le ballon (part)"].add(
                    1.0 if behind >= 2 else 0.0)
        holder = by_name.get(ball.holder) if ball.holder else None
        if holder is not None:
            goal = Vec2(0.0 if dfd == "home" else PITCH_LENGTH_M, PITCH_WIDTH_M / 2.0)
            cover = pressing_cover(holder, defenders, goal)
            if cover is not None:
                self.stats["couverture du presseur (part)"].add(1.0 if cover else 0.0, **keys)
            mates = [p for p in players if p.team == holder.team]
            all_opponents = [p for p in players if p.team == dfd]  # gardien compris, comme dans le moteur
            chances = pass_chances(holder, mates, all_opponents)
            options = sum(1 for c in chances if c >= OPTION_PROBABILITY)
            easy = sum(1 for c in chances if c >= EASY_OPTION_PROBABILITY)
            self.stats["solutions de passe ouvertes (nombre)"].add(options, **keys)
            self.stats["solutions de passe faciles (nombre)"].add(easy, **keys)
            if chances:
                self.stats["réussite moyenne des passes disponibles (part)"].add(sum(chances) / len(chances), **keys)
            for m in mates:  # réserve A3 du 02g : l'appelant retenu est-il une solution de passe pour le porteur ?
                if m is not holder and self.roles.get(m.name) == APPEL:
                    free = (holder.position.distance_to(m.position) <= OPTION_RANGE_M
                            and pass_success_probability(holder, m, all_opponents) >= OPTION_PROBABILITY)
                    self.stats["appelant retenu : passe ouverte pour le porteur (part)"].add(1.0 if free else 0.0, **keys)
            if level:
                self.stats[f"profil {level} : solutions de passe ouvertes (nombre)"].add(options)
                space = [min(m.position.distance_to(o.position) for o in all_opponents)
                         for m in mates if m is not holder and m.poste != "GK"]
                if space and all_opponents:  # critère reporté du ticket cerveau 03 (ticket 16)
                    self.stats[f"profil {level} : espace des coéquipiers du porteur (m)"].add(statistics.fmean(space))
            defending = self.levels.get(defenders[0].name) if defenders else None
            if defending:  # ticket 08 : solutions laissées au porteur par l'équipe haute ou basse
                self.stats[f"profil {defending} : solutions laissées au porteur adverse (nombre)"].add(options)
                self.stats[f"profil {defending} : solutions faciles laissées au porteur adverse (nombre)"].add(easy)

    def end_match(self) -> None:
        self._close_pass_calibration(lost=False, received=False)  # dernière passe sans contact (ticket v2-realisme/18g)
        self.matches += 1
        for name, d in self.dist.items():
            if self.poste.get(name) != "GK":
                self.km[self.poste[name]].append(d / 1000.0)
                self.km["tous"].append(d / 1000.0)
        if self.total > 0:
            self.stats["distance au-dessus de 25 km/h (part)"].add(self.sprint / self.total)
            self.stats["temps au-dessus de 19,8 km/h (part)"].add(self.hi_time / self.time)
            # ticket v2-realisme/01d : la source mesure la distance (repère R6), le temps reste suivi
            self.stats["distance au-dessus de 19,8 km/h (part)"].add(self.hi / self.total)
            self.stats["temps au-dessus de 25 km/h (part)"].add(self.sprint_time / self.time)
        for name in list(self.sprint_run):  # sprint encore en cours au coup de sifflet final
            self._close_sprint(name)
        if self.hi_first > 0:
            self.stats["baisse de la course intense en fin de match (part)"].add(1.0 - self.hi_last / self.hi_first)
        for r in self.retreat_done + self.retreat:
            if r["latency"] is not None:
                self.stats["repli : latence (s)"].add(r["latency"])
            if r["speeds"]:
                self.stats["repli : vitesse de recul (m/s)"].add(statistics.fmean(r["speeds"]))
            if self.length_out[r["team"]] and r["length0"] is not None:
                # bloc reformé : longueur revenue sous sa médiane sans ballon du match (calcul a posteriori),
                # seulement si le bloc était plus long que cette médiane au moment de la perte
                ref = statistics.median(self.length_out[r["team"]])
                t = None if r["length0"] <= ref else next((e for e, length in r["lengths"] if length <= ref), None)
                if t is not None:
                    self.stats["repli : temps pour reformer le bloc (s)"].add(t)
        self._close_recovery(math.inf, relost=False)  # dernière récupération du match
        for z, lost in self.relost:
            self.stats["pertes en transition (part des récupérations)"].add(1.0 if lost else 0.0, zone=z)
        per_player = Counter(name for name, *_ in self.run_log)
        for name, poste in self.poste.items():  # tous les joueurs de champ, y compris ceux sans appel
            if poste != "GK":
                self.stats[f"appels par joueur et par match : {poste}"].add(per_player.get(name, 0))
                self.stats["alternances appel / tenir par joueur et par match"].add(self.role_switches[name])
                self.stats["passages APPEL / TENIR dans une possession par joueur et par match"].add(
                    self.possession_switches[name])  # ticket v2-realisme/02h, réserve A2 du 02g
                # ticket v2-realisme/01d : par poste, à côté des km (repères R4 à R6)
                self.stats[f"distance au-dessus de 19,8 km/h par joueur (m) : {poste}"].add(self.hi_by[name])
                self.stats[f"sprints par joueur et par match : {poste}"].add(self.sprints[name])
                self.stats["sprints par joueur et par match"].add(self.sprints[name])
                if self.now > 0:
                    per_90 = per_player.get(name, 0) * MATCH_90_S / self.now
                    self.stats[f"appels par joueur et par 90 min : {poste}"].add(per_90)
                    self.stats["appels par joueur et par 90 min"].add(per_90)
                    episodes = self.call_episodes[name] * MATCH_90_S / self.now  # ticket v2-realisme/02h, réserve A1 du 02g
                    self.stats[f"épisodes APPEL par joueur et par 90 min : {poste}"].add(episodes)
                    self.stats["épisodes APPEL par joueur et par 90 min"].add(episodes)
        for n, jumps, total, big, most, running in self.keeper_place.values():  # saut de cible du gardien en placement (03h)
            if jumps:
                self.stats["gardien en placement : saut de cible moyen (m)"].add(total / jumps)
                self.stats["gardien en placement : saut de cible de plus de 1 m (part)"].add(big / jumps)
                self.stats["gardien en placement : saut de cible maximal du match (m)"].add(most)
            if n:
                self.stats["gardien en placement : en course à plus de 5 m/s (part)"].add(running / n)
        for far_max, far_sum, n in self.keeper_dist.values():  # le gardien et son but (ticket v2-realisme/03a)
            self.stats["distance maximale du gardien à son but (m)"].add(far_max)
            self.stats["distance moyenne du gardien à son but (m)"].add(far_sum / n)
        for situation, most in self.max_callers.items():  # plus d'appelants simultanés d'une équipe, ce match
            self.stats["appelants simultanés d'une équipe, maximum du match : " + situation].add(most)
        for (name, phase), (n, depth, lateral) in self.place_acc.items():  # place moyenne par poste et par phase (02h)
            poste = self.poste.get(name)
            if poste and poste != "GK" and n:
                self.stats[f"place moyenne {phase} : {poste} : profondeur (m)"].add(depth / n)
                self.stats[f"place moyenne {phase} : {poste} : côté (m, négatif = gauche)"].add(lateral / n)
        for name, (n, ok, n_calm, ok_calm) in self.side_time.items():
            poste = self.poste[name]
            self.stats[f"part du temps du côté de son poste : {poste}"].add(ok / n)
            if n_calm:
                self.stats[f"part du temps du côté de son poste, hors transition : {poste}"].add(ok_calm / n_calm)
        redundant = 0
        for a, s1, e1, p1 in self.run_log:
            if any(b != a and s2 < e1 and s1 < e2 and p1.distance_to(p2) < RUN_SAME_ZONE_M
                   for b, s2, e2, p2 in self.run_log):
                redundant += 1
        if self.run_log:
            self.stats["appels redondants (part)"].add(redundant / len(self.run_log))
        for name, level in self.levels.items():  # profils : même mesure, attribut haut contre bas
            if self.poste.get(name) not in (None, "GK"):
                self.stats[f"profil {level} : course intense par joueur (m)"].add(self.hi_by[name])
                self.stats[f"profil {level} : appels par joueur"].add(per_player.get(name, 0))
                self.stats[f"profil {level} : appels dans le dos par joueur"].add(self.deep_runs[name])
                self.stats[f"profil {level} : km par joueur"].add(self.dist[name] / 1000.0)
        for axis, pairs in self.follow.items():  # pente : part du déplacement du ballon suivie par le centre d'équipe
            if len(pairs) > 2:
                self.stats[f"suivi du ballon par le bloc, {axis} (pente)"].add(slope(pairs))
        for level, gaps in self.profile_gaps.items():
            if len(gaps) > 1:
                self.stats[f"profil {level} : écart-type distance défense-milieu (m)"].add(statistics.pstdev(gaps))
        self.count["appels"] += len(self.run_log)
        self.count["durée de match (s)"] += self.now  # temps additionnel compris (ticket v2-realisme/01d)
        self.count["gardien : ballons avec sortie, non résolus en fin de match"] += len(self.exits)  # moins de 5 s de suivi
        if self.free_ball is not None:
            self._close_free_ball()
        self._classify_exits()
        self.count["appels dans le dos"] += sum(self.deep_runs.values())
        self._combinations()
        self.minutes.end_match(self.pass_log)  # ticket v2-realisme/19d
        self._reset_match()

    def _combinations(self) -> None:
        """Enchaînements de passes du match (ticket v2-collectif/14)."""
        k = self.count
        for p, q in zip(self.pass_log, self.pass_log[1:] + [None]):
            if not p["done"]:
                continue
            k["passes réussies (journal)"] += 1
            nxt = q if q is not None and q["passer"] == p["target"] and q["team"] == p["team"] else None
            if p["gain"] < NO_GAIN_M:  # C2 du ticket 13
                k["passes sans gain réussies"] += 1
                k["passes sans gain suivies d'une passe qui fait avancer"] += nxt is not None and nxt["progressive"]
            if nxt is None:
                continue
            if nxt["target"] == p["passer"] and nxt["t"] - p["t"] <= RETURN_WINDOW_S:
                k["retours au passeur en 3 s"] += 1
                one_two = progress(p["team"], nxt["end"].x) - progress(p["team"], p["start"].x) >= ONE_TWO_MIN_GAIN_M
                k["une-deux"] += one_two
            if p["follow"] is not None and nxt["target"] == p["follow"] and nxt["done"]:
                k["troisième homme (suite prévue jouée et réussie)"] += 1


def _final_third(team: str, x: float) -> bool:
    """Le point `x` est-il dans le dernier tiers que `team` attaque (domicile attaque vers x = 105) ?"""
    return x >= 70.0 if team == "home" else x <= 35.0

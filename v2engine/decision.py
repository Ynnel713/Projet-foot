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

from v2engine.attributes import success_probability
from v2engine.condition import effective_rating
from v2engine.contextes import IDEE_DE_PREMIERE, LECTURE_DU_PRESSING, contextual_rating
from v2engine.danger import danger, loss_cost
from v2engine.flux import DECISION, DUEL, PERCEPTION
from ligue1sim.pitch_geometry import PENALTY_AREA_WIDTH_M
from v2engine.geometry import PITCH_LENGTH_M, PITCH_WIDTH_M, Vec2, in_penalty_area
from v2engine.movement import PlayerState, max_speed_mps, turn_rate_rad_s
from v2engine.off_ball import OPEN_LANE_PROBABILITY
from v2engine.offside import is_clearly_offside, pass_margin_m, perceived_defence_line
from v2engine.possession import (BACKHEEL_MAX_M, BALL_FRICTION_PER_S, BALL_STOPPED_MPS, LONG_PASS_M, max_pass_reach_m,
                                  control_probability, keeper_kick_reach_m,
                                  pass_success_probability,
                                  pressure)
from v2engine.shooting import SHOOTING_RANGE_M, shot_outcome_shares

# Constantes produit validées par le propriétaire (24/10/2026).
DECISION_INTERVAL_S = 0.5  # le porteur réévalue ses options deux fois par seconde
# Vitesse balle au pied (ticket v2-realisme/04d, constantes proposées le 08/11/2026, validées d'office ; chiffres réels :
# non trouvés, ordres de grandeur) : part de la vitesse max (Pace reste la vitesse max). Sans adversaire à 5 m : 0,85 à
# Dribbling 55 (valeur d'avant), 0,90 à 99, 0,80 à 11 (courbe commune des attributs) ; au contact, jusqu'à
# `CONTACT_SLOWDOWN` de cette part en moins, au prorata de la gêne. Une seule fonction, `dribble_speed_factor`, sert à
# l'évaluation de l'espace atteint (`free_point`) et au déplacement du porteur (`cerveau`).
_CARRY_SPEED = (0.85, 0.05)  # baseline, amplitude (Dribbling)
CONTACT_SLOWDOWN = 0.15
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
# Se réorienter avant l'action (ticket v2-realisme/07e, constantes recommandées et validées par délégation du
# propriétaire, 13/11/2026 ; chiffres réels non trouvés). Une passe ou un tir dans une direction éloignée du cap
# (`PlayerState.facing`, 07a) part après la rotation qui manque : (angle - cône libre) / vitesse de rotation (Agility,
# 07f). Cône libre : ± 90° pour la passe (intérieur ou extérieur du pied jusqu'à son côté), ± 60° pour le tir (une
# frappe demande un corps plus face au but). Pendant la rotation, il garde le ballon sous la même loi de perte que la
# conduite (`keep_ball_probability` rapportée à la durée) : la décision l'applique à la valeur de l'option, l'exécution
# la tire avec le même délai (`match`). La conduite se réoriente au ticket 07b.
PASS_FREE_CONE_DEG = 90.0
SHOT_FREE_CONE_DEG = 60.0
# Sélection des frappes de loin (ticket v2-realisme/18m, valeur validée par le propriétaire le 21/11/2026). Hors de la
# surface, le porteur ne frappe que si la frappe vaut, à ses yeux, au moins `LONG_SHOT_MARGIN` de plus que la meilleure
# option pour continuer (même monnaie que `shot_value` et `option_value` : points de chance de but). Elle entre dans la
# règle de choix de `choose_action` : sur la valeur perçue (le choix reste brouillé par Decisions) et sur le meilleur
# choix factuel (`best`, `gap`), jugé avec la même règle ; la valeur des options (`evaluate_options`) et l'exécution
# (Long Shots) ne changent pas. Pas sur coup de pied arrêté (frappe directe). Premier essai à 0,03 (50 matchs appariés) :
# tirs hors surface de 12,86 à 7,04 par équipe, cible non atteinte (environ 4,1, Opta) ; 0,05 retenu par le propriétaire.
# Ramenée à 0 au ticket v2-realisme/05l (22/11/2026, recommandation retenue par délégation du propriétaire) : elle
# compensait une frappe de loin surévaluée (chance d'un tir propre environ deux fois la table cible). Gardien et visée
# recalés, 50 matchs appariés : 0,05 -> 0,55 tir hors surface par équipe, 0,02 -> 1,17, 0 -> 2,64 (repère environ 4,1),
# conversion hors surface 7,6 % (réel 4,2 %). Règle gardée (constante réglable).
LONG_SHOT_MARGIN = 0.0
# Talonnade (même ticket) : vers un coéquipier dans le dos (hors du cône de la passe) à `BACKHEEL_MAX_M` au plus, la
# passe part sans rotation, plus difficile (`possession.BACKHEEL_DIFFICULTY`, Technique). Flair règle la chance qu'il
# y pense à cette décision (docs/CARTE_ATTRIBUTS_V2.md : tendance à tenter l'inattendu) ; la valeur de l'option tranche
# ensuite. Courbe commune : baseline, amplitude, min, max (99 -> 0,12, 55 -> 0,06, 11 -> 0,005). Fréquence visée : 1 à 4
# talonnades par match (ordre de grandeur, borne haute StatsBomb : 5,2 passes « Other » par match) ; premier essai à
# 0,30 / 0,15 / 0,01 : 7,9 par match sur 12 matchs, d'où ces valeurs (réglage du 13/11/2026, par délégation).
_BACKHEEL_IDEA = (0.06, 0.06, 0.005, 0.2)
# Jeu à une touche (ticket v2-collectif/31a, valeurs proposées et validées par le propriétaire le 13/11/2026) : à la
# réception d'une passe au sol qui lui est destinée, le receveur pense à jouer de première selon la moyenne de First
# Touch et Technique (linéaire ; proposé à 11 -> 8 %, 55 -> 22 %, 99 -> 40 %, niveau calé ensuite comme validé, x 1,75 :
# 5,2 % puis 9,1 % des passes décidées sur 6 matchs), et plus souvent sous pression (x 1,5 au contact :
# faute de temps pour contrôler ; la précision baisse, elle, par `possession.pass_difficulty`). Il décide alors tout de
# suite (Decisions, `choose_action`) ; si son choix est une passe sans rotation (07e), elle part de première, sinon il
# contrôle comme avant. Réel : 7,4 à 9,3 % des passes au pied du jeu courant partent au moment de la réception (calcul
# du 13/11/2026 sur les données ouvertes StatsBomb, 45 matchs : Ligue 1 et Premier League 2015-16, Bundesliga 2023-24 ;
# méthode StatsBomb, écart de 0,0 s entre la réception et la passe) : niveau à caler sur environ 9 %.
_ONE_TOUCH_IDEA_POINTS: tuple[tuple[float, float], ...] = ((11.0, 0.14), (55.0, 0.385), (99.0, 0.70))
ONE_TOUCH_PRESSURE_GAIN = 0.5
# Ligne fermée pendant la rotation (même ticket, réserve A1 de l'expert ; constante recommandée et validée par délégation
# du propriétaire, 13/11/2026) : il renonce à la passe si sa chance de réussite est passée sous `OPEN_LANE_PROBABILITY`
# en perdant au moins `LANE_CLOSED_DROP` depuis la décision. Sans cette marge (toute baisse sous 0,7), 65 passes par
# match étaient abandonnées sur de petites variations (baisse médiane 0,13 ; 8 matchs) ; avec 0,3 : environ 16 par match,
# les lignes réellement coupées.
LANE_CLOSED_DROP = 0.3
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

# Troisième homme en construction (ticket v2-collectif/15b1, constantes validées par le propriétaire le 17/11/2026,
# constat avant le code : 8,3 troisièmes hommes par match, 9,6 % des passes courtes de construction, sans être cherchés).
# Sous pressing (`bloc.build_up_pressed`), le porteur lit la structure du pressing, une fois par décision (flux
# décision), avec la chance `reads_third_man_probability` (contexte « lecture du pressing ») : 11 -> 15 %, 55 -> 45 %,
# 99 -> 80 %. S'il la lit, la suite du receveur (ticket 13) vers un coéquipier libre DERRIÈRE la première ligne, quand
# le receveur est devant elle ou sur elle, vaut `1 + THIRD_MAN_BONUS` fois plus : le pressing cassé vaut plus que la
# position atteinte, encore basse dans son camp. Première ligne : le `FIRST_LINE_RANK`-ième adversaire de champ le plus
# proche de son but. Valeurs non trouvées (choix de modèle) ; repère réel : non trouvé.
_READS_THIRD_MAN = ((11.0, 0.15), (55.0, 0.45), (99.0, 0.80))  # (note du contexte, chance de lire)
FIRST_LINE_RANK = 3
THIRD_MAN_BONUS = 0.5

# Relance longue (ticket v2-collectif/15a, validé par le propriétaire le 17/11/2026). Dans sa zone de construction
# (`bloc.builds_up` : gardien ou défenseur dans ses 35 m), le porteur envisage en plus une passe longue EN L'AIR vers
# chaque coéquipier haut (`LONG_BALL_POSTES`) situé à plus de `possession.LONG_PASS_M` et à portée de frappe
# (`possession.max_pass_reach_m`), même hors de la portée de sa Vision : c'est un schéma d'équipe connu, pas une passe à
# repérer. Personne ne la coupe en vol (vol aérien des remises) ; sa réussite est la précision (Passing, difficulté de
# la passe en l'air), multipliée par `LONG_BALL_WON`, la part des retombées que le porteur pense voir gagnées par son
# coéquipier (estimation d'un joueur : le duel aérien n'existe pas encore, ticket v2-realisme/15b). Perdue, elle l'est
# là où elle retombe. Decisions et Composure jouent par la perception, comme pour toute option.
LONG_BALL_WON = 0.5
LONG_BALL_POSTES = frozenset({"BU", "ATT", "SA", "AG", "AD", "MOC"})

# Centre (ticket v2-attributs-restants/01, constantes validées par le propriétaire le 23/11/2026) : le porteur dans les
# `CROSS_ZONE_DEPTH_M` derniers mètres, hors de la largeur de la surface (plus de `PENALTY_AREA_WIDTH_M` / 2 de l'axe),
# envisage un centre vers chaque coéquipier de champ dans la surface adverse (hors-jeu évident exclu) : passe en l'air
# (vol du ticket v2-hauteur-ballon/02a1), que personne ne coupe en vol, dont Crossing règle la précision et le dosage à la
# place de Passing (`possession.pass_accuracy_probability`, `dosage_quality`), avec la difficulté au mètre des passes en
# l'air (`possession.LONG_BALL_DIFFICULTY_PER_M`) ; la retombée se joue au premier qui l'atteint (atteinte en hauteur,
# ticket v2-hauteur-ballon/03a) ; le porteur l'estime gagnée avec `LONG_BALL_WON`, comme une relance longue, jusqu'au duel
# aérien (`v2-realisme/15b`). Repères réels (cités de mémoire, à confirmer) : 20 à 25 % de centres réussis, 15 à 20
# centres par équipe et par match. Centres variés (tendu, en retrait) : ticket 11.
CROSS_ZONE_DEPTH_M = 35.0


def in_cross_zone(position: Vec2, goal: Vec2) -> bool:
    """Le porteur peut-il centrer : dans les `CROSS_ZONE_DEPTH_M` derniers mètres avant la ligne du but `goal`, hors
    de la largeur de la surface ?"""
    return abs(goal.x - position.x) <= CROSS_ZONE_DEPTH_M and abs(position.y - PITCH_WIDTH_M / 2.0) > PENALTY_AREA_WIDTH_M / 2.0

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

# Choix du geste de la tête (ticket v2-realisme/15c1, constantes validées par le propriétaire le 24/11/2026 ; aucune
# source trouvée, ordres de grandeur). Au contact de la tête, un joueur de champ juge ses options en une touche, sans
# tirage « pense-t-il à jouer de première » (en l'air, on ne peut pas attendre) : passe de la tête (de première, à
# `HEADER_PASS_RANGE_M` au plus), tir de la tête (à `HEADER_SHOT_RANGE_M` au plus du but), dégagement (dans sa moitié,
# ballon envoyé à `CLEARANCE_DISTANCE_M` droit devant, loin de son but ; provisoire, vers l'extérieur au ticket 15d ;
# valeur : son équipe le récupère à l'arrivée avec `CLEARANCE_KEEP_SHARE`), ou amorti (contrôle, comme avant) quand
# la meilleure option à ses yeux se joue au pied (conduite, passe après rotation, tir plus loin). Choix : Decisions et
# Vision, rôles existants. Exécution provisoire neutre : les notes du geste (`HEADER_NEUTRAL_ATTRIBUTES`) valent
# `HEADER_NEUTRAL_NOTE` dans l'évaluation et l'exécution des gestes de la tête, jusqu'aux tickets 15c2 à 15c4.
HEADER_PASS_RANGE_M = 20.0
HEADER_SHOT_RANGE_M = 16.0
CLEARANCE_DISTANCE_M = 30.0
CLEARANCE_KEEP_SHARE = 0.4
HEADER_NEUTRAL_ATTRIBUTES = ("Passing", "Technique", "Crossing", "Finishing", "Long Shots")
HEADER_NEUTRAL_NOTE = 50
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
    kind: str  # "shot" | "pass" | "dribble" | "clearance" (dégagement de la tête, ticket v2-realisme/15c1)
    value: float
    target: PlayerState | None = None  # coéquipier visé, pour une passe
    considered: int = 1  # options envisagées à cette décision (journal des décisions, ADR 0001)
    best: bool = True  # meilleure option prise (Decisions)
    follow: str | None = None  # suite prévue pour le receveur d'une passe, s'il en a une meilleure (ticket 14)
    plan: str | None = None  # sort du plan reçu : PLAN_HELD, _DROPPED, _UNSEEN ou _REFUSED (ticket 14)
    point: Vec2 | None = None  # cible de conduite, tenue jusqu'à la décision suivante (ticket 33)
    best_kind: str | None = None  # meilleur choix factuel de cette décision (ticket 33)
    gap: float = 0.0  # valeur réelle perdue par rapport au meilleur choix factuel, en part de celui-ci (ticket 33)
    rotation_s: float = 0.0  # rotation avant que la passe ou le tir parte (ticket v2-realisme/07e)
    backheel: bool = False  # passe en talonnade (ticket v2-realisme/07e)
    one_touch: bool = False  # passe jouée de première, sans contrôle (ticket v2-collectif/31a)
    # valeur telle que le porteur la perçoit (ticket v2-realisme/08d) : évaluée sur les positions perçues des adversaires
    # (mémoire de perception, 08b) ; `value` reste la valeur RÉELLE (journal du meilleur choix) ; `None` : perçue = réelle
    seen_value: float | None = None
    lofted: bool = False  # relance longue en l'air (ticket v2-collectif/15a)
    cross: bool = False  # centre, passe en l'air réglée par Crossing (ticket v2-attributs-restants/01)
    # meilleures valeurs réelles d'une passe courte (au sol) et d'une relance longue, quand une relance longue était
    # envisagée : le « pourquoi » du choix court ou long au journal des décisions (ticket v2-collectif/15a)
    short_long: tuple[float | None, float] | None = None


def turn_angle_deg(facing: Vec2, direction: Vec2) -> float:
    """Angle (0-180°) entre le cap et la direction du geste ; direction nulle : 0."""
    if direction.length() < 1e-9:
        return 0.0
    d = direction.normalized()
    return math.degrees(math.acos(max(-1.0, min(1.0, facing.x * d.x + facing.y * d.y))))


def rotation_delay_s(holder: PlayerState, direction: Vec2, free_cone_deg: float) -> float:
    """Rotation qui manque avant que le geste parte (ticket v2-realisme/07e) : l'angle au-delà du cône libre, à la
    vitesse de rotation du porteur (Agility, 07f). Même valeur à la décision et à l'exécution."""
    excess = turn_angle_deg(holder.facing, direction) - free_cone_deg
    return 0.0 if excess <= 0.0 else math.radians(excess) / turn_rate_rad_s(effective_rating(holder, "Agility"))


def rotation_keep_probability(holder: PlayerState, gene: float, delay_s: float) -> float:
    """Chance de garder le ballon pendant la rotation (ticket 07e) : la loi de perte de la conduite sur cette durée."""
    return 1.0 - dribble_loss_probability(holder, gene, delay_s) if delay_s > 0.0 else 1.0


def with_rotation(value: float, holder: PlayerState, mode: str | None, keep: float) -> float:
    """Valeur d'une option précédée d'une rotation (ticket 07e) : sa valeur s'il garde le ballon pendant la rotation,
    sinon le ballon perdu à sa place (pondéré par la transition, comme toute perte)."""
    if keep >= 1.0:
        return value
    _, loss_weight = _TRANSITION_WEIGHTS[mode]
    return keep * value - (1.0 - keep) * loss_weight * loss_cost(holder.position, holder.team)


def lane_closed_during_turn(holder: PlayerState, target: PlayerState, opponents: list[PlayerState], backheel: bool,
                            decided_chance: float) -> bool:
    """Après sa rotation (ticket v2-realisme/07e, réserve A1 de l'expert), le porteur renonce à la passe si sa ligne
    s'est fermée pendant la rotation : la chance de réussite est tombée sous `OPEN_LANE_PROBABILITY` en perdant au moins
    `LANE_CLOSED_DROP` depuis la décision. Une passe déjà risquée à la décision, choisie en connaissance de cause, part."""
    now = pass_success_probability(holder, target, opponents, backheel)
    return now < OPEN_LANE_PROBABILITY and decided_chance - now >= LANE_CLOSED_DROP


def backheel_idea_probability(holder: PlayerState) -> float:
    """Chance que le porteur pense à une talonnade à cette décision (Flair, ticket 07e)."""
    baseline, amplitude, low, high = _BACKHEEL_IDEA
    return success_probability(effective_rating(holder, "Flair"), baseline=baseline, amplitude=amplitude,
                               min_prob=low, max_prob=high)


def one_touch_idea_probability(receiver: PlayerState, opponents: list[PlayerState]) -> float:
    """Chance que le receveur d'une passe pense à jouer de première (ticket v2-collectif/31a) : First Touch et
    Technique (contexte « idée de jouer de première » du registre), plus souvent sous pression."""
    note = contextual_rating(receiver, IDEE_DE_PREMIERE)
    note = min(max(note, _ONE_TOUCH_IDEA_POINTS[0][0]), _ONE_TOUCH_IDEA_POINTS[-1][0])
    base = _ONE_TOUCH_IDEA_POINTS[-1][1]
    for (n0, v0), (n1, v1) in zip(_ONE_TOUCH_IDEA_POINTS, _ONE_TOUCH_IDEA_POINTS[1:]):
        if note <= n1:
            base = v0 + (note - n0) / (n1 - n0) * (v1 - v0)
            break
    return min(1.0, base * (1.0 + ONE_TOUCH_PRESSURE_GAIN * pressure(receiver, opponents)))


def thinks_one_touch(receiver: PlayerState, opponents: list[PlayerState]) -> bool:
    """Tirage (flux décision) : le receveur pense-t-il à jouer de première (ticket v2-collectif/31a) ?"""
    return DECISION.random() < one_touch_idea_probability(receiver, opponents)


def reads_third_man_probability(holder: PlayerState) -> float:
    """Chance que le porteur, en construction sous pressing, lise un troisième homme à cette décision (ticket 15b1) :
    contexte « lecture du pressing » (Vision, Anticipation, Decisions), interpolé entre les repères, borné."""
    note = contextual_rating(holder, LECTURE_DU_PRESSING)
    points = _READS_THIRD_MAN
    note = min(max(note, points[0][0]), points[-1][0])
    (n0, v0), (n1, v1) = next(pair for pair in zip(points, points[1:]) if note <= pair[1][0])
    return v0 + (note - n0) / (n1 - n0) * (v1 - v0)


def _from_own_goal(team: str, x: float) -> float:
    """Distance à son propre but dans l'axe du terrain (domicile défend x = 0)."""
    return x if team == "home" else PITCH_LENGTH_M - x


def first_pressing_line(team: str, opponents: list[PlayerState]) -> float | None:
    """Hauteur de la première ligne de pressing adverse, en distance au but de `team` : le `FIRST_LINE_RANK`-ième
    adversaire de champ le plus proche de ce but (ticket 15b1). None s'il y a moins d'adversaires de champ."""
    heights = sorted(_from_own_goal(team, p.position.x) for p in opponents if p.poste != "GK")
    return heights[FIRST_LINE_RANK - 1] if len(heights) >= FIRST_LINE_RANK else None


def adopt_plan_probability(player: PlayerState) -> float:
    baseline, amplitude, low, high = _ADOPT_PLAN
    return success_probability(effective_rating(player, "Teamwork"), baseline=baseline, amplitude=amplitude,
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
    vision = effective_rating(holder, "Vision")
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
                     mode: str | None = None, planned: str | None = None,
                     seen_opponents: list[PlayerState] | None = None, one_touch: bool = False,
                     build_up: bool = False, pressed: bool = False) -> list[Action]:
    """Les options du porteur avec leur valeur FACTUELLE (ticket v2-collectif/33 : danger attendu, vraies capacités),
    de la meilleure à la moins bonne : un tir à portée (`SHOOTING_RANGE_M`), une passe par coéquipier envisagé (Vision),
    une conduite par direction (`DRIBBLE_DIRECTIONS_DEG`). `mode` : choix de
    transition de son équipe, contre-attaque ou conservation (ticket v2-collectif/11), sinon `None`. `planned` :
    coéquipier que son passeur a prévu pour la suite (plan de passe, ticket v2-collectif/14). `seen_opponents` : les
    adversaires tels que le porteur les perçoit (ticket v2-realisme/08d, mémoire de perception) ; les tirs et les passes
    reçoivent alors aussi leur valeur perçue (`Action.seen_value`), sans tirage de plus (un seul passage pour les deux
    étages). Les conduites perçues se calculent dans `choose_action`. Seuls les adversaires changent : la gêne du
    porteur (au contact, il la sent), les coéquipiers et le gardien restent réels. `one_touch` : le receveur juge ses
    passes sans rotation comme jouées de première (précision du geste, ticket v2-collectif/31a). `build_up` : porteur
    dans sa zone de construction, relances longues en l'air envisagées en plus (ticket v2-collectif/15a). `pressed` :
    construction sous pressing, le porteur peut y lire un troisième homme (ticket v2-collectif/15b1)."""
    opponents = [p for p in players if p.team != holder.team]
    mates = [p for p in players if p.team == holder.team and p.name != holder.name]
    # Hors-jeu (ticket v2-collectif/23, deuxième passe du 28/10/2026) : le porteur ne sert pas un coéquipier qu'il
    # voit nettement au-delà de la ligne -- mais ce qu'il voit dépend de sa Vision. Trois leviers, tous sur la Vision
    # (docs/CARTE_ATTRIBUTS_V2.md, audit A12) : la portée (`visible_teammates`), le seuil de tolérance
    # (`pass_margin_m`, angle mort de 0,85 m à Vision 0 à 0,3 m à Vision 100) et l'erreur de lecture de la ligne (`perceived_defence_line`, 0,05 à 0,25 m).
    # Les deux derniers se composent en un seul seuil effectif, d'où les passes que l'arbitre siffle.
    vision = effective_rating(holder, "Vision")
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
        # qualité de l'occasion (ticket 28a) : chance de but, contres compris (même loi qu'à la résolution) ; depuis le
        # ticket v2-realisme/18k, un tir non marqué rend le ballon à l'adversaire (`shot_value`)
        goal_chance, blocked = shot_outcome_shares(holder, goal, keeper, opponents)
        turn = rotation_delay_s(holder, goal - holder.position, SHOT_FREE_CONE_DEG)  # ticket 07e
        keep_turn = rotation_keep_probability(holder, gene, turn)
        value = with_rotation(shot_value(holder, mode, goal_chance, blocked, goal), holder, mode, keep_turn)
        seen_value = None
        if seen_opponents is not None:  # même tir, adversaires perçus (08d)
            seen_chance, seen_blocked = shot_outcome_shares(holder, goal, keeper, seen_opponents)
            seen_value = with_rotation(shot_value(holder, mode, seen_chance, seen_blocked, goal), holder, mode, keep_turn)
        options.append(Action("shot", value, rotation_s=turn, seen_value=seen_value))
    # suite du receveur (ticket 13) : meilleure passe suivante vers un coéquipier que le porteur voit lui-même ; le
    # passeur n'en fait pas partie (pas d'aller-retour) ; pas de suite en contre-attaque (on joue vite vers l'avant)
    share = 0.0 if mode == CONTRE_ATTAQUE else _FOLLOW_UP_SHARE
    # troisième homme (ticket 15b1) : lu ou non à cette décision, un tirage, seulement s'il y a une suite à valoriser
    third_man = pressed and share > 0.0 and DECISION.random() < reads_third_man_probability(holder)
    # talonnade (ticket 07e) : il y pense ou non à cette décision (Flair), un tirage s'il a un coéquipier à portée
    backheel_ok = None
    for mate in teammates:
        turn = rotation_delay_s(holder, mate.position - holder.position, PASS_FREE_CONE_DEG)  # ticket 07e
        backheel = turn > 0.0 and holder.position.distance_to(mate.position) <= BACKHEEL_MAX_M
        if backheel and backheel_ok is None:
            backheel_ok = DECISION.random() < backheel_idea_probability(holder)
        # passe après rotation, et sa talonnade si le porteur y pense
        for heel in (False, True) if backheel and backheel_ok else (False,):
            first = one_touch and (heel or turn == 0.0)  # de première : seulement sans rotation (ticket 31a)
            option = _pass_option(holder, mate, opponents, seen_full, team, mode, share, held, margin,
                                  seen_line, gene, 0.0 if heel else turn, heel, first, third_man=third_man)
            if seen_opponents is not None:  # même passe, adversaires perçus (08d)
                option = replace(option, seen_value=_pass_option(holder, mate, seen_opponents, seen_full, team, mode,
                                                                 share, held, margin, seen_line, gene,
                                                                 0.0 if heel else turn, heel, first,
                                                                 third_man=third_man).value)
            options.append(option)
    if build_up and not one_touch:  # relance longue en l'air (ticket v2-collectif/15a)
        reach = keeper_kick_reach_m(holder) if holder.poste == "GK" else max_pass_reach_m()  # Kicking (ticket 03c1)
        for mate in mates:
            length = holder.position.distance_to(mate.position)
            if mate.poste not in LONG_BALL_POSTES or not LONG_PASS_M < length <= reach \
                    or is_clearly_offside(team, mate.position, holder.position, opponents, margin, seen_line):
                continue
            turn = rotation_delay_s(holder, mate.position - holder.position, PASS_FREE_CONE_DEG)
            option = _pass_option(holder, mate, opponents, seen_full, team, mode, share, held, margin, seen_line, gene,
                                  turn, False, lofted=True)
            if seen_opponents is not None:
                option = replace(option, seen_value=_pass_option(holder, mate, seen_opponents, seen_full, team, mode,
                                                                 share, held, margin, seen_line, gene, turn, False,
                                                                 lofted=True).value)
            options.append(option)
    if not one_touch and in_cross_zone(holder.position, goal):  # centre (ticket v2-attributs-restants/01)
        for mate in mates:
            if mate.poste == "GK" or not in_penalty_area(team, mate.position) \
                    or is_clearly_offside(team, mate.position, holder.position, opponents, margin, seen_line):
                continue
            turn = rotation_delay_s(holder, mate.position - holder.position, PASS_FREE_CONE_DEG)
            option = _pass_option(holder, mate, opponents, seen_full, team, mode, share, held, margin, seen_line, gene,
                                  turn, False, lofted=True, cross=True)
            if seen_opponents is not None:
                option = replace(option, seen_value=_pass_option(holder, mate, seen_opponents, seen_full, team, mode,
                                                                 share, held, margin, seen_line, gene, turn, False,
                                                                 lofted=True, cross=True).value)
            options.append(option)
    if planned is not None and mode != CONTRE_ATTAQUE:  # sort du plan, pour la mesure (ticket 14)
        # abandonné : la cible est vue mais la ligne s'est fermée ; non vu : hors de sa Vision ou hors-jeu évident
        target = next((m for m in teammates if m.name == held), None)
        state = PLAN_REFUSED if held is None else PLAN_UNSEEN if target is None \
            else PLAN_HELD if pass_success_probability(holder, target, opponents) >= OPEN_LANE_PROBABILITY \
            else PLAN_DROPPED
        options = [replace(o, plan=state) for o in options]
    return sorted(options, key=lambda a: a.value, reverse=True)


def _pass_option(holder: PlayerState, mate: PlayerState, opponents: list[PlayerState],
                 seen_full: list[PlayerState], team: str, mode: str | None, share: float, held: str | None,
                 margin: float, seen_line: float, gene: float, turn: float, backheel: bool,
                 one_touch: bool = False, lofted: bool = False, third_man: bool = False, cross: bool = False) -> Action:
    """Valeur d'une passe vers `mate` (tickets 13, 14, 33), après `turn` secondes de rotation (07e), en talonnade
    ou non, jouée de première ou non (31a), au sol ou en relance longue en l'air (15a). `third_man` : le porteur lit
    le pressing (ticket 15b1) ; la suite vers un coéquipier derrière la première ligne, quand `mate` est devant elle
    ou sur elle, est majorée de `THIRD_MAN_BONUS`."""
    # le ballon arrive (v2-socle/04) ; en l'air, rien ne la coupe en vol et la retombée se dispute (ticket 15a)
    success = pass_success_probability(holder, mate, opponents, lofted=True, cross=cross) * LONG_BALL_WON if lofted \
        else pass_success_probability(holder, mate, opponents, backheel, one_touch)
    # temps disponible : il garde le ballon assez longtemps pour jouer (A9 reclassé au ticket 13)
    keep = success * (1.0 - PRESSURE_KEEP_SHARE * pressure(mate, opponents))
    now = danger(mate.position, team)
    future, follow = now, None
    if share:
        line = first_pressing_line(team, opponents) if third_man else None
        if line is not None and _from_own_goal(team, mate.position.x) > line:
            line = None  # le receveur est déjà derrière la ligne : pas de troisième homme

        def broken(n: PlayerState) -> float:  # suite qui casse la première ligne (ticket 15b1)
            return 1.0 + THIRD_MAN_BONUS if line is not None and _from_own_goal(team, n.position.x) > line else 1.0
        best_next, nxt = max(((pass_success_probability(mate, n, opponents) * danger(n.position, team) * broken(n),
                               n.name)
                              for n in seen_full if n is not mate
                              and not is_clearly_offside(team, n.position, mate.position, opponents, margin,
                                                         seen_line)),
                             key=lambda vn: vn[0], default=(0.0, None))
        if best_next > now:  # la suite vaut au moins la position atteinte (il garde le ballon)
            future, follow = best_next, nxt
    reached = (1.0 - share) * now + share * future
    if mate.name == held and success >= OPEN_LANE_PROBABILITY:  # plan tenu, encore jouable (ticket 14)
        reached *= 1.0 + PLAN_BONUS
    # perdue : à mi-chemin au sol, là où elle retombe en l'air
    lost_at = mate.position if lofted else Vec2((holder.position.x + mate.position.x) / 2.0,
                                                (holder.position.y + mate.position.y) / 2.0)
    value = with_rotation(option_value(holder, mode, keep, reached, lost_at), holder, mode,
                          rotation_keep_probability(holder, gene, turn))
    return Action("pass", value, mate, follow=follow, rotation_s=turn, backheel=backheel, one_touch=one_touch,
                  lofted=lofted, cross=cross)


def option_value(holder: PlayerState, mode: str | None, keep: float, reached: float, lost_at: Vec2) -> float:
    """Monnaie commune (ticket 33) : s'il garde le ballon, le danger d'ici plus le gain (pondéré par la transition) ;
    s'il le perd, le danger qu'aurait l'adversaire là où il le perd (pondéré aussi)."""
    here = danger(holder.position, holder.team)
    gain_weight, loss_weight = _TRANSITION_WEIGHTS[mode]
    return keep * (here + gain_weight * (reached - here)) - (1.0 - keep) * loss_weight * loss_cost(lost_at, holder.team)


def shot_value(holder: PlayerState, mode: str | None, goal_chance: float, blocked: float, goal: Vec2) -> float:
    """Valeur du tir dans la monnaie commune (ticket v2-realisme/18k) : la chance de but, moins ce que coûte un tir non
    marqué, comme la perte d'une passe ou d'une conduite (`loss_cost`, pondérée par la transition) : contré, le ballon est
    perdu près du tireur ; à côté, au-dessus, dévissé ou arrêté, il revient à l'adversaire à son but (sortie de but,
    gardien). Aucune constante nouvelle. Approximation : le tir claqué en corner (environ 3 % des tirs) compte comme une
    perte."""
    _, loss_weight = _TRANSITION_WEIGHTS[mode]
    missed = max(0.0, 1.0 - goal_chance - blocked)
    cost = blocked * loss_cost(holder.position, holder.team) + missed * loss_cost(goal, holder.team)
    return goal_chance - loss_weight * cost


def keep_ball_probability(holder: PlayerState, gene: float) -> float:
    """Chance de garder le ballon en conduisant pendant `DRIBBLE_REFERENCE_S` (tickets 33 et v2-realisme/04a) : Dribbling
    compte d'autant plus qu'un adversaire est proche, un dixième de ce risque sans adversaire à 5 m. Seule fonction de
    ce risque : l'évaluation de l'option et le tirage de la perte (`dribble_lost`) l'appellent."""
    baseline, amplitude = _KEEP_BALL
    skill = success_probability(effective_rating(holder, "Dribbling"), baseline=baseline, amplitude=amplitude)
    contested = FREE_TOUCH_SHARE + (1.0 - FREE_TOUCH_SHARE) * gene  # 0,1 sans adversaire à 5 m, 1 au contact
    return 1.0 - (1.0 - skill) * contested


def dribble_speed_factor(holder: PlayerState, gene: float) -> float:
    """Part de sa vitesse max à laquelle le porteur conduit sous la gêne `gene` (0 sans adversaire à 5 m, 1 au contact) :
    Dribbling sans adversaire, moins `CONTACT_SLOWDOWN` x `gene` (ticket v2-realisme/04d)."""
    baseline, amplitude = _CARRY_SPEED
    free = success_probability(effective_rating(holder, "Dribbling"), baseline=baseline, amplitude=amplitude)
    return free * (1.0 - CONTACT_SLOWDOWN * gene)


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
    return REACTION_S + start.distance_to(point) / max_speed_mps(effective_rating(opponent, "Pace"))


def free_point(holder: PlayerState, opponents: list[PlayerState], heading: Vec2, projection: float,
               speed_factor: float | None = None) -> Vec2 | None:
    """Dernier point libre dans la direction `heading` (tous les `DRIBBLE_STEP_M` jusqu'à `DRIBBLE_REACH_M`) : le
    porteur, balle au pied, y arrive `DRIBBLE_MARGIN_S` avant tout adversaire, dont il prolonge le déplacement pour
    la part `projection` (1 : le vrai ; moins : ce que son Anticipation lui fait voir, `arrival_s`). `speed_factor` :
    part de sa vitesse max balle au pied (`dribble_speed_factor`, ticket 04d) ; sans lui, celle sans adversaire. `None` :
    rien de libre."""
    if speed_factor is None:
        speed_factor = dribble_speed_factor(holder, 0.0)
    speed = max_speed_mps(effective_rating(holder, "Pace")) * speed_factor
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
    speed_factor = dribble_speed_factor(holder, gene)
    options = []
    for angle in DRIBBLE_DIRECTIONS_DEG:
        rad = math.radians(angle)
        heading = Vec2(forward * math.cos(rad), math.sin(rad))
        reached = free_point(holder, opponents, heading, projection, speed_factor)
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
    note = min(max(effective_rating(holder, "Decisions"), _ERROR_POINTS[0][0]), _ERROR_POINTS[-1][0])
    (n0, e0), (n1, e1) = next(pair for pair in zip(_ERROR_POINTS, _ERROR_POINTS[1:]) if note <= pair[1][0])
    error = e0 + (note - n0) / (n1 - n0) * (e1 - e0)
    return error * (1.0 + gene * _curve(effective_rating(holder, "Composure"), _COMPOSURE_K))


def anticipation_share(holder: PlayerState) -> float:
    """Part du déplacement des adversaires que le porteur prolonge pendant sa conduite (ticket 33)."""
    return min(1.0, _curve(effective_rating(holder, "Anticipation"), _ANTICIPATION_SHARE))


def choose_action(holder: PlayerState, players: list[PlayerState], goal: Vec2, keeper: PlayerState | None,
                  mode: str | None = None, planned: str | None = None,
                  felt: dict[int, float] | None = None, set_piece: bool = False,
                  seen_opponents: list[PlayerState] | None = None, one_touch: bool = False,
                  build_up: bool = False, pressed: bool = False, header: bool = False,
                  ball_velocity: Vec2 | None = None) -> Action:
    """Prend l'option qu'il CROIT la meilleure (ticket 33) : valeur réelle brouillée par sa perception (Decisions,
    Composure sous pression), conduites jugées avec son Anticipation. Deux options proches font hésiter même un très
    bon joueur ; un joueur faible se trompe surtout entre options voisines. `planned` : ticket v2-collectif/14.
    `felt` : son erreur sur chaque direction de conduite (en écarts-types), gardée pendant sa possession ; complétée
    ici si besoin. `set_piece` : coup franc (ticket v2-collectif/30), il frappe ou passe, la conduite n'est pas une
    option. `seen_opponents` : les adversaires tels qu'il les perçoit (ticket v2-realisme/08d, mémoire de perception, 08b) :
    les tirs, les passes et les conduites sont jugés sur leurs positions perçues, la valeur RÉELLE (`best`, `gap`)
    reste calculée sur les vraies positions, et l'exécution aussi. `None` : il perçoit les vraies positions.
    `one_touch` : receveur qui pense à jouer de première (ticket v2-collectif/31a). `build_up` : zone de construction,
    relances longues envisagées (ticket v2-collectif/15a). `pressed` : sous pressing, troisième homme (15b1).
    `header` : contact de la tête (ticket v2-realisme/15c1), options restreintes et dégagement (`header_options`) ;
    `holder` est alors son double aux notes du geste neutres (`header_twin`) et `one_touch` vrai ; `ball_velocity` :
    vitesse du ballon qui arrive, pour la chance de l'amortir."""
    options = evaluate_options(holder, players, goal, keeper, mode, planned, seen_opponents, one_touch, build_up,
                               pressed)
    incoming = ball_velocity if ball_velocity is not None else Vec2(0.0, 0.0)
    if header:
        options = header_options(holder, options, goal, mode, players, incoming)
    if set_piece:
        options = [o for o in options if o.kind != "dribble"] or options
    # frappe de loin (ticket v2-realisme/18m) : la marge fait partie de la règle de choix, perçue comme réelle ; le
    # meilleur choix factuel (`best`, `gap`, courbe de Decisions) se juge avec la même règle
    margin = 0.0 if set_piece or in_penalty_area(holder.team, holder.position) else LONG_SHOT_MARGIN

    def choice_value(option: Action) -> float:
        return option.value - margin if option.kind == "shot" else option.value
    best = max(options, key=choice_value)
    longs = [o.value for o in options if o.lofted]
    shorts = [o.value for o in options if o.kind == "pass" and not o.lofted]
    tagged = dict(considered=len(options), best_kind=best.kind,
                  short_long=(max(shorts) if shorts else None, max(longs)) if longs else None)
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
    seen_world = opponents if seen_opponents is None else seen_opponents
    seen_as = {} if share >= 1.0 and seen_opponents is None else {
        real.point: seen for real, seen in zip(real_dribbles, dribble_options(holder, seen_world, gene, mode, share))}
    if header and seen_as:  # amorti : conduites perçues pondérées comme les réelles (réserve A1 de l'expert, 15c1)
        cushioned = header_cushion(holder, players, mode, incoming)
        seen_as = {point: replace(seen, value=cushioned(seen.value)) for point, seen in seen_as.items()}
    felt = {} if felt is None else felt
    sigma = perception_error(holder, gene) * max(abs(choice_value(best)), 1e-3)
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
        seen_value = seen.value if seen.seen_value is None else seen.seen_value  # tir et passe : valeur perçue (08d)
        if option.kind == "shot":
            seen_value -= margin  # frappe de loin : nettement meilleure ou rien (ticket v2-realisme/18m)
        perceived.append((seen_value + PERCEPTION.gauss(0.0, sigma), option, seen.point))
    _, chosen, point = max(perceived, key=lambda t: t[0])
    # valeur perdue, en part de la meilleure ; une option presque équivalente compte comme le meilleur choix
    gap = (choice_value(best) - choice_value(chosen)) / max(abs(choice_value(best)), 1e-9)
    return replace(chosen, point=point, best=gap < BEST_CHOICE_TOLERANCE, gap=gap, **tagged)


def header_twin(player: PlayerState) -> PlayerState:
    """Double de `player` pour un geste de la tête (ticket v2-realisme/15c1) : notes du geste neutres
    (`HEADER_NEUTRAL_ATTRIBUTES` à `HEADER_NEUTRAL_NOTE`), le reste identique (joueur sans fiche : notes par défaut) ;
    provisoire, jusqu'aux tickets 15c2-15c4."""
    return replace(player, attributes={**(player.attributes or {}),
                                       **{a: HEADER_NEUTRAL_NOTE for a in HEADER_NEUTRAL_ATTRIBUTES}})


def clearance_point(holder: PlayerState) -> Vec2:
    """Point visé d'un dégagement de la tête : `CLEARANCE_DISTANCE_M` droit devant, vers le but adverse, dans le
    terrain (provisoire, ticket 15d : vers l'extérieur)."""
    forward = 1.0 if holder.team == "home" else -1.0
    x = min(max(holder.position.x + forward * CLEARANCE_DISTANCE_M, 0.0), PITCH_LENGTH_M)
    return Vec2(x, holder.position.y)


def in_own_half(player: PlayerState) -> bool:
    """`player` est dans sa moitié de terrain (`home` défend x = 0)."""
    return player.position.x < PITCH_LENGTH_M / 2.0 if player.team == "home" else player.position.x > PITCH_LENGTH_M / 2.0


def header_options(holder: PlayerState, options: list[Action], goal: Vec2, mode: str | None,
                   players: list[PlayerState], ball_velocity: Vec2) -> list[Action]:
    """Options au contact de la tête (ticket v2-realisme/15c1) : le tir à `HEADER_SHOT_RANGE_M` au plus, les passes
    de première à `HEADER_PASS_RANGE_M` au plus deviennent des gestes de la tête ; conduites et passes après rotation
    restent, elles valent l'amorti (contrôle puis jeu au pied) ; un tir plus loin, une passe de première plus longue
    sont écartés (ni de la tête ni de première). Dans sa moitié, un dégagement en plus, valeur dans la monnaie
    commune : son équipe le récupère à l'arrivée avec `CLEARANCE_KEEP_SHARE`, sinon l'adversaire l'a là. Amorti : les
    options au pied supposent le ballon contrôlé ; leur valeur est pondérée par la chance de réussir le contrôle
    (`possession.control_probability`, même loi que la réception), le contrôle raté perdant le ballon sur place."""
    cushioned = header_cushion(holder, players, mode, ball_velocity)
    kept = []
    for o in options:
        if o.kind == "shot" and holder.position.distance_to(goal) > HEADER_SHOT_RANGE_M:
            continue
        if o.kind == "pass" and o.one_touch and holder.position.distance_to(o.target.position) > HEADER_PASS_RANGE_M:
            continue
        if o.backheel:  # pas de talonnade de la tête (réserve A3 de l'expert) ; déviation vers l'arrière : 15c2
            continue
        if not header_gesture(o):  # amorti, puis jeu au pied
            o = replace(o, value=cushioned(o.value),
                        seen_value=None if o.seen_value is None else cushioned(o.seen_value))
        kept.append(o)
    if in_own_half(holder):
        point = clearance_point(holder)
        value = option_value(holder, mode, CLEARANCE_KEEP_SHARE, danger(point, holder.team), point)
        kept.append(Action("clearance", value, point=point))
    return sorted(kept, key=lambda a: a.value, reverse=True)


def header_cushion(holder: PlayerState, players: list[PlayerState], mode: str | None, ball_velocity: Vec2):
    """Pondération de l'amorti (ticket v2-realisme/15c1) : une option au pied, de valeur `v` ballon contrôlé, vaut
    `c x v - (1 - c) x perte sur place`, `c` la chance de réussir le contrôle (`possession.control_probability`).
    Appliquée aux valeurs réelles et perçues (`header_options`) et aux conduites perçues (`choose_action`, A1)."""
    opponents = [p for p in players if p.team != holder.team]
    control = control_probability(holder, ball_velocity, opponents)
    _, loss_weight = _TRANSITION_WEIGHTS[mode]
    missed = loss_weight * loss_cost(holder.position, holder.team)

    def cushioned(value: float) -> float:
        return control * value - (1.0 - control) * missed
    return cushioned


def header_gesture(action: Action) -> bool:
    """L'action choisie au contact de la tête se joue de la tête (tir, passe de première, dégagement) ; sinon amorti."""
    return action.kind in ("shot", "clearance") or (action.kind == "pass" and action.one_touch)


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
    return best if DECISION.random() < best_choice_probability(effective_rating(holder, "Decisions")) else other

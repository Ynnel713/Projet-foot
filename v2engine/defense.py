"""Rôles défensifs (ticket v2-collectif/07) : quand l'adversaire a le ballon, l'équipe attribue des rôles une fois par
tick, au lieu de laisser tout joueur à moins de `cerveau.CHASE_RADIUS_M` foncer sur le porteur (essaim mesuré le
30/10/2026 : 2,95 défenseurs en moyenne à moins de 3 m du porteur, 86 tacles par match) :
- un **presseur** : celui qui arrive le premier sur le porteur (Pace et Acceleration, capacité seule, règle R5) ;
- une **couverture**, porteur dans sa moitié : le joueur qui arrive le premier sur le point situé à `COVER_DEPTH_M`
  derrière le porteur, sur la ligne porteur-but -- elle ferme aussi l'axe (pas de rôle séparé). Positioning règle la
  précision de ce placement (même erreur que dans le bloc, `Bloc.placement_error`) ;
- un **marqueur** par attaquant dangereux (hors porteur, à `DANGER_M` ou moins du but défendu) : le défenseur libre
  le plus proche, côté but, à une distance réglée par Marking.
Dans les 25 m, le marqueur défend côté but, sous la ligne du bloc s'il le faut, comme les défenseurs réels autour de
la surface : le piège du hors-jeu se joue plus haut (décision du propriétaire du 30/10/2026, après mesure de trois
versions ; « tenir la ligne » ne remontait le hors-jeu que de 0,3 à 0,5 par match et annulait l'effet de Marking).
Les autres tiennent le bloc (ticket 04), sauf l'indiscipliné qui le quitte pour aller au ballon (Teamwork, critère
reporté du ticket 04). Work Rate (envie de presser) est laissé au ticket 08 ; Anticipation agit déjà par le délai de
réaction à la situation de jeu.

Constantes validées par le propriétaire le 30/10/2026 (ordres de grandeur, ajustables ; valeurs réelles non trouvées) :
- couverture à 6 m derrière le porteur (guides d'entraînement : « 5 à 7 pas, en retrait et décalé ») ;
- attaquant dangereux à 25 m ou moins du but ;
- distance de marquage : Marking 99 -> 1 m, 55 -> 2,5 m, 11 -> 4 m ;
- quitter le bloc pour aller au ballon : Teamwork 99 -> 0 %, 55 -> 15 %, 11 -> 35 %, tiré toutes les 5 s ;
- presseur et couverture restent à leur titulaire, pour le même porteur, tant qu'un autre ne peut pas arriver au moins
  0,3 s avant lui (`HOLD_MARGIN_S`, réserve A1 de l'expert : sans mémoire, le presseur changeait de main puis revenait
  en moins de 1 s dans 14 % des changements ; avec, 0 %). Le marqueur n'a pas de mémoire : avec elle, le marqueur
  attitré décrochait de son attaquant et l'effet de Marking disparaissait (5,50 contre 5,32 m), sans elle le
  ping-pong du marqueur est déjà à 3,7 % (mesures du 30/10/2026, 4 matchs).

Pressing coordonné (ticket v2-collectif/08, constantes validées par le propriétaire le 31/10/2026 ; durées de repos,
décalage et parts non trouvés, ordres de grandeur ajustables) :
- intensité de course du presseur, Work Rate : 99 -> 100 %, 55 -> 80 %, 11 -> 55 % de sa vitesse max (socle 02) ;
- effort par à-coups : au plus `PRESS_BURST_S` = 5 s (fenêtre de 5 s des analyses StatsBomb), puis il souffle, Work
  Rate 99 -> 5 s, 55 -> 10 s, 11 -> 20 s ; le suivant qui arrive le premier prend le relais ;
- course orientée : il vise, à sa distance d'arrêt, le côté de la ligne de passe vers le receveur le plus dangereux
  (le plus proche du but défendu), décalé d'au plus `SHADOW_M` = 1,5 m de son approche directe ; Anticipation règle
  la part des bonnes lectures (99 -> 85 %, 55 -> 65 %, 11 -> 40 %, sinon un autre receveur), un tirage par porteur ;
  porteur à `SHOT_LANE_RANGE_M` = 25 m ou moins du but défendu : la bonne lecture, même courbe, est la ligne de tir
  (ticket v2-realisme/10k), sinon il garde sa lecture de passe ;
- distance d'arrêt face au porteur, Aggression (engagement au contact) : 99 -> 0,8 m, 55 -> 1,2 m, 11 -> 1,6 m, au-delà
  du rayon de tacle (1,5 m) : il laisse le porteur se retourner ;
- déclencheurs collectifs (passe en retrait d'au moins `BACKWARD_PASS_M` = 3 m, réserve A2 de l'expert ; porteur qui
  reçoit en reculant vers son but ; contrôle raté) : pressing d'équipe pendant `TRIGGER_S` = 5 s ; chaque partenaire
  suit, Teamwork 99 -> 95 %, 55 -> 80 %, 11 -> 55 %, un tirage par déclenchement, et marque côté ballon, le plus libre
  d'abord, chaque receveur à moins de `FOLLOW_M` = 15 m du ballon.

Passe adverse en vol (réserve A2 du ticket 07, reprise au ticket v2-collectif/09) : les rôles sont attribués comme si
le receveur avait déjà le ballon, à son point de réception ; sans cela, le marqueur lâchait son attaquant au départ de
la passe (rôle attribué 57,5 % du temps de possession adverse, mesure du 01/11/2026). Les déclencheurs du pressing
suivent toujours le vrai porteur ; les lecteurs de passe gardent leur priorité. L'effort du presseur (`burst`) compte
donc depuis le départ de la passe vers son porteur, vol compris.

Compensations (ticket v2-collectif/09, constantes validées par le propriétaire le 01/11/2026 ; valeurs réelles non
trouvées, ordres de grandeur) : un défenseur (DC, LB, RB) à plus de `HOLE_AWAY_M` = 10 m de sa place dans le bloc sans
ballon laisse un trou si personne n'est à moins de `HOLE_FILLED_M` = 5 m de cette place, qu'elle est dans sa moitié
entre le ballon et son but, et qu'un attaquant adverse non marqué (porteur compris) en est à `HOLE_DANGER_M` = 20 m ou
moins. Le comble
le premier, dans l'ordre milieu défensif, central voisin, latéral opposé, qui arrive avant cet attaquant (temps
d'arrivée, plus son délai de réaction d'Anticipation) et qui accepte de quitter sa place (Teamwork, courbe du
ticket 08, un tirage par trou, gardé jusqu'au retour de l'absent) ; Positioning règle la précision de son placement, comme pour la couverture. Le
titulaire en route garde la place tant qu'il arrive au plus `HOLD_MARGIN_S` après l'attaquant ; arrivé, il la tient
jusqu'à ce que le joueur absent revienne à moins de 5 m. Deux niveaux de cascade au plus. Decisions et Concentration n'y sont pas (règles R1 et
R3) ; le repli du joueur qui a quitté sa place relève du ticket 10.

Contre-pressing (ticket v2-collectif/10, constantes validées par le propriétaire le 02/11/2026) : une perte dans le jeu
(ni ballon pris par le gardien, ni coup franc de hors-jeu, ni engagement) déclenche le pressing d'équipe ci-dessus
pour l'équipe qui a perdu, pendant `TRIGGER_S` = 5 s. Ne suivent que les joueurs à `FOLLOW_M` = 15 m ou moins du
ballon (Teamwork, même tirage), sauf les `REST_DEFENDERS` = 2 joueurs de champ les plus reculés, qui protègent
l'axe. Les autres se replient (`cerveau`, intensité du contexte « repli après la perte », `retreat_intensity`).

Presseur selon la zone (ticket v2-realisme/10a, constantes validées par le propriétaire le 18/11/2026 ; chiffres réels
non trouvés, ordres de grandeur calés sur le bloc sans ballon de 32 x 40 m) : la zone de responsabilité d'un joueur est
un rectangle centré sur sa place de référence sans ballon (`Bloc.reference`, ballon au porteur), de `ZONE_DEPTH_M` = 8 m
en profondeur et `ZONE_WIDTH_M` = 10 m en largeur de chaque côté (environ 11 m entre les lignes et 13 m entre deux
défenseurs d'une ligne à quatre : les zones voisines se recouvrent). Bords ouverts : la zone de la dernière ligne
s'étend jusqu'à son but, celle de la ligne la plus avancée vers l'avant, celle du joueur le plus excentré jusqu'à sa
touche (personne n'a de zone au-delà). Le presseur est choisi parmi ceux dont la zone contient le porteur et qui
arrivent au plus `PRESS_ZONE_MARGIN_S` = 1 s après le plus rapide de tous, le premier arrivé d'entre eux ; s'il n'y en
a aucun, le plus rapide de tous, comme avant. La mémoire du titulaire (`HOLD_MARGIN_S`) s'applique contre ce choix,
même si le porteur a quitté la zone du titulaire : sans elle, le porteur qui longe le bord d'une zone faisait changer
le presseur puis revenir dans la seconde (21,6 % des relais contre 1,9 % avant, 30 minutes mesurées le 18/11/2026).
L'effort et le relais du ticket 08 s'appliquent aux mêmes candidats. Sans bloc (scènes de test) : le premier arrivé, comme avant.

Le central ne quitte sa ligne que couvert (ticket v2-realisme/10b, règle validée par le propriétaire le 18/11/2026,
sans constante nouvelle ; chiffres réels non trouvés) : un défenseur central (DC) sort de sa ligne quand le point visé
par son rôle (presser, marquer, suivre un receveur du pressing d'équipe) est à plus de `HOLE_AWAY_M` = 10 m de sa place
de référence sans ballon, sans être plus près de son but qu'elle. Il ne sort que couvert : un partenaire est déjà à
`HOLE_FILLED_M` = 5 m ou moins de sa place ; ou un compensateur (même ordre que les compensations : milieu défensif,
autre central, latéral) libre y arrive, délai de réaction compris, avant l'attaquant le plus proche de cette place et
l'accepte (Teamwork : un tirage par partenaire visé tant que le porteur ne change pas, comme la ligne de passe lue
par le presseur ; l'accord qui autorise la sortie devient le tirage du trou, repris par la compensation qui suivra
quel que soit le porteur, tant que la sortie dure ; un trou encore ouvert impose son tirage) ; ou aucun attaquant
(hors celui qu'il presse ou marque) n'est à `HOLE_DANGER_M` = 20 m ou moins de sa place. Sinon il garde sa ligne et
cède le rôle : le presseur est choisi parmi les autres (règle du 10a), le marquage revient au défenseur libre le plus
proche après lui ; seul joueur libre, il presse quand même, mais ne marque pas. La vérification se fait quand le rôle
devient une sortie : sorti couvert, il garde son rôle pour le même partenaire.

Même règle pour la couverture (ticket v2-realisme/10b2, décision du propriétaire du 18/11/2026) : un central dont le
point de couverture est une sortie ne la prend que couvert ; sinon elle revient au premier arrivé parmi les autres, et
si personne d'autre n'est libre, personne ne couvre (comme le marquage). Le couvreur dont l'accord autorise une sortie
est réservé pour le reste du tick (réserve A2 de l'expert au 10b) : ni couverture, ni marquage, ni suivi ; il reste
libre pour la compensation qui comblera la place. Le central qui couvre est revérifié à chaque tick, sans l'exemption
« sorti couvert » du pressing et du marquage (décision du propriétaire du 18/11/2026) : si son couvreur n'arrive plus à
temps, la couverture revient à un autre ; le tirage du couvreur reste gardé. Le central déjà titulaire de la
couverture garde la marge `HOLD_MARGIN_S` sur l'arrivée de son couvreur, comme le titulaire d'une compensation ; un
autre central ne prend sans couverture un point de couverture qu'à moins de `HOLE_AWAY_M` moins la distance qu'il
parcourt à pleine vitesse en `HOLD_MARGIN_S`, ou à plus de cette distance en deçà de sa place vers son but
(hystérésis : le titulaire, lui, perd le rôle aux seuils de `line_exit`) (réserve
A1 de l'expert au 10b2 : sans elle, le rôle allait et venait au seuil). Le couvreur d'une sortie en cours est réservé
dès avant le choix de la couverture (réserve A2 du 10b2).

Zones de la surface (ticket v2-realisme/10f, constantes validées par le propriétaire le 21/11/2026 ; chiffres réels non
trouvés, ordres de grandeur des guides d'entraînement) : quand le ballon (ou le point de réception d'une passe) est
dans un couloir extérieur du dernier tiers défendu, à `WIDE_LAST_THIRD_M` = 35 m ou moins de sa ligne de but et hors de
la largeur de la surface, les défenseurs encore libres après le presseur, la couverture, les marqueurs et les
compensations (boucher le couloir d'un latéral monté passe avant la surface, décision du propriétaire du 21/11/2026)
tiennent, dans cet ordre, le premier poteau (4 m de la ligne, 3 m côté ballon), le point de penalty
(11 m, dans l'axe), le second poteau (5 m, 4 m côté opposé) et la zone de retrait (13 m, 6 m côté ballon) :
`BOX_ZONES`. Chaque zone revient au premier arrivé parmi les libres de son propre camp, avec la mémoire du titulaire
(`HOLD_MARGIN_S`) ; Positioning règle la précision du placement, comme pour la couverture. Aucun attribut nouveau.
Réserves A1 et A2 de l'expert, corrigées avec des constantes validées par le propriétaire le 21/11/2026 (« Ok corrige
les ») : les poteaux ne sont tenus que ballon à `POST_ZONES_MAX_M` = 20 m ou moins de la ligne (plus loin, descendre
aux poteaux faisait tomber la ligne de hors-jeu à 4 m ; restent le penalty et le retrait) ; une zone active le reste
tant que le ballon ne dépasse pas ses seuils de plus de `ZONE_HOLD_MARGIN_M` = 2 m (sinon un porteur qui longe un seuil
allumait et éteignait les zones d'un pas à l'autre)."""

from __future__ import annotations

import math
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING

from v2engine.anticipation import reaction_delay_s, receiving_point
from v2engine.attributes import success_probability
from v2engine.condition import effective_rating
from v2engine.contextes import REPLI_APRES_LA_PERTE, contextual_rating
from v2engine.ball_state import BallState
from v2engine.bloc import POSITIONING_REDRAW_S, Bloc
from v2engine.flux import DEFENSE
from v2engine.geometry import PENALTY_AREA_WIDTH_M, PITCH_LENGTH_M, PITCH_WIDTH_M, Vec2, clamp_to_pitch
from v2engine.movement import PlayerState, accel_tau_s, max_speed_mps
from v2engine.possession import MISS_RETRY_S
from v2engine.situation import DEFENSE_PLACEE, TRANSITION_DEFENSIVE

if TYPE_CHECKING:
    from v2engine.perception_memory import PerceptionMemory

PRESSEUR, COUVERTURE, MARQUAGE, COMPENSATION = "presseur", "couverture", "marquage", "compensation"
ZONE_SURFACE = "zone de surface"  # ticket v2-realisme/10f

COVER_DEPTH_M = 6.0
DANGER_M = 25.0
_MARKING_M = (2.5, 1.5, 1.0, 4.0)  # baseline, amplitude, min, max (inversés : bonne note = marquage serré)
_STAYS = (0.85, 0.2, 0.65, 1.0)  # Teamwork : probabilité de tenir le bloc (99 -> 100 %, 55 -> 85 %, 11 -> 65 %)
LEAVE_REDRAW_S = POSITIONING_REDRAW_S  # même rythme de tirage que l'erreur de placement
HOLD_MARGIN_S = 0.3
# Pressing coordonné (ticket 08) : (baseline, amplitude, min, max) sur la courbe partagée
_PRESS_INTENSITY = (0.8, 0.25, 0.55, 1.0)  # Work Rate
_PRESS_REST_S = (10.0, -10.0, 5.0, 20.0)  # Work Rate (amplitude négative : bonne note = repos court)
# Intensité selon le rôle (ticket v2-realisme/12d, constantes recommandées et retenues par délégation du propriétaire,
# 11/11/2026) : part de la vitesse max pour rejoindre sa place, Work Rate (efforts sans ballon) la module. Vitesse max
# d'un joueur moyen 30 km/h : sans ballon, course (0,55 : 16,5 km/h ; 14,4-19,8 km/h au réel, Bradley 2009) ; en
# possession, trot (0,40 : 12 km/h ; 7-14,4 km/h). Le repli et le pressing gardent `_PRESS_INTENSITY` (sprint).
_REPLACE_INTENSITY = (0.55, 0.10, 0.45, 0.65)  # Work Rate, sans ballon
_HOLD_INTENSITY = (0.40, 0.08, 0.32, 0.48)  # Work Rate, en possession
# Marquage et couverture à l'allure suivie (ticket v2-realisme/18d, PROVISOIRE, recommandée et retenue par délégation
# du propriétaire, 11/11/2026 ; mesure : `docs/INDICATEURS_V2.md` section 28) : le défenseur suit l'allure de l'adversaire
# qu'il marque ou couvre, plus `FOLLOW_CATCH_UP` de sa vitesse max pour reprendre l'écart (3 km/h pour un joueur
# moyen ; 0,20 essayé : sans effet mesurable sur les défenseurs), jamais sous sa course sans ballon (`_REPLACE_INTENSITY`). Avant : sprint quelle que soit l'allure de l'adversaire
# (38 % de la course au-dessus de 19,8 km/h des milieux venait du marquage).
FOLLOW_CATCH_UP = 0.10
_GOOD_LANE = (0.65, 0.25, 0.40, 0.85)  # Anticipation
_STOP_M = (1.2, -0.4, 0.8, 1.6)  # Aggression
_FOLLOWS = (0.8, 0.25, 0.55, 0.95)  # Teamwork
PRESS_BURST_S = 5.0
SHADOW_M = 1.5
TRIGGER_S = 5.0
FOLLOW_M = 15.0
# Ligne de tir (ticket v2-realisme/10k, recommandation retenue par délégation du propriétaire, 21/11/2026) : porteur à
# `SHOT_LANE_RANGE_M` ou moins du centre du but défendu, le presseur qui lit bien (même courbe Anticipation que la ligne
# de passe, `_GOOD_LANE`, un tirage par presseur et porteur) tourne vers la ligne de tir au lieu de la ligne de passe,
# sur le même arc (`SHADOW_M`). Diagnostic (20 matchs) : presseur à 1,5 m en médiane mais ligne de tir couverte dans
# 21 % des tirs de 16 à 25 m, 9 % contrés. 25 m : portée des frappes de loin retenues au 18m (8 tirs sur 167 au-delà).
SHOT_LANE_RANGE_M = 25.0
OPTION_RANGE_M = 40.0  # receveurs considérés par le presseur (même portée que l'indicateur des solutions de passe)
BACKWARD_MPS = 0.5  # porteur qui reçoit en reculant vers son but : vitesse vers son but au-delà de 0,5 m/s
BACKWARD_PASS_M = 3.0  # passe en retrait : le receveur est au moins 3 m plus près de son but (réserve A2 de l'expert)
MISS_FRESH_S = 0.25  # un contrôle raté déclenche s'il date de moins de 0,25 s
HOLE_AWAY_M = 10.0  # compensations (ticket v2-collectif/09)
HOLE_FILLED_M = 5.0
HOLE_DANGER_M = 20.0
CASCADE_LEVELS = 2
_HOLE_POSTES = ("DC", "LB", "RB")
ZONE_DEPTH_M = 8.0  # presseur selon la zone (ticket v2-realisme/10a)
ZONE_WIDTH_M = 10.0
PRESS_ZONE_MARGIN_S = 1.0
# Joueurs de champ qui restent derrière le ballon en possession installée (validé le 30/10/2026, ticket v2-collectif/06),
# et qui ne contre-pressent pas à la perte (ticket v2-collectif/10)
REST_DEFENDERS = 2
# zones de la surface (ticket v2-realisme/10f) : (nom, distance à la ligne de but, décalage côté ballon), par priorité
WIDE_LAST_THIRD_M = 35.0
BOX_ZONES = (("premier poteau", 4.0, 3.0), ("point de penalty", 11.0, 0.0), ("second poteau", 5.0, -4.0),
             ("retrait", 13.0, 6.0))
POST_ZONES = ("premier poteau", "second poteau")  # réserve A1 de l'expert : seulement ballon proche
POST_ZONES_MAX_M = 20.0
ZONE_HOLD_MARGIN_M = 2.0  # réserve A2 de l'expert : marge de maintien d'une zone active


def own_goal(team: str) -> Vec2:
    """Centre du but défendu (domicile défend x = 0)."""
    return Vec2(0.0 if team == "home" else PITCH_LENGTH_M, PITCH_WIDTH_M / 2.0)


def box_zone_spots(ball: Vec2, goal: Vec2, held: frozenset[str] = frozenset()) -> list[tuple[str, Vec2]]:
    """Zones de la surface à tenir (ticket v2-realisme/10f), par priorité, quand `ball` est dans un couloir extérieur
    du dernier tiers défendu (but `goal`) ; les poteaux seulement à `POST_ZONES_MAX_M` ou moins de la ligne. `held` :
    zones actives au tick précédent, gardées jusqu'à `ZONE_HOLD_MARGIN_M` au-delà de leurs seuils."""
    depth, aside = abs(ball.x - goal.x), ball.y - goal.y
    inward = 1.0 if goal.x < PITCH_LENGTH_M / 2.0 else -1.0
    side = 1.0 if aside > 0.0 else -1.0
    spots = []
    for name, zone_depth, offset in BOX_ZONES:
        margin = ZONE_HOLD_MARGIN_M if name in held else 0.0
        reach = (POST_ZONES_MAX_M if name in POST_ZONES else WIDE_LAST_THIRD_M) + margin
        if depth <= reach and abs(aside) > PENALTY_AREA_WIDTH_M / 2.0 - margin:
            spots.append((name, Vec2(goal.x + inward * zone_depth, goal.y + side * offset)))
    return spots


def arrival_time_s(player: PlayerState, point: Vec2) -> float:
    """Temps pour rejoindre `point` : distance à vitesse de pointe, plus le temps de montée en vitesse (capacité)."""
    return player.position.distance_to(point) / max_speed_mps(effective_rating(player, "Pace")) + accel_tau_s(effective_rating(player, "Acceleration"))


def marking_distance_m(player: PlayerState) -> float:
    baseline, amplitude, low, high = _MARKING_M
    return low + high - success_probability(effective_rating(player, "Marking"), baseline=baseline,
                                            amplitude=amplitude, min_prob=low, max_prob=high)


def leave_probability(player: PlayerState) -> float:
    baseline, amplitude, low, high = _STAYS
    return 1.0 - success_probability(effective_rating(player, "Teamwork"), baseline=baseline, amplitude=amplitude,
                                     min_prob=low, max_prob=high)


def _curve(note: float, curve: tuple[float, float, float, float]) -> float:
    baseline, amplitude, low, high = curve
    return success_probability(note, baseline=baseline, amplitude=amplitude, min_prob=low, max_prob=high)


def press_intensity(player: PlayerState) -> float:
    return _curve(effective_rating(player, "Work Rate"), _PRESS_INTENSITY)


def retreat_intensity(player: PlayerState) -> float:
    """Part de sa vitesse max pour se replier après la perte (ticket v2-collectif/10) : courbe du presseur, appliquée
    depuis le ticket v2-attributs-contextes/03 au contexte « repli après la perte » (Work Rate 0,7, Teamwork 0,3)
    au lieu de Work Rate seul."""
    return _curve(contextual_rating(player, REPLI_APRES_LA_PERTE), _PRESS_INTENSITY)


def replacement_intensity(player: PlayerState, in_possession: bool) -> float:
    """Part de sa vitesse max pour rejoindre sa place dans le bloc (ticket v2-realisme/12d) : trot en possession,
    course sans ballon, plus vite quand Work Rate est haut."""
    return _curve(effective_rating(player, "Work Rate"), _HOLD_INTENSITY if in_possession else _REPLACE_INTENSITY)


def follow_intensity(player: PlayerState, target_velocity: Vec2) -> float:
    """Part de sa vitesse max pour marquer ou couvrir (ticket v2-realisme/18d) : l'allure de l'adversaire suivi plus
    `FOLLOW_CATCH_UP`, entre sa course sans ballon et le sprint."""
    pace = target_velocity.length() / max_speed_mps(effective_rating(player, "Pace")) + FOLLOW_CATCH_UP
    return min(1.0, max(replacement_intensity(player, False), pace))


def press_rest_s(player: PlayerState) -> float:
    return _curve(effective_rating(player, "Work Rate"), _PRESS_REST_S)


def good_lane_probability(player: PlayerState) -> float:
    return _curve(effective_rating(player, "Anticipation"), _GOOD_LANE)


def stop_distance_m(player: PlayerState) -> float:
    return _curve(effective_rating(player, "Aggression"), _STOP_M)


def follow_probability(player: PlayerState) -> float:
    return _curve(effective_rating(player, "Teamwork"), _FOLLOWS)


def press_point(presser: PlayerState, holder: PlayerState, receiver: PlayerState | None,
                aim: Vec2 | None = None) -> Vec2:
    """Où le presseur se présente : à sa distance d'arrêt (Aggression) du porteur, du côté de la ligne de passe vers
    `receiver` (ou de la ligne vers `aim`, le but défendu pour la ligne de tir, ticket v2-realisme/10k), à au plus
    `SHADOW_M` de son approche directe."""
    distance = stop_distance_m(presser)
    approach = presser.position - holder.position
    toward = aim if aim is not None else (receiver.position if receiver is not None else None)
    if approach.length() < 1e-9 or toward is None or toward.distance_to(holder.position) < 1e-9:
        return clamp_to_pitch(holder.position + approach.normalized() * distance if approach.length() > 1e-9
                              else holder.position)
    # il tourne autour du porteur, de son approche directe vers la ligne fermée, d'un arc de corde SHADOW_M au plus
    start = math.atan2(approach.y, approach.x)
    lane = toward - holder.position
    turn = (math.atan2(lane.y, lane.x) - start + math.pi) % (2.0 * math.pi) - math.pi
    limit = 2.0 * math.asin(min(1.0, SHADOW_M / (2.0 * distance)))
    angle = start + max(-limit, min(limit, turn))
    return clamp_to_pitch(holder.position + Vec2(math.cos(angle), math.sin(angle)) * distance)


def _goal_side(point: Vec2, goal: Vec2, distance: float) -> Vec2:
    """Point à `distance` de `point`, vers le but (le point lui-même s'il est déjà dans le but)."""
    to_goal = goal - point
    return point if to_goal.length() < 1e-9 else clamp_to_pitch(point + to_goal.normalized() * min(distance, to_goal.length()))


def in_zone(name: str, places: dict[str, Vec2], point: Vec2, goal: Vec2) -> bool:
    """`point` est-il dans la zone de responsabilité du joueur `name` (ticket v2-realisme/10a) ? `places` : place de
    référence sans ballon de chaque joueur de champ de son équipe ; `goal` : son but. Rectangle de `ZONE_DEPTH_M` en
    profondeur et `ZONE_WIDTH_M` en largeur de chaque côté de sa place, ouvert vers son but s'il est dans la dernière
    ligne, vers l'avant s'il est dans la ligne la plus avancée, vers la touche si aucun partenaire de sa bande de
    profondeur n'est plus excentré que lui de ce côté."""
    place = places[name]
    depths = {n: abs(v.x - goal.x) for n, v in places.items()}
    ahead = abs(point.x - goal.x) - depths[name]
    if ahead < -ZONE_DEPTH_M and depths[name] - min(depths.values()) > ZONE_DEPTH_M:
        return False  # derrière sa zone, et une ligne derrière lui
    if ahead > ZONE_DEPTH_M and max(depths.values()) - depths[name] > ZONE_DEPTH_M:
        return False  # devant sa zone, et une ligne devant lui
    aside = point.y - place.y
    if abs(aside) <= ZONE_WIDTH_M:
        return True
    side = 1.0 if aside > 0.0 else -1.0
    # un partenaire dont la zone recouvre la sienne en profondeur est plus excentré de ce côté : sa zone n'y va pas
    return not any(n != name and (v.y - place.y) * side > ZONE_WIDTH_M
                   and abs(depths[n] - depths[name]) < 2.0 * ZONE_DEPTH_M for n, v in places.items())


@dataclass(frozen=True)
class Assignment:
    role: str
    target: Vec2
    mate: str  # porteur pressé ou couvert, attaquant marqué ; zone tenue (`BOX_ZONES`, ticket v2-realisme/10f)
    target_velocity: Vec2
    intensity: float = 1.0  # part de la vitesse max (presseur : Work Rate, ticket 08)
    # presseur (ticket v2-realisme/10a) : le porteur est-il dans sa zone (None : pas de bloc) ; place de référence sans
    # ballon du presseur, et depuis le ticket v2-realisme/10b de la couverture et des marqueurs (trace des sorties)
    zone: bool | None = None
    reference: Vec2 | None = None


@dataclass
class DefensiveRoles:
    """Rôles de l'équipe sans ballon (`update`, une fois par tick) et indiscipline de chaque joueur (`leaves_the_bloc`)."""
    assignments: dict[str, Assignment] = field(default_factory=dict)
    leaving: dict[str, tuple[bool, float]] = field(default_factory=dict)  # joueur -> (quitte le bloc, prochain tirage)
    # titulaires du tick précédent : (rôle, porteur) -> défenseur (`HOLD_MARGIN_S`) ; (COMPENSATION, absent) -> compensateur
    holders: dict[tuple[str, str], str] = field(default_factory=dict)
    # pressing coordonné (ticket 08)
    # presseur -> (porteur, début de l'effort) ; gardé s'il revient sur le même porteur (réserve A4 de l'expert)
    burst: dict[str, tuple[str, float]] = field(default_factory=dict)
    rest_until: dict[str, float] = field(default_factory=dict)  # presseur qui souffle -> fin du repos
    lanes: dict[tuple[str, str], str | None] = field(default_factory=dict)  # (presseur, porteur) -> receveur fermé
    shot_lanes: dict[tuple[str, str], bool] = field(default_factory=dict)  # (presseur, porteur) -> lit le tir (10k)
    trigger_until: dict[str, float] = field(default_factory=dict)  # équipe -> fin du pressing d'équipe
    follows: dict[str, bool] = field(default_factory=dict)  # partenaire -> suit le pressing d'équipe en cours
    followed: dict[str, str] = field(default_factory=dict)  # partenaire qui suit -> receveur qu'il ferme
    last_holder: tuple[str, str, float] | None = None  # (nom, équipe, progression) du porteur précédent
    seen_misses: set[tuple[str, float]] = field(default_factory=set)
    # compensations (ticket 09)
    willing: dict[tuple[str, str], bool] = field(default_factory=dict)  # (absent, candidat) -> accepte (Teamwork)
    levels: dict[str, int] = field(default_factory=dict)  # compensateur -> niveau de cascade de sa compensation
    # central qui ne sort que couvert (ticket v2-realisme/10b)
    exits: dict[str, str] = field(default_factory=dict)  # central sorti de sa ligne à ce tick -> partenaire visé
    exits_before: dict[str, str] = field(default_factory=dict)  # même chose au tick précédent (lu par la vérification)
    # (central, couvreur, partenaire visé) -> accepte : tirage Teamwork du central encore à sa place, gardé tant que le
    # porteur ne change pas
    cover_draws: dict[tuple[str, str, str], bool] = field(default_factory=dict)
    # (central, partenaire visé) -> couvreur dont l'accord autorise la sortie, à ce tick
    cover_found: dict[tuple[str, str], str] = field(default_factory=dict)
    # central sorti couvert -> (couvreur, partenaire visé) : l'accord devient le tirage du trou (`willing`), repris par
    # la compensation quel que soit le porteur, tant que la sortie dure (expert, passage 2)
    exit_cover: dict[str, tuple[str, str]] = field(default_factory=dict)
    reserved: set[str] = field(default_factory=set)  # couvreurs retenus à ce tick (10b2) : seule la compensation
    zones_held: dict[str, frozenset[str]] = field(default_factory=dict)  # équipe -> zones actives (10f, réserve A2)

    def resting(self, player: PlayerState, now_s: float) -> bool:
        return self.rest_until.get(player.name, 0.0) > now_s

    def start_team_press(self, team: str, players: list[PlayerState], now_s: float,
                         excluded: frozenset[str] = frozenset()) -> None:
        self.trigger_until[team] = now_s + TRIGGER_S
        self.followed = {}
        for p in players:
            if p.team == team:
                self.follows[p.name] = p.name not in excluded and DEFENSE.random() < follow_probability(p)

    def _counter_press(self, team: str, players: list[PlayerState], ball: BallState, now_s: float) -> None:
        """Contre-pressing à la perte (ticket v2-collectif/10) : pressing d'équipe pour `team`, suivi seulement par les
        joueurs proches du ballon, hors les plus reculés."""
        goal = own_goal(team)
        field_players = sorted((p for p in players if p.team == team and p.poste != "GK"),
                               key=lambda p: abs(p.position.x - goal.x))
        far = {p.name for p in field_players if p.position.distance_to(ball.position) > FOLLOW_M}
        self.start_team_press(team, players, now_s, frozenset(far | {p.name for p in field_players[:REST_DEFENDERS]}))

    def _watch_triggers(self, players: list[PlayerState], ball: BallState, holder: PlayerState | None,
                        now_s: float, situations: dict[str, str] | None = None) -> None:
        """Déclencheurs du pressing d'équipe : passe en retrait, réception en reculant vers son but, contrôle raté ;
        avec `situations`, perte dans le jeu (contre-pressing, ticket v2-collectif/10)."""
        self.seen_misses = {m for m in self.seen_misses if m[1] > now_s}  # échus : oubliés (A4 de l'expert, passage 2)
        for name, until in ball.control_ban_until_s.items():
            if until > now_s and (name, until) not in self.seen_misses:
                self.seen_misses.add((name, until))
                missed = next((p for p in players if p.name == name), None)
                if missed is not None and until - now_s >= MISS_RETRY_S - MISS_FRESH_S:
                    self.start_team_press("away" if missed.team == "home" else "home", players, now_s)
        if holder is None:
            return
        goal = own_goal(holder.team)
        progress = abs(holder.position.x - goal.x)
        previous, self.last_holder = self.last_holder, (holder.name, holder.team, progress)
        # perte dans le jeu (ticket v2-collectif/10) : ni ballon pris par le gardien, ni coup franc de hors-jeu
        if previous is not None and previous[1] != holder.team and situations is not None \
                and situations.get(previous[1]) == TRANSITION_DEFENSIVE and holder.poste != "GK" \
                and not any(until > now_s for until in ball.offside_out_until.values()):
            self._counter_press(previous[1], players, ball, now_s)
        if previous is None or previous[0] == holder.name or previous[1] != holder.team:
            return
        backward = holder.velocity.x * (1.0 if goal.x > holder.position.x else -1.0) > BACKWARD_MPS
        if progress < previous[2] - BACKWARD_PASS_M or backward:
            self.start_team_press("away" if holder.team == "home" else "home", players, now_s)

    def _lane(self, presser: PlayerState, holder: PlayerState, players: list[PlayerState],
              goal: Vec2) -> PlayerState | None:
        """Receveur dont le presseur ferme la ligne : le plus dangereux s'il lit bien (Anticipation), sinon un autre."""
        key = (presser.name, holder.name)
        if key not in self.lanes:
            options = sorted((p for p in players if p.team == holder.team and p.name != holder.name and p.poste != "GK"
                              and p.position.distance_to(holder.position) <= OPTION_RANGE_M),
                             key=lambda p: p.position.distance_to(goal))
            if not options:
                self.lanes[key] = None
            elif len(options) == 1 or DEFENSE.random() < good_lane_probability(presser):
                self.lanes[key] = options[0].name
            else:
                self.lanes[key] = DEFENSE.choice(options[1:]).name
        return next((p for p in players if p.name == self.lanes[key]), None)

    def _reads_shot(self, presser: PlayerState, holder: PlayerState) -> bool:
        """Le presseur ferme la ligne de tir (ticket v2-realisme/10k) : Anticipation, un tirage par presseur et porteur."""
        key = (presser.name, holder.name)
        if key not in self.shot_lanes:
            self.shot_lanes[key] = DEFENSE.random() < good_lane_probability(presser)
        return self.shot_lanes[key]

    @staticmethod
    def _press_pool(fresh: list[PlayerState], holder: PlayerState, places: dict[str, Vec2],
                    goal: Vec2) -> list[PlayerState]:
        """Candidats au pressing (ticket v2-realisme/10a) : ceux dont la zone contient le porteur et qui arrivent au
        plus `PRESS_ZONE_MARGIN_S` après le plus rapide de tous ; aucun : tous (le premier arrivé presse)."""
        if not places:
            return fresh
        limit = min(arrival_time_s(p, holder.position) for p in fresh) + PRESS_ZONE_MARGIN_S
        return [p for p in fresh if p.name in places and in_zone(p.name, places, holder.position, goal)
                and arrival_time_s(p, holder.position) <= limit] or fresh

    def _keep(self, previous: dict[tuple[str, str], str], role: str, mate: str, free: list[PlayerState], point: Vec2,
              best: PlayerState) -> PlayerState:
        """`best`, sauf si le titulaire du rôle pour `mate` est encore libre et n'arrive pas 0,3 s plus tard que lui."""
        incumbent = next((p for p in free if p.name == previous.get((role, mate))), None)
        if incumbent is not None and arrival_time_s(incumbent, point) <= arrival_time_s(best, point) + HOLD_MARGIN_S:
            best = incumbent
        self.holders[(role, mate)] = best.name
        return best

    def update(self, players: list[PlayerState], ball: BallState, bloc: Bloc | None, now_s: float,
               situations: dict[str, str] | None = None, memory: PerceptionMemory | None = None) -> None:
        """`situations` : situation de chaque équipe (`SituationTracker.current`), pour le contre-pressing (ticket 10).
        `memory` : mémoire de perception (ticket v2-realisme/08e) : chaque marqueur situe l'attaquant qu'il marque là où
        il le perçoit, pas là où il est ; le ballon et son porteur restent connus de tous, et le plan de l'équipe (qui
        est dangereux, qui est le receveur proche) reste sur les vraies positions. Sans mémoire : les vraies positions."""
        self.assignments = {}
        self.exits_before, self.exits = self.exits, {}  # aucun rôle à ce tick (ballon libre) : aucune sortie gardée
        self.cover_found, self.reserved = {}, set()
        holder = next((p for p in players if p.name == ball.holder), None) if ball.holder else None
        previous_holder = self.last_holder  # avant `_watch_triggers`, qui le remplace
        self._watch_triggers(players, ball, holder, now_s, situations)  # le vrai porteur, même pendant une passe
        previous = self.holders
        if holder is None:  # passe en vol (réserve A2) : le receveur, à son point de réception
            receiver = next((p for p in players if p.name == ball.receiver), None) if ball.receiver else None
            if receiver is None or ball.last_pass_team != receiver.team:
                self.zones_held = {}  # ballon libre : plus de zone active à garder (10f, réserve A2)
                return
            point = clamp_to_pitch(receiving_point(receiver, ball))  # même point que le receveur (ticket v2-realisme/15a1)
            holder = replace(receiver, position=point, velocity=Vec2(0.0, 0.0))
            # titulaires du passeur gardés : il peut récupérer le ballon (passe coupée, rendue) ; ceux des
            # compensations sont réécrits à chaque tick par `_compensate`, qui lit `previous`
            self.holders = {k: v for k, v in previous.items() if k[1] != holder.name and k[0] != COMPENSATION}
        else:
            self.holders = {}
            # effort et ligne lue valent pour la détention en cours : oubliés quand le porteur change (A1 et A2 de
            # l'expert, passage 2 ; sans cela, un presseur retrouvant plus tard ce porteur était mis au repos après un
            # effort quasi nul)
            self.burst = {k: v for k, v in self.burst.items() if v[0] == holder.name}
            self.lanes = {k: v for k, v in self.lanes.items() if k[1] == holder.name}
            self.shot_lanes = {k: v for k, v in self.shot_lanes.items() if k[1] == holder.name}
            if previous_holder is not None and previous_holder[0] != holder.name:
                self.cover_draws = {}  # tirages des couvreurs (10b) : un par porteur, comme la ligne lue
        team = "away" if holder.team == "home" else "home"
        goal = own_goal(team)
        # le lecteur de passe court la couper (priorité dans `cerveau`) : pas d'autre rôle pour lui
        free = [p for p in players if p.team == team and p.poste != "GK" and p.name not in ball.readers]
        if not free:
            return
        fresh = [p for p in free if not self.resting(p, now_s)] or free  # celui qui souffle ne presse pas
        # zones de responsabilité (ticket v2-realisme/10a) : places de référence sans ballon, ballon au porteur
        places = {} if bloc is None else {p.name: bloc.reference(p, holder.position, DEFENSE_PLACEE, now_s)
                                          for p in players if p.team == team and p.poste != "GK"}
        # le central ne sort pas sans couverture (ticket v2-realisme/10b) ; seul joueur libre, il presse quand même
        uncovered = {p.name for p in fresh
                     if self._leaves_uncovered(p, holder.position, holder.name, players, free, places, goal, ball, now_s)}
        pool = self._press_pool([p for p in fresh if p.name not in uncovered] or fresh, holder, places, goal)
        best = min(pool, key=lambda p: arrival_time_s(p, holder.position))
        # le titulaire reste candidat hors de sa zone (`HOLD_MARGIN_S`) : sans cela, le porteur qui longe le bord
        # d'une zone faisait changer le presseur puis revenir dans la seconde (21,6 % des relais, 1,9 % avant 10a)
        incumbent = [p for p in fresh if p.name == previous.get((PRESSEUR, holder.name)) and p not in pool
                     and p.name not in uncovered]
        presser = self._keep(previous, PRESSEUR, holder.name, pool + incumbent, holder.position, best)
        start = self.burst.get(presser.name)
        if start is None or start[0] != holder.name:
            self.burst[presser.name] = (holder.name, now_s)
        elif now_s - start[1] >= PRESS_BURST_S and len(fresh) > 1:  # effort fini : il souffle, un autre prend le relais
            self.rest_until[presser.name] = now_s + press_rest_s(presser)
            del self.burst[presser.name]  # reposé, il repartira pour un nouvel effort
            fresh.remove(presser)
            presser = min(self._press_pool([p for p in fresh if p.name not in uncovered] or fresh, holder, places, goal),
                          key=lambda p: arrival_time_s(p, holder.position))
            self.holders[(PRESSEUR, holder.name)] = presser.name
            self.burst[presser.name] = (holder.name, now_s)
        if holder.position.distance_to(goal) <= SHOT_LANE_RANGE_M and self._reads_shot(presser, holder):
            target = press_point(presser, holder, None, aim=goal)  # ligne de tir (ticket v2-realisme/10k)
        else:
            target = press_point(presser, holder, self._lane(presser, holder, players, goal))
        self.assignments[presser.name] = Assignment(
            PRESSEUR, target, holder.name, holder.velocity, press_intensity(presser),
            in_zone(presser.name, places, holder.position, goal) if presser.name in places else None,
            places.get(presser.name))
        free.remove(presser)
        self._reserve_coverer(presser, target, holder.name, places, goal)
        own_half = holder.position.distance_to(Vec2(goal.x, holder.position.y)) <= PITCH_LENGTH_M / 2.0
        if own_half and free and holder.position.distance_to(goal) > 1e-9:  # porteur dans le but : rien à couvrir
            spot = _goal_side(holder.position, goal, COVER_DEPTH_M)
            # le couvreur d'une sortie en cours (marquage, suivi : attribués après) est réservé dès maintenant (10b2)
            self.reserved |= {coverer for name, (coverer, mate) in self.exit_cover.items()
                              if self.exits_before.get(name) == mate}
            # le central qui sortirait sans couverture ne couvre pas (10b2) ; personne d'autre : personne ne couvre ; le
            # central qui couvrait déjà ce porteur garde la marge du titulaire (`HOLD_MARGIN_S`, comme la compensation)
            covers = [p for p in free if p.name not in self.reserved and not self._leaves_uncovered(
                p, spot, holder.name, players, free, places, goal, ball, now_s, recheck=True,
                margin_s=HOLD_MARGIN_S if previous.get((COUVERTURE, holder.name)) == p.name else 0.0)]
            if covers:
                cover = self._keep(previous, COUVERTURE, holder.name, covers, spot,
                                   min(covers, key=lambda p: arrival_time_s(p, spot)))
                self._reserve_coverer(cover, spot, holder.name, places, goal)
                if bloc is not None:  # Positioning : précision du placement, comme dans le bloc
                    spot = clamp_to_pitch(spot + bloc.placement_error(cover, now_s))
                self.assignments[cover.name] = Assignment(COUVERTURE, spot, holder.name, holder.velocity,
                                                          reference=places.get(cover.name))
                free.remove(cover)
        # l'attaquant qui recule après un hors-jeu sifflé (ticket 23) n'est pas marqué
        dangerous = sorted((p for p in players if p.team == holder.team and p.name != holder.name and p.poste != "GK"
                            and p.position.distance_to(goal) <= DANGER_M and ball.offside_out_until.get(p.name, 0.0) <= now_s),
                           key=lambda p: p.position.distance_to(goal))
        for attacker in dangerous:
            if not free:
                break
            # le central qui sortirait sans couverture garde sa ligne (ticket v2-realisme/10b) : le suivant marque
            candidates = [p for p in free if p.name not in self.reserved and not self._leaves_uncovered(
                p, _goal_side(attacker.position, goal, marking_distance_m(p)), attacker.name, players, free, places,
                goal, ball, now_s)]
            if not candidates:
                continue
            marker = self._closest_to(candidates, attacker, memory, now_s)
            where, moving = self._seen_at(marker, attacker, memory, now_s)
            spot = _goal_side(where, goal, marking_distance_m(marker))
            self.assignments[marker.name] = Assignment(MARQUAGE, spot, attacker.name, moving,
                                                       reference=places.get(marker.name))
            free.remove(marker)
            self._reserve_coverer(marker, spot, attacker.name, places, goal)
        if bloc is not None:  # niveaux de cascade gardés tant qu'aucun tick ne les recalcule (ballon libre)
            levels, self.levels = self.levels, {}
            self._compensate(players, ball, holder, team, goal, free, bloc, previous, levels, now_s)
        # zones de la surface (ticket v2-realisme/10f), après les compensations (décision du propriétaire, 21/11/2026)
        spots = box_zone_spots(holder.position, goal, self.zones_held.get(team, frozenset()))
        self.zones_held[team] = frozenset(zone for zone, _ in spots)
        for zone, spot in spots:
            # libres de son propre camp ; les points sont plus près du but que toute place : aucune sortie de ligne
            candidates = [p for p in free if p.name not in self.reserved
                          and abs(p.position.x - goal.x) <= PITCH_LENGTH_M / 2.0]
            if not candidates:
                break
            keeper = self._keep(previous, ZONE_SURFACE, zone, candidates, spot,
                                min(candidates, key=lambda p: arrival_time_s(p, spot)))
            if bloc is not None:  # Positioning : précision du placement, comme la couverture
                spot = clamp_to_pitch(spot + bloc.placement_error(keeper, now_s))
            self.assignments[keeper.name] = Assignment(ZONE_SURFACE, spot, zone, Vec2(0.0, 0.0),
                                                       reference=places.get(keeper.name))
            free.remove(keeper)
        if self.trigger_until.get(team, 0.0) > now_s:  # pressing d'équipe : les partenaires proches suivent (Teamwork)
            marked = {a.mate for a in self.assignments.values()}
            defenders = [p for p in players if p.team == team]
            # le plus libre d'abord : le plus loin de tout défenseur
            near = sorted((p for p in players if p.team == holder.team and p.name != holder.name and p.poste != "GK"
                           and p.name not in marked and p.position.distance_to(holder.position) <= FOLLOW_M),
                          key=lambda p: -min(d.position.distance_to(p.position) for d in defenders))
            # chacun garde son receveur jusqu'à la fin du pressing d'équipe (sans quoi il change de cible en courant)
            near.sort(key=lambda p: p.name not in self.followed.values())
            for receiver in near:
                followers = [p for p in free if self.follows.get(p.name)]
                if not followers:
                    break
                # le central qui sortirait sans couverture ne suit pas (ticket v2-realisme/10b)
                followers = [p for p in followers if p.name not in self.reserved and not self._leaves_uncovered(
                    p, _goal_side(receiver.position, holder.position, marking_distance_m(p)), receiver.name, players,
                    free, places, goal, ball, now_s)]
                if not followers:
                    continue
                marker = next((p for p in followers if self.followed.get(p.name) == receiver.name), None) or self._closest_to(
                    [p for p in followers if self.followed.get(p.name) not in {r.name for r in near}] or followers,
                    receiver, memory, now_s)
                self.followed[marker.name] = receiver.name
                # côté ballon, sur la ligne de passe : il ferme la solution plutôt que de couvrir son but
                where, moving = self._seen_at(marker, receiver, memory, now_s)
                spot = _goal_side(where, holder.position, marking_distance_m(marker))
                self.assignments[marker.name] = Assignment(MARQUAGE, spot, receiver.name, moving,
                                                           reference=places.get(marker.name))
                free.remove(marker)
                self._reserve_coverer(marker, spot, receiver.name, places, goal)
        self._remember_exits(players, goal)

    def _remember_exits(self, players: list[PlayerState], goal: Vec2) -> None:
        """Centraux sortis de leur ligne à ce tick, avec le partenaire visé (ticket v2-realisme/10b) : ils gardent leur
        rôle pour lui sans nouvelle vérification."""
        postes = {p.name: p.poste for p in players}
        self.exits = {n: a.mate for n, a in self.assignments.items()
                      if postes.get(n) == "DC" and a.role in (PRESSEUR, MARQUAGE, COUVERTURE) and a.reference is not None
                      and line_exit(a.target, a.reference, goal)}
        # le couvreur qui a autorisé la sortie (nouvelle) ou celui de la sortie en cours (même partenaire) : son accord
        # est le tirage du trou, réécrit à chaque tick tant que la sortie dure (l'effacement des trous refermés, dans
        # `_compensate`, passe avant)
        covers = {}
        for name, mate in self.exits.items():
            if (name, mate) in self.cover_found:
                covers[name] = (self.cover_found[(name, mate)], mate)
            elif self.exit_cover.get(name, ("", ""))[1] == mate:
                covers[name] = self.exit_cover[name]
        self.exit_cover = covers
        for name, (coverer, _) in covers.items():
            self.willing[(name, coverer)] = True

    def _reserve_coverer(self, player: PlayerState, target: Vec2, mate: str, places: dict[str, Vec2],
                         goal: Vec2) -> None:
        """`player` prend un rôle qui vise `target` pour `mate` : si c'est la sortie d'un central autorisée par un couvreur
        (à ce tick, ou sortie en cours pour le même partenaire), ce couvreur est réservé pour le reste du tick (ticket
        v2-realisme/10b2, réserve A2 de l'expert au 10b) : il ne prend ni couverture, ni marquage, ni suivi."""
        if player.poste != "DC" or player.name not in places or not line_exit(target, places[player.name], goal):
            return
        coverer = self.cover_found.get((player.name, mate))
        if coverer is None and self.exits_before.get(player.name) == mate \
                and self.exit_cover.get(player.name, ("", ""))[1] == mate:
            coverer = self.exit_cover[player.name][0]
        if coverer is not None:
            self.reserved.add(coverer)

    def _leaves_uncovered(self, player: PlayerState, target: Vec2, mate: str, players: list[PlayerState],
                          free: list[PlayerState], places: dict[str, Vec2], goal: Vec2, ball: BallState,
                          now_s: float, recheck: bool = False, margin_s: float = 0.0) -> bool:
        """Le central `player`, en visant `target` pour `mate`, quitterait-il sa ligne sans couverture (ticket
        v2-realisme/10b) ? Non s'il n'est pas central, s'il est déjà sorti couvert pour ce partenaire, si `target` n'est
        pas une sortie, si un partenaire tient sa place, si aucun attaquant ne la menace ou si un compensateur libre y
        arrive avant l'attaquant et l'accepte (Teamwork). `recheck` (couverture, 10b2) : pas d'exemption « sorti
        couvert », la vérification est refaite à chaque tick ; `margin_s` : délai accordé au couvreur quand le central
        est déjà titulaire du rôle (`HOLD_MARGIN_S`, sinon le rôle va et vient au seuil). Hystérésis du seuil de sortie
        à la revérification : le titulaire perd le rôle aux seuils de `line_exit` ; un autre central ne le prend sans
        couverture qu'en deçà de `HOLE_AWAY_M` moins la distance qu'il parcourt en `HOLD_MARGIN_S`, ou à plus de cette
        distance en deçà de sa place vers son but."""
        if player.poste != "DC" or player.name not in places or (
                not recheck and self.exits_before.get(player.name) == mate):
            return False
        place = places[player.name]
        if not line_exit(target, place, goal):
            # revérification, central non titulaire : la sortie commence plus tôt, à `HOLE_AWAY_M` moins la distance qu'il
            # parcourt en `HOLD_MARGIN_S`, et jusqu'à cette distance en deçà de sa place vers son but (réserve A1 au
            # 10b2 : hystérésis ; le titulaire perd le rôle aux seuils de `line_exit`)
            band = HOLD_MARGIN_S * max_speed_mps(effective_rating(player, "Pace"))
            if not recheck or margin_s > 0.0 or target.distance_to(place) <= HOLE_AWAY_M - band \
                    or abs(target.x - goal.x) < abs(place.x - goal.x) - band:
                return False
        if any(m.team == player.team and m.poste != "GK" and m.name != player.name
               and m.position.distance_to(place) <= HOLE_FILLED_M for m in players):
            return False
        threats = [p for p in players if p.team != player.team and p.poste != "GK" and p.name != mate
                   and ball.offside_out_until.get(p.name, 0.0) <= now_s]
        attacker = min(threats, key=lambda p: p.position.distance_to(place), default=None)
        if attacker is None or attacker.position.distance_to(place) > HOLE_DANGER_M:
            return False
        deadline = arrival_time_s(attacker, place)
        ranked = sorted((p for p in free if p.name != player.name and _rank(p, player) is not None),
                        key=lambda p: (_rank(p, player), p.position.distance_to(place)))
        for p in ranked:
            if arrival_time_s(p, place) + reaction_delay_s(p) <= deadline + margin_s and self._covers(player, p, mate):
                self.cover_found[(player.name, mate)] = p.name
                return False
        return True

    def _covers(self, owner: PlayerState, candidate: PlayerState, mate: str) -> bool:
        """Le couvreur accepte-t-il de quitter sa place pour celle du central (Teamwork, courbe des compensations) ? Trou
        encore ouvert : son tirage (`willing`), celui que la compensation appliquera. Sinon un tirage par partenaire visé
        par le central, gardé tant que le porteur ne change pas ; s'il autorise la sortie, il devient le tirage du trou
        (`_remember_exits`)."""
        if (owner.name, candidate.name) in self.willing:
            return self.willing[(owner.name, candidate.name)]
        key = (owner.name, candidate.name, mate)
        if key not in self.cover_draws:
            self.cover_draws[key] = DEFENSE.random() < follow_probability(candidate)
        return self.cover_draws[key]

    @staticmethod
    def _seen_at(marker: PlayerState, attacker: PlayerState, memory: PerceptionMemory | None,
                 now_s: float) -> tuple[Vec2, Vec2]:
        """Où `marker` situe `attacker` et à quelle vitesse (ticket v2-realisme/08e) : sa vraie place et sa vraie vitesse
        s'il le voit, sinon sa dernière vue extrapolée (08b). Sans mémoire : la réalité."""
        if memory is None:
            return attacker.position, attacker.velocity
        return memory.perceived_position(marker, attacker.name, now_s), memory.perceived_velocity(marker, attacker.name)

    @classmethod
    def _closest_to(cls, candidates: list[PlayerState], attacker: PlayerState, memory: PerceptionMemory | None,
                    now_s: float) -> PlayerState:
        """Celui de `candidates` le plus proche de l'attaquant tel qu'il le perçoit chacun (ticket v2-realisme/08e)."""
        if memory is None:
            return min(candidates, key=lambda p: p.position.distance_to(attacker.position))
        return min(candidates,
                   key=lambda p: p.position.distance_to(memory.perceived_position(p, attacker.name, now_s)))

    def _compensate(self, players: list[PlayerState], ball: BallState, holder: PlayerState, team: str, goal: Vec2,
                    free: list[PlayerState], bloc: Bloc, previous: dict[tuple[str, str], str],
                    levels: dict[str, int], now_s: float) -> None:
        """Compensations (ticket v2-collectif/09) : la place d'un défenseur parti est comblée par le premier, dans
        l'ordre de `_rank`, qui arrive avant l'attaquant le plus proche et accepte de quitter la sienne (Teamwork)."""
        mates = [p for p in players if p.team == team and p.poste != "GK"]
        marked = {a.mate for a in self.assignments.values() if a.role == MARQUAGE}
        # le porteur compte, même pressé : l'ailier servi qui file vers la place vide est la menace du scénario de
        # référence (réserve A2 de l'expert, passage 1) ; l'attaquant qui recule après un hors-jeu sifflé (ticket 23) non
        threats = [p for p in players if p.team == holder.team and p.poste != "GK" and p.name not in marked
                   and ball.offside_out_until.get(p.name, 0.0) <= now_s]
        threats = [holder if p.name == holder.name else p for p in threats]  # receveur : à son point de réception
        free_names = {p.name for p in free}
        ball_depth = abs(holder.position.x - goal.x)
        closed = set()
        for owner in (p for p in mates if p.poste in _HOLE_POSTES):
            level = levels.get(owner.name, 0) + 1  # il compense lui-même : sa place est un trou de niveau 2
            key = (COMPENSATION, owner.name)
            # titulaire : seulement s'il est encore libre (passé marqueur, il n'occupe plus la place pour elle)
            incumbent_name = previous.get(key) if previous.get(key) in free_names else None
            place = bloc.reference(owner, holder.position, DEFENSE_PLACEE, now_s)
            depth = abs(place.x - goal.x)
            away = owner.position.distance_to(place)
            if away <= HOLE_FILLED_M:
                closed.add(owner.name)  # revenu : le trou est fini, ses tirages Teamwork aussi
            # il rend la place quand le joueur absent revient à moins de 5 m, on ne la comble qu'au-delà de 10 m
            if level > CASCADE_LEVELS or away <= (HOLE_FILLED_M if incumbent_name else HOLE_AWAY_M) \
                    or depth > PITCH_LENGTH_M / 2.0 or depth >= ball_depth \
                    or any(m is not owner and m.name != incumbent_name
                           and m.position.distance_to(place) < HOLE_FILLED_M for m in mates):
                continue
            attacker = min(threats, key=lambda p: p.position.distance_to(place), default=None)
            if attacker is None or attacker.position.distance_to(place) > HOLE_DANGER_M:
                continue
            deadline = arrival_time_s(attacker, place)
            # arrivé (à 5 m de la place ou du point qu'il vise), il la tient jusqu'au retour de l'absent ; en route, il
            # la garde s'il n'arrive pas plus de `HOLD_MARGIN_S` après l'attaquant
            chosen = next((p for p in free if p.name == incumbent_name and (
                min(p.position.distance_to(place), p.position.distance_to(place + bloc.placement_error(p, now_s)))
                <= HOLE_FILLED_M or arrival_time_s(p, place) <= deadline + HOLD_MARGIN_S)), None)
            if chosen is None:
                ranked = sorted((p for p in free if p is not owner and _rank(p, owner) is not None),
                                key=lambda p: (_rank(p, owner), p.position.distance_to(place)))
                chosen = next((p for p in ranked if arrival_time_s(p, place) + reaction_delay_s(p) <= deadline
                               and self._willing(owner, p)), None)
            if chosen is None:
                continue
            self.holders[key] = chosen.name
            self.levels[chosen.name] = level
            spot = clamp_to_pitch(place + bloc.placement_error(chosen, now_s))  # Positioning, comme la couverture
            self.assignments[chosen.name] = Assignment(COMPENSATION, spot, owner.name, Vec2(0.0, 0.0))
            free.remove(chosen)
        # un tirage par trou : gardé tant que l'absent n'est pas revenu, même si le danger s'éloigne un instant
        self.willing = {k: v for k, v in self.willing.items() if k[0] not in closed}

    def _willing(self, owner: PlayerState, candidate: PlayerState) -> bool:
        """Accepte-t-il de quitter sa place pour combler celle de `owner` ? Teamwork, un tirage par trou."""
        key = (owner.name, candidate.name)  # central sorti couvert (10b) : l'accord du couvreur y est déjà
        if key not in self.willing:
            self.willing[key] = DEFENSE.random() < follow_probability(candidate)
        return self.willing[key]

    def leaves_the_bloc(self, player: PlayerState, now_s: float) -> bool:
        """Sans rôle et près du ballon, quitte-t-il quand même le bloc pour y aller ? Tiré toutes les 5 s (Teamwork)."""
        leaves, next_s = self.leaving.get(player.name, (False, 0.0))
        if now_s >= next_s:
            leaves = DEFENSE.random() < leave_probability(player)
            self.leaving[player.name] = (leaves, now_s + LEAVE_REDRAW_S)
        return leaves


def line_exit(point: Vec2, place: Vec2, goal: Vec2) -> bool:
    """`point` sort-il de la ligne d'un joueur dont la place de référence sans ballon est `place` (ticket
    v2-realisme/10b) ? À plus de `HOLE_AWAY_M` de sa place, sans être plus près de son but `goal` qu'elle."""
    return point.distance_to(place) > HOLE_AWAY_M and abs(point.x - goal.x) >= abs(place.x - goal.x)


def _rank(candidate: PlayerState, owner: PlayerState) -> int | None:
    """Ordre des compensateurs (ticket 09) : milieu défensif, central, latéral opposé (l'un ou l'autre pour un central)."""
    if candidate.poste == "MDC":
        return 0
    if candidate.poste == "DC":
        return 1
    if candidate.poste in ("LB", "RB") and candidate.poste != owner.poste:
        return 2
    return None

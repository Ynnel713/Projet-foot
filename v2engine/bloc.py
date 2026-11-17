"""Bloc de référence dynamique (ticket v2-collectif/04) : la place d'un joueur loin du ballon n'est plus sa position
de coup d'envoi mais une position de référence dans le bloc de son équipe. Le bloc suit le ballon (surtout dans la
longueur) et change de forme selon la situation de jeu perçue (ticket 03) : resserré sans ballon, étiré avec.

Deux attributs, en deux temps distincts (règle R2, docs/CARTE_ATTRIBUTS_V2.md) : Positioning calcule la place
(erreur de placement), puis Teamwork décide d'y retourner (écart toléré avant de se replacer).

Constantes validées par le propriétaire le 27/10/2026 (valeurs de départ, ajustables) :
- suivi du ballon : 50 % de son décalage au centre du terrain en longueur, 30 % en largeur (Frencken et al. 2012 :
  le centre de l'équipe suit surtout le ballon dans la longueur ; parts exactes non trouvées), plages 30-70 % et 15-45 % ;
- forme sans ballon 32 x 40 m, avec ballon 42 x 46 m (longueur x largeur, joueurs de champ ; réel 31-46 x 35-48 m,
  bloc médian de la Coupe du monde 2022 à 27,2 x 40,1 m) ;
- Positioning, erreur de placement tirée toutes les 5 s : 99 -> 0,5 m, 55 -> 2 m, 11 -> 4 m (ordre de grandeur) ;
- Teamwork, écart toléré : 99 -> 2 m, 55 -> 5 m, 11 -> 9 m (ordre de grandeur) ;
- avec ballon, le bloc montait de 8 m vers le but adverse (`POSSESSION_ADVANCE_M`, 27/10/2026), sans règle sur la
  hauteur de sa dernière ligne : les centraux restaient près de leur gardien. Remplacé par le calage sur la ligne
  (ticket v2-realisme/09j, ci-dessous).

Hauteur de la dernière ligne avec ballon (ticket v2-realisme/09j, constantes validées par le propriétaire le 16/11/2026 ;
ordres de grandeur, chiffres réels non vérifiés dans une source, à recalibrer au ticket 27b) : comme sans ballon, le bloc
se cale sur la hauteur de sa dernière ligne, `H = 40 + 0,5 x (ballon - 52,5)` depuis son but, bornée entre 15 et 55 m.
Tout le bloc monte avec elle, les décalages des rôles (02d) à l'intérieur. Les corrections de la ligne sans ballon
(pression sur le porteur, attaquant adverse le plus avancé) ne s'appliquent pas : se protéger du contre relève de la
défense préventive (09g). Le retard de réaction au Teamwork faible (`line_lag_s`) s'applique.

Distances entre les lignes avec ballon (ticket v2-realisme/09e, constantes validées par le propriétaire le 16/11/2026 ;
réel avec ballon, SkillCorner, `docs/INDICATEURS_V2.md` : défense-milieu 13,7 m (11,1-16,6), milieu-attaque 14,3 m
(11,5-17,2), longueur 33,9 m) : lignes = moyenne des centraux (DC), des milieux axiaux (MDC, MC, MOC), des avant-centres
(BU), dans la forme avec ballon mise à l'échelle. Un écart défense-milieu hors de 10-15 m, ou milieu-attaque hors de
10-20 m, est ramené à la borne la plus proche : la ligne et tout ce qui est devant elle se déplacent, les joueurs entre
deux lignes sont étirés en proportion (décalages des rôles du 02d conservés). La dernière ligne reste sur `H` ; le bloc
avec ballon raccourcit en conséquence (il n'est pas remis à 42 m).

Hauteur de la ligne défensive sans ballon (ticket v2-collectif/05, revue par le ticket v2-collectif/23 le
28/10/2026) : le bloc se place pour que sa dernière ligne soit à la plus basse de deux hauteurs, jamais à moins
de 5 m de son but :
- 35 m de son but ballon au centre, suivant le ballon comme le bloc (ligne médiane 45 m, moyenne 47 m, dans
  arXiv 2511.06191) ; + 5 m si le porteur adverse est pressé (adversaire à moins de 3 m), - 5 m s'il est libre
  (le plus proche à 9 m ou plus), progressif entre les deux ;
- au plus 5 m AU-DESSUS de l'attaquant adverse le plus avancé (`offside.TRAP_DEPTH_M`), moins ce que l'attaquant
  gagne sur 30 m sur le défenseur le plus lent de la ligne (vitesses max, Pace : capacité, règle R5). Jusqu'au
  ticket 23, la ligne devait rester 2 m DERRIÈRE cet attaquant : sans hors-jeu c'était le seul garde-fou, et il
  interdisait le piège par construction. Le hors-jeu le remplace : la ligne peut monter au-dessus de l'attaquant,
  au risque d'être prise dans le dos (mesuré, ticket 23) ;
- la ligne monte en bloc, mais chaque défenseur la suit avec un retard d'autant plus grand que son Teamwork est
  faible (`line_lag_s` : 99 -> 0 s, 55 -> 0,75 s, 11 -> 1,5 s). Le Positioning n'est pas relu ici : il agit déjà
  par l'erreur de placement du ticket 04, qui décale le défenseur de la ligne de la même façon. C'est la faille
  collective : un seul défenseur en retard remet tout le monde en jeu, puisque le hors-jeu se juge sur les
  positions réelles.

Place avec ballon propre au rôle (ticket v2-realisme/02d, constantes proposées par Claude le 06/11/2026 et validées
par délégation ; chiffres réels non trouvés, ordres de grandeur tactiques) : avec ballon, chaque joueur est décalé de
`ROLE_PLACE_WITH_BALL[rôle]` = (avance vers le but adverse, écart à l'axe vers la touche ; négatif = rentre) AVANT la
mise à l'échelle du bloc. La forme décalée sert aussi à mesurer le bloc avec ballon (centre, longueur, largeur) : les
rôles redistribuent les joueurs DANS le bloc 42 x 46 m déjà calibré, sans le déplacer ni l'agrandir (1 m de bloc en
plus = environ 1,4 tir par équipe, mesuré au ticket 04). Un rôle absent de la table, ou vide, ne bouge pas : le
comportement d'avant 02d.

Place sans ballon propre au rôle (ticket v2-realisme/02e, mêmes principes, table `ROLE_PLACE_WITHOUT_BALL`) : le bloc
sans ballon reste 32 x 40 m, calé sur la hauteur de sa dernière ligne. Les rôles redistribuent les joueurs dans ce
bloc ; personne ne passe derrière la dernière ligne de la forme de départ (`without_ball_place`), la ligne reste donc
celle des défenseurs. Le repli défensif propre à chaque rôle (qui suit son latéral, qui reste prêt à ressortir) en
découle ; la couverture et les zones arrivent au ticket 10.

Placement de construction (ticket v2-realisme/25b, constantes proposées par Claude et validées par le propriétaire le
17/11/2026 ; chiffres réels non trouvés, ordres de grandeur tactiques) : quand le ballon est au gardien, à un défenseur
dans ses 35 m (`BUILD_UP_ZONE_M`) ou que l'équipe a une sortie de but (pendant la passe qui en part aussi, jusqu'au
contrôle suivant), la place avec ballon reçoit en plus `ROLE_PLACE_BUILD_UP[rôle]` (avance, écart vers la touche), en
mètres sur le terrain, après la mise à l'échelle du bloc : les centraux s'ouvrent vers les angles de la surface, la
sentinelle ou le regista décroche dans l'axe, les latéraux montent et s'ouvrent, les relayeurs vont dans les
demi-espaces. Sous pressing haut (adversaires de champ dans nos 35 m : 2 ou moins, écartement complet ; 4 ou plus,
moitié ; linéaire entre), l'écart vers la touche est réduit : les joueurs restent plus près du porteur. Personne ne
s'ouvre à moins de 2 m de la touche. La hauteur de la dernière ligne (09j) n'est pas changée ; la place reste ensuite
tenue avec la tolérance du Teamwork (`replacement`)."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from v2engine.attributes import success_probability
from v2engine.condition import effective_rating
from v2engine.geometry import PITCH_LENGTH_M, PITCH_WIDTH_M, Vec2, clamp_to_pitch
from v2engine.ball_state import BallState
from v2engine.flux import PLACEMENT
from v2engine.movement import PlayerState, max_speed_mps
from v2engine.offside import TRAP_DEPTH_M
from v2engine.restart import GOAL_KICK
from v2engine.situation import DEFENSE_PLACEE, TRANSITION_DEFENSIVE

if TYPE_CHECKING:
    from v2engine.perception_memory import PerceptionMemory

BLOCK_SHIFT = (0.5, 0.3)  # part du décalage du ballon suivie par le bloc : longueur, largeur
SHAPE_WITHOUT_BALL = (32.0, 40.0)  # longueur, largeur visées (m)
SHAPE_WITH_BALL = (42.0, 46.0)
POSITIONING_REDRAW_S = 5.0
# baseline, amplitude, min, max (inversés : bonne note = petite valeur, voir `_inverse`)
_POSITIONING_ERROR_M = (2.5, 2.0, 0.5, 4.0)
_TEAMWORK_TOLERANCE_M = (6.0, 4.0, 2.0, 9.0)
ARRIVAL_M = 1.0  # place atteinte à 1 m près (pas une constante produit : l'erreur de Positioning va de 0,5 à 4 m)
LINE_HEIGHT_M = 35.0  # dernière ligne, depuis son but, ballon au centre et porteur ni pressé ni libre
# Avec ballon (ticket v2-realisme/09j, validées le 16/11/2026) : dernière ligne ballon au centre, suivi du ballon, plancher,
# plafond (2,5 m au-delà de la ligne médiane, atteint ballon à 22,5 m du but adverse).
LINE_HEIGHT_WITH_BALL_M = 40.0
LINE_BALL_FOLLOW = 0.5
LINE_MIN_WITH_BALL_M, LINE_MAX_WITH_BALL_M = 15.0, 55.0
PRESSURE_STEP_M = 5.0  # la ligne monte (porteur pressé) ou recule (porteur libre) d'autant
PRESSED_M, FREE_M = 3.0, 9.0  # distance du défenseur le plus proche au porteur : pressé en dessous, libre au-delà
CUSHION_RUN_M = 30.0  # rabaissement de la ligne quand elle est plus lente que l'attaquant le plus avancé
# Réaction de la ligne (ticket v2-collectif/23, directive « piège collectif » du 28/10/2026) : la ligne monte en
# bloc, mais un défenseur au Teamwork faible suit avec un retard -- c'est la faille qui laisse
# l'attaquant en jeu (le classique appel dans le dos d'une ligne qui monte). 99 -> 0 s, 55 -> 0,75 s, 11 -> 1,5 s.
LINE_LAG_MAX_S = 1.5
_DEPTH_MARGIN_M = 5.0  # le bloc garde sa dernière ligne à 5 m de son but (marge de `formation`), pas une constante produit
_CENTER = Vec2(PITCH_LENGTH_M / 2.0, PITCH_WIDTH_M / 2.0)
# rôle -> (avance, écart à l'axe) en mètres sur la forme de départ, avec ballon. Les 20 rôles de `roles.ROLES` y
# figurent (un test le vérifie) : 0 = reste à sa place de départ.
ROLE_PLACE_WITH_BALL: dict[str, tuple[float, float]] = {
    "gardien": (0.0, 0.0), "défenseur central": (0.0, 0.0),
    "latéral": (5.0, 1.0), "latéral défensif": (-3.0, -2.0), "piston": (12.0, 4.0),
    "sentinelle": (-4.0, 0.0), "récupérateur": (-6.0, 0.0), "regista": (-4.0, 0.0),
    "milieu relayeur": (0.0, 0.0), "box to box": (4.0, 0.0), "mezzala": (2.0, 3.0),
    "meneur": (4.0, 0.0), "milieu offensif": (6.0, 0.0),
    "ailier de couloir": (8.0, 2.0), "ailier intérieur": (6.0, -8.0), "meneur excentré": (2.0, -5.0),
    "second attaquant": (-2.0, 0.0), "avant-centre": (3.0, 0.0), "buteur axial": (5.0, 0.0), "pivot": (-5.0, 0.0),
}
# Même table, sans ballon (ticket v2-realisme/02e, constantes proposées par Claude le 06/11/2026, validées par
# délégation ; chiffres réels non trouvés, ordres de grandeur tactiques). Les défenseurs ne bougent pas : leur ligne
# est celle du bloc (`Bloc.update`). Le piston, l'ailier de couloir et le récupérateur redescendent ; l'ailier
# intérieur et le meneur excentré restent plus hauts qu'eux ; les attaquants restent hauts, prêts à ressortir.
ROLE_PLACE_WITHOUT_BALL: dict[str, tuple[float, float]] = {
    "gardien": (0.0, 0.0), "défenseur central": (0.0, 0.0),
    "latéral": (0.0, -2.0), "latéral défensif": (0.0, -3.0), "piston": (-10.0, -3.0),
    "sentinelle": (-3.0, 0.0), "récupérateur": (-5.0, 0.0), "regista": (-2.0, 0.0),
    "milieu relayeur": (0.0, 0.0), "box to box": (-2.0, 0.0), "mezzala": (-2.0, -2.0),
    "meneur": (-2.0, 0.0), "milieu offensif": (-2.0, 0.0),
    "ailier de couloir": (-8.0, -2.0), "ailier intérieur": (-2.0, -5.0), "meneur excentré": (-3.0, -4.0),
    "second attaquant": (-2.0, 0.0), "avant-centre": (3.0, 0.0), "buteur axial": (5.0, 0.0), "pivot": (2.0, 0.0),
}
# Placement de construction (ticket v2-realisme/25b, validées le 17/11/2026) : rôle -> (avance, écart vers la touche) en
# mètres sur le terrain, ajoutés à la place avec ballon. Un rôle absent ne bouge pas.
ROLE_PLACE_BUILD_UP: dict[str, tuple[float, float]] = {
    "défenseur central": (0.0, 8.0), "sentinelle": (-6.0, 0.0), "regista": (-8.0, 0.0), "récupérateur": (-3.0, 0.0),
    "latéral": (6.0, 10.0), "latéral défensif": (3.0, 8.0), "piston": (0.0, 6.0),
    "milieu relayeur": (0.0, 4.0), "mezzala": (0.0, 4.0), "box to box": (0.0, 4.0),
}
BUILD_UP_ZONE_M = 35.0  # porteur défenseur dans ses 35 m ; pressing haut compté dans la même zone
BUILD_UP_BUILDERS = frozenset({"GK", "DC", "LB", "RB", "LWB", "RWB"})
BUILD_UP_PRESS_COUNT = (2, 4)  # adversaires de champ dans la zone : écartement complet jusqu'au 1er, réduit dès le 2nd
BUILD_UP_PRESS_SPREAD = 0.5  # part de l'écart vers la touche gardée sous pressing haut
BUILD_UP_TOUCHLINE_M = 2.0  # personne ne s'ouvre plus près de la touche
# Bornes des écarts entre lignes avec ballon (ticket v2-realisme/09e) et postes de chaque ligne
GAP_DEF_MID_M = (10.0, 15.0)
GAP_MID_ATT_M = (10.0, 20.0)
_LINE_POSTES = ({"DC"}, {"MDC", "MC", "MOC"}, {"BU"})
_ON_AXIS_M = 1.0  # à moins de 1 m de l'axe, pas de côté : seule l'avance s'applique
_WITHOUT_BALL = (DEFENSE_PLACEE, TRANSITION_DEFENSIVE)


def _progress(team: str, x: float) -> float:
    """Distance à son propre but, dans l'axe du terrain (domicile défend x = 0)."""
    return x if team == "home" else PITCH_LENGTH_M - x


def builds_up(holder: PlayerState) -> bool:
    """Le porteur est-il dans sa zone de construction (ticket 25b) : gardien ou défenseur (`BUILD_UP_BUILDERS`) dans
    ses `BUILD_UP_ZONE_M` ? Lu aussi par la décision (relance courte ou longue, ticket v2-collectif/15a)."""
    return holder.poste in BUILD_UP_BUILDERS and _progress(holder.team, holder.position.x) < BUILD_UP_ZONE_M


def build_up_rivals(team: str, players: list[PlayerState]) -> int:
    """Adversaires de champ dans la zone de construction de `team` (ses `BUILD_UP_ZONE_M`), ticket 25b."""
    return sum(1 for p in players if p.team != team and p.poste != "GK"
               and _progress(team, p.position.x) < BUILD_UP_ZONE_M)


def build_up_pressed(holder: PlayerState, players: list[PlayerState]) -> bool:
    """Le porteur construit-il sous pressing (ticket v2-collectif/15b1) : dans sa zone de construction, avec au moins
    `BUILD_UP_PRESS_COUNT[0]` adversaires de champ dans cette zone (même seuil que le placement du ticket 25b) ?"""
    return builds_up(holder) and build_up_rivals(holder.team, players) >= BUILD_UP_PRESS_COUNT[0]


def _remember(history: list[tuple[float, float]], now_s: float, height: float) -> None:
    """Ajoute la hauteur de ligne du tick et oublie ce qui dépasse le plus long retard possible (`LINE_LAG_MAX_S`)."""
    history.append((now_s, height))
    while len(history) > 1 and now_s - history[0][0] > LINE_LAG_MAX_S:
        history.pop(0)


def _inverse(note: float, params: tuple[float, float, float, float]) -> float:
    baseline, amplitude, low, high = params
    return low + high - success_probability(note, baseline=baseline, amplitude=amplitude, min_prob=low, max_prob=high)


def positioning_error_m(player: PlayerState) -> float:
    return _inverse(effective_rating(player, "Positioning"), _POSITIONING_ERROR_M)


def teamwork_tolerance_m(player: PlayerState) -> float:
    return _inverse(effective_rating(player, "Teamwork"), _TEAMWORK_TOLERANCE_M)


def line_lag_s(player: PlayerState) -> float:
    """Retard avec lequel `player` suit la montée de sa ligne (99 -> 0 s, 55 -> 0,75 s, 11 -> 1,5 s). C'est la
    discipline collective qui est en jeu, donc Teamwork seul : l'écart de placement dû au Positioning est déjà
    tiré par `target` (ticket 04), et un défenseur décalé joue lui aussi l'attaquant en jeu -- deux effets
    distincts, un attribut chacun (règles R1 et R2 de la carte)."""
    return (1.0 - success_probability(effective_rating(player, "Teamwork"), baseline=0.5, amplitude=0.5,
                                      min_prob=0.0, max_prob=1.0)) * LINE_LAG_MAX_S


@dataclass
class _Shape:
    center: Vec2  # centre de la formation de départ (moyenne des joueurs de champ)
    length: float
    width: float
    back: float  # écart en x au centre du joueur de plus petit x (négatif)
    front: float  # écart en x au centre du joueur de plus grand x (positif)


def with_ball_line(team: str, ball_x: float) -> float:
    """Hauteur de la dernière ligne avec ballon, depuis son but (ticket v2-realisme/09j)."""
    height = LINE_HEIGHT_WITH_BALL_M + (_progress(team, ball_x) - _CENTER.x) * LINE_BALL_FOLLOW
    return min(max(height, LINE_MIN_WITH_BALL_M), LINE_MAX_WITH_BALL_M)


def with_ball_place(player: PlayerState) -> Vec2:
    """Place de départ du joueur décalée selon son rôle, pour le jeu avec ballon (ticket 02d)."""
    return _role_place(player, ROLE_PLACE_WITH_BALL)


def deepest_x(shape: _Shape, team: str) -> float:
    """Abscisse de la dernière ligne de la forme de départ (celle des défenseurs)."""
    return shape.center.x + (shape.back if team == "home" else shape.front)


def without_ball_place(player: PlayerState, deepest: float) -> Vec2:
    """Place de départ décalée selon son rôle, pour le jeu sans ballon (ticket 02e). Personne ne passe derrière la
    dernière ligne de la forme de départ (`deepest`) : un piston ou un récupérateur qui redescend rejoint la ligne
    des défenseurs, il ne la recule pas."""
    place = _role_place(player, ROLE_PLACE_WITHOUT_BALL)
    return Vec2(max(place.x, deepest) if player.team == "home" else min(place.x, deepest), place.y)


def _role_place(player: PlayerState, table: dict[str, tuple[float, float]]) -> Vec2:
    ahead, wide = table.get(player.role, (0.0, 0.0))
    start = player.home_target
    forward = 1.0 if player.team == "home" else -1.0
    side = start.y - _CENTER.y
    if abs(side) > _ON_AXIS_M:  # vers la touche de son côté (ou vers l'axe, sans le franchir)
        side = math.copysign(max(abs(side) + wide, 0.0), side)
        return Vec2(start.x + forward * ahead, _CENTER.y + side)
    return Vec2(start.x + forward * ahead, start.y)


def _depth(shape: _Shape, team: str, place: Vec2, sx: float) -> float:
    """Distance, mise à l'échelle, d'une place de la forme à sa dernière ligne, vers le but adverse."""
    return ((place.x - (shape.center.x + shape.back)) if team == "home" else (shape.center.x + shape.front - place.x)) * sx


def line_gap_knots(players: list[PlayerState], shape: _Shape, team: str) -> tuple[tuple[float, float, int], ...]:
    """Ticket v2-realisme/09e : un point de passage par ligne présente (profondeur de la ligne avant, après, indice de la
    ligne dans `_LINE_POSTES`) qui ramène les écarts entre les lignes de la forme avec ballon dans leurs bornes. Une
    ligne absente (pas de BU, par exemple) n'est pas contrainte."""
    sx = SHAPE_WITH_BALL[0] / shape.length if shape.length > 0 else 1.0
    levels = []
    for postes in _LINE_POSTES:
        depths = [_depth(shape, team, with_ball_place(p), sx) for p in players if p.poste in postes]
        levels.append(sum(depths) / len(depths) if depths else None)
    knots: list[tuple[float, float, int]] = []
    for index, (level, bounds) in enumerate(zip(levels, (None, GAP_DEF_MID_M, GAP_MID_ATT_M))):
        if level is None:
            continue
        if not knots:
            moved = level
        elif bounds is None or level <= knots[-1][0]:
            moved = knots[-1][1] + (level - knots[-1][0])
        else:
            moved = knots[-1][1] + min(max(level - knots[-1][0], bounds[0]), bounds[1])
        knots.append((level, moved, index))
    return tuple(knots)


def remap_depth(knots: tuple[tuple[float, float, int], ...], depth: float, poste: str = "") -> float:
    """Profondeur après correction des écarts. Un joueur d'une ligne suit sa ligne d'un bloc (la moyenne de la ligne
    tombe sur sa cible) ; les autres : identité avant la première ligne, linéaire entre deux lignes, décalage de la
    dernière ligne au-delà."""
    for level, moved, index in knots:
        if poste in _LINE_POSTES[index]:
            return depth + (moved - level)
    if not knots or depth <= knots[0][0]:
        return depth if not knots else depth + (knots[0][1] - knots[0][0])
    for (a, a2, _), (b, b2, _) in zip(knots, knots[1:]):
        if depth <= b:
            return a2 + (depth - a) * (b2 - a2) / (b - a) if b > a else b2
    return depth + (knots[-1][1] - knots[-1][0])


def _build_up_place(player: PlayerState, x: float, y: float, spread: float) -> tuple[float, float]:
    """Place avec ballon (x, y) décalée pour la construction (ticket 25b) : avance vers le but adverse, écart vers la
    touche de son côté (réduit par `spread`, jamais à moins de BUILD_UP_TOUCHLINE_M de la touche). Un joueur dans l'axe
    (à moins de 1 m) ne s'écarte pas."""
    ahead, wide = ROLE_PLACE_BUILD_UP.get(player.role, (0.0, 0.0))
    x += ahead * (1.0 if player.team == "home" else -1.0)
    side = y - _CENTER.y
    if abs(side) > _ON_AXIS_M and wide:
        limit = max(abs(side), _CENTER.y - BUILD_UP_TOUCHLINE_M)
        y = _CENTER.y + math.copysign(min(abs(side) + wide * spread, limit), side)
    return x, y


def _shape_of(pts: list[Vec2]) -> _Shape:
    xs, ys = [p.x for p in pts], [p.y for p in pts]
    cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
    return _Shape(Vec2(cx, cy), max(xs) - min(xs), max(ys) - min(ys), min(xs) - cx, max(xs) - cx)


@dataclass
class Bloc:
    """Forme de départ de chaque équipe (`from_players`), erreurs de placement en cours et joueurs en train de se
    replacer."""
    shapes: dict[str, _Shape]
    # forme de départ décalée par les rôles (ticket 02d) : sert au bloc avec ballon ; égale à `shapes` sans rôle
    shapes_ball: dict[str, _Shape] = field(default_factory=dict)
    shapes_low: dict[str, _Shape] = field(default_factory=dict)  # idem sans ballon (ticket 02e)
    errors: dict[str, tuple[Vec2, float]] = field(default_factory=dict)  # joueur -> (erreur, prochain tirage)
    returning: set[str] = field(default_factory=set)  # joueurs repartis vers leur place, jusqu'à l'atteindre
    lines: dict[str, float] = field(default_factory=dict)  # équipe -> hauteur de sa dernière ligne sans ballon (`update`)
    # équipe -> (instant, hauteur) : courte mémoire de la ligne, pour que chaque défenseur la suive avec son
    # propre retard (`line_lag_s`, ticket v2-collectif/23)
    line_history: dict[str, list[tuple[float, float]]] = field(default_factory=dict)
    # même chose avec ballon (ticket v2-realisme/09j) : hauteur de la dernière ligne et sa courte mémoire
    lines_ball: dict[str, float] = field(default_factory=dict)
    line_history_ball: dict[str, list[tuple[float, float]]] = field(default_factory=dict)
    gap_knots: dict[str, tuple[tuple[float, float, int], ...]] = field(default_factory=dict)  # écarts entre lignes (09e)
    # équipe en construction -> part de l'écartement gardée (1 sans pressing, 0,5 sous pressing haut), ticket 25b
    build_up: dict[str, float] = field(default_factory=dict)

    @classmethod
    def from_players(cls, players: list[PlayerState]) -> Bloc:
        shapes, shapes_ball, shapes_low = {}, {}, {}
        for team in {p.team for p in players}:
            field_players = [p for p in players if p.team == team and p.poste != "GK"]
            if not field_players:  # équipe sans joueur de champ : pas de bloc, chacun garde sa place de départ
                continue
            shapes[team] = _shape_of([p.home_target for p in field_players])
            shapes_ball[team] = _shape_of([with_ball_place(p) for p in field_players])
            deepest = deepest_x(shapes[team], team)
            shapes_low[team] = _shape_of([without_ball_place(p, deepest) for p in field_players])
        knots = {team: line_gap_knots([p for p in players if p.team == team], shape, team)
                 for team, shape in shapes_ball.items()}
        return cls(shapes, shapes_ball, shapes_low, gap_knots=knots)

    def update(self, players: list[PlayerState], ball: BallState, now_s: float = 0.0,
               memory: PerceptionMemory | None = None) -> None:
        """Hauteur de la dernière ligne de chaque équipe, sans ballon et avec ballon (une fois par tick). `memory` :
        mémoire de perception (ticket v2-realisme/08e) : l'attaquant le plus avancé est celui que le défenseur le plus bas
        de l'équipe (celui qui cale la ligne) perçoit comme tel, à la place où il le perçoit : une course dans son dos qu'il
        n'a pas vue ne fait pas redescendre la ligne. Sans mémoire : les vraies positions."""
        holder = next((p for p in players if p.name == ball.holder), None) if ball.holder else None
        self._update_build_up(players, ball, holder)
        for team in self.shapes:
            self.lines_ball[team] = with_ball_line(team, ball.position.x)  # ticket v2-realisme/09j
            _remember(self.line_history_ball.setdefault(team, []), now_s, self.lines_ball[team])
            own = [p for p in players if p.team == team and p.poste != "GK"]
            rivals = [p for p in players if p.team != team and p.poste != "GK"]
            if not own or not rivals:
                self.lines.pop(team, None)
                continue
            height = LINE_HEIGHT_M + (_progress(team, ball.position.x) - _CENTER.x) * BLOCK_SHIFT[0]
            if holder is not None and holder.team != team:
                gap = min(p.position.distance_to(holder.position) for p in own)
                free = min(max((gap - PRESSED_M) / (FREE_M - PRESSED_M), 0.0), 1.0)  # 0 pressé, 1 libre
                height += PRESSURE_STEP_M * (1.0 - 2.0 * free)
            if memory is None:
                deepest = max(rivals, key=lambda p: -_progress(team, p.position.x))  # attaquant le plus près de notre but
                deepest_x = deepest.position.x
            else:  # tel que le défenseur le plus bas le perçoit
                anchor = min(own, key=lambda p: _progress(team, p.position.x))
                where = {p.name: memory.perceived_position(anchor, p.name, now_s).x for p in rivals}
                deepest = max(rivals, key=lambda p: -_progress(team, where[p.name]))
                deepest_x = where[deepest.name]
            back = min(_progress(team, p.home_target.x) for p in own)
            # ligne la plus basse de la forme de départ (bandes espacées d'au moins 10 m : 1 m de tolérance suffit)
            slowest = min(max_speed_mps(effective_rating(p, "Pace")) for p in own if _progress(team, p.home_target.x) <= back + 1.0)
            gain = max(0.0, 1.0 - slowest / max_speed_mps(effective_rating(deepest, "Pace"))) * CUSHION_RUN_M
            # ticket 23 : la ligne peut se tenir jusqu'à TRAP_DEPTH_M au-dessus de l'attaquant le plus avancé ;
            # si elle est plus lente que lui, le gain de vitesse la fait redescendre (critère Pace du ticket 05).
            height = min(height, _progress(team, deepest_x) + TRAP_DEPTH_M - gain)
            self.lines[team] = max(height, _DEPTH_MARGIN_M)
            _remember(self.line_history.setdefault(team, []), now_s, self.lines[team])

    def _update_build_up(self, players: list[PlayerState], ball: BallState, holder: PlayerState | None) -> None:
        """Phase de construction de chaque équipe (ticket 25b) et écartement gardé selon le pressing adverse. Ballon en vol
        ou libre, hors remise : la phase continue jusqu'au contrôle suivant."""
        if ball.restart is not None:
            building = ball.restart.team if ball.restart.kind == GOAL_KICK else None
        elif holder is not None:
            building = holder.team if builds_up(holder) else None
        else:
            building = next(iter(self.build_up), None)
        self.build_up.clear()
        if building is None:
            return
        rivals = build_up_rivals(building, players)
        low, high = BUILD_UP_PRESS_COUNT
        pressed = min(max((rivals - low) / (high - low), 0.0), 1.0)
        self.build_up[building] = 1.0 - pressed * (1.0 - BUILD_UP_PRESS_SPREAD)

    def in_build_up(self, team: str) -> bool:
        """L'équipe est-elle en phase de construction (ticket 25b) ?"""
        return team in self.build_up

    def _line_for(self, player: PlayerState, now_s: float, with_ball: bool = False) -> float | None:
        """Hauteur de ligne telle que `player` la perçoit : la ligne d'il y a `line_lag_s(player)` secondes. `with_ball` :
        la ligne avec ballon (ticket v2-realisme/09j)."""
        line = (self.lines_ball if with_ball else self.lines).get(player.team)
        if line is None:
            return None
        history = (self.line_history_ball if with_ball else self.line_history).get(player.team)
        lag = line_lag_s(player)
        if not history or lag <= 0.0:
            return line
        wanted = now_s - lag
        seen = history[0][1]
        for instant, value in history:
            if instant <= wanted:
                seen = value
            else:
                break
        return seen

    def reference(self, player: PlayerState, ball: Vec2, situation: str, now_s: float = 0.0) -> Vec2:
        """Place du joueur dans le bloc, sans l'erreur de Positioning. Le gardien garde sa place de départ.
        `now_s` sert au retard de réaction (`line_lag_s`) : sans lui (0.0), un joueur au Teamwork faible voit la
        ligne de l'entrée la plus ancienne de l'historique au lieu de la ligne courante -- passer l'instant du tick
        dans le moteur, la valeur par défaut ne sert qu'aux tests sans historique."""
        shape = self.shapes.get(player.team)
        if shape is None or player.poste == "GK":
            return player.home_target
        with_ball = situation not in _WITHOUT_BALL
        start, anchor = player.home_target, shape.center  # le bloc reste centré sur le centre de la forme de départ
        if with_ball:  # place décalée par le rôle, et forme mesurée sur ces places (ticket 02d)
            shape, start = self.shapes_ball.get(player.team, shape), with_ball_place(player)
        elif player.team in self.shapes_low:  # idem sans ballon (ticket 02e)
            start = without_ball_place(player, deepest_x(shape, player.team))
            shape = self.shapes_low[player.team]
        length, width = SHAPE_WITH_BALL if with_ball else SHAPE_WITHOUT_BALL
        sx = length / shape.length if shape.length > 0 else 1.0
        sy = width / shape.width if shape.width > 0 else 1.0
        cx = anchor.x + (ball.x - _CENTER.x) * BLOCK_SHIFT[0]
        cy = anchor.y + (ball.y - _CENTER.y) * BLOCK_SHIFT[1]
        line = self._line_for(player, now_s, with_ball)
        if with_ball and line is None:  # pas encore de mise à jour (scène de test) : la ligne du ballon donné
            line = with_ball_line(player.team, ball.x)
        if line is not None:  # le bloc se cale sur la hauteur de sa dernière ligne : sans ballon (ticket 05), avec (09j)
            cx = line - shape.back * sx if player.team == "home" else PITCH_LENGTH_M - line - shape.front * sx
        # la forme entière reste sur le terrain, ses lignes extrêmes à 5 m au moins de chaque ligne de but
        cx = min(max(cx, _DEPTH_MARGIN_M - shape.back * sx), PITCH_LENGTH_M - _DEPTH_MARGIN_M - shape.front * sx)
        offset = start - shape.center
        x = cx + offset.x * sx
        knots = self.gap_knots.get(player.team) if with_ball else None
        if knots:  # écarts entre les lignes ramenés dans leurs bornes (ticket 09e)
            depth = _depth(shape, player.team, start, sx)
            x += (remap_depth(knots, depth, player.poste) - depth) * (1.0 if player.team == "home" else -1.0)
        y = cy + offset.y * sy
        spread = self.build_up.get(player.team) if with_ball else None
        if spread is not None:  # placement de construction (ticket 25b)
            x, y = _build_up_place(player, x, y, spread)
        return clamp_to_pitch(Vec2(x, y))

    def target(self, player: PlayerState, ball: Vec2, situation: str, now_s: float) -> Vec2:
        """Place visée : la référence, décalée sans ballon de l'erreur de Positioning du moment (placement défensif de
        zone, règle R3 ; tirée toutes les 5 s, direction quelconque, distance uniforme entre 0 et deux fois l'erreur
        moyenne). Le gardien n'est pas concerné."""
        if situation not in _WITHOUT_BALL or player.poste == "GK":
            return self.reference(player, ball, situation, now_s)
        return clamp_to_pitch(self.reference(player, ball, situation, now_s) + self.placement_error(player, now_s))

    def placement_error(self, player: PlayerState, now_s: float) -> Vec2:
        """Erreur de placement du moment (Positioning), tirée toutes les 5 s : sert à sa place dans le bloc comme à
        la couverture (ticket v2-collectif/07), une seule erreur par joueur."""
        error, next_s = self.errors.get(player.name, (None, 0.0))
        if error is None or now_s >= next_s:
            angle = PLACEMENT.uniform(0.0, 2.0 * math.pi)
            distance = PLACEMENT.uniform(0.0, 2.0 * positioning_error_m(player))
            error = Vec2(math.cos(angle) * distance, math.sin(angle) * distance)
            self.errors[player.name] = (error, now_s + POSITIONING_REDRAW_S)
        return error

    def replacement(self, player: PlayerState, ball: Vec2, situation: str, now_s: float) -> Vec2 | None:
        """Place à rejoindre, ou None s'il la tient (Teamwork). Il ne repart que s'il s'en écarte de plus que sa
        tolérance ; reparti, il va jusqu'à sa place (à ARRIVAL_M près). Le gardien rejoint toujours la sienne."""
        place = self.target(player, ball, situation, now_s)
        if player.poste == "GK":
            return place
        distance = player.position.distance_to(place)
        if player.name in self.returning:
            if distance > ARRIVAL_M:
                return place
            self.returning.discard(player.name)
            return None
        if distance > teamwork_tolerance_m(player):
            self.returning.add(player.name)
            return place
        return None

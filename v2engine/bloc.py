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
- avec ballon, le bloc monte de 8 m vers le but adverse (validé à 15 m le 27/10/2026, ajustable par mesure ; mesuré sur
  20 matchs à 0, 5, 8, 11 et 15 m : de 5,7 à 25,7 tirs par équipe ; 8 m (13,7 tirs, 3,0 buts) garde tirs et buts dans les
  fourchettes réelles ;
  sans lui, le bloc d'attaque restait centré sur la place du coup d'envoi, dans sa moitié : tirs divisés par deux).

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
  positions réelles."""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from v2engine.attributes import player_attribute, success_probability
from v2engine.geometry import PITCH_LENGTH_M, PITCH_WIDTH_M, Vec2, clamp_to_pitch
from v2engine.ball_state import BallState
from v2engine.flux import PLACEMENT
from v2engine.movement import PlayerState, max_speed_mps
from v2engine.offside import TRAP_DEPTH_M
from v2engine.situation import DEFENSE_PLACEE, TRANSITION_DEFENSIVE

BLOCK_SHIFT = (0.5, 0.3)  # part du décalage du ballon suivie par le bloc : longueur, largeur
SHAPE_WITHOUT_BALL = (32.0, 40.0)  # longueur, largeur visées (m)
SHAPE_WITH_BALL = (42.0, 46.0)
POSSESSION_ADVANCE_M = 8.0  # le bloc monte vers le but adverse quand l'équipe a le ballon
POSITIONING_REDRAW_S = 5.0
# baseline, amplitude, min, max (inversés : bonne note = petite valeur, voir `_inverse`)
_POSITIONING_ERROR_M = (2.5, 2.0, 0.5, 4.0)
_TEAMWORK_TOLERANCE_M = (6.0, 4.0, 2.0, 9.0)
ARRIVAL_M = 1.0  # place atteinte à 1 m près (pas une constante produit : l'erreur de Positioning va de 0,5 à 4 m)
LINE_HEIGHT_M = 35.0  # dernière ligne, depuis son but, ballon au centre et porteur ni pressé ni libre
PRESSURE_STEP_M = 5.0  # la ligne monte (porteur pressé) ou recule (porteur libre) d'autant
PRESSED_M, FREE_M = 3.0, 9.0  # distance du défenseur le plus proche au porteur : pressé en dessous, libre au-delà
CUSHION_RUN_M = 30.0  # rabaissement de la ligne quand elle est plus lente que l'attaquant le plus avancé
# Réaction de la ligne (ticket v2-collectif/23, directive « piège collectif » du 28/10/2026) : la ligne monte en
# bloc, mais un défenseur au Teamwork faible suit avec un retard -- c'est la faille qui laisse
# l'attaquant en jeu (le classique appel dans le dos d'une ligne qui monte). 99 -> 0 s, 55 -> 0,75 s, 11 -> 1,5 s.
LINE_LAG_MAX_S = 1.5
_DEPTH_MARGIN_M = 5.0  # le bloc garde sa dernière ligne à 5 m de son but (marge de `formation`), pas une constante produit
_CENTER = Vec2(PITCH_LENGTH_M / 2.0, PITCH_WIDTH_M / 2.0)
_WITHOUT_BALL = (DEFENSE_PLACEE, TRANSITION_DEFENSIVE)


def _progress(team: str, x: float) -> float:
    """Distance à son propre but, dans l'axe du terrain (domicile défend x = 0)."""
    return x if team == "home" else PITCH_LENGTH_M - x


def _inverse(note: float, params: tuple[float, float, float, float]) -> float:
    baseline, amplitude, low, high = params
    return low + high - success_probability(note, baseline=baseline, amplitude=amplitude, min_prob=low, max_prob=high)


def positioning_error_m(player: PlayerState) -> float:
    return _inverse(player_attribute(player, "Positioning"), _POSITIONING_ERROR_M)


def teamwork_tolerance_m(player: PlayerState) -> float:
    return _inverse(player_attribute(player, "Teamwork"), _TEAMWORK_TOLERANCE_M)


def line_lag_s(player: PlayerState) -> float:
    """Retard avec lequel `player` suit la montée de sa ligne (99 -> 0 s, 55 -> 0,75 s, 11 -> 1,5 s). C'est la
    discipline collective qui est en jeu, donc Teamwork seul : l'écart de placement dû au Positioning est déjà
    tiré par `target` (ticket 04), et un défenseur décalé joue lui aussi l'attaquant en jeu -- deux effets
    distincts, un attribut chacun (règles R1 et R2 de la carte)."""
    return (1.0 - success_probability(player_attribute(player, "Teamwork"), baseline=0.5, amplitude=0.5,
                                      min_prob=0.0, max_prob=1.0)) * LINE_LAG_MAX_S


@dataclass
class _Shape:
    center: Vec2  # centre de la formation de départ (moyenne des joueurs de champ)
    length: float
    width: float
    back: float  # écart en x au centre du joueur de plus petit x (négatif)
    front: float  # écart en x au centre du joueur de plus grand x (positif)


@dataclass
class Bloc:
    """Forme de départ de chaque équipe (`from_players`), erreurs de placement en cours et joueurs en train de se
    replacer."""
    shapes: dict[str, _Shape]
    errors: dict[str, tuple[Vec2, float]] = field(default_factory=dict)  # joueur -> (erreur, prochain tirage)
    returning: set[str] = field(default_factory=set)  # joueurs repartis vers leur place, jusqu'à l'atteindre
    lines: dict[str, float] = field(default_factory=dict)  # équipe -> hauteur de sa dernière ligne sans ballon (`update`)
    # équipe -> (instant, hauteur) : courte mémoire de la ligne, pour que chaque défenseur la suive avec son
    # propre retard (`line_lag_s`, ticket v2-collectif/23)
    line_history: dict[str, list[tuple[float, float]]] = field(default_factory=dict)

    @classmethod
    def from_players(cls, players: list[PlayerState]) -> Bloc:
        shapes = {}
        for team in {p.team for p in players}:
            pts = [p.home_target for p in players if p.team == team and p.poste != "GK"]
            if not pts:  # équipe sans joueur de champ : pas de bloc, chacun garde sa place de départ
                continue
            xs, ys = [p.x for p in pts], [p.y for p in pts]
            cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
            shapes[team] = _Shape(Vec2(cx, cy), max(xs) - min(xs), max(ys) - min(ys), min(xs) - cx, max(xs) - cx)
        return cls(shapes)

    def update(self, players: list[PlayerState], ball: BallState, now_s: float = 0.0) -> None:
        """Hauteur de la dernière ligne de chaque équipe, si elle n'a pas le ballon (une fois par tick)."""
        holder = next((p for p in players if p.name == ball.holder), None) if ball.holder else None
        for team in self.shapes:
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
            deepest = max(rivals, key=lambda p: -_progress(team, p.position.x))  # attaquant le plus près de notre but
            back = min(_progress(team, p.home_target.x) for p in own)
            # ligne la plus basse de la forme de départ (bandes espacées d'au moins 10 m : 1 m de tolérance suffit)
            slowest = min(max_speed_mps(p.pace) for p in own if _progress(team, p.home_target.x) <= back + 1.0)
            gain = max(0.0, 1.0 - slowest / max_speed_mps(deepest.pace)) * CUSHION_RUN_M
            # ticket 23 : la ligne peut se tenir jusqu'à TRAP_DEPTH_M au-dessus de l'attaquant le plus avancé ;
            # si elle est plus lente que lui, le gain de vitesse la fait redescendre (critère Pace du ticket 05).
            height = min(height, _progress(team, deepest.position.x) + TRAP_DEPTH_M - gain)
            self.lines[team] = max(height, _DEPTH_MARGIN_M)
            history = self.line_history.setdefault(team, [])
            history.append((now_s, self.lines[team]))
            while len(history) > 1 and now_s - history[0][0] > LINE_LAG_MAX_S:
                history.pop(0)

    def _line_for(self, player: PlayerState, now_s: float) -> float | None:
        """Hauteur de ligne telle que `player` la perçoit : la ligne d'il y a `line_lag_s(player)` secondes."""
        line = self.lines.get(player.team)
        if line is None:
            return None
        history = self.line_history.get(player.team)
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
        length, width = SHAPE_WITH_BALL if with_ball else SHAPE_WITHOUT_BALL
        sx = length / shape.length if shape.length > 0 else 1.0
        sy = width / shape.width if shape.width > 0 else 1.0
        forward = 1.0 if player.team == "home" else -1.0  # convention du moteur : domicile attaque vers x croissant
        cx = shape.center.x + (ball.x - _CENTER.x) * BLOCK_SHIFT[0] + (forward * POSSESSION_ADVANCE_M if with_ball else 0.0)
        cy = shape.center.y + (ball.y - _CENTER.y) * BLOCK_SHIFT[1]
        line = None if with_ball else self._line_for(player, now_s)
        if line is not None:  # sans ballon : le bloc se cale sur la hauteur de sa dernière ligne (ticket 05)
            cx = line - shape.back * sx if player.team == "home" else PITCH_LENGTH_M - line - shape.front * sx
        # la forme entière reste sur le terrain, ses lignes extrêmes à 5 m au moins de chaque ligne de but
        cx = min(max(cx, _DEPTH_MARGIN_M - shape.back * sx), PITCH_LENGTH_M - _DEPTH_MARGIN_M - shape.front * sx)
        offset = player.home_target - shape.center
        return clamp_to_pitch(Vec2(cx + offset.x * sx, cy + offset.y * sy))

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

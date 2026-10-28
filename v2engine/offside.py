"""Hors-jeu (loi 11, ticket v2-collectif/23) : le jugement est pris AU DÉPART de la passe, sur les positions
réelles, et ne se transforme en coup franc que si le joueur signalé touche ensuite le ballon (« hors-jeu
passif » : on ne siffle que la participation active). Ce module ne fait que la règle et les probabilités qui
la concernent ; le coup franc lui-même est rendu par `match._step_ball`.

Constantes produit validées par le propriétaire le 28/10/2026 :
- tolérance de 0,3 m : en dessous, les joueurs sont « à hauteur », donc en jeu (l'œil humain ne juge pas 2 cm) ;
- profondeur du piège de 5 m : la ligne défensive peut se tenir jusqu'à 5 m AU-DESSUS de l'attaquant le plus
  avancé (hauteur de ligne d'une équipe qui presse haut, façon Klopp/Pochettino), au lieu des 2 m EN DESSOUS
  du ticket 05 qui interdisaient le hors-jeu par construction ;
- Off the Ball règle le respect de la ligne : 99 -> 95 %, 55 -> 75 %, 11 -> 55 %. C'est le « timing de l'appel »,
  rayon propre d'Off the Ball (`docs/CARTE_ATTRIBUTS_V2.md`), donc pas de double comptage avec Decisions.

Ajouts du 28/10/2026 (directives comportementales du propriétaire -- valeurs de départ ajustables, à valider avec la
calibration du ticket 22) :
- `HESITATION_S` (1,5 s) et `HESITATION_INTENSITY` (0,4) : un défenseur qui voit le drapeau lève la main et relâche
  son effort (`play the whistle` : personne ne s'arrête avant le sifflet, mais le défenseur, lui, attend) ;
  `_SEES_FLAG` règle s'il le voit, par Anticipation : 99 -> 70 %, 55 -> 45 %, 11 -> 20 % ;
- `OFFSIDE_OUT_S` (1,5 s) : l'attaquant fautif est écarté de l'action après le coup franc, le temps de reculer ;
- `LINE_LAG_MAX_S` (1,5 s, `bloc.py`) : retard maximal d'un défenseur au Teamwork faible sur la montée de la ligne ;
- `PASS_OFFSIDE_MARGIN_M` (0,5 m) : ce que le passeur voit. En dessous, il joue la passe et l'arbitre juge -- sans
  ce filtre, le moteur servait délibérément un joueur cinq mètres hors-jeu (21,5 hors-jeu et 28 tirs de contre par
  match mesurés le 28/10/2026).

Réalité mesurée (indicateur de calibration, pas un objectif) : 3,2 à 3,5 hors-jeu par match en Ligue 1 et en
Premier League, soit 1,6 à 1,8 par équipe (PerformanceOdds 2023-24 et 2024-25, FootyStats 2026-27). Moteur sur
20 matchs, 28/10/2026 : 3,5 par match, 1,75 par équipe.

Non modélisé, assumé : pas de hors-jeu sur touche, sortie de but ni corner (ces phases n'existent pas encore) ;
pas de hors-jeu sur une passe d'un adversaire (aucune déviation modélisée) ; pas de hors-jeu pour gêne du
gardien sans toucher le ballon.
"""

from __future__ import annotations

import random
from collections.abc import Sequence

from v2engine.attributes import player_attribute, success_probability
from v2engine.geometry import PITCH_LENGTH_M, Vec2
from v2engine.movement import PlayerState

OFFSIDE_TOLERANCE_M = 0.3  # écart en dessous duquel deux joueurs sont « à hauteur »
TRAP_DEPTH_M = 5.0  # la ligne peut se tenir jusqu'à 5 m au-dessus de l'attaquant le plus avancé
# Œil du passeur : au-delà d'un demi-mètre, un professionnel voit que son coéquipier est hors-jeu et ne le sert
# pas. En dessous, il joue la passe -- c'est le hors-jeu « à la limite », celui que l'arbitre met deux minutes à
# trancher. Un mètre serait un angle mort trop large pour un joueur de ce niveau.
# Sans ce filtre, le moteur passait délibérément à des joueurs 5 m au-delà de la ligne : 21,5 hors-jeu par match au
# lieu de 3,2 à 3,5 (mesure du 28/10/2026), et les coups francs rendaient le ballon à l'adversaire en pleine
# attaque, ce qui faisait exploser les tirs de contre (28 au lieu de 9,5).
PASS_OFFSIDE_MARGIN_M = 0.5
# Seuil net, pas un tirage : c'est une information du joueur (comme la portée de Vision), pas un attribut. Un
# tirage inventerait un attribut qui n'existe pas dans la carte (règle R1) ; le jugement du passeur reste grossier,
# c'est assumé.
ONSIDE_MARGIN_M = 1.0  # marge visée derrière la ligne par un attaquant qui règle son appel
# Respect de la ligne (Off the Ball) : baseline, amplitude, min, max -> 99 : 95 %, 55 : 75 %, 11 : 55 %.
_KEEP_ONSIDE = (0.75, 0.20, 0.40, 0.97)
# Voir le drapeau (Anticipation) : 99 -> 70 %, 55 -> 45 %, 11 -> 20 %.
_SEES_FLAG = (0.45, 0.25, 0.20, 0.70)
HESITATION_S = 1.5  # temps de flottement du défenseur qui lève la main
HESITATION_INTENSITY = 0.4  # part de sa vitesse max pendant ce flottement
OFFSIDE_OUT_S = 1.5  # temps pendant lequel l'attaquant fautif est écarté de l'action après le coup franc


def progress(team: str, x: float) -> float:
    """Distance à son propre but, dans l'axe du terrain (domicile défend x = 0)."""
    return x if team == "home" else PITCH_LENGTH_M - x


def second_last_defender_progress(team: str, opponents: Sequence[PlayerState]) -> float | None:
    """Distance à son propre but de l'AVANT-DERNIER adversaire (le deuxième plus proche de son but, le gardien
    étant le dernier en général). `None` si l'équipe adverse compte moins de deux joueurs (cas synthétique)."""
    values = sorted((progress(team, o.position.x) for o in opponents), reverse=True)
    return values[1] if len(values) >= 2 else None


def offside_line(team: str, ball: Vec2, opponents: Sequence[PlayerState]) -> float | None:
    """Ligne du hors-jeu (distance à son propre but) : le plus avancé du ballon et de l'avant-dernier adversaire.
    Un attaquant à hauteur de cette ligne est en jeu ; au-delà, il est en position de hors-jeu."""
    second = second_last_defender_progress(team, opponents)
    if second is None:
        return None
    return max(progress(team, ball.x), second)


def is_offside_position(team: str, position: Vec2, ball: Vec2, opponents: Sequence[PlayerState],
                        tolerance: float = OFFSIDE_TOLERANCE_M) -> bool:
    """Position de hors-jeu (loi 11) : dans la moitié adverse, plus près du but adverse que le ballon ET que
    l'avant-dernier adversaire, de plus que la tolérance. Être à hauteur n'est pas être hors-jeu."""
    ahead = progress(team, position.x)
    if ahead <= PITCH_LENGTH_M / 2.0:  # on ne peut pas être hors-jeu dans sa propre moitié
        return False
    if ahead <= progress(team, ball.x) + tolerance:  # derrière le ballon, ou à sa hauteur
        return False
    second = second_last_defender_progress(team, opponents)
    if second is None:
        return False
    return ahead > second + tolerance


def offside_at_pass(team: str, ball: Vec2, mates: Sequence[PlayerState], opponents: Sequence[PlayerState],
                    tolerance: float = OFFSIDE_TOLERANCE_M) -> set[str]:
    """Joueurs de `team` en position de hors-jeu à l'instant du départ de la passe (le passeur n'en fait pas
    partie : il joue le ballon, il est par définition à sa hauteur)."""
    return {p.name for p in mates
            if is_offside_position(team, p.position, ball, opponents, tolerance)}


def is_clearly_offside(team: str, position: Vec2, ball: Vec2, opponents: Sequence[PlayerState],
                       margin: float = PASS_OFFSIDE_MARGIN_M) -> bool:
    """Vrai si le décalage est assez gros pour qu'un passeur le voie (`PASS_OFFSIDE_MARGIN_M`) : il ne sert alors
    pas ce coéquipier. En dessous, il joue la passe et c'est à l'arbitre de juger -- d'où les hors-jeu à la limite
    que l'on veut simuler, et non les passes délibérées à un joueur cinq mètres au-delà de la ligne."""
    return is_offside_position(team, position, ball, opponents, margin)


def keep_onside_probability(off_the_ball: float) -> float:
    """Chance qu'un attaquant règle son appel sur la ligne au lieu de partir au-delà (Off the Ball)."""
    baseline, amplitude, low, high = _KEEP_ONSIDE
    return success_probability(off_the_ball, baseline=baseline, amplitude=amplitude, min_prob=low, max_prob=high)


def respects_the_line(player: PlayerState) -> bool:
    """Tirage : cet attaquant respecte-t-il la ligne du hors-jeu sur cet appel ?"""
    return random.random() < keep_onside_probability(player_attribute(player, "Off the Ball"))


def clamp_to_onside(team: str, point: Vec2, line: float, margin: float = ONSIDE_MARGIN_M) -> Vec2:
    """Ramène un point visé derrière la ligne du hors-jeu, à `margin` près, en conservant sa largeur. Ne touche à
    rien dans la moitié défensive (le hors-jeu n'y existe pas)."""
    limit = line - margin
    if limit <= PITCH_LENGTH_M / 2.0 or progress(team, point.x) <= limit:
        return point
    x = limit if team == "home" else PITCH_LENGTH_M - limit
    return Vec2(x, point.y)


def sees_the_flag_probability(anticipation: float) -> float:
    """Chance qu'un défenseur voie le drapeau et lève la main (Anticipation : lire l'action avant qu'elle
    arrive). Il ne s'arrête pas -- il attend le sifflet, ce que le moteur ne prononce qu'au contact du ballon."""
    baseline, amplitude, low, high = _SEES_FLAG
    return success_probability(anticipation, baseline=baseline, amplitude=amplitude, min_prob=low, max_prob=high)

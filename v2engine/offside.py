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
- `LINE_LAG_MAX_S` (1,5 s, `bloc.py`) : retard maximal d'un défenseur au Teamwork faible sur la montée de la ligne.

Deuxième passe du 28/10/2026 (le passeur n'est plus omniscient) :
- `PASS_OFFSIDE_MARGIN_M` (0,5 m) : seuil d'un passeur de Vision moyenne. C'est ce qui empêche de servir
  délibérément un joueur cinq mètres hors-jeu (sans lui, 21,5 hors-jeu et 28 tirs de contre par match mesurés le
  28/10/2026) ;
- `pass_margin_m` : ce seuil est un angle mort, qui se resserre quand la Vision monte (11 -> 0,79 m, 63,4 -> 0,5 m,
  100 -> 0,3 m, la tolérance de l'arbitre). Correction du 29/10/2026 (option S2, choix du propriétaire) : la première
  version faisait grandir le seuil avec la Vision (0,1 à 0,78 m), donc les meilleurs passeurs servaient le plus de
  joueurs sifflés (5,5 passes vers un hors-jeu pour 1 000 à Vision 70 et plus, contre 1,55 à 50-69) ;
- `_LINE_READ_ERROR_M` (0,05 m à Vision 99, 0,25 m à Vision 0, `perceived_defence_line`) : le passeur ne voit pas la
  ligne parfaite. Quand il la surestime -- il ne voit pas le défenseur qui la tient -- il joue une passe que
  l'arbitre siffle. C'est l'erreur humaine qui rouvre les passes en profondeur. Le tirage utilise le flux aléatoire
  du match : il décale donc les scores des matchs suivants quand on change son amplitude, ce qui rend les écarts
  entre deux réglages non attribuables sur les autres indicateurs (mesuré le 28/10/2026) ;
- ancrage du seuil : `PASS_MARGIN_REFERENCE_VISION` vaut 63,4, la Vision moyenne des titulaires de Ligue 1 -- et non
  55, qui est le milieu de l'échelle 11-99. Ancrer sur 55 gonflait toutes les marges de 16 % : 4,45 hors-jeu par match
  au lieu de 3,65 (même code, seule la constante change, 20 matchs). La commande de mesure de cette moyenne :
  `uv run python -m scripts.vision_moyenne`.

Réalité mesurée (indicateur de calibration, pas un objectif) : 3,2 à 3,5 hors-jeu par match en Ligue 1 et en
Premier League, soit 1,6 à 1,8 par équipe (PerformanceOdds 2023-24 et 2024-25, FootyStats 2026-27). Moteur sur
20 matchs, 29/10/2026, après la correction de la deuxième passe : 3,1 par match, 1,55 par équipe (3,65 avant).

Non modélisé, assumé : pas de hors-jeu sur touche, sortie de but ni corner (ces phases n'existent pas encore) ;
pas de hors-jeu sur une passe d'un adversaire (aucune déviation modélisée) ; pas de hors-jeu pour gêne du
gardien sans toucher le ballon.
"""

from __future__ import annotations

from collections.abc import Sequence

from v2engine.attributes import success_probability
from v2engine.condition import effective_rating
from v2engine.flux import DECISION, PERCEPTION
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
# Seuil de RÉFÉRENCE : la Vision d'un passeur MOYEN mesurée sur la base, et non le milieu de l'échelle 11-99.
# 55 est le milieu de l'échelle (le point d'ancrage des courbes de la carte), pas la moyenne des joueurs : la Vision
# moyenne des 198 titulaires de Ligue 1 vaut 63,4 (joueurs sans attributs comptés 60, comme dans le moteur ; mesure
# reproductible avec `uv run python -m scripts.vision_moyenne`). Ancrer le seuil sur 55 gonflait donc toutes les
# marges de 16 % et, avec elles, le hors-jeu (4,45 par match au lieu de 3,65, mesuré le 28/10/2026, même code et
# seule cette constante changée) : ce n'est pas la modulation qui coûtait, c'est son point d'ancrage.
# `pass_margin_m` module la base par la Vision du passeur.
PASS_MARGIN_REFERENCE_VISION = 63.4
# Erreur de lecture de la ligne défensive (Vision) : 0,05 m à Vision 99, 0,25 m à Vision 0 (0,23 m à Vision 11).
# C'est l'erreur humaine demandée le 28/10/2026 : un passeur qui surestime la ligne -- il ne voit pas le défenseur qui
# la tient -- joue une passe que l'arbitre siffle. Symétrique : il sous-estime aussi, et refuse alors des passes
# légales. Reste modeste : elle s'ajoute à l'angle mort du passeur (`pass_margin_m`, 0,3 à 0,85 m). Le tirage consomme
# le flux aléatoire du match : changer cette amplitude décale les scores des matchs suivants, donc les écarts entre
# deux réglages ne sont pas attribuables (mesuré le 28/10/2026).
_LINE_READ_ERROR_M = (0.05, 0.25)
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
                        tolerance: float = OFFSIDE_TOLERANCE_M, defence_line: float | None = None) -> bool:
    """Position de hors-jeu (loi 11) : dans la moitié adverse, plus près du but adverse que le ballon ET que
    l'avant-dernier adversaire, de plus que la tolérance. Être à hauteur n'est pas être hors-jeu.
    `defence_line` : ligne défensive telle que la voit celui qui juge (par défaut, la vraie) ; le ballon, lui, est
    toujours exact -- le passeur l'a dans les pieds."""
    ahead = progress(team, position.x)
    if ahead <= PITCH_LENGTH_M / 2.0:  # on ne peut pas être hors-jeu dans sa propre moitié
        return False
    if ahead <= progress(team, ball.x) + tolerance:  # derrière le ballon, ou à sa hauteur
        return False
    second = second_last_defender_progress(team, opponents) if defence_line is None else defence_line
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
                       margin: float = PASS_OFFSIDE_MARGIN_M, defence_line: float | None = None) -> bool:
    """Vrai si le décalage dépasse ce que ce passeur-là tolère (`margin`, voir `pass_margin_m`) : il ne sert alors
    pas ce coéquipier. En dessous, il joue la passe et c'est à l'arbitre de juger -- d'où les hors-jeu à la limite
    que l'on veut simuler, et non les passes délibérées à un joueur cinq mètres au-delà de la ligne."""
    return is_offside_position(team, position, ball, opponents, margin, defence_line)


def pass_margin_m(vision: float, base: float = PASS_OFFSIDE_MARGIN_M) -> float:
    """Angle mort du passeur : décalage au-delà de la ligne en dessous duquel il ne voit pas que son coéquipier est
    hors-jeu, et joue donc la passe. Au-delà de la tolérance de l'arbitre (0,3 m), chaque centimètre d'angle mort est
    une passe sifflée : mieux on voit, plus l'angle mort se resserre. Vision moyenne (63,4) : le seuil validé de
    0,5 m ; Vision 11 : 0,79 m ; Vision 100 : la tolérance elle-même, jamais en dessous -- un très bon passeur ne
    refuse pas une passe légale par excès de prudence (option S2, choisie par le propriétaire le 29/10/2026, après
    l'audit qui a relevé le sens inverse de la deuxième passe)."""
    slope = (base - OFFSIDE_TOLERANCE_M) / (100.0 - PASS_MARGIN_REFERENCE_VISION)
    return OFFSIDE_TOLERANCE_M + slope * (100.0 - max(0.0, min(100.0, vision)))


def line_read_error_m(vision: float) -> float:
    """Erreur de lecture de la ligne défensive, en mètres : 0,05 m à Vision 99, 0,25 m à Vision 0."""
    small, large = _LINE_READ_ERROR_M
    return large - (large - small) * (max(0.0, min(100.0, vision)) / 100.0)


def perceived_defence_line(team: str, opponents: Sequence[PlayerState], vision: float) -> float | None:
    """Ligne défensive telle que le passeur la CROIT : la vraie, plus une erreur de lecture d'autant plus grande que
    sa Vision est basse (`line_read_error_m`). C'est l'erreur humaine demandée le 28/10/2026 : le passeur ne voit
    pas la ligne parfaite. Quand il surestime la ligne (il ne voit pas le défenseur qui la tient), il joue une passe
    que l'arbitre siffle ; quand il la sous-estime, il refuse une passe légale."""
    line = second_last_defender_progress(team, opponents)
    if line is None:
        return None
    error = line_read_error_m(vision)
    return line + PERCEPTION.uniform(-error, error)


def keep_onside_probability(off_the_ball: float) -> float:
    """Chance qu'un attaquant règle son appel sur la ligne au lieu de partir au-delà (Off the Ball)."""
    baseline, amplitude, low, high = _KEEP_ONSIDE
    return success_probability(off_the_ball, baseline=baseline, amplitude=amplitude, min_prob=low, max_prob=high)


def respects_the_line(player: PlayerState) -> bool:
    """Tirage : cet attaquant respecte-t-il la ligne du hors-jeu sur cet appel ?"""
    return DECISION.random() < keep_onside_probability(effective_rating(player, "Off the Ball"))


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

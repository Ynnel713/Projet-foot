"""Déplacement sans ballon de l'équipe en possession (Phase 5, ticket v2-cerveau-joueurs/03, Off the Ball) :
au lieu de foncer sur le ballon, chaque coéquipier du porteur cherche un espace libre autour de sa place de
formation, surtout vers l'avant (appel), parfois en décrochage. Off the Ball règle jusqu'où il cherche et la
probabilité qu'il trouve le meilleur espace (Guide_attributs_joueurs.pdf, Off the Ball).

Soutien du porteur (ticket v2-collectif/06) : un bon espace est d'abord trouvable par une passe du porteur, et pas
collé à un coéquipier."""

from __future__ import annotations

import random
from collections.abc import Sequence
from dataclasses import replace

from v2engine.attributes import player_attribute, success_probability
from v2engine.geometry import PITCH_LENGTH_M, Vec2, clamp_to_pitch
from v2engine.movement import PlayerState
from v2engine.offside import ONSIDE_MARGIN_M
from v2engine.possession import pass_success_probability

# Constantes produit validées par le propriétaire (30/10/2026, ticket v2-collectif/06).
OPEN_LANE_PROBABILITY = 0.7  # espace trouvable : passe au moins aussi sûre qu'une passe moyenne du moteur (69,8 %)
SPACING_MIN_M = 8.0  # écart minimal à un coéquipier (sa position ou l'espace qu'il vise)
SPACE_REACHED_M = 2.0  # espace atteint : il en cherche un autre (pas avant RUN_INTERVAL_S)
SPACE_HOLD_MAX_S = 3.0  # au plus tard, il en cherche un autre
# Contre-attaque (ticket v2-collectif/11, validé le 01/11/2026) : un coéquipier devant le ballon cherche son espace
# 15 m plus loin vers l'avant que sa place dans le bloc, sans dépasser la ligne du hors-jeu s'il la respecte.
COUNTER_RUN_DEPTH_M = 15.0

# Appel dans le dos (ticket v2-collectif/16, validé le 02/11/2026). Volonté du coureur (Off the Ball), par recherche
# d'espace : baseline, amplitude, min, max -> 99 : 60 %, 55 : 35 %, 11 : 10 %.
_DEPTH_RUN = (0.35, 0.25, 0.10, 0.60)
# Le porteur peut-il l'exploiter : il voit l'appel (Vision) et sait le servir (Passing), trois probabilités distinctes
# multipliées (règle R2, pas de moyenne) ; même courbe pour les deux -> produit à notes égales 99 : 95 %, 55 : 70 %, 11 : 47 % (45 % proposé).
_EXPLOIT = (0.8367, 0.152, 0.05, 0.975)
DEPTH_REACH_M = 20.0  # place dans le bloc à 20 m ou moins de la ligne du hors-jeu
DEPTH_LANE_M = 15.0  # pas d'appel dans le dos à moins de 15 m (en largeur) d'un coéquipier posté ou parti sur la ligne

# Constantes produit validées par le propriétaire (24/10/2026).
RUN_INTERVAL_S = 1.0  # délai minimal avant de chercher un autre espace (ticket 06 : garde jusqu'à l'atteindre)
_SEARCH_RADIUS_M = (8.0, 7.0, 2.0, 15.0)  # baseline, amplitude, min, max : 99 -> 15 m, 55 -> 8 m, 11 -> 2 m
_FORWARD_SHARE = 2.0 / 3.0  # part du rayon cherchée vers l'avant ; le reste (1/3) en arrière
# Choisir le meilleur espace : 99 -> 95 %, 55 -> 70 %, 11 -> 45 % (même courbe que Decisions).
_BEST_SPACE_BASELINE = 0.70
_BEST_SPACE_AMPLITUDE = 0.25

# Grille de points candidats, en fractions du rayon : avant/arrière x latéral. Pas une constante produit.
_FORWARD_STEPS = (-1.0 / 3.0, 0.0, 1.0 / 3.0, _FORWARD_SHARE)
_LATERAL_STEPS = (-0.5, 0.0, 0.5)


def search_radius_m(off_the_ball: float) -> float:
    baseline, amplitude, low, high = _SEARCH_RADIUS_M
    return success_probability(off_the_ball, baseline=baseline, amplitude=amplitude, min_prob=low, max_prob=high)


def best_space_probability(off_the_ball: float) -> float:
    return success_probability(off_the_ball, baseline=_BEST_SPACE_BASELINE, amplitude=_BEST_SPACE_AMPLITUDE)


def depth_run_probability(runner: PlayerState, holder: PlayerState) -> float:
    """Chance qu'un coureur tente l'appel dans le dos : sa volonté (Off the Ball) fois la capacité du porteur à
    l'exploiter (Vision, puis Passing). Un porteur faible fait renoncer même un excellent coureur (ticket 16)."""
    baseline, amplitude, low, high = _DEPTH_RUN
    will = success_probability(player_attribute(runner, "Off the Ball"), baseline=baseline, amplitude=amplitude,
                               min_prob=low, max_prob=high)
    baseline, amplitude, low, high = _EXPLOIT
    sees = success_probability(player_attribute(holder, "Vision"), baseline=baseline, amplitude=amplitude,
                               min_prob=low, max_prob=high)
    delivers = success_probability(player_attribute(holder, "Passing"), baseline=baseline, amplitude=amplitude,
                                   min_prob=low, max_prob=high)
    return will * sees * delivers


def depth_run(player: PlayerState, anchor: Vec2, ball: Vec2, line: float, holder: PlayerState | None,
              forward: float, mate_targets: Sequence[Vec2], held_for: str | None = None) -> Vec2 | None:
    """Point d'un appel dans le dos (ticket v2-collectif/16), ou None. `line` : ligne du hors-jeu, en distance au but
    de l'équipe du joueur (`offside.offside_line`). Candidat : devant le ballon, place dans le bloc à `DEPTH_REACH_M`
    ou moins de la ligne, aucun coéquipier, posté ou visant déjà la ligne, à moins de `DEPTH_LANE_M` en largeur. Il vise la ligne elle-même, à la
    largeur de sa place ; c'est ensuite la règle du hors-jeu qui le règle juste derrière (ticket 23).

    `held_for` : porteur pour qui il a déjà lancé cet appel. Il le tient sans nouveau tirage tant qu'il reste candidat
    et que ce porteur a le ballon, ou que la passe est en l'air ; un nouveau porteur le fait retirer au sort."""
    def depth(x: float) -> float:  # distance à son propre but
        return x if forward > 0 else PITCH_LENGTH_M - x

    holding = held_for is not None and (holder is None or holder.name == held_for)
    if (holder is None and not holding) or forward * (player.position.x - ball.x) <= 0.0 \
            or depth(anchor.x) < line - DEPTH_REACH_M:
        return None
    if any(depth(t.x) >= line - ONSIDE_MARGIN_M - SPACE_REACHED_M and abs(t.y - anchor.y) < DEPTH_LANE_M
           for t in mate_targets):
        return None  # profondeur déjà prise dans ce couloir : il ne double pas l'appel
    if not holding and random.random() >= depth_run_probability(player, holder):
        return None
    return clamp_to_pitch(Vec2(line if forward > 0 else PITCH_LENGTH_M - line, anchor.y))


def choose_space(player: PlayerState, opponents: list[PlayerState], forward: float, anchor: Vec2 | None = None,
                 holder: PlayerState | None = None, mates: Sequence[Vec2] = ()) -> Vec2:
    """Point libre visé par `player` (coéquipier du porteur), autour de `anchor` (sa place dans le bloc, ticket
    v2-collectif/04 ; à défaut, sa place de formation). `forward` : +1 si son équipe attaque vers x croissant, -1
    sinon. Un espace à moins de `SPACING_MIN_M` d'un point de `mates` (coéquipiers et espaces qu'ils visent) est
    écarté, sauf s'il n'en reste aucun ; un espace trouvable par une passe de `holder` passe avant les autres
    (ticket v2-collectif/06). Puis un espace vaut sa distance à l'adversaire le plus proche ; à égalité, le plus
    avancé gagne."""
    radius = search_radius_m(player_attribute(player, "Off the Ball"))
    origin = player.home_target if anchor is None else anchor
    candidates = [
        clamp_to_pitch(origin + Vec2(forward * fx * radius, ly * radius))
        for fx in _FORWARD_STEPS
        for ly in _LATERAL_STEPS
    ]
    spaced = [c for c in candidates if all(c.distance_to(m) >= SPACING_MIN_M for m in mates)]
    candidates = spaced or candidates

    def openness(point: Vec2) -> tuple[bool, float]:
        reachable = holder is None or pass_success_probability(
            holder, replace(player, position=point), opponents) >= OPEN_LANE_PROBABILITY
        nearest = min((point.distance_to(o.position) for o in opponents), default=0.0)
        return reachable, nearest + 0.01 * forward * point.x

    ranked = sorted(candidates, key=openness, reverse=True)
    if random.random() < best_space_probability(player_attribute(player, "Off the Ball")) or len(ranked) == 1:
        return ranked[0]
    return random.choice(ranked[1:])

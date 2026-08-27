"""Placement des 11 titulaires sur un terrain pour l'écran de détail d'un
match (vue "stade"). Logique pure, sans dépendance Streamlit : convertit une
liste de `PlayerMatchStat` en coordonnées (x, y) en pourcentage du terrain,
ligne par ligne (gardien / défense / milieu / attaque), selon le poste exact
de chaque joueur.
"""

from __future__ import annotations

from dataclasses import dataclass

from ligue1sim.events import PlayerMatchStat
from ligue1sim.players import ATTACKER, DEFENDER, GOALKEEPER, MIDFIELDER, position_group

# --- Nomenclature de placement latéral --------------------------------
#
# Couloir (0=gauche, 1=axe, 2=droite) de chaque poste. Les postes absents
# (axiaux : DC, MDC/MC/MOC, SA, BU, GK) valent 1 par défaut.
#
# Le placement d'une ligne doit toujours être strictement symétrique
# (miroir gauche-droite), quelle que soit sa composition exacte. Règle,
# dans cet ordre :
# 1. Ne compte comme "paire large confirmée" que des couloirs gauche ET
#    droite en nombre ÉGAL (ex. 1 latéral gauche + 1 latéral droit). La
#    sélection de la meilleure compo (voir `lineup.select_best_xi`) ne
#    garantit pas cet équilibre -- un effectif peut n'avoir aucun latéral
#    gauche mais deux latéraux droits. Le surplus sans contrepartie de
#    l'autre côté (ex. le 2e RB) est traité comme axial : l'affecter seul à
#    un bord casserait la symétrie et pousserait un joueur d'axe (ex. un
#    vrai DC) à l'opposé, sur la touche.
# 2. Chaque paire confirmée occupe deux positions strictement symétriques
#    par rapport à l'axe du terrain (voir `_wide_pair_positions`).
# 3. Tout le reste (postes d'axe + surplus non apparié) se regroupe dans une
#    bande centrale (voir `_central_band`), qui ne s'élargit jamais jusqu'à
#    chevaucher les paires latérales confirmées.
#
# Ces couloirs sont définis comme au vrai foot : gauche/droite du point de
# vue de l'équipe qui attaque (dans le sens de son attaque), pas de celui du
# spectateur. Une équipe qui attaque vers le HAUT de l'écran (`attacking_up`)
# a donc son latéral droit affiché à... droite de l'écran (les deux sens
# coïncident) ; une équipe qui attaque vers le BAS (le gardien tourné vers le
# haut de l'écran, dos au sens du jeu) a sa gauche/droite inversée à
# l'écran par rapport à la sienne -- son latéral droit apparaît à GAUCHE de
# l'écran. `_screen_lane` applique ce miroir ; ce dict reste la référence
# "gauche/droite du point de vue de l'équipe qui attaque vers le haut".
_LANE: dict[str, int] = {
    "LB": 0,
    "AG": 0,
    "RB": 2,
    "AD": 2,
}


def _screen_lane(poste: str, attacking_up: bool) -> int:
    lane = _LANE.get(poste, 1)
    return lane if attacking_up else 2 - lane

_FULL_WIDTH: tuple[float, float] = (12.0, 88.0)
_CENTRAL_BAND: tuple[float, float] = (32.0, 68.0)  # pour 1 ou 2 joueurs d'axe seuls dans leur ligne
_CENTRAL_BAND_GROWTH = 7.0  # % ajoutés de chaque côté par joueur d'axe supplémentaire au-delà de 2
_CENTRAL_BAND_CAP_WHEN_FLANKED: tuple[float, float] = (25.0, 75.0)  # marge de sécurité sous les paires latérales

# Poste qui forme systématiquement la ligne la plus basse d'un bloc milieu
# (sentinelle devant la défense, pointe basse du triangle d'un 4-3-3, etc.).
_HOLDING_MIDFIELD_POSTE = "MDC"

# Repli quand aucun "MDC" n'est identifiable mais que le bloc milieu compte 5
# joueurs ou plus (ex. 4-2-3-1) : ces postes sont considérés comme la ligne
# basse plausible.
_DEEP_MIDFIELD_POSTES = {"MDC", "MC"}


@dataclass(frozen=True)
class PlacedPlayer:
    stat: PlayerMatchStat
    x: float  # 0-100, pourcentage de la largeur du terrain
    y: float  # 0-100, pourcentage de la hauteur du terrain (0 = haut, 100 = bas)


def actual_formation_label(starters: list[PlayerMatchStat]) -> str:
    """Dispositif réellement aligné (ex. "3-4-2-1"), calculé à partir des
    places effectivement pourvues plutôt que du nom du dispositif visé au
    coup d'envoi.

    Priorité à `stat.band` (voir `lineup.Lineup.bands`, `_group_into_lines`
    ci-dessus) : le nombre de joueurs par ligne, dans l'ordre du dispositif
    exact choisi dans l'onglet "Dispositifs tactiques" (le gardien, bande 0,
    n'est pas compté). Si un joueur n'a pas de bande connue (repli par
    quotas génériques, voir `lineup._select_by_group_quota`), retombe sur un
    résumé générique DEF-MID-ATT (ex. "4-4-2").

    Dans les deux cas, quand l'effectif d'un club manque de profondeur dans
    un secteur, la sélection de la meilleure compo (voir
    `lineup.select_best_xi`) complète les places manquantes avec les
    meilleurs joueurs restants, quel que soit leur poste : le XI réel peut
    donc s'écarter du dispositif visé. Cette étiquette reflète toujours ce
    qui est effectivement affiché sur le terrain, pour rester cohérente avec
    `place_starting_xi`.
    """
    if starters and all(s.band is not None for s in starters):
        counts: dict[int, int] = {}
        for s in starters:
            counts[s.band] = counts.get(s.band, 0) + 1
        return "-".join(str(counts[band]) for band in sorted(counts) if band != 0)

    group_counts = {DEFENDER: 0, MIDFIELDER: 0, ATTACKER: 0}
    for s in starters:
        group = position_group(s.poste)
        if group in group_counts:
            group_counts[group] += 1
    return f"{group_counts[DEFENDER]}-{group_counts[MIDFIELDER]}-{group_counts[ATTACKER]}"


def place_starting_xi(starters: list[PlayerMatchStat], *, attacking_up: bool) -> list[PlacedPlayer]:
    """Place les titulaires ligne par ligne, du gardien vers l'attaque.

    `attacking_up=True` : le gardien est en bas du terrain, l'équipe attaque
    vers le haut (utilisé pour l'équipe à l'extérieur sur le terrain
    partagé, l'équipe à domicile étant placée en haut).
    `attacking_up=False` : inverse (équipe à domicile).
    """
    lines = _group_into_lines(starters)
    nb_lines = len(lines)
    placed: list[PlacedPlayer] = []
    for i, line in enumerate(lines):
        depth = i / (nb_lines - 1) if nb_lines > 1 else 0.0
        y = _line_y(depth, attacking_up)
        placed.extend(_place_line(line, y, attacking_up))
    return placed


def _place_line(line: list[PlayerMatchStat], y: float, attacking_up: bool) -> list[PlacedPlayer]:
    """Place une ligne en séparant paire(s) large(s) confirmée(s) (voir la
    nomenclature ci-dessus) et groupe central, chacun positionné en miroir
    symétrique par rapport à l'axe du terrain."""
    left = [s for s in line if _screen_lane(s.poste, attacking_up) == 0]
    right = [s for s in line if _screen_lane(s.poste, attacking_up) == 2]
    center = [s for s in line if _screen_lane(s.poste, attacking_up) == 1]

    pairs = min(len(left), len(right))
    wide_left, overflow_left = left[:pairs], left[pairs:]
    wide_right, overflow_right = right[:pairs], right[pairs:]
    center = overflow_left + center + overflow_right

    placed: list[PlacedPlayer] = []
    if pairs == 0:
        lo, hi = _central_band(len(center))
    else:
        for stat, x in zip(wide_left + wide_right, _wide_pair_positions(pairs)):
            placed.append(PlacedPlayer(stat=stat, x=x, y=y))
        lo, hi = _central_band(len(center), cap=_CENTRAL_BAND_CAP_WHEN_FLANKED)

    placed.extend(PlacedPlayer(stat=stat, x=_spread(i, len(center), lo, hi), y=y) for i, stat in enumerate(center))
    return placed


def _wide_pair_positions(pairs: int) -> list[float]:
    """Positions des `2 * pairs` joueurs des paires larges confirmées : les
    `pairs` de gauche puis les `pairs` de droite, toujours symétriques par
    construction (`_spread` sur un intervalle centré)."""
    total = 2 * pairs
    xs = [_spread(i, total, *_FULL_WIDTH) for i in range(total)]
    return xs[:pairs] + list(reversed(xs[pairs:]))


def _central_band(count: int, cap: tuple[float, float] = _FULL_WIDTH) -> tuple[float, float]:
    """Bande centrale pour le groupe axial (postes d'axe + surplus non
    apparié) : étroite pour 1-2 joueurs, s'élargit progressivement au-delà
    pour garder un espacement suffisant entre les ronds, sans jamais
    dépasser `cap` (la largeur complète du terrain si aucune paire large ne
    flanque la ligne, une bande plus resserrée sinon pour ne jamais
    chevaucher les paires latérales confirmées)."""
    lo, hi = _CENTRAL_BAND
    growth = max(0, count - 2) * _CENTRAL_BAND_GROWTH
    return max(cap[0], lo - growth), min(cap[1], hi + growth)


def _group_into_lines(starters: list[PlayerMatchStat]) -> list[list[PlayerMatchStat]]:
    """Regroupe les titulaires en lignes de profondeur, du gardien vers
    l'attaque.

    Priorité à `stat.band` (voir `lineup.Lineup.bands`) : l'indice de ligne
    exact déduit du dispositif choisi dans l'onglet "Dispositifs tactiques"
    (ex. un 3-4-2-1 rend fidèlement 3 défenseurs axiaux puis une ligne de 4
    -- les 2 pistons ET les 2 milieux -- puis 2 meneurs puis 1 pointe, plutôt
    que de regrouper les pistons avec les défenseurs axiaux). Si un joueur
    n'a pas de bande connue (repli par quotas génériques, voir
    `lineup._select_by_group_quota`), retombe sur l'ancien regroupement par
    grande famille de poste (GK/DEF/MID/ATT) pour toute la compo."""
    if starters and all(s.band is not None for s in starters):
        by_band: dict[int, list[PlayerMatchStat]] = {}
        for s in starters:
            by_band.setdefault(s.band, []).append(s)
        return [by_band[band] for band in sorted(by_band)]

    by_group: dict[str, list[PlayerMatchStat]] = {GOALKEEPER: [], DEFENDER: [], MIDFIELDER: [], ATTACKER: []}
    for s in starters:
        by_group[position_group(s.poste)].append(s)

    lines = [by_group[GOALKEEPER], by_group[DEFENDER]]
    lines += _midfield_lines(by_group[MIDFIELDER])
    if by_group[ATTACKER]:
        lines.append(by_group[ATTACKER])
    return [line for line in lines if line]


def _midfield_lines(mid: list[PlayerMatchStat]) -> list[list[PlayerMatchStat]]:
    """Sépare le bloc milieu en 1 ou 2 lignes de profondeur.

    Un bloc milieu qui contient une vraie "MDC" forme naturellement un
    triangle (ligne basse = sentinelle(s), ligne haute = le reste) -- que ce
    soit un 4-3-3 (1 sentinelle + 2 relayeurs) ou un 4-2-3-1 (2 sentinelles +
    3 devant). Sans "MDC" identifiable mais avec 5 milieux ou plus, on repère
    quand même une ligne basse plausible pour éviter une seule ligne à 5 trop
    tassée. En dessous de 5, sans "MDC", le bloc reste une bande plate unique
    (ex. milieu à 4 d'un 4-4-2)."""
    if not mid:
        return []

    holding = [s for s in mid if s.poste == _HOLDING_MIDFIELD_POSTE]
    rest = [s for s in mid if s.poste != _HOLDING_MIDFIELD_POSTE]
    if holding and rest:
        return [holding, rest]

    if len(mid) >= 5:
        ordered = sorted(mid, key=lambda s: s.poste not in _DEEP_MIDFIELD_POSTES)
        return [ordered[:2], ordered[2:]]

    return [mid]


def _spread(index: int, count: int, lo: float, hi: float) -> float:
    if count == 1:
        return (lo + hi) / 2.0
    step = (hi - lo) / (count - 1)
    return lo + index * step


def _line_y(depth: float, attacking_up: bool) -> float:
    # Les lignes offensives des deux équipes s'arrêtent à distance du milieu
    # de terrain (au lieu de s'étirer jusqu'à la ligne médiane) pour ne pas se
    # chevaucher visuellement quand les deux équipes alignent une ligne large.
    if attacking_up:
        return 90.0 - depth * 32.0
    return 10.0 + depth * 32.0
